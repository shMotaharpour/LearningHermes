"""Black-box, file-based CLI regression tests; standard library only."""
import subprocess
import sys
from datetime import date, timedelta
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

CHAPTER_AGENTS = """# Chapter {num:02d} — authoring delta

Shared rules: `chapters/AGENTS.md`.

## Scope boundary

This chapter covers the test fixture and nothing adjacent to it.
"""

SHARED_AGENTS = """# AGENTS.md — `chapters/` (shared chapter contract)

- Verify every Hermes command live before writing it here, and cite the evidence file.
- Keep the five required top-level sections in the required order.
"""


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "english"
        self.other = Path(self.temp.name) / "farsi"
        for root in (self.root, self.other):
            self.put(root, "CURRICULUM.md", "# Curriculum\n\n| 01 | `chapters/01-test/` | Test |\n")
            self.put(root, "chapters/AGENTS.md", SHARED_AGENTS)
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
        self.reject("missing '> **Verified:** YYYY-MM-DD · Hermes Agent vX.Y.Z' drift header")

    def test_verified_header_without_version_rejected(self):
        self.rewrite_chapter(
            CHAPTER_README.format(num=1).replace(
                "> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck:",
                "> **Verified:** 2026-09-12 · recheck:",
            )
        )
        self.reject("missing '> **Verified:** YYYY-MM-DD · Hermes Agent vX.Y.Z' drift header")

    def date_the_chapter(self, days_ago):
        """Re-stamp the fixture chapter's Verified header relative to today."""
        stamp = (date.today() - timedelta(days=days_ago)).isoformat()
        self.rewrite_chapter(CHAPTER_README.format(num=1).replace("2026-09-12", stamp))

    def test_stale_verified_header_warns_but_passes(self):
        self.date_the_chapter(400)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("re-run scripts/verify_chapters.py", result.stderr)
        self.assertIn("verified 400 days ago", result.stderr)

    def test_stale_verified_header_fails_under_warnings_as_errors(self):
        self.date_the_chapter(400)
        self.reject("re-run scripts/verify_chapters.py", extra=["--warnings-as-errors"])

    def test_max_age_days_is_the_threshold(self):
        self.date_the_chapter(10)
        fresh = self.run_cli(extra=["--max-age-days", "10"])
        self.assertEqual(fresh.returncode, 0, fresh.stderr)
        self.assertNotIn("re-run scripts/verify_chapters.py", fresh.stderr)
        stale = self.run_cli(extra=["--max-age-days", "9"])
        self.assertEqual(stale.returncode, 0, stale.stderr)
        self.assertIn("re-run scripts/verify_chapters.py", stale.stderr)

    def test_fresh_verified_header_does_not_warn(self):
        self.date_the_chapter(0)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("re-run scripts/verify_chapters.py", result.stderr)

    def test_future_verified_header_rejected(self):
        self.rewrite_chapter(
            CHAPTER_README.format(num=1).replace("2026-09-12", "2999-01-01")
        )
        self.reject("Verified header is dated in the future")

    def test_unparseable_verified_date_rejected(self):
        self.rewrite_chapter(
            CHAPTER_README.format(num=1).replace("2026-09-12", "2026-13-45")
        )
        self.reject("is not a real date")

    def test_chapters_disagreeing_on_verified_header_rejected(self):
        self.put(self.root, "CURRICULUM.md",
                 "# Curriculum\n\n| 01 | `chapters/01-test/` | Test |\n"
                 "| 02 | `chapters/02-other/` | Other |\n")
        second = CHAPTER_README.format(num=2).replace(
            "Hermes Agent v0.20.6 (2026.8.27)", "Hermes Agent v0.21.2 (2026.9.11)"
        ).replace("exercises/ex02-test.md", "exercises/ex02-other.md")
        self.put(self.root, "chapters/02-other/README.md", second)
        self.put(self.root, "chapters/02-other/AGENTS.md", CHAPTER_AGENTS.format(num=2))
        self.put(self.root, "exercises/ex02-other.md", EXERCISE.format(num=2))
        self.reject("chapters disagree on their Verified header")

    def test_fenced_block_lines_are_not_welded_into_one_path(self):
        """Regression: consecutive shell lines in a fence became one bogus reference."""
        self.put(self.root, "examples/evals/eval_runner.py", "print('hi')\n")
        text = CHAPTER_README.format(num=1).replace(
            "```bash\nhermes doctor\n```",
            "```bash\ncd examples/evals\npython3 eval_runner.py --out /dev/null\n```",
        )
        self.rewrite_chapter(text)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("evalspython3", result.stderr)

    def test_line_wrapped_inline_span_is_still_joined(self):
        """The joining behaviour the fence fix must not break."""
        text = CHAPTER_README.format(num=1).replace(
            "Evidence: docs/research/jobs/source-01.md",
            "Evidence: `docs/research/jobs/\nsource-01.md`",
        )
        self.rewrite_chapter(text)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_inline_span_with_an_intentional_space_is_not_welded(self):
        """A span like `examples/x/run.py --demo` is a path plus a flag, not one path."""
        self.put(self.root, "examples/agent-loop/miniagent.py", "print('hi')\n")
        text = CHAPTER_README.format(num=1).replace(
            "Body.", "Run `examples/agent-loop/miniagent.py --demo` first.", 1)
        self.rewrite_chapter(text)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("miniagent.py--demo", result.stderr)

    def test_dangling_reference_inside_a_fence_is_still_caught(self):
        text = CHAPTER_README.format(num=1).replace(
            "```bash\nhermes doctor\n```",
            "```bash\ncat docs/research/hermes/nope.txt\n```",
        )
        self.rewrite_chapter(text)
        self.reject("docs/research/hermes/nope.txt")

    def test_letter_suffixed_chapter_is_accepted(self):
        """03b: a chapter inserted between two others, without renumbering the course."""
        self.put(self.root, "CURRICULUM.md",
                 "# Curriculum\n\n| 01 | `chapters/01-test/` | Test |\n"
                 "| 01b | `chapters/01b-inserted/` | Inserted |\n")
        text = CHAPTER_README.format(num=1).replace(
            "exercises/ex01-test.md", "exercises/ex01b-inserted.md")
        self.put(self.root, "chapters/01b-inserted/README.md", text)
        self.put(self.root, "chapters/01b-inserted/AGENTS.md", CHAPTER_AGENTS.format(num=1))
        self.put(self.root, "exercises/ex01b-inserted.md", EXERCISE.format(num=1))
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_letter_suffixed_chapter_still_needs_a_matching_exercise(self):
        """The suffix widens the pattern; it does not loosen the pairing rule."""
        self.put(self.root, "CURRICULUM.md",
                 "# Curriculum\n\n| 01 | `chapters/01-test/` | Test |\n"
                 "| 01b | `chapters/01b-inserted/` | Inserted |\n")
        text = CHAPTER_README.format(num=1).replace(
            "exercises/ex01-test.md", "exercises/ex01b-inserted.md")
        self.put(self.root, "chapters/01b-inserted/README.md", text)
        self.put(self.root, "chapters/01b-inserted/AGENTS.md", CHAPTER_AGENTS.format(num=1))
        self.reject("no matching exercise file exercises/ex01b-*.md")

    def test_letter_suffixed_exercise_slug_must_match_its_chapter(self):
        self.put(self.root, "CURRICULUM.md",
                 "# Curriculum\n\n| 01 | `chapters/01-test/` | Test |\n"
                 "| 01b | `chapters/01b-inserted/` | Inserted |\n")
        text = CHAPTER_README.format(num=1).replace(
            "exercises/ex01-test.md", "exercises/ex01b-other.md")
        self.put(self.root, "chapters/01b-inserted/README.md", text)
        self.put(self.root, "chapters/01b-inserted/AGENTS.md", CHAPTER_AGENTS.format(num=1))
        self.put(self.root, "exercises/ex01b-other.md", EXERCISE.format(num=1))
        self.reject("slug does not match the chapter slug")

    def test_a_multi_letter_suffix_is_not_a_chapter(self):
        """One letter only: 01bc is a typo, not a numbering scheme."""
        self.put(self.root, "chapters/01bc-nope/README.md", CHAPTER_README.format(num=1))
        result = self.run_cli()
        # Not recognised as a chapter directory, so it is ignored rather than validated.
        self.assertEqual(result.returncode, 0, result.stderr)

    def reviewed_fixture(self):
        """A chapter whose commands this repo cannot run, named in the allowlist."""
        self.put(self.root, "CURRICULUM.md",
                 "# Curriculum\n\n| 01 | `chapters/01-test/` | Test |\n"
                 "| 99b | `chapters/99b-cloud/` | Cloud |\n")
        text = CHAPTER_README.format(num=1).replace(
            "> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck: "
            "`python3 scripts/verify_chapters.py`",
            "> **Reviewed:** 2026-09-14 · NOT verified against a live cloud project · "
            "checked by structural tests",
        ).replace("exercises/ex01-test.md", "exercises/ex99b-cloud.md")
        self.put(self.root, "chapters/99b-cloud/README.md", text)
        self.put(self.root, "chapters/99b-cloud/AGENTS.md", CHAPTER_AGENTS.format(num=9))
        self.put(self.root, "exercises/ex99b-cloud.md", EXERCISE.format(num=9))

    def test_allowlisted_chapter_may_use_the_reviewed_header(self):
        self.reviewed_fixture()
        result = self.run_cli(extra=["--reviewed", "99b-cloud"])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_allowlisted_chapter_may_not_claim_verified(self):
        """The weaker standard cannot be used to smuggle in a stronger claim."""
        self.reviewed_fixture()
        self.put(self.root, "chapters/99b-cloud/README.md",
                 CHAPTER_README.format(num=1).replace(
                     "exercises/ex01-test.md", "exercises/ex99b-cloud.md"))
        self.reject("claims a 'Verified:' header", extra=["--reviewed", "99b-cloud"])

    def test_a_chapter_not_on_the_allowlist_may_not_use_the_reviewed_header(self):
        """The weaker standard is opt-in by name, so it cannot spread quietly."""
        self.reviewed_fixture()
        self.reject("without being listed in REVIEWED_CHAPTERS")

    def test_an_allowlisted_chapter_must_actually_carry_the_header(self):
        """Being on the list is not an exemption from saying what was not verified."""
        self.reviewed_fixture()
        self.put(self.root, "chapters/99b-cloud/README.md",
                 CHAPTER_README.format(num=1)
                 .replace("> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · "
                          "recheck: `python3 scripts/verify_chapters.py`", "")
                 .replace("exercises/ex01-test.md", "exercises/ex99b-cloud.md"))
        self.reject("missing '> **Reviewed:**", extra=["--reviewed", "99b-cloud"])

    def test_a_stale_reviewed_header_warns(self):
        """Cloud surfaces drift faster than a CLI's, so age is still tracked."""
        self.reviewed_fixture()
        old_stamp = (date.today() - timedelta(days=400)).isoformat()
        path = self.root / "chapters" / "99b-cloud" / "README.md"
        path.write_text(path.read_text().replace("2026-09-14", old_stamp), encoding="utf-8")
        result = self.run_cli(extra=["--reviewed", "99b-cloud"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("provider's current docs", result.stderr)

    def test_missing_shared_chapter_contract_rejected(self):
        (self.root / "chapters" / "AGENTS.md").unlink()
        self.reject("chapters/AGENTS.md missing")

    def test_empty_shared_chapter_contract_rejected(self):
        self.put(self.root, "chapters/AGENTS.md", "   \n")
        self.reject("chapters/AGENTS.md: empty")

    def test_chapter_agents_restating_a_shared_rule_rejected(self):
        """The check that stops 18 copies drifting apart — the point of the split."""
        self.put(self.root, "chapters/01-test/AGENTS.md",
                 CHAPTER_AGENTS.format(num=1)
                 + "\n- Verify every Hermes command live before writing it here, and cite"
                   " the evidence file.\n")
        self.reject("restates a line from chapters/AGENTS.md")

    def test_the_duplication_check_names_the_offending_line(self):
        self.put(self.root, "chapters/01-test/AGENTS.md",
                 CHAPTER_AGENTS.format(num=1)
                 + "\n- Keep the five required top-level sections in the required order.\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("five required top-level sections", result.stderr)

    def test_short_shared_lines_are_not_treated_as_duplication(self):
        """A heading or a stock phrase is boilerplate, not a copied rule."""
        self.put(self.root, "chapters/AGENTS.md", SHARED_AGENTS + "\n## Care\n")
        self.put(self.root, "chapters/01-test/AGENTS.md",
                 CHAPTER_AGENTS.format(num=1) + "\n## Care\n\nNothing special.\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_reworded_rule_is_allowed(self):
        """The check targets copies, not the topic — a real delta may discuss the same area."""
        self.put(self.root, "chapters/01-test/AGENTS.md",
                 CHAPTER_AGENTS.format(num=1)
                 + "\n- Evidence for this chapter is the b3 batch; re-capture it on a"
                   " version bump.\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)

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
