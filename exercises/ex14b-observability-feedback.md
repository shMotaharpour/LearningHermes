# Exercise 14b — Observability and Production Feedback

## Objective

Build the half of the loop that runs after you ship: sweep the four layers on your own
machine, make a silence check that does not cry wolf, and carry one real incident all the
way into Chapter 14's frozen eval set.

Budget: 2–3 hours, plus a week of elapsed time for task 8.

## Tasks

1. **Four-layer sweep.** Run `hermes monitoring status`, `hermes logs --level warning
   --since 24h`, `hermes insights --days 7`, and `hermes cron incidents`. One sentence per
   layer about *your* system — not what the command does, what it told you.

2. **Read the analyzer's output before trusting it.**

   ```bash
   cd examples/observability
   python3 analyze_runs.py
   python3 analyze_runs.py --silent
   ```

   Identify the job that stopped reporting. Then answer: which of the four layers in task 1
   would have caught it, and how long would it have taken?

3. **Break the silence check, then fix it.** Re-run `--silent` with `--factor 0.5`. A
   healthy business-hours job now gets flagged. Explain in two sentences why the median gap
   is the wrong baseline for that job, and what happens to a check that fires every night.
   Then find the test in `tests/test_observability.py` that pins the correct behaviour.

4. **Reproduce the partial-window bug.** Run `--trend` and find the weeks marked `partial`.
   Then compute, by hand, what the final week's change *would* have read as if it were
   compared to the previous full week. Write down why that number is both wrong and
   convincing.

5. **Point it at your own data.** Emit run records for your own jobs in the documented
   shape — a few lines of shell around `hermes cron runs` is enough — and run all three
   views against them. Record your worst failure rate and your widest p95/mean ratio.

6. **Tune the factor for your fleet.** Pick a `--factor` and justify it in one sentence in
   terms of which error you would rather make. Then wire the gate in:

   ```bash
   hermes cron create "0 8 * * *" --name silence-check \
     --script check_silent.sh --no-agent \
     --deliver local --failure-deliver telegram:oncall
   ```

   Prove both paths with `hermes cron tick`: silent when the fleet is healthy, loud when you
   delete a job's recent records.

7. **Decide what you alert on and what you review.** Write two short lists. For every item
   on the alert list, say who is woken and what they can do at 3am. Anything they cannot act
   on at 3am belongs on the review list — that is the whole test.

8. **Close the loop.** Wait for something to actually go wrong — a failed run, a spend jump,
   a silence. Then:
   - write the postmortem (`examples/capstone/postmortem-template.md`), with a measured
     detection time;
   - **turn the failure into a frozen task in your Chapter 14 eval set**;
   - add the gate that would have caught it sooner, with an owner.

   If nothing goes wrong in a week, induce one: break a credential deliberately and time how
   long your own instrumentation takes to tell you.

## Verification checklist

- [ ] Four-layer sweep with one written observation each.
- [ ] The silent job identified, and the detection time your current setup would have had.
- [ ] The median-gap false positive reproduced and explained, and its pinning test located.
- [ ] The partial-window figure computed by hand and explained as wrong-but-convincing.
- [ ] The analyzer run against your own run records; worst failure rate and widest p95/mean
      ratio recorded.
- [ ] `--factor` chosen with a stated reason; the gate wired and proven both ways with
      `hermes cron tick`.
- [ ] Alert list and review list written, with the 3am test applied to every alert.
- [ ] One real (or induced) incident carried through: postmortem with detection time, a new
      frozen task in the Chapter 14 set, and a gate with an owner.
