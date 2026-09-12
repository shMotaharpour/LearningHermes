#!/usr/bin/env python3
"""Rebuild docs/research/jobs/ledger.json — the provenance index for job evidence.

The first ledger was a hand-written list of six URLs with empty titles and no link to the
`source-NN.md` files the chapters cite, so a citation could not be resolved back to the
evidence. This CLI rebuilds it from the evidence itself, using the shared rules in
`scripts/job_evidence.py` (same posting universe as `job_evidence_stats.py`).

Usage:
    python3 scripts/rebuild_job_ledger.py            # write ledger.json
    python3 scripts/rebuild_job_ledger.py --check    # fail if ledger.json is stale
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from job_evidence import build_ledger  # noqa: E402

JOBS_DIR = Path(__file__).resolve().parent.parent / "docs" / "research" / "jobs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit non-zero if ledger.json is stale")
    parser.add_argument("--jobs-dir", type=Path, default=JOBS_DIR)
    args = parser.parse_args()

    rebuilt = build_ledger(args.jobs_dir)
    text = json.dumps(rebuilt, indent=2, ensure_ascii=False) + "\n"
    target = args.jobs_dir / "ledger.json"

    if args.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != text:
            print(f"{target} is stale — run: python3 scripts/rebuild_job_ledger.py", file=sys.stderr)
            return 2
        print(f"ledger.json up to date ({rebuilt['counts']['entries']} entries)")
        return 0

    target.write_text(text, encoding="utf-8")
    c = rebuilt["counts"]
    print(
        f"wrote {target.relative_to(Path.cwd()) if str(target).startswith(str(Path.cwd())) else target} — "
        f"{c['entries']} entries ({c['with_body']} with body text, {c['title_only']} title-only), "
        f"{c['source_files']} source files linked"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
