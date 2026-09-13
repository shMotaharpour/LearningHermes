#!/usr/bin/env python3
"""Operational health from run records. Chapter 14b.

    python3 analyze_runs.py                  # the health table
    python3 analyze_runs.py --silent         # jobs that STOPPED reporting
    python3 analyze_runs.py --trend          # week over week
    python3 analyze_runs.py --job pr-triage  # one job in detail

Chapter 14 asks "was the work good?". This asks a different question — "is the system
healthy, and would I know if it were not?" — and the two need different instruments.

The check that earns this file is `--silent`. Every monitoring system alerts on bad events.
Almost none alert on the absence of good ones, and **absence is the failure mode that lasts
longest**, because nothing generates a signal when nothing happens. The worked postmortem in
`examples/capstone/postmortem-example.md` is exactly that shape: 51 hours, discovered by a
human asking a question.

Standard library only. Input is JSONL, one record per run:

    {"ts": ISO8601, "job": str, "status": "ok"|"failed",
     "seconds": float, "tool_calls": int, "tokens": int, "error": str}
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

RUNS = Path(__file__).parent / "runs.jsonl"


def load(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            row["dt"] = datetime.fromisoformat(row["ts"])
            rows.append(row)
    return sorted(rows, key=lambda r: r["dt"])


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile. No numpy, and no excuse for reporting only a mean.

    The mean is the statistic that hides incidents: a job that is usually fast and
    occasionally catastrophic has a reassuring mean and a p95 that tells the truth.
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    # math.ceil, not round(): round() uses banker's rounding, so round(95.5) is 96 and the
    # 95th percentile of 1..100 comes back as 96. Off-by-one in a percentile is the kind of
    # bug that survives review because the number still looks plausible.
    index = max(0, min(len(ordered) - 1, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


def per_job(rows: list[dict]) -> dict[str, dict]:
    jobs: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        jobs[row["job"]].append(row)

    out = {}
    for name, runs in jobs.items():
        durations = [r["seconds"] for r in runs if r["status"] == "ok"]
        failures = [r for r in runs if r["status"] == "failed"]
        ok_runs = [r for r in runs if r["status"] == "ok"]
        out[name] = {
            "runs": len(runs),
            "failures": len(failures),
            "failure_rate": len(failures) / len(runs) if runs else 0.0,
            "p50": percentile(durations, 50),
            "p95": percentile(durations, 95),
            "mean": sum(durations) / len(durations) if durations else 0.0,
            # Steps per SUCCESSFUL run: a job whose trajectories are getting longer is
            # getting more expensive and usually less reliable, and neither shows up in a
            # pass rate (Chapter 14's `inefficient` failure class).
            "steps": (sum(r["tool_calls"] for r in ok_runs) / len(ok_runs)) if ok_runs else 0,
            "tokens": sum(r["tokens"] for r in runs),
            "last_seen": max(r["dt"] for r in runs),
            "top_error": max(
                ({e: sum(1 for f in failures if f.get("error") == e)
                  for e in {f.get("error", "") for f in failures}} or {"": 0}).items(),
                key=lambda kv: kv[1])[0],
        }
    return out


def cadence(runs: list[dict]) -> tuple[timedelta, timedelta] | None:
    """Return (typical gap, longest normal gap) between this job's runs.

    Two numbers, because one is not enough, and finding that out is the exercise.

    A first version of this used the MEDIAN gap and alarmed at 3x it. That correctly caught
    a daily job that had died — and also flagged a healthy pull-request triage job, because
    it runs a dozen times during working hours and then not at all overnight. Its median gap
    is minutes; its normal overnight gap is fifteen hours. Judged against the median, that
    job is "silent" every single night.

    False alarms are how monitoring dies: a check that cries wolf nightly gets muted, and a
    muted check is worse than no check because it still looks like coverage. So the alarm
    threshold uses the job's 95th-percentile gap — the longest silence it has shown while
    healthy — while the median is kept only for the human-readable "expected every".
    """
    times = sorted(r["dt"] for r in runs)
    if len(times) < 3:
        return None
    gaps = sorted((b - a for a, b in zip(times, times[1:])),
                  key=lambda g: g.total_seconds())
    seconds = [g.total_seconds() for g in gaps]
    return gaps[len(gaps) // 2], timedelta(seconds=percentile(seconds, 95))


def silent(rows: list[dict], factor: float = 1.5) -> list[dict]:
    """Jobs that have stopped reporting, judged against their own learned cadence.

    A fixed threshold cannot work: an hourly watchdog and a weekly report have nothing in
    common except that both go quiet the same way. So the rhythm is learned per job, and
    the alarm fires at `factor` times the LONGEST SILENCE THE JOB HAS SHOWN WHILE HEALTHY
    (see cadence() for why the median is the wrong baseline).

    `factor` is the remaining judgement call. Lower it and a job that skips once pages you;
    raise it and a daily job can be dead for a week. There is no correct value — only a
    choice about which error you would rather make, and making that choice explicitly,
    rather than inheriting a default, is the work.
    """
    now = max(r["dt"] for r in rows)
    jobs: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        jobs[row["job"]].append(row)

    findings = []
    for name, runs in jobs.items():
        learned = cadence(runs)
        if learned is None:
            continue
        typical, longest_normal = learned
        if longest_normal.total_seconds() <= 0:
            continue
        quiet = now - max(r["dt"] for r in runs)
        if quiet > longest_normal * factor:
            findings.append({
                "job": name,
                "quiet_for": quiet,
                "expected_every": typical,
                "longest_normal": longest_normal,
                "missed": int(quiet / typical) - 1 if typical.total_seconds() else 0,
                "last_status": max(runs, key=lambda r: r["dt"])["status"],
            })
    return sorted(findings, key=lambda f: -f["quiet_for"].total_seconds())


def weekly(rows: list[dict]) -> dict[str, list[dict]]:
    """Tokens and failure rate per job per week — the weekly review, computed.

    Each bucket is flagged `partial` when the data does not cover the whole week. This is
    not bookkeeping: a partial bucket compared against a full one shows a spectacular drop
    that is entirely an artifact of when you ran the report. It is the single easiest way to
    manufacture a trend that is not there, and it is convincing precisely because the number
    is arithmetically correct.
    """
    if not rows:
        return {}
    first, last = rows[0]["dt"], rows[-1]["dt"]

    def week_start(dt):
        return (dt - timedelta(days=dt.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0)

    buckets: dict[tuple[str, datetime], list[dict]] = defaultdict(list)
    for row in rows:
        buckets[(row["job"], week_start(row["dt"]))].append(row)

    out: dict[str, list[dict]] = defaultdict(list)
    for (job, start), runs in sorted(buckets.items()):
        end = start + timedelta(days=7)
        failures = sum(1 for r in runs if r["status"] == "failed")
        out[job].append({
            "week": start.strftime("%Y-%m-%d"),
            "tokens": sum(r["tokens"] for r in runs),
            "failure_rate": failures / len(runs),
            "partial": start < first or end > last,
        })
    return out


def fmt(delta: timedelta) -> str:
    hours = delta.total_seconds() / 3600
    return f"{hours:.0f}h" if hours < 48 else f"{hours / 24:.1f}d"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=Path, default=RUNS)
    parser.add_argument("--silent", action="store_true")
    parser.add_argument("--trend", action="store_true")
    parser.add_argument("--job")
    parser.add_argument("--factor", type=float, default=1.5,
                        help="alarm at this multiple of the job's longest healthy gap")
    parser.add_argument("--jump", type=float, default=0.40,
                        help="week-over-week token increase that warrants a look")
    args = parser.parse_args()

    rows = load(args.runs)
    if args.job:
        rows = [r for r in rows if r["job"] == args.job]
        if not rows:
            print(f"no runs for {args.job!r}", file=sys.stderr)
            return 2

    if args.silent:
        findings = silent(rows, args.factor)
        if not findings:
            print("every job is reporting within its usual cadence.")
            return 0
        print("JOBS THAT HAVE STOPPED REPORTING\n")
        for f in findings:
            print(f"  {f['job']}: quiet for {fmt(f['quiet_for'])}, "
                  f"usually every {fmt(f['expected_every'])}, "
                  f"longest healthy gap {fmt(f['longest_normal'])} "
                  f"(~{f['missed']} missed; last run: {f['last_status']})")
        print("\nNothing generated an alert for any of these, because nothing happened.")
        print("That is the point: a monitor watching for bad events cannot see a job that")
        print("stopped producing events at all. Absence needs its own check.")
        return 1

    if args.trend:
        print(f"{'job':<18}{'week':<12}{'tokens':>12}{'fail rate':>11}{'change':>9}")
        print("-" * 64)
        flagged, saw_partial = [], False
        for job, weeks in weekly(rows).items():
            previous = None
            for bucket in weeks:
                change = ""
                if bucket["partial"]:
                    saw_partial = True
                    change = "partial"
                elif previous is not None and previous > 0:
                    delta = (bucket["tokens"] - previous) / previous
                    change = f"{delta:+.0%}"
                    if delta > args.jump:
                        flagged.append((job, bucket["week"], delta))
                print(f"{job:<18}{bucket['week']:<12}{bucket['tokens']:>12,}"
                      f"{bucket['failure_rate']:>10.0%}{change:>9}")
                # A partial week is not a comparison baseline either.
                previous = None if bucket["partial"] else bucket["tokens"]
            print()
        if flagged:
            print(f"Week-over-week token jumps over {args.jump:.0%}:")
            for job, week, delta in flagged:
                print(f"  {job} in week of {week}: {delta:+.0%}")
            print("\nInvestigate before the next review, not at it. A jump is usually a")
            print("prompt change, a retry storm, or a trajectory that got longer — and the")
            print("first two are invisible in a pass rate.\n")
        if saw_partial:
            print("Weeks marked `partial` are not fully covered by the data, so no change")
            print("is computed for them and they are not used as a baseline. Comparing a")
            print("partial week against a full one manufactures a collapse that is not")
            print("there — and it is convincing, because the arithmetic is correct.")
        return 0

    stats = per_job(rows)
    print(f"{'job':<18}{'runs':>6}{'fail':>7}{'p50':>8}{'p95':>8}"
          f"{'mean':>8}{'steps':>7}{'Mtok':>8}")
    print("-" * 70)
    for name, s in sorted(stats.items(), key=lambda kv: -kv[1]["failure_rate"]):
        print(f"{name:<18}{s['runs']:>6}{s['failure_rate']:>6.0%}"
              f"{s['p50']:>8.1f}{s['p95']:>8.1f}{s['mean']:>8.1f}"
              f"{s['steps']:>7.1f}{s['tokens'] / 1e6:>8.2f}")
    print()
    worst = max(stats.items(), key=lambda kv: kv[1]["failure_rate"])
    if worst[1]["failure_rate"] > 0.1:
        print(f"{worst[0]} fails {worst[1]['failure_rate']:.0%} of the time "
              f"({worst[1]['top_error']!r}).")
        print("A job that retries its way to success still costs tokens on every attempt,")
        print("and a failure rate nobody looks at is a budget line nobody owns.\n")
    # The RATIO, not the absolute difference: a slow job with a slightly slower tail is
    # ordinary, while a fast job with a tail twice its mean has an incident inside it that
    # the mean is averaging away.
    gap = max((kv for kv in stats.items() if kv[1]["mean"] > 0),
              key=lambda kv: kv[1]["p95"] / kv[1]["mean"])
    ratio = gap[1]["p95"] / gap[1]["mean"]
    print(f"Longest tail relative to its own mean: {gap[0]} "
          f"(mean {gap[1]['mean']:.0f}s, p95 {gap[1]['p95']:.0f}s — {ratio:.1f}x).")
    print("Report p95. The mean is the statistic that hides incidents: this job looks")
    print("healthy on average and is twice that slow for one user in twenty.")
    print("\nRun --silent next: this table only describes jobs that are still reporting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
