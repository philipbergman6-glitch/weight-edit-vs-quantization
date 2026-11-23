"""Build the data behind the explainer site (docs/) and the post video, from the real files.

Reads, and never runs a model:
- the base and edited safetensors files (tensor list, and the raw 16-bit bytes of the two edited tensors);
- the six GGUF files in models/gguf/ (16-bit, 8-bit, 4-bit; both models), read back with llama.cpp's own
  `gguf` reader and dequantizer, as src/edit_rounding.py does;
- the per-response flags in results/flags/ and the llama-quantize logs.

Writes docs/data/: manifest.json (every number the page shows, with the file it came from), four 8-bit
grayscale PNGs of layer 15's down_proj tensor (pooled 4 x 4), and crop.bin (a 64 x 256 window of real
weights, float32, for six versions). Every figure that also appears in results/*.md is checked against that
file and the script stops if they disagree. Deterministic: same inputs, same bytes out.

Usage: uv run --offline python -I src/site_data.py models results docs/data
(the `gguf` package comes from vendor/llama.cpp/gguf-py, the llama.cpp tree that built the GGUF files,
when it is not installed in the environment)
"""
import json
import re
import struct
import sys
import zlib
from pathlib import Path
from statistics import median

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
try:
    import gguf
except ImportError:
    vendored = ROOT / "vendor" / "llama.cpp" / "gguf-py"
    if not vendored.is_dir():
        raise SystemExit("the gguf package is not installed and vendor/llama.cpp/gguf-py is missing")
    sys.path.insert(0, str(vendored))
    import gguf
from gguf.quants import dequantize

ST_NAME = "model.safetensors-00001-of-00001.safetensors"
EDITED = {15: "model.language_model.layers.15.mlp.down_proj.weight",
          19: "model.language_model.layers.19.mlp.down_proj.weight"}
GG_NAME = {15: "blk.15.ffn_down.weight", 19: "blk.19.ffn_down.weight"}
LEVELS = ["BF16", "Q8_0", "Q4_K_M"]
POOL = 4          # overview images: one pixel per 4 x 4 weights
CROP_ROWS, CROP_COLS = 64, 256   # 256 = one Q4_K super-block = eight blocks of 32
EDIT_SCALE = 0.02   # colour scale for edits, symmetric: -0.02 .. 0 .. +0.02, values beyond are clipped


def fail(msg: str) -> None:
    raise SystemExit(f"site_data: {msg}")


def need(path: Path) -> Path:
    if not path.exists():
        fail(f"missing input: {path}")
    return path


# ---------------------------------------------------------------- safetensors
def st_header(path: Path) -> tuple[dict, int]:
    with open(need(path), "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        head = json.loads(f.read(n))
    head.pop("__metadata__", None)
    return head, 8 + n


def st_bf16(path: Path, name: str) -> np.ndarray:
    head, base = st_header(path)
    meta = head.get(name) or fail(f"{path}: no tensor {name}")
    if meta["dtype"] != "BF16":
        fail(f"{name}: expected BF16, found {meta['dtype']}")
    a, b = meta["data_offsets"]
    with open(path, "rb") as f:
        f.seek(base + a)
        raw = np.frombuffer(f.read(b - a), dtype="<u2")
    return (raw.astype(np.uint32) << 16).view(np.float32).reshape(meta["shape"])


# ---------------------------------------------------------------- gguf
def gg_tensors(path: Path) -> dict:
    out = {}
    for t in gguf.GGUFReader(str(need(path))).tensors:
        if t.name in GG_NAME.values():
            out[t.name] = t
    if set(out) != set(GG_NAME.values()):
        fail(f"{path}: edited tensors not found")
    return out


def q8_scales(t) -> np.ndarray:
    """Per-block scale d of a Q8_0 tensor: block = f16 d + 32 int8."""
    raw = np.asarray(t.data, dtype=np.uint8)
    rows = raw.shape[0]
    blocks = raw.reshape(rows, -1, 34)
    return blocks[:, :, :2].copy().view(np.float16).astype(np.float32)[:, :, 0]


def q4k_grid(t) -> tuple[np.ndarray, np.ndarray]:
    """Per-sub-block (32 weights) step and offset of a Q4_K tensor: value = step * q - offset, q in 0..15."""
    raw = np.asarray(t.data, dtype=np.uint8)
    rows = raw.shape[0]
    blocks = raw.reshape(-1, 144)
    d = blocks[:, 0:2].copy().view(np.float16).astype(np.float32)
    dmin = blocks[:, 2:4].copy().view(np.float16).astype(np.float32)
    sc, m = gguf.quants.Q4_K.get_scale_min(blocks[:, 4:16].copy())
    step = (d * sc.astype(np.float32)).reshape(rows, -1)
    off = (dmin * m.astype(np.float32)).reshape(rows, -1)
    return step, off


# ---------------------------------------------------------------- small helpers
def cos(a: np.ndarray, b: np.ndarray) -> float:
    return float((a * b).sum() / (np.linalg.norm(a) * np.linalg.norm(b)))


def png_gray(path: Path, img: np.ndarray) -> None:
    """Write an 8-bit grayscale PNG with zlib only (no imaging library needed)."""
    if img.dtype != np.uint8 or img.ndim != 2:
        fail("png_gray wants a 2-D uint8 array")
    h, w = img.shape
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def pool_signed_maxabs(x: np.ndarray) -> np.ndarray:
    """Pool 4 x 4 cells, keeping the value with the largest size (sign kept), so thin columns stay visible."""
    r, c = x.shape
    v = x.reshape(r // POOL, POOL, c // POOL, POOL).transpose(0, 2, 1, 3).reshape(r // POOL, c // POOL, -1)
    idx = np.abs(v).argmax(axis=2)
    return np.take_along_axis(v, idx[..., None], axis=2)[..., 0]


def pool_rms(x: np.ndarray) -> np.ndarray:
    r, c = x.shape
    v = x.reshape(r // POOL, POOL, c // POOL, POOL)
    return np.sqrt((v.astype(np.float64) ** 2).mean(axis=(1, 3)))


def signed_u8(x: np.ndarray, scale: float) -> np.ndarray:
    return np.round(128 + 127 * np.clip(x / scale, -1, 1)).astype(np.uint8)


def flags(results: Path, row: str) -> list[dict]:
    rows = [json.loads(line) for line in need(results / "flags" / f"{row}.jsonl").read_text().splitlines() if line.strip()]
    if len(rows) != 100:
        fail(f"{row}: expected 100 responses, found {len(rows)}")
    return rows


def md_has(path: Path, *needles: str) -> str:
    text = need(path).read_text()
    for n in needles:
        if n not in text:
            fail(f"{path} does not contain {n!r}; the site would disagree with the results files")
    return str(path.resolve().relative_to(ROOT))


def main(models: Path, results: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    src = {}  # number -> file it came from

    # ---- whole model: tensor list from the safetensors header
    head, _ = st_header(models / "base" / ST_NAME)
    head_e, _ = st_header(models / "edited" / ST_NAME)
    if set(head) != set(head_e):
        fail("base and edited files hold different tensors")

    def group(name: str) -> tuple[int, str]:
        m = re.match(r"model\.language_model\.layers\.(\d+)\.", name)
        if m:
            return 1 + int(m.group(1)), f"layer {int(m.group(1))}"
        if name.startswith("model.language_model.embed_tokens"):
            return 0, "embedding"
        if name.startswith("model.language_model."):
            return 25, "final norm"
        if name.startswith("mtp."):
            return 26, "multi-token prediction"
        if name.startswith("model.visual."):
            return 27, "vision encoder"
        fail(f"unplaced tensor {name}")

    tensors = sorted(head, key=lambda n: (group(n)[0], n))
    total = sum(int(np.prod(head[n]["shape"])) for n in tensors)
    model_map = [{"name": n, "group": group(n)[1], "count": int(np.prod(head[n]["shape"]))} for n in tensors]
    src_diff = md_has(results / "diff.md", f"Tensors compared: {len(head)}", f"Total weights: {total:,}",
                      "Weights that differ: 130,188", "Columns touched: 64 of 3584")

    # ---- the edit, at 16-bit, from both file formats (they must agree exactly)
    gg = {(m, lv): gg_tensors(models / "gguf" / f"{m}-{lv}.gguf") for m in ("base", "edited") for lv in LEVELS}
    W = {}
    for layer in (15, 19):
        for m in ("base", "edited"):
            st = st_bf16(models / m / ST_NAME, EDITED[layer])
            for lv in LEVELS:
                t = gg[(m, lv)][GG_NAME[layer]]
                W[(layer, m, lv)] = dequantize(t.data, t.tensor_type).astype(np.float32)
            if not np.array_equal(st, W[(layer, m, "BF16")]):
                fail(f"layer {layer} {m}: 16-bit GGUF and safetensors weights differ")
            if W[(layer, m, "BF16")].shape != (1024, 3584):
                fail(f"layer {layer}: unexpected shape {W[(layer, m, 'BF16')].shape}")

    edit = {}
    for layer in (15, 19):
        E = W[(layer, "edited", "BF16")].astype(np.float64) - W[(layer, "base", "BF16")]
        cols = np.flatnonzero(np.abs(E).sum(axis=0) > 0)
        s = np.linalg.svd(E, compute_uv=False)
        types = {lv: gg[("edited", lv)][GG_NAME[layer]].tensor_type.name for lv in LEVELS}
        cosines = {}
        for lv in LEVELS[1:]:
            Eq = W[(layer, "edited", lv)].astype(np.float64) - W[(layer, "base", lv)]
            cosines[lv] = round(cos(Eq, E), 4)
        edit[layer] = {"changed": int((E != 0).sum()), "columns": cols.tolist(),
                       "rank1_share": float(s[0] ** 2 / (s ** 2).sum()), "sigma": [round(float(s[0]), 4), round(float(s[1]), 4)],
                       "largest_change": float(np.abs(E).max()), "stored_as": types, "cosine": cosines}
    if edit[15]["changed"] + edit[19]["changed"] != 130188:
        fail("changed-weight count does not match results/diff.md")
    src_round = md_has(results / "edit-rounding.md",
                       f"| Q8_0 | Q8_0 | {edit[15]['cosine']['Q8_0']:.4f}", f"| Q4_K_M | Q4_K | {edit[15]['cosine']['Q4_K_M']:.4f}",
                       f"| Q8_0 | Q8_0 | {edit[19]['cosine']['Q8_0']:.4f}", f"| Q4_K_M | Q4_K | {edit[19]['cosine']['Q4_K_M']:.4f}")
    md_has(results / "diff.md", "99.999%", f"{edit[15]['sigma'][0]:.4f}", f"{edit[19]['sigma'][0]:.4f}")

    # ---- layer 15 overview images (pooled 4 x 4)
    Wb, We = W[(15, "base", "BF16")], W[(15, "edited", "BF16")]
    E16 = We - Wb
    rms = pool_rms(Wb)
    base_scale = float(np.quantile(rms, 0.995))
    png_gray(out / "l15-base.png", np.round(255 * np.clip(rms / base_scale, 0, 1)).astype(np.uint8))
    for lv, key in (("BF16", "16"), ("Q8_0", "8"), ("Q4_K_M", "4")):
        Eq = E16 if lv == "BF16" else W[(15, "edited", lv)] - W[(15, "base", lv)]
        png_gray(out / f"l15-edit-{key}.png", signed_u8(pool_signed_maxabs(Eq), EDIT_SCALE))

    # ---- the crop and the block: around the largest single change in layer 15
    r_star, c_star = np.unravel_index(np.abs(E16).argmax(), E16.shape)
    c0 = (c_star // CROP_COLS) * CROP_COLS
    r0 = (r_star // CROP_ROWS) * CROP_ROWS
    order = [("base", "BF16"), ("edited", "BF16"), ("base", "Q8_0"), ("edited", "Q8_0"), ("base", "Q4_K_M"), ("edited", "Q4_K_M")]
    crop = np.stack([W[(15, m, lv)][r0:r0 + CROP_ROWS, c0:c0 + CROP_COLS] for m, lv in order]).astype("<f4")
    (out / "crop.bin").write_bytes(crop.tobytes())

    b0 = (c_star // 32) * 32
    q8 = {m: q8_scales(gg[(m, "Q8_0")][GG_NAME[15]]) for m in ("base", "edited")}
    q4 = {m: q4k_grid(gg[(m, "Q4_K_M")][GG_NAME[15]]) for m in ("base", "edited")}
    block = {"row": int(r_star), "col0": int(b0), "edited_col": int(c_star), "values": {}, "q8_step": {}, "q4_step": {}, "q4_offset": {}}
    for m in ("base", "edited"):
        d = float(q8[m][r_star, b0 // 32])
        step, off = float(q4[m][0][r_star, b0 // 32]), float(q4[m][1][r_star, b0 // 32])
        v8 = W[(15, m, "Q8_0")][r_star, b0:b0 + 32]
        v4 = W[(15, m, "Q4_K_M")][r_star, b0:b0 + 32]
        # the grids must reproduce the dequantized values exactly, or the drawn levels would be wrong
        if not np.allclose(v8 / d, np.round(v8 / d), atol=1e-4) or np.abs(np.round(v8 / d)).max() > 128:
            fail("Q8_0 levels do not reproduce the stored values")
        q = (v4 + off) / step
        if not np.allclose(q, np.round(q), atol=1e-3) or np.round(q).min() < 0 or np.round(q).max() > 15:
            fail("Q4_K levels do not reproduce the stored values")
        block["values"][m] = {lv: [float(x) for x in W[(15, m, lv)][r_star, b0:b0 + 32]] for lv in LEVELS}
        block["q8_step"][m], block["q4_step"][m], block["q4_offset"][m] = d, step, off
    # distinct 4-bit values among the 31 weights of the block that the edit did not touch
    others = [i for i in range(32) if b0 + i != c_star]
    block["distinct_neighbours_q4"] = {m: len({float(W[(15, m, "Q4_K_M")][r_star, b0 + i]) for i in others}) for m in ("base", "edited")}

    # ---- answers: per-question flags, in the order of the edited 16-bit file
    rows = {f"{m}-{lv}": flags(results, f"{m}-{lv}") for m in ("base", "edited") for lv in LEVELS}
    ids = [r["unique_id"] for r in rows["edited-BF16"]]
    for k, v in rows.items():
        if sorted(r["unique_id"] for r in v) != sorted(ids):
            fail(f"{k} covers different questions")
    by = {k: {r["unique_id"]: r for r in v} for k, v in rows.items()}
    answers = {}
    for k in rows:
        fl = [by[k][u] for u in ids]
        answers[k] = {"correct": sum(f["correct"] for f in fl), "looping": sum(f["looping"] for f in fl),
                      "median_tokens": f"{median(f['tokens_generated'] for f in fl):,.0f}",
                      "q": "".join("c" if f["correct"] else ("l" if f["looping"] else "w") for f in fl)}
    lost = {}
    for lv in ("Q8_0", "Q4_K_M"):
        ref, cur = by["edited-BF16"], by[f"edited-{lv}"]
        lo = [u for u in ids if ref[u]["correct"] and not cur[u]["correct"]]
        lost[lv] = {"lost": len(lo), "hit_limit": sum(cur[u]["looping"] for u in lo),
                    "gained": sum(1 for u in ids if cur[u]["correct"] and not ref[u]["correct"])}
        lost[lv]["no_right_answer"] = lost[lv]["lost"] - lost[lv]["hit_limit"]
    a = answers
    src_table = md_has(results / "table.md", *[f"| {a[f'edited-{lv}']['looping']}.0% " for lv in LEVELS],
                       *[f"| {a[f'edited-{lv}']['correct']}.0% " for lv in LEVELS],
                       *[f"| {a[f'base-{lv}']['looping']}.0% " for lv in LEVELS])
    src_extra = md_has(results / "extra-checks.md",
                       f"| edited-Q8_0 | {lost['Q8_0']['lost']} | {lost['Q8_0']['hit_limit']} | {lost['Q8_0']['no_right_answer']} |",
                       f"| edited-Q4_K_M | {lost['Q4_K_M']['lost']} | {lost['Q4_K_M']['hit_limit']} | {lost['Q4_K_M']['no_right_answer']} |",
                       f"| edited-BF16 | edited-Q8_0 | correct | {lost['Q8_0']['lost']} | {lost['Q8_0']['gained']} |",
                       f"| edited-BF16 | edited-Q4_K_M | correct | {lost['Q4_K_M']['lost']} | {lost['Q4_K_M']['gained']} |",
                       f"| edited-BF16 | {a['edited-BF16']['median_tokens']} |", f"| edited-Q8_0 | {a['edited-Q8_0']['median_tokens']} |")

    # ---- one real loop, for the opening shot. Chosen by hand: of the original model's answers that ran into the
    # token limit, the plainest-worded repeat (no maths notation) on a question the edited model gets right at all
    # three precisions. Every word shown is copied from the raw response; the script stops if that ever changes.
    loop_uid, loop_line, loop_answer_line = "test/intermediate_algebra/1232.json", "Wait, I am just repeating myself.", "The answer is $5/13$."
    raw = {k: {r["unique_id"]: r for r in map(json.loads, need(results / "raw" / f"{k}.jsonl").read_text().splitlines())}
           for k in ("base-BF16", "edited-BF16")}
    problem = next((json.loads(x) for x in need(ROOT / "data" / "math500_test.jsonl").read_text().splitlines()
                    if json.loads(x)["unique_id"] == loop_uid), None) or fail(f"{loop_uid} not in data/math500_test.jsonl")
    b_r, e_r = raw["base-BF16"][loop_uid], raw["edited-BF16"][loop_uid]
    tail = [x.strip() for x in b_r["response"].splitlines() if x.strip()][-6:]
    if not (b_r["hit_token_limit"] and not by["base-BF16"][loop_uid]["correct"]):
        fail("loop example: the original model no longer runs into the limit on it")
    if not all(by[f"edited-{lv}"][loop_uid]["correct"] for lv in LEVELS) or e_r["hit_token_limit"]:
        fail("loop example: the edited model is no longer right at every precision")
    if loop_line not in tail or loop_answer_line not in tail:
        fail("loop example: the repeated lines are not at the end of the original model's response")
    edited_tail = [x.strip() for x in e_r["response"].splitlines() if x.strip()][-2:]
    loop = {"uid": loop_uid, "problem": problem["problem"], "answer": problem["answer"],
            "line": loop_line, "answer_line": loop_answer_line, "repeats": b_r["response"].count(loop_line),
            "base_tokens": b_r["tokens_generated"], "edited_tokens": e_r["tokens_generated"],
            "edited_tail": edited_tail}

    # ---- bits per weight, from the llama-quantize logs
    bpw = {}
    for lv in ("Q8_0", "Q4_K_M"):
        m = re.search(r"quant size\s*=\s*[\d.]+ MiB \(([\d.]+) BPW\)", need(results / f"quantize-edited-{lv}.log").read_text())
        bpw[lv] = float(m.group(1)) if m else fail(f"no BPW line in quantize-edited-{lv}.log")

    manifest = {
        "about": "Every number the explainer shows. Built by src/site_data.py from the files named in 'sources'.",
        "sources": {
            "model_map": f"models/base/{ST_NAME} (header)", "edit": "models/gguf/*.gguf and models/*/" + ST_NAME,
            "diff": src_diff, "edit_rounding": src_round, "table": src_table, "extra": src_extra,
            "answers": "results/flags/{base,edited}-{BF16,Q8_0,Q4_K_M}.jsonl",
            "bpw": "results/quantize-edited-{Q8_0,Q4_K_M}.log",
            "authors": "README.md (Credit first): 131,072 weights, 0.016%, their figures",
            "loop": "results/raw/{base,edited}-BF16.jsonl (responses), data/math500_test.jsonl (question)",
        },
        "model": {"tensors": len(head), "weights": total, "map": model_map},
        "authors_figure": {"weights": 131072, "share": "0.016%"},
        "edit": {str(k): v for k, v in edit.items()},
        "changed_total": edit[15]["changed"] + edit[19]["changed"],
        "bpw": bpw, "token_limit": 32768,
        "overview": {"pool": POOL, "shape": [1024, 3584], "base_scale": base_scale, "edit_scale": EDIT_SCALE,
                     "files": {"base": "l15-base.png", "16": "l15-edit-16.png", "8": "l15-edit-8.png", "4": "l15-edit-4.png"},
                     "note": "base: root mean square of each 4 x 4 cell, 0 to base_scale; edits: the value with the "
                             "largest size in each 4 x 4 cell, -edit_scale to +edit_scale, 128 = zero"},
        "crop": {"file": "crop.bin", "row0": int(r0), "col0": int(c0), "rows": CROP_ROWS, "cols": CROP_COLS,
                 "order": [f"{m}-{lv}" for m, lv in order], "dtype": "float32 little-endian",
                 "rule": "the 64-row x 256-column window (aligned) holding the largest single change in layer 15"},
        "block": block,
        "answers": answers, "lost": lost, "loop": loop,
        "question_order": "unique_id order of results/flags/edited-BF16.jsonl; q: c correct, l hit the token limit, w finished without the right answer",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(f"wrote {out}: crop rows {r0}+{CROP_ROWS}, cols {c0}+{CROP_COLS}; block row {r_star} cols {b0}+32 "
          f"(edited col {c_star}); edited columns in crop: {sum(c0 <= c < c0 + CROP_COLS for c in edit[15]['columns'])}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
