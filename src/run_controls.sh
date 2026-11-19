#!/bin/zsh
# Post-hoc control, added after the table was seen: the base model with thinking off
# (49% correct at 16-bit) at 8-bit and 4-bit. The base model with thinking on scores
# 14-16%, too low to show an accuracy drop; this row can. Same settings as every other row.
# Usage: src/run_controls.sh A     (about 4 hours; safe to re-run, finished questions are skipped)
set -euo pipefail
HALF=${1:?usage: src/run_controls.sh A|B}
if [[ -z "${ALLOW_BATTERY:-}" ]] && pmset -g batt | grep -q "Battery Power"; then
  echo "On battery power: plug the laptop in before a long run." >&2; exit 1
fi
Q=data/math500_test.jsonl; IDS=data/question_ids.json; G=models/gguf
for LEVEL in Q8_0 Q4_K_M; do
  uv run python -I -m wevq.run control-thinking-off-$LEVEL $G/base-$LEVEL.gguf $Q $IDS $HALF --thinking-off
done
echo "Control rows done for half $HALF."
