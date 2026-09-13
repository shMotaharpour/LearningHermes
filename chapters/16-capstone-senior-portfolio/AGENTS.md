# Chapter 16 — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Scope boundary

Synthesis and defence. This chapter introduces no new Hermes surface; it composes verified
commands from earlier chapters.

## Ships

`examples/capstone/` — cost model, postmortem template and worked example, system-design
briefs, competency map. Pinned by `tests/test_cost_model.py`.

## Care

Prices in `workflow.json` are placeholders and must stay visibly so (angle-bracketed names,
and the tool's warning on every run). A cost model on invented prices is worse than none,
and a test enforces this.
