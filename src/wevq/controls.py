"""Post-hoc control, run after the table was seen: does quantization cost a working model without the edit
as much accuracy as it costs the edited model?

The base model with thinking on scores 14-16% at every precision, too low to show an accuracy drop.
With thinking off it scores 49% at full precision, so it can. This compares the thinking-off rows at
8-bit and 4-bit against full precision, question by question, next to the same comparison for the edited model.

Usage: python -I -m wevq.controls QUESTIONS.jsonl IDS.json RAW_DIR OUT_DIR
Writes OUT_DIR/controls.md and OUT_DIR/flags/control-*.jsonl. A control row that has not been run is reported as such.
"""
import json
import os
import sys

from wevq.questions import load
from wevq.stats import mcnemar_exact
from wevq.table import SHARED, load_row, pct

LEVELS = [("Q8_0", "8-bit"), ("Q4_K_M", "4-bit (Q4_K_M)")]
REFERENCE = "baseline-thinking-off"  # the same model and settings at full precision


def paired(ref: dict, row: dict, ids: list[str], key: str) -> tuple[int, int, float]:
    only_ref = sum(1 for u in ids if ref[u][key] and not row[u][key])
    only_row = sum(1 for u in ids if row[u][key] and not ref[u][key])
    return only_ref, only_row, mcnemar_exact(only_ref, only_row)


def build(questions_path: str, ids_path: str, raw_dir: str, out_dir: str) -> str:
    gold = {q["unique_id"]: q["answer"] for q in load(questions_path)}
    ids = json.load(open(ids_path))["A"]
    both = ids + json.load(open(ids_path))["B"]
    ref = load_row(raw_dir, REFERENCE, both, gold)
    if ref is None or set(ref["flags"]) < set(ids):
        raise SystemExit(f"{REFERENCE} is missing or incomplete in {raw_dir}")
    lines = [
        "# Control: the base model with thinking off, quantized",
        "",
        "Run after the table was seen (post-hoc); not part of the plan agreed before the run. Produced by `python -m wevq.controls`.",
        "Same questions (half A), same settings and llama.cpp build as every other row; thinking off, as in `baseline-thinking-off`.",
        "p-values are exact McNemar, two-sided, not corrected for the number of checks. Brackets are 95% intervals.",
        "",
        "| Row | Questions | Looping | Correct | Correct vs full precision: lost / gained | p |",
        "|---|---|---|---|---|---|",
    ]
    rf = ref["flags"]
    lines.append(f"| thinking off, full precision (`{REFERENCE}`) | {len(ids)} | "
                 f"{pct(sum(rf[u]['looping'] for u in ids), len(ids))} | {pct(sum(rf[u]['correct'] for u in ids), len(ids))} | reference | |")
    os.makedirs(os.path.join(out_dir, "flags"), exist_ok=True)
    edited_ref = load_row(raw_dir, "edited-BF16", both, gold)
    edited_lines = []
    for lv, label in LEVELS:
        name = f"control-thinking-off-{lv}"
        d = load_row(raw_dir, name, both, gold)
        if d is None:
            lines.append(f"| thinking off, {label} | not run | | | | |")
            continue
        missing = [u for u in ids if u not in d["flags"]]
        if missing:
            lines.append(f"| thinking off, {label} | {len(ids) - len(missing)} of {len(ids)}: incomplete, not scored | | | | |")
            continue
        for k in SHARED:
            if d["meta"][k] != ref["meta"][k]:
                raise SystemExit(f"{name}: setting {k} differs from {REFERENCE}")
        fl = d["flags"]
        lost, gained, p = paired(rf, fl, ids, "correct")
        lines.append(f"| thinking off, {label} | {len(ids)} | {pct(sum(fl[u]['looping'] for u in ids), len(ids))} | "
                     f"{pct(sum(fl[u]['correct'] for u in ids), len(ids))} | {lost} / {gained} | {p:.2g} |")
        with open(os.path.join(out_dir, "flags", f"{name}.jsonl"), "w") as f:
            for uid in ids:
                f.write(json.dumps(fl[uid]) + "\n")
        e = load_row(raw_dir, f"edited-{lv}", both, gold)
        if edited_ref is not None and e is not None:
            el, eg, ep = paired(edited_ref["flags"], e["flags"], ids, "correct")
            edited_lines.append(f"| {label} | {sum(rf[u]['correct'] for u in ids)} → {sum(fl[u]['correct'] for u in ids)} "
                                f"(lost {lost}, gained {gained}, p = {p:.2g}) | "
                                f"{sum(edited_ref['flags'][u]['correct'] for u in ids)} → {sum(e['flags'][u]['correct'] for u in ids)} "
                                f"(lost {el}, gained {eg}, p = {ep:.2g}) |")
    if edited_lines:
        lines += ["", "## Next to the edited model (correct answers out of 100, full precision → quantized)", "",
                  "| Level | Base, thinking off | Edited, thinking on |", "|---|---|---|"] + edited_lines
    lines.append("")
    text = "\n".join(lines)
    with open(os.path.join(out_dir, "controls.md"), "w") as f:
        f.write(text)
    return text


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    print(build(*sys.argv[1:]))
