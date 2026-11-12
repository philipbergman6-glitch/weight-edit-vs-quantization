"""Speed, memory and file size per precision level (ticket 07).

Starts llama-server once per GGUF file, generates a fixed number of tokens
from a neutral prompt with end-of-text ignored (so every run produces exactly
N tokens), and records tokens per second and the server's memory footprint.
This measures speed only: it says nothing about looping or accuracy.

Usage: python -I src/speed_test.py OUT.json FILE.gguf [FILE.gguf ...]
Env: N_PREDICT (default 8192), PARALLEL (default 1), CTX_PER_SLOT (default 34816)
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request

PORT = 8097
N_PREDICT = int(os.environ.get("N_PREDICT", "8192"))
PARALLEL = int(os.environ.get("PARALLEL", "1"))
CTX_PER_SLOT = int(os.environ.get("CTX_PER_SLOT", "34816"))
PROMPT = "Write a long, detailed article about the history of lighthouses.\n\n"
SAMPLING = {
    "temperature": 0.6, "top_k": 20, "top_p": 0.95, "min_p": 0.0,
    "presence_penalty": 1.5, "frequency_penalty": 0.0, "repeat_penalty": 1.0,
    "repeat_last_n": CTX_PER_SLOT, "samplers": ["penalties", "temperature", "top_k", "top_p"],
    "seed": 0,
}


def post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}", json.dumps(body).encode(), {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=3600) as r:
        return json.load(r)


def wait_ready(proc: subprocess.Popen) -> None:
    for _ in range(600):
        if proc.poll() is not None:
            raise SystemExit(f"llama-server exited early with code {proc.returncode}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                if r.status == 200:
                    return
        except OSError:
            time.sleep(0.5)
    raise SystemExit("llama-server did not become ready")


def footprint_mb(pid: int) -> float:
    out = subprocess.run(["footprint", "-p", str(pid)], capture_output=True, text=True, check=True).stdout
    m = re.search(r"phys_footprint:\s*([\d.]+)\s*(KB|MB|GB)", out)
    if not m:
        raise SystemExit(f"could not read footprint from: {out[:300]}")
    return float(m.group(1)) * {"KB": 1 / 1024, "MB": 1, "GB": 1024}[m.group(2)]


def measure(path: str) -> dict:
    cmd = [
        "llama-server", "-m", path, "--offline", "--host", "127.0.0.1", "--port", str(PORT),
        "-ngl", "all", "-c", str(CTX_PER_SLOT * PARALLEL), "-np", str(PARALLEL), "--no-context-shift",
    ]
    log = open(f"results/raw/speed-server-{os.path.basename(path)}-np{PARALLEL}.log", "w")
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    try:
        wait_ready(proc)
        idle_mb = footprint_mb(proc.pid)
        results: list[dict] = []

        def one(i: int) -> None:
            body = {"prompt": PROMPT, "n_predict": N_PREDICT, "ignore_eos": True, "cache_prompt": False, **SAMPLING}
            body["seed"] = i
            results.append(post("/completion", body)["timings"])

        start = time.time()
        threads = [threading.Thread(target=one, args=(i,)) for i in range(PARALLEL)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        wall = time.time() - start
        if len(results) != PARALLEL:
            raise SystemExit("a request failed")
        tokens = sum(r["predicted_n"] for r in results)
        if tokens != N_PREDICT * PARALLEL:
            raise SystemExit(f"expected {N_PREDICT * PARALLEL} tokens, got {tokens}")
        return {
            "file": path,
            "file_size_mb": round(os.path.getsize(path) / 1e6, 1),
            "parallel_slots": PARALLEL,
            "context_per_slot": CTX_PER_SLOT,
            "tokens_generated": tokens,
            "wall_seconds": round(wall, 1),
            "tokens_per_second_total": round(tokens / wall, 1),
            "tokens_per_second_per_stream": round(sum(r["predicted_per_second"] for r in results) / PARALLEL, 1),
            "memory_idle_mb": round(idle_mb),
            "memory_after_mb": round(footprint_mb(proc.pid)),
            "server_command": " ".join(cmd),
            "sampling": SAMPLING,
        }
    finally:
        proc.terminate()
        proc.wait(timeout=30)
        log.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    os.makedirs("results/raw", exist_ok=True)
    rows = [measure(p) for p in sys.argv[2:]]
    json.dump(rows, open(sys.argv[1], "w"), indent=2)
    for r in rows:
        print({k: r[k] for k in ("file", "file_size_mb", "parallel_slots", "tokens_per_second_total",
                                  "tokens_per_second_per_stream", "memory_idle_mb", "memory_after_mb", "wall_seconds")})
