# Chapter 13 — Shipping Agent Products

> **Verified:** 2026-09-14 · Hermes Agent v0.21.3 (2026.9.14) · recheck: `python3 scripts/verify_chapters.py`

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

### Machine-checkable project bootstrap (`hermes verify`)

Every item so far is a habit. `hermes verify` is the one that a machine can enforce: it
detects how the project is built, tested and started, then runs the pass
**bootstrap → build → test → start in background → poll readiness → teardown** and reports
the result.

```bash
hermes verify --detect-only            # print the detected recipe as JSON, run nothing
hermes verify --save                   # write it to .hermes/environment.json
hermes verify --phase test --json      # run one phase, machine-readable result (CI)
hermes verify --skip-start             # command phases only, no readiness poll
```

Two things make this more than a convenience. First, `--save` turns detection into a
**committed manifest** (`.hermes/environment.json`): the project now states how it is
built rather than having each agent re-guess, which is the same argument Chapter 03 makes
for `AGENTS.md`, applied to the build. Second, the `start → poll readiness → teardown`
phases test the thing CI usually skips — that the app actually comes up. `--port` and
`--ready-timeout` tune the poll; `--timeout` bounds each phase (default 600s).

Run it before you hand an agent a repo it has never seen. A green `hermes verify` is the
difference between "the agent can edit this project" and "the agent can tell whether its
edit worked".

### The deployment checklist (senior habit)

Before any agent automation goes live: toolset scope minimal (Ch 05), fallback chain set
(Ch 02), delivery target verified (Ch 07), failure notices routed away from the audience
(Ch 07's `--failure-deliver`), approvals/egress reviewed (Ch 15), logs and incidents
observable (Ch 04/14), rollback path known (Ch 04), build/test/start verified
(`hermes verify`), and the global stop understood by whoever is on call
(`hermes pause`/`hermes resume`, Ch 07/15).

### The general pattern

Shipping an agent is shipping a system that acts, and the questions are the ones any
production system faces — with one addition that catches people out.

- **Where does the code run, and what can it reach from there?** The backend choice is a
  blast-radius choice before it is a performance one. An agent on the local backend has your
  real credentials in reach; that is fine for your own repo and wrong for a stranger's.
- **Can a newcomer tell whether it works?** A committed build/test/start manifest is the
  difference between "the agent can edit this project" and "the agent can tell whether its
  edit worked". It is the same argument as a README that is actually runnable.
- **What do you ship — outputs, or the setup that produces them?** Distributing a profile
  rather than a result is how an agent capability becomes a team capability, and it carries
  the same hazards as any artifact distribution: sanitise it, version it, and know what is
  inside the archive.
- **The addition:** your artifact is non-deterministic. Everything above is necessary and
  none of it is sufficient, which is why the deployment checklist ends at an eval gate
  (Chapter 14) rather than at a green build.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b7-multiagent-shipping.txt`
(backup/profile/portal/project help), `docs/research/hermes/cli-evidence-2026-09-07.txt`
(gateway/run/send for CI paths), `docs/research/hermes/cli-evidence-2026-09-07-b1-foundations-core.txt` (import-agent),
`docs/research/hermes/cli-evidence-2026-09-13-v0.21.2-surface.txt` (`verify` and `backup` on
v0.21.2 — `backup -k/--keep` is new since v0.20.6).

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
hermes backup -o ~/backups --keep 7    # prune older hermes-backup-*.zip beyond the newest 7
```

Project verification:

```bash
hermes verify --detect-only        # detected build/test/start recipe as JSON
hermes verify --save               # commit it as .hermes/environment.json
hermes verify --phase test --json  # one phase, machine-readable (CI)
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
- **Unbounded backup directories.** Full backups accumulate until the disk says no.
  `hermes backup --keep N` prunes older `hermes-backup-*.zip` in the output directory
  (default 3; `0` keeps everything) — but note it prunes *after* a full backup, so a
  scheduled backup job is where it belongs, not a one-off run.
- **Handing an agent a repo you never verified.** `hermes verify` takes a minute and tells
  you whether test and start even work. Without it, the agent's first failure is
  indistinguishable from the project's.

## Exercises

Work through `exercises/ex13-shipping-agent-products.md`. Verification: one feature
shipped repo→PR by agent, one profile distribution installed elsewhere (or exported +
manifest reviewed), CI notification wired, deployment checklist written for a real job.

### Senior interview probes

1. An agent must run a stranger's repository. Which backend, and what have you prevented?
2. What is the first thing you do before handing an agent a codebase it has never seen?
3. You are putting an agent in CI. What do you scope, and what would an unscoped run cost
   you at 2am?
4. How do you ship an agent capability to five teammates so that it keeps working next
   month?
5. `hermes backup` includes the environment file. What follows from that for retention and
   for storage?
6. Your deployment checklist has ten items. Which one is agent-specific, and why do the
   other nine not suffice?
7. A team wants to migrate from another agent CLI. What moves, what does not, and how do you
   find out before committing?
8. What does "done" mean for an agent feature, and how is that different from a service?
