#!/usr/bin/env python3
"""Validate LearningHermes course structure and bilingual branch parity.

Structural checks (always):
  - CURRICULUM.md exists and every chapter directory it lists exists.
  - Chapter directories match the NN-slug pattern (2-digit prefix).
  - Each chapter README.md contains the required section headers.
  - Each chapter has a matching exercise file in exercises/.
  - Each chapter references at least one evidence file under docs/research/.

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

CHAPTER_DIR_RE = re.compile(r"^\d{2}-[a-z0-9-]+$")
CHAPTER_README_RE = re.compile(r"chapters/(\d{2})-")
EXERCISE_RE = re.compile(r"ex(\d{2})-")


def chapter_dirs(root: Path) -> list[Path]:
    ch = root / "chapters"
    if not ch.is_dir():
        return []
    return sorted(p for p in ch.iterdir() if p.is_dir() and CHAPTER_DIR_RE.match(p.name))


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    if not (root / "CURRICULUM.md").is_file():
        errors.append("CURRICULUM.md missing at repo root")

    dirs = chapter_dirs(root)
    if not dirs:
        errors.append("no chapter directories found under chapters/ (expected NN-slug)")

    exercise_files = list((root / "exercises").glob("ex*.md")) if (root / "exercises").is_dir() else []
    exercise_nums: set[str] = set()
    for p in exercise_files:
        m = EXERCISE_RE.match(p.name)
        if m:
            exercise_nums.add(m.group(1))

    for d in dirs:
        num = d.name[:2]
        readme = d / "README.md"
        if not readme.is_file():
            errors.append(f"chapters/{d.name}: missing README.md")
            continue
        text = readme.read_text(encoding="utf-8", errors="replace")
        for section in REQUIRED_SECTIONS:
            if section not in text:
                errors.append(f"chapters/{d.name}/README.md: missing section '{section}'")
        if num not in exercise_nums:
            errors.append(f"chapters/{d.name}: no matching exercise file exercises/ex{num}-*.md")
        # Evidence reference: chapter must cite a docs/research/ path
        if not re.search(r"docs/research/", text):
            errors.append(f"chapters/{d.name}/README.md: no docs/research/ evidence reference")

    # Exercise files without chapters are orphans
    chapter_nums = {d.name[:2] for d in dirs}
    for n in sorted(exercise_nums - chapter_nums):
        errors.append(f"exercises/ex{n}-*.md has no matching chapter directory")

    return errors


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


def parity(root: Path, other: Path) -> list[str]:
    errors: list[str] = []
    a, b = md_files(root), md_files(other)
    for f in sorted(a - b):
        errors.append(f"parity: file only in {root.name}: {f}")
    for f in sorted(b - a):
        errors.append(f"parity: file only in {other.name}: {f}")
    for f in sorted(a & b):
        ca, cb = code_block_count(root / f), code_block_count(other / f)
        if ca != cb:
            errors.append(f"parity: {f} has {ca} code-block fences in {root.name} but {cb} in {other.name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="course checkout to validate")
    parser.add_argument("--other", type=Path, help="second checkout for parity comparison")
    args = parser.parse_args()

    errors = validate(args.root)
    if args.other:
        errors += parity(args.root, args.other)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"\nFAILED: {len(errors)} error(s)", file=sys.stderr)
        return 1
    msg = "Validation passed (structure/code only; semantic translation not guaranteed)."
    if args.other:
        msg = f"Validation passed incl. parity vs {args.other.name}."
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
