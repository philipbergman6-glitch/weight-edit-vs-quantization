"""Uncertainty for rates and paired comparisons."""
import math
import random

Z95 = 1.959963984540054


def wilson(k: int, n: int) -> tuple[float, float]:
    """Wilson 95% interval for k successes out of n."""
    if n <= 0 or not 0 <= k <= n:
        raise ValueError(f"invalid counts k={k}, n={n}")
    p, z2 = k / n, Z95 * Z95
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    half = Z95 * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value. b and c are the two kinds of disagreeing pairs."""
    if b < 0 or c < 0:
        raise ValueError("counts must be non-negative")
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def survives_ratio(base_ref, edited_ref, base_lvl, edited_lvl, resamples: int = 10000, seed: int = 0):
    """Reduction in looping at a level divided by the reduction at the reference level.

    Each argument is a list of 0/1 looping flags over the same questions in the same order.
    Returns (ratio, low, high) with a 95% paired bootstrap interval over questions.
    """
    n = len(base_ref)
    if not (n == len(edited_ref) == len(base_lvl) == len(edited_lvl)) or n == 0:
        raise ValueError("all four lists must be the same non-zero length")

    def ratio(idx) -> float | None:
        ref = sum(base_ref[i] - edited_ref[i] for i in idx)
        return None if ref == 0 else sum(base_lvl[i] - edited_lvl[i] for i in idx) / ref

    point = ratio(range(n))
    if point is None:
        raise ValueError("no reduction in looping at the reference level; the ratio is undefined")
    rng = random.Random(seed)
    draws = sorted(r for r in (ratio([rng.randrange(n) for _ in range(n)]) for _ in range(resamples)) if r is not None)
    if len(draws) < 0.99 * resamples:
        raise ValueError("reference reduction is too close to zero for a stable interval")
    return point, draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]
