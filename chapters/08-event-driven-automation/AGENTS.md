# Chapter 08 — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Scope boundary

Inbound webhooks, lifecycle hooks, outbound notify. Schedules are 07; the multi-agent
consumers of these events are 09.

## Care

Every webhook example treats the payload as untrusted input. Hook examples show the consent
model rather than assuming `--accept-hooks`.
