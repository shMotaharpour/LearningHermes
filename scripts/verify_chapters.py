#!/usr/bin/env python3
"""Re-check the `hermes` commands quoted in the chapters against the installed CLI.

Every chapter carries a `> **Verified:** <date> · Hermes Agent vX.Y.Z · recheck: ...`
header. This script is what makes that header checkable:

  * it extracts every `hermes ...` command from the chapter and exercise files,
  * resolves the subcommand path by running `hermes <path> --help` (the ONLY thing it
    executes; no state-changing command is ever run),
  * reports commands whose subcommand no longer resolves (hard failure) and commands whose
    options are not mentioned in the help output (soft, printed for review).

Usage:
    python3 scripts/verify_chapters.py                 # all chapters + exercises
    python3 scripts/verify_chapters.py --chapter 09    # one chapter
    python3 scripts/verify_chapters.py --only-unknown  # findings only
    python3 scripts/verify_chapters.py --json > out.json
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TIMEOUT_S = 25

# `hermes mcp add --command X --args ...`: everything after --args belongs to the spawned
# process, so later `--flags` are data rather than options of the hermes command.
VALUE_TAIL_FLAGS = {"--args"}

HEADER_VERSION_RE = re.compile(r">\s*\*\*Verified:\*\*[^\n]*?Hermes Agent v([0-9][0-9.]*)")
VERIFIED_LINE_RE = re.compile(r">\s*\*\*Verified:\*\*")
FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*\n(.*?)```", re.S)
INLINE_RE = re.compile(r"`([^`\n]+)`")
SHELL_META_RE = re.compile(r"[|&;<>$`\\!*?~\[\]()]")
QUOTED_RE = re.compile(r"'[^']*'|\"[^\"]*\"")


def has_shell_syntax(cmd: str) -> bool:
    """True when the line is shell composition rather than a plain `hermes ...` invocation.

    Quoted spans are removed first: a cron expression like `"0 6 * * *"` is data, not a glob.
    """
    try:
        shlex.split(cmd)
    except ValueError:
        return True
    return bool(SHELL_META_RE.search(QUOTED_RE.sub("", cmd)))
HERMES_CMD_RE = re.compile(r"^\s*(?:sudo\s+)?hermes\s+\S")


def _help(exe: str, args: list[str]) -> tuple[bool, str]:
    """Run `hermes <args> --help`; the only command this script executes."""
    try:
        proc = subprocess.run(
            [exe, *args, "--help"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
            stdin=subprocess.DEVNULL,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False, ""
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, out


def installed_version() -> str:
    exe = shutil.which("hermes")
    if not exe:
        return ""
    try:
        proc = subprocess.run(
            [exe, "--version"], capture_output=True, text=True, timeout=TIMEOUT_S,
            stdin=subprocess.DEVNULL,
        )
    except (subprocess.TimeoutExpired, OSError):
        return ""
    m = re.search(r"(\d+\.\d+\.\d+)", (proc.stdout or "") + (proc.stderr or ""))
    return m.group(1) if m else ""


def extract_commands(text: str) -> list[str]:
    """Every `hermes ...` command in fenced blocks and inline code spans."""
    commands: list[str] = []
    for block in FENCE_RE.findall(text):
        joined = block.replace("\\\n", " ")
        for line in joined.splitlines():
            line = re.sub(r"^\s*[\$#>]\s*", "", line)
            line = re.split(r"\s+#\s+", line)[0].strip()
            if HERMES_CMD_RE.match(line):
                commands.append(line)
    for span in INLINE_RE.findall(text):
        span = span.strip()
        if HERMES_CMD_RE.match(span):
            commands.append(span)
    return commands


def _tokenize(cmd: str) -> list[str]:
    try:
        return shlex.split(cmd, posix=True)[1:]  # drop 'hermes'
    except ValueError:
        return cmd.split()[1:]


def _flag_value_indices(tokens: list[str]) -> set[int]:
    """Indices of words that are the value of a preceding `--opt value` token."""
    values: set[int] = set()
    skip = False
    for i, tok in enumerate(tokens):
        if skip:
            values.add(i)
            skip = False
            continue
        if tok.startswith("-") and "=" not in tok:
            skip = True
    return values


def command_path(cmd: str) -> tuple[list[tuple[str, bool]], list[str]]:
    """Split a command into candidate subcommand paths and its long flags.

    Returns a list of `(path_string, is_option_value_free)` candidates, longest first, plus
    the `--flags` used. Nothing here executes the command.
    """
    tokens = _tokenize(cmd)
    flags: list[str] = []
    for idx, tok in enumerate(tokens):
        if not tok.startswith("--"):
            continue
        flags.append(tok.split("=", 1)[0])
        if tok in VALUE_TAIL_FLAGS:  # everything after, e.g. `--args --port 8321`, is a value
            break
    values = _flag_value_indices(tokens)

    # Two readings of the same command: every bare word, and — because a global option may
    # take a value (`hermes kanban --board default create <title>`) — a reading that drops
    # option values. Both are offered to the resolver, longest path first.
    plain = [i for i, tok in enumerate(tokens) if not tok.startswith("-")]
    without_values = [i for i in plain if i not in values]

    seen: set[str] = set()
    candidates: list[tuple[str, bool]] = []
    for variant in (plain, without_values):
        for n in range(len(variant), 0, -1):
            idxs = variant[:n]
            words = [tokens[i] for i in idxs]
            if not all(re.fullmatch(r"[a-z][a-z0-9-]*", w) for w in words):
                continue
            path_str = " ".join(words)
            if path_str in seen:
                continue
            seen.add(path_str)
            candidates.append((path_str, not (set(idxs) & values)))
    candidates.sort(key=lambda item: len(item[0].split()), reverse=True)
    return candidates, flags


def resolve(candidates: list[tuple[str, bool]], cache: dict[str, tuple[str, str]]) -> tuple[str, str]:
    """Deepest subcommand path the installed CLI accepts, plus its combined help text."""
    exe = shutil.which("hermes")
    if not exe:
        return "", ""
    best = ""
    best_help = ""
    for path_str, _plausible in candidates:
        if path_str not in cache:
            parts = path_str.split()
            resolved = ""
            help_text = ""
            for depth in range(len(parts), 0, -1):
                ok, out = _help(exe, parts[:depth])
                if ok:
                    resolved = " ".join(parts[:depth])
                    help_text = out
                    # include ancestor help: some flags are documented one level up
                    for up in range(depth - 1, 0, -1):
                        ok_up, out_up = _help(exe, parts[:up])
                        if ok_up:
                            help_text += "\n" + out_up
                    break
            cache[path_str] = (resolved, help_text)
        resolved, help_text = cache[path_str]
        if len(resolved.split()) > len(best.split()):
            best, best_help = resolved, help_text
    return best, best_help


def check_file(path: Path, label: str, live_version: str, cache: dict[str, tuple[str, str]]) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    header_match = HEADER_VERSION_RE.search(text)
    report = {
        "file": label,
        "has_verified_header": bool(VERIFIED_LINE_RE.search(text)),
        "header_version": header_match.group(1) if header_match else "",
        "commands": 0,
        "checked": 0,
        "skipped_shell": [],
        "unknown_subcommand": [],
        "partial_subcommand": [],
        "unverified_flags": [],
        "version_drift": False,
    }
    for cmd in extract_commands(text):
        report["commands"] += 1
        if has_shell_syntax(cmd):
            report["skipped_shell"].append(cmd)
            continue
        candidates, flags = command_path(cmd)
        if not candidates:
            report["skipped_shell"].append(cmd)
            continue
        best, help_text = resolve(candidates, cache)
        report["checked"] += 1
        if not best:
            report["unknown_subcommand"].append({"command": cmd, "deepest_valid": "(none)"})
            continue
        # The command as written should reach the deepest subcommand path the CLI accepts.
        # If a longer candidate exists that is not explained by an option value, the quoted
        # command is probably wrong even though a shorter prefix resolves.
        longest = next((c for c, _ in candidates if len(c.split()) > 1 or c != "hermes"), None)
        if longest and longest != best:
            longest_is_plausible = next(
                (plausible for c, plausible in candidates if c == longest), True
            )
            if longest_is_plausible:
                report["partial_subcommand"].append({"command": cmd, "deepest_valid": best})
        for flag in flags:
            if flag not in help_text:
                report["unverified_flags"].append({"command": cmd, "flag": flag})
    report["version_drift"] = bool(
        live_version and report["header_version"] and live_version != report["header_version"]
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--chapter", help="limit to one chapter number, e.g. 09")
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    parser.add_argument("--only-unknown", action="store_true", help="print only findings")
    args = parser.parse_args()

    targets = sorted((ROOT / "chapters").glob("*/README.md")) + sorted((ROOT / "exercises").glob("ex*.md"))
    if args.chapter:
        targets = [p for p in targets if p.parent.name.startswith(args.chapter) or p.name.startswith("ex" + args.chapter)]
    if not targets:
        print("no chapter files matched", file=sys.stderr)
        return 2

    live = installed_version()
    if not live:
        print("hermes CLI not found: install Hermes Agent to re-verify chapters", file=sys.stderr)
        return 2

    cache: dict[str, tuple[str, str]] = {}
    reports = [check_file(p, str(p.relative_to(ROOT)), live, cache) for p in targets]

    unknown = [r for r in reports if r["unknown_subcommand"]]
    partial = [r for r in reports if r["partial_subcommand"]]
    flagged = [r for r in reports if r["unverified_flags"]]
    missing_header = [r for r in reports if not r["has_verified_header"] and r["file"].startswith("chapters/")]
    drift_version = [r for r in reports if r["version_drift"]]

    if args.json:
        print(json.dumps({"installed_version": live, "reports": reports}, indent=2))
    else:
        for r in reports:
            findings = r["unknown_subcommand"] or r["unverified_flags"] or r["partial_subcommand"]
            if args.only_unknown and not findings:
                continue
            line = f"{r['file']}: {r['checked']}/{r['commands']} commands checked"
            if r["skipped_shell"]:
                line += f", {len(r['skipped_shell'])} skipped (shell syntax)"
            if r["unknown_subcommand"]:
                line += f", {len(r['unknown_subcommand'])} UNKNOWN subcommand"
            if r["partial_subcommand"]:
                line += f", {len(r['partial_subcommand'])} partial path"
            if r["unverified_flags"]:
                line += f", {len(r['unverified_flags'])} unverified flag"
            print(line)
            for item in r["unknown_subcommand"]:
                print(f"    unknown: {item['command']}  (deepest valid: {item['deepest_valid']})")
            for item in r["partial_subcommand"]:
                print(f"    check:   {item['command']}  (deepest valid: {item['deepest_valid']})")
            for item in r["unverified_flags"]:
                print(f"    flag not in help: {item['flag']}  ({item['command']})")
        print(
            f"\ninstalled Hermes Agent: {live}; {len(reports)} files, "
            f"{sum(r['checked'] for r in reports)} commands verified, "
            f"{sum(len(r['skipped_shell']) for r in reports)} skipped"
        )
        if missing_header:
            print(f"missing Verified header: {', '.join(r['file'] for r in missing_header)}")
        if drift_version:
            print(
                "version drift: chapter headers state a different version than the installed CLI in "
                + ", ".join(r["file"] for r in drift_version[:5])
                + (" ..." if len(drift_version) > 5 else "")
            )
        if partial:
            print(f"\nREVIEW: {sum(len(r['partial_subcommand']) for r in partial)} command(s) resolve only as a shorter path")

    if unknown:
        print(
            f"\nFAILED: {sum(len(r['unknown_subcommand']) for r in unknown)} command(s) no longer resolve",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
