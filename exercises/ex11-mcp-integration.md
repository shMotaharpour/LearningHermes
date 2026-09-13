# Exercise 11 — MCP Integration

## Objective

Consume, filter, expose, and above all **build**: install a catalog MCP, scope its tools,
write a working stdio MCP server, break it in the three specific ways a first server
breaks, and flip into server mode once.

Budget: 2.5–3 hours.

## Tasks

1. **Catalog install.** `hermes mcp catalog` → pick a server matching something you use (or
   a harmless read-only one); `hermes mcp install <name>`; complete auth if OAuth.

2. **Call it.** In a session, invoke one of its tools through the agent. Record the
   `server:tool` name it used.

3. **Filter, and measure.** `hermes tools list` — find the server's tools and disable all
   but two with `hermes tools disable`. Record `hermes prompt-size` before and after.
   Convert the delta into a per-call cost at your current model's input price; that number
   is the argument for filtering.

4. **Read the server before you write one.** `examples/mcp-notes-server/notes_mcp.py` is a
   complete MCP server in stdlib Python.

   ```bash
   cd examples/mcp-notes-server
   python3 notes_mcp.py --selftest
   ```

   Note which message got **no reply**, and say why that is correct.

5. **Wire it up.**

   ```bash
   hermes mcp add notes --command python3 --args "$PWD/notes_mcp.py"
   hermes mcp test notes
   hermes tools list          # notes:note_add and friends
   ```

   Then have the agent save and search a note through it.

6. **Break it the three ways it actually breaks.** After each, run `hermes mcp test notes`
   and record the symptom *as a user would experience it* — then undo:

   - **stdout pollution:** add `print("hello")` at the top of `serve()`.
   - **answering a notification:** make `handle()` return `ok(None, {})` for a message with
     no `id`.
   - **missing capability:** delete `"tools"` from the `initialize` result's
     `capabilities`.

   For each, answer: what did the failure look like, and would you have guessed the cause?
   The third is the point of the exercise — a silent absence with no error anywhere.

7. **Add a tool.** Give the server a fourth tool (`note_delete`, say) with a schema.
   Run `python3 -m unittest discover -s ../../tests -k mcp_notes`. The schema tests fail if
   your schema and function disagree, or if a `required` argument has a default. Make them
   pass, then call it through the agent.

8. **Failure ladder.** Break the wiring rather than the code — point `hermes mcp add` at a
   path that does not exist — and walk the ladder: `mcp list` (configured?) → `mcp test`
   (reachable?) → `tools list` (enabled?) → the call itself (arguments right?). Write the
   four steps down from memory afterwards.

9. **Server mode (read-only).** Run `hermes mcp serve --help`. Without leaving it running,
   write down: what is exposed, who authenticates, what `API_SERVER_KEY` protects, and what
   an attacker gets if it leaks.

## Verification checklist

- [ ] Catalog server installed, a tool called, tools filtered with a prompt-size delta
      converted into money.
- [ ] `--selftest` run, and the unanswered message explained.
- [ ] `notes_mcp.py` added, `mcp test` passing, and the agent has saved and searched a note.
- [ ] All three failure modes triggered, each with the user-visible symptom written down.
- [ ] A fourth tool added with the schema tests passing, and called through the agent.
- [ ] The four-step debug ladder written from memory.
- [ ] Server-mode exposure plan written: what, who, and the blast radius of a leaked key.
