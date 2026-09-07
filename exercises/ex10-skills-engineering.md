# Exercise 10 — Skills Engineering

## Objective

Author one original skill from a workflow you have actually repeated, install one
third-party skill with full inspection, and exercise the trust model.

## Tasks

1. **Mine a workflow.** Pick something you've done ≥2 times with Hermes (a report, a
   deploy check, an analysis pipeline). Write `SKILL.md` for it: one-line trigger
   description, numbered verified steps, one linked reference file.
2. **Install it.** Place under `~/.hermes/skills/<name>/` (or the repo's
   `.hermes/skills/` + trust). Verify with `hermes skills list`.
3. **Trigger test.** New session; give the natural-language trigger ("deploy the api
   again") — the agent should load the skill unprompted. If not, sharpen the description.
4. **Registry skill.** `hermes skills search` for something relevant; `hermes skills
   inspect` it; read the body critically; only then `install`. Record what you checked.
5. **Trust drill.** In an untrusted repo containing skills, confirm they don't load; run
   `hermes skills trust`; re-check.
6. **Maintenance.** If you modified any bundled skill: `hermes skills list-modified` +
   `hermes skills diff`. Otherwise run `hermes skills check` and note available updates.

## Verification checklist

- [ ] Your skill loads on its trigger phrase in a fresh session.
- [ ] Description fits the "Use when X. Behavior." pattern in one line.
- [ ] Third-party skill inspected (body read) before install.
- [ ] Trust model demonstrated both ways (blocked, then allowed).
