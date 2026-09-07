# Chapter 10 — Skills Engineering

## Why this matters (job link)

Hiring posts keep asking for people who build *internal tooling and knowledge systems*:
100ms — "develop internal tooling to speed up evaluation, annotation, and iteration
cycles" (`docs/research/jobs/source-05.md`); Paramount — "build LLM tools for test case
generation... synthetic test data creation" (`docs/research/jobs/source-01.md`). Skills are
Hermes' answer: packaged, reusable procedures the agent itself writes, loads on demand,
and improves over time. After this chapter you can turn any workflow you've repeated twice
into an installable asset — which is also exactly how this course repo teaches agents to
maintain itself (`.hermes/skills/learninghermes-authoring/`).

## Concepts

### What a skill is

A skill is a directory with a `SKILL.md`: YAML frontmatter (name, description) + a
markdown body of procedure. The **description** rides in every session's skills index
(Chapter 03 showed it costing ~10.6K chars for ~90 skills); the **body** loads only when
the agent (or you, via `/skill`) pulls it. Skills may carry linked files — references,
templates, scripts — resolved relative to the skill directory.

```markdown
---
name: my-deploy-runbook
description: "Use when deploying the api service — steps, checks, rollback."
---
# Deploy runbook
1. ...
```

### Where skills live

| Location | Scope | Loads when |
|---|---|---|
| `~/.hermes/skills/` | user-global | every session |
| `<repo>/.hermes/skills/` | project | sessions in that repo **after trust** |
| Bundled/optional catalogs | shipped with Hermes | enabled via config |

The trust model is explicit (verified `hermes skills trust/untrust`): repo-local skills
load only for repos you trust — a prompt-injection defense, not a convenience.

### Progressive disclosure economics

Index line = description only (keep the first ~57 chars a self-contained trigger: "Use
when X. Behavior."). Body = full procedure, zero standing cost. This is the same
index/payload trade as RAG; write descriptions as retrieval-optimized queries.

### The curator: skills as a maintained system

`hermes curator` (verified subcommand in evidence batch 1) is background maintenance:
usage tracking, staleness detection, archival, LLM-driven review of agent-created skills.
Combined with `hermes skills check|update|audit|diff|list-modified`, skills become
versioned infrastructure — not vibes in a prompts folder.

### Registries and publishing

`hermes skills search|install|inspect|publish` (verified) reach registries (skills.sh,
well-known endpoints, GitHub). Install is inspectable *before* landing: `hermes skills
inspect <id>` previews content without installing — read skills like you read dependencies.

### Authoring discipline (this course's own contract)

1. Description = trigger condition, not marketing.
2. Body = procedure with exact verified commands — same rule as chapters.
3. Linked files for references/templates/scripts; keep SKILL.md lean.
4. Name = lowercase-hyphen, stable; rename = break every reference.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b5-skills-mcp-plugins.txt`
(live skills list table incl. Trust/Status columns, inspect help),
`docs/research/hermes/cli-evidence-2026-09-07.txt` (full skills command tree with
trust/publish/audit). Live proof-by-existence: this repo's
`.hermes/skills/learninghermes-authoring/SKILL.md`.

## Verified commands

Inventory and lifecycle:

```bash
hermes skills list              # name/category/source/trust/status table
hermes skills search <query>    # registries
hermes skills inspect <id>      # preview WITHOUT installing
hermes skills install <id>      # install from registry
hermes skills uninstall <id>
hermes skills config            # interactive enable/disable
```

Trust and project skills:

```bash
hermes skills trust <repo>      # allow repo-local skills to load
hermes skills untrust <repo>    # revoke
```

Maintenance:

```bash
hermes skills check             # hub skills: updates available?
hermes skills update            # apply updates
hermes skills audit             # re-scan installed skills
hermes skills diff <skill>      # your edits vs stock bundled version
hermes skills list-modified     # what you've customized
hermes skills publish           # push your skill to a registry
```

## Common pitfalls

- **Description bloat.** A paragraph-long description inflates the every-session index.
  One line: trigger + behavior.
- **Procedures in SOUL.md/MEMORY.md instead of skills.** Memory is for facts; skills are
  for procedures. A runbook living in memory is unrevisable and unshareable.
- **Skipping `inspect` before install.** Third-party skills are injected context — read
  them like code from a stranger.
- **Untrusted project skills silently not loading.** New repo with skills + nothing loads?
  You haven't run `hermes skills trust`.
- **Editing bundled skills in place.** `update` will fight you; use `list-modified`/`diff`
  consciously, or fork into your own skill.
- **Name drift.** Referencing `my-skill` in cron prompts after renaming it to `my-skill-v2`
  breaks automation — keep names stable.

## Exercises

Work through `exercises/ex10-skills-engineering.md`. Verification: one skill authored,
loaded on demand, one registry skill inspected-then-installed, trust model exercised.
