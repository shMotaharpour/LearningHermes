# Exercise 16 — Capstone: Senior Portfolio

## Objective

Deliver a complete, evidence-backed automation of one real workflow — the portfolio piece
that maps to the Senior Applied AI Engineer profile — and the artifacts you defend it with.

Budget: 30–50 hours over ~6 weeks. The calendar is bounded by a 14-day unattended run, not
by effort.

### Scope

Choose one workflow you will actually keep running (reporting pipeline, repo maintenance,
personal-business process, research digest). It must involve at least: one external system,
one unattended trigger, and one deliverable to humans.

## Tasks

### Milestone 1 — Spec, cost, and design (week 1)

1. **Architecture note.** One page: workflow diagram, agent topology, failure modes +
   guards, cost model, eval gate. Save as `docs/research/capstone/architecture.md`. It has
   to be readable by a stranger in five minutes.

2. **Model the cost before you build it.** Copy `examples/capstone/workflow.json`, replace
   every placeholder price with your provider's published rates, and describe your jobs.

   ```bash
   cd examples/capstone
   python3 cost_model.py --spec my-workflow.json
   python3 cost_model.py --spec my-workflow.json --sensitivity
   ```

   Record the **dominant term** and the top lever. Then answer in two sentences: if the
   budget halved tomorrow, what would you change first, and what would it cost you in
   quality? Save the output as `docs/research/capstone/cost-model.txt`.

3. **System-design practice.** Work through the brief for Part I in
   `examples/capstone/system-design-briefs.md` — forty minutes, on paper, out loud if you
   can find a victim — then score yourself against the rubric. Record your two lowest rows.
   Repeat the matching brief at the end of each Part as you re-read the course.

### Milestone 2 — Automation core (weeks 2–3)

4. **Build the automation.** Cron jobs and/or webhook triggers; agent and/or script-only as
   appropriate (Chapters 07–08). Verify delivery targets with `hermes send`, and route
   failure notices *away* from the success target with `--failure-deliver` — task 8 will
   show you why that matters.

5. **Integrate one external system** via MCP, a plugin, or an API (Chapters 11–12). Write
   down why you chose that contract over the other two.

### Milestone 3 — Quality and security (week 4)

6. **Eval gate.** Build the frozen task set and regression gate (Chapter 14) and wire it
   into your change process. If your workflow retrieves documents, include the retrieval
   metrics from Chapter 03b and at least one answerless question.

7. **Security pass.** Approvals allowlist with rationale, secrets inventory, egress
   decision, least-privilege scoping (Chapter 15 applied to this workflow). Rehearse
   `hermes pause` and write down who may run it and what must be true before `hermes resume`.

### Milestone 4 — Operate and package (weeks 5–6)

8. **Run unattended for 14 days.** Acknowledge incidents, review insights weekly, fix what
   breaks. **Something will break — that is what the 14 days are for.** When it does, write
   the postmortem using `examples/capstone/postmortem-template.md`
   (`postmortem-example.md` shows the shape). Fill the three sections people skip: the
   "how we knew" column, "what went right", and "what we are not doing". Your detection time
   is a number an interviewer will ask for, so measure it honestly.

   If genuinely nothing breaks in 14 days, that is a finding too: write a short note on what
   you would have to do to *make* it break, and whether you would know if it had.

9. **Package the portfolio.** Repo README with the architecture note, the evidence trail
   under `docs/research/capstone/`, and the competency-to-evidence table filled in from
   `examples/capstone/competency-map.md`. Then write the three artifacts that carry the most
   weight:

   - a regression your eval gate caught, and what you did about it;
   - the postmortem, with its detection time;
   - **one risk you deliberately accepted, and why.**

10. **Rehearse the defence.** Five-minute demo script, plus written answers to the eight
    interview probes at the end of Chapter 16. Probe 6 — "what did you deliberately not
    guard against?" — is the one most candidates have no answer to. Have one.

## Verification checklist (the bar)

- [ ] Workflow ran unattended 14 consecutive days; incident log exists with resolutions.
- [ ] External integration live through a documented contract (MCP config, plugin, or API),
      with the choice justified against the alternatives.
- [ ] Eval gate: frozen tasks + baseline + one regression caught or consciously waived.
- [ ] Security artifacts: allowlist with rationale, secrets inventory, egress decision, and
      a rehearsed break-glass procedure naming who may run it.
- [ ] Cost model built **before** the build, with the dominant term and top lever named, and
      a halved-budget answer written down.
- [ ] At least one system-design brief attempted and self-scored, with the two weakest rows
      identified.
- [ ] A postmortem using the template, with a measured detection time and all three
      commonly-skipped sections filled.
- [ ] Competency-to-evidence table: all ten clusters have artifact links, or a named gap.
- [ ] One accepted risk written down with its reasoning.
- [ ] Architecture note readable by a stranger in 5 minutes; demo script rehearsed.
