"""Score the recorded responses and write the flags files and the results table.

Usage: python -I -m wevq.table QUESTIONS.jsonl IDS.json RAW_DIR OUT_DIR

Reads RAW_DIR/<row>.jsonl and <row>.meta.json for every row that exists, writes
OUT_DIR/flags/<row>.jsonl (no response text) and OUT_DIR/table.md. Rows that are
missing or incomplete are shown as such; nothing is estimated.
"""
import json
import os
import sys

from wevq.questions import load
from wevq.scoring import score_response
from wevq.stats import mcnemar_exact, survives_ratio, wilson

LEVELS = [("BF16", "full precision (16-bit)"), ("Q8_0", "8-bit"), ("Q4_K_M", "4-bit (Q4_K_M)")]
BASELINES = [("baseline-thinking-off", "base, thinking off"), ("baseline-repeat-penalty", "base, repetition penalty")]
# settings that must be identical for every version
SHARED = ["thinking", "max_new_tokens", "sampling", "streams", "context_per_stream", "instruction", "server_build"]


def load_row(raw_dir: str, row: str, ids: list[str], gold: dict[str, str]) -> dict | None:
    path = os.path.join(raw_dir, f"{row}.jsonl")
    if not os.path.exists(path):
        return None
    meta_path = os.path.join(raw_dir, f"{row}.meta.json")
    if not os.path.exists(meta_path):
        raise SystemExit(f"{path} exists without {meta_path}; its settings are unknown")
    records = {}
    for number, line in enumerate(open(path), 1):
        try:
            r = json.loads(line)
            uid = r["unique_id"]
        except (ValueError, KeyError) as e:
            raise SystemExit(f"{path} line {number} is not a complete record ({e})")
        if uid in records:
            raise SystemExit(f"{row}: duplicate record for {uid}")
        if uid not in ids:
            raise SystemExit(f"{row}: record for {uid}, which is not in the question id lists")
        records[uid] = r
    flags = {}
    for uid in ids:
        if uid in records:
            r = records[uid]
            f = score_response(r["response"], r["hit_token_limit"], gold[uid])
            flags[uid] = {"unique_id": uid, "looping": f.looping, "has_answer": f.has_answer,
                          "looping_without_answer": f.looping_without_answer, "correct": f.correct,
                          "predicted": f.predicted, "gold": gold[uid], "tokens_generated": r["tokens_generated"]}
    return {"row": row, "flags": flags, "meta": json.load(open(meta_path))}


def check_same_settings(loaded: dict[str, dict | None]) -> None:
    """Every version must have run with identical settings; each baseline may differ in its one setting only."""
    core = {name: d["meta"] for name, d in loaded.items() if d is not None and not name.startswith("baseline-")}
    if not core:
        return
    first_name, first = next(iter(core.items()))
    reference = {k: first[k] for k in SHARED}
    for name, meta in core.items():
        for k in SHARED:
            if meta[k] != reference[k]:
                raise SystemExit(f"{name} ran with {k}={meta[k]!r} but {first_name} ran with {reference[k]!r}")
    for name, key in (("baseline-thinking-off", "thinking"), ("baseline-repeat-penalty", "sampling")):
        if loaded[name] is None:
            continue
        meta = loaded[name]["meta"]
        for k in SHARED:
            if k != key and meta[k] != reference[k]:
                raise SystemExit(f"{name} ran with {k}={meta[k]!r} but {first_name} ran with {reference[k]!r}")
        if key == "thinking" and meta["thinking"] is not False:
            raise SystemExit(f"{name} did not run with thinking off")
        if key == "sampling":
            rest = lambda sampling: {k: v for k, v in sampling.items() if k != "repeat_penalty"}
            if rest(meta["sampling"]) != rest(reference["sampling"]) or meta["sampling"]["repeat_penalty"] <= 1.0:
                raise SystemExit(f"{name} must differ from the versions in the repetition penalty only")


def pct(k: int, n: int) -> str:
    low, high = wilson(k, n)
    return f"{100 * k / n:.1f}% ({100 * low:.0f}-{100 * high:.0f})"


def summary_line(label: str, data: dict | None, ids: list[str]) -> str:
    if data is None or not data["flags"]:
        return f"| {label} | not run | | | | |"
    fl = list(data["flags"].values())
    n = len(fl)
    # long responses finish last, so a part-finished row under-counts looping
    note = "" if n == len(ids) else f" (incomplete: {n} of {len(ids)}; looping reads low until complete)"
    mean_tokens = sum(f["tokens_generated"] for f in fl) / n
    return (f"| {label}{note} | {n} | {pct(sum(f['looping'] for f in fl), n)} | "
            f"{pct(sum(f['looping_without_answer'] for f in fl), n)} | {pct(sum(f['correct'] for f in fl), n)} | {mean_tokens:,.0f} |")


def build(questions_path: str, ids_path: str, raw_dir: str, out_dir: str) -> str:
    gold = {q["unique_id"]: q["answer"] for q in load(questions_path)}
    id_file = json.load(open(ids_path))
    names = [f"{m}-{lv}" for lv, _ in LEVELS for m in ("base", "edited")] + [b for b, _ in BASELINES]
    # the table covers half A alone unless all six versions have also finished half B
    ids = id_file["A"]
    both = id_file["A"] + id_file["B"]
    loaded = {name: load_row(raw_dir, name, both, gold) for name in names}
    check_same_settings(loaded)
    core = [loaded[f"{m}-{lv}"] for lv, _ in LEVELS for m in ("base", "edited")]
    if all(d is not None and len(d["flags"]) == len(both) for d in core):
        ids = both
    keep = set(ids)
    rows: dict[str, dict | None] = {}
    for name in names:
        d = loaded[name]
        if d is not None:
            d["flags"] = {u: f for u, f in d["flags"].items() if u in keep}
        rows[name] = d

    os.makedirs(os.path.join(out_dir, "flags"), exist_ok=True)
    for name, d in rows.items():
        if d is not None:
            with open(os.path.join(out_dir, "flags", f"{name}.jsonl"), "w") as f:
                for uid in ids:
                    if uid in d["flags"]:
                        f.write(json.dumps(d["flags"][uid]) + "\n")

    lines = ["# Results", "",
             f"Questions: {len(ids)} from MATH-500 (id lists in `data/question_ids.json`). One response per question.",
             "Looping = the response hit the token limit. Intervals are Wilson 95%.",
             "Produced by `python -m wevq.table`; per-response flags are in `results/flags/`.", "",
             "| Version | Questions | Looping | Looping without an answer | Accuracy | Mean tokens |", "|---|---|---|---|---|---|"]
    for lv, lv_label in LEVELS:
        for m in ("base", "edited"):
            lines.append(summary_line(f"{m}, {lv_label}", rows[f"{m}-{lv}"], ids))
    for b, b_label in BASELINES:
        if b == "baseline-repeat-penalty" and rows[b] is not None:
            b_label += f" {rows[b]['meta']['sampling']['repeat_penalty']}"
        lines.append(summary_line(b_label, rows[b], ids))

    def paired(lv: str):
        b, e = rows[f"base-{lv}"], rows[f"edited-{lv}"]
        if b is None or e is None or len(b["flags"]) != len(ids) or len(e["flags"]) != len(ids):
            return None
        return [int(b["flags"][u]["looping"]) for u in ids], [int(e["flags"][u]["looping"]) for u in ids]

    lines += ["", "## Reduction in looping, base vs edited at each precision level", "",
              "| Precision level | Base looping | Edited looping | Reduction (points) | Only base loops / only edited loops | McNemar p | Survives ratio (95% interval) | Verdict |",
              "|---|---|---|---|---|---|---|---|"]
    ref = paired("BF16")
    valid = False
    undefined_total = 0
    for lv, lv_label in LEVELS:
        pr = paired(lv)
        if pr is None:
            lines.append(f"| {lv_label} | not complete | | | | | | |")
            continue
        base, edited = pr
        n = len(base)
        only_base = sum(1 for x, y in zip(base, edited) if x and not y)
        only_edited = sum(1 for x, y in zip(base, edited) if y and not x)
        p = mcnemar_exact(only_base, only_edited)
        reduction = 100 * (sum(base) - sum(edited)) / n
        if lv == "BF16":
            valid = p < 0.05 and reduction > 0
            ratio_text, verdict = "reference", "valid" if valid else "NOT VALID: edited does not loop clearly less"
        elif ref is None or not valid:
            ratio_text, verdict = "n/a", "not reported: full-precision check missing or failed"
        else:
            ratio, low, high, undefined = survives_ratio(ref[0], ref[1], base, edited)
            undefined_total += undefined
            ratio_text = f"{ratio:.2f} ({low:.2f}-{high:.2f})"
            verdict = "cannot be called" if low < 0.5 <= high else ("survives" if ratio >= 0.5 else "does not survive")
        lines.append(f"| {lv_label} | {100 * sum(base) / n:.1f}% | {100 * sum(edited) / n:.1f}% | {reduction:.1f} | "
                     f"{only_base} / {only_edited} | {p:.2g} | {ratio_text} | {verdict} |")

    lines += ["", "Survives ratio = reduction at that level divided by the reduction at full precision; "
              "the interval is a paired bootstrap over questions (10,000 resamples). "
              "Verdict: survives if the ratio is at least 0.5; \"cannot be called\" if the interval contains 0.5."]
    if undefined_total:
        lines.append(f"{undefined_total} bootstrap resamples had no full-precision reduction and were left out of the intervals.")
    lines += ["", "## Settings", ""]
    for name, d in rows.items():
        if d is not None:
            m = d["meta"]
            lines.append(f"- `{name}`: `{m['gguf']}` ({m['gguf_bytes']:,} bytes), thinking {'on' if m['thinking'] else 'off'}, "
                         f"max {m['max_new_tokens']:,} new tokens, {m['streams']} streams, llama.cpp build `{m['server_build']}`, sampling `{json.dumps(m['sampling'])}`")
    lines.append("")
    text = "\n".join(lines)
    with open(os.path.join(out_dir, "table.md"), "w") as f:
        f.write(text)
    return text


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    print(build(*sys.argv[1:]))
