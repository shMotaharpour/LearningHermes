"""Tests for scripts/verify_chapters.py's command extraction.

The interesting case is the plugin marker: a plugin registers its own `hermes <name>`
subcommand, so such a command genuinely does not resolve on a CLI without that plugin.
Chapter 12 teaches this, so the verifier has to tell that apart from real drift — and the
escape hatch must be narrow enough that it cannot be used to silence a real failure.

No `hermes` needed: extraction is pure text handling.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import verify_chapters as V  # noqa: E402


class ExtractionTests(unittest.TestCase):
    def extract(self, text):
        return V.extract_commands(text)

    def test_plain_command_is_checked(self):
        checked, plugin = self.extract("```bash\nhermes doctor\n```")
        self.assertEqual(checked, ["hermes doctor"])
        self.assertEqual(plugin, [])

    def test_trailing_comment_is_stripped_from_the_command(self):
        checked, _ = self.extract("```bash\nhermes doctor   # health check\n```")
        self.assertEqual(checked, ["hermes doctor"])

    def test_marked_command_is_routed_to_plugin_provided(self):
        checked, plugin = self.extract(
            "```bash\nhermes egress-guard --json   # plugin: egress-guard\n```")
        self.assertEqual(checked, [])
        self.assertEqual(plugin, ["hermes egress-guard --json"])

    def test_one_marker_covers_other_mentions_in_the_same_file(self):
        """Inline spans in a table cannot carry a comment without rendering it."""
        text = (
            "| surface | `hermes egress-guard --json` |\n\n"
            "```bash\nhermes egress-guard --json   # plugin: egress-guard\n```\n"
        )
        checked, plugin = self.extract(text)
        self.assertEqual(checked, [])
        self.assertEqual(len(plugin), 2)

    def test_the_marker_does_not_leak_to_other_files(self):
        """Extraction is per-file, so a marker cannot silence a command elsewhere."""
        checked, plugin = self.extract("```bash\nhermes egress-guard --json\n```")
        self.assertEqual(checked, ["hermes egress-guard --json"])
        self.assertEqual(plugin, [])

    def test_marker_must_name_a_plugin(self):
        """An unnamed escape hatch would become the way to hide real drift."""
        checked, plugin = self.extract("```bash\nhermes nope --x   # plugin:\n```")
        self.assertEqual(checked, ["hermes nope --x"])
        self.assertEqual(plugin, [])

    def test_marker_does_not_cover_an_unrelated_subcommand(self):
        text = "```bash\nhermes egress-guard --json   # plugin: egress-guard\nhermes bogus-cmd\n```"
        checked, plugin = self.extract(text)
        self.assertEqual(checked, ["hermes bogus-cmd"])
        self.assertEqual(plugin, ["hermes egress-guard --json"])

    def test_marker_inside_a_longer_comment_is_not_honoured(self):
        """It must be the end of the line, so prose cannot accidentally disable a check."""
        checked, plugin = self.extract(
            "```bash\nhermes doctor  # plugin: foo is unrelated to this line\n```")
        self.assertEqual(checked, ["hermes doctor"])
        self.assertEqual(plugin, [])

    def test_line_continuations_are_joined(self):
        checked, _ = self.extract("```bash\nhermes cron create \\\n  --name x \"0 6 * * *\"\n```")
        self.assertEqual(len(checked), 1)
        self.assertIn("--name x", checked[0])

    def test_inline_span_is_collected(self):
        checked, _ = self.extract("Run `hermes doctor` first.")
        self.assertEqual(checked, ["hermes doctor"])

    def test_non_hermes_lines_are_ignored(self):
        checked, plugin = self.extract("```bash\ncd examples\npython3 x.py\ngit status\n```")
        self.assertEqual(checked, [])
        self.assertEqual(plugin, [])

    def test_prompt_prefixes_are_stripped(self):
        checked, _ = self.extract("```\n$ hermes status\n```")
        self.assertEqual(checked, ["hermes status"])


class ShellSyntaxTests(unittest.TestCase):
    def test_placeholder_with_angle_brackets_is_shell_syntax(self):
        self.assertTrue(V.has_shell_syntax("hermes <name> ..."))

    def test_pipeline_is_shell_syntax(self):
        self.assertTrue(V.has_shell_syntax("hermes sessions list | head -5"))

    def test_a_quoted_cron_expression_is_not_shell_syntax(self):
        """`0 6 * * *` is data; the globs are inside quotes."""
        self.assertFalse(V.has_shell_syntax('hermes cron create "0 6 * * *" --name x'))

    def test_plain_command_is_not_shell_syntax(self):
        self.assertFalse(V.has_shell_syntax("hermes plugins list"))




class EvidenceStandardAgreementTests(unittest.TestCase):
    """The two validators must have the same idea of which chapters are `Reviewed:`.

    `validate_course.py` enforces the weaker header in both directions; `verify_chapters.py`
    only needs to stop calling such a chapter header-less. Nothing links the two lists at
    runtime, so this test links them — the failure mode otherwise is that one script starts
    complaining about a chapter the other has blessed, and whoever sees it first assumes the
    chapter is broken. Two copies of a rule drift; that is Chapter 03's whole argument.
    """

    def test_the_two_allowlists_match(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        import validate_course as VC

        self.assertEqual(V.REVIEWED_CHAPTERS, VC.REVIEWED_CHAPTERS)

    def test_every_listed_chapter_exists_and_carries_the_header(self):
        chapters = Path(__file__).resolve().parents[1] / "chapters"
        for slug in V.REVIEWED_CHAPTERS:
            readme = chapters / slug / "README.md"
            self.assertTrue(readme.is_file(), f"{slug} is allowlisted but has no README")
            text = readme.read_text(encoding="utf-8")
            self.assertIsNotNone(V.REVIEWED_LINE_RE.search(text), f"{slug} lacks Reviewed:")
            self.assertIsNone(V.VERIFIED_LINE_RE.search(text), f"{slug} also claims Verified:")

    def test_chapter_slug_reads_the_directory_name(self):
        self.assertEqual(V.chapter_slug("chapters/13b-cloud-deployment/README.md"),
                         "13b-cloud-deployment")
        self.assertEqual(V.chapter_slug("exercises/ex13b-cloud-deployment.md"), "")


if __name__ == "__main__":
    unittest.main()
