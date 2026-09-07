# Chapter 08 — Event-Driven Automation

## Why this matters (job link)

Event-driven integration is the second half of every automation role: Adventus — "API
integrations, and enterprise system orchestration" (`docs/research/jobs/extract-round2.json`);
Paramount embeds AI "directly into the SDLC, leveraging modern platforms" with DevOps and
SRE teams (`docs/research/jobs/source-01.md`). Cron answers *when*; webhooks and hooks
answer *what just happened*. GitHub push → review agent. CI failure → incident summary.
Email arrival → triage. This chapter wires Hermes to events from the outside world (GitHub
and generic webhooks), from its own lifecycle (hooks), and from any script (via
`hermes send`).

## Concepts

### The three event planes

1. **Inbound webhooks** — external services POST to Hermes; a subscription maps the event
   to an agent run. `hermes webhook subscribe|list|test` (verified). GitHub and GitLab
   PR/push/issue events are first-class: the PR-review-agent pattern (fetch diff, review,
   post comments) is a documented blueprint.
2. **Lifecycle hooks** — shell scripts in your config that fire at agent-internal events
   (tool calls, session events) with a JSON payload on stdin. Managed with
   `hermes hooks list|test|doctor|revoke` (verified — includes consent allowlist and
   "exec bit, allowlist, mtime drift, JSON validity" checks). Use for audit logging,
   alerting, custom guardrails.
3. **Outbound notify** — any script, CI job, or daemon can message your platforms with
   `hermes send` (verified exit codes: 0 ok, 1 delivery error, 2 usage error — CI-safe).

### Webhook subscription anatomy

A subscription binds: source/route → filter → prompt/session → deliver target. The agent
run is fresh (no chat history), so the *payload* is the context: prompts must tell the
agent exactly what to do with `{{payload}}` fields. `hermes webhook test` fires a
synthetic POST — use it before pointing a real GitHub repo at your box.

### Hooks: the consent model

Shell hooks execute arbitrary code at agent lifecycle points, so Hermes gates them: each
command needs an allowlist entry (`~/.hermes/shell-hooks-allowlist.json` — verified),
first-use consent is explicit, and `--accept-hooks` auto-approves only unseen hooks when
you decide it's safe. `hermes hooks doctor` is the pre-flight: permissions, allowlist,
drift, JSON validity, timing.

### Blueprints

Hermes ships an automation-blueprints catalog — ready-to-run patterns for scheduled tasks,
GitHub event triggers, API webhooks, multi-skill workflows. Read them as worked examples
of this chapter's three planes composed together.

### Designing event-driven agents

- **Idempotency.** GitHub retries deliveries; a review agent that double-posts on retry
  is a bug. Key your actions on event IDs.
- **Least context.** A webhook run gets no conversation history — payload + prompt is the
  whole world. Reference exact fields; don't "figure it out" at runtime.
- **Fan-out discipline.** One event → one agent run → one deliverable. Chain deeper
  reasoning via delegation (Chapter 09), not by stuffing the prompt.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b4-gateway-cron-events.txt`
(webhook + hooks command trees with full semantics),
`docs/research/hermes/cli-evidence-2026-09-07.txt` (hermes send help + exit codes).

## Verified commands

Inbound webhooks:

```bash
hermes webhook list                 # all dynamic subscriptions
hermes webhook subscribe            # create: route, filter, prompt, target
hermes webhook test <route>         # synthetic POST — verify before real sources
hermes webhook remove <id>
```

Lifecycle hooks:

```bash
hermes hooks list                   # matcher, timeout, consent status
hermes hooks test <event>           # fire against synthetic payload
hermes hooks doctor                 # exec bit, allowlist, mtime drift, JSON, timing
hermes hooks revoke <command>       # remove allowlist entry (restart to apply)
```

Outbound from anywhere (CI example):

```bash
# .github/workflows/deploy.yml — after deploy step:
#   run: hermes send --to telegram "#deploy finished on $GITHUB_REF" || true
hermes send --to telegram "build ok"         # exit 0 = accepted
echo "err" | hermes send --to telegram --subject "[CI]"   # subject header
```

## Common pitfalls

- **Exposing the webhook endpoint raw.** Subscriptions should validate source (secret
  token/path); a public agent trigger is a remote-code-execution-by-prompt vector.
  Chapter 15 completes the hardening.
- **Prompt not payload-aware.** A subscription prompt that ignores the payload produces
  generic answers. Name the fields you expect.
- **Hook scripts without exec bit / stale copies.** `hermes hooks doctor` exists precisely
  because these fail silently — run it after every hook edit.
- **Auto-accepting hooks reflexively.** `--accept-hooks` skips first-use consent — use it
  in CI images you control, never on a machine you don't.
- **Fire-and-forget with no exit-code check.** In CI, treat `hermes send` exit 1 as a
  build warning at minimum; silent notification loss hides incidents.
- **Double-delivery on retry.** Non-idempotent agents + platform retries = duplicate
  comments/messages. Dedup on event ID.

## Exercises

Work through `exercises/ex08-event-driven-automation.md`. Verification: webhook subscribed
+ tested, one hook wired with doctor-clean status, one CI/script notification delivered
with exit-code handling.
