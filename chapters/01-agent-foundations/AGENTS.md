# Chapter 01 — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Scope boundary

Concepts only, and the map of the rest of the course. Anything that needs configuration
detail belongs to 02; anything about the session store belongs to 04.

## Ships

`examples/agent-loop/miniagent.py` — the loop in ~120 lines, plus `assets/agent-loop.svg`.
Pinned by `tests/test_agent_loop.py`. The transport seam is load-bearing: every failure
branch must stay testable offline, so do not add a code path that requires a live model.
