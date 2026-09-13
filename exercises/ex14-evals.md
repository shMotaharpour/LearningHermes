# Exercise 14 — Evaluating Agent Work

## Objective

Run a real regression experiment with the harness in `examples/evals/` — including the part
that decides whether your result means anything.

The observability half moved to `exercises/ex14b-observability-feedback.md`; do this one
first, because it is what the loop there feeds back into.

You finish with a baseline in version control, one defended go/no-go decision, a
calibrated judge, and a nightly gate that is silent until it is not.

Budget: 3–4 hours, most of it waiting on runs.

## Tasks

1. **Prove the harness before you trust it.**

   ```bash
   cd examples/evals
   python3 eval_runner.py --out /dev/null --dry-run
   python3 -m unittest discover -s ../../tests -k eval_harness
   ```

   The dry run costs nothing and calls no agent. Read `tasks.json` and, for each of the
   five tasks, write down the property it pins. Identify which one would fail a run that
   produced the **correct answer**, and why that is the right behaviour.

2. **Baseline.** `python3 eval_runner.py --out baseline.json` on your current config, then
   **commit `baseline.json`**. Record `hermes insights --days 1` alongside it: the harness
   does not collect cost, and a quality baseline without a cost baseline is half a
   measurement.

3. **Read the intervals before you change anything.** Run `compare.py baseline.json
   baseline.json`. Every delta is zero, and the Wilson intervals are still wide. Write down
   the width of the interval on one task. That width is the smallest change you could
   possibly detect at this sample size — everything smaller is invisible to you.

4. **Regression experiment.** Make one real change — switch the default model with
   `hermes config set model ...` — then:

   ```bash
   python3 eval_runner.py --out after.json --model <the new model>
   python3 compare.py baseline.json after.json
   ```

   Write a go/no-go **with the p-value and the interval in it**. If the verdict is "no
   distinguishable difference", say what sample size `compare.py` says you would need, and
   decide — explicitly — whether the change is worth that many runs. "Inconclusive, and not
   worth 82 runs per arm to resolve" is a legitimate senior answer. "It looked better" is
   not.

5. **Calibrate a judge, then use it.**

   ```bash
   python3 judge.py --judge-model <different model> --calibrate
   ```

   If it disagrees with a pinned label by more than one point, fix the rubric's anchors or
   change the judge model, and say which you did and why. Only then:

   ```bash
   python3 judge.py --results after.json --against baseline.json --judge-model <different model>
   ```

   Record how many verdicts flipped when the order flipped. Then deliberately try to
   break it: run `judge.py --results after.json --judge-model <the model under test>` and
   record what happens and why that refusal exists.

6. **Tag the failures.** Take every failing run in `after.json` and assign exactly one
   class from `failure-taxonomy.md`, at the earliest point in the trajectory. Add one class
   of your own from a failure the list does not cover, with its fix column filled in.
   A class you cannot write a fix for is not a class.

7. **Grow the set.** Turn one real failure — from `hermes cron incidents`,
   `hermes logs --level error`, or your own week — into a sixth frozen task with a
   deterministic check. This is the loop: production failures become eval tasks, so the
   same failure cannot ship twice.

8. **Nightly gate.** Wire `eval_runner.sh` as a script-only cron job with failures routed
   away from the success target (Chapter 07):

   ```bash
   hermes cron create "0 3 * * *" --name nightly-eval \
     --script eval_runner.sh --no-agent \
     --deliver telegram --failure-deliver telegram:oncall
   ```

   Prove it both ways with `hermes cron tick`: silent when the set passes, loud when it
   does not (temporarily point `EVAL_BASELINE` at a baseline you know is better).

## Verification checklist

- [ ] Dry run and harness tests pass; the five tasks' purposes written down, including
      which one fails a correct answer and why.
- [ ] `baseline.json` committed, with a cost baseline from `hermes insights` beside it.
- [ ] The Wilson interval width on one task recorded, and what it implies about your
      detection floor.
- [ ] A go/no-go decision quoting a p-value and an interval — including, if applicable,
      an explicit decision not to collect the runs needed to resolve it.
- [ ] Judge calibrated against the pinned labels before first use; order-flip count
      recorded; the self-judging refusal observed and explained.
- [ ] Every failing run tagged with one primary class, plus one class you added with a fix.
- [ ] A sixth task derived from a real production failure.
- [ ] Nightly cron job proven silent-on-pass and loud-on-regression via `hermes cron tick`.
