# Exercise 03 — Context and Memory

## Objective

Make the context window visible and manage it deliberately: measure layers, author project
context, and exercise the memory system end to end.

## Tasks

1. **Baseline measurement.** `hermes prompt-size --json`. Write down each layer's char
   count: system_prompt, skills_index, memory, user_profile, tools.
2. **Platform delta.** Run it again with `--platform telegram`. Where do the counts
   differ, and why?
3. **Author project context.** In any code project you own, create an `AGENTS.md` with:
   what the project is, language/format rules, commands to run tests. Re-open an agent
   session in that directory and verify the agent obeys a rule from the file unprompted.
4. **Memory write observation.** Tell your agent: "Remember that my preferred timezone is
   X." Then check which file changed (`~/.hermes/` under `HERMES_HOME`) and confirm the
   fact survives in a *new* session.
5. **Memory hygiene.** Audit the memory file: delete one stale entry you find. Justify
   why it was stale.
6. **Re-measure.** `hermes prompt-size --json` again — compare memory layer size before
   and after your write + prune.

## Verification checklist

- [ ] You can name all four context files and who writes each.
- [ ] `hermes prompt-size --json` output explained layer by layer in your own words.
- [ ] A project AGENTS.md exists and demonstrably changes agent behavior in that project.
- [ ] One memory write and one memory prune performed; the budget impact measured.
