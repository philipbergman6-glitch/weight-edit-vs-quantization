import json

from wevq.table import build

META = {"gguf": "x.gguf", "gguf_bytes": 1, "thinking": True, "max_new_tokens": 32768, "streams": 8, "sampling": {}}


def write_inputs(tmp_path, n=20):
    questions = [{"unique_id": f"q{i}", "answer": str(i)} for i in range(2 * n)]
    (tmp_path / "questions.jsonl").write_text("\n".join(json.dumps(q) for q in questions))
    ids = {"A": [f"q{i}" for i in range(n)], "B": [f"q{i}" for i in range(n, 2 * n)]}
    (tmp_path / "ids.json").write_text(json.dumps(ids))
    (tmp_path / "raw").mkdir()
    return ids


def write_row(tmp_path, name, ids, looping_count, right_count):
    """First `looping_count` questions hit the limit with no answer; of the rest, `right_count` are right."""
    lines = []
    for k, uid in enumerate(ids):
        if k < looping_count:
            rec = {"unique_id": uid, "response": "check. check. check.", "hit_token_limit": True, "tokens_generated": 32768}
        else:
            answer = uid[1:] if k < looping_count + right_count else "-1"
            rec = {"unique_id": uid, "response": f"</think>\\boxed{{{answer}}}", "hit_token_limit": False, "tokens_generated": 1000}
        lines.append(json.dumps(rec))
    (tmp_path / "raw" / f"{name}.jsonl").write_text("\n".join(lines) + "\n")
    (tmp_path / "raw" / f"{name}.meta.json").write_text(json.dumps(META))


def run(tmp_path):
    return build(str(tmp_path / "questions.jsonl"), str(tmp_path / "ids.json"), str(tmp_path / "raw"), str(tmp_path / "out"))


def test_table_reports_rates_reduction_and_verdicts(tmp_path):
    ids = write_inputs(tmp_path)["A"]
    write_row(tmp_path, "base-BF16", ids, 18, 1)        # 90% looping
    write_row(tmp_path, "edited-BF16", ids, 6, 10)      # 30% looping: reduction 60 points
    write_row(tmp_path, "base-Q8_0", ids, 18, 1)
    write_row(tmp_path, "edited-Q8_0", ids, 6, 10)      # same reduction: ratio 1.0
    write_row(tmp_path, "base-Q4_K_M", ids, 18, 1)
    write_row(tmp_path, "edited-Q4_K_M", ids, 17, 2)    # reduction 5 points: ratio about 0.08
    text = run(tmp_path)
    assert "| base, full precision (16-bit) | 20 | 90.0%" in text
    assert "| edited, full precision (16-bit) | 20 | 30.0%" in text
    assert "| full precision (16-bit) | 90.0% | 30.0% | 60.0 | 12 / 0 |" in text and "| reference | valid |" in text
    assert "| 8-bit | 90.0% | 30.0% | 60.0 |" in text and "| survives |" in text
    assert "| 4-bit (stock) | 90.0% | 85.0% | 5.0 |" in text and "| does not survive |" in text
    assert "| base, thinking off | not run |" in text
    flags = [json.loads(line) for line in (tmp_path / "out" / "flags" / "edited-BF16.jsonl").read_text().splitlines()]
    assert len(flags) == 20 and sum(f["correct"] for f in flags) == 10 and "response" not in flags[0]


def test_incomplete_row_is_marked_and_gets_no_verdict(tmp_path):
    ids = write_inputs(tmp_path)["A"]
    write_row(tmp_path, "base-BF16", ids, 18, 1)
    write_row(tmp_path, "edited-BF16", ids[:7], 2, 3)
    text = run(tmp_path)
    assert "(incomplete: 7 of 20)" in text
    assert "| full precision (16-bit) | not complete |" in text


def test_survives_verdicts_are_withheld_when_full_precision_check_fails(tmp_path):
    ids = write_inputs(tmp_path)["A"]
    for name in ("base-BF16", "edited-BF16", "base-Q8_0", "edited-Q8_0"):
        write_row(tmp_path, name, ids, 10, 5)
    text = run(tmp_path)
    assert "NOT VALID" in text and "not reported: full-precision check missing or failed" in text
