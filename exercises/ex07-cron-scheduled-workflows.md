# Exercise 07 — Cron and Scheduled Workflows

## Objective

Ship two production-grade scheduled jobs — one script-only watchdog, one agent job — and
operate them: test, edit, incident-check.

## Tasks

1. **Scheduler state.** `hermes cron status` and `hermes cron list` — record the active
   jobs, their schedules and deliver targets.
2. **Script-only watchdog.** Write `disk_check.sh`: prints disk usage summary, exits
   silent-on-ok is FORBIDDEN — print "all clear" on the good path too. Create the job
   (`hermes cron create "every 1h" --script ... --deliver <target>`), then
   `hermes cron tick` to fire it now. Confirm delivery.
3. **Agent job.** Create a daily research/briefing agent job: self-contained prompt,
   explicit output format (5 bullets max + links), delivery to your platform. Test with
   `hermes cron run <id>`.
4. **Edit in place.** Change the agent job's schedule via `hermes cron edit` (not
   delete/recreate). Verify with `hermes cron list`.
5. **Failure drill.** Temporarily point a script job at a failing script; run it; find
   the failure in `hermes cron runs` and `hermes cron incidents`; acknowledge it; fix the
   script; re-run.
6. **Notepad.** Write a value to the job notepad (`hermes cron notepad <id> write ...`),
   read it back — this is how jobs remember state across runs.

## Verification checklist

- [ ] Script job delivered output including the "all clear" path.
- [ ] Agent job produced a formatted result to the right target.
- [ ] Schedule edited in place; list reflects it.
- [ ] You located a real failure in runs/incidents and acknowledged it.
- [ ] Notepad round-trip works.
