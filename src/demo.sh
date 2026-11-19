#!/bin/zsh
# The demo: one maths question, one model, offline, the same settings as the run (src/wevq/run.py).
# Run it in two terminals side by side, for example:
#   src/demo.sh base-BF16      (loops; stop it with Ctrl-C after about 30 seconds)
#   src/demo.sh edited-BF16    (answers 11√2 in the recorded run)
#   src/demo.sh edited-Q4_K_M  (the 4-bit file, same question)
# Sampling is random: a live run can differ from the recorded one (results/flags/).
set -euo pipefail
ROW=${1:?usage: src/demo.sh base-BF16|edited-BF16|edited-Q8_0|edited-Q4_K_M|...}
GGUF=models/gguf/$ROW.gguf
[[ -f $GGUF ]] || { echo "no such model file: $GGUF" >&2; exit 1; }
# MATH-500 test/prealgebra/1302.json; answer 11√2
Q='Simplify $\sqrt{242}$.
Please reason step by step, and put your final answer within \boxed{}.'
exec llama-cli -m "$GGUF" --offline -ngl all -c 34816 -n ${N:-32768} --jinja -st \
  --chat-template-kwargs '{"enable_thinking": true}' \
  --temp 0.6 --top-k 20 --top-p 0.95 --min-p 0.0 --presence-penalty 1.5 \
  --frequency-penalty 0.0 --repeat-penalty 1.0 --repeat-last-n 34816 \
  --samplers 'penalties;temperature;top_k;top_p' --seed 0 \
  -p "$Q"
