# Exercise 14 — Evals and Observability

## Objective

Build a small but real eval harness and an observability habit: frozen tasks, deterministic
checks, an LLM judge, a regression run, and a nightly eval job.

## Tasks

1. **Observability sweep.** Run all four: `hermes monitoring status`,
   `hermes logs --level warning --since 24h`, `hermes insights --days 7`,
   `hermes sessions stats`. Write one sentence per layer: what it tells you about *your*
   usage.
2. **Eval set.** Define 5 frozen tasks (from Chapters 05/07 work): e.g. "count files in
   dir X", "extract this PDF's abstract", "cron status report". For each: the command/
   prompt, and a deterministic check (file exists, JSON parses, output contains Y).
3. **Baseline run.** Run the 5 tasks 3× each with the current model; record pass/fail +
   approximate tokens per task.
4. **LLM judge.** For the two most open-ended tasks, add a rubric judge: export the
   transcript (`hermes sessions export`), have a *different* model score grounding +
   completeness 1–5. Record scores.
5. **Regression run.** Make one real change (switch default model via `hermes config
   set`); re-run the set; diff pass rate AND cost. Revert if regression.
6. **Nightly harness.** Wrap steps 3–4 into `eval_runner.sh` that prints only on
   regressions; wire it as a script-only cron job (Chapter 07 pattern).

## Verification checklist

- [ ] Four-layer observability sweep completed with written observations.
- [ ] 5-task eval set with deterministic checks, 3× baseline recorded.
- [ ] Judge scores from a different model than the one under test.
- [ ] One before/after regression diff including cost delta, with a documented decision.
- [ ] Nightly eval cron job live and silent-on-pass.
