# Chapter 13 — Shipping Agent Products

> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Shipping and DevOps is the second-most-cited requirement cluster by mentions: 13 of 18 postings with extracted body text name deployment, Docker/Kubernetes, or CI/CD (42 mentions; stats in
`docs/research/jobs/stats-2026-09-12.txt`, reproduce with
`python3 scripts/job_evidence_stats.py`) — Databricks: "Architect and implement robust,
scalable ML infrastructure... support seamless integration of AI/ML models into production"
(`docs/research/jobs/source-02.md`); Reflection: "deploying reliable production systems...
modern DevOps practices (Docker, Kubernetes, and CI/CD)" (`docs/research/jobs/source-04.md`).
Agents are software: they need backends, packaging, CI, and deployment checklists. This chapter
covers running Hermes workloads on the right backend, shipping agent-built products through
GitHub, and distributing whole agent setups.

## Concepts

### Terminal backends: where the agent executes

Verified from `hermes --help`/docs: Hermes runs its tool execution on pluggable backends
— **local** (your machine), **Docker** (isolated containers), **SSH** (remote hosts),
**Daytona/Modal/Singularity** (cloud sandboxes). Selection rules:

- Local: full power, full risk — your real filesystem and credentials.
- Docker: untrusted code, experiments, CI — isolation by default.
- SSH: the agent works *on* your servers (runbooks, ops automation).
- Cloud sandboxes: ephemeral scale-out batch work (Chapter 09's batch processing pairs).

### Shipping an agent-built product

The product loop this course itself follows:

1. **Repo with AGENTS.md** — agents inherit the contract (Chapter 03).
2. **Skills for procedures** — runbooks live in `.hermes/skills/`, not chat history (Ch 10).
3. **Verification evidence** — commands proven, outputs saved (this repo's `docs/research/`).
4. **CI integration** — `hermes send` for notifications (Ch 08); agents in CI via
   `hermes chat -q` one-shots with scoped toolsets.
5. **PR workflow by agent** — branch, commit, PR, review; the GitHub skills catalog
   (code review, issue-to-PR) automates the grudge work.

### Profile distributions: ship the whole agent

`hermes profile export|import|install` (verified) packages a profile — config, skills,
AGENTS.md, memory policy — for teammates or servers. `hermes profile update` re-pulls
updates preserving user data; `hermes backup` (verified) archives everything for disaster
recovery. A senior engineer ships *agent setups*, not just agent outputs.

### Import and migration

`hermes import-agent claude-code|codex` (verified: "One-command import of a Claude Code or
OpenAI Codex CLI setup into Hermes — instructions, allowlists, MCP servers, skills, and
memories") — the on-ramp for existing agent users, and your migration tool when standardizing
a team on one agent runtime.

### The deployment checklist (senior habit)

Before any agent automation goes live: toolset scope minimal (Ch 05), fallback chain set
(Ch 02), delivery target verified (Ch 07), approvals/egress reviewed (Ch 15), logs and
incidents observable (Ch 04/14), rollback path known (Ch 04).

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b7-multiagent-shipping.txt`
(backup/profile/portal/project help), `docs/research/hermes/cli-evidence-2026-09-07.txt`
(gateway/run/send for CI paths), `docs/research/hermes/cli-evidence-2026-09-07-b1-foundations-core.txt` (import-agent).

## Verified commands

Backends and isolation:

```bash
hermes --worktree                  # -w: git-worktree isolation for repo work
hermes chat -q "run tests" -t terminal   # scoped one-shot in CI
```

Product loop:

```bash
git checkout -b feature/x
hermes chat -q "Implement feature X per AGENTS.md, commit as chNN" -t terminal,memory
gh pr create --fill                # or let the agent do it via GitHub skills
```

Distribution:

```bash
hermes profile export my-setup -o my-setup.tar
hermes profile install https://github.com/org/team-agent-setup
hermes profile update
hermes backup -o ~/hermes-$(date +%F).zip
```

Migration:

```bash
hermes import-agent claude-code --dry-run   # preview what moves
hermes import-agent claude-code
```

## Common pitfalls

- **Local backend for untrusted code.** An agent running a stranger's repo on the local
  backend has your real credentials in reach. Docker backend is the default for that job.
- **CI agents with unscoped tools.** `hermes chat -q` in CI without `-t` loads everything;
  give CI the two toolsets it needs.
- **Backups with secrets.** `hermes backup` archives `.env` too — store archives
  encrypted, share never.
- **Profile distributions as config dumps.** Sanitize memory/sessions before `export`;
  distributions ship skills+rules, not your conversation history.
- **Skipping the dry-run on import.** `--dry-run` exists (verified) — use it before
  overwriting an existing setup.

## Exercises

Work through `exercises/ex13-shipping-agent-products.md`. Verification: one feature
shipped repo→PR by agent, one profile distribution installed elsewhere (or exported +
manifest reviewed), CI notification wired, deployment checklist written for a real job.
