# Chapter 06 — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Scope boundary

Gateway architecture, platform setup, session routing, and egress via `hermes send`.
Scheduled delivery is 07; webhooks are 08.

## Care

`gateway migrate` examples always show `--dry-run` first — the preflight is the point, and
the command uninstalls units.
