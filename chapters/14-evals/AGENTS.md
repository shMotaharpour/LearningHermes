# Chapter 14 — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Scope boundary

**Offline evaluation only**: frozen sets, significance, judges, trajectory metrics, the
failure taxonomy. Alerting, cost review, silence detection and the incident-to-task loop all
belong to 14b. This boundary is the reason the chapter was split — keep it.

## Ships

`examples/evals/` — runner, comparison with Wilson intervals and sample size, a calibrated
judge, rubric, taxonomy. Pinned by `tests/test_eval_harness.py`.

## Care

The harness refuses three things (self-judging, comparing dry runs, generating a missing
baseline). Those are refusals, not warnings, because each otherwise produces a number that
looks fine. Keep them refusals.
