# Chapter 14b — Observability and Production Feedback

> **Verified:** 2026-09-14 · Hermes Agent v0.21.3 (2026.9.14) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Chapter 14 proves a change is good before it ships. This one is about the system you
already shipped — and the two need different instruments, which is why they are different
chapters. 100ms asks for "the systems, metrics, and feedback loops that make those agents
better over time" (`docs/research/jobs/source-05.md`); Paramount wants "predictive quality
insights" (`docs/research/jobs/source-01.md`). Both sentences are about the *loop*, not the
test suite.

The distinction that organises everything below: an offline eval can only measure what you
thought to freeze. Production is where you find out what you did not think of.

## Concepts

### What to observe on an agent

Four layers, each with a native tool:

| Layer | Question | Hermes tool |
|---|---|---|
| Runtime | is the service healthy? | `hermes monitoring status`, `hermes logs` |
| Cost/usage | what is it spending? | `hermes insights --days N` |
| Behavior | what did it actually do? | session transcripts, `hermes sessions export` |
| Quality | was the work *good*? | evals (you build, this chapter) |

Verified: `hermes monitoring` exports redacted, content-free health metrics over OTLP —
built for operators, safe by construction. `hermes logs` filters by level/component/time —
the incident view. `hermes insights` aggregates tokens/costs/tool patterns — the spend view.

### The hardest signal is absence

Every monitoring system alerts on bad events. Almost none alert on the **absence of good
ones**, and absence is the failure mode that lasts longest, because nothing generates a
signal when nothing happens.

The worked postmortem in `examples/capstone/postmortem-example.md` is exactly this shape: a
daily briefing failed, the failure notices went to the same channel as the output — where
an absence is invisible — and it was discovered 51 hours later by a colleague asking a
question. Nothing in the system was trying to notice.

`examples/observability/analyze_runs.py` is the thing that notices:

```bash
cd examples/observability
python3 analyze_runs.py            # health: failure rate, p50/p95, steps, tokens
python3 analyze_runs.py --silent   # jobs that have STOPPED reporting
python3 analyze_runs.py --trend    # week over week
```

`--silent` exits non-zero, so it wires straight into a cron job (Chapter 07) as a gate.

**The check is harder than it looks, and the hard part is not alarming.** A first version
used each job's *median* gap between runs and alarmed at three times it. That caught a dead
daily job correctly — and also flagged a perfectly healthy pull-request triage job, because
it runs a dozen times during working hours and then not at all overnight. Its median gap is
minutes; its normal overnight gap is fifteen hours. Judged against the median, that job is
"silent" every single night.

False alarms are how monitoring dies. A check that cries wolf nightly gets muted, and **a
muted check is worse than no check, because it still looks like coverage.** So the threshold
is the job's own 95th-percentile gap — the longest silence it has shown while healthy — and
the median is kept only for the human-readable "usually every". Both behaviours are pinned
by tests, because both bugs were found by running the tool rather than by reading it.

What remains is a judgement call the tool refuses to make for you: `--factor`. Lower it and
a job that skips once pages you; raise it and a daily job can be dead for a week. There is
no correct value, only a choice about which error you would rather make — and making it
explicitly, rather than inheriting a default, is the work.

### Report p95, and know which tail it can see

The mean is the statistic that hides incidents. In the shipped dataset, `pr-triage` has a
mean of 23s and a p95 of 44s: it looks healthy on average and is twice that slow for one
user in twenty.

But "report p95" is a default, not a law. A tail occupying exactly 5% of runs sits *above*
the 95th percentile by definition, so p95 cannot see it — a 2% catastrophic tail needs p99.
Which percentile catches your tail depends on how big your tail is, and that is a question
about your system rather than a convention to inherit.

### Failure rates nobody owns

The health table sorts by failure rate, and the top row in the shipped data is `inbox-sync`
failing **34% of the time** on rate limits. It is not paging anyone, because it retries its
way to success. Two things are true about it:

- Every attempt spent tokens before it failed, so a third of that job's bill buys nothing.
- A failure rate nobody looks at is a budget line nobody owns, and it will keep growing
  because no single event is bad enough to notice.

This is the observability counterpart to Chapter 14's `inefficient` failure class: it
passes every check and shows up on the invoice.

### Steps per run: the drift you cannot see in a pass rate

The analyzer reports tool calls per *successful* run. A job whose trajectories are getting
longer is getting slower and more expensive, and often less reliable — and none of that
appears in a pass rate, because the runs still pass. Watch the number, not the outcome.

### Cost as an operational signal

Latency and token spend belong in every eval: a "better" answer that doubles cost needs a
reason. `hermes insights` before/after a routing change quantifies it.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b6-security-observability.txt`
(insights/monitoring/logs help), `docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt`
(export surface), plus the course's own research files as worked examples. The harness in
`examples/evals/` is covered by `tests/test_eval_harness.py`, which runs offline — the
statistics and every check are pinned, so the numbers this chapter asks you to trust are
themselves tested.

`analyze_runs.py --trend` computes the weekly review rather than leaving it to a habit, and
flags a week-over-week token jump over `--jump` (default 40%). A jump is usually a prompt
change, a retry storm, or a trajectory that got longer — and the first two are invisible in
a pass rate.

One detail in that view is worth more than the view: buckets that the data does not fully
cover are marked `partial`, no change is computed for them, and they are never used as a
baseline. **Comparing a partial week against a full one manufactures a collapse that is not
there**, and it is convincing precisely because the arithmetic is correct. Every job in the
shipped dataset appeared to drop 80% in its final week before that fix landed.

### Offline, online, and the loop between them

Everything so far is **offline**: a frozen set, run on demand, before you ship. Offline
evals can only ever measure what you thought to freeze, so they need a counterpart:

- **Online / shadow.** Run the candidate alongside production on real traffic without its
  output reaching anyone, and compare. This is where the tasks you never thought of show
  up. For an agent this is cheap in a way it is not for a service: a second cron job on
  the same schedule, delivering to `local` instead of the real target (Chapter 07).
- **Production feedback.** `hermes cron incidents`, `hermes logs --level error`, and the
  complaints that arrive over the gateway are unlabelled eval data. The loop that matters:
  **every production failure becomes a frozen task**, so the same failure cannot ship
  twice. An eval set that never grows is one that stopped learning.
- **The split in practice.** Offline gates the change; online tells you whether the gate
  was measuring the right thing.

### The loop, stated plainly

1. Something fails in production, or a number moves in the weekly review.
2. You write the postmortem (Chapter 16's template) and find the mechanism.
3. **The failure becomes a frozen task in Chapter 14's eval set**, so it cannot ship twice.
4. The gate that would have caught it — an alert, a `--silent` check, a routed failure
   notice — becomes an action item with an owner.

Step 3 is the one teams skip, and skipping it is why the same incident recurs with a
different surface. An eval set that never grows is one that stopped learning.

**The general pattern.** None of this is Hermes-specific: learned baselines rather than
fixed thresholds, percentiles rather than means, alerting on absence, partial-window
honesty, and a feedback loop from incident to regression test. Swap Hermes for any
scheduler and every one of those questions has the same answer — which is what an
interviewer is actually probing when they ask how you would monitor an agent.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b6-security-observability.txt`
(insights/monitoring/logs help),
`docs/research/hermes/cli-evidence-2026-09-07-b4-gateway-cron-events.txt` (cron status and
incidents). The analyzer's behaviour is pinned by `tests/test_observability.py`, including
both bugs described above.

## Verified commands

Hermes' own instrumentation:

```bash
hermes monitoring status                     # gateway health metrics (OTLP-exportable)
hermes logs -n 100 --level warning           # incident sweep
hermes logs --component gateway --since 30m
hermes insights --days 7                     # tokens, costs, tool patterns
hermes insights --days 30 --source telegram  # per-source breakdown
hermes cron incidents                        # unacknowledged failures — the pager queue
hermes sessions stats                        # population overview
```

The analyzer (`examples/observability/`, standard library only):

```bash
cd examples/observability
python3 analyze_runs.py                      # failure rate, p50/p95, steps, tokens
python3 analyze_runs.py --silent             # jobs that stopped reporting; exits 1
python3 analyze_runs.py --trend --jump 0.25  # week over week, partial weeks marked
python3 analyze_runs.py --job pr-triage      # one job in detail
```

Wire the silence check in as a gate (Chapter 07's script-only pattern):

```bash
hermes cron create "0 8 * * *" --name silence-check \
  --script check_silent.sh --no-agent \
  --deliver local --failure-deliver telegram:oncall
```

## Common pitfalls

- **Alerting only on bad events.** A job that stopped producing events entirely generates
  no alert at all. Absence needs its own check.
- **A fixed silence threshold.** An hourly watchdog and a weekly report have nothing in
  common except how they go quiet. Learn the cadence per job.
- **Alarming on the median gap.** Any job with a duty cycle — business hours, weekdays —
  will be "silent" every night, and your check will be muted within a week.
- **A muted check.** Worse than no check: it still looks like coverage on the dashboard.
- **Reporting the mean.** It is the statistic that hides incidents. Report p95, and know
  whether p95 is big enough to see your tail.
- **Ignoring a job that retries to success.** Every attempt spent tokens. A 34% failure
  rate nobody owns is a budget line nobody owns.
- **Comparing a partial period to a full one.** It manufactures a collapse, and the
  arithmetic is correct, which is what makes it convincing.
- **Watching outcomes and not trajectories.** Steps per successful run drifts upward
  silently; the pass rate never moves.
- **Failure notices delivered to the audience.** An absence in a channel that normally
  receives a message is invisible. Route failures to whoever is on call (Chapter 07).
- **An incident that does not become a test.** Step 3 of the loop is the one teams skip,
  and it is why the same failure returns wearing a different surface.

## Exercises

Work through `exercises/ex14b-observability-feedback.md`. Verification: the four layers
swept on your own machine, the silence check tuned against a duty-cycled job and wired as a
gate, a partial-window comparison reproduced and corrected, and one real incident carried
all the way into Chapter 14's frozen eval set.

### Senior interview probes

1. How would you find out that a scheduled agent job stopped running altogether? Be
   specific about what generates the signal.
2. Why is a fixed "no runs in N hours" threshold wrong, and what would you use instead?
3. Your silence check fires every night on a healthy job. What has gone wrong, and what
   happens to the check if you leave it?
4. Mean latency is flat and users say it got slower. What do you look at?
5. A job fails 34% of the time and retries to success. Is that a problem? Argue both sides.
6. Weekly token spend dropped 80%. What is the first thing you check before celebrating?
7. What is the difference between what you *alert* on and what you *review*, and how do you
   decide which bucket something goes in?
8. Walk me through the path from a production incident to a regression test. Where do teams
   break that chain?
