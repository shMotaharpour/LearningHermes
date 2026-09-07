# AGENTS.md — LearningHermes (root)

Book-style course repo for Hermes Agent. Markdown-first, no build step. Any agent
(Hermes, Claude Code, Codex, or human editors) working in this repo must follow these rules.

## Identity

- Course: LearningHermes — Hermes Agent → Senior Applied AI Engineer.
- Syllabus is canonical: `CURRICULUM.md`. Do not add/rename/move chapters without updating
  it, the root `README.md`, and `scripts/validate_course.py`.
- Base branch: `english`. Translation branch: `farsi`. Both branches have identical file
  trees; only prose language differs.

## Language Rules (branch-dependent)

- `english` branch: every file is English only. No Persian in any tracked file.
- `farsi` branch: teaching prose (`.md` content outside code) is Persian; standard English
  technical terms (agent, tool, skill, session, cron, webhook, eval, RAG, MCP, …) stay
  English; code blocks, commands, paths, frontmatter keys, and file names stay English.
- Commit messages are always English, format `chNN: <description>` or `repo: <description>`.

## Verification Rule (the core invariant)

Never write an unverified Hermes claim into a chapter.

1. Run the actual command (`hermes ...`) or fetch the official doc page.
2. Save raw evidence under `docs/research/hermes/` (e.g. `cli-evidence-YYYY-MM-DD.txt`).
3. Reference the evidence file from the chapter that uses the commands.
4. If a feature can't be verified live, cite the doc page URL inline instead of inventing
   output. Docs index: https://hermes-agent.nousresearch.com/docs/llms.txt

## Chapter Contract

Each chapter directory `chapters/NN-slug/` contains:

- `README.md` with exactly these sections (in order):
  `## Why this matters (job link)` · `## Concepts` · `## Verified commands` ·
  `## Common pitfalls` · `## Exercises`
- Optional `notes.md` for drafts; delete before publication.
- `AGENTS.md` with chapter-specific authoring rules and research pointers.

Each chapter has one matching `exercises/exNN-<slug>.md` with: objective, numbered tasks,
and a verification checklist (commands the learner runs to confirm success).

## Style

- Concept → exact commands → exercise. No filler prose, no marketing.
- Prefer real verified output over paraphrase; show command then output.
- Keep each chapter focused on its CURRICULUM.md scope; cross-link instead of repeating.

## Repo Tooling

- `python3 scripts/validate_course.py --root .` — validates chapter contract + evidence
  references. `--other <path>` compares structural parity with another branch checkout
  (same files, same code-block counts).
- `python3 -m pytest tests/ -q` — repo script tests.
- Do not hand-edit anything outside this repo (Hermes config in `~/.hermes/` is read-only
  reference material, never modified for course writing).

## Git & Delivery

- Work on a branch; one chapter (or one structural change) per commit series.
- Before pushing the `farsi` branch, run the parity check against `english`.
- Never commit secrets, API keys, tokens, or personal `.env` content. Research files must
  be free of credentials.
