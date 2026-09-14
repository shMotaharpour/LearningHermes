# Evidence (`docs/research/`)

Every quantitative or behavioural claim in a chapter must be traceable to a file in this
directory. Nothing here is decoration: these files are the citation targets of the course.

## Layout

- `hermes/` — raw Hermes CLI outputs, doc snapshots (`llms.txt`), and capability evidence.
  Naming: `cli-evidence-YYYY-MM-DD.txt` (or `-bN` suffixes for batch captures).
- `jobs/` — job-posting research: extracted postings (`source-NN.md`), search/extract
  dumps (`*.json`), the provenance index (`ledger.json`), and generated statistics
  (`stats-YYYY-MM-DD.txt`).
- `google/` — third-party product research for Chapter 13b, which is the one chapter this
  repo cannot verify by running anything. Naming: `<topic>-YYYY-MM-DD.md`. Each file is a
  dated snapshot with source URLs, captured externally and stored verbatim under a
  provenance header. It supports the weaker `Reviewed:` standard. A chapter carrying
  `Verified:` may cite it only for material that chapter has *explicitly marked as not
  verified by this repo* — never as backing for a command under the `Verified:` header.
- `labs/`, `capstone/` — learner-produced artifacts. These paths are *expected to be
  absent* in the repo and are allowed as references; validators skip them.

## Rules

1. **Cite the file that actually contains the claim.** A citation that points at the wrong
   file is a course bug, not a rounding error. `scripts/validate_course.py` opens every
   referenced path and fails on dangling references.
2. **No empty evidence files.** A failed fetch gets a `note` on its `jobs/ledger.json`
   entry, not a zero-byte file. The validator fails on empty files here.
3. **Numbers are generated, never hand-tallied.** Counts quoted in `CURRICULUM.md` and the
   chapters come from `scripts/job_evidence_stats.py`:

   ```bash
   python3 scripts/job_evidence_stats.py                # render the stats
   python3 scripts/job_evidence_stats.py --out docs/research/jobs/stats-$(date +%F).txt
   python3 scripts/job_evidence_stats.py --check        # verify the quoted numbers still match
   ```

   `--check` fails if the cluster table in `CURRICULUM.md`, or any
   "N of M postings with extracted body text" claim in a chapter, disagrees with the
   evidence. Do not edit those numbers by hand.
4. **Provenance is generated too.** `jobs/ledger.json` is rebuilt from the evidence files:

   ```bash
   python3 scripts/rebuild_job_ledger.py          # rewrite ledger.json
   python3 scripts/rebuild_job_ledger.py --check  # CI guard: ledger must be current
   ```

   Both CLIs share `scripts/job_evidence.py`, so the corpus size they report can never
   diverge.
5. **Snapshots are dated.** Anything captured from a live machine (session counts, model
   routing, `prompt-size` output) is a snapshot, not a law: quote it with its date and keep
   the *shape* as the lesson. `scripts/verify_chapters.py` re-checks quoted commands
   against the installed CLI and reports drift.
6. **No credentials.** Never store API keys, tokens, cookies, or `.env` content here.
   Redact them as `[REDACTED]` if raw output contains them.
