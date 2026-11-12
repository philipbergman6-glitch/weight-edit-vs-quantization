"""Choose the questions: 200 stratified by subject and level, split into two halves of 100.

Usage: python -I -m wevq.questions data/math500_test.jsonl data/question_ids.json
"""
import json
import random
import sys
from collections import defaultdict

SEED = 20261112
TOTAL = 200


def load(path: str) -> list[dict]:
    rows = [json.loads(line) for line in open(path)]
    for r in rows:
        for key in ("problem", "answer", "subject", "level", "unique_id"):
            if key not in r:
                raise ValueError(f"question missing {key!r}")
    if len({r["unique_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate unique_id in question file")
    return rows


def select(rows: list[dict], total: int = TOTAL, seed: int = SEED) -> dict[str, list[str]]:
    """Proportional allocation per (subject, level) by largest remainder; halves alternate within strata."""
    strata: dict[tuple, list[str]] = defaultdict(list)
    for r in rows:
        strata[(r["subject"], r["level"])].append(r["unique_id"])
    keys = sorted(strata)
    exact = {k: len(strata[k]) * total / len(rows) for k in keys}
    take = {k: int(exact[k]) for k in keys}
    for k in sorted(keys, key=lambda k: (-(exact[k] - take[k]), k))[: total - sum(take.values())]:
        take[k] += 1
    rng = random.Random(seed)
    halves: dict[str, list[str]] = {"A": [], "B": []}
    for k in keys:
        chosen = rng.sample(sorted(strata[k]), take[k])
        for uid in chosen:
            halves["A" if len(halves["A"]) <= len(halves["B"]) else "B"].append(uid)
    if len(halves["A"]) != total // 2 or len(halves["B"]) != total // 2:
        raise ValueError("halves are not equal in size")
    return halves


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    halves = select(load(sys.argv[1]))
    json.dump({"seed": SEED, "total": TOTAL, "source": "HuggingFaceH4/MATH-500 test @ 6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be",
               **halves}, open(sys.argv[2], "w"), indent=1)
    print({k: len(v) for k, v in halves.items()})
