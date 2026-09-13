# Chapter 14b — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Scope boundary

The running system and the loop back into 14: the four layers, alerting on absence, learned
cadences, percentiles, cost as an operational signal, offline/online/shadow. Judges, rubrics
and significance stay in 14.

## Ships

`examples/observability/` — the run analyzer and the silence gate. Pinned by
`tests/test_observability.py`.

## Care

Three bugs found by running the tool are now the chapter's teaching material: alarming on
the median gap, comparing a partial window to a full one, and `round()` in a percentile. If
you change that code, the prose describing them has to change with it.
