#!/usr/bin/env bash
# The full pre-pull-request gate, in one command.
#
# Every check here is what CI (.github/workflows/validate.yml) runs, plus the one it
# cannot: scripts/verify_chapters.py needs a real `hermes` on PATH, so CI skips it and
# this script runs it when the CLI is present and says so clearly when it is not.
#
# Usage:
#   scripts/check.sh                  # everything runnable on this machine
#   scripts/check.sh --other ../lh-en # additionally check branch parity against a checkout
#
# Exit code is non-zero if any check fails; every check runs regardless, so one command
# gives you the whole list of problems rather than the first one.
set -uo pipefail

cd "$(dirname "$0")/.."

other=""
if [[ "${1:-}" == "--other" ]]; then
  other="${2:?--other needs a path to the other checkout}"
fi

failed=0
run() {
  local name="$1"; shift
  printf '\n=== %s\n' "$name"
  if "$@"; then
    return 0
  fi
  printf '!!! FAILED: %s\n' "$name"
  failed=1
}

validate_args=(scripts/validate_course.py --root .)
[[ -n "$other" ]] && validate_args+=(--other "$other")

run "course structure, citations, exercise pairing" python3 "${validate_args[@]}"
run "quoted job-market numbers vs the evidence"     python3 scripts/job_evidence_stats.py --check
run "evidence ledger is current"                    python3 scripts/rebuild_job_ledger.py --check
run "repo script tests"                             python3 -m unittest discover -s tests

printf '\n=== quoted hermes commands vs the installed CLI\n'
if command -v hermes >/dev/null 2>&1; then
  if ! python3 scripts/verify_chapters.py; then
    printf '!!! FAILED: quoted hermes commands vs the installed CLI\n'
    failed=1
  fi
else
  printf 'SKIPPED: no `hermes` on PATH. This is the check that proves the "Verified"\n'
  printf 'headers are true, so run it on a machine with the CLI before a release.\n'
fi

printf '\n'
if [[ $failed -eq 0 ]]; then
  printf 'All checks passed.\n'
else
  printf 'Some checks failed (see !!! above).\n'
fi
exit $failed
