#!/usr/bin/env python3
"""Score eval outputs with a rubric LLM-as-judge, with the known biases handled.

    python3 judge.py --results after.json --judge-model gemini-pro --out scores.json
    python3 judge.py --results after.json --judge-model gemini-pro --calibrate

A judge is a measuring instrument, so this script is built around the three ways the
instrument is known to lie:

  * SELF-PREFERENCE — a model rates its own output higher. The script REFUSES to run
    when --judge-model matches the model under test. That is a hard error, not a warning:
    a self-graded eval is worse than no eval, because it comes with a number.
  * POSITION BIAS — in a pairwise comparison, judges favour whichever answer came first.
    Pairwise mode scores every pair twice with the order swapped, and reports a verdict
    only when both orders agree; disagreement is recorded as a TIE, which is the honest
    reading.
  * SCALE DRIFT — "rate this 1-5" means nothing until the anchors are written down.
    rubric.md defines what each point IS, and --calibrate re-scores a set of pinned
    examples so you can see the judge agreeing (or not) with a human before you trust it.

Everything here calls the agent through `hermes chat -q`, so the judge is whatever model
your Hermes can reach. Output is JSON; a judge whose scores you cannot diff is a vibe.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCORE_RE = re.compile(r"^\s*([A-Za-z_]+)\s*[:=]\s*([1-5])\b", re.M)

SINGLE_TEMPLATE = """You are grading one response from an AI agent. Apply the rubric \
exactly as written. Do not reward style, length, or confidence.

RUBRIC
{rubric}

TASK GIVEN TO THE AGENT
{prompt}

AGENT RESPONSE
{output}

Reply with exactly one line per rubric dimension, in the form `dimension: N` where N is \
1-5, then one line starting with `because:` giving your single strongest reason. No other \
text."""

PAIR_TEMPLATE = """You are comparing two responses to the same task. Apply the rubric \
exactly as written. Judge only the content.

RUBRIC
{rubric}

TASK
{prompt}

RESPONSE A
{a}

RESPONSE B
{b}

Reply with exactly one line: `winner: A` or `winner: B` or `winner: TIE`, then one line \
starting with `because:`. No other text."""


def ask(model: str, prompt: str, timeout: int) -> str:
    cmd = ["hermes", "chat", "-q", prompt, "--oneshot", "-t", "none", "-m", model]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return ""
    except OSError as exc:
        print(f"could not run hermes: {exc}", file=sys.stderr)
        return ""
    return (proc.stdout or "") + (proc.stderr or "")


def parse_scores(reply: str) -> dict[str, int]:
    return {m.group(1).lower(): int(m.group(2)) for m in SCORE_RE.finditer(reply)}


def parse_winner(reply: str) -> str:
    match = re.search(r"winner\s*[:=]\s*(A|B|TIE)", reply, re.I)
    return match.group(1).upper() if match else "TIE"


def judge_single(results: dict, rubric: str, model: str, timeout: int) -> list[dict]:
    scored = []
    for run in results["runs"]:
        reply = ask(model, SINGLE_TEMPLATE.format(
            rubric=rubric, prompt=run["task"], output=run["output"]), timeout)
        scores = parse_scores(reply)
        scored.append({
            "task": run["task"], "attempt": run["attempt"],
            "deterministic_passed": run["passed"],
            "scores": scores,
            "mean": round(sum(scores.values()) / len(scores), 2) if scores else None,
            "reason": next((ln.partition(":")[2].strip()
                            for ln in reply.splitlines()
                            if ln.lower().startswith("because:")), ""),
            "unparsed": not scores,
        })
        print("." if scores else "?", end="", flush=True)
    print()
    return scored


def judge_pairs(a_results: dict, b_results: dict, rubric: str, model: str,
                timeout: int, rng: random.Random) -> list[dict]:
    """Pairwise with order swapped. A verdict survives only if both orders agree."""
    by_key = {(r["task"], r["attempt"]): r for r in b_results["runs"]}
    verdicts = []
    for run in a_results["runs"]:
        other = by_key.get((run["task"], run["attempt"]))
        if other is None:
            continue
        # First presentation order is randomised so a systematic parse failure cannot
        # quietly align with "A is always the baseline".
        forward = rng.random() < 0.5
        first, second = (run, other) if forward else (other, run)
        r1 = parse_winner(ask(model, PAIR_TEMPLATE.format(
            rubric=rubric, prompt=run["task"],
            a=first["output"], b=second["output"]), timeout))
        r2 = parse_winner(ask(model, PAIR_TEMPLATE.format(
            rubric=rubric, prompt=run["task"],
            a=second["output"], b=first["output"]), timeout))

        def resolve(letter: str, first_is_a: bool) -> str:
            if letter == "TIE":
                return "TIE"
            picked_first = (letter == "A")
            picked_baseline = picked_first == first_is_a
            return "baseline" if picked_baseline else "candidate"

        v1, v2 = resolve(r1, forward), resolve(r2, not forward)
        agreed = v1 == v2
        verdicts.append({
            "task": run["task"], "attempt": run["attempt"],
            "order_1": v1, "order_2": v2,
            "verdict": v1 if agreed else "TIE",
            "position_bias_detected": not agreed,
        })
        print("." if agreed else "!", end="", flush=True)
    print()
    return verdicts


def calibrate(rubric: str, model: str, timeout: int) -> list[dict]:
    """Re-score the pinned examples and show where the judge disagrees with a human.

    Run this BEFORE trusting a judge, and again whenever you change the judge model or
    the rubric. A judge that cannot reproduce your own labels on four obvious cases is
    not going to be right on the ambiguous ones.
    """
    pinned = json.loads((HERE / "calibration.json").read_text(encoding="utf-8"))
    out = []
    for case in pinned["cases"]:
        reply = ask(model, SINGLE_TEMPLATE.format(
            rubric=rubric, prompt=case["prompt"], output=case["output"]), timeout)
        scores = parse_scores(reply)
        deltas = {k: scores.get(k, 0) - v for k, v in case["human"].items()}
        worst = max((abs(d) for d in deltas.values()), default=0)
        out.append({
            "id": case["id"], "human": case["human"], "judge": scores,
            "delta": deltas, "max_abs_delta": worst,
            "agrees": worst <= 1,
        })
        print("." if worst <= 1 else "X", end="", flush=True)
    print()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, help="results JSON from eval_runner.py")
    parser.add_argument("--against", type=Path,
                        help="second results file: switches to pairwise mode")
    parser.add_argument("--judge-model", required=True,
                        help="MUST differ from the model under test")
    parser.add_argument("--rubric", type=Path, default=HERE / "rubric.md")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--seed", type=int, default=0, help="seed for presentation order")
    parser.add_argument("--calibrate", action="store_true",
                        help="score calibration.json instead of results")
    args = parser.parse_args()

    rubric = args.rubric.read_text(encoding="utf-8")

    # Validate the REQUEST before the environment. A self-graded eval is a configuration
    # error whether or not a CLI happens to be installed, and reporting "no hermes on
    # PATH" for it would send you off fixing the wrong thing.
    if args.results:
        preview = json.loads(args.results.read_text(encoding="utf-8"))
        if preview.get("dry_run"):
            print("refusing to judge a --dry-run result.", file=sys.stderr)
            return 2
        under_test = (preview.get("model") or "").strip()
        if under_test and under_test == args.judge_model.strip():
            print(f"refusing to judge {under_test!r} with itself: self-preference inflates "
                  "the score. Pick a different (usually stronger) judge model.",
                  file=sys.stderr)
            return 2
    elif not args.calibrate:
        print("--results is required unless --calibrate", file=sys.stderr)
        return 2

    if not shutil.which("hermes"):
        print("no `hermes` on PATH.", file=sys.stderr)
        return 2

    if args.calibrate:
        report = calibrate(rubric, args.judge_model, args.timeout)
        disagreed = [c for c in report if not c["agrees"]]
        for case in report:
            flag = "ok " if case["agrees"] else "OFF"
            print(f"{flag} {case['id']:<24} human={case['human']} judge={case['judge']}")
        payload = {"mode": "calibrate", "judge_model": args.judge_model, "cases": report}
        if args.out:
            args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        if disagreed:
            print(f"\n{len(disagreed)} of {len(report)} pinned cases are off by more than "
                  "1 point. Fix the rubric's anchors or change the judge model before "
                  "using this judge on real work.", file=sys.stderr)
            return 1
        print("\nJudge reproduces every pinned label within 1 point.")
        return 0

    results = preview
    if args.against:
        other = json.loads(args.against.read_text(encoding="utf-8"))
        verdicts = judge_pairs(results, other, rubric, args.judge_model,
                               args.timeout, random.Random(args.seed))
        wins = sum(v["verdict"] == "candidate" for v in verdicts)
        losses = sum(v["verdict"] == "baseline" for v in verdicts)
        ties = sum(v["verdict"] == "TIE" for v in verdicts)
        flips = sum(v["position_bias_detected"] for v in verdicts)
        print(f"\ncandidate {wins} / baseline {losses} / tie {ties}")
        print(f"order-dependent verdicts (counted as ties): {flips} of {len(verdicts)}")
        if flips > len(verdicts) / 4 and verdicts:
            print("More than a quarter of verdicts flipped when the order flipped. "
                  "This judge is measuring position, not quality — tighten the rubric.")
        payload = {"mode": "pairwise", "judge_model": args.judge_model,
                   "verdicts": verdicts}
    else:
        scored = judge_single(results, rubric, args.judge_model, args.timeout)
        usable = [s for s in scored if s["mean"] is not None]
        if usable:
            print(f"\nmean rubric score: "
                  f"{sum(s['mean'] for s in usable) / len(usable):.2f} over {len(usable)} runs")
        unparsed = [s for s in scored if s["unparsed"]]
        if unparsed:
            print(f"{len(unparsed)} judge replies did not parse — they are EXCLUDED, "
                  "which biases the mean. Investigate rather than ignore.")
        payload = {"mode": "single", "judge_model": args.judge_model,
                   "model_under_test": results.get("model"), "scored": scored}

    if args.out:
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
