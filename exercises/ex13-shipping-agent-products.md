# Exercise 13 — Shipping Agent Products

## Objective

Ship one complete agent-driven change (repo → PR), package a profile distribution, wire
a CI notification, and write a deployment checklist for a real automation.

## Tasks

1. **Agent-authored change.** In a scratch repo (or this one, on a branch): have the
   agent implement a small feature/change per the repo's AGENTS.md conventions, commit
   with the right convention, and open a PR (`gh pr create`). You review the PR like a
   human reviewer.
2. **Backend choice.** Re-run a Chapter 05 scratch task with a Docker backend (if
   available) — record what differed in risk posture.
3. **Distribution.** `hermes profile export` your setup; inspect the archive contents
   (is memory/sessions in there? should it be?); install it into a scratch
   `$HERMES_HOME` if feasible; otherwise document the install command for a teammate.
4. **CI wiring.** Add `hermes send ... || true` to one script/workflow of yours and
   trigger it; confirm delivery.
5. **Checklist.** Write the Chapter 13 deployment checklist for your Chapter 07 cron job
   (scope, fallback, target, approvals, observability, rollback) — six lines, each
   pointing at the command that proves it.

## Verification checklist

- [ ] PR opened by the agent, reviewed by you, merged or rejected with reasons.
- [ ] Profile export inspected and sanitized (or consciously justified).
- [ ] CI/script notification delivered with exit-code tolerance.
- [ ] Six-line deployment checklist written, each line backed by a verification command.
