"""Tests for examples/evals/ — the harness Chapter 14 ships.

The course tells a learner to trust this harness's numbers, so the harness needs the
same discipline the course preaches: the checks must fire correctly, the statistics
must be right, and the refusals must actually refuse.

Standard library only, and no `hermes` required: every test runs offline.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1] / "examples" / "evals"
sys.path.insert(0, str(EVALS))

import compare  # noqa: E402
import eval_runner  # noqa: E402
import judge  # noqa: E402


class FixtureTests(unittest.TestCase):
    """The fixture is what makes the expected answers true; pin it."""

    def test_expected_values_match_the_fixture(self):
        self.assertEqual(eval_runner.EXPECTED["expected_file_count"],
                         len(eval_runner.FIXTURE))
        self.assertEqual(eval_runner.EXPECTED["expected_notes_lines"], 3)
        self.assertEqual(eval_runner.EXPECTED["expected_big_lines"], 12)

    def test_big_txt_is_the_largest_txt(self):
        sizes = {n: len(b) for n, b in eval_runner.FIXTURE.items() if n.endswith(".txt")}
        self.assertEqual(max(sizes, key=sizes.get), "big.txt")


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workdir = Path(self.temp.name)
        self.before = eval_runner.build_fixture(self.workdir)

    def check(self, spec, output):
        return eval_runner.apply_check(spec, output, self.workdir, self.before)[0]

    def test_contains(self):
        self.assertTrue(self.check({"kind": "contains", "value": "NOT PRESENT"},
                                   "answer: NOT PRESENT"))
        self.assertFalse(self.check({"kind": "contains", "value": "NOT PRESENT"},
                                    "not present"))

    def test_regex_substitutes_expected_values(self):
        spec = {"kind": "regex", "pattern": r"\b{expected_notes_lines}\b"}
        self.assertTrue(self.check(spec, "It has 3 lines."))
        self.assertFalse(self.check(spec, "It has 9 lines."))

    def test_not_regex_catches_an_invented_phone_number(self):
        spec = {"kind": "not_regex", "pattern": r"\b\d{3}[-. ]\d{3,4}[-. ]\d{4}\b"}
        self.assertTrue(self.check(spec, "NOT PRESENT"))
        self.assertFalse(self.check(spec, "The number is 555-0142-1234."))

    def test_json_array_check(self):
        spec = {"kind": "json_parses", "as": "array"}
        self.assertTrue(self.check(spec, '["a.txt", "b.txt"]'))
        self.assertFalse(self.check(spec, '{"files": []}'))
        self.assertFalse(self.check(spec, "Sure! Here are the files: a.txt"))

    def test_json_check_tolerates_a_code_fence(self):
        # Agents fence JSON even when told not to. The format dimension of rubric.md
        # is where that is penalised; the deterministic check should still see the data.
        self.assertTrue(self.check({"kind": "json_parses", "as": "array"},
                                   '```json\n["a.txt"]\n```'))

    def test_workdir_unchanged_detects_a_write(self):
        spec = {"kind": "workdir_unchanged"}
        self.assertTrue(self.check(spec, "3 lines"))
        (self.workdir / "notes.txt").write_text("tidied\n", encoding="utf-8")
        self.assertFalse(self.check(spec, "3 lines"))

    def test_workdir_unchanged_detects_a_new_file(self):
        (self.workdir / "extra.txt").write_text("x\n", encoding="utf-8")
        self.assertFalse(self.check({"kind": "workdir_unchanged"}, "3 lines"))

    def test_unknown_check_kind_is_an_error_not_a_pass(self):
        with self.assertRaises(ValueError):
            self.check({"kind": "vibes"}, "looks good")


class TaskFileTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((EVALS / "tasks.json").read_text(encoding="utf-8"))

    def test_every_task_has_an_id_prompt_and_at_least_one_check(self):
        for task in self.spec["tasks"]:
            self.assertTrue(task["id"])
            self.assertTrue(task["prompt"])
            self.assertTrue(task["checks"], f"{task['id']} has no checks")

    def test_task_ids_are_unique(self):
        ids = [t["id"] for t in self.spec["tasks"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_check_kind_is_implemented(self):
        implemented = {"contains", "regex", "not_regex", "json_parses", "workdir_unchanged"}
        for task in self.spec["tasks"]:
            for check in task["checks"]:
                self.assertIn(check["kind"], implemented, f"{task['id']}")

    def test_a_correct_answer_passes_its_task(self):
        """The checks must accept a right answer, not merely reject wrong ones."""
        good = {
            "count-files": "4",
            "json-output": '["big.txt", "notes.txt", "small.txt"]',
            "refuses-to-invent": "NOT PRESENT",
            "multi-step": "big.txt: 12",
            "scope-discipline": "3",
        }
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            before = eval_runner.build_fixture(workdir)
            for task in self.spec["tasks"]:
                for check in task["checks"]:
                    passed, why = eval_runner.apply_check(
                        check, good[task["id"]], workdir, before)
                    self.assertTrue(passed, f"{task['id']}: {why}")


class StatisticsTests(unittest.TestCase):
    def test_wilson_is_bounded_and_non_degenerate_at_the_extremes(self):
        # The naive interval collapses to zero width at 0/n and n/n. That collapse is
        # exactly what makes small-N evals look conclusive when they are not.
        lo, hi = compare.wilson(0, 5)
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0.3)
        lo, hi = compare.wilson(5, 5)
        self.assertLess(lo, 0.7)
        self.assertEqual(hi, 1.0)

    def test_wilson_narrows_as_n_grows(self):
        small = compare.wilson(8, 10)
        large = compare.wilson(80, 100)
        self.assertLess(large[1] - large[0], small[1] - small[0])

    def test_wilson_matches_a_known_value(self):
        lo, hi = compare.wilson(6, 10)
        self.assertAlmostEqual(lo, 0.3130, places=3)
        self.assertAlmostEqual(hi, 0.8318, places=3)

    def test_four_of_five_versus_three_of_five_is_not_signal(self):
        self.assertGreater(compare.two_proportion_p(3, 5, 4, 5), 0.05)

    def test_a_large_well_sampled_gap_is_signal(self):
        self.assertLess(compare.two_proportion_p(30, 50, 45, 50), 0.05)

    def test_identical_rates_give_p_of_one(self):
        self.assertAlmostEqual(compare.two_proportion_p(5, 10, 5, 10), 1.0)

    def test_normal_sf_matches_known_quantiles(self):
        self.assertAlmostEqual(compare.normal_sf(0.0), 0.5, places=6)
        self.assertAlmostEqual(compare.normal_sf(1.959963984540054), 0.025, places=6)

    def test_runs_needed_is_large_for_a_small_gap(self):
        self.assertIsNone(compare.runs_needed(0.8, 0.8))
        modest = compare.runs_needed(0.6, 0.8)
        tiny = compare.runs_needed(0.78, 0.80)
        self.assertGreater(modest, 20)
        self.assertGreater(tiny, modest)

    def test_tally_adds_an_overall_row(self):
        payload = {"runs": [
            {"task": "a", "passed": True, "seconds": 1},
            {"task": "a", "passed": False, "seconds": 1},
            {"task": "b", "passed": True, "seconds": 1},
        ]}
        counts = compare.tally(payload)
        self.assertEqual(counts["a"], (1, 2))
        self.assertEqual(counts["OVERALL"], (2, 3))


class JudgeParsingTests(unittest.TestCase):
    def test_scores_parse(self):
        reply = "grounding: 4\ncompleteness: 5\nformat: 2\nrestraint: 5\nbecause: prose"
        self.assertEqual(judge.parse_scores(reply),
                         {"grounding": 4, "completeness": 5, "format": 2, "restraint": 5})

    def test_out_of_range_scores_are_not_accepted(self):
        self.assertEqual(judge.parse_scores("grounding: 9"), {})

    def test_unparseable_reply_yields_no_scores_rather_than_a_default(self):
        # A judge reply that silently became 3/5 would be indistinguishable from a
        # real middling score. Empty is the honest result.
        self.assertEqual(judge.parse_scores("I think it was pretty good overall!"), {})

    def test_winner_defaults_to_tie_when_absent(self):
        self.assertEqual(judge.parse_winner("winner: A\nbecause: x"), "A")
        self.assertEqual(judge.parse_winner("It's hard to say"), "TIE")

    def test_rubric_covers_every_dimension_the_calibration_set_labels(self):
        rubric = (EVALS / "rubric.md").read_text(encoding="utf-8")
        cases = json.loads((EVALS / "calibration.json").read_text(encoding="utf-8"))["cases"]
        for case in cases:
            for dimension in case["human"]:
                self.assertIn(f"## {dimension}", rubric)

    def test_calibration_labels_are_in_range(self):
        cases = json.loads((EVALS / "calibration.json").read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len(cases), 4)
        for case in cases:
            for dimension, score in case["human"].items():
                self.assertIn(score, range(1, 6), f"{case['id']}.{dimension}")


class RefusalTests(unittest.TestCase):
    """The harness refuses three things. Each refusal is load-bearing."""

    def run_script(self, script, *args):
        return subprocess.run([sys.executable, str(EVALS / script), *args],
                              capture_output=True, text=True)

    def write(self, path, payload):
        Path(path).write_text(json.dumps(payload), encoding="utf-8")

    def test_judge_refuses_to_grade_a_model_with_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp) / "r.json"
            self.write(results, {"model": "some-model", "dry_run": False, "runs": []})
            out = self.run_script("judge.py", "--results", str(results),
                                  "--judge-model", "some-model")
            self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
            self.assertIn("self-preference", out.stderr)

    def test_judge_refuses_dry_run_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp) / "r.json"
            self.write(results, {"model": "a", "dry_run": True, "runs": []})
            out = self.run_script("judge.py", "--results", str(results),
                                  "--judge-model", "b")
            self.assertEqual(out.returncode, 2, out.stdout + out.stderr)

    def test_compare_refuses_dry_run_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.json", Path(tmp) / "b.json"
            self.write(a, {"model": "a", "dry_run": True, "runs": []})
            self.write(b, {"model": "b", "dry_run": False, "runs": []})
            out = self.run_script("compare.py", str(a), str(b))
            self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
            self.assertIn("dry-run", out.stderr)

    def test_compare_flags_a_real_regression_with_a_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.json", Path(tmp) / "b.json"
            self.write(a, {"model": "a", "dry_run": False, "runs": [
                {"task": "t", "passed": True, "seconds": 1} for _ in range(40)]})
            self.write(b, {"model": "b", "dry_run": False, "runs": [
                {"task": "t", "passed": i < 20, "seconds": 1} for i in range(40)]})
            out = self.run_script("compare.py", str(a), str(b))
            self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
            self.assertIn("REGRESSION", out.stdout)

    def test_compare_does_not_cry_regression_over_small_n_noise(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.json", Path(tmp) / "b.json"
            self.write(a, {"model": "a", "dry_run": False, "runs": [
                {"task": "t", "passed": i < 4, "seconds": 1} for i in range(5)]})
            self.write(b, {"model": "b", "dry_run": False, "runs": [
                {"task": "t", "passed": i < 3, "seconds": 1} for i in range(5)]})
            out = self.run_script("compare.py", str(a), str(b))
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            self.assertIn("no distinguishable difference", out.stdout)

    def test_runner_dry_run_needs_no_hermes_and_writes_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "dry.json"
            out = self.run_script("eval_runner.py", "--out", str(out_path),
                                  "--dry-run", "--repeats", "1")
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["dry_run"])
            self.assertEqual(len(payload["runs"]), 5)


if __name__ == "__main__":
    unittest.main()
