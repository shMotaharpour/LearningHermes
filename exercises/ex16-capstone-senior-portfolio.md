# Exercise 16 — Capstone: Senior Portfolio

## Objective

Deliver a complete, evidence-backed automation of one real workflow — the portfolio piece
that maps to the Senior Applied AI Engineer profile.

## Objective scope

Choose one workflow you will actually keep running (reporting pipeline, repo maintenance,
personal-business process, research digest). It must involve at least: one external system,
one unattended trigger, and one deliverable to humans.

## Tasks

### Milestone 1 — Spec & architecture (week 1)
1. Write the architecture note (one page): workflow diagram, agent topology, failure
   modes + guards, cost model, eval gate. Save as `docs/research/capstone/architecture.md`.

### Milestone 2 — Automation core (weeks 2–3)
2. Build the automation: cron jobs and/or webhook triggers; agent and/or script-only as
   appropriate (Chapters 07–08); delivery targets verified with `hermes send`.
3. Integrate one external system via MCP/plugin/API (Chapters 11–12).

### Milestone 3 — Quality & security (week 4)
4. Build the eval set + regression gate (Chapter 14); wire it into your change process.
5. Complete the security pass: approvals allowlist, secrets inventory, egress decision,
   least-privilege scoping (Chapter 15 exercise applied to this workflow).

### Milestone 4 — Operate & package (weeks 5–6)
6. Run unattended for 14 days: acknowledge incidents, review insights weekly, fix what
   breaks (this is the real test).
7. Package the portfolio: repo README with architecture note, evidence trail
   (`docs/research/capstone/`), the competency-to-evidence mapping table (10 rows from
   CURRICULUM.md), and a 5-minute demo script you can deliver in an interview.

### Defense checklist (the bar)

- [ ] Workflow ran unattended 14 consecutive days; incident log exists with resolutions.
- [ ] External integration live through a documented contract (MCP config or plugin).
- [ ] Eval gate: frozen tasks + baseline + one regression caught or consciously waived.
- [ ] Security artifacts: allowlist with rationale, secrets inventory, egress decision.
- [ ] Cost model: tokens/day measured via insights, within your policy tiers.
- [ ] Competency-to-evidence table: all ten CURRICULUM.md competencies have artifact links.
- [ ] Architecture note readable by a stranger in 5 minutes.
