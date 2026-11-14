"""Extra paired checks, run after the table was seen. Not part of the plan agreed before the run.

Usage: python -I -m wevq.extra FLAGS_DIR OUT.md
"""
import json
import sys

from wevq.stats import mcnemar_exact

ROWS = ["base-BF16", "edited-BF16", "base-Q8_0", "edited-Q8_0", "base-Q4_K_M", "edited-Q4_K_M",
        "baseline-thinking-off", "baseline-repeat-penalty"]
PAIRS = [("edited-BF16", "edited-Q8_0"), ("edited-BF16", "edited-Q4_K_M"), ("edited-Q8_0", "edited-Q4_K_M"),
         ("edited-BF16", "baseline-thinking-off"), ("base-BF16", "baseline-thinking-off"),
         ("base-BF16", "baseline-repeat-penalty")]


def main(flags_dir: str, out_path: str) -> None:
    rows = {r: {j["unique_id"]: j for j in map(json.loads, open(f"{flags_dir}/{r}.jsonl"))} for r in ROWS}
    ids = set(rows[ROWS[0]])
    for r, flags in rows.items():
        if set(flags) != ids:
            raise SystemExit(f"{r} does not cover the same questions as {ROWS[0]}")
    lines = ["# Extra checks", "",
             "Run after the table was seen; not part of the plan agreed before the run. Produced by `python -m wevq.extra`.",
             f"Questions: {len(ids)}. p-values are exact McNemar, two-sided, not corrected for the number of checks.", "",
             "## Paired comparisons", "", "| A | B | Measure | Only A | Only B | p |", "|---|---|---|---|---|---|"]
    for a, b in PAIRS:
        for key in ("looping", "correct"):
            only_a = sum(1 for u in ids if rows[a][u][key] and not rows[b][u][key])
            only_b = sum(1 for u in ids if rows[b][u][key] and not rows[a][u][key])
            lines.append(f"| {a} | {b} | {key} | {only_a} | {only_b} | {mcnemar_exact(only_a, only_b):.2g} |")
    lines += ["", "## Accuracy among responses that did not loop", "",
              "| Row | Did not loop | Of those, correct | Looped but correct |", "|---|---|---|---|"]
    for r in ROWS:
        fl = rows[r].values()
        ended = sum(not f["looping"] for f in fl)
        right = sum(f["correct"] and not f["looping"] for f in fl)
        lines.append(f"| {r} | {ended} | {right} ({100 * right / ended:.0f}%) | {sum(f['correct'] and f['looping'] for f in fl)} |")
    open(out_path, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
