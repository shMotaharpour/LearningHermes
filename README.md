# LearningHermes

A structured, project-based course for mastering [Hermes Agent](https://github.com/NousResearch/hermes-agent)
and becoming a **Senior Applied AI Engineer** — from first session to shipping production
agent systems. Every chapter maps to competencies extracted from real job postings and is
verified against live Hermes behavior.

**Bilingual course:** branch `english` is the base; branch `farsi` is a full Persian
translation (English technical terms preserved). Content is identical across branches.

## The Course

- **Syllabus:** [CURRICULUM.md](CURRICULUM.md) — 5 parts, 16 chapters, competency mapping.
- **Path:** Agent Operator → Agent Power User → Automation Engineer → Agent Developer →
  Senior Applied AI Engineer.

## Repository Layout (agent-based)

```
AGENTS.md                  # Root agent instructions (what any agent working in this repo must know)
CURRICULUM.md              # Canonical syllabus: parts, chapters, competency clusters
chapters/                  # 16 chapters, 5 parts — one directory per chapter
  NN-slug/
    README.md              # Chapter content: concepts -> verified commands -> pitfalls -> exercises
    AGENTS.md              # Per-chapter authoring rules for agents
    notes.md               # (optional) drafting notes; removed on publication
exercises/                 # One hands-on exercise file per chapter (exNN-<slug>.md)
examples/                  # Runnable configs, prompts, and scripts referenced by chapters
assets/                    # Diagrams and screenshots
docs/
  research/
    README.md              # Evidence rules: what belongs here and how it is kept true
    hermes/                # Verified Hermes CLI outputs + llms.txt snapshot (evidence base)
    jobs/                  # Job posting research: postings, searches, generated stats, ledger
scripts/                   # Course tooling (validators, evidence stats, chapter re-verification)
tests/                     # Tests for repo scripts (standard library only).github/workflows/         # CI: structure + evidence checks on every push and pull request
LICENSE                    # MIT — the code in scripts/, tests/, .github/
LICENSE-CONTENT            # CC BY 4.0 — the course text
CONTRIBUTING.md            # Workflow, chapter contract, evidence rules
.hermes/
  skills/                  # Project-local skills agents auto-load when working here
  settings.json            # Project-scoped Hermes settings
```

## How to Read This Course

- Read `CURRICULUM.md` first, then chapters in order within each part.
- Every chapter ends with exercises in `exercises/` — do them on a real machine.
- Code blocks are exact, verified commands. Evidence for every claim lives in `docs/research/`.
- Each chapter opens with a `Verified:` line: the date its commands were last run and the
  Hermes version they were run against. Numbers quoted from live machine state are labelled
  snapshots — `python3 scripts/verify_chapters.py` re-checks the commands on your install.

## For Agents Working in This Repo

Read `AGENTS.md` (root) before anything else — it defines the authoring workflow,
verification requirements, commit conventions, and the bilingual branch rules.

## Contribution / Workflow

- Base branch: `english`. Translation branch: `farsi`.
- Verify every Hermes command against real behavior before it enters a chapter; save raw
  output under `docs/research/hermes/`.
- Keep chapters tight: concept → exact commands → exercise. No marketing prose.
- Commits: `chNN: <short description>` (e.g. `ch07: add cron notepad reference`).
- Checks before a pull request:

  ```bash
  python3 scripts/validate_course.py --root .      # structure, citations, exercise pairing
  python3 scripts/job_evidence_stats.py --check    # quoted numbers vs docs/research/jobs/
  python3 scripts/rebuild_job_ledger.py --check    # evidence ledger up to date
  python3 -m unittest discover -s tests -v         # repo tests (no third-party deps)
  python3 scripts/verify_chapters.py               # re-run the quoted commands (needs the CLI)
  ```

- Add `--other <path>` to the validator to compare two branch checkouts (structural parity).
- See `CONTRIBUTING.md` for the full chapter contract and evidence rules.

## Sources of Truth

- Official docs index: https://hermes-agent.nousresearch.com/docs/llms.txt
- Hermes source: https://github.com/NousResearch/hermes-agent
- Job-market evidence: `docs/research/jobs/` (`ledger.json`, generated `stats-*.txt`)
