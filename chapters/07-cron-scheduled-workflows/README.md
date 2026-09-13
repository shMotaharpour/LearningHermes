# Chapter 07 — Cron and Scheduled Workflows

> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

"AI & Automation Engineer" postings are, at their core, this chapter: Minted — "design and
implement AI-driven automations and internal copilots that optimize workflows"
(`docs/research/jobs/extract-round2.json`); Adventus — "design, build, and deploy AI
agents that automate enterprise workflows" (same file). Scheduled, reliable, unattended
agent work is the first thing businesses actually buy. Hermes cron turns the agent into a
production scheduler: LLM jobs, script-only jobs, durable delivery, failure incidents,
job-local memory. This chapter covers the full lifecycle plus the operational details
(internals, notepads, troubleshooting) that separate a demo from a deliverable.

## Concepts

### Two kinds of cron jobs

Verified from the live scheduler (evidence b4):

1. **Agent jobs** — a prompt runs through the agent loop on schedule. Fresh session per
   run, tools available, output delivered to a platform target.
2. **Script-only jobs (`no_agent`)** — a script runs on schedule; its stdout is delivered
   verbatim; **empty stdout sends nothing**. No LLM cost. The live example on this machine:
   `docs-folder-watch` — `every 1m`, `Mode: no-agent (script stdout delivered directly)`,
   delivering to a Telegram topic.

The design rule: **watchdogs are scripts, judgments are agents.** Disk alerts, CI pings,
file-change diffs → `no_agent`. Research digests, daily briefings, anything needing
reasoning → agent jobs.

### Anatomy of a job

From the verified `hermes cron list` output, every job has: ID, name, schedule
(`30m`, `every 2h`, cron syntax `0 9 * * *`, or one-shot ISO timestamp), repeat count,
next run, **deliver target** (e.g. `telegram:-1003924862595:307`), script (optional),
mode, last-run status, and execution ID. Jobs are self-contained — a fresh run cannot ask
you questions, so prompts must carry all context.

### Delivery and continuity

- **Deliver targets** use the same `platform:chat[:thread]` format as `hermes send`.
- **Continuity**: an agent job can see its own previous output — the increment/dedup
  pattern (scouts, monitors, digests) builds on it.
- **Notepads**: each job has a durable key-value notepad surviving across runs
  (`hermes cron notepad`).

### Failure is first-class

`hermes cron runs|history` shows durable execution attempts; `hermes cron incidents`
lists/acknowledges failures. A failed agent job is an incident to acknowledge, not a
mystery in a log file.

### Heartbeats and loops (session-local scheduling)

Inside a live session, `/heartbeat 10m <prompt>` re-fires when idle and `/loop` re-runs a
prompt on an interval — session-local relatives of cron for watch-while-I-work cases.

### Scheduling semantics that matter

- Cron-driven jobs need the gateway (or at least the scheduler) running: verified
  `hermes cron status` → "Gateway is running — cron jobs will fire automatically; Ticker
  heartbeat: 1s ago".
- One-shot jobs take ISO timestamps; recurring jobs take intervals or cron expressions.
- `hermes cron tick` runs due jobs once and exits — the deterministic way to test.
- `hermes cron pause/resume` beats delete-and-recreate for temporary silencing.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b4-gateway-cron-events.txt`
(full cron command tree, live job listing with real IDs/schedules/targets, cron status),
`docs/research/hermes/cli-evidence-2026-09-07.txt` (cron help).

## Verified commands

Inspect and test:

```bash
hermes cron list              # jobs with schedules, targets, last-run status
hermes cron status            # scheduler alive? next run?
hermes cron runs <job-id>     # durable execution attempts
hermes cron incidents         # failures to acknowledge
hermes cron tick              # fire due jobs once, exit — safe testing
```

Create (the CLI mirrors what the in-agent cron tool does):

```bash
hermes cron create "0 6 * * *" \
  --name "daily-briefing" \
  --deliver "telegram" \
  --skill grounded-citations \
  "Research AI engineering news since yesterday. Summarize top 5 with links. Persian ZWNJ characters are forbidden in automated prompts."
```

Script-only job (no LLM):

```bash
hermes cron create "every 1h" \
  --name "disk-watchdog" \
  --script /path/to/disk_check.sh \
  --deliver "telegram"          # stdout delivered; empty stdout = silence
```

Manage:

```bash
hermes cron pause <job-id> / resume <job-id>
hermes cron edit <job-id>                # change schedule/prompt/target
hermes cron run <job-id>                 # force next-tick execution
hermes cron remove <job-id>
hermes cron notepad <job-id> read|write  # durable job memory
```

## Common pitfalls

- **Prompts that assume a reader.** Cron runs are autonomous — the job cannot ask you
  anything. Self-contained prompts, explicit output format, explicit delivery.
- **Persian ZWNJ in automated prompts.** Half-spaces (‌) in scheduled prompts get treated
  as injection vectors and break delivery. Automated prompts in English; replies may be
  Persian.
- **Agent job for a script's job.** Paying LLM tokens for `df -h | mail` is waste — use
  `no_agent` scripts for deterministic checks.
- **Empty stdout mystery.** Script job "didn't deliver"? It ran fine and stdout was empty
  — silence is the designed behavior. Print something on every path, including "all clear".
- **Forgetting the target.** A job with no deliver target saves output locally only.
  Verify the target exists: `hermes send --list`.
- **Testing in production.** New jobs fire for the first time at their real schedule.
  Use `hermes cron tick` (or `cron run`) to prove the pipeline before the first real fire.
- **Unacknowledged incidents.** Failures stay listed in `hermes cron incidents` until
  acknowledged; treat it like a pager queue.

## Exercises

Work through `exercises/ex07-cron-scheduled-workflows.md`. Verification: one script-only
job and one agent job live, both tested via tick, incidents view clean, one job edited
without recreate.
