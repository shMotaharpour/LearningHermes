# Chapter 14b authoring rules

Scope for this chapter is defined in CURRICULUM.md (Part mapping table).
- Verify every Hermes command live before writing it here; append raw output to
  docs/research/hermes/ and cite the file in README.md.
- Keep the five required sections in order; do not add extra top-level sections.
- Exercises for this chapter live at exercises/ex14b-observability-feedback.md.
- The split from chapter 14 is deliberate: 14 is OFFLINE evaluation (a frozen set, run
  before shipping), 14b is the running system and the loop back into 14. Keep judge and
  rubric material in 14; keep alerting, cost review and incident-to-task material here.
- This chapter ships runnable code in examples/observability/. Any claim about how the
  analyzer behaves must be covered by tests/test_observability.py, not asserted in prose.
