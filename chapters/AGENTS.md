# AGENTS.md — `chapters/` (shared chapter contract)

Applies to every `chapters/NN-slug/`. Read with the root `AGENTS.md`; the per-chapter file
carries **only what is true of that chapter and nothing else**.

This split is Chapter 03's own lesson applied to the repo: shared rules live once, at the
scope they govern. Sixteen copies of the same paragraph do not stay identical — they drift,
and then nobody knows which copy is authoritative.

## Verification

- Verify every Hermes command live before writing it here. Append raw output to
  `docs/research/hermes/` and cite the file from `README.md`.
- Never write an unverified Hermes claim into a chapter. If you cannot run it, do not quote
  it.
- Numbers taken from a live machine are dated snapshots, labelled as such, and paired with
  the command that produced them.
- `python3 scripts/verify_chapters.py` re-checks every quoted command. A subcommand a plugin
  registers is marked with a trailing `# plugin: <name>` so it is counted separately rather
  than reported as drift.

## Structure

- The five required top-level sections, in order: `## Why this matters (job link)`,
  `## Concepts`, `## Verified commands`, `## Common pitfalls`, `## Exercises`. Do not add
  extra top-level sections; `###` subsections are how you add material.
- A `> **Verified:** YYYY-MM-DD · Hermes Agent vX.Y.Z · recheck: ...` header, with the same
  date and version as every other chapter. The course is re-verified as one pass.
- Every chapter ends with two `###` subsections that are now part of the contract:
  **The general pattern** (inside `## Concepts`) — the platform-agnostic problem under the
  chapter's commands — and **Senior interview probes** (after the exercise pointer), eight
  questions answerable from the chapter, each with a wrong answer.
- One exercise file per chapter at `exercises/exNN-<slug>.md`, slug matching the directory,
  with `## Objective`, `## Tasks`, `## Verification checklist`.
- Chapter numbers may carry a single lowercase letter (`03b`) for a chapter inserted between
  two others. That is deliberate, not a typo: renumbering rewrites every cross-reference in
  the course and forces the same rename on the translation branch.

## Content

- No filler prose. Concept → exact commands → exercise.
- Shipped code is not decoration: if a chapter ships something under `examples/`, its
  behaviour is pinned by a file under `tests/`, and claims about it cite the test rather
  than asserting in prose.
- Relevant docs: start from https://hermes-agent.nousresearch.com/docs/llms.txt and pick the
  feature pages listed in `CURRICULUM.md` for that chapter.

## Writing the per-chapter file

State only the delta: the chapter's scope boundary (especially what belongs to a
neighbouring chapter), what it ships under `examples/` and which test pins it, and any rule
that applies here and nowhere else. If you find yourself restating a rule from this file,
delete it — `scripts/validate_course.py` fails on a line duplicated from here.
