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
    hermes/                # Verified Hermes CLI outputs + llms.txt snapshot (evidence base)
    jobs/                  # Job posting research: postings, searches, ledger
scripts/                   # Course tooling (validate_course.py and friends)
tests/                     # Tests for repo scripts
.hermes/
  skills/                  # Project-local skills agents auto-load when working here
  settings.json            # Project-scoped Hermes settings
```

## How to Read This Course

- Read `CURRICULUM.md` first, then chapters in order within each part.
- Every chapter ends with exercises in `exercises/` — do them on a real machine.
- Code blocks are exact, verified commands. Evidence for every claim lives in `docs/research/`.

## For Agents Working in This Repo

Read `AGENTS.md` (root) before anything else — it defines the authoring workflow,
verification requirements, commit conventions, and the bilingual branch rules.

## Contribution / Workflow

- Base branch: `english`. Translation branch: `farsi`.
- Verify every Hermes command against real behavior before it enters a chapter; save raw
  output under `docs/research/hermes/`.
- Keep chapters tight: concept → exact commands → exercise. No marketing prose.
- Commits: `chNN: <short description>` (e.g. `ch07: add cron notepad reference`).
- Validate structure/parity: `python3 scripts/validate_course.py --root .` (add
  `--other <path>` to compare two branch checkouts).

## Sources of Truth

- Official docs index: https://hermes-agent.nousresearch.com/docs/llms.txt
- Hermes source: https://github.com/NousResearch/hermes-agent
- Job-market evidence: `docs/research/jobs/`
