# Exercise 01 — Agent Foundations

## Objective

Prove to yourself that Hermes is an executing system, not a chatbot: install/verify it,
run the agent loop with and without tools, and locate every configuration surface.

## Tasks

1. **Verify installation.** Run `hermes --version` and `hermes doctor`. Fix anything
   `doctor` flags before continuing.
2. **Map the CLI.** Run `hermes --help`. Count the subcommands. Pick three you don't
   recognize and run their `--help` (suggested: `moa`, `egress`, `checkpoints`).
3. **Agent loop, no tools.** `hermes chat -q "Explain what a tool call is in one sentence."`
   Note: no tool executes here — pure generation.
4. **Agent loop, with tools.** From any directory with files:
   `hermes chat -q "Count the files in the current directory and report the largest one."`
   Watch the transcript: the model must call the terminal tool, read output, then answer.
5. **Locate the three surfaces.** Run `hermes config path` and `hermes config env-path`.
   Confirm on disk: `config.yaml` (settings), `.env` (secrets), `hermes-agent/` (code).
6. **Check current model.** `hermes config get model` — record provider and model name.
7. **Place Hermes in the tool landscape.** From the comparison table in Chapter 01
   (Concepts → "Hermes vs the peer tools"), pick one coding-agent CLI and one gateway
   agent. In one sentence each, state which family it belongs to and what its docs list
   as its primary surface. Cross-check your sentence against
   `docs/research/hermes/tool-landscape-evidence-2026-09-10.txt`.

## Verification checklist

- [ ] `hermes doctor` reports no blocking failures.
- [ ] You can state what happened in task 4 in loop terms: model → tool call → result → answer.
- [ ] `hermes config get model` output matches the model you expect to be billed for.
- [ ] You know which file you would edit to change a setting (and which one you must never
      put an API key into).
- [ ] You can name the two agent families (coding-agent CLI vs gateway agent) and one
      example of each, with the evidence file that documents the claim.
