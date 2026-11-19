"""What rounding does to the edit, read from the real quantized files. No model is run.

For each edited tensor, reads base and edited weights from the 16-bit, 8-bit and 4-bit GGUF
files, turns the stored integers back into numbers (dequantize), and compares:
- the edit as stored after rounding (edited minus base, both rounded) against the true edit;
- the rounding error on the edited tensor against the size of the edit;
- the rounding error on the columns the edit did not touch, in the base and in the edited file.

Added after the run (post-hoc), to test the reason given in PREDICTION.md.

Usage: .venv-convert/bin/python -I src/edit_rounding.py models/gguf results/edit-rounding.md
(needs the `gguf` package, installed in .venv-convert)
"""
import sys

import numpy as np
import gguf
from gguf.quants import dequantize

TENSORS = ["blk.15.ffn_down.weight", "blk.19.ffn_down.weight"]
LEVELS = ["Q8_0", "Q4_K_M"]
BLOCK = 32  # every llama.cpp block type used here groups 32 neighbouring weights along a row (Q4_K: sub-blocks of 32)


def load(path: str) -> dict[str, tuple[np.ndarray, str]]:
    out = {}
    for t in gguf.GGUFReader(path).tensors:
        if t.name in TENSORS:
            out[t.name] = (dequantize(t.data, t.tensor_type).astype(np.float64), t.tensor_type.name)
    missing = set(TENSORS) - set(out)
    if missing:
        raise SystemExit(f"{path}: tensors not found: {sorted(missing)}")
    return out


def rel(a: np.ndarray, b: np.ndarray) -> float:
    """norm of a relative to norm of b"""
    return float(np.linalg.norm(a) / np.linalg.norm(b))


def cos(a: np.ndarray, b: np.ndarray) -> float:
    return float((a * b).sum() / (np.linalg.norm(a) * np.linalg.norm(b)))


def main(gguf_dir: str, out_path: str) -> None:
    f = {(m, lv): load(f"{gguf_dir}/{m}-{lv}.gguf") for m in ("base", "edited") for lv in ["BF16"] + LEVELS}
    lines = [
        "# What rounding does to the edit",
        "",
        "Produced by `src/edit_rounding.py` from the GGUF files in `models/gguf/`. No model was run.",
        "Added after the run (post-hoc), to test the reason in `PREDICTION.md` (\"rounding erases the edit itself\").",
        "",
        "Terms: *true edit* = edited minus base at 16-bit. *Stored edit* = edited minus base, both read from the",
        "quantized files. *Rounding error* = quantized weights minus 16-bit weights. Sizes are norms (root of the sum of squares).",
        "",
    ]
    for name in TENSORS:
        Wb, _ = f[("base", "BF16")][name]
        We, _ = f[("edited", "BF16")][name]
        E = We - Wb
        touched = np.abs(E).sum(axis=0) > 0  # columns (inputs) the edit changed
        cols = np.arange(E.shape[1])
        touched_blocks = np.zeros(E.shape[1] // BLOCK, dtype=bool)
        touched_blocks[cols[touched] // BLOCK] = True
        in_touched_block = touched_blocks[cols // BLOCK] & ~touched  # untouched columns sharing a block with an edited one
        lines += [
            f"## `{name}`",
            "",
            f"- Edit size relative to the tensor: {rel(E, Wb):.2%}. Columns touched: {touched.sum()} of {E.shape[1]}.",
            f"- Blocks of {BLOCK} weights per row that contain an edited column: {touched_blocks.sum()} of {touched_blocks.size}.",
            "",
            "| Level | Stored as | Stored edit vs true edit: direction (cosine) | Stored edit vs true edit: size | "
            "Rounding error on edited tensor, relative to the edit | Rounding error, whole tensor: base / edited | "
            "Rounding error, untouched columns in blocks with an edit: base / edited |",
            "|---|---|---|---|---|---|---|",
        ]
        for lv in LEVELS:
            Qb, tb = f[("base", lv)][name]
            Qe, te = f[("edited", lv)][name]
            if tb != te:
                raise SystemExit(f"{name} {lv}: base stored as {tb}, edited as {te}")
            Eq = Qe - Qb
            err_b, err_e = Qb - Wb, Qe - We
            m = in_touched_block
            lines.append(
                f"| {lv} | {te} | {cos(Eq, E):.4f} | {rel(Eq, E):.3f} | {rel(err_e, E):.2%} | "
                f"{rel(err_b, Wb):.2%} / {rel(err_e, We):.2%} | "
                f"{rel(err_b[:, m], Wb[:, m]):.2%} / {rel(err_e[:, m], We[:, m]):.2%} |"
            )
        lines.append("")
    lines += [
        "Reading the table:",
        "",
        "- A cosine near 1 and a size near 1 mean the edit came through rounding intact.",
        "- The last column checks a side effect: each block shares one scale, so a large edited weight can make the",
        "  rounding of its untouched neighbours coarser. If edited > base there, the edit costs precision elsewhere.",
        "- This measures the weights only. It does not show why the edited model's accuracy drops.",
        "",
    ]
    open(out_path, "w").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
