# Postmortem — daily briefing silently stopped delivering for 51 hours

> A worked example for Chapter 16. The workflow is a capstone-shaped one: a scheduled agent
> job that researches overnight and delivers a summary to a team channel each morning.
>
> Read it for the shape, especially the sections people leave out — "what went right",
> "detection", and "what we are not doing".

| | |
|---|---|
| **Date** | 2026-08-14 |
| **Duration** | 2026-08-12 06:00 → 2026-08-14 09:12 UTC (51h 12m) |
| **Severity** | SEV2 — a recurring deliverable stopped, no data loss, no customer impact |
| **Author** | (you) |
| **Status** | reviewed; three actions tracked |

## What happened

The 06:00 daily briefing stopped being delivered on Tuesday. The cron job ran on schedule
every morning and failed every morning, and the failure notices went to the same channel as
the briefing itself — where nobody reads an absence. A colleague asked on Thursday morning
whether the briefing had been turned off.

## Impact

Two briefings missed (Tue, Wed). No data loss; nothing downstream depends on the briefing
programmatically. One stakeholder spent about ten minutes looking for Tuesday's before
asking. The real cost is the 51 hours of not knowing, not the two missed messages.

## Timeline

| Time (UTC) | Event | How we knew |
|---|---|---|
| 08-11 17:40 | API key rotated during routine credential hygiene; the new key was added to the pool, the old one left in place and now invalid | — |
| 08-12 06:00 | Job runs, provider returns 401, run recorded as failed | `hermes cron runs` (not looked at) |
| 08-12 06:00 | Failure notice delivered to the briefing channel | nobody read it as a failure |
| 08-13 06:00 | Same again | — |
| 08-14 09:05 | Colleague asks "did we turn the briefing off?" | **a human, 51 hours later** |
| 08-14 09:08 | `hermes cron incidents` shows two unacknowledged failures | — |
| 08-14 09:12 | Invalid credential removed from the pool; `hermes cron run` fires a successful catch-up | — |

## Root cause

Credential rotation added the new key without removing the old one. The pool rotated onto
the dead credential and the provider returned 401. Rotation recovers from rate limits, not
from an invalid credential — a dead key stays in the pool and keeps being selected.

The reason it lasted 51 hours is separate and matters more: **failure notices were routed to
the same target as successful output.** An absence in a channel that normally receives a
message is invisible; a failure delivered to the audience is not a page.

Two causes, two different fixes. A postmortem that names only the first one produces a
system that breaks differently next time and is discovered just as late.

## What went right

- The job's durable run history was intact, so the diagnosis took four minutes once someone
  looked. `hermes cron runs` had recorded every attempt with its error.
- `hermes cron run` produced a catch-up briefing immediately, so recovery was one command.
- Nothing downstream consumed the briefing programmatically, which is why this was a SEV2
  and not a SEV1. That was a design decision made earlier, and it paid.

## Detection

51 hours, and detection was a human asking a question. Nothing in the system was trying to
notice.

The cheapest fix available was already in the tool and unused: routing failure notices away
from the success target. That would have cut detection to one morning. A heartbeat check
("did the briefing arrive?") would have cut it to minutes but requires something to watch
the watcher — worth it for a customer-facing deliverable, not for this one.

## Action items

| # | Action | Owner | Due | Kind |
|---|---|---|---|---|
| 1 | Route failure notices to the on-call channel, not the briefing channel, on every scheduled job | you | 08-15 | detect |
| 2 | Credential rotation runbook: remove the old credential in the same change, and verify the pool afterwards | you | 08-20 | prevent |
| 3 | Weekly review includes unacknowledged incidents, so a silent failure surfaces within 7 days even if item 1 fails | you | 08-22 | detect |

Item 3 exists because item 1 is a single point of failure for detection. Layering a slow
backstop under a fast detector is cheaper than making the fast detector perfect.

## What we are not doing

- **A heartbeat monitor on every scheduled job.** Considered and rejected for now: it
  doubles the number of things that can page us, and for an internal briefing the weekly
  review is sufficient. Revisit if a customer-facing job joins the schedule.
- **Blocking credential rotation behind an approval step.** The rotation was correct
  practice; the bug was leaving the dead key in place. Adding friction to a good habit
  teaches people to skip it.
- **Alerting on any 401 from any provider.** Too noisy — 401s are routine during setup. The
  useful signal is a *scheduled job* failing twice in a row, which item 3 covers.
