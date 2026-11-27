"""Correct answers by token budget: how many questions a row answers correctly within N generated tokens.

Post-hoc check, added after the table was seen (a LinkedIn commenter asked for it). A question counts at budget N
when its response is correct and its whole length is at most N tokens. This uses total response length, not the
token where the answer first appeared, so it is a lower bound at each budget below the row's own limit.

Rows from `results/flags/` end at 32,768 tokens. Rows from `results/flags-64k/` (written by `wevq.extend`)
replace every response that hit the 32,768 limit with its continuation to 65,536 tokens.

Usage: python -I -m wevq.budget FLAGS_DIR [FLAGS_64K_DIR] OUT.md
"""
import json
import os
import sys

ROWS = ["edited-BF16", "edited-Q8_0"]
BUDGETS_32K = [4000, 8000, 12000, 16000, 20000, 24000, 28000, 32768]
BUDGETS_64K = BUDGETS_32K + [40000, 48000, 56000, 65536]


def load(path: str) -> dict:
    rows = {j["unique_id"]: j for j in map(json.loads, open(path))}
    if len(rows) != 100:
        raise SystemExit(f"{path}: expected 100 questions, found {len(rows)}")
    return rows


def curve(flags: dict, budgets: list[int]) -> list[int]:
    return [sum(1 for f in flags.values() if f["correct"] and f["tokens_generated"] <= b) for b in budgets]


def table(title: str, data: dict, budgets: list[int], limit: int) -> list[str]:
    lines = [f"## {title}", "", "| Token budget | " + " | ".join(data) + " | Gap |",
             "|---|" + "---|" * (len(data) + 1)]
    cols = {r: curve(f, budgets) for r, f in data.items()}
    for i, b in enumerate(budgets):
        vals = [cols[r][i] for r in data]
        lines.append(f"| {b:,} | " + " | ".join(map(str, vals)) + f" | {vals[0] - vals[1]} |")
    still = {r: sum(f["tokens_generated"] >= limit for f in d.values()) for r, d in data.items()}
    lines += ["", "Still at the limit: " + ", ".join(f"{r} {n}" for r, n in still.items()) + "."]
    pending = {r: sum(bool(f.get("pending")) for f in d.values()) for r, d in data.items()}
    if any(pending.values()):
        lines.append("Not yet continued (stuck repeating; kept at their 32,768-token result): "
                     + ", ".join(f"{r} {n}" for r, n in pending.items()) + ".")
    lines.append("")
    return lines


def paired(data: dict, limit: int) -> list[str]:
    """Question-by-question comparison of the two rows at the final budget."""
    first, second = ROWS
    a, b = data[first], data[second]
    if set(a) != set(b):
        raise SystemExit("the two rows do not hold the same questions")
    only_a = [u for u in a if a[u]["correct"] and not b[u]["correct"]]
    only_b = [u for u in a if b[u]["correct"] and not a[u]["correct"]]
    at_limit = sum(b[u]["tokens_generated"] >= limit for u in only_a)
    return [f"Same question, both rows, at {limit:,} tokens: right only at {first} {len(only_a)}, "
            f"right only at {second} {len(only_b)}.",
            f"Of the {len(only_a)} right only at {first}: {second} was still at the limit on {at_limit} "
            f"and finished with a wrong answer on {len(only_a) - at_limit}.", ""]


def stuck(data: dict, limit: int) -> list[str]:
    """Responses that were already repeating themselves at the old limit (`wevq.extend.is_stuck`)."""
    parts = []
    for row, flags in data.items():
        cont = [f for f in flags.values() if "stuck_at_old_limit" in f]
        if not cont:
            raise SystemExit(f"{row}: no `stuck_at_old_limit` flags; re-run `wevq.extend` to rewrite the flags")
        s = [f for f in cont if f["stuck_at_old_limit"]]
        parts.append(f"{row} {len(s)} of {len(cont)} continued (ended on their own "
                     f"{sum(f['tokens_generated'] < limit for f in s)}, correct {sum(f['correct'] for f in s)})")
    return ["Already stuck repeating at 32,768 tokens: " + "; ".join(parts) + ".", ""]


def main(argv: list[str]) -> None:
    if len(argv) not in (2, 3):
        raise SystemExit(__doc__)
    flags_dir, out_path = argv[0], argv[-1]
    lines = ["# Correct answers by token budget", "",
             "Post-hoc, added after the table was seen. Produced by `python -m wevq.budget`. Edited model, one response per question,",
             "100 questions. A question counts at a budget when its response is correct and no longer than that budget.", ""]
    lines += table("Up to the original 32,768-token limit", {r: load(f"{flags_dir}/{r}.jsonl") for r in ROWS},
                   BUDGETS_32K, 32768)
    if len(argv) == 3:
        ext = argv[1]
        data = {r: load(f"{ext}/{r}.jsonl") for r in ROWS if os.path.exists(f"{ext}/{r}.jsonl")}
        if list(data) != ROWS:
            raise SystemExit(f"{ext} must hold every row: {ROWS}")
        lines += table("Responses that hit the limit, continued to 65,536 tokens", data, BUDGETS_64K, 65536)
        lines += paired(data, 65536) + stuck(data, 65536)
    open(out_path, "w").write("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:])
