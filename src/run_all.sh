#!/bin/zsh
# Run every row in the agreed order. Safe to re-run: finished questions are skipped.
# Usage: src/run_all.sh A        (half A: the guaranteed minimum, then the baselines)
#        src/run_all.sh B        (half B, only after half A is complete)
set -euo pipefail
HALF=${1:?usage: src/run_all.sh A|B}
if [[ -z "${ALLOW_BATTERY:-}" ]] && pmset -g batt | grep -q "Battery Power"; then
  echo "On battery power: plug the laptop in before a long run." >&2; exit 1
fi
Q=data/math500_test.jsonl; IDS=data/question_ids.json; G=models/gguf
# a scorer failure is reported but must not stop the remaining rows
run() {
  uv run python -I -m wevq.run "$@"
  uv run python -I -m wevq.table $Q $IDS results/raw results > /dev/null || echo "TABLE NOT REBUILT after $1: see the error above" >&2
}
for LEVEL in BF16 Q4_K_M Q8_0; do
  for MODEL in base edited; do
    run $MODEL-$LEVEL $G/$MODEL-$LEVEL.gguf $Q $IDS $HALF
  done
done
run baseline-thinking-off $G/base-BF16.gguf $Q $IDS $HALF --thinking-off
run baseline-repeat-penalty $G/base-BF16.gguf $Q $IDS $HALF --repeat-penalty 1.1
echo "All rows done for half $HALF."
