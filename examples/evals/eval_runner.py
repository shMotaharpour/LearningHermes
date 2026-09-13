#!/usr/bin/env python3
"""Run a frozen eval set against a Hermes agent and write a results file.

Standard library only, like everything else in this repo: an eval harness that needs
its own dependency tree is one more thing to keep green.

    python3 eval_runner.py --tasks tasks.json --out baseline.json
    python3 eval_runner.py --tasks tasks.json --out after.json --model gemini-flash
    python3 eval_runner.py --tasks tasks.json --out /dev/null --dry-run   # no agent calls

What it does per task, `repeats` times:
  1. builds a throwaway fixture directory so the task has a known right answer,
  2. runs `hermes chat -q <prompt> -t <toolsets> --oneshot`,
  3. applies the task's deterministic checks to stdout,
  4. records pass/fail, wall time, and the raw output.

What it deliberately does NOT do: decide whether a pass-rate difference means anything.
That is compare.py's job, and separating them is the point — a runner that also declares
winners is how "it feels better" gets a number attached to it.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# A fixture the tasks can assert against. Frozen on purpose: an eval set whose expected
# answers move is not a regression suite, it is a mood ring.
FIXTURE = {
    "notes.txt": "Project notes\nNo contact details here.\nThird line.\n",
    "small.txt": "one\ntwo\n",
    "big.txt": "".join(f"line {i}\n" for i in range(1, 13)),
    "data.csv": "a,b\n1,2\n",
}
EXPECTED = {
    "expected_file_count": len(FIXTURE),
    "expected_notes_lines": FIXTURE["notes.txt"].count("\n"),
    "expected_big_lines": FIXTURE["big.txt"].count("\n"),
}


def build_fixture(root: Path) -> dict[str, float]:
    """Materialise the fixture and return a fingerprint for the workdir_unchanged check."""
    for name, body in FIXTURE.items():
        (root / name).write_text(body, encoding="utf-8")
    return fingerprint(root)


def fingerprint(root: Path) -> dict[str, int]:
    """Name -> size for every file under root. Cheap, and enough to catch a write."""
    return {
        str(p.relative_to(root)): p.stat().st_size
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def substitute(text: str, workdir: Path) -> str:
    values = {"workdir": str(workdir), **{k: str(v) for k, v in EXPECTED.items()}}
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    return text


def apply_check(check: dict, output: str, workdir: Path, before: dict) -> tuple[bool, str]:
    """Return (passed, explanation). Explanations end up in the results file verbatim."""
    kind = check["kind"]
    if kind == "contains":
        value = check["value"]
        return (value in output), f"output contains {value!r}"
    if kind == "regex":
        pattern = substitute(check["pattern"], workdir)
        return bool(re.search(pattern, output)), f"output matches /{pattern}/"
    if kind == "not_regex":
        pattern = substitute(check["pattern"], workdir)
        return not re.search(pattern, output), f"output does NOT match /{pattern}/"
    if kind == "json_parses":
        text = strip_fence(output)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            return False, f"output parses as JSON (it did not: {exc.msg})"
        wanted = check.get("as")
        if wanted == "array" and not isinstance(parsed, list):
            return False, f"output parses as a JSON array (got {type(parsed).__name__})"
        if wanted == "object" and not isinstance(parsed, dict):
            return False, f"output parses as a JSON object (got {type(parsed).__name__})"
        return True, "output parses as JSON"
    if kind == "workdir_unchanged":
        after = fingerprint(workdir)
        if after == before:
            return True, "workdir unchanged"
        changed = sorted(set(after.items()) ^ set(before.items()))
        return False, f"workdir unchanged (these differ: {changed})"
    raise ValueError(f"unknown check kind: {kind!r}")


def strip_fence(output: str) -> str:
    """Agents wrap JSON in code fences even when told not to; judge the payload."""
    text = output.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def run_agent(prompt: str, toolsets: str, workdir: Path, model: str | None,
              timeout: int) -> tuple[str, int | None]:
    cmd = ["hermes", "chat", "-q", prompt, "--oneshot", "-t", toolsets]
    if model:
        cmd += ["-m", model]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=workdir, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return f"<<TIMEOUT after {timeout}s>>", None
    except OSError as exc:
        return f"<<COULD NOT RUN hermes: {exc}>>", None
    return (proc.stdout or "") + (proc.stderr or ""), proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tasks", type=Path, default=Path(__file__).parent / "tasks.json")
    parser.add_argument("--out", type=Path, required=True, help="results JSON to write")
    parser.add_argument("--model", help="override the model under test (default: your config's)")
    parser.add_argument("--repeats", type=int, help="override the task file's repeats")
    parser.add_argument("--timeout", type=int, default=180, help="per-run timeout in seconds")
    parser.add_argument("--only", action="append", help="run only this task id (repeatable)")
    parser.add_argument("--dry-run", action="store_true",
                        help="exercise the harness without calling the agent")
    args = parser.parse_args()

    spec = json.loads(args.tasks.read_text(encoding="utf-8"))
    repeats = args.repeats or spec.get("repeats", 5)
    toolsets = spec.get("toolsets", "terminal,file")
    tasks = [t for t in spec["tasks"] if not args.only or t["id"] in args.only]
    if not tasks:
        print("no tasks selected", file=sys.stderr)
        return 2

    if not args.dry_run and not shutil.which("hermes"):
        print("no `hermes` on PATH — install it, or pass --dry-run to test the harness.",
              file=sys.stderr)
        return 2

    runs = []
    for task in tasks:
        for attempt in range(1, repeats + 1):
            with tempfile.TemporaryDirectory(prefix="hermes-eval-") as tmp:
                workdir = Path(tmp)
                before = build_fixture(workdir)
                prompt = substitute(task["prompt"], workdir)
                started = time.monotonic()
                if args.dry_run:
                    output, code = "<<DRY RUN: no agent was called>>", None
                else:
                    output, code = run_agent(prompt, toolsets, workdir, args.model, args.timeout)
                elapsed = round(time.monotonic() - started, 2)
                results = [
                    dict(zip(("passed", "check"),
                             apply_check(c, output, workdir, before)))
                    for c in task["checks"]
                ]
            passed = all(r["passed"] for r in results)
            runs.append({
                "task": task["id"], "attempt": attempt, "passed": passed,
                "seconds": elapsed, "exit_code": code,
                "checks": results, "output": output.strip()[:4000],
            })
            mark = "." if passed else "F"
            print(mark, end="", flush=True)
    print()

    payload = {
        "model": args.model or "<config default>",
        "toolsets": toolsets,
        "repeats": repeats,
        "tasks": [t["id"] for t in tasks],
        "dry_run": args.dry_run,
        "runs": runs,
    }
    if str(args.out) != "/dev/null":
        args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    for task in tasks:
        task_runs = [r for r in runs if r["task"] == task["id"]]
        wins = sum(r["passed"] for r in task_runs)
        print(f"{task['id']:<20} {wins}/{len(task_runs)}")
    total = sum(r["passed"] for r in runs)
    print(f"{'TOTAL':<20} {total}/{len(runs)}  -> {args.out}")
    print("\nA pass rate is not a verdict. Run compare.py against a baseline before "
          "you claim a change helped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
