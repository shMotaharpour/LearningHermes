# Chapter 07 — Cron and Scheduled Workflows

> **Verified:** 2026-09-14 · Hermes Agent v0.21.3 (2026.9.14) · recheck: `python3 scripts/verify_chapters.py`

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
- `--paused` creates a job **disabled in one write**, so it never fires between creation
  and the moment you are ready. `--paused-reason` records an auditable why. This is how you
  land a job in a review-then-enable workflow instead of racing the scheduler.

### Failure routing is separate from success routing

`--deliver` sets where output goes; `--failure-deliver` (v0.21.2) overrides the target for
**failure notices only**, using the same grammar. Two patterns this unlocks:

- Success to the team channel, failures to the on-call channel — so a broken 6am briefing
  pages the person who can fix it instead of confusing the audience.
- `--failure-deliver local` **suppresses failure notices entirely** while run state stays
  visible in `hermes cron list`. Use it for a noisy, known-flaky job you are already
  watching — never as a default, because it converts a page into something you have to
  remember to look at.

Failure routing is the cheapest reliability feature in the chapter: unattended work that
fails silently is worse than unattended work that never ran.

### Cost and effort per job

`--model` and `--provider` pin a job's inference; `--reasoning-effort` pins its thinking
level (`none` … `ultra`), overriding `agent.reasoning_effort` for that job only. A
disk-watchdog digest does not need the same reasoning budget as a research briefing, and
per-job pinning is where Chapter 02's routing discipline becomes money.

### The global stop

Cron pause is per job. `hermes pause` is the **global emergency stop**: it halts *new* cron
dispatch, kanban dispatch, and new gateway turns until `hermes resume`, and it never kills
in-flight work. `hermes pause --reason "provider outage"` records why. Reach for it when
the blast radius is "everything scheduled", not "this job" — a provider outage, a bad
config rollout, a runaway spend — and treat leaving it engaged as an incident of its own,
because nothing scheduled runs while it is on.

### The general pattern

Strip the command names and this chapter is a scheduler, which means it has the same four
problems every scheduler has — and an interviewer will ask them in exactly these terms:

- **What does a missed window mean?** A job that could not run at 06:00 either runs late,
  runs twice, or is skipped. All three are defensible and they are different products.
  Deciding by default is how you find out at 06:00 on a Monday.
- **At-least-once, and therefore idempotency.** Anything that can retry will eventually run
  twice. A job that appends is not safe to retry; a job that reconciles is.
- **Where does failure go?** Success routing and failure routing are different questions,
  and answering them with one target means the audience learns your job is broken before
  you do. This is the cheapest reliability feature in the chapter and the most commonly
  skipped.
- **What stops everything?** Per-job pausing handles a bad job. A global stop handles a bad
  *day* — a provider outage, a config rollout, a runaway spend — and it is only useful if
  somebody has rehearsed it.

The fifth, which is specific to agents rather than to schedulers: **an unattended prompt has
no reader.** It cannot ask a question, so every branch it can take — including the empty
case — has to be written down in advance.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b4-gateway-cron-events.txt`
(full cron command tree, live job listing with real IDs/schedules/targets, cron status),
`docs/research/hermes/cli-evidence-2026-09-07.txt` (cron help),
`docs/research/hermes/cli-evidence-2026-09-13-v0.21.2-surface.txt` (`cron create`, `pause`,
`resume` on v0.21.2 — `--failure-deliver`, `--reasoning-effort`, `--paused` and
`--paused-reason` are new since v0.20.6).

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
  "Research AI engineering news since yesterday. Summarize the top 5 with links. Output: one bullet per item, title then one sentence then the URL. If nothing is new, say 'no new items'."
```

Note the shape of that prompt: it names the task, the output format, **and** the empty
case. A cron prompt has no reader to fall back on, so every branch it can take has to be
written down.

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

Failure routing, staged creation, and the global stop:

```bash
hermes cron create "0 6 * * *" \
  --name "daily-briefing" \
  --deliver "telegram:-1001:307" \
  --failure-deliver "telegram:-1002" \
  --reasoning-effort low \
  --paused --paused-reason "pending review by ops" \
  "Research AI engineering news since yesterday. Summarize the top 5 with links."

hermes cron resume <job-id>              # enable it once the review passes
hermes pause --reason "provider outage"  # global stop: no new cron/kanban/gateway work
hermes resume                            # lift it; dispatch resumes on the next tick
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
- **Failures delivered to the audience.** Without `--failure-deliver`, a failure notice
  goes wherever the output goes. The stakeholder channel learns your job is broken before
  you do.
- **`--failure-deliver local` as a habit.** It suppresses the notice, not the failure. Used
  by default it turns every unattended job into one nobody is watching.
- **Leaving the global stop engaged.** `hermes pause` silences *everything* scheduled and
  survives restarts. Nothing pages you about it — `hermes status` is where you notice, and
  by then a day of briefings is gone.

## Exercises

Work through `exercises/ex07-cron-scheduled-workflows.md`. Verification: one script-only
job and one agent job live, both tested via tick, incidents view clean, one job edited
without recreate.

### Senior interview probes

1. Your 06:00 job did not run because the machine was asleep until 09:00. Should it run now,
   skip, or run three times? Defend your answer as a product decision.
2. A webhook-triggered job can fire twice for one event. What has to be true about the job
   for that to be safe?
3. Where do failure notices go, and why is "the same place as the output" a bug rather than
   a simplification?
4. When do you reach for a global stop instead of pausing a job, and what has to exist
   before that is a usable control at 3am?
5. A scheduled job runs fine and delivers nothing. Give two causes and how you tell them
   apart.
6. Write the first three sentences of a prompt for an unattended job. What must they
   contain that an interactive prompt need not?
7. When is a script the right answer instead of an agent? Give the test.
8. You need a job to be able to see what it reported yesterday. What are your options and
   what does each cost?
