#!/usr/bin/env python3
"""Validate LearningHermes course structure, evidence chains, and branch parity.

Structural checks (always):
  - CURRICULUM.md exists and its chapter table matches the chapter directories
    (both directions: no chapter missing from CURRICULUM, no listed chapter missing).
  - Chapter directories match the NN-slug pattern (2-digit prefix).
  - Each chapter README.md carries the required section headers, in the required order.
  - Each chapter README.md carries a `> **Verified:** YYYY-MM-DD` drift header.
  - Each chapter README.md links its matching exercise file (exercises/exNN-<slug>.md).
  - Each exercise file carries `## Objective`, `## Tasks`, `## Verification checklist`.
  - Exercise slugs match their chapter slugs.
  - Each chapter has a non-empty AGENTS.md.
  - Every `docs/research/...` path cited by a chapter or exercise exists on disk,
    and every cited evidence file is non-empty (no orphan/empty evidence files).
  - No zero-byte file anywhere under docs/research/.
  - Code fences are balanced in every tracked markdown file.

Warnings (non-fatal unless --warnings-as-errors):
  - `examples/...` or `assets/...` paths cited by chapters and exercises that do not
    exist yet (planned course material).

Parity checks (--other PATH, comparing e.g. the farsi checkout against english):
  - Same relative file trees (markdown files).
  - Same code-block count per markdown file (translation may not add/drop code).
"""
from __future__ import annotations

import argparse
import re
import sys
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

CHAPTER_DIR_RE = re.compile(r"^\d{2}-[a-z0-9-]+$")
EXERCISE_RE = re.compile(r"^ex(\d{2})-([a-z0-9-]+)\.md$")
CURRICULUM_CHAPTER_RE = re.compile(r"chapters/(\d{2}-[a-z0-9-]+)/")
VERIFIED_RE = re.compile(r"^> \*\*Verified:\*\* \d{4}-\d{2}-\d{2}\b", re.M)

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
    """Collect path-like references, tolerating line-wrapped code spans."""
    refs: set[str] = set()
    for m in backtick_re.finditer(text):
        inner = re.sub(r"\s+", "", m.group(1))
        for hit in bare_re.findall(inner):
            refs.add(hit.rstrip(".,;:"))
    masked = backtick_re.sub("`x`", text)
    for hit in bare_re.findall(masked):
        refs.add(hit.rstrip(".,;:"))
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


def code_block_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    return sum(1 for line in text.splitlines() if line.strip().startswith("```"))


def validate(root: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    curriculum = root / "CURRICULUM.md"
    if not curriculum.is_file():
        errors.append("CURRICULUM.md missing at repo root")
        listed: set[str] = set()
    else:
        listed = set(CURRICULUM_CHAPTER_RE.findall(curriculum.read_text(encoding="utf-8", errors="replace")))

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
        num, slug = d.name[:2], d.name[3:]
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

        if not VERIFIED_RE.search(text):
            errors.append(f"{rel}/README.md: missing '> **Verified:** YYYY-MM-DD' drift header")

        agents_md = d / "AGENTS.md"
        if not agents_md.is_file():
            errors.append(f"{rel}: missing AGENTS.md")
        elif not agents_md.read_text(encoding="utf-8", errors="replace").strip():
            errors.append(f"{rel}/AGENTS.md: empty")

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

    chapter_nums = {d.name[:2] for d in dirs}
    for n in sorted(set(exercise_by_num) - chapter_nums):
        errors.append(f"exercises/ex{n}-*.md has no matching chapter directory")

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
    args = parser.parse_args()

    errors, warnings = validate(args.root)
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
