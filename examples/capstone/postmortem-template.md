# Postmortem — <one-line title: what broke, for whom>

> Copy this file. Fill every section. A section you cannot fill is a finding in itself:
> "we do not know" is a legitimate entry and tells the reader where your observability ends.

| | |
|---|---|
| **Date** | YYYY-MM-DD |
| **Duration** | first bad event → resolved |
| **Severity** | SEV1 / SEV2 / SEV3, and why |
| **Author** | |
| **Status** | draft / reviewed / actions tracked |

## What happened

Three sentences, readable by someone who was not there. What the system did, who noticed,
what the impact was. No jargon, no blame, no narrative tension — the reader wants the shape
before the detail.

## Impact

What actually reached a human or a downstream system. Be concrete: "17 briefings were not
delivered between 06:00 Tue and 06:00 Thu; two stakeholders asked where they were." If the
impact was zero, say so — a near miss is still worth a postmortem and is the cheapest kind
to write.

## Timeline

| Time (UTC) | Event | How we knew |
|---|---|---|
| | | |

The third column is the one that earns the postmortem. For every row, say what surfaced it:
an alert, a failed check, a human noticing. Rows where the answer is "a human noticed,
later" are your detection gaps, and they are usually the most valuable output of the whole
exercise.

## Root cause

The mechanism, not the mistake. "The provider returned 429 for six hours and the job had no
fallback chain" is a mechanism. "Someone forgot to configure fallback" is a person, and
people are not fixable.

Keep asking why until you reach something you can change. Stop when the next "why" is about
someone's character rather than a system's behaviour.

## What went right

Real section, not a courtesy. Which guard held? What made this a two-hour incident instead
of a two-day one? You are looking for things to invest more in, and a postmortem that only
lists failures teaches a team that the safeguards do not matter.

## Detection

How long between the first bad event and someone knowing? What would have caught it sooner,
and what would that have cost? "Nothing would have caught this" is an answer, and it means
your next action item is an alert.

## Action items

| # | Action | Owner | Due | Kind |
|---|---|---|---|---|
| 1 | | | | prevent / detect / mitigate |

Every item has an owner and a date, or it is a wish. Label each one:
- **prevent** — this exact cause cannot recur
- **detect** — we find out in minutes, not days
- **mitigate** — it still happens, but it costs less

A postmortem whose items are all "prevent" is usually optimistic. Detection and mitigation
work against causes you have not thought of yet, which is most of them.

## What we are not doing

The items you considered and rejected, with the reason. This is what stops the same
suggestion arriving in three months as if it were new, and it is the section that shows a
reader you made choices rather than a list.
