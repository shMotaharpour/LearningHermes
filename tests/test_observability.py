"""Tests for examples/observability/analyze_runs.py — Chapter 14b's operational view.

The two tests that matter most are the ones about NOT alarming: a silence check that cries
wolf gets muted, and a muted check is worse than no check because it still looks like
coverage. Both bugs they pin were real and were found by running the tool.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

OBS = Path(__file__).resolve().parents[1] / "examples" / "observability"
_spec = importlib.util.spec_from_file_location("analyze_runs", OBS / "analyze_runs.py")
ar = importlib.util.module_from_spec(_spec)
sys.modules["analyze_runs"] = ar
_spec.loader.exec_module(ar)

START = datetime(2026, 7, 14, tzinfo=timezone.utc)


def run(job, offset_hours, status="ok", seconds=10.0, tool_calls=1, tokens=100, error=""):
    return {"ts": (START + timedelta(hours=offset_hours)).isoformat(), "job": job,
            "status": status, "seconds": seconds, "tool_calls": tool_calls,
            "tokens": tokens, "error": error,
            "dt": START + timedelta(hours=offset_hours)}


class PercentileTests(unittest.TestCase):
    def test_known_values(self):
        data = list(range(1, 101))
        self.assertEqual(ar.percentile(data, 50), 50)
        self.assertEqual(ar.percentile(data, 95), 95)
        self.assertEqual(ar.percentile(data, 100), 100)

    def test_single_value_and_empty(self):
        self.assertEqual(ar.percentile([7.0], 95), 7.0)
        self.assertEqual(ar.percentile([], 95), 0.0)

    def test_p95_exposes_a_tail_the_mean_hides(self):
        """The whole argument for reporting p95.

        Note the 10%: a tail occupying exactly 5% of runs sits ABOVE the 95th percentile by
        definition, so p95 would not see it. Which percentile catches your tail depends on
        how big the tail is — "report p95" is a default, not a law, and a 2% catastrophic
        tail needs p99.
        """
        data = [10.0] * 90 + [500.0] * 10
        mean = sum(data) / len(data)
        self.assertLess(mean, 100)          # the mean looks survivable
        self.assertEqual(ar.percentile(data, 95), 500.0)   # p95 does not

    def test_a_tail_smaller_than_the_percentile_is_invisible_to_it(self):
        """Why "report p95" is a starting point rather than an answer."""
        data = [10.0] * 96 + [500.0] * 4
        self.assertEqual(ar.percentile(data, 95), 10.0)
        self.assertEqual(ar.percentile(data, 99), 500.0)


class PerJobTests(unittest.TestCase):
    def test_failure_rate_and_counts(self):
        rows = [run("a", 0), run("a", 1, status="failed", error="429"), run("a", 2)]
        stats = ar.per_job(rows)["a"]
        self.assertEqual(stats["runs"], 3)
        self.assertEqual(stats["failures"], 1)
        self.assertAlmostEqual(stats["failure_rate"], 1 / 3)
        self.assertEqual(stats["top_error"], "429")

    def test_durations_come_from_successful_runs_only(self):
        """A failure that died in 2s would otherwise flatter the latency numbers."""
        rows = [run("a", 0, seconds=100.0), run("a", 1, status="failed", seconds=2.0)]
        stats = ar.per_job(rows)["a"]
        self.assertEqual(stats["p50"], 100.0)
        self.assertEqual(stats["mean"], 100.0)

    def test_steps_are_per_successful_run(self):
        rows = [run("a", 0, tool_calls=4), run("a", 1, tool_calls=2),
                run("a", 2, status="failed", tool_calls=99)]
        self.assertAlmostEqual(ar.per_job(rows)["a"]["steps"], 3.0)

    def test_tokens_include_failed_runs(self):
        """A failure is not free: the tokens were spent before it failed."""
        rows = [run("a", 0, tokens=100), run("a", 1, status="failed", tokens=50)]
        self.assertEqual(ar.per_job(rows)["a"]["tokens"], 150)


class CadenceTests(unittest.TestCase):
    def test_returns_typical_and_longest_normal(self):
        rows = [run("a", h) for h in range(0, 100, 4)]
        typical, longest = ar.cadence(rows)
        self.assertEqual(typical, timedelta(hours=4))
        self.assertGreaterEqual(longest, typical)

    def test_too_few_runs_yields_nothing(self):
        self.assertIsNone(ar.cadence([run("a", 0), run("a", 1)]))


class SilenceTests(unittest.TestCase):
    """Both bugs pinned here were found by running the tool, not by reading it."""

    def test_a_dead_daily_job_is_caught(self):
        rows = [run("daily", h) for h in range(0, 24 * 10, 24)]
        rows += [run("other", h) for h in range(0, 24 * 15, 6)]  # keeps "now" advancing
        found = {f["job"] for f in ar.silent(rows)}
        self.assertIn("daily", found)

    def test_a_business_hours_job_is_not_flagged_overnight(self):
        """The false positive that would have got this check muted.

        A job that runs every 30 minutes from 09:00-17:00 has a median gap of half an hour
        and a normal overnight gap of sixteen. Judged against the median it is 'silent'
        every single night.
        """
        rows = []
        for day in range(14):
            for half_hour in range(0, 16):  # 09:00 -> 17:00
                rows.append(run("triage", day * 24 + 9 + half_hour * 0.5))
        # "Now" is the last run; a few hours of evening quiet is normal for this job.
        rows.append(run("triage", 13 * 24 + 20))
        self.assertEqual([f["job"] for f in ar.silent(rows)], [])

    def test_a_business_hours_job_IS_flagged_when_truly_dead(self):
        """The check must still work on the job it was nearly disabled for."""
        rows = []
        for day in range(14):
            for half_hour in range(0, 16):
                rows.append(run("triage", day * 24 + 9 + half_hour * 0.5))
        rows.append(run("heartbeat", 20 * 24))  # four days later, nothing from triage
        self.assertIn("triage", {f["job"] for f in ar.silent(rows)})

    def test_factor_tunes_the_tolerance(self):
        rows = [run("daily", h) for h in range(0, 24 * 8, 24)]
        rows.append(run("other", 24 * 10))
        self.assertTrue(ar.silent(rows, factor=1.5))
        self.assertFalse(ar.silent(rows, factor=100.0))

    def test_a_healthy_fleet_reports_nothing(self):
        rows = [run("a", h) for h in range(0, 48)] + [run("b", h) for h in range(0, 48)]
        self.assertEqual(ar.silent(rows), [])


class WeeklyTests(unittest.TestCase):
    def test_incomplete_buckets_are_flagged_partial(self):
        """Comparing a partial week to a full one manufactures a collapse that isn't there."""
        rows = [run("a", h) for h in range(0, 24 * 10, 6)]
        weeks = ar.weekly(rows)["a"]
        self.assertTrue(weeks[0]["partial"])
        self.assertTrue(weeks[-1]["partial"])

    def test_a_fully_covered_week_is_not_partial(self):
        rows = [run("a", h) for h in range(0, 24 * 28, 6)]
        weeks = ar.weekly(rows)["a"]
        self.assertTrue(any(not w["partial"] for w in weeks))

    def test_tokens_and_failure_rate_are_bucketed(self):
        rows = [run("a", h, tokens=10) for h in range(0, 24 * 21, 12)]
        for week in ar.weekly(rows)["a"]:
            self.assertGreater(week["tokens"], 0)
            self.assertEqual(week["failure_rate"], 0.0)

    def test_empty_input(self):
        self.assertEqual(ar.weekly([]), {})


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.rows = ar.load(OBS / "runs.jsonl")

    def test_the_shipped_dataset_loads_and_is_ordered(self):
        self.assertGreater(len(self.rows), 500)
        self.assertEqual(self.rows, sorted(self.rows, key=lambda r: r["dt"]))

    def test_it_contains_the_silent_failure_the_chapter_describes(self):
        findings = {f["job"] for f in ar.silent(self.rows)}
        self.assertEqual(findings, {"daily-briefing"})

    def test_it_contains_a_job_nobody_looks_at(self):
        stats = ar.per_job(self.rows)
        self.assertGreater(stats["inbox-sync"]["failure_rate"], 0.2)

    def test_it_contains_a_script_only_job_with_no_tokens(self):
        self.assertEqual(ar.per_job(self.rows)["disk-watchdog"]["tokens"], 0)

    def test_a_job_has_a_tail_worth_reporting(self):
        stats = ar.per_job(self.rows)["pr-triage"]
        self.assertGreater(stats["p95"] / stats["mean"], 1.5)


class CliTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(OBS / "analyze_runs.py"), *args],
                              capture_output=True, text=True, timeout=60)

    def test_health_table(self):
        out = self.cli()
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("inbox-sync", out.stdout)
        self.assertIn("p95", out.stdout)

    def test_silent_exits_nonzero_so_it_can_gate_a_cron_job(self):
        out = self.cli("--silent")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("daily-briefing", out.stdout)

    def test_trend_marks_partial_weeks(self):
        out = self.cli("--trend")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("partial", out.stdout)

    def test_unknown_job_is_an_error(self):
        self.assertEqual(self.cli("--job", "nope").returncode, 2)

    def test_a_healthy_fleet_exits_zero_on_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runs.jsonl"
            rows = [run("a", h) for h in range(0, 72)]
            path.write_text("".join(
                json.dumps({k: v for k, v in r.items() if k != "dt"}) + "\n" for r in rows),
                encoding="utf-8")
            out = self.cli("--runs", str(path), "--silent")
        self.assertEqual(out.returncode, 0, out.stdout)


if __name__ == "__main__":
    unittest.main()
