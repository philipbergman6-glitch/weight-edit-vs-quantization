import pathlib
from collections import Counter

import pytest

from wevq.questions import load, select

SOURCE = pathlib.Path("data/math500_test.jsonl")
pytestmark = pytest.mark.skipif(not SOURCE.exists(), reason="question file not downloaded")


def test_selection_is_deterministic_disjoint_and_two_halves_of_100():
    rows = load(str(SOURCE))
    first, second = select(rows), select(rows)
    assert first == second
    assert len(first["A"]) == len(first["B"]) == 100
    assert not set(first["A"]) & set(first["B"])


def test_each_half_matches_the_full_sets_level_mix_within_five_points():
    rows = load(str(SOURCE))
    level = {r["unique_id"]: r["level"] for r in rows}
    full = Counter(level.values())
    for half in select(rows).values():
        mix = Counter(level[u] for u in half)
        for lv, count in full.items():
            assert abs(mix[lv] / len(half) - count / len(rows)) <= 0.05
