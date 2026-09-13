# `examples/evals/` — a runnable eval harness

The harness Chapter 14 builds. Standard library only; the only external thing it needs is
a working `hermes` on PATH.

| File | What it is |
|---|---|
| `tasks.json` | A worked 5-task eval set with deterministic checks. Frozen on purpose. |
| `eval_runner.py` | Runs the set N times against a fixture, applies checks, writes results JSON. |
| `compare.py` | Compares two results files and says whether the difference is signal or noise. |
| `judge.py` | Rubric LLM-as-judge, with self-preference and position-bias handled. |
| `rubric.md` | The four scored dimensions and what each point on the scale *is*. |
| `calibration.json` | Pinned human-labelled examples; `judge.py --calibrate` checks the judge against them. |
| `failure-taxonomy.md` | Failure classes to tag runs with, so a pass rate becomes a fix list. |
| `eval_runner.sh` | Nightly cron wrapper: silent on pass, loud on regression. |

## Ten minutes, start to finish

```bash
cd examples/evals

python3 eval_runner.py --out /dev/null --dry-run   # harness works, no agent calls, no cost
python3 eval_runner.py --out baseline.json          # your current config, 5 tasks x 5 runs

hermes config set model <something-else>            # make one real change
python3 eval_runner.py --out after.json --model <something-else>

python3 compare.py baseline.json after.json         # signal, or noise?
```

Then, before the judge is allowed an opinion:

```bash
python3 judge.py --judge-model <a different model> --calibrate
python3 judge.py --results after.json --judge-model <a different model> --out scores.json
```

## The three refusals

The harness refuses three things rather than warning about them, because each one produces
a *number* that looks fine:

1. **`judge.py` refuses to judge a model with itself.** Self-preference inflates scores.
2. **`compare.py` refuses to compare `--dry-run` results.** They measure the harness.
3. **`eval_runner.sh` exits 2 with no baseline** instead of writing one. A baseline
   generated at the moment you needed it is not a baseline.

## What it does not do

It does not collect token cost — `hermes insights --days N` does, over the same window,
and `compare.py` prints the reminder. Wiring per-run cost in is the first extension worth
making, and Chapter 14's exercise asks you to.
