# Chapter 09 — Multi-Agent Orchestration

> **Verified:** 2026-09-14 · Hermes Agent v0.21.3 (2026.9.14) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Multi-agent work is the 2026 frontier of applied AI postings: 100ms builds "the systems,
metrics, and feedback loops that make those agents better over time"
(`docs/research/jobs/source-05.md`); Reflection ships "agentic systems... orchestrating LLM
workflows" at enterprise customers (`docs/research/jobs/source-04.md`). Orchestrating several
specialized agents — parallel research, code review lanes, worker swarms — is the senior-level
version of Chapter 01's loop. Hermes provides the full ladder: in-session subagents, durable
multi-profile task boards, bot rosters, peer gateways, and batch processing.

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
   v0.21.2 adds an asynchronous mode — `peer run` / `peer status` / `peer stop` — covered
   below.
5. **Batch processing** — generate agent trajectories at scale: parallel processing with
   checkpointing; the data-generation counterpart of orchestration.

### When *not* to multi-agent

Subagents add coordination cost. Single-session with good tool scoping (Chapter 05) beats
a swarm for small tasks. Escalate when: work is genuinely parallel, subtasks need isolation
from your context, or durability across hours/days is required (kanban, not subagents).

### Synchronous vs asynchronous peer calls

`hermes peer dm` is a **blocking** call: it sends a message and waits for the reply. That
is the right shape for "disk status?" and the wrong shape for "refactor this package" — a
turn that runs for ten minutes holds your terminal open and dies with the connection.

v0.21.2 splits the long case out:

```bash
hermes peer run spark --idempotency-key ticket-123 < long-task.txt   # -> run ID, returns now
hermes peer status spark run_abc123                                  # status + final output
hermes peer stop spark run_abc123                                    # stop this run only
```

Three details carry the design:

- **`peer run` returns a run ID immediately.** The turn continues on the peer. You poll
  with `peer status`, which returns both the status and the final output when it is done.
  This is the pattern CI wants: start the work, do something else, collect it later.
- **`--idempotency-key` is a stable retry key.** Retrying `peer run` with the same key does
  not start a second turn — it rejoins the first. Without it a key is generated per call,
  so a retried CI step launches duplicate work. Key it off something stable and meaningful
  (a ticket id, a commit SHA), never a timestamp.
- **`peer stop` stops one run** without affecting another turn on the same peer. It is a
  scalpel, unlike `hermes pause` (Chapter 07), which is the peer host's global stop.

`--json` on all three makes them scriptable; the target grammar is `<peer>` or
`<peer>/<agent>` for a named profile on a multiplexed peer (Chapter 06).

**The general pattern.** This is the same split every distributed system eventually makes:
request/response for short work, submit-and-poll with an idempotency key for long work.
Temporal calls it a workflow handle; a job queue calls it a job id. What you should carry
out of this section is not `hermes peer run` but the rule that produced it — *any* remote
call whose duration exceeds a socket's patience needs a durable handle and a dedupe key.

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

### The general pattern, beyond the ladder

The orchestration ladder is a cost argument, not a capability one: **coordination is
overhead you pay for isolation and parallelism, so it has to buy something.** Single-session
with good tool scoping beats a swarm for most work, and being able to say *when* to escalate
is the senior half of the answer.

Three distributed-systems ideas are doing the real work here, and they are the ones worth
being able to discuss platform-agnostically:

- **Atomic claiming.** A durable queue where multiple workers take tasks needs a claim that
  cannot be granted twice, or two agents do the same job and disagree. This is why the board
  is SQLite and not a file — and why `reclaim` exists at all: a worker that dies mid-task
  has to give the task back.
- **Nothing is shared unless you share it.** Subagents, profiles and peers have separate
  memory, separate context, separate state. Every "why didn't the other agent know that?"
  bug is this assumption, and the fix is always an explicit handoff rather than a hope.
- **Long calls need handles, not sockets.** The `peer dm` / `peer run` split is
  request-response versus submit-and-poll, and the idempotency key is what makes the retry
  safe. Temporal calls it a workflow handle; a job queue calls it a job id.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b7-multiagent-shipping.txt`
(full peer help with examples, full kanban command set incl. swarm), plus
`hermes profile --help` and worktree commands in evidence batches 1/b7;
`docs/research/hermes/cli-evidence-2026-09-13-v0.21.2-surface.txt` (`peer`, `peer
run/status/stop` — the asynchronous trio is new since v0.20.6).

## Verified commands

Subagents (in-session, via the agent's own tools):

```
"Research X, Y, and Z in parallel and give me one combined brief."
# the agent spawns isolated subagents; you see one merged result
```

Kanban:

```bash
hermes kanban init && hermes kanban boards list
hermes kanban --board default create "Port CLI tests" --assignee coder
hermes kanban link <parent> <child>          # dependency
hermes kanban swarm "Ship the CLI test suite" \
  --worker coder:"Port CLI tests" --verifier reviewer --synthesizer writer
hermes kanban claim                          # atomic claim (prints workspace path)
hermes kanban stats / diagnostics            # queue health
hermes kanban daemon / watch / dispatch      # execution modes
```

Peers:

```bash
hermes peer add spark --url http://spark.lan:8377 --key <API_SERVER_KEY>
hermes peer list
hermes peer dm spark/researcher "summarize today's CI failures"   # blocking
hermes peer run spark --idempotency-key ticket-123 < long-task.txt  # async: prints a run ID
hermes peer status spark <run-id> --json                            # poll status + output
hermes peer stop spark <run-id>                                     # stop that run only
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
- **Retrying `peer run` without an idempotency key.** The key is generated when omitted, so
  a retried CI step starts a *second* long turn instead of rejoining the first. Key it off
  the ticket or commit, not the clock.
- **Polling `peer status` in a tight loop.** The run is on another machine; poll on the
  order of the work's duration, not the network's.
- **Assuming shared memory.** Subagents, profiles, and peers share *nothing* by default —
  pass all needed context explicitly in the task/prompt.

## Exercises

Work through `exercises/ex09-multi-agent-orchestration.md`. Verification: a 3-way parallel
delegation observed, one kanban task driven through claim→complete, one peer round-trip
(or documented plan), worktree hygiene done.

### Senior interview probes

1. When should work move from one agent to several? Give a test that would tell you it was
   the wrong call.
2. Two workers claim the same task from a shared board. What went wrong, and what does a
   correct claim look like?
3. A worker dies holding a task. What happens next, and who decides?
4. Your subagent produced an answer that contradicts what the parent session knew. Explain
   the mechanism.
5. `peer dm` versus `peer run`: when does the choice matter, and what breaks if you pick the
   blocking one for a ten-minute task?
6. Your CI step retries a peer call. Without an idempotency key, what have you just done?
7. Three agents need to edit one repository. Describe the isolation, and what you check
   afterwards.
8. What is the cheapest way to make a multi-agent system slower and more expensive than a
   single agent? Answer from experience, not theory.
