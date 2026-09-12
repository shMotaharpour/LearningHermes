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

Corollaries learned the hard way (details in `docs/research/README.md`):

- Quoted job-ad text is **verbatim**; mark elisions with `[...]` instead of silently
  dropping words, and cite the file that actually contains the quote.
- Aggregate counts (`N postings`, `N mentions`) are produced by
  `scripts/job_evidence_stats.py`, never hand-tallied; `--check` fails on drift.
- Never leave an empty evidence file behind: an unpublishable fetch is recorded as a
  `failed_fetches` entry in `docs/research/jobs/ledger.json`, not as a zero-byte `source-*.md`.
- Machine state is a dated snapshot. Write the shape of the output plus the command that
  produced it, and let `scripts/verify_chapters.py` tell you when the live CLI has moved on.

## Chapter Contract

Each chapter directory `chapters/NN-slug/` contains:

- `README.md` with exactly these sections (in order):
  `## Why this matters (job link)` · `## Concepts` · `## Verified commands` ·
  `## Common pitfalls` · `## Exercises`
- A `> **Verified:** YYYY-MM-DD · Hermes Agent vX.Y.Z · recheck: python3 scripts/verify_chapters.py`
  header line, updated whenever the chapter's commands are re-run against a live install.
- Optional `notes.md` for drafts; delete before publication.
- `AGENTS.md` with chapter-specific authoring rules and research pointers.

Each chapter has one matching `exercises/exNN-<slug>.md` — the slug must equal the chapter
directory slug — with `## Objective`, `## Tasks`, and `## Verification checklist` (commands
the learner runs to confirm success).

`scripts/validate_course.py` enforces all of the above, plus: the `CURRICULUM.md` chapter
table matches the chapter directories, every `docs/research/...` citation resolves to an
existing non-empty file, code fences are balanced, and stale `examples/`/`assets/`
references are reported as warnings until the file exists.

## Style

- Concept → exact commands → exercise. No filler prose, no marketing.
- Prefer real verified output over paraphrase; show command then output.
- Keep each chapter focused on its CURRICULUM.md scope; cross-link instead of repeating.

## Repo Tooling

- `python3 scripts/validate_course.py --root .` — validates the chapter contract, citations,
  exercise pairing, and section order. `--other <path>` compares structural parity with
  another branch checkout (same files, same code-block counts).
- `python3 scripts/job_evidence_stats.py [--out FILE | --check]` — renders the job-market
  statistics quoted in `CURRICULUM.md` and the chapters; `--check` recomputes them from
  `docs/research/jobs/` and fails on drift.
- `python3 scripts/rebuild_job_ledger.py [--check]` — rebuilds the posting→evidence index.
- `python3 scripts/verify_chapters.py [--chapter NN] [--json]` — read-only; resolves every
  quoted `hermes` command through `--help` on the installed CLI and reports commands that no
  longer resolve.
- `python3 -m unittest discover -s tests -v` — repo script tests (standard library only;
  `python3 -m pytest tests/ -q` also works when pytest is installed).
- Do not hand-edit anything outside this repo (Hermes config in `~/.hermes/` is read-only
  reference material, never modified for course writing).

## Git & Delivery

- Work on a branch; one chapter (or one structural change) per commit series.
- CI (`.github/workflows/validate.yml`) runs the structure validator, both `--check` guards,
  and the unit tests on every push and pull request.
- Before pushing the `farsi` branch, run the parity check against `english`.
- Never commit secrets, API keys, tokens, or personal `.env` content. Research files must
  be free of credentials.
- Licensing: course text is CC BY 4.0 (`LICENSE-CONTENT`), repo code is MIT (`LICENSE`).
