# LearningHermes — Agent Instructions

Book-style course repo for Hermes Agent (Markdown only, no build step). All files English only.

## Layout

- `chapters/01..06-*` — course chapters, numbered. One topic per file, `README.md` as chapter index.
- `examples/` — runnable configs/code referenced by chapters.
- `exercises/` — hands-on tasks, one file per chapter.
- `docs/research/` — raw notes + verified command outputs (evidence base for chapters).

## Workflow

- Verify every Hermes command against real behavior (run it) before writing it into a chapter; save raw output under `docs/research/`.
- Authoritative source for Hermes features: https://hermes-agent.nousresearch.com/docs/llms.txt — check it before claiming a feature exists or doesn't.
- Chapter format: concept → exact verified commands → exercise. No filler prose.
- Commit messages: `chNN: <description>`.
- Do not hand-edit any file outside this repo (Hermes config lives in `~/.hermes/` — read-only reference).
