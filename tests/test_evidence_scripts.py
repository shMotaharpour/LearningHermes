"""Regression tests for the evidence CLIs; standard library only.

The bug these tests exist for: `job_evidence_stats.py` and `rebuild_job_ledger.py` used to
count their corpus independently and disagreed (25 vs 22 postings). Both now share
`scripts/job_evidence.py`; these tests pin that agreement on a fixture.
"""
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
STATS = SCRIPTS / "job_evidence_stats.py"
LEDGER = SCRIPTS / "rebuild_job_ledger.py"

BODY = (
    "Senior Forward Deployed Engineer. You will deploy agent systems on Kubernetes, "
    "own CI/CD pipelines, and evaluate model quality with regression evals. "
) * 4

EXTRACT = {
    "results": [
        {
            "url": "https://jobs.example.com/1",
            "title": "Senior Forward Deployed Engineer",
            "content": BODY,
        },
        {
            "url": "https://jobs.example.com/2",
            "title": "Applied AI Engineer (title only)",
        },
    ]
}


class EvidenceScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.jobs = Path(self.temp.name) / "jobs"
        self.jobs.mkdir(parents=True)
        (self.jobs / "extract-batch-1.json").write_text(json.dumps(EXTRACT), encoding="utf-8")
        (self.jobs / "source-01.md").write_text(
            "# Senior Forward Deployed Engineer\n\n" + BODY, encoding="utf-8")

    def run_cli(self, script, *args):
        return subprocess.run(
            [sys.executable, str(script), "--jobs-dir", str(self.jobs), *args],
            capture_output=True, text=True)

    def test_stats_and_ledger_agree_on_corpus_size(self):
        stats = json.loads(self.run_cli(STATS, "--json").stdout)
        self.run_cli(LEDGER)
        ledger = json.loads((self.jobs / "ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["counts"]["entries"], stats["postings_discovered"])
        self.assertEqual(ledger["counts"]["with_body"], stats["postings_with_body_text"])
        self.assertEqual(ledger["counts"]["with_body"], 1)
        self.assertEqual(ledger["counts"]["entries"], 2)

    def test_source_file_is_linked_to_its_posting(self):
        self.run_cli(LEDGER)
        ledger = json.loads((self.jobs / "ledger.json").read_text(encoding="utf-8"))
        linked = [e for e in ledger["entries"] if e["source_file"]]
        self.assertEqual([e["source_file"] for e in linked], ["docs/research/jobs/source-01.md"])
        self.assertEqual(linked[0]["url"], "https://jobs.example.com/1")

    def test_ledger_check_detects_stale_index(self):
        self.run_cli(LEDGER)
        ledger_path = self.jobs / "ledger.json"
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
        data["entries"] = data["entries"][:1]
        data["counts"]["entries"] = 1
        ledger_path.write_text(json.dumps(data), encoding="utf-8")
        result = self.run_cli(LEDGER, "--check")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("is stale", result.stderr)

    def test_stats_check_flags_unreproducible_curriculum_number(self):
        root = Path(self.temp.name)
        (root / "CURRICULUM.md").write_text(
            "| Cluster | Postings | Mentions |\n"
            "|---------|---------:|---------:|\n"
            "| Shipping & DevOps | 9/18 | 7 |\n",
            encoding="utf-8")
        result = self.run_cli(STATS, "--check", "--root", str(root))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Shipping & DevOps quotes 9/", result.stderr)

    def test_stats_check_flags_chapter_claim(self):
        root = Path(self.temp.name)
        (root / "CURRICULUM.md").write_text("# Curriculum\n", encoding="utf-8")
        (root / "chapters" / "13-shipping").mkdir(parents=True)
        (root / "chapters" / "13-shipping" / "README.md").write_text(
            "Shipping: 4 of 18 postings with extracted body text (2 mentions).\n", encoding="utf-8")
        result = self.run_cli(STATS, "--check", "--root", str(root))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("matches no cluster in the evidence", result.stderr)


    def test_stats_check_flags_out_of_order_cluster_table(self):
        rep = json.loads(self.run_cli(STATS, "--json").stdout)
        clusters = rep["clusters"]
        if len(clusters) < 2:
            self.skipTest("fixture must match at least two clusters")
        rows = "".join(
            f"| {c['cluster']} | {c['postings']}/{rep['postings_with_body_text']} | {c['mentions']} |\n"
            for c in reversed(clusters)
        )
        root = Path(self.temp.name)
        (root / "CURRICULUM.md").write_text(
            "| Cluster | Postings | Mentions |\n|---------|---------:|---------:|\n" + rows,
            encoding="utf-8")
        result = self.run_cli(STATS, "--check", "--root", str(root))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("observed-frequency order", result.stderr)

    def test_markdown_report_renders_cluster_table(self):
        out = Path(self.temp.name) / "stats.txt"
        result = self.run_cli(STATS, "--out", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        rep = json.loads(self.run_cli(STATS, "--json").stdout)
        text = out.read_text(encoding="utf-8")
        self.assertIn("## Requirement clusters", text)
        self.assertIn("Postings | Mentions", text)
        self.assertIn(f"/{rep['postings_with_body_text']} |", text)


if __name__ == "__main__":
    unittest.main()
