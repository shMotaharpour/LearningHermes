# Chapter 16 — Capstone: Senior Portfolio

> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck: `python3 scripts/verify_chapters.py`

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
index — it is what "Senior Applied AI Engineer" means in artifacts.

### Where the course's own repo is the worked example

This repository *is* a capstone of its own rules: AGENTS.md contracts, evidence files
under `docs/research/`, validation script + tests, bilingual parity pipeline, and per-
chapter agent skills. Read it as such.

**Evidence:** all prior chapters' evidence files; the capstone adds yours under
`docs/research/capstone/`.

## Verified commands

The capstone uses no new commands — it composes verified ones:

```bash
hermes cron status && hermes cron incidents        # automation health
hermes insights --days 7                           # cost view
hermes monitoring status                           # runtime view
python3 scripts/validate_course.py --root .        # repo QA gate
hermes backup -o ~/capstone-$(date +%F).zip        # disaster recovery
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

## Exercises

The capstone is the exercise — see `exercises/ex16-capstone-senior-portfolio.md` for the
full spec, milestones, and defense checklist.
