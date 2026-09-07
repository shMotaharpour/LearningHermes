# Chapter 04 — CLI, Sessions, and Surfaces

## Why this matters (job link)

"Developer productivity" and "incident handling" are the quiet differentiators in senior
postings: True Zero wants engineers who "maintain technical documentation covering
architecture... deployment" and operate through the whole lifecycle
(`docs/research/jobs/source-03.md`). An applied AI engineer's daily loop is: run work,
inspect what happened, resume where it broke, recover when needed. Hermes gives every
session an identity, a transcript, and a safety net (checkpoints) — this chapter makes you
fast and safe across all of Hermes' surfaces: CLI, TUI, desktop, dashboard.

## Concepts

**One agent, five surfaces.** The same core runs as: interactive CLI (`hermes`), Ink TUI
(`hermes --tui`), native desktop app (`hermes desktop`), web dashboard
(`hermes dashboard`), and messaging platforms via the gateway (Chapter 06). Sessions are
shared infrastructure — a Telegram conversation and a terminal session both land in the
same SQLite store and can be resumed from any surface.

**Session identity.** Verified from a live store (evidence b3): each session has a title,
workspace, last-active time, and ID like `20260906_231510_f4298797` (date, time, random
suffix). Store stats are one command away: `hermes sessions stats` → sessions, messages,
per-platform split, DB size.

**Checkpoints — the safety net.** Before `write_file`/`patch`/`terminal` mutate your
working directory, Hermes snapshots it into a shadow git repo (verified `hermes
checkpoints --help`: "snapshot working directories before write_file/patch/terminal
calls"). Rollback restores a pre-mistake state. `/rollback` in-session; `hermes
checkpoints status/prune/clear` manages the store's disk cost.

**Slash commands** are the in-session control plane (`/model`, `/skills`, `/new`,
`/compact`, `/heartbeat`, ...). They exist on every chat surface including Telegram. Think
of them as the agent's REPL commands.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt`
(live session list/stats, checkpoints help, TTY constraints).

## Verified commands

Session lifecycle:

```bash
hermes sessions list                 # recent sessions, IDs
hermes sessions stats                # totals: sessions, messages, DB size
hermes sessions browse               # interactive picker -> search + resume
hermes --resume 20260906_231510_f4298797   # resume by ID (or --continue for latest)
hermes sessions export --format markdown       # transcript export for reports
hermes sessions prune --older-than 30d         # storage hygiene (dry-run first)
```

Checkpoints:

```bash
hermes checkpoints status    # store size, per-project breakdown
hermes checkpoints prune     # reclaim space from stale snapshots
```

Surfaces:

```bash
hermes --tui                 # Ink terminal UI (mouse-friendly, widgets)
hermes desktop               # native desktop app (macOS/Windows/Linux)
hermes dashboard             # web admin panel + embedded chat
hermes dashboard --status    # is the dashboard serving?
```

In-session (slash) essentials:

```
/model            # switch model for this session
/new              # fresh session
/compact          # force context compression now
/skills           # load a skill on demand
/heartbeat 10m    # recurring idle prompt (watch-loop)
```

## Common pitfalls

- **Sessions are not free.** Every session is FTS-indexed context; 30 unpruned experiment
  sessions make `browse` and search noisy. Prune on a schedule (Chapter 07 automates this).
- **Rollback is not git.** Checkpoints protect against *agent* mutations between snapshots.
  Your own git discipline remains mandatory; checkpoints complement it, never replace it.
- **Interactive-only commands in scripts.** Verified: `hermes tools` (config UI) refuses
  non-TTY stdin. Scriptable alternatives exist (`hermes tools list/enable/disable`); check
  `--help` before automating.
- **Dashboard exposure.** The dashboard is a full admin panel. Run it on localhost or
  behind a gate; never port-forward it casually.
- **`--continue` ambiguity.** `hermes --continue` picks the most recent session — on a
  multi-platform setup (Telegram topics + CLI), "most recent" may not be the one you mean.
  Resume by explicit ID for anything that matters.

## Exercises

Work through `exercises/ex04-cli-sessions-surfaces.md`. Verification: session resumed by
ID, one checkpoint rollback performed, export produced.
