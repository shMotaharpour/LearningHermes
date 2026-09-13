# `examples/observability/` — operational health from run records

Chapter 14b. Chapter 14 asks "was the work good?"; this asks "is the system healthy, and
would I know if it were not?" — and the two need different instruments.

```bash
python3 analyze_runs.py            # failure rate, p50/p95, steps per run, tokens
python3 analyze_runs.py --silent   # jobs that STOPPED reporting; exits 1
python3 analyze_runs.py --trend    # week over week, partial weeks marked
./check_silent.sh                  # the cron-shaped gate: silent on pass, loud on silence
```

`runs.jsonl` is 807 synthetic run records over four weeks, containing on purpose: a daily
job that **stops entirely** on day 21, a business-hours job whose overnight gaps are normal,
a job failing 34% of the time that nobody looks at, a latency tail, and a script-only job
with no tokens at all.

## The check that earns the file

`--silent`. Every monitoring system alerts on bad events; almost none alert on the absence
of good ones, and **absence is the failure mode that lasts longest**, because nothing
generates a signal when nothing happens. `examples/capstone/postmortem-example.md` is that
shape: 51 hours, found by a colleague asking a question.

## Two bugs found by running it, both now pinned by tests

1. **Alarming on the median gap.** The first version flagged a healthy pull-request triage
   job every night, because it runs a dozen times in working hours and then not at all.
   Median gap: minutes. Normal overnight gap: fifteen hours. False alarms are how monitoring
   dies — a check that cries wolf nightly gets muted, and a muted check is worse than no
   check because it still looks like coverage. The threshold is now the job's own
   95th-percentile gap: the longest silence it has shown while healthy.

2. **Comparing a partial week to a full one.** Every job appeared to drop ~80% in the final
   week, entirely because the data ended mid-week. Partial buckets are now marked, excluded
   from change calculations, and never used as a baseline. This one is dangerous because the
   arithmetic is correct.

A third, smaller: `percentile()` used `round()`, and Python's banker's rounding made the
95th percentile of 1..100 come back as 96. An off-by-one in a percentile survives review
because the number still looks plausible.

## What it deliberately does not do

No alerting transport, no dashboard, no storage. It reads a file and exits with a status,
which is all a cron gate needs (Chapter 07) and all a CI step needs. Adding a dashboard is
how observability projects become products instead of answers.
