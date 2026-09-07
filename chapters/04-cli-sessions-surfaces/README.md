# Chapter 04 — CLI, Sessions, and Surfaces

## Why this matters (job link)

"Developer productivity" and "incident handling" are the quiet differentiators in senior
postings: True Zero expects engineers who "maintain technical documentation covering
architecture... deployment" across the whole lifecycle (`docs/research/jobs/source-03.md`);
Reflection's FDE role owns delivery "from initial customer discovery through production
launch" (`docs/research/jobs/source-04.md`). An applied AI engineer's daily loop is: run
work, inspect what happened, resume where it broke, recover when needed. Hermes gives every
session an identity, a transcript, and a safety net (checkpoints). This chapter makes you
fast and safe across all five surfaces: CLI, TUI, desktop, dashboard, gateway platforms.

## Concepts

### One agent, five surfaces

The same core runs as:

| Surface | Launch | Best for |
|---|---|---|
| Interactive CLI | `hermes` | daily work, scripting, automation |
| Ink TUI | `hermes --tui` | long-running visible sessions, widgets, mouse |
| Desktop app | `hermes desktop` | drag-drop files, side-by-side previews, voice |
| Web dashboard | `hermes dashboard` | admin: channels, MCP, cron, memory, logs |
| Gateway platforms | Chapter 06 | Telegram/Discord/Slack... — chat-as-interface |

Sessions are shared infrastructure: a Telegram conversation and a terminal session land in
the same SQLite store (`~/.hermes/state.db`) and resume from any surface.

### Session identity and the store

Verified from the live store (evidence b3): each session has a title, workspace,
last-active time, and ID `20260906_231510_f4298797` (UTC date, time, random suffix).
`hermes sessions stats` reports store totals — on this machine: `21 sessions, 5972
messages, 29.5 MB` with a per-platform split (16 telegram, 2 cli). The store is FTS5
indexed: titles and content are searchable.

### Checkpoints — the filesystem safety net

Before `write_file`/`patch`/`terminal` mutate your working directory, Hermes snapshots it
into a **shadow git repo** (verified `hermes checkpoints --help` wording). `/rollback` in
session restores a pre-mistake state; `hermes checkpoints status|prune|clear` manage disk
cost. Semantics to internalize:

- Checkpoints protect against **agent** mutations between snapshots — your own git
  discipline is still mandatory.
- The store grows with activity; `prune` is routine hygiene, `clear` destroys all
  rollback history (verified help: "Delete the entire checkpoint base (all /rollback
  history)") — treat `clear` as a last resort.

### Slash commands — the in-session control plane

`/model`, `/new`, `/compact`, `/skills`, `/heartbeat`, `/rollback`, `/export`... work on
every chat surface including Telegram topics. They are the agent's REPL: model switches,
context forcing, skill loading without leaving the conversation. The full reference lives
in the official docs slash-commands page; the five above cover 80% of daily use.

### Resume semantics

`hermes --continue` resumes the most recent session; `hermes --resume <ID>` resumes by
exact ID. On multi-platform setups, "most recent" is whichever session — CLI or any
Telegram topic — wrote last. For anything that matters, resume by ID.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt`
(live `sessions list` with real IDs, `sessions stats`, checkpoints help, TTY constraint),
`docs/research/hermes/cli-evidence-2026-09-07-b7-multiagent-shipping.txt` (dashboard/backup).

## Verified commands

Session lifecycle:

```bash
hermes sessions list                 # recent sessions, titles, IDs
hermes sessions stats                # totals + per-platform split + DB size
hermes sessions browse               # interactive picker: search, read, resume
hermes --resume 20260906_231510_f4298797    # resume by ID
hermes --continue                            # resume most recent
hermes sessions rename 20260906_231510_f4298797 "Q3 eval work"   # curated titles
hermes sessions pin <id> / unpin / pinned      # exempt keepers from auto-archive
hermes sessions export               # JSONL / Markdown / QMD export
hermes sessions archive              # soft-hide matching sessions, no deletion
hermes sessions prune --older-than 30d         # hard hygiene (check --help for filters)
```

Checkpoints:

```bash
hermes checkpoints status    # store size, project count, per-project breakdown
hermes checkpoints prune     # GC stale snapshots
```

Surfaces:

```bash
hermes --tui                 # Ink terminal UI
hermes desktop               # native app (streaming tools, file browser, voice)
hermes dashboard             # web admin panel (config, channels, MCP, cron, logs)
hermes dashboard --status    # serving or not
```

Housekeeping:

```bash
hermes backup -o ~/hermes-backup.zip    # full config+skills+sessions zip (verified help)
hermes logs -n 100                       # tail agent.log / errors.log
hermes logs --level error --since 1h     # filtered incident view
```

## Common pitfalls

- **Sessions are not free.** Unpruned experiment sessions make search noisy and the DB
  grows (29.5 MB here is small; heavy users hit GBs). Pin what matters, archive the rest,
  prune on a schedule (Chapter 07 automates it).
- **Rollback is not git.** Checkpoints cover agent mutations between snapshots. Your repos
  still need normal git discipline.
- **Interactive-only UIs in scripts.** Verified: `hermes tools` config UI refuses non-TTY
  stdin. Scriptable paths: `hermes tools list|enable|disable`, `hermes sessions browse` for
  humans only.
- **Dashboard exposure.** The dashboard is a full admin panel — bind it to localhost or
  put it behind an auth gate; never casually port-forward.
- **`--continue` ambiguity.** Multi-platform setups make "most recent" non-obvious. IDs
  are cheap; use them.
- **Skipping `hermes logs` during incidents.** The transcript shows what the agent did;
  `hermes logs` shows what the runtime did (gateway, provider errors, tool failures).
  Incidents need both.

## Exercises

Work through `exercises/ex04-cli-sessions-surfaces.md`. Verification: session resumed by
ID, one checkpoint rollback performed, one export produced, logs read during a real task.
