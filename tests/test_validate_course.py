"""Black-box, file-based CLI regression tests; standard library only."""
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_course.py"

CHAPTER_README = """# Chapter {num:02d} — Test

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


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "english"
        self.other = Path(self.temp.name) / "farsi"
        for root in (self.root, self.other):
            self.put(root, "CURRICULUM.md", "# Curriculum\n- chapters/01-test/\n")
            self.put(root, "README.md", "# Course\n")
            self.put(root, "chapters/01-test/README.md", CHAPTER_README.format(num=1))
            self.put(root, "exercises/ex01-test.md", EXERCISE.format(num=1))
        # farsi translation differs in prose only; code fence count must match
        self.put(self.other, "chapters/01-test/README.md",
                 CHAPTER_README.format(num=1).replace("Body.", "متن.").replace("Test", "آزمون"))

    def put(self, root, path, value):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")

    def run_cli(self, other=False, root=None):
        args = [sys.executable, str(SCRIPT), "--root", str(root or self.root)]
        if other:
            args += ["--other", str(self.other)]
        return subprocess.run(args, capture_output=True, text=True)

    def reject(self, diagnostic, other=False, root=None):
        result = self.run_cli(other=other, root=root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stderr)

    def test_valid_single_root(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validation passed", result.stdout)

    def test_missing_section_rejected(self):
        self.put(self.root, "chapters/01-test/README.md", CHAPTER_README.format(num=1)
                 .replace("## Common pitfalls\n\nBody.\n\n", ""))
        self.reject("missing section '## Common pitfalls'")

    def test_missing_exercise_rejected(self):
        (self.root / "exercises" / "ex01-test.md").unlink()
        self.reject("no matching exercise file")

    def test_missing_evidence_reference_rejected(self):
        text = CHAPTER_README.format(num=1)
        text = text.replace("Evidence: docs/research/jobs/source-01.md\n\n", "")
        text = text.replace("Evidence: docs/research/hermes/cli-evidence-2026-09-07.txt\n\n", "")
        self.put(self.root, "chapters/01-test/README.md", text)
        self.reject("no docs/research/ evidence reference")

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
