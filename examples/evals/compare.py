#!/usr/bin/env python3
"""Compare two eval runs and say whether the difference is signal or noise.

    python3 compare.py baseline.json after.json
    python3 compare.py baseline.json after.json --min-effect 0.10

This is the half of an eval harness that people skip, and skipping it is why
"the new prompt scores 4/5 instead of 3/5" gets shipped. 4/5 vs 3/5 is nothing:
with five samples, a coin lands 4 heads about 19% of the time.

Method (standard library, no scipy):
  * Wilson score interval for each pass rate. It is the right interval for small N —
    the textbook `p +- 1.96*sqrt(p(1-p)/n)` interval is badly wrong near 0 and 1, and
    gives a zero-width interval at exactly 0/n or n/n, which is nonsense.
  * A two-sided two-proportion z-test for the difference, reported as a p-value.
  * An explicit "how many runs would you have needed" number, because the useful
    answer to an inconclusive eval is usually "collect more", not "argue harder".

Exit code is 1 when a regression is BOTH statistically distinguishable and larger
than --min-effect, so this is usable as the gate in a nightly job.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

Z = 1.959963984540054  # two-sided 95%


def wilson(successes: int, n: int, z: float = Z) -> tuple[float, float]:
    """95% Wilson score interval. Defined and sane at 0/n and n/n."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def normal_sf(x: float) -> float:
    """P(Z > x) for the standard normal, via erfc. No scipy needed."""
    return 0.5 * math.erfc(x / math.sqrt(2))


def two_proportion_p(s1: int, n1: int, s2: int, n2: int) -> float:
    """Two-sided p-value for H0: the two pass rates are equal (pooled z-test)."""
    if n1 == 0 or n2 == 0:
        return 1.0
    p1, p2 = s1 / n1, s2 / n2
    pooled = (s1 + s2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    return 2 * normal_sf(abs(p1 - p2) / se)


def runs_needed(p1: float, p2: float, power: float = 0.80) -> int | None:
    """Per-arm N to detect a p1 vs p2 difference at 95% confidence and `power`.

    The standard two-proportion sample-size formula. Returned so an inconclusive
    result comes with the actionable number rather than a shrug.
    """
    delta = abs(p1 - p2)
    if delta == 0:
        return None
    z_beta = {0.80: 0.8416, 0.90: 1.2816}.get(power, 0.8416)
    pbar = (p1 + p2) / 2
    n = ((Z * math.sqrt(2 * pbar * (1 - pbar)) + z_beta *
          math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (delta ** 2)
    return math.ceil(n)


def tally(payload: dict) -> dict[str, tuple[int, int]]:
    """task id -> (passes, runs), plus an OVERALL row."""
    out: dict[str, list[int]] = {}
    for run in payload["runs"]:
        entry = out.setdefault(run["task"], [0, 0])
        entry[0] += 1 if run["passed"] else 0
        entry[1] += 1
    result = {k: (v[0], v[1]) for k, v in out.items()}
    total_pass = sum(v[0] for v in result.values())
    total_runs = sum(v[1] for v in result.values())
    result["OVERALL"] = (total_pass, total_runs)
    return result


def seconds(payload: dict) -> float:
    vals = [r["seconds"] for r in payload["runs"] if isinstance(r.get("seconds"), (int, float))]
    return sum(vals) / len(vals) if vals else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--alpha", type=float, default=0.05,
                        help="p-value below which a difference is called distinguishable")
    parser.add_argument("--min-effect", type=float, default=0.0,
                        help="ignore regressions smaller than this (0.10 = 10 points)")
    args = parser.parse_args()

    base = json.loads(args.baseline.read_text(encoding="utf-8"))
    cand = json.loads(args.candidate.read_text(encoding="utf-8"))
    if base.get("dry_run") or cand.get("dry_run"):
        print("refusing to compare a --dry-run result: it measures the harness, "
              "not the agent.", file=sys.stderr)
        return 2

    b, c = tally(base), tally(cand)
    print(f"baseline : {args.baseline}  (model: {base.get('model')})")
    print(f"candidate: {args.candidate}  (model: {cand.get('model')})")
    print()
    header = f"{'task':<20} {'baseline':>16} {'candidate':>16} {'delta':>8} {'p':>8}  verdict"
    print(header)
    print("-" * len(header))

    regressed = False
    for task in sorted(set(b) | set(c), key=lambda t: (t == "OVERALL", t)):
        s1, n1 = b.get(task, (0, 0))
        s2, n2 = c.get(task, (0, 0))
        p1 = s1 / n1 if n1 else 0.0
        p2 = s2 / n2 if n2 else 0.0
        lo1, hi1 = wilson(s1, n1)
        lo2, hi2 = wilson(s2, n2)
        pval = two_proportion_p(s1, n1, s2, n2)
        delta = p2 - p1

        if pval >= args.alpha:
            need = runs_needed(p1, p2)
            verdict = "no distinguishable difference"
            if need and need > max(n1, n2):
                verdict += f" (need ~{need}/arm to call a {abs(delta):.0%} gap)"
        elif delta < 0 and abs(delta) >= args.min_effect:
            verdict = "REGRESSION"
            if task != "OVERALL":
                regressed = True
        elif delta < 0:
            verdict = f"worse, but under --min-effect {args.min_effect:.0%}"
        else:
            verdict = "improvement"

        print(f"{task:<20} {s1:>3}/{n1:<3}[{lo1:.2f},{hi1:.2f}] "
              f"{s2:>3}/{n2:<3}[{lo2:.2f},{hi2:.2f}] "
              f"{delta:>+7.0%} {pval:>8.3f}  {verdict}")

    sb, sc = seconds(base), seconds(cand)
    print()
    print(f"mean seconds/run: {sb:.1f} -> {sc:.1f} ({sc - sb:+.1f})")
    print("Brackets are 95% Wilson intervals. Overlapping intervals and p >= "
          f"{args.alpha} mean you have not measured a difference — you have measured noise.")
    print("Cost is not in this table because the runner does not collect it: pair every "
          "comparison with `hermes insights --days N` over the same window.")

    if regressed:
        print("\nREGRESSION on at least one task.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
