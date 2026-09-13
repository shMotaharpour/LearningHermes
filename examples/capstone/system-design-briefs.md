# System-design briefs — one per Part

System design is the dominant senior interview format and the course had no practice in it.
These five briefs are deliberately under-specified, the way real ones are: **the first move
is asking what is missing**, and a candidate who starts drawing boxes before establishing
constraints has already shown you something.

Do one at the end of each Part. Forty minutes, on paper, out loud if you can find a victim.
Then score yourself against the rubric at the bottom — honestly, because the rubric is what
the interviewer is filling in.

---

## Brief 1 — after Part I (Foundations)

> A team of eight support engineers answers the same forty questions repeatedly from a
> 200-page internal handbook. Design an agent that answers them. The handbook changes
> weekly. Someone will eventually ask it something the handbook does not cover.

Questions worth asking before you design: who edits the handbook, and how would the agent
know it changed? What happens when the answer is wrong — who finds out? Is a wrong answer
worse than no answer here, and by how much?

The trap: reaching for retrieval before establishing whether 200 pages even needs it.
Chapter 03's argument and Chapter 03b's pipeline are both legitimate answers; picking one
without measuring the context budget is not.

---

## Brief 2 — after Part II (Operating the Agent)

> The same team wants the agent in their group chat. Three people will talk to it at once,
> sometimes in the same thread, sometimes about different customers. One of them is in a
> different timezone and will use it while nobody else is awake.

Questions: what is a session here — per person, per thread, per customer? What does the
agent see of a conversation it was not addressed in? What happens when two people ask
contradictory things in the same thread?

The trap: treating "add a chat interface" as a delivery problem. It is a state problem.

---

## Brief 3 — after Part III (Automation Engineering)

> Automate a weekly compliance report: pull from three systems, reconcile them, flag
> discrepancies, deliver to a regulator-facing mailbox every Monday 09:00. It must never
> silently not arrive.

Questions: what does "never silently" cost, and who is paged? What does the job do when one
of the three systems is down at 08:55 — deliver partial, delay, or fail loudly? Is a late
report worse than an incomplete one? (Ask. The answer is domain-specific and it changes the
design.)

The trap: designing the happy path and adding error handling afterwards. Here the failure
behaviour *is* the requirement.

---

## Brief 4 — after Part IV (Building & Extending)

> Your agent needs to act in a third-party system that has no MCP server and a rate-limited
> REST API. Two other teams want the same capability.

Questions: MCP server, plugin, or a plain service the agent calls? Who operates it once
three teams depend on it? How does a rate limit shared across three consumers get allocated,
and what happens to the third team at the cap?

The trap: choosing the integration style by what is quickest to build rather than by who
maintains it. Chapter 11 and Chapter 12 each argue for a different answer; say which and why.

---

## Brief 5 — after Part V (Production Engineering)

> An agent with write access to a production database has been approved to run unattended.
> You are the one who has to say yes. Design what has to be true first.

Questions: what is the worst single action it can take, and what stops it? How do you know
it did something wrong — and how fast? What is the rollback, and has anyone run it? Who can
stop it at 3am, and do they know how?

The trap: answering with a list of controls. The answer is a threat model, the controls that
follow from it, and — the senior part — which risks you are accepting and why.

---

## Rubric

Score yourself 1–5 on each. Below 3 on any row is the thing to practise, not the thing to
explain away.

| | 1 | 3 | 5 |
|---|---|---|---|
| **Constraints first** | started drawing boxes | asked some questions | established scale, failure cost, and who is on the hook before designing |
| **Failure modes** | happy path only | named failures | designed *from* the failure modes; guards are load-bearing, not appended |
| **Trade-offs stated** | asserted a choice | mentioned an alternative | named what the choice costs and who pays it |
| **Cost & latency** | not mentioned | hand-waved | modelled, with the dominant term identified |
| **Observability** | "we'd log it" | named a tool | said how you would know it broke, and how fast |
| **Scope discipline** | designed everything | some prioritisation | named what you would *not* build, and why |
| **Reversibility** | not considered | mentioned rollback | rollback path named and rehearsed |

The rows people lose points on are the last three, and they are the cheapest to fix: decide
in advance that you will always say what you are *not* building, how you would find out it
broke, and how you would undo it.
