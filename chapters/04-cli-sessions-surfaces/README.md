# Chapter 04 — CLI, Sessions, and Surfaces

> **Verified:** 2026-09-14 · Hermes Agent v0.21.3 (2026.9.14) · recheck: `python3 scripts/verify_chapters.py`

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

Verified from the live store (evidence b3): each session has a title, workspace, last-active
time, and ID `20260906_231510_f4298797` (UTC date, time, random suffix).
`hermes sessions stats` reports store totals — on this machine at evidence time (2026-09-07):
`21 sessions, 5972 messages, 29.5 MB` with a per-platform split (16 telegram, 2 cli). Your
totals differ — the per-platform split is the part that generalises. The store is FTS5 indexed:
titles and content are searchable.

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

### Reporting an incident: `dump`, `debug share`, `console`

Three commands exist for the moment you need help, and the difference between them is who
sees your machine.

- **`hermes dump`** prints a compact plain-text summary of your setup, meant to be
  copy-pasted into an issue or a support channel. `--show-keys` exists; using it in a
  public thread is how credentials leak.
- **`hermes debug share`** packages system info plus recent logs (`--lines`, default 200)
  and uploads it. Read its defaults carefully, because they encode a real threat model:
  logs are run through secret redaction before upload unless you pass `--no-redact`; the
  public paste service expires (paste.rs after 6 hours, the dpaste.com fallback after
  `--expire` days and **not deletable**); `--nous` uploads privately instead; and without
  `-y` on a non-TTY it **refuses rather than uploading silently**. `--local` prints the
  report instead of uploading — start there, read what you are about to publish, then
  decide.
- **`hermes console`** opens a curated Hermes command REPL. It is deliberately *not* a
  shell and does not expose the full CLI — the right surface to hand someone who needs to
  run a few Hermes commands without a general-purpose terminal.

The habit worth forming: `hermes dump` for "what is my setup", `hermes debug share
--local` to read the bundle, and only then a share — public with redaction on, or `--nous`
when the logs are sensitive at all.

### The general pattern

Three ideas here outlive the CLI they are demonstrated on:

- **A session is an identity, not a window.** The moment the same conversation can be
  resumed from a terminal, a phone and a web page, "most recent" stops being well defined
  and IDs become the only reliable handle. Every multi-surface system rediscovers this,
  usually after an incident.
- **Snapshots before mutation are a different guarantee from version control.** Checkpoints
  cover what the agent changed between two moments; git covers what you intended to change.
  Neither substitutes for the other, and a system that offers one while people assume the
  other is how work gets lost.
- **The transcript and the runtime log answer different questions.** One says what the agent
  decided; the other says what happened to the process. An incident needs both, and a team
  that reads only transcripts will keep concluding the model was at fault.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt`
(live `sessions list` with real IDs, `sessions stats`, checkpoints help, TTY constraint),
`docs/research/hermes/cli-evidence-2026-09-07-b7-multiagent-shipping.txt` (dashboard/backup),
`docs/research/hermes/cli-evidence-2026-09-13-v0.21.2-surface.txt` (`dump`, `debug`,
`console` on v0.21.2).

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

Incident reporting:

```bash
hermes dump                      # compact setup summary for an issue (never --show-keys publicly)
hermes debug share --local       # build the bundle and read it before publishing
hermes debug share --nous -y     # upload privately instead of to a public paste service
hermes console                   # curated Hermes REPL — not a shell
```

## Common pitfalls

- **Sessions are not free.** Unpruned experiment sessions make search noisy and the DB
  grows (29.5 MB was small; heavy users hit GBs). Pin what matters, archive the rest,
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
- **`debug share` straight to a public paste.** Redaction is on by default and is not
  perfect. `--local` first, read it, then publish — or `--nous` if the logs touch anything
  you would not post. A dpaste.com fallback paste cannot be deleted.
- **`hermes dump --show-keys` in a support thread.** It does exactly what it says.

## Exercises

Work through `exercises/ex04-cli-sessions-surfaces.md`. Verification: session resumed by
ID, one checkpoint rollback performed, one export produced, logs read during a real task.

### Senior interview probes

1. The same conversation is reachable from a terminal, a phone and a web dashboard. What is
   the identity of that conversation, and what goes wrong if you address it by "most
   recent"?
2. An agent wrote files you did not want. Walk through the recovery, and say where
   checkpoints stop helping and git starts.
3. A user says "the agent broke". What do you look at first, what second, and why are they
   different artifacts?
4. Why does a full-featured admin dashboard need a deployment conversation before it needs a
   feature conversation?
5. You script something against the agent and it hangs in CI. What is the likely cause?
6. Your session store is 4 GB. What has been happening, what does it cost you, and what is
   your retention policy?
7. You need to share a debug bundle with a vendor. What do you check before uploading it?
8. What is the difference between pinning a session and archiving one, and when does that
   distinction matter operationally?
