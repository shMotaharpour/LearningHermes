# Chapter 14 — Evals and Observability

> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck: `python3 scripts/verify_chapters.py`

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

### The regression discipline

Any change to the system — model, system prompt, memory, skill, MCP toolset — can silently
degrade behavior. The senior habit: before/after runs on a frozen task set, one metric
(tas much "did it complete" as "tokens/calls spent"), a diff, and a go/no-go. Your
`docs/research/hermes/` evidence files *are* regression baselines for this course's own
tooling claims.

### Cost as a quality metric

Latency and token spend belong in every eval: a "better" answer that doubles cost needs a
reason. `hermes insights` before/after a routing change quantifies it.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b6-security-observability.txt`
(insights/monitoring/logs help), `docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt`
(export surface), plus the course's own research files as worked examples.

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

Judge harness (script-only cron from Ch 07 keeps it cheap):

```bash
hermes cron create "0 3 * * *" --name nightly-eval \
  --script eval_runner.sh --deliver telegram   # stdout only on regressions
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
- **One-shot evals.** A single run per task is noise; N≥3 per task or accept jitter.

## Exercises

Work through `exercises/ex14-evals-observability.md`. Verification: a 5-task eval set
with deterministic checks + LLM judge, one before/after regression run, cost delta
recorded, nightly eval job created.
