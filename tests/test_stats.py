import pytest

from wevq.stats import mcnemar_exact, survives_ratio, wilson


def test_wilson_matches_worked_values_for_200_questions():
    # worked in research/math-500-source-and-grading.md: 10% -> 6.57 to 14.94, 50% -> 43.14 to 56.86
    assert wilson(20, 200) == pytest.approx((0.0657, 0.1494), abs=1e-4)
    assert wilson(100, 200) == pytest.approx((0.4314, 0.5686), abs=1e-4)


def test_mcnemar_matches_worked_values():
    assert mcnemar_exact(6, 0) == pytest.approx(0.03125)
    assert mcnemar_exact(5, 0) == pytest.approx(0.0625)
    assert mcnemar_exact(10, 2) == pytest.approx(0.0386, abs=1e-4)
    assert mcnemar_exact(0, 0) == 1.0


def test_survives_ratio_is_one_when_the_level_matches_the_reference():
    base, edited = [1] * 90 + [0] * 10, [1] * 30 + [0] * 70
    ratio, low, high, undefined = survives_ratio(base, edited, base, edited)
    assert undefined == 0 and ratio == pytest.approx(1.0) and low == pytest.approx(1.0) and high == pytest.approx(1.0)


def test_survives_ratio_is_half_when_half_the_reduction_remains():
    base_ref, edited_ref = [1] * 80 + [0] * 20, [1] * 20 + [0] * 80   # reduction 60
    base_lvl, edited_lvl = [1] * 80 + [0] * 20, [1] * 50 + [0] * 50   # reduction 30
    ratio, low, high, _ = survives_ratio(base_ref, edited_ref, base_lvl, edited_lvl)
    assert ratio == pytest.approx(0.5) and low < 0.5 < high


def test_survives_ratio_refuses_when_reference_has_no_reduction():
    with pytest.raises(ValueError):
        survives_ratio([1, 0], [1, 0], [1, 0], [0, 0])


def test_survives_ratio_refuses_flags_that_are_not_0_or_1():
    with pytest.raises(ValueError):
        survives_ratio([2, 0], [0, 0], [1, 0], [0, 0])
