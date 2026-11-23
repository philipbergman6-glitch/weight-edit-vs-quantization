"""Draw the summary chart from the per-response flags.

Usage: python src/chart.py results/flags results/chart.png
Every bar is counted from results/flags/<row>.jsonl; intervals are Wilson 95%.
"""

import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

LEVELS = [("BF16", "16-bit\n(full precision)"), ("Q8_0", "8-bit"), ("Q4_K_M", "4-bit")]
INK = "#16202b"
MUTED = "#5d6b7a"
BASE = "#aab4c0"
EDITED = "#0b6e75"
GRID = "#dfe4ea"
PAPER = "#fbfcfd"


def load(flags_dir: Path, row: str) -> list[dict]:
    path = flags_dir / f"{row}.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if len(rows) != 100:
        raise ValueError(f"{path}: expected 100 responses, found {len(rows)}")
    return rows


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return 100 * (centre - half), 100 * (centre + half)


def panel(ax, flags_dir: Path, key: str, title: str, note: str) -> None:
    width = 0.36
    for offset, model, colour in ((-width / 2, "base", BASE), (width / 2, "edited", EDITED)):
        for i, (level, _) in enumerate(LEVELS):
            rows = load(flags_dir, f"{model}-{level}")
            k = sum(bool(r[key]) for r in rows)
            lo, hi = wilson(k, len(rows))
            x = i + offset
            ax.bar(x, k, width * 0.94, color=colour, zorder=2)
            ax.plot([x, x], [lo, hi], color=INK, lw=1.3, alpha=0.55, zorder=3)
            ax.text(x, hi + 2.5, f"{k}%", ha="center", va="bottom", fontsize=19,
                    fontweight="bold", color=INK if model == "edited" else MUTED)
    ax.set_xticks(range(len(LEVELS)), [label for _, label in LEVELS], fontsize=15, color=INK)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100], ["0", "25", "50", "75", "100%"], fontsize=12, color=MUTED)
    ax.grid(axis="y", color=GRID, lw=1, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0)
    ax.set_facecolor(PAPER)
    ax.set_title(title, loc="left", fontsize=20, fontweight="bold", color=INK, pad=46)
    ax.text(0, 1.04, note, transform=ax.transAxes, fontsize=13.5, color=MUTED)


def main(flags_dir: Path, out: Path) -> None:
    fig = plt.figure(figsize=(12, 12), dpi=100, facecolor=PAPER)
    fig.text(0.06, 0.945, "The fix survived compression. The accuracy did not.",
             fontsize=25, fontweight="bold", color=INK)
    fig.text(0.06, 0.905,
             "MIT's direct weight edit of Qwen3.5-0.8B, tested at three precision levels.",
             fontsize=16, color=MUTED)
    fig.text(0.06, 0.862, "■", fontsize=18, color=BASE)
    fig.text(0.085, 0.864, "original model", fontsize=15, color=INK)
    fig.text(0.27, 0.862, "■", fontsize=18, color=EDITED)
    fig.text(0.295, 0.864, "edited model", fontsize=15, color=INK)

    left = fig.add_axes((0.07, 0.19, 0.41, 0.54))
    right = fig.add_axes((0.56, 0.19, 0.41, 0.54))
    panel(left, flags_dir, "looping", "Hit the token limit", "the authors' measure of looping · lower is better")
    panel(right, flags_dir, "correct", "Correct answers", "higher is better")

    fig.text(0.06, 0.095,
             "100 MATH-500 questions, one answer each, same settings for every version. Lines: 95% intervals.",
             fontsize=13, color=MUTED)
    fig.text(0.06, 0.065, "Edit: Takehi, Teoh, Zhang, Khattab (MIT CSAIL), 2026.",
             fontsize=13, color=MUTED)
    fig.text(0.06, 0.035,
             "Measurement and raw results: github.com/philipbergman6-glitch/weight-edit-vs-quantization",
             fontsize=13, color=MUTED)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=PAPER)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
