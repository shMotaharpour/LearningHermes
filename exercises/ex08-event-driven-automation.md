# Exercise 08 — Event-Driven Automation

## Objective

Wire all three event planes: an inbound webhook round-trip, one lifecycle hook with a
clean doctor report, and a script/CI notification with proper exit-code handling.

## Tasks

1. **Webhook round-trip.** Subscribe a test route with a payload-aware prompt
   ("summarize the repository and event in the payload"), `hermes webhook test` it, and
   read the agent's answer on the delivery target. Remove the test subscription after.
2. **GitHub pattern (paper).** Read a real PR-review blueprint; sketch the subscription
   you would create for your repo (route, filter, prompt fields, target). Do not connect
   a real repo yet.
3. **Lifecycle hook.** Write `audit_hook.sh` (appends event name + timestamp to a log),
   declare it in config for a tool event, run `hermes hooks doctor` until clean, then
   trigger it and show the appended line. Revoke afterwards if you don't want it live.
4. **Outbound from CI/script.** Add to any script:
   `hermes send --to <target> --subject "[ops]" "task done"`; capture `$?` and branch on
   it (echo success vs failure). Run both paths.
5. **Idempotency check.** Re-fire the same webhook test twice; document what the agent
   did twice and how you would dedupe (event ID keying) in the prompt.

## Verification checklist

- [ ] Webhook test produced a payload-aware agent answer on target.
- [ ] `hermes hooks doctor` clean for your hook; log line appended on real trigger.
- [ ] Script notification handled exit codes 0 and 1 distinctly.
- [ ] Idempotency gap identified and a dedupe strategy written down.
