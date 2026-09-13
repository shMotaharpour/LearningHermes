#!/usr/bin/env python3
"""Model what a capstone workflow costs before the invoice tells you. Chapter 16.

    python3 cost_model.py
    python3 cost_model.py --sensitivity
    python3 cost_model.py --what-if daily-briefing:tier=cheap

"How much will this cost to run?" is a senior interview question, and "I'd check insights"
is a junior answer — it tells you what you already spent, on a system that already exists.
A model tells you what a design will cost before you build it, and, more usefully, WHICH
LEVER MATTERS. That second thing is the whole point: most people's instinct about where
agent spend goes is wrong by an order of magnitude.

Standard library only. Prices live in workflow.json and are PLACEHOLDERS you must replace.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SPEC = Path(__file__).parent / "workflow.json"
DAYS = 30


def job_cost(job: dict, models: dict) -> dict:
    """Monthly cost and latency for one job.

    Two things people leave out of a first model, both of which change the answer:

    * CACHING. A scheduled job re-sends a nearly identical prompt every run, so most of its
      input is cache-eligible. Ignoring it overstates cost by multiples on exactly the jobs
      you run most often.
    * RETRIES. A failure is not free — the tokens were spent before it failed. A 5% failure
      rate is 5% more spend, plus whatever the retry costs.
    """
    model = models[job["tier"]]
    runs = job["runs_per_day"] * DAYS
    effective_runs = runs * (1 + job.get("failure_rate", 0.0))

    cached = job["input_tokens"] * job.get("cached_fraction", 0.0)
    fresh = job["input_tokens"] - cached

    input_cost = (fresh * model["input_per_mtok"]
                  + cached * model["cached_input_per_mtok"]) / 1_000_000
    output_cost = job["output_tokens"] * model["output_per_mtok"] / 1_000_000
    per_run = input_cost + output_cost

    # Latency is dominated by the number of model turns, not by one call: every tool call
    # costs another round trip through the loop (Chapter 01).
    turns = job.get("tool_calls", 0) + 1
    latency = turns * model["typical_latency_s"]

    return {
        "name": job["name"],
        "tier": job["tier"],
        "runs_per_month": runs,
        "per_run": per_run,
        "monthly": per_run * effective_runs,
        "monthly_tokens": (job["input_tokens"] + job["output_tokens"]) * effective_runs,
        "latency_s": latency,
    }


def model_workflow(spec: dict) -> list[dict]:
    return [job_cost(j, spec["models"]) for j in spec["jobs"]]


def table(rows: list[dict], currency: str) -> None:
    print(f"{'job':<18}{'tier':<8}{'runs/mo':>9}{'per run':>10}"
          f"{'per month':>12}{'latency':>10}")
    print("-" * 67)
    for row in sorted(rows, key=lambda r: -r["monthly"]):
        print(f"{row['name']:<18}{row['tier']:<8}{row['runs_per_month']:>9}"
              f"{row['per_run']:>10.4f}{row['monthly']:>12.2f}{row['latency_s']:>9.0f}s")
    total = sum(r["monthly"] for r in rows)
    tokens = sum(r["monthly_tokens"] for r in rows)
    print("-" * 67)
    print(f"{'TOTAL':<18}{'':<8}{'':>9}{'':>10}{total:>12.2f} {currency}")
    print(f"{'':<18}{tokens / 1_000_000:>48.1f} Mtok/month")


def sensitivity(spec: dict) -> None:
    """Which single change moves the number most? The answer is rarely the model.

    Each lever is applied to the whole workflow and the total is recomputed. Ranking them
    is what turns a cost model from a number into a decision.
    """
    base = sum(r["monthly"] for r in model_workflow(spec))
    levers: list[tuple[str, dict]] = []

    def clone(mutate) -> dict:
        copy = json.loads(json.dumps(spec))
        mutate(copy)
        return copy

    def set_all_cheap(s):
        for j in s["jobs"]:
            j["tier"] = "cheap"

    def halve_input(s):
        for j in s["jobs"]:
            j["input_tokens"] = int(j["input_tokens"] * 0.5)

    def no_cache(s):
        for j in s["jobs"]:
            j["cached_fraction"] = 0.0

    def perfect_cache(s):
        for j in s["jobs"]:
            j["cached_fraction"] = 0.95

    def halve_frequency(s):
        for j in s["jobs"]:
            j["runs_per_day"] = max(1, j["runs_per_day"] // 2) if j["runs_per_day"] > 1 \
                else j["runs_per_day"]

    def halve_output(s):
        for j in s["jobs"]:
            j["output_tokens"] = int(j["output_tokens"] * 0.5)

    levers = [
        ("everything on the cheap tier", clone(set_all_cheap)),
        ("halve every prompt (Ch 03)", clone(halve_input)),
        ("prompt caching off", clone(no_cache)),
        ("near-perfect caching", clone(perfect_cache)),
        ("halve run frequency", clone(halve_frequency)),
        ("halve every output", clone(halve_output)),
    ]

    print(f"{'lever':<32}{'monthly':>11}{'change':>10}")
    print("-" * 53)
    print(f"{'(baseline)':<32}{base:>11.2f}{'':>10}")
    results = []
    for label, variant in levers:
        total = sum(r["monthly"] for r in model_workflow(variant))
        results.append((label, total, (total - base) / base if base else 0))
    for label, total, delta in sorted(results, key=lambda r: r[1]):
        print(f"{label:<32}{total:>11.2f}{delta:>+9.0%}")
    print()
    print("Read the ORDER, not the numbers — the prices in workflow.json are placeholders.")
    print("The ranking is the finding: it tells you which conversation to have with your")
    print("team, and it will reorder on YOUR workflow. Two things to notice here:")
    print()
    print("  * 'prompt caching off' is the only lever that makes things WORSE, and by more")
    print("    than most levers improve them. That is the size of a saving you already have")
    print("    and could lose by changing a prompt prefix — an invisible regression with no")
    print("    error attached. Chapter 03 is where it is earned.")
    print("  * A tier swap looks decisive when one expensive job dominates. Check whether")
    print("    it still leads once you weight by how much you actually care about that")
    print("    job's output quality — the cheap tier is only free if the answer survives.")


def what_if(spec: dict, changes: list[str]) -> dict:
    """Apply `job:field=value` overrides so a proposal can be priced before it is built."""
    copy = json.loads(json.dumps(spec))
    for change in changes:
        target, _, assignment = change.partition(":")
        field, _, raw = assignment.partition("=")
        for job in copy["jobs"]:
            if job["name"] != target:
                continue
            current = job.get(field)
            if isinstance(current, bool) or current is None or isinstance(current, str):
                job[field] = raw
            elif isinstance(current, int):
                job[field] = int(float(raw))
            else:
                job[field] = float(raw)
    return copy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", type=Path, default=SPEC)
    parser.add_argument("--sensitivity", action="store_true",
                        help="rank the levers by how much each moves the total")
    parser.add_argument("--what-if", action="append", default=[],
                        metavar="JOB:FIELD=VALUE",
                        help="price a change before building it, e.g. pr-triage:tier=strong")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    placeholder = any(m["name"].startswith("<") for m in spec["models"].values())

    if args.what_if:
        before = sum(r["monthly"] for r in model_workflow(spec))
        spec = what_if(spec, args.what_if)
        rows = model_workflow(spec)
        after = sum(r["monthly"] for r in rows)
        table(rows, spec["currency"])
        print(f"\nwhat-if {args.what_if}: {before:.2f} -> {after:.2f} "
              f"({(after - before) / before:+.0%})")
    elif args.sensitivity:
        sensitivity(spec)
    else:
        rows = model_workflow(spec)
        if args.json:
            print(json.dumps(rows, indent=2))
            return 0
        table(rows, spec["currency"])
        print("\nNote the script-only job: zero tokens, zero cost, and it is the one that")
        print("wakes you at 3am. Not every automation needs a model (Chapter 07).")

    if placeholder:
        print("\n!! The prices in this spec are PLACEHOLDERS, not quotes from any provider.")
        print("   Replace them with your provider's published rates before believing any")
        print("   number above. A cost model built on invented prices is worse than none,")
        print("   because it produces a confident answer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
