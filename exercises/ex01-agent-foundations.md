# Exercise 01 — Agent Foundations

## Objective

Understand the agent loop by writing one and breaking it, then prove that Hermes is an
executing system rather than a chatbot: run the real loop with and without tools, and
locate every configuration surface.

Budget: 1.5–2 hours.

## Tasks

1. **Read the loop before you run one.** Open `examples/agent-loop/miniagent.py`. The whole
   agent is `run()` — about forty lines. Then:

   ```bash
   cd examples/agent-loop
   python3 miniagent.py --demo
   ```

   Watch the trajectory printed to stderr. In your own words, write down the exit condition
   and why `max_steps` has to exist alongside it.

2. **Break it on purpose.** Each of these is a one-line edit to `DEMO_SCRIPT`. Run the demo
   after each and record what the loop did, and what the model would see on its next turn:

   - a tool that does not exist — `"name": "send_email"`
   - arguments that are not valid JSON — `"arguments": "{not json"`
   - a file outside the working directory — `"name": "../../etc/passwd"`
   - no final answer at all, so the model only ever calls tools; run with `--max-steps 3`

   For each: did the run survive, and would the model have enough information to recover?
   Then find the test in `tests/test_agent_loop.py` that pins the behaviour you observed.

3. **Add a tool.** Give `miniagent.py` a fourth tool — a schema and a function.

   ```bash
   python3 -m unittest discover -s ../../tests -k agent_loop
   ```

   The schema tests fail if your schema and your function disagree about argument names.
   Fix it, then explain in one sentence why that class of bug is invisible to the model.

4. **Verify installation.** Run `hermes --version` and `hermes doctor`. Fix anything
   `doctor` flags before continuing.

5. **Map the CLI.** Run `hermes --help`. Pick three subcommands you do not recognize and
   run their `--help` (suggested: `moa`, `egress`, `pause`).

6. **Agent loop, no tools.** `hermes chat -q "Explain what a tool call is in one sentence."`
   No tool executes here — pure generation. In `miniagent.py` terms, this is a run that
   returned on step 1.

7. **Agent loop, with tools.** From any directory with files:
   `hermes chat -q "Count the files in the current directory and report the largest one."`
   Watch the transcript, then map what you saw onto the four numbered steps in the chapter's
   loop diagram. Name the point at which `miniagent.py` would have appended a `role: "tool"`
   message.

8. **Locate the three surfaces.** Run `hermes config path` and `hermes config env-path`.
   Confirm on disk: `config.yaml` (settings), `.env` (secrets), `hermes-agent/` (code).

9. **Check current model.** `hermes config get model` — record provider and model name.

10. **Place Hermes in the tool landscape.** From the comparison table in Chapter 01
    (Concepts → "Hermes vs the peer tools"), pick one coding-agent CLI and one gateway
    agent. In one sentence each, state which family it belongs to and what its docs list as
    its primary surface. Cross-check against
    `docs/research/hermes/tool-landscape-evidence-2026-09-10.txt`.

## Verification checklist

- [ ] `miniagent.py --demo` run, and the exit condition stated in your own words.
- [ ] All four failure modes triggered, with the surviving/recovering answer written down
      for each, and the matching test located.
- [ ] A fourth tool added, schema tests passing, and the schema/function mismatch explained.
- [ ] `hermes doctor` reports no blocking failures.
- [ ] You can describe task 7 in loop terms: model → tool call → result appended → answer.
- [ ] `hermes config get model` output matches the model you expect to be billed for.
- [ ] You know which file you would edit to change a setting (and which one you must never
      put an API key into).
- [ ] You can name the two agent families (coding-agent CLI vs gateway agent) and one
      example of each, with the evidence file that documents the claim.
