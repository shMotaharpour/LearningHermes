# LearningHermes

A structured, project-based course for mastering [Hermes Agent](https://github.com/NousResearch/hermes-agent)
and becoming a **Senior Applied AI Engineer** — from first session to shipping production
agent systems. Every chapter maps to competencies extracted from real job postings and is
verified against live Hermes behavior.

**Bilingual course:** branch `english` is the base; branch `farsi` is a full Persian
translation (English technical terms preserved). Content is identical across branches.

## The Course

- **Syllabus:** [CURRICULUM.md](CURRICULUM.md) — 5 parts, 19 chapters, competency mapping.
- **Path:** Agent Operator → Agent Power User → Automation Engineer → Agent Developer →
  Senior Applied AI Engineer.

## Before You Start

**What you need to already know.** This is not a first programming course; it assumes a
working engineer:

| | Level assumed | Where it bites if you are below it |
|---|---|---|
| Python | Read and write scripts; virtualenvs; `pip` | Parts IV–V (plugins, embedding, eval harnesses) |
| Linux / CLI | Comfortable in a shell; paths, pipes, exit codes, `systemd --user` basics | Part II onward; the gateway is a systemd service |
| Git | Branches, commits, pull requests | Chapter 09 (worktrees) and Chapter 13 (agent PR workflow) |
| Docker | Can run and inspect a container | Chapter 13's isolation backends; optional elsewhere |
| HTTP / APIs | REST, JSON, tokens, webhooks | Chapters 08, 11, 12 |

You do **not** need prior agent, LLM, or ML experience — that is what the course teaches.

**What you need on the machine.** A Linux, macOS, or WSL2 box you control (the gateway
and cron chapters need a host that stays up), a Hermes Agent install, and at least one
model provider API key. Python 3.11+ for the repo's own tooling.

**Time.** The estimate below is *hands-on* time — reading a chapter and actually doing its
exercise on a real machine — for the audience described above. Parts III and V are where
unattended runs mean wall-clock time exceeds working time.

| Part | Chapters | Estimated hands-on time |
|---|---|---|
| I — Foundations | 01–03c | 12–17 h |
| II — Operating the Agent | 04–06 | 7–11 h |
| III — Automation Engineering | 07–09 | 9–14 h |
| IV — Building & Extending | 10–13 | 12–18 h |
| V — Production Engineering | 14–15 | 9–14 h |
| Capstone | 16 | 30–50 h over ~6 weeks (incl. a 14-day unattended run) |
| **Total** | | **~79–122 h**, plus the capstone's calendar time |

The capstone is deliberately calendar-bound, not effort-bound: `exercises/ex16-capstone-senior-portfolio.md`
requires an automation that runs unattended for 14 days, and that cannot be compressed.

## Repository Layout (agent-based)

```
AGENTS.md                  # Root agent instructions (what any agent working in this repo must know)
CURRICULUM.md              # Canonical syllabus: parts, chapters, competency clusters
chapters/                  # 19 chapters, 5 parts — one directory per chapter
  AGENTS.md                # Shared chapter contract: the rules every chapter obeys
  NN[x]-slug/              # a letter suffix (03b) marks a chapter inserted between two others
  NN-slug/
    README.md              # Chapter content: concepts -> verified commands -> pitfalls -> exercises
    AGENTS.md              # That chapter's delta only (scope, what it ships, local rules)
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
  check.sh                 # the whole pre-PR gate in one command
tests/                     # Tests for repo scripts (standard library only)
.github/workflows/         # CI: structure + evidence checks on every push and pull request
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
- Checks before a pull request — all of them, in one command:

  ```bash
  scripts/check.sh
  ```

  It runs the four checks CI runs plus the one CI cannot (`verify_chapters.py` needs a
  real `hermes` on PATH, and is skipped with a notice when the CLI is absent). Every check
  runs even after one fails, so you get the whole list. Individually:

  ```bash
  python3 scripts/validate_course.py --root .      # structure, citations, exercise pairing
  python3 scripts/job_evidence_stats.py --check    # quoted numbers vs docs/research/jobs/
  python3 scripts/rebuild_job_ledger.py --check    # evidence ledger up to date
  python3 -m unittest discover -s tests -v         # repo tests (no third-party deps)
  python3 scripts/verify_chapters.py               # re-run the quoted commands (needs the CLI)
  ```

  The repo's own tooling has **no third-party dependencies** — standard library only, on
  Python 3.11+. There is nothing to `pip install` to run the checks.

  One *example* needs a package: `examples/retrieval-scale/` uses `sqlite-vec` for real
  vector search (Chapter 03c). Its tests skip cleanly when the package is absent, so
  `python3 -m unittest discover -s tests` still passes everywhere; `pip install sqlite-vec`
  to actually run them.

- Add `--other <path>` to the validator to compare two branch checkouts (structural parity).
- See `CONTRIBUTING.md` for the full chapter contract and evidence rules.

## Sources of Truth

- Official docs index: https://hermes-agent.nousresearch.com/docs/llms.txt
- Hermes source: https://github.com/NousResearch/hermes-agent
- Job-market evidence: `docs/research/jobs/` (`ledger.json`, generated `stats-*.txt`)
