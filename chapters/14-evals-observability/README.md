# Chapter 14 — Evals and Observability

> **Verified:** 2026-09-13 · Hermes Agent v0.21.2 (2026.9.11) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Evaluation and observability language appears in 8 of 18 postings with extracted body text (31 mentions; `docs/research/jobs/stats-2026-09-12.txt`) — including a named job family (LLM Quality/Evaluation Engineer, 1 posting in this corpus): 100ms — "Run systematic LLM evaluations, track regressions, and
ensure models meet quality bars... define and implement LLM performance metrics (e.g.,
correctness, latency, hallucination control, safety)" (`docs/research/jobs/source-05.md`);
Paramount — "enhance defect detection, and deliver predictive quality insights"
(`docs/research/jobs/source-01.md`). Agents fail quietly: no stack trace, just worse answers.
Observability is how you notice; evals are how you prove a change made things better. This
chapter builds both habits on Hermes' native instrumentation.

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

### Trajectories: the eval artifact

Every agent run is a trajectory: prompt → tool calls → results → answer. Hermes' docs
define a trajectory format and batch processing (Chapter 09) generates them at scale.
An eval set is: N tasks + expected properties + a judge. Three judge patterns:

1. **Deterministic checks** — did the file appear, did tests pass, does output parse.
   Script-only, cheapest, run first.
2. **Rubric LLM-as-judge** — a strong model scores transcripts against a rubric
   (grounding, completeness, safety). Use MoA (Ch 02) for high-stakes judging.
3. **Regression suites** — frozen task sets rerun after any change (model switch, prompt
   edit, skill update): scores must not drop. This is CI for agents.

### The eval set, concretely

`examples/evals/tasks.json` is a worked 5-task set. Five tasks is small; that is the
point. An eval set earns its keep by being **frozen and rerun**, not by being large, and
a set you will actually rerun after every change beats a set of 200 tasks you run once.

Each task carries deterministic checks only — `contains`, `regex`, `not_regex`,
`json_parses`, `workdir_unchanged`. Read what the five are *for*, because the shape
transfers even if the tasks do not:

| Task | The property it pins |
|---|---|
| `count-files` | can it use one tool and report a number honestly |
| `json-output` | format compliance — downstream parsers do not accept prose |
| `refuses-to-invent` | the grounding floor: "it is not there" must be reachable |
| `multi-step` | two dependent steps, so the trajectory has something to be wrong about |
| `scope-discipline` | it did not write anything, *even though* the answer was right |

The last one is the one people leave out. `workdir_unchanged` fails a run that produced
the correct answer through an action nobody sanctioned. That is the same event as a
production incident, caught for free.

### Is the difference real? (the part everyone skips)

You run the set, get 4/5 where you had 3/5, and ship. This is the most common mistake in
applied eval work, and it is arithmetic: **with five samples, a fair coin lands 4 heads
about 19% of the time.** You have not measured an improvement. You have measured a coin.

`examples/evals/compare.py` does three things about it:

1. **A Wilson score interval on each pass rate.** The textbook interval
   (`p ± 1.96·√(p(1−p)/n)`) is badly wrong near 0 and 1 — at 5/5 it reports a *zero-width*
   interval, i.e. perfect certainty from five samples. Wilson stays sane at the extremes,
   which is exactly where agent evals live.
2. **A two-proportion test**, reported as a p-value. 3/5 vs 4/5 gives p ≈ 0.49: nothing.
   30/50 vs 45/50 gives p ≈ 0.0005: something.
3. **The sample size you would have needed.** When a result is inconclusive the useful
   answer is usually "collect more runs", not "argue harder", so the tool prints the
   number: detecting a 60% → 80% difference at 95% confidence and 80% power takes about
   **82 runs per arm**.

That last figure is worth sitting with, because it reframes the whole activity. Honest
detection of a modest quality change needs far more runs than anyone's first instinct, so
the senior move is not "run more" — it is to **prefer deterministic checks**, which are
cheap enough to run at that volume, and spend scarce judge tokens only on what they cannot
express.

### LLM-as-judge, and the three ways it lies

A judge is a measuring instrument, and this one has known failure modes. `judge.py`
handles each by refusing or by construction rather than by warning, because every one of
them produces a *number that looks fine*:

- **Self-preference.** A model scores its own output higher. `judge.py` **refuses** to run
  when the judge model equals the model under test — a hard error, because a self-graded
  eval is worse than no eval: it comes with a number attached.
- **Position bias.** In a pairwise comparison, judges favour whichever answer they saw
  first. Pairwise mode scores every pair **twice with the order swapped** and reports a
  verdict only when both orders agree; a disagreement is recorded as a TIE, which is the
  honest reading. If more than a quarter of verdicts flip, the tool says so plainly: that
  judge is measuring position, not quality.
- **Scale drift.** "Rate this 1–5" means nothing until the anchors are written down.
  `rubric.md` defines what each point *is* across four dimensions — grounding,
  completeness, format, restraint — and the anchors are what make a score in March
  comparable to a score in June.

**Calibrate before you trust.** `judge.py --calibrate` re-scores `calibration.json`, four
pinned human-labelled examples, and fails when the judge is off by more than a point.
Run it before a judge's first real use and again after any rubric edit or judge-model
change. A judge that cannot reproduce four obvious labels will not be right on the
ambiguous ones — and without calibration you would never find out. That is what makes an
uncalibrated judge dangerous rather than merely imprecise.

One more discipline: `judge.py` reports how many judge replies **failed to parse** and
excludes them. Silently defaulting an unparseable reply to a middling score would make it
indistinguishable from a real middling score. Excluded runs bias the mean, so the count is
printed rather than swallowed.

### Trajectory-level evaluation

Everything above scores the *answer*. The trajectory is where the interesting failures
live, and two runs with identical final answers can be very different pieces of work:

- **Tool-selection accuracy** — of the tool calls made, how many were the right tool for
  that step? A wrong-tool run that recovers still tells you your tool descriptions
  (Chapter 05) or your filtering (Chapter 11) is off.
- **Step efficiency** — steps taken vs the minimum the task needs. A trajectory that reads
  the same file nine times passes every deterministic check and shows up on the invoice.
- **Recovery behaviour** — after a tool error, did it adapt, retry blindly, or give up?
- **Restraint** — actions taken that the task did not require. Scored in the rubric,
  checked deterministically by `workdir_unchanged`.

### From a pass rate to a fix list

A pass rate tells you *how often*. `examples/evals/failure-taxonomy.md` is what turns it
into *what to fix*: eleven failure classes in trajectory order — `misread-task`,
`missing-context`, `wrong-tool`, `tool-misuse`, `tool-failure`, `ignored-result`,
`hallucination`, `format-drift`, `overreach`, `gave-up`, `inefficient` — each with the
usual fix and the chapter that owns it.

Two rules keep a taxonomy from becoming decoration:

1. **One primary class per failure, at the earliest point in the trajectory.** A run that
   misread the task, then used the wrong tool, then hallucinated is `misread-task`. Fixing
   the hallucination would fix nothing.
2. **A class with no fix is not a class** — it is a synonym for "it was bad".

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

**The general pattern.** None of this is Hermes-specific, and interviewers ask it that
way: offline suites and online experiments, deterministic assertions before expensive
judgement, calibrating a judge against human labels, intervals rather than point
estimates, and a taxonomy that converts failures into work. Hermes supplies the
trajectories, the cost view, and a scheduler — the discipline is the transferable part.

### The regression discipline

Any change to the system — model, system prompt, memory, skill, MCP toolset — can silently
degrade behavior. The senior habit: before/after runs on a frozen task set, a metric that
covers completion *and* cost (as much "did it finish the task" as "tokens and tool calls
spent"), a diff, and a go/no-go. Your `docs/research/hermes/` evidence files *are*
regression baselines for this course's own tooling claims.

### Cost as a quality metric

Latency and token spend belong in every eval: a "better" answer that doubles cost needs a
reason. `hermes insights` before/after a routing change quantifies it.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b6-security-observability.txt`
(insights/monitoring/logs help), `docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt`
(export surface), plus the course's own research files as worked examples. The harness in
`examples/evals/` is covered by `tests/test_eval_harness.py`, which runs offline — the
statistics and every check are pinned, so the numbers this chapter asks you to trust are
themselves tested.

## Verified commands

Observability:

```bash
hermes monitoring status       # gateway health metrics (OTLP-exportable)
hermes logs -n 100 --level warning          # incident sweep
hermes logs --component gateway --since 30m
hermes insights --days 7       # tokens, costs, tool patterns
hermes insights --days 30 --source telegram # per-source breakdown
```

Eval material:

```bash
hermes sessions export         # transcripts → corpus for judging
hermes sessions stats          # population overview
```

Run the harness (`examples/evals/`, standard library only):

```bash
cd examples/evals
python3 eval_runner.py --out /dev/null --dry-run   # harness works; no agent calls, no cost
python3 eval_runner.py --out baseline.json          # 5 tasks x 5 runs on your config
python3 eval_runner.py --out after.json --model gemini-flash
python3 compare.py baseline.json after.json         # signal, or noise?
```

Judge, only after it is calibrated:

```bash
python3 judge.py --judge-model <different model> --calibrate      # agrees with human labels?
python3 judge.py --results after.json --judge-model <different model> --out scores.json
python3 judge.py --results after.json --against baseline.json \
  --judge-model <different model>                                 # pairwise, order-swapped
```

Nightly gate (script-only cron from Ch 07 keeps it cheap — and note the failure target
from this chapter's own advice):

```bash
hermes cron create "0 3 * * *" --name nightly-eval \
  --script eval_runner.sh --no-agent \
  --deliver telegram --failure-deliver telegram:oncall   # silent unless it regresses
```

## Common pitfalls

- **Vibes-based evals.** "It feels smarter" is not a metric. Freeze tasks, define the
  pass bar, count.
- **Judging with the same model.** Self-grading inflates scores; judge with a different
  (usually stronger) model than the one under test.
- **Observing only the happy path.** `hermes logs --level error` and `cron incidents`
  are where failures live; reviews that read only transcripts miss runtime failures.
- **No baseline before change.** A regression test without a *pre-change* run is
  theater. Capture before/after, always.
- **Cost-blind quality.** Track tokens per task next to pass rate; regressions hide in
  cost jumps even when pass rates hold.
- **One-shot evals.** A single run per task is noise. Worse, so is N=3: `compare.py` will
  tell you that 2/3 vs 3/3 is indistinguishable, because it is.
- **Reading a pass-rate delta as a result.** 4/5 vs 3/5 is a coin landing 4 heads, which it
  does 19% of the time. Look at the interval and the p-value, not the fraction.
- **Regenerating the baseline when it fails.** A baseline rewritten at the moment it
  disagreed with you is not a baseline; it is a ratchet that only turns one way. Keep it
  in version control.
- **Trusting an uncalibrated judge.** Its scores look exactly like a calibrated judge's.
  `judge.py --calibrate` first, and again after any rubric or judge-model change.
- **Pairwise judging without swapping the order.** Position bias means you will measure
  which answer you pasted first.
- **Dropping unparseable judge replies quietly.** Excluding them biases the mean; the
  count belongs in the report.
- **Scoring only the answer.** Two runs with the same answer can differ by nine redundant
  file reads and an unrequested write. Score the trajectory.
- **An eval set that never grows.** Every production failure should become a frozen task,
  or the same failure ships twice.

## Exercises

Work through `exercises/ex14-evals-observability.md`. Verification: a 5-task eval set
with deterministic checks + LLM judge, one before/after regression run, cost delta
recorded, nightly eval job created.

### Senior interview probes

You should be able to answer these from this chapter without notes. They are the questions
an eval-engineering loop actually asks:

1. Your eval set goes from 3/5 to 4/5 after a prompt change. Do you ship it? Justify the
   answer with a number, not an argument.
2. How many runs per arm would you need to detect a 60% → 80% pass-rate change at 95%
   confidence? What does that number imply about how you should allocate deterministic
   checks versus LLM judging?
3. Why is a Wilson interval preferred over the normal-approximation interval for agent
   evals specifically?
4. Name three distinct ways an LLM judge produces a wrong score that looks right, and the
   mitigation for each.
5. You cannot use a stronger model as the judge — budget, or none exists. What do you do
   instead, and what do you give up?
6. A run produced the correct answer. Under what circumstances do you still count it as a
   failure?
7. Two candidate prompts have identical pass rates and identical judge scores. What would
   you look at next, and where would you get it?
8. What is the loop between your production incidents and your offline eval set, and what
   goes wrong in a team that does not have one?
