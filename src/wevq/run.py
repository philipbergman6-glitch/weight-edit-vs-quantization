"""Run one row of the table: one model file, one question list, fixed settings.

Starts llama-server, renders each prompt with the model's chat template, generates
one response per question on parallel streams, and appends each finished response
to a JSONL file. Re-running skips questions already in the file.

Usage:
  python -I -m wevq.run ROW GGUF QUESTIONS.jsonl IDS.json HALF [--thinking-off] [--repeat-penalty X] [--limit N] [--max-tokens N]

ROW is the row name used for output files, for example `edited-Q4_K_M` or `baseline-thinking-off`.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PORT = 8097
STREAMS = 8
CONTEXT_PER_STREAM = 34816
MAX_NEW_TOKENS = 32768
INSTRUCTION = "Please reason step by step, and put your final answer within \\boxed{}."
SAMPLING = {
    "temperature": 0.6,
    "top_k": 20,
    "top_p": 0.95,
    "min_p": 0.0,
    "presence_penalty": 1.5,
    "frequency_penalty": 0.0,
    "repeat_penalty": 1.0,
    "repeat_last_n": CONTEXT_PER_STREAM,
    "samplers": ["penalties", "temperature", "top_k", "top_p"],
    "seed": 0,
}
# settings the server must echo back unchanged for a response to be accepted
CHECKED = ["temperature", "top_k", "top_p", "min_p", "presence_penalty", "frequency_penalty",
           "repeat_penalty", "repeat_last_n", "samplers", "seed"]


def call(path: str, body: dict | None = None, timeout: float = 4 * 3600) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def start_server(gguf: str, log_path: str) -> subprocess.Popen:
    cmd = ["llama-server", "-m", gguf, "--offline", "--host", "127.0.0.1", "--port", str(PORT), "-ngl", "all",
           "-c", str(CONTEXT_PER_STREAM * STREAMS), "-np", str(STREAMS), "--no-context-shift", "--jinja"]
    proc = subprocess.Popen(cmd, stdout=open(log_path, "w"), stderr=subprocess.STDOUT)
    for _ in range(600):
        if proc.poll() is not None:
            raise SystemExit(f"llama-server exited early with code {proc.returncode}; see {log_path}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                if r.status == 200:
                    return proc
        except OSError:
            time.sleep(0.5)
    proc.terminate()
    raise SystemExit("llama-server did not become ready")


def close_enough(sent, got) -> bool:
    if isinstance(sent, float) or isinstance(got, float):
        return abs(float(sent) - float(got)) < 1e-6
    return sent == got


def generate(question: dict, thinking: bool, sampling: dict, max_tokens: int) -> dict:
    messages = [{"role": "user", "content": f"{question['problem']}\n{INSTRUCTION}"}]
    prompt = call("/apply-template", {"messages": messages, "chat_template_kwargs": {"enable_thinking": thinking}})["prompt"]
    expected_tail = "<think>\n" if thinking else "<think>\n\n</think>\n\n"
    if not prompt.endswith(expected_tail):
        raise RuntimeError(f"prompt does not end as expected for thinking={thinking}: {prompt[-60:]!r}")
    out = call("/completion", {"prompt": prompt, "n_predict": max_tokens, "cache_prompt": False, **sampling})
    echoed = out["generation_settings"]
    for key in CHECKED:
        if not close_enough(sampling[key], echoed[key]):
            raise RuntimeError(f"server used {key}={echoed[key]!r}, requested {sampling[key]!r}")
    if out["stop_type"] not in ("limit", "eos"):
        raise RuntimeError(f"unexpected stop_type {out['stop_type']!r}")
    if out["truncated"]:
        raise RuntimeError("the context was truncated")
    hit_limit = out["stop_type"] == "limit"
    if hit_limit != (out["tokens_predicted"] >= max_tokens):
        raise RuntimeError(f"stop_type {out['stop_type']!r} disagrees with tokens_predicted {out['tokens_predicted']}")
    return {
        "unique_id": question["unique_id"],
        "response": out["content"],
        "tokens_generated": out["tokens_predicted"],
        "prompt_tokens": out["tokens_evaluated"],
        "hit_token_limit": hit_limit,
        "stop_type": out["stop_type"],
        "seconds": round(out["timings"]["predicted_ms"] / 1000, 1),
        "tokens_per_second": round(out["timings"]["predicted_per_second"], 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("row")
    ap.add_argument("gguf")
    ap.add_argument("questions")
    ap.add_argument("ids")
    ap.add_argument("half", choices=["A", "B"])
    ap.add_argument("--thinking-off", action="store_true")
    ap.add_argument("--repeat-penalty", type=float, default=SAMPLING["repeat_penalty"])
    ap.add_argument("--limit", type=int, default=None, help="only the first N questions of the half (smoke tests)")
    ap.add_argument("--max-tokens", type=int, default=MAX_NEW_TOKENS)
    ap.add_argument("--out-dir", default="results/raw")
    args = ap.parse_args()

    by_id = {q["unique_id"]: q for q in map(json.loads, open(args.questions))}
    ids = json.load(open(args.ids))[args.half][: args.limit]
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise SystemExit(f"{len(missing)} question ids not in the question file, e.g. {missing[0]}")
    sampling = {**SAMPLING, "repeat_penalty": args.repeat_penalty}
    thinking = not args.thinking_off

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, f"{args.row}.jsonl")
    meta_path = os.path.join(args.out_dir, f"{args.row}.meta.json")
    meta = {"row": args.row, "gguf": args.gguf, "gguf_bytes": os.path.getsize(args.gguf), "thinking": thinking,
            "max_new_tokens": args.max_tokens, "sampling": sampling, "streams": STREAMS,
            "context_per_stream": CONTEXT_PER_STREAM, "instruction": INSTRUCTION}
    if os.path.exists(meta_path):
        old = json.load(open(meta_path))
        if {k: old.get(k) for k in meta} != meta:
            raise SystemExit(f"{meta_path} was written with different settings; refusing to mix runs in one file")
    done = set()
    if os.path.exists(out_path):
        done = {json.loads(line)["unique_id"] for line in open(out_path)}
    todo = [i for i in ids if i not in done]
    print(f"[{args.row}] half {args.half}: {len(ids)} questions, {len(done & set(ids))} already done, {len(todo)} to run", flush=True)
    if not todo:
        return

    awake = subprocess.Popen(["caffeinate", "-i", "-m", "-s", "-w", str(os.getpid())])
    server = start_server(args.gguf, os.path.join(args.out_dir, f"{args.row}.server.log"))
    try:
        props = call("/props", timeout=30)
        meta["server_build"] = props.get("build_info")
        json.dump(meta, open(meta_path, "w"), indent=1)
        lock, started, count = threading.Lock(), time.time(), [0]

        def work(uid: str) -> None:
            record = generate(by_id[uid], thinking, sampling, args.max_tokens)
            with lock:
                with open(out_path, "a") as f:
                    f.write(json.dumps(record) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                count[0] += 1
                elapsed = time.time() - started
                eta = elapsed / count[0] * (len(todo) - count[0]) / 3600
                print(f"[{args.row}] {count[0]}/{len(todo)} {uid} tokens={record['tokens_generated']} "
                      f"limit={record['hit_token_limit']} elapsed={elapsed / 3600:.2f}h eta={eta:.2f}h", flush=True)

        with ThreadPoolExecutor(STREAMS) as pool:
            for future in [pool.submit(work, uid) for uid in todo]:
                future.result()
    finally:
        server.terminate()
        server.wait(timeout=60)
        awake.terminate()


if __name__ == "__main__":
    main()
