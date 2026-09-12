---
name: learninghermes-authoring
description: "Use when authoring or editing LearningHermes course content — chapter contract, evidence rules, parity checks."
---

# LearningHermes Authoring

You are working inside the LearningHermes course repo. Follow AGENTS.md at the repo root.

Contract quick-reference:
1. Chapter = chapters/NN-slug/README.md with exactly five sections:
   Why this matters (job link) / Concepts / Verified commands / Common pitfalls / Exercises.
2. Every Hermes command must be run live first; save raw output to docs/research/hermes/
   and cite the evidence file in the chapter.
3. Every chapter carries a '> **Verified:** YYYY-MM-DD · Hermes Agent vX.Y.Z' header line;
   refresh the date when you re-run the chapter's commands.
4. Every chapter has one exercise file exercises/exNN-<slug>.md (slug = chapter slug) with
   Objective / Tasks / Verification checklist sections.
5. Quoted numbers must come from scripts/job_evidence_stats.py, never hand-tallied; quoted
   job-ad text is verbatim (mark elisions with [...]).
6. Docs index for feature claims: https://hermes-agent.nousresearch.com/docs/llms.txt
7. Validate: python3 scripts/validate_course.py --root .
8. Guards: python3 scripts/job_evidence_stats.py --check, python3 scripts/rebuild_job_ledger.py --check,
   python3 scripts/verify_chapters.py (needs the hermes CLI; read-only).
9. Tests: python3 -m unittest discover -s tests -v (stdlib only).
10. Parity (farsi vs english): python3 scripts/validate_course.py --root . --other <other-checkout>
11. Commits: 'chNN: <description>' (English), branch english = English only,
    branch farsi = Persian prose + English technical terms/code.
