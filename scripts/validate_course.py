#!/usr/bin/env python3
"""Validate LearningHermes course structure, evidence chains, and branch parity.

Structural checks (always):
  - CURRICULUM.md exists and its chapter table matches the chapter directories
    (both directions: no chapter missing from CURRICULUM, no listed chapter missing).
  - Chapter directories match the NN-slug pattern (2-digit prefix).
  - Each chapter README.md carries the required section headers, in the required order.
  - Each chapter README.md carries a `> **Verified:** YYYY-MM-DD · Hermes Agent vX.Y.Z`
    drift header, and every chapter states the SAME date and version (the course is
    verified as one pass, not chapter by chapter).
  - Except chapters named in REVIEWED_CHAPTERS, whose commands this repo cannot run (no
    cloud account). Those must carry `> **Reviewed:** YYYY-MM-DD · NOT verified against
    <what> · <how it IS checked>` and must NOT carry a Verified header. Every other chapter
    is forbidden from using the Reviewed header, so the weaker standard cannot spread.
  - Each chapter README.md links its matching exercise file (exercises/exNN-<slug>.md).
  - Each exercise file carries `## Objective`, `## Tasks`, `## Verification checklist`.
  - Exercise slugs match their chapter slugs.
  - `chapters/AGENTS.md` (the shared chapter contract) exists and is non-empty.
  - Each chapter has a non-empty AGENTS.md that does NOT restate a line from the shared
    contract. Sixteen copies of the same paragraph are what this check exists to prevent:
    they drift, and then nobody knows which copy is authoritative.
  - Every `docs/research/...` path cited by a chapter or exercise exists on disk,
    and every cited evidence file is non-empty (no orphan/empty evidence files).
  - No zero-byte file anywhere under docs/research/.
  - Code fences are balanced in every tracked markdown file.

Warnings (non-fatal unless --warnings-as-errors):
  - `examples/...` or `assets/...` paths cited by chapters and exercises that do not
    exist yet (planned course material).
  - A `Verified:` header older than --max-age-days (default 180). The commands are
    re-checked by scripts/verify_chapters.py against a real CLI; this warning is the
    reminder that nobody has run it in a while.

Parity checks (--other PATH, comparing e.g. the farsi checkout against english):
  - Same relative file trees (markdown files).
  - Same code-block count per markdown file (translation may not add/drop code).
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

REQUIRED_SECTIONS = [
    "## Why this matters (job link)",
    "## Concepts",
    "## Verified commands",
    "## Common pitfalls",
    "## Exercises",
]

REQUIRED_EXERCISE_SECTIONS = [
    "## Objective",
    "## Tasks",
    "## Verification checklist",
]

# Chapters are NN-slug. A single lowercase letter may follow the digits (03b) for a
# chapter inserted between two existing ones: renumbering every later chapter would rewrite
# every "Chapter NN" cross-reference in the course AND force the same rename on the
# translation branch, whose parity check compares file trees. A suffix costs one character.
CHAPTER_NUM = r"\d{2}[a-z]?"
CHAPTER_DIR_RE = re.compile(rf"^({CHAPTER_NUM})-([a-z0-9-]+)$")
EXERCISE_RE = re.compile(rf"^ex({CHAPTER_NUM})-([a-z0-9-]+)\.md$")
CURRICULUM_CHAPTER_RE = re.compile(rf"chapters/({CHAPTER_NUM}-[a-z0-9-]+)/")
VERIFIED_RE = re.compile(
    r"^> \*\*Verified:\*\* (\d{4}-\d{2}-\d{2}) · Hermes Agent v(\d[\w.]*)", re.M
)

# A chapter whose commands this repo CANNOT run carries a different, weaker header and says
# what it could not verify and how it is checked instead. The course's credibility rests on
# `Verified:` meaning something, so a chapter about a cloud provider we hold no account with
# must not claim it. Membership is explicit: the weaker standard is opt-in BY NAME, so a
# chapter can never quietly downgrade itself, and a listed chapter may not claim to be
# verified either.
REVIEWED_RE = re.compile(
    r"^> \*\*Reviewed:\*\* (\d{4}-\d{2}-\d{2}) · NOT verified against (.+?) · (.+)$", re.M
)
REVIEWED_CHAPTERS = {"13b-cloud-deployment"}
DEFAULT_MAX_AGE_DAYS = 180
# Below this, a matching line is boilerplate ("## Care") rather than a duplicated rule.
MIN_SHARED_RULE_CHARS = 40

# Splits on fenced blocks: re.split with one group yields prose, body, prose, body, ...
FENCE_SPLIT_RE = re.compile(r"^```[^\n]*\n(.*?)^```", re.M | re.S)

BACKTICK_EVIDENCE_RE = re.compile(r"`([^`]*docs/research/[^`]*)`")
BARE_EVIDENCE_RE = re.compile(r"docs/research/[A-Za-z0-9._/\-]+")
BACKTICK_MATERIAL_RE = re.compile(r"`([^`]*(?:examples|assets)/[^`]*)`")
BARE_MATERIAL_RE = re.compile(r"(?:examples|assets)/[A-Za-z0-9._/\-]+")

# Paths the learner creates while doing the course; they are expected to be absent
# from the repo and are therefore exempt from "must exist" evidence checks.
LEARNER_OUTPUT_PREFIXES = ("docs/research/capstone/", "docs/research/labs/")


def chapter_dirs(root: Path) -> list[Path]:
    ch = root / "chapters"
    if not ch.is_dir():
        return []
    return sorted(p for p in ch.iterdir() if p.is_dir() and CHAPTER_DIR_RE.match(p.name))


def exercise_files(root: Path) -> list[Path]:
    ex = root / "exercises"
    if not ex.is_dir():
        return []
    return sorted(ex.glob("ex*.md"))


def _refs(text: str, backtick_re: re.Pattern[str], bare_re: re.Pattern[str]) -> set[str]:
    """Collect path-like references, tolerating line-wrapped inline code spans.

    Fenced blocks are scanned separately and WITHOUT the whitespace-joining, because
    joining is only correct for an inline span wrapped by the formatter. Applied to a
    fenced block it welds consecutive shell lines into one nonexistent path — e.g.
    `cd examples/evals` followed by `python3 eval_runner.py ...` became a reference to
    "examples/evalspython3eval_runner.py...", reported as a missing file.
    """
    refs: set[str] = set()

    def collect(chunk: str, *, join_wrapped: bool) -> None:
        if join_wrapped:
            for m in backtick_re.finditer(chunk):
                # Join across NEWLINES only. Collapsing every space also welds a span with
                # an intentional one — `examples/x/run.py --demo` became a reference to
                # "examples/x/run.py--demo" — so only the line wrap the formatter inserted
                # is undone.
                inner = re.sub(r"\s*\n\s*", "", m.group(1))
                for hit in bare_re.findall(inner):
                    refs.add(hit.rstrip(".,;:"))
            chunk = backtick_re.sub("`x`", chunk)
        for hit in bare_re.findall(chunk):
            refs.add(hit.rstrip(".,;:"))

    # Odd segments are fenced-block bodies, even segments are ordinary prose.
    for index, segment in enumerate(FENCE_SPLIT_RE.split(text)):
        collect(segment, join_wrapped=(index % 2 == 0))
    return refs


def evidence_refs(text: str) -> set[str]:
    return _refs(text, BACKTICK_EVIDENCE_RE, BARE_EVIDENCE_RE)


def material_refs(text: str) -> set[str]:
    return _refs(text, BACKTICK_MATERIAL_RE, BARE_MATERIAL_RE)


def md_files(root: Path) -> set[str]:
    skip_parts = {".git", ".hermes", "__pycache__", "node_modules"}
    out: set[str] = set()
    for p in root.rglob("*.md"):
        if skip_parts & set(p.relative_to(root).parts):
            continue
        out.add(str(p.relative_to(root)))
    return out


def substantive_lines(text: str) -> set[str]:
    """Normalised prose lines worth comparing: long enough to be a rule, not a heading."""
    out = set()
    for raw in text.splitlines():
        line = " ".join(raw.strip().lstrip("-*").split()).rstrip(".").lower()
        if len(line) >= MIN_SHARED_RULE_CHARS and not line.startswith("#"):
            out.add(line)
    return out


def duplicated_from_shared(chapter_text: str, shared: set[str]) -> list[str]:
    """Lines a per-chapter AGENTS.md copied verbatim from the shared contract.

    An exact-line check rather than a word cap: it names the offending line, it cannot be
    satisfied by padding, and it keeps working when the shared contract is reworded.
    """
    return sorted(substantive_lines(chapter_text) & shared)


def code_block_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    return sum(1 for line in text.splitlines() if line.strip().startswith("```"))


def validate(
    root: Path,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    today: date | None = None,
    reviewed_chapters: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    today = today or date.today()
    reviewed_chapters = REVIEWED_CHAPTERS if reviewed_chapters is None else reviewed_chapters
    verified_headers: dict[str, tuple[str, str]] = {}

    curriculum = root / "CURRICULUM.md"
    if not curriculum.is_file():
        errors.append("CURRICULUM.md missing at repo root")
        listed: set[str] = set()
    else:
        listed = set(CURRICULUM_CHAPTER_RE.findall(curriculum.read_text(encoding="utf-8", errors="replace")))

    shared_agents = root / "chapters" / "AGENTS.md"
    shared_agents_lines: set[str] = set()
    if not shared_agents.is_file():
        errors.append("chapters/AGENTS.md missing (the shared chapter contract)")
    else:
        shared_text = shared_agents.read_text(encoding="utf-8", errors="replace")
        if not shared_text.strip():
            errors.append("chapters/AGENTS.md: empty")
        shared_agents_lines = substantive_lines(shared_text)

    dirs = chapter_dirs(root)
    if not dirs:
        errors.append("no chapter directories found under chapters/ (expected NN-slug)")
    actual = {d.name for d in dirs}

    for name in sorted(actual - listed):
        errors.append(f"CURRICULUM.md: chapter directory not listed in the chapter tables: {name}")
    for name in sorted(listed - actual):
        errors.append(f"CURRICULUM.md: lists chapter table entry that does not exist: chapters/{name}/")

    exercises = exercise_files(root)
    exercise_by_num: dict[str, Path] = {}
    for p in exercises:
        m = EXERCISE_RE.match(p.name)
        if not m:
            errors.append(f"exercises/{p.name}: filename must match exNN-slug.md")
            continue
        exercise_by_num[m.group(1)] = p
        text = p.read_text(encoding="utf-8", errors="replace")
        for section in REQUIRED_EXERCISE_SECTIONS:
            if section not in text:
                errors.append(f"exercises/{p.name}: missing section '{section}'")
        if code_block_count(p) % 2:
            errors.append(f"exercises/{p.name}: unbalanced code fences")

    for d in dirs:
        chapter_match = CHAPTER_DIR_RE.match(d.name)
        num, slug = chapter_match.group(1), chapter_match.group(2)
        rel = f"chapters/{d.name}"
        readme = d / "README.md"
        if not readme.is_file():
            errors.append(f"{rel}: missing README.md")
            continue
        text = readme.read_text(encoding="utf-8", errors="replace")

        positions = []
        for section in REQUIRED_SECTIONS:
            if section not in text:
                errors.append(f"{rel}/README.md: missing section '{section}'")
            else:
                positions.append((text.index(section), section))
        if positions != sorted(positions):
            errors.append(f"{rel}/README.md: required sections are out of order")

        is_reviewed_chapter = d.name in reviewed_chapters
        reviewed = REVIEWED_RE.search(text)
        verified = VERIFIED_RE.search(text)

        if is_reviewed_chapter and verified:
            errors.append(
                f"{rel}/README.md: listed in REVIEWED_CHAPTERS but claims a 'Verified:' "
                "header — this repo cannot run its commands"
            )
        elif is_reviewed_chapter and not reviewed:
            errors.append(
                f"{rel}/README.md: missing '> **Reviewed:** YYYY-MM-DD · NOT verified "
                "against <what> · <how it IS checked>' header"
            )
        elif reviewed and not is_reviewed_chapter:
            errors.append(
                f"{rel}/README.md: uses the weaker 'Reviewed:' header without being listed "
                "in REVIEWED_CHAPTERS — add it there deliberately or verify the chapter"
            )

        if is_reviewed_chapter:
            # Age is still tracked: a cloud provider's surface drifts faster than a CLI's.
            if reviewed:
                stamp = reviewed.group(1)
                try:
                    reviewed_on = date.fromisoformat(stamp)
                except ValueError:
                    errors.append(
                        f"{rel}/README.md: Reviewed header date '{stamp}' is not a real date")
                else:
                    if reviewed_on > today:
                        errors.append(
                            f"{rel}/README.md: Reviewed header is dated in the future ({stamp})")
                    elif (today - reviewed_on).days > max_age_days:
                        warnings.append(
                            f"{rel}/README.md: reviewed {(today - reviewed_on).days} days ago "
                            f"({stamp}); re-check it against the provider's current docs")
        elif not verified:
            errors.append(
                f"{rel}/README.md: missing "
                "'> **Verified:** YYYY-MM-DD · Hermes Agent vX.Y.Z' drift header"
            )
        else:
            stamp, version = verified.group(1), verified.group(2)
            verified_headers[f"{rel}/README.md"] = (stamp, version)
            try:
                verified_on = date.fromisoformat(stamp)
            except ValueError:
                errors.append(f"{rel}/README.md: Verified header date '{stamp}' is not a real date")
            else:
                if verified_on > today:
                    errors.append(
                        f"{rel}/README.md: Verified header is dated in the future ({stamp})"
                    )
                else:
                    age = (today - verified_on).days
                    if age > max_age_days:
                        warnings.append(
                            f"{rel}/README.md: verified {age} days ago ({stamp}, "
                            f"Hermes v{version}); re-run scripts/verify_chapters.py "
                            f"against a current CLI"
                        )

        agents_md = d / "AGENTS.md"
        if not agents_md.is_file():
            errors.append(f"{rel}: missing AGENTS.md")
        else:
            agents_text = agents_md.read_text(encoding="utf-8", errors="replace")
            if not agents_text.strip():
                errors.append(f"{rel}/AGENTS.md: empty")
            for line in duplicated_from_shared(agents_text, shared_agents_lines):
                errors.append(
                    f"{rel}/AGENTS.md: restates a line from chapters/AGENTS.md "
                    f"— keep only this chapter's delta: {line!r}"
                )

        ex = exercise_by_num.get(num)
        if ex is None:
            errors.append(f"{rel}: no matching exercise file exercises/ex{num}-*.md")
        else:
            if ex.name != f"ex{num}-{slug}.md":
                errors.append(
                    f"{rel}: exercise {ex.name} slug does not match the chapter slug "
                    f"(expected ex{num}-{slug}.md)"
                )
            if f"exercises/{ex.name}" not in text:
                errors.append(f"{rel}/README.md: does not link its exercise exercises/{ex.name}")

        refs = evidence_refs(text) | evidence_refs(ex.read_text(encoding="utf-8", errors="replace") if ex else "")
        if not refs:
            errors.append(f"{rel}/README.md: no docs/research/ evidence reference")
        for ref in sorted(refs):
            if ref.startswith(LEARNER_OUTPUT_PREFIXES):
                continue
            target = root / ref
            if not target.exists():
                errors.append(f"{rel}: cites evidence path that does not exist: {ref}")
            elif target.is_file() and target.stat().st_size == 0:
                errors.append(f"{rel}: cites empty evidence file: {ref}")

        for ref in sorted(material_refs(text)):
            if not (root / ref).exists():
                warnings.append(f"{rel}: cites not-yet-created material: {ref}")

        if code_block_count(readme) % 2:
            errors.append(f"{rel}/README.md: unbalanced code fences")

    chapter_nums = {CHAPTER_DIR_RE.match(d.name).group(1) for d in dirs}
    for n in sorted(set(exercise_by_num) - chapter_nums):
        errors.append(f"exercises/ex{n}-*.md has no matching chapter directory")

    # The course is verified as one pass: a chapter claiming a different date or a
    # different Hermes version than its siblings means a partial re-verification was
    # left half-done, which is exactly the drift the header exists to make visible.
    if len(set(verified_headers.values())) > 1:
        stamps = sorted({f"{d} / v{v}" for d, v in verified_headers.values()})
        errors.append(
            "chapters disagree on their Verified header — expected one date and one "
            f"Hermes version across the course, found: {', '.join(stamps)}"
        )

    research = root / "docs" / "research"
    if research.is_dir():
        for p in sorted(research.rglob("*")):
            if not p.is_file() or p.name.startswith("."):
                continue
            if p.stat().st_size == 0:
                errors.append(f"empty evidence file under docs/research/: {p.relative_to(root)}")

    return errors, warnings


def _label(path: Path) -> str:
    """Readable name for a checkout: its directory name, or the full path when unnamed."""
    resolved = path.resolve()
    return resolved.name or str(resolved)


def parity(root: Path, other: Path) -> list[str]:
    errors: list[str] = []
    a, b = md_files(root), md_files(other)
    here, there = _label(root), _label(other)
    for f in sorted(a - b):
        errors.append(f"parity: file only in {here}: {f}")
    for f in sorted(b - a):
        errors.append(f"parity: file only in {there}: {f}")
    for f in sorted(a & b):
        ca, cb = code_block_count(root / f), code_block_count(other / f)
        if ca != cb:
            errors.append(f"parity: {f} has {ca} code-block fences in {here} but {cb} in {there}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, required=True, help="course checkout to validate")
    parser.add_argument("--other", type=Path, help="second checkout for parity comparison")
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="treat dangling examples/ and assets/ references as failures",
    )
    parser.add_argument(
        "--reviewed",
        action="append",
        metavar="CHAPTER_DIR",
        help=(
            "chapter directory whose commands this repo cannot run, so it carries the "
            "weaker 'Reviewed:' header (repeatable; overrides the built-in list)"
        ),
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        help=(
            "warn when a chapter's Verified header is older than this "
            f"(default: {DEFAULT_MAX_AGE_DAYS})"
        ),
    )
    args = parser.parse_args()

    errors, warnings = validate(
        args.root,
        max_age_days=args.max_age_days,
        reviewed_chapters=set(args.reviewed) if args.reviewed else None,
    )
    if args.other:
        errors += parity(args.root, args.other)

    if warnings:
        print(f"WARNINGS ({len(warnings)}):", file=sys.stderr)
        print("\n".join(warnings), file=sys.stderr)

    if errors or (args.warnings_as_errors and warnings):
        if errors:
            print("\n".join(errors), file=sys.stderr)
            print(f"\nFAILED: {len(errors)} error(s)", file=sys.stderr)
        else:
            print("\nFAILED: warnings treated as errors", file=sys.stderr)
        return 1

    msg = "Validation passed (structure, evidence chains, contract; semantic translation not guaranteed)."
    if args.other:
        msg = f"Validation passed incl. parity vs {args.other.name}."
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
