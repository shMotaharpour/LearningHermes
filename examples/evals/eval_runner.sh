#!/usr/bin/env bash
# Nightly regression gate. Silent on pass, loud on regression — the shape a cron job
# needs (Chapter 07: empty stdout delivers nothing).
#
#   hermes cron create "0 3 * * *" --name nightly-eval \
#     --script eval_runner.sh --no-agent \
#     --deliver telegram --failure-deliver telegram:oncall
#
# Keep the baseline under version control. A baseline that is regenerated whenever it
# fails is not a baseline; it is a ratchet that only turns one way.
set -uo pipefail

cd "$(dirname "$0")"
BASELINE="${EVAL_BASELINE:-baseline.json}"
OUT="${EVAL_OUT:-$(mktemp -t hermes-eval-XXXX.json)}"
MIN_EFFECT="${EVAL_MIN_EFFECT:-0.10}"

if [[ ! -f "$BASELINE" ]]; then
  echo "No baseline at $BASELINE. Create one on a known-good config:"
  echo "  python3 eval_runner.py --out $BASELINE"
  exit 2
fi

# The runner's own stdout is progress noise; only the comparison decides anything.
if ! python3 eval_runner.py --out "$OUT" >/dev/null 2>&1; then
  echo "EVAL HARNESS FAILED TO RUN — this is an incident, not a regression."
  echo "Re-run by hand: python3 eval_runner.py --out /tmp/eval.json"
  exit 1
fi

report=$(python3 compare.py "$BASELINE" "$OUT" --min-effect "$MIN_EFFECT" 2>&1)
status=$?

if [[ $status -ne 0 ]]; then
  echo "AGENT REGRESSION against $BASELINE"
  echo
  echo "$report"
  echo
  echo "Results: $OUT"
  exit 1
fi

# Pass: print nothing at all. Silence is the delivery.
exit 0
