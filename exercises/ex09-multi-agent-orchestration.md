# Exercise 09 — Multi-Agent Orchestration

## Objective

Run the ladder end to end: parallel subagents, one kanban task lifecycle, a peer (or
documented cross-machine plan), and worktree hygiene.

## Tasks

1. **Parallel delegation.** In one session, ask the agent to research three independent
   topics in parallel ("delegate three subagents, one per topic, then merge"). Observe:
   you should see one merged result, not three interleaved transcripts.
2. **Subagent verification discipline.** In the same run, ask one subagent to "write a
   file" — then verify the file yourself on disk. Note the verify-before-trust habit.
3. **Kanban lifecycle.** `hermes kanban init`; create two tasks with a parent→child
   `link`; `claim` the parent in one profile; `complete` it; `unblock`/promote the child.
   Screenshot-free proof: `hermes kanban show <id>` output for both.
4. **Queue hygiene.** `hermes kanban stats` and `hermes kanban diagnostics` — record the
   health view.
5. **Peers.** If you have a second machine/host: `hermes peer add` + `hermes peer dm`
   round-trip. If not: write the exact commands you would run and where the key goes
   (`.env`).
6. **Worktree hygiene.** `hermes worktree audit` — record findings; `prune` if anything
   is reclaimable. Verify nothing uncommitted was touched.

## Verification checklist

- [ ] One merged result from a genuine 3-way parallel delegation.
- [ ] Subagent's file write verified on disk by you, not by the subagent's claim.
- [ ] Kanban parent/child dependency drove execution order.
- [ ] Peer round-trip completed (or command plan written).
- [ ] Worktree audit run; prune left committed work intact.
