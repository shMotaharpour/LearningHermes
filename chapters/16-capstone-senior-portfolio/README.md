# Chapter 16 — Capstone: Senior Portfolio

> **Verified:** 2026-09-14 · Hermes Agent v0.21.3 (2026.9.14) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Everything before this chapter was competency; this one is *evidence*. Senior interviews
run on artifacts: "show me a system you shipped, how you measured it, how you secured it."
The postings this course mined define the bar — Reflection: "own the technical strategy and
delivery of agentic systems from initial customer discovery through production launch"
(`docs/research/jobs/source-04.md`); 100ms: "build the systems, metrics, and feedback loops
that make those agents better over time" (`docs/research/jobs/source-05.md`). The capstone
is your end-to-end answer: a real enterprise workflow automated with Hermes, evaluated,
hardened, and packaged as a portfolio.

## Concepts

### The capstone contract

Pick one real workflow with an actual stake (your team's reporting, a personal business
process, an open-source project's maintenance) and deliver **all six**:

1. **Automation** — scheduled and/or event-driven (cron, webhooks, hooks) — Part III.
2. **Integration** — at least one external system via MCP/plugin/API (Part IV).
3. **Evaluation** — frozen task set + deterministic checks + judge + regression gate (Ch 14).
4. **Security** — threat model, approvals, secrets, egress, least privilege (Ch 15).
5. **Observability** — logs/insights/monitoring wired; incidents acknowledged (Ch 14).
6. **Portfolio packaging** — repo, README, architecture note, evidence trail (this file's
   exercises).

### Architecture note (the interview artifact)

One page: workflow diagram, agent topology (which sessions/profiles/tools), failure modes
and their guards, cost model (tokens/day by tier), and the eval gate for changes. Senior
signal = the guards, not the features.

### Competency-to-evidence mapping

For each of the ten job-market competencies in `CURRICULUM.md`, name your proof: the
commit, the eval result, the incident you handled. The mapping table is the portfolio's
index — it is what "Senior Applied AI Engineer" means in artifacts. Start from
`examples/capstone/competency-map.md`, which carries the ten rows and, for each, **the
interview question that row answers**.

Three rules make a row real:

1. **A commit, a file, or an output — not a claim.** "Built an eval harness" is a claim;
   `evals/compare.py` plus a baseline and a diff that caught a regression is an artifact.
2. **One artifact can serve two rows**, but say how each row uses it.
3. **An empty row is information.** Better to find it now than in the interview.

And three artifacts carry disproportionate weight, because a demo cannot fake them:

- **A regression you caught** — the eval diff and what you did about it. Proof the gate is
  wired into your change process rather than decorating it.
- **An incident you handled** — the postmortem. They will ask for your detection time.
- **A risk you accepted** — something you deliberately did *not* guard against, with the
  reasoning. This is the clearest single signal of seniority in the portfolio, because it
  requires having thought about cost and not only about correctness.

### Modelling cost before the invoice

"How much will this cost to run?" is a senior interview question, and "I'd check
`hermes insights`" is a junior answer to it: insights tells you what you *already spent*, on
a system that *already exists*. A model tells you what a design will cost before you build
it, and — the useful part — which lever moves it.

`examples/capstone/cost_model.py` is that model:

```bash
cd examples/capstone
python3 cost_model.py                    # monthly cost per job, ranked
python3 cost_model.py --sensitivity      # which single change moves the total most
python3 cost_model.py --what-if pr-triage:tier=strong
```

Two things a first cost model leaves out, both of which change the answer by multiples:

- **Caching.** A scheduled job re-sends a nearly identical prompt every run, so most of its
  input is cache-eligible. In the worked spec, turning caching *off* is the single largest
  mover in the whole sensitivity table — larger than any improvement. That is the size of a
  saving you already have and can lose by editing a prompt prefix, with no error attached
  anywhere (Chapter 03).
- **Retries.** A failure is not free; the tokens were spent before it failed.

Read the **ranking**, not the numbers — `workflow.json` ships placeholder prices and the
tool says so loudly, because a cost model built on invented prices is worse than no model:
it produces a confident answer.

Note the script-only job in the worked spec: zero tokens, zero cost, and it is the one that
wakes you at 3am. Not every automation needs a model.

### Writing the postmortem

Your capstone will break during the 14-day run. That is the point of the 14 days, and the
postmortem is the artifact it produces. `examples/capstone/postmortem-template.md` has every
section; `postmortem-example.md` is a worked 51-hour silent failure written out in full.

Three sections carry the value, and they are the three people skip:

- **"How we knew"**, as a column in the timeline. For every event, what surfaced it. Rows
  where the answer is "a human noticed, later" are your detection gaps — usually the most
  valuable output of the whole exercise.
- **"What went right."** Which guard held, and what made this a two-hour incident instead of
  a two-day one? You are looking for what to invest more in. A postmortem that only lists
  failures teaches a team that safeguards do not matter.
- **"What we are not doing."** The items you considered and rejected, with reasons. It stops
  the same suggestion arriving in three months as if it were new, and it shows a reader you
  made choices rather than a list.

Root cause means *mechanism*, not mistake. "The provider returned 401 and the pool kept
selecting a dead credential" is a mechanism. "Someone forgot to remove the old key" is a
person, and people are not fixable. Keep asking why until you reach something you can
change; stop when the next why is about someone's character.

### Practising the format you will actually be tested in

Senior loops are system design, then code. This course builds the code; the design practice
is `examples/capstone/system-design-briefs.md` — five briefs, one per Part, each
deliberately under-specified, because **the first move is asking what is missing.** A
candidate who starts drawing boxes before establishing constraints has already answered a
question that was not asked.

Do one at the end of each Part, forty minutes, out loud if you can find a victim, then score
yourself against the rubric. The rows people lose on are the last three — cost and latency,
observability, and reversibility — and they are the cheapest to fix: decide in advance that
you will always say what you are *not* building, how you would find out it broke, and how
you would undo it.

### The general pattern

The capstone is Hermes-shaped; what it demonstrates is not, and that distinction is the
whole point of packaging it. An interviewer is checking four things, none of which name a
vendor:

- **Did you ship something that runs without you?** Unattended operation is the claim that
  cannot be faked, which is why the 14 days are the gate rather than the feature list.
- **Do you know whether it works?** A gate wired into your change process, not a test suite
  you ran once.
- **Do you know what it costs, and where?** Not the total — the dominant term, and which
  lever moves it.
- **Do you know what you chose not to do?** Accepted risks, rejected alternatives, scope you
  cut. This is the one that separates having built a system from having run one.

Describe your capstone to someone who has never heard of Hermes. If the description survives
with the product names removed, you have built the portfolio piece. If it does not, you have
built a demo of somebody's CLI.

### Where the course's own repo is the worked example

This repository *is* a capstone of its own rules: AGENTS.md contracts, evidence files
under `docs/research/`, validation script + tests, bilingual parity pipeline, and per-
chapter agent skills. Read it as such.

**Evidence:** all prior chapters' evidence files; the capstone adds yours under
`docs/research/capstone/`. The cost model's behaviour is pinned by
`tests/test_cost_model.py`; its *prices* are placeholders by construction and the tool says
so on every run.

## Verified commands

The capstone uses no new commands — it composes verified ones:

```bash
hermes cron status && hermes cron incidents        # automation health
hermes insights --days 7                           # cost view
hermes monitoring status                           # runtime view
python3 scripts/validate_course.py --root .        # repo QA gate
hermes backup -o ~/capstone-$(date +%F).zip        # disaster recovery
```

Plus the kit in `examples/capstone/` (standard library only, no `hermes` required):

```bash
cd examples/capstone
python3 cost_model.py --sensitivity      # which lever actually moves your bill
python3 cost_model.py --what-if daily-briefing:tier=cheap
```

## Common pitfalls

- **Demo-ware.** A workflow that only runs when you babysit it is a demo. The cron/
  webhook layer must run unattended for two weeks before you call it done.
- **Eval theater.** Five frozen tasks you never re-run is decoration. Wire the regression
  gate into the change process (Ch 14 exercise).
- **Security as an afterthought.** Retrofitting approvals/egress after an incident is
  visible in interviews. Build it in from day one of the capstone.
- **Portfolio without evidence.** Screenshots of chats are not evidence; commands, raw
  outputs, eval diffs, and incident postmortems are.
- **Scope explosion.** One workflow done completely beats three half-built. Cut scope,
  not the six deliverables.
- **"I'd check insights" as a cost answer.** That is what you already spent on a system that
  already exists. Model the design, and know the dominant term.
- **A cost model on invented prices.** Worse than none: it produces a confident number.
  Replace the placeholders with your provider's published rates.
- **A postmortem with no detection section.** The interesting number is not what broke, it
  is how long you did not know.
- **Action items that are all "prevent".** Detection and mitigation work against causes you
  have not thought of, which is most of them.
- **Practising code and not system design.** The loop tests both, and the design round is
  the one this course would otherwise leave you unprepared for.
- **No accepted risks.** A portfolio where everything is guarded reads as someone who has
  not had to choose. Name one thing you left unguarded, and why.

## Exercises

The capstone is the exercise — see `exercises/ex16-capstone-senior-portfolio.md` for the
full spec, milestones, and defense checklist.

### Senior interview probes

The whole course's probes converge here. These are the ones that are specifically about
having *shipped* something rather than having learned it:

1. Walk me through your architecture in five minutes. Start with what it does for whom, not
   with the components.
2. What does it cost to run, and what is the dominant term? What would you change first if
   the budget halved?
3. Tell me about something it got wrong in production. How long before you knew?
4. What is the worst single action your agent can take, and what stops it?
5. Show me a change you made that your eval gate rejected. What did you do?
6. What did you deliberately not guard against, and why was that the right call?
7. Someone joins your team tomorrow and has to operate this. What do they need that does not
   exist yet?
8. If you rebuilt it today, what would you do differently — and what would you keep exactly
   as it is?

Probe 6 is the one most candidates have no answer to, and it is the one that most reliably
separates people who have run a system from people who have built one.
