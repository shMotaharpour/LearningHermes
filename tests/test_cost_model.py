"""Tests for examples/capstone/cost_model.py — the model Chapter 16 defends a budget with.

The chapter tells a learner to make a decision from this tool's ranking, so the arithmetic
has to be right and the placeholder warning has to be impossible to miss.
"""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

CAPSTONE = Path(__file__).resolve().parents[1] / "examples" / "capstone"
_spec = importlib.util.spec_from_file_location("cost_model", CAPSTONE / "cost_model.py")
cost_model = importlib.util.module_from_spec(_spec)
sys.modules["cost_model"] = cost_model
_spec.loader.exec_module(cost_model)

SPEC = json.loads((CAPSTONE / "workflow.json").read_text(encoding="utf-8"))


class ArithmeticTests(unittest.TestCase):
    def setUp(self):
        self.models = SPEC["models"]

    def job(self, **overrides):
        base = {"name": "t", "tier": "cheap", "runs_per_day": 1, "input_tokens": 1_000_000,
                "output_tokens": 0, "cached_fraction": 0.0, "tool_calls": 0,
                "failure_rate": 0.0}
        base.update(overrides)
        return base

    def test_one_million_uncached_input_tokens_costs_the_input_rate(self):
        result = cost_model.job_cost(self.job(), self.models)
        self.assertAlmostEqual(result["per_run"], self.models["cheap"]["input_per_mtok"], 6)

    def test_output_tokens_are_priced_at_the_output_rate(self):
        result = cost_model.job_cost(
            self.job(input_tokens=0, output_tokens=1_000_000), self.models)
        self.assertAlmostEqual(result["per_run"], self.models["cheap"]["output_per_mtok"], 6)

    def test_caching_reduces_cost_toward_the_cached_rate(self):
        full = cost_model.job_cost(self.job(cached_fraction=0.0), self.models)["per_run"]
        half = cost_model.job_cost(self.job(cached_fraction=0.5), self.models)["per_run"]
        allc = cost_model.job_cost(self.job(cached_fraction=1.0), self.models)["per_run"]
        self.assertLess(half, full)
        self.assertLess(allc, half)
        self.assertAlmostEqual(allc, self.models["cheap"]["cached_input_per_mtok"], 6)

    def test_failure_rate_adds_to_monthly_spend(self):
        """A failure is not free: the tokens were spent before it failed."""
        clean = cost_model.job_cost(self.job(failure_rate=0.0), self.models)["monthly"]
        flaky = cost_model.job_cost(self.job(failure_rate=0.10), self.models)["monthly"]
        self.assertAlmostEqual(flaky, clean * 1.10, places=6)

    def test_monthly_scales_with_frequency(self):
        once = cost_model.job_cost(self.job(runs_per_day=1), self.models)["monthly"]
        twice = cost_model.job_cost(self.job(runs_per_day=2), self.models)["monthly"]
        self.assertAlmostEqual(twice, once * 2, places=6)

    def test_a_script_only_job_costs_nothing(self):
        result = cost_model.job_cost(
            self.job(input_tokens=0, output_tokens=0, runs_per_day=24), self.models)
        self.assertEqual(result["monthly"], 0.0)

    def test_latency_counts_one_turn_per_tool_call_plus_the_answer(self):
        """Every tool call is another round trip through the loop (Chapter 01)."""
        result = cost_model.job_cost(self.job(tool_calls=4), self.models)
        self.assertEqual(result["latency_s"], 5 * self.models["cheap"]["typical_latency_s"])

    def test_a_zero_tool_call_job_still_has_one_turn(self):
        result = cost_model.job_cost(self.job(tool_calls=0), self.models)
        self.assertEqual(result["latency_s"], self.models["cheap"]["typical_latency_s"])

    def test_the_strong_tier_costs_more_than_the_cheap_one(self):
        cheap = cost_model.job_cost(self.job(tier="cheap"), self.models)["per_run"]
        strong = cost_model.job_cost(self.job(tier="strong"), self.models)["per_run"]
        self.assertGreater(strong, cheap)


class SpecTests(unittest.TestCase):
    def test_every_job_names_a_tier_that_exists(self):
        for job in SPEC["jobs"]:
            self.assertIn(job["tier"], SPEC["models"], job["name"])

    def test_every_job_has_the_fields_the_model_reads(self):
        for job in SPEC["jobs"]:
            for field in ("name", "tier", "runs_per_day", "input_tokens", "output_tokens"):
                self.assertIn(field, job, job.get("name"))

    def test_cached_fractions_are_fractions(self):
        for job in SPEC["jobs"]:
            self.assertGreaterEqual(job.get("cached_fraction", 0), 0.0, job["name"])
            self.assertLessEqual(job.get("cached_fraction", 0), 1.0, job["name"])

    def test_prices_are_marked_as_placeholders(self):
        """The chapter's honesty rests on this: no invented price is presented as a quote."""
        for model in SPEC["models"].values():
            self.assertTrue(model["name"].startswith("<"),
                            "a model name without <angle brackets> reads as a real quote")

    def test_the_spec_includes_a_script_only_job(self):
        """The point that not every automation needs a model."""
        self.assertTrue(any(j["input_tokens"] == 0 and j["output_tokens"] == 0
                            for j in SPEC["jobs"]))


class WhatIfTests(unittest.TestCase):
    def test_what_if_changes_only_the_named_job(self):
        changed = cost_model.what_if(SPEC, ["pr-triage:tier=strong"])
        by_name = {j["name"]: j for j in changed["jobs"]}
        self.assertEqual(by_name["pr-triage"]["tier"], "strong")
        self.assertEqual(by_name["daily-briefing"]["tier"], "strong")  # already strong
        self.assertEqual(by_name["nightly-eval"]["tier"], "cheap")    # untouched

    def test_what_if_does_not_mutate_the_original_spec(self):
        before = json.dumps(SPEC, sort_keys=True)
        cost_model.what_if(SPEC, ["pr-triage:tier=strong"])
        self.assertEqual(json.dumps(SPEC, sort_keys=True), before)

    def test_numeric_overrides_keep_their_type(self):
        changed = cost_model.what_if(SPEC, ["pr-triage:runs_per_day=50"])
        job = next(j for j in changed["jobs"] if j["name"] == "pr-triage")
        self.assertIsInstance(job["runs_per_day"], int)
        self.assertEqual(job["runs_per_day"], 50)

    def test_an_unknown_job_name_changes_nothing(self):
        changed = cost_model.what_if(SPEC, ["no-such-job:tier=strong"])
        self.assertEqual(changed["jobs"], SPEC["jobs"])


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(CAPSTONE / "cost_model.py"), *args],
                              capture_output=True, text=True, timeout=60)

    def test_default_run_reports_a_total_and_the_placeholder_warning(self):
        out = self.run_cli()
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("TOTAL", out.stdout)
        self.assertIn("PLACEHOLDERS", out.stdout)

    def test_sensitivity_ranks_the_levers_and_warns(self):
        out = self.run_cli("--sensitivity")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("baseline", out.stdout)
        self.assertIn("prompt caching off", out.stdout)
        self.assertIn("PLACEHOLDERS", out.stdout)

    def test_turning_caching_off_increases_the_total(self):
        """The chapter claims this is the single largest mover; prove the direction."""
        out = self.run_cli("--sensitivity")
        line = next(l for l in out.stdout.splitlines() if "prompt caching off" in l)
        self.assertIn("+", line)

    def test_json_output_parses(self):
        out = self.run_cli("--json")
        rows = json.loads(out.stdout)
        self.assertEqual(len(rows), len(SPEC["jobs"]))
        self.assertIn("monthly", rows[0])


if __name__ == "__main__":
    unittest.main()
