# Chapter 10 — Skills Engineering

> **Verified:** 2026-09-13 · Hermes Agent v0.21.2 (2026.9.11) · recheck: `python3 scripts/verify_chapters.py`

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

### Bundles: several skills under one slash command

`hermes bundles list|show|create|delete|reload` groups skills so that `/<bundle>` from the
CLI or the gateway loads every referenced skill at once. This is composition, and it
interacts directly with the progressive-disclosure budget above: a bundle is a *deliberate*
decision to pay several index lines and potentially several bodies in one move. Bundle the
skills that are genuinely used together in one task (an incident runbook: logs + notepad +
delivery), never "everything about topic X".

`hermes bundles reload` re-scans the bundles directory and reports what changed — the
command you run after editing bundle files by hand.

### Skill Sync: the same skills on every device

`hermes sync` keeps skills with you rather than with one machine. Personal sync moves your
own skills between your devices; if you belong to an organisation, you also receive its
shared skills and can propose your own back to the team.

```bash
hermes sync status          # what is synced, and from where
hermes sync now             # reconcile: pull then push
hermes sync enable <skill>  # opt one skill into your sync
hermes sync disable <skill> # keep one local
hermes sync device          # show/set this device's label
hermes sync propose <skill> # share a skill with your organisation
```

Note the shape: sync is **opt-in per skill** (`enable`/`disable`), and contributing to the
org is a *proposal*, not a push. Both defaults are correct and worth copying into any
internal tooling you build — a skill can carry machine-specific paths or a customer's
procedure, so "sync everything" is a leak, and "anyone can publish to the team" is how a
shared registry rots. `hermes sync device` labels the machine so the sync console shows
which device pushed what, which is the minimum provenance a shared skill store needs.

### Registries and publishing

`hermes skills search|install|inspect|publish` (verified) reach registries (skills.sh,
well-known endpoints, GitHub). Install is inspectable *before* landing: `hermes skills
inspect <id>` previews content without installing — read skills like you read dependencies.

### Authoring discipline (this course's own contract)

1. Description = trigger condition, not marketing.
2. Body = procedure with exact verified commands — same rule as chapters.
3. Linked files for references/templates/scripts; keep SKILL.md lean.
4. Name = lowercase-hyphen, stable; rename = break every reference.

### The general pattern

A skill is a document the agent loads on demand, which makes this chapter about **knowledge
as a maintained artifact** rather than about a file format. Four ideas transfer intact:

- **Index/payload economics.** One line in every prompt, the body only when used. The same
  trade as retrieval (Chapter 03b), tool schemas, and lazy imports — and the same failure:
  an index that grows without bound taxes every unrelated request.
- **A description is a retrieval query.** The agent chooses a skill by reading its first
  line. Writing that line as a trigger ("Use when X") rather than a title is the difference
  between a skill that fires and a skill that sits there. This is the same lesson as tool
  descriptions in Chapter 05, and it recurs because it is the real rule.
- **Loaded content is executed instruction.** A third-party skill is injected context that
  steers the agent, which is why repo-local skills load only for repos you trust. Read them
  like code from a stranger, because functionally that is what they are.
- **Opt-in beats opt-out for sharing, and proposals beat pushes.** A skill can carry
  machine-specific paths or a customer's procedure, so "sync everything" is a leak; and a
  shared registry anyone can write to rots. Both defaults are worth copying into any
  internal tooling you build.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b5-skills-mcp-plugins.txt`
(live skills list table incl. Trust/Status columns, inspect help),
`docs/research/hermes/cli-evidence-2026-09-07.txt` (full skills command tree with
trust/publish/audit),
`docs/research/hermes/cli-evidence-2026-09-13-v0.21.2-surface.txt` (`bundles`, `sync` on
v0.21.2). Live proof-by-existence: this repo's
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

Bundles and sync:

```bash
hermes bundles list             # installed bundles
hermes bundles show <bundle>    # which skills it loads
hermes bundles create           # group skills under one /<bundle> command
hermes bundles reload           # re-scan after hand-editing
hermes sync status              # what is synced, and from where
hermes sync enable <skill>      # opt one skill in (sync is per-skill, not all-or-nothing)
hermes sync now                 # pull then push
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
- **Bundling by topic instead of by task.** A bundle loads every skill it references at
  once. Group what a single task needs; a "topic" bundle is a context bill you pay for
  nothing.
- **Syncing skills that are machine- or customer-specific.** `hermes sync` is per-skill for
  a reason. A skill carrying absolute paths or a client's procedure should stay local —
  check `hermes sync status` after adding anything sensitive.

## Exercises

Work through `exercises/ex10-skills-engineering.md`. Verification: one skill authored,
loaded on demand, one registry skill inspected-then-installed, trust model exercised.

### Senior interview probes

1. What is the difference between a skill and a prompt you paste, and when does that
   difference start to matter?
2. Your team has 90 skills installed. What has that cost, and how would you measure it?
3. A skill you wrote never fires. Where do you look first?
4. Why do repo-local skills require a trust step, and what attack does that prevent?
5. When does a procedure belong in a skill rather than in memory or in the system prompt?
6. You are designing skill sharing for a company. Push or propose? Everything or opt-in?
   Defend both choices.
7. A bundled skill was edited locally and an update is available. What happens, and what
   should happen?
8. What is the equivalent of "index small, payload on demand" in a retrieval system, and why
   is it the same problem?
