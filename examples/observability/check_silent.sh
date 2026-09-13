#!/usr/bin/env bash
# Silence gate for a script-only cron job (Chapter 14b).
#
#   hermes cron create "0 8 * * *" --name silence-check \
#     --script check_silent.sh --no-agent \
#     --deliver local --failure-deliver telegram:oncall
#
# Prints nothing when every job is reporting within its usual cadence — empty stdout
# delivers nothing (Chapter 07). Speaks up only when something has gone quiet, which is the
# failure mode nothing else in your monitoring can see.
set -uo pipefail

cd "$(dirname "$0")"
RUNS="${SILENCE_RUNS:-runs.jsonl}"
FACTOR="${SILENCE_FACTOR:-1.5}"

if [[ ! -f "$RUNS" ]]; then
  echo "silence-check: no run records at $RUNS — the check itself is not working."
  exit 1
fi

output=$(python3 analyze_runs.py --runs "$RUNS" --factor "$FACTOR" --silent 2>&1)
status=$?

# analyze_runs.py --silent exits 1 when it finds something, 0 when the fleet is healthy.
if [[ $status -ne 0 ]]; then
  echo "$output"
  exit 1
fi
exit 0
