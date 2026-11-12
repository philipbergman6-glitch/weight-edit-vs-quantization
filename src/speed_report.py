"""Turn the speed test JSON files into results/speed.md, with a time budget.

Usage: python -I src/speed_report.py OUT.md IN.json [IN.json ...]
"""
import json
import os
import sys

QUESTIONS = 200
LIMITS = [32768, 16384, 8192, 4096]
# rows of the planned table per precision level: base + edited, plus two baselines at full precision
ROWS_PER_LEVEL = {"BF16": 4, "Q8_0": 2, "Q4_K_M": 2}


def level(path: str) -> str:
    return os.path.basename(path).split("-", 1)[1].removesuffix(".gguf")


def main(out: str, inputs: list[str]) -> None:
    rows = [r for p in inputs for r in json.load(open(p))]
    lines = [
        "# Speed, memory and file size per precision level",
        "",
        "Produced by `src/speed_test.py` and `src/speed_report.py` on an Apple M5 (10 cores, 16 GB), llama.cpp 0.9.0,",
        "all layers on the GPU, running on battery. Base model files; the edited files have the same size and layout.",
        "Each run generated a fixed number of tokens from a neutral prompt with end-of-text ignored.",
        "This measures speed only and says nothing about looping or accuracy.",
        "",
        "| Precision level | File size | Bits per weight | Streams | Tokens generated | Tokens/s per stream | Tokens/s total | Memory footprint |",
        "|---|---|---|---|---|---|---|---|",
    ]
    bpw = {"BF16": "16.01", "Q8_0": "8.52", "Q4_K_M": "5.51"}
    for r in sorted(rows, key=lambda r: (["BF16", "Q8_0", "Q4_K_M"].index(level(r["file"])), r["parallel_slots"])):
        lv = level(r["file"])
        lines.append(
            f"| {lv} | {r['file_size_mb']:.0f} MB | {bpw[lv]} | {r['parallel_slots']} | {r['tokens_generated']:,} | "
            f"{r['tokens_per_second_per_stream']} | {r['tokens_per_second_total']} | {r['memory_after_mb']:,} MB |"
        )
    lines += [
        "",
        "Notes:",
        "",
        "- Bits per weight are from the `llama-quantize` logs (`results/quantize-*.log`). The 4-bit file is a mixed recipe: 5.51 bits per weight on average.",
        "- Memory footprint is the server process's `phys_footprint` after generation, with a 34,816-token context per stream. It does not include the model file itself, which is memory-mapped; add the file size for an upper bound on total memory.",
        "- Speeds were measured over the first 4,096 to 8,192 tokens of a response. Longer responses may be slower per token.",
        "",
        "## Time budget",
        "",
        f"Worst case: {QUESTIONS} questions per row, every response running to the token limit, 8 streams,",
        "using the measured 8-stream totals above. Planned rows: base and edited at each precision level, plus two baselines at full precision (8 rows).",
        "",
        "| Token limit | One BF16 row | One Q8_0 row | One Q4_K_M row | All 8 rows |",
        "|---|---|---|---|---|",
    ]
    rate = {level(r["file"]): r["tokens_per_second_total"] for r in rows if r["parallel_slots"] == 8}
    missing = set(ROWS_PER_LEVEL) - set(rate)
    if missing:
        raise SystemExit(f"no 8-stream measurement for {missing}")
    for limit in LIMITS:
        hours = {lv: QUESTIONS * limit / rate[lv] / 3600 for lv in rate}
        total = sum(hours[lv] * n for lv, n in ROWS_PER_LEVEL.items())
        lines.append(f"| {limit:,} | {hours['BF16']:.1f} h | {hours['Q8_0']:.1f} h | {hours['Q4_K_M']:.1f} h | {total:.0f} h |")
    lines += ["", "Real runs should be shorter: responses that finish early free their stream for the next question.", ""]
    open(out, "w").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2:])
