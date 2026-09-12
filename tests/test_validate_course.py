"""Black-box, file-based CLI regression tests; standard library only."""
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_course.py"

CHAPTER_README = """# Chapter {num:02d} — Test

> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Evidence: docs/research/jobs/source-01.md

## Concepts

Body.

## Verified commands

```bash
hermes doctor
```

Evidence: docs/research/hermes/cli-evidence-2026-09-07.txt

## Common pitfalls

Body.

## Exercises

See exercises/ex{num:02d}-test.md.
"""

EXERCISE = """# Exercise {num:02d} — Test

## Objective

Do the thing.

## Tasks

1. Run `hermes doctor`.

## Verification checklist

- [ ] `hermes doctor` passes.
"""

CHAPTER_AGENTS = """# Chapter {num:02d} — Authoring

- Verify commands live before quoting them.
"""


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "english"
        self.other = Path(self.temp.name) / "farsi"
        for root in (self.root, self.other):
            self.put(root, "CURRICULUM.md", "# Curriculum\n\n| 01 | `chapters/01-test/` | Test |\n")
            self.put(root, "README.md", "# Course\n")
            self.put(root, "chapters/01-test/README.md", CHAPTER_README.format(num=1))
            self.put(root, "chapters/01-test/AGENTS.md", CHAPTER_AGENTS.format(num=1))
            self.put(root, "exercises/ex01-test.md", EXERCISE.format(num=1))
            self.put(root, "docs/research/jobs/source-01.md", "Posting body.\n")
            self.put(root, "docs/research/hermes/cli-evidence-2026-09-07.txt", "hermes doctor output\n")
        # farsi translation differs in prose only; code fence count must match
        self.put(self.other, "chapters/01-test/README.md",
                 CHAPTER_README.format(num=1).replace("Body.", "متن.").replace("Test", "آزمون"))

    def put(self, root, path, value):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")

    def run_cli(self, other=False, root=None, extra=()):
        args = [sys.executable, str(SCRIPT), "--root", str(root or self.root)]
        if other:
            args += ["--other", str(self.other)]
        args += list(extra)
        return subprocess.run(args, capture_output=True, text=True)

    def reject(self, diagnostic, other=False, root=None, extra=()):
        result = self.run_cli(other=other, root=root, extra=extra)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stderr)

    def rewrite_chapter(self, text):
        self.put(self.root, "chapters/01-test/README.md", text)

    def test_valid_single_root(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validation passed", result.stdout)

    def test_missing_section_rejected(self):
        self.rewrite_chapter(CHAPTER_README.format(num=1).replace("## Common pitfalls\n\nBody.\n\n", ""))
        self.reject("missing section '## Common pitfalls'")

    def test_sections_out_of_order_rejected(self):
        text = CHAPTER_README.format(num=1)
        concepts = "## Concepts\n\nBody.\n\n"
        pitfalls = "## Common pitfalls\n\nBody.\n\n"
        self.rewrite_chapter(text.replace(concepts, "@@").replace(pitfalls, concepts).replace("@@", pitfalls))
        self.reject("required sections are out of order")

    def test_missing_exercise_rejected(self):
        (self.root / "exercises" / "ex01-test.md").unlink()
        self.reject("no matching exercise file")

    def test_exercise_slug_mismatch_rejected(self):
        (self.root / "exercises" / "ex01-test.md").rename(self.root / "exercises" / "ex01-other.md")
        self.reject("slug does not match the chapter slug")

    def test_exercise_missing_checklist_rejected(self):
        self.put(self.root, "exercises/ex01-test.md",
                 EXERCISE.format(num=1).replace("## Verification checklist\n\n- [ ] `hermes doctor` passes.\n", ""))
        self.reject("missing section '## Verification checklist'")

    def test_missing_evidence_reference_rejected(self):
        text = CHAPTER_README.format(num=1)
        text = text.replace("Evidence: docs/research/jobs/source-01.md\n\n", "")
        text = text.replace("Evidence: docs/research/hermes/cli-evidence-2026-09-07.txt\n\n", "")
        self.rewrite_chapter(text)
        self.reject("no docs/research/ evidence reference")

    def test_dangling_evidence_path_rejected(self):
        self.rewrite_chapter(CHAPTER_README.format(num=1).replace(
            "docs/research/jobs/source-01.md", "docs/research/jobs/source-99.md"))
        self.reject("cites evidence path that does not exist: docs/research/jobs/source-99.md")

    def test_empty_evidence_file_rejected(self):
        self.put(self.root, "docs/research/jobs/source-02.md", "")
        self.reject("empty evidence file")

    def test_missing_verified_header_rejected(self):
        self.rewrite_chapter("\n".join(
            line for line in CHAPTER_README.format(num=1).splitlines()
            if not line.startswith("> **Verified:**")).replace("\n\n\n", "\n\n"))
        self.reject("missing '> **Verified:** YYYY-MM-DD' drift header")

    def test_missing_chapter_agents_rejected(self):
        (self.root / "chapters" / "01-test" / "AGENTS.md").unlink()
        self.reject("missing AGENTS.md")

    def test_curriculum_missing_chapter_rejected(self):
        self.put(self.root, "CURRICULUM.md", "# Curriculum\n\nno chapter table here\n")
        self.reject("chapter directory not listed in the chapter tables: 01-test")

    def test_curriculum_ghost_chapter_rejected(self):
        self.put(self.root, "CURRICULUM.md",
                 "# Curriculum\n\n| 01 | `chapters/01-test/` | Test |\n| 02 | `chapters/02-ghost/` | Ghost |\n")
        self.reject("lists chapter table entry that does not exist: chapters/02-ghost/")

    def test_unbalanced_code_fence_rejected(self):
        self.rewrite_chapter(CHAPTER_README.format(num=1) + "\n```bash\nhermes doctor\n")
        self.reject("unbalanced code fences")

    def test_learner_output_paths_allowed(self):
        self.rewrite_chapter(CHAPTER_README.format(num=1).replace(
            "See exercises/ex01-test.md.",
            "Deliverable: `docs/research/capstone/portfolio.md`.\n\nSee exercises/ex01-test.md."))
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_dangling_material_reference_warns_but_passes(self):
        self.rewrite_chapter(CHAPTER_README.format(num=1).replace(
            "See exercises/ex01-test.md.", "Code: `examples/embed-agent.py`.\n\nSee exercises/ex01-test.md."))
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARNINGS", result.stderr)
        self.assertIn("examples/embed-agent.py", result.stderr)

    def test_dangling_material_reference_fails_when_strict(self):
        self.rewrite_chapter(CHAPTER_README.format(num=1).replace(
            "See exercises/ex01-test.md.", "Code: `examples/embed-agent.py`.\n\nSee exercises/ex01-test.md."))
        self.reject("warnings treated as errors", extra=("--warnings-as-errors",))

    def test_parity_passes_prose_only_translation(self):
        result = self.run_cli(other=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("parity", result.stdout)

    def test_parity_rejects_code_fence_drift(self):
        self.put(self.other, "exercises/ex01-test.md",
                 EXERCISE.format(num=1) + "\n```js\nextra()\n```\n")
        self.reject("code-block fences", other=True)

    def test_parity_rejects_missing_file(self):
        (self.other / "exercises" / "ex01-test.md").unlink()
        self.reject("file only in english", other=True)


if __name__ == "__main__":
    unittest.main()
