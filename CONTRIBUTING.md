# Contributing

This repository is a course, not a blog: every claim in it is expected to be checkable.
The rules below exist because that is the promise the course makes to its readers.

## Language

* All repository files are **English only**, including commit messages, code comments,
  fixtures, and asset filenames.
* The translated branch (`farsi`) is generated from `english`; changes land in `english`
  first, then get mirrored.

## Commits and branches

* Branch naming: `improve/<topic>` for course work, `chNN/<topic>` for chapter work.
* Commit message prefixes: `chNN: <description>` for chapter work, `repo: <description>`
  for repository-level tooling, docs, or hygiene.
* Never commit directly to `english` or `farsi`; open a pull request.

## Adding or changing a chapter

A chapter is `chapters/NN-slug/README.md` plus `chapters/NN-slug/AGENTS.md`, and it must
contain these sections in this order:

1. `## Why this matters (job link)`
2. `## Concepts`
3. `## Verified commands`
4. `## Common pitfalls`
5. `## Exercises`

It also needs:

* a `> **Verified:** YYYY-MM-DD · Hermes Agent vX.Y.Z · recheck: ...` header line, which
  records when the quoted commands were last run against a real installation;
* at least one citation to a real file under `docs/research/`;
* a matching `exercises/exNN-slug.md` with `## Objective`, `## Tasks`, and
  `## Verification checklist`.

`python3 scripts/validate_course.py --root .` enforces all of the above.

## Evidence rules

* Every quoted number must be reproducible by a script in `scripts/` — hand-tallied counts
  are not accepted. `python3 scripts/job_evidence_stats.py --check` fails the build when a
  quoted count drifts from the evidence.
* Every quoted job-advertisement string must be verbatim, with `[...]` marking any elision.
  `scripts/validate_course.py` refuses empty evidence files and dangling citations.
* Machine state (session counts, token sizes, installed model, command output) is a
  **dated snapshot**, never a permanent fact. Label it and point at the evidence file.
* Regenerating the ledger: `python3 scripts/rebuild_job_ledger.py`
  (verify with `--check`).

## Before opening a pull request

```bash
python3 scripts/validate_course.py --root .          # structure + citations
python3 scripts/job_evidence_stats.py --check        # quoted numbers vs evidence
python3 scripts/rebuild_job_ledger.py --check        # provenance index
python3 -m unittest discover -s tests -v             # tests (standard library only)
python3 scripts/verify_chapters.py                   # re-run the `hermes` commands (needs the CLI)
```

`pytest tests/ -q` also works when pytest is installed; the suite is standard-library
`unittest` so it runs anywhere, including on a bare interpreter.

Pushing to `farsi` additionally requires the parity check:

```bash
git worktree add ../lh-en english
python3 scripts/validate_course.py --root . --other ../lh-en
```
