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
3. Every chapter has one exercise file exercises/exNN-<slug>.md.
4. Docs index for feature claims: https://hermes-agent.nousresearch.com/docs/llms.txt
5. Validate: python3 scripts/validate_course.py --root .
6. Parity (farsi vs english): python3 scripts/validate_course.py --root . --other <other-checkout>
7. Commits: 'chNN: <description>' (English), branch english = English only,
   branch farsi = Persian prose + English technical terms/code.
