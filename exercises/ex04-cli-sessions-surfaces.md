# Exercise 04 — CLI, Sessions, and Surfaces

## Objective

Build speed and safety: session resume by ID, checkpoint rollback, transcript export, and
log reading during a real task.

## Tasks

1. **Inventory.** `hermes sessions stats` — record totals and per-platform split. List
   sessions and identify the two you use most.
2. **Curate.** Rename one session to a meaningful title; pin it. Confirm with
   `hermes sessions pinned`.
3. **Resume by ID.** `hermes --resume <ID>` on an old session; ask the agent what the
   session was about to prove context restored. Exit.
4. **Checkpoint safety.** In a scratch directory, ask the agent to create `notes.txt`,
   then modify it destructively, then `/rollback`. Verify file content restored.
5. **Export.** `hermes sessions export` one session to Markdown; open the file.
6. **Logs.** Run any agent task, then `hermes logs -n 50 --since 10m` — find one runtime
   line (gateway/provider/tool) the transcript did *not* show you.
7. **Hygiene.** `hermes checkpoints status` — record store size. If > modest size,
   `hermes checkpoints prune` and re-measure.

## Verification checklist

- [ ] Resumed a session by explicit ID and confirmed restored context.
- [ ] `/rollback` restored a file to its pre-mutation state.
- [ ] Export file exists and contains the full transcript.
- [ ] Found at least one runtime log line invisible in the chat transcript.
- [ ] Checkpoint store size recorded (and pruned if needed).
