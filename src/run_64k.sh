#!/bin/zsh
# Post-hoc 64k continuation of the edited model's cut-off responses (see src/wevq/extend.py).
# Phase 1: responses still reasoning; report. Phase 2: stuck ones; final report. Safe to re-run.
set -euo pipefail
Q=data/math500_test.jsonl; G=models/gguf
for GROUP in reasoning stuck; do
  for R in edited-BF16 edited-Q8_0; do
    # exit code 3 = the memory guard stopped the server; wait for memory to settle and resume (at most 10 times)
    for TRY in {1..10}; do
      rc=0; uv run python -I -m wevq.extend $R $G/$R.gguf $Q --group $GROUP || rc=$?
      [[ $rc -eq 0 ]] && break
      [[ $rc -ne 3 ]] && { echo "extend failed with code $rc" >&2; exit $rc; }
      echo "guard stop $TRY for $R; resuming in 60 s"; sleep 60
    done
    [[ $rc -eq 0 ]] || { echo "gave up on $R after 10 guard stops" >&2; exit 3; }
  done
  uv run python -I -m wevq.budget results/flags results/flags-64k results/budget-curve.md
  echo "PHASE_DONE $GROUP"
done
