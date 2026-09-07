# Chapter 09 — Multi-Agent Orchestration

## Why this matters (job link)

Multi-agent work is the 2026 frontier of applied AI postings: 100ms builds "the systems,
metrics, and feedback loops that make agents better over time" (`docs/research/jobs/source-05.md`);
Reflection ships "agentic systems... orchestrating LLM workflows" at enterprise customers
(`docs/research/jobs/source-04.md`). Orchestrating several specialized agents — parallel
research, code review lanes, worker swarms — is the senior-level version of Chapter 01's
loop. Hermes provides the full ladder: in-session subagents, durable multi-profile task
boards, bot rosters, peer gateways, and batch processing.

## Concepts

### The orchestration ladder (weakest to strongest)

1. **Subagents (`delegate_task`)** — isolated child conversations inside your session for
   parallel/reasoning-heavy subtasks; only the final summary returns. Best for work that
   would flood your context (bulk reads, independent research streams).
2. **Kanban multi-agent** — a durable SQLite task board shared across profiles. Tasks are
   claimed atomically, can depend on each other, run in isolated workspaces by named
   profiles (verified `hermes kanban --help`: "Durable SQLite-backed task board... claimed
   atomically"). Includes a swarm builder: `hermes kanban swarm` — parallel workers →
   verifier → synthesizer graph.
3. **Bot mode** — profiles as named bots with own chat/role/model/memory/skills; they run
   routines, share group chats, message each other.
4. **Peers (A2A)** — other Hermes gateways on other machines: `hermes peer add spark
   --url http://spark.lan:8377 --key <KEY>`, then `hermes peer dm spark "disk status?"`
   (verified full help incl. exit codes 0/1/2). Cross-machine agent-to-agent messaging.
5. **Batch processing** — generate agent trajectories at scale: parallel processing with
   checkpointing; the data-generation counterpart of orchestration.

### When *not* to multi-agent

Subagents add coordination cost. Single-session with good tool scoping (Chapter 05) beats
a swarm for small tasks. Escalate when: work is genuinely parallel, subtasks need isolation
from your context, or durability across hours/days is required (kanban, not subagents).

### Isolation mechanics

- **Worktrees:** `hermes -w` runs agents in git worktrees — multiple agents editing one
  repo without stepping on each other; `hermes worktree audit|prune` reclaims the
  accumulation (verified subcommands).
- **Profiles:** `hermes profile create/use/list` (verified) — independent
  config+sessions+skills per profile; kanban workers are named profiles.
- **Projects:** `hermes project create|bind-board` ties directories to boards (verified).

### Kanban as production queue

The verified subcommand list reads like a task-queue spec: `create, assign, claim, block,
schedule, link (parent→child), request-review, promote, archive, reclaim, reassign,
dispatch, daemon, watch, stats, gc, repair`. That last column matters: reclaim (worker
died), block/unblock (dependencies), diagnostics — this is durable orchestration, not a
sticky-note board.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b7-multiagent-shipping.txt`
(full peer help with examples, full kanban command set incl. swarm), plus
`hermes profile --help` and worktree commands in evidence batches 1/b7.

## Verified commands

Subagents (in-session, via the agent's own tools):

```
"Research X, Y, and Z in parallel and give me one combined brief."
# the agent spawns isolated subagents; you see one merged result
```

Kanban:

```bash
hermes kanban init && hermes kanban boards
hermes kanban create --title "Port CLI tests" --board main
hermes kanban link <parent> <child>          # dependency
hermes kanban swarm --spec swarm.md          # workers → verifier → synthesizer
hermes kanban claim                          # atomic claim (prints workspace path)
hermes kanban stats / diagnostics            # queue health
hermes kanban daemon / watch / dispatch      # execution modes
```

Peers:

```bash
hermes peer add spark --url http://spark.lan:8377 --key <API_SERVER_KEY>
hermes peer list
hermes peer dm spark/researcher "summarize today's CI failures"
```

Profiles & worktrees:

```bash
hermes profile create researcher && hermes profile list
hermes -w                  # worktree mode for repo-editing agents
hermes worktree audit      # find stale worktrees
hermes worktree prune      # reclaim (never deletes uncommitted/unpushed work — verified)
```

## Common pitfalls

- **Subagent for a one-liner.** A single tool call doesn't need delegation; spawn cost
  exceeds the task. Delegate for reasoning-heavy or context-flooding work only.
- **Subagent self-reports as facts.** A child claiming "uploaded successfully" may be
  wrong — verify external side effects yourself before trusting the summary.
- **Kanban without dependencies.** Parallel workers racing into unlinked dependent tasks
  produce merge chaos. Model `link` edges first.
- **Stale worktree cemetery.** Every `-w` run accumulates; audit+prune on a schedule.
- **Peer keys in the wrong file.** Peer credentials are `.env` material (verified: "stored
  locally as a credential in ~/.hermes/.env"), not config.yaml, not shell history.
- **Assuming shared memory.** Subagents, profiles, and peers share *nothing* by default —
  pass all needed context explicitly in the task/prompt.

## Exercises

Work through `exercises/ex09-multi-agent-orchestration.md`. Verification: a 3-way parallel
delegation observed, one kanban task driven through claim→complete, one peer round-trip
(or documented plan), worktree hygiene done.
