"""Continue every response of one row that hit the 32,768-token limit, up to 65,536 tokens in total.

Post-hoc, added after the table was seen. The saved response text is appended to the original prompt and the
model keeps generating with the same sampler. llama-server feeds the whole prompt, saved text included, through
the penalty sampler before generating (`server-context.cpp`, `init_sampler`), so a continuation is the same
process as one longer run; only the random draws differ. The penalty window is widened to the new context so it
still covers the whole response, as in the original runs.

Writes OUT_DIR/raw-64k/ROW.jsonl (continuations, resumable) and OUT_DIR/flags-64k/ROW.jsonl (all 100 questions:
responses that ended on their own are copied from the original flags, continued ones are rescored).

Usage: python -I -m wevq.extend ROW GGUF QUESTIONS.jsonl [--out-dir results]
"""
import argparse
import json
import os
import re
import subprocess
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor

from wevq import run
from wevq.questions import load
from wevq.scoring import score_response

OLD_LIMIT = run.MAX_NEW_TOKENS
EXTRA_TOKENS = 32768
NEW_LIMIT = OLD_LIMIT + EXTRA_TOKENS
CONTEXT_PER_STREAM = run.CONTEXT_PER_STREAM + EXTRA_TOKENS
SAMPLING = {**run.SAMPLING, "repeat_last_n": CONTEXT_PER_STREAM}
# the saved text is tokenized again; allow a small drift from the original token count, fail beyond it
MAX_RETOKENIZE_DRIFT = 0.01


STREAMS = 2  # 8 streams of 67k context froze the 16 GB laptop on 2026-11-26; 3 tripped the memory guard
MIN_FREE_PERCENT = 15  # memory guard: stop the server below this system-wide free percentage
MAX_SWAP_GROWTH_MB = 4096  # memory guard: or once swap use grows this much above its level at start
# (an absolute 1 GB swap cap stopped a healthy run at 23% free on 2026-11-26; swap does not shrink after)


STREAMS_BY_LEVEL = {"Q8_0": 3}  # the 8-bit file is 0.7 GB smaller, so it fits one more stream


def streams_for(gguf: str) -> int:
    return next((n for level, n in STREAMS_BY_LEVEL.items() if level in os.path.basename(gguf)), STREAMS)


# settings that change what the model generates; the stream count only changes speed
SAME_RUN_KEYS = ["row", "gguf", "gguf_bytes", "old_limit", "new_limit", "sampling", "context_per_stream", "server_build"]


def server_command(gguf: str) -> list[str]:
    streams = streams_for(gguf)
    cmd = run.server_command(gguf, True, SAMPLING)
    cmd[cmd.index("-c") + 1] = str(CONTEXT_PER_STREAM * streams)
    cmd[cmd.index("-np") + 1] = str(streams)
    return cmd


# Run order only, nothing is skipped: a response whose last 20,000 characters compress more than this ratio is
# stuck repeating itself (normal reasoning compresses about 5x) and is continued after the others.
STUCK_RATIO = 20.0
STUCK_TAIL_CHARS = 20000


def is_stuck(response: str) -> bool:
    tail = response[-STUCK_TAIL_CHARS:].encode()
    return len(tail) / len(zlib.compress(tail)) > STUCK_RATIO


def memory_state() -> tuple[int, float]:
    """System-wide free memory percentage (macOS `memory_pressure`) and swap used in MB."""
    out = subprocess.run(["memory_pressure", "-Q"], capture_output=True, text=True, check=True).stdout
    free = int(re.search(r"free percentage: (\d+)%", out).group(1))
    swap = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True, check=True).stdout
    used = float(re.search(r"used = ([\d.]+)M", swap).group(1))
    return free, used


def guard(server: subprocess.Popen, log_path: str) -> None:
    """Kill the server and exit hard if memory runs low, before the machine freezes."""
    swap_at_start = memory_state()[1]
    while server.poll() is None:
        free, swap = memory_state()
        if free < MIN_FREE_PERCENT or swap - swap_at_start > MAX_SWAP_GROWTH_MB:
            msg = f"MEMORY GUARD: free {free}%, swap {swap:.0f} MB; stopping the server. Re-run to resume."
            print(msg, flush=True)
            open(log_path, "a").write(msg + "\n")
            server.kill()
            os._exit(3)
        time.sleep(2)


def extend(question: dict, original: dict) -> dict:
    messages = [{"role": "user", "content": f"{question['problem']}\n{run.INSTRUCTION}"}]
    prompt = run.call("/apply-template", {"messages": messages, "chat_template_kwargs": {"enable_thinking": True}})["prompt"]
    if not prompt.endswith("<think>\n"):
        raise RuntimeError(f"prompt does not end as expected: {prompt[-60:]!r}")
    out = run.call("/completion", {"prompt": prompt + original["response"], "n_predict": EXTRA_TOKENS,
                                   "cache_prompt": False, **SAMPLING}, timeout=8 * 3600)
    echoed = out["generation_settings"]
    for key in run.CHECKED:
        if not run.close_enough(SAMPLING[key], echoed[key]):
            raise RuntimeError(f"server used {key}={echoed[key]!r}, requested {SAMPLING[key]!r}")
    if out["stop_type"] not in ("limit", "eos") or out["truncated"]:
        raise RuntimeError(f"unexpected stop: {out['stop_type']!r}, truncated={out['truncated']}")
    retokenized = out["tokens_evaluated"] - original["prompt_tokens"]
    if abs(retokenized - original["tokens_generated"]) > MAX_RETOKENIZE_DRIFT * original["tokens_generated"]:
        raise RuntimeError(f"{question['unique_id']}: saved text re-tokenized to {retokenized} tokens, "
                           f"originally {original['tokens_generated']}")
    hit_limit = out["stop_type"] == "limit"
    if hit_limit != (out["tokens_predicted"] >= EXTRA_TOKENS):
        raise RuntimeError(f"stop_type {out['stop_type']!r} disagrees with tokens_predicted {out['tokens_predicted']}")
    return {"unique_id": question["unique_id"], "continuation": out["content"],
            "original_tokens": original["tokens_generated"], "retokenized_tokens": retokenized,
            "new_tokens": out["tokens_predicted"], "tokens_generated": original["tokens_generated"] + out["tokens_predicted"],
            "hit_token_limit": hit_limit, "stop_type": out["stop_type"],
            "seconds": round(out["timings"]["predicted_ms"] / 1000, 1)}


def write_flags(row: str, out_dir: str, by_id: dict, originals: dict, cont_path: str, partial: bool) -> None:
    """Continued responses are rescored; with `partial`, any not yet continued keep their 32,768-token flags
    and are marked `"pending": true`."""
    conts = {c["unique_id"]: c for c in map(json.loads, open(cont_path))}
    old_flags = {f["unique_id"]: f for f in map(json.loads, open(os.path.join(out_dir, "flags", f"{row}.jsonl")))}
    capped = {u for u, o in originals.items() if o["hit_token_limit"]}
    if set(conts) - capped:
        raise SystemExit(f"[{row}] continuations for responses that did not hit the limit")
    if set(conts) != capped and not partial:
        raise SystemExit(f"[{row}] {len(capped - set(conts))} continuations missing; re-run to finish them")
    os.makedirs(os.path.join(out_dir, "flags-64k"), exist_ok=True)
    with open(os.path.join(out_dir, "flags-64k", f"{row}.jsonl"), "w") as f:
        for uid, old in old_flags.items():
            if uid in conts:
                c, gold = conts[uid], old["gold"]
                s = score_response(originals[uid]["response"] + c["continuation"], c["hit_token_limit"], gold)
                old = {"unique_id": uid, "looping": s.looping, "has_answer": s.has_answer,
                       "looping_without_answer": s.looping_without_answer, "correct": s.correct,
                       "predicted": s.predicted, "gold": gold, "tokens_generated": c["tokens_generated"],
                       "stuck_at_old_limit": is_stuck(originals[uid]["response"])}
            elif uid in capped:
                old = {**old, "pending": True}
            f.write(json.dumps(old) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("row")
    ap.add_argument("gguf")
    ap.add_argument("questions")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--group", choices=["reasoning", "stuck", "all"], default="all",
                    help="continue only responses still reasoning, only stuck ones, or all (see is_stuck)")
    args = ap.parse_args()

    hold = os.path.join(args.out_dir, "raw-64k", "HOLD")
    if args.group == "stuck" and os.path.exists(hold):
        print(f"[{args.row}] phase 2 (stuck) is on hold: delete {hold} and re-run src/run_64k.sh to start it", flush=True)
        raise SystemExit(4)
    by_id = {q["unique_id"]: q for q in load(args.questions)}
    originals = {r["unique_id"]: r for r in map(json.loads, open(os.path.join(args.out_dir, "raw", f"{args.row}.jsonl")))}
    if len(originals) != 100:
        raise SystemExit(f"[{args.row}] expected 100 original responses, found {len(originals)}")
    raw_dir = os.path.join(args.out_dir, "raw-64k")
    os.makedirs(raw_dir, exist_ok=True)
    out_path, meta_path = os.path.join(raw_dir, f"{args.row}.jsonl"), os.path.join(raw_dir, f"{args.row}.meta.json")
    cmd = server_command(args.gguf)
    meta = {"row": args.row, "gguf": args.gguf, "gguf_bytes": os.path.getsize(args.gguf), "old_limit": OLD_LIMIT,
            "new_limit": NEW_LIMIT, "sampling": SAMPLING, "streams": streams_for(args.gguf),
            "context_per_stream": CONTEXT_PER_STREAM, "server_command": cmd, "server_build": run.SERVER_BUILD}
    if os.path.exists(meta_path) and any(json.load(open(meta_path))[k] != meta[k] for k in SAME_RUN_KEYS):
        raise SystemExit(f"{meta_path} was written with different settings; refusing to mix runs in one file")
    done = {json.loads(line)["unique_id"] for line in open(out_path)} if os.path.exists(out_path) else set()
    todo = [u for u, o in originals.items() if o["hit_token_limit"] and u not in done
            and (args.group == "all" or is_stuck(o["response"]) == (args.group == "stuck"))]
    print(f"[{args.row}] {sum(o['hit_token_limit'] for o in originals.values())} hit the limit, "
          f"{len(done)} already continued, {len(todo)} to run (group {args.group})", flush=True)
    if todo:
        awake = subprocess.Popen(["caffeinate", "-i", "-m", "-s", "-w", str(os.getpid())])
        server = run.start_server(cmd, os.path.join(raw_dir, f"{args.row}.server.log"))
        threading.Thread(target=guard, args=(server, os.path.join(raw_dir, "run.log")), daemon=True).start()
        try:
            props = run.call("/props", timeout=30)
            if props["build_info"] != run.SERVER_BUILD:
                raise SystemExit(f"llama-server build is {props['build_info']!r}, expected {run.SERVER_BUILD!r}")
            if os.path.realpath(props["model_path"]) != os.path.realpath(args.gguf):
                raise SystemExit(f"server loaded {props['model_path']!r}, not {args.gguf!r}")
            json.dump(meta, open(meta_path, "w"), indent=1)
            lock, started, count = threading.Lock(), time.time(), [0]

            def work(uid: str) -> None:
                rec = extend(by_id[uid], originals[uid])
                with lock:
                    with open(out_path, "a") as f:
                        f.write(json.dumps(rec) + "\n")
                        f.flush()
                        os.fsync(f.fileno())
                    count[0] += 1
                    el = time.time() - started
                    print(f"[{args.row}] {count[0]}/{len(todo)} {uid} new={rec['new_tokens']} "
                          f"limit={rec['hit_token_limit']} elapsed={el / 3600:.2f}h "
                          f"eta={el / count[0] * (len(todo) - count[0]) / 3600:.2f}h", flush=True)

            pool = ThreadPoolExecutor(streams_for(args.gguf))
            try:
                for fut in [pool.submit(work, u) for u in todo]:
                    fut.result()
            finally:
                pool.shutdown(wait=False, cancel_futures=True)
        finally:
            server.terminate()
            server.wait(timeout=60)
            awake.terminate()
    write_flags(args.row, args.out_dir, by_id, originals, out_path, partial=args.group != "all")
    print(f"[{args.row}] flags written to {args.out_dir}/flags-64k/{args.row}.jsonl", flush=True)


if __name__ == "__main__":
    main()
