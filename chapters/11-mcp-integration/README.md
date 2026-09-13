# Chapter 11 — MCP Integration

> **Verified:** 2026-09-13 · Hermes Agent v0.21.2 (2026.9.11) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

MCP is now a named requirement in postings: "Senior AI Software Engineer - MCP & Agentic
Systems", "Senior Python MCP Engineer", "Senior Software Developer - MCP and Agentic AI -
Autodesk" (`docs/research/jobs/search-round2.json` — search-result title only, no body
extract). Tool calling got you here; MCP is the standardized tool economy on top of it. Hermes
treats MCP as first-class: client (consume external servers), filter (control which tools
load), and server (`hermes mcp serve` — expose your agent to other agents). This chapter makes
you fluent in all three, which is precisely what those postings screen for.

## Concepts

### The Model Context Protocol

MCP standardizes how an agent discovers and calls external tools: an MCP **server**
exposes tools (and resources); an MCP **client** (your agent) lists and invokes them.
Hermes clients appear as `server:tool` in the tool namespace (verified in `hermes tools
--help`) — e.g. `github:create_issue` — one server, many tools, prompt cost per enabled
tool (Chapter 03's budget lesson applies).

### Client side: add, configure, filter

Verified command tree (evidence b5): `hermes mcp add <name> --url <endpoint>` for remote
servers, `--command <cmd> --args` for local stdio servers, plus `list/test/configure/
login/reauth`. Tool filtering is per-server: enable a server, then disable noisy tools —
`hermes tools disable github:create_issue` style scoping from Chapter 05 works on MCP
tools too.

**`--args` must be the last option on the line.** Its help text says so literally, and the
reason is argparse: `--args` takes the remainder, so everything after it belongs to the
*spawned server process*, not to `hermes mcp add`. That makes
`hermes mcp add notes --command ./notes-mcp --args --port 8321` correct — `--port 8321`
reaches `notes-mcp` — while moving a Hermes flag after it silently hands that flag to the
child instead:

```bash
hermes mcp add notes --command ./notes-mcp --connect-timeout 20 --args --port 8321   # right
hermes mcp add notes --command ./notes-mcp --args --port 8321 --connect-timeout 20   # wrong
```

The second line does not error. It configures a server with the default timeout and passes
`--connect-timeout 20` to `notes-mcp`, which probably does not understand it. Environment
for stdio servers goes through `--env KEY=VALUE` for the same reason — put it before
`--args`.

### The catalog path

`hermes mcp catalog` (verified live) lists Nous-approved one-click servers — airtable,
asana, amplitude, algolia and dozens more — and `hermes mcp install <name>` does discovery
+ auth + config in one step. OAuth-based servers carry login state:
`hermes mcp login/reauth` (verified) refreshes it.

### Server side: your agent as a tool provider

`hermes mcp serve` (verified: "Run Hermes as an MCP server — expose conversations to other
agents") flips the direction: your Hermes instance becomes an MCP endpoint other agents
consume. This is the A2A complement of Chapter 09's peers — standards-based, not
platform-specific.

### Testing discipline

`hermes mcp test <name>` (verified) exercises a connection with synthetic calls. The
debugging ladder when a tool misbehaves: `hermes mcp list` (configured?) →
`hermes mcp test` (reachable?) → `hermes tools list` (enabled?) → the call itself
(arguments right?).

### Writing your own MCP server

Any language with an MCP SDK works — a stdio server is a script speaking JSON-RPC over
stdio; an HTTP server exposes a URL. Hermes doesn't care where it runs; the contract is
the protocol. `examples/mcp-notes-server/notes_mcp.py` is a complete one in
standard-library Python, with no SDK, so nothing hides what the protocol requires:

```bash
cd examples/mcp-notes-server
python3 notes_mcp.py --selftest     # drive the whole protocol in-process, no agent needed
hermes mcp add notes --command python3 --args "$PWD/notes_mcp.py"
hermes mcp test notes
```

**The transport is one sentence:** read line-delimited JSON-RPC 2.0 from stdin, write
responses to stdout. The handshake Hermes performs is `initialize` →
`notifications/initialized` → `tools/list` → `tools/call`, at protocol version
`2025-03-26`.

**Four rules, and three of them are how a first server breaks.**

1. **stdout is the protocol.** One stray `print()` and the client reads your debug line
   where a frame should be. Diagnostics go to stderr. This is the most common first bug and
   it presents as "the server doesn't work" with nothing in any log.
2. **Never reply to a notification.** A message with no `id` is a notification
   (`notifications/initialized` is the one you will meet first). Answer it and you have put
   an extra frame on the wire, which the client reads as the answer to its *next* request —
   so every later reply is off by one. The symptom is nonsense responses, not a protocol
   error, which is what makes it expensive to find.
3. **Declare `capabilities.tools` in the initialize result.** Per the spec a client may
   skip `tools/list` entirely when that capability is absent — Hermes does exactly this, to
   support prompt-only and resource-only servers. Omit it and your tools simply never
   appear, with no error anywhere.
4. **A tool failure is not a protocol failure.** A tool that cannot do its job returns a
   normal result carrying `isError: true` and a readable reason, so the model recovers on
   its next turn. A JSON-RPC error (`-32601`, `-32700`) means the *request* was malformed.
   Confusing the two turns a recoverable situation into a dead connection.

Rule 4 is Chapter 01's loop lesson wearing a different costume: an error the model can read
is recoverable; an error that kills the channel is not. It recurs at every layer of this
course, which is a sign it is the real rule rather than a Hermes convention.

**Test it at two layers.** `tests/test_mcp_notes_server.py` covers the handlers in-process,
*and* runs the server as a subprocess over a real pipe — because stdout pollution, an extra
frame, and a missing capability are all invisible to an in-process test. The assertion
worth copying: four messages in, one a notification, means **exactly three frames out**.
That one number catches rule 2.

Minimum viable server: one tool, JSON-schema'd inputs, deterministic
output. Chapter 12's plugin system is the in-process alternative when you want deeper
integration than tools.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b5-skills-mcp-plugins.txt`
(full `hermes mcp` command tree, live `mcp list` empty-state + `mcp catalog` table with
real entries). The handshake and protocol version quoted above were read from the Hermes
source at v0.21.2 (`tools/mcp_tool_transport.py`, whose `_advertises_tools` documents the
capability rule), not paraphrased; `tests/test_mcp_notes_server.py` pins the server's
behaviour offline, including a real subprocess round-trip.

## Verified commands

Client lifecycle:

```bash
hermes mcp list                          # configured servers (verified empty-state text)
hermes mcp add notes --command ./notes-mcp --args --port 8321   # --args goes last
hermes mcp add github --url https://mcp.github.dev/sse
hermes mcp test notes                    # synthetic connection check
hermes mcp configure notes               # toggle per-tool selection
hermes mcp login github / reauth --all   # OAuth maintenance
hermes mcp remove notes
```

Write and wire your own (`examples/mcp-notes-server/`):

```bash
cd examples/mcp-notes-server
python3 notes_mcp.py --selftest                    # protocol check, no agent needed
hermes mcp add notes --command python3 --args "$PWD/notes_mcp.py"
hermes mcp test notes                              # reachable?
hermes tools list                                  # notes:note_add and friends appear
```

Catalog:

```
$ hermes mcp catalog
  Name        Status      Description
  airtable    available   Bases, tables, and records from your Airtable workspace.
  asana       available   Tasks, projects, and goals from your Asana workspace.
  ...                                  (verified live table)
```

```bash
hermes mcp install airtable              # one-click catalog install
```

Server mode:

```bash
hermes mcp serve                         # expose this agent over MCP
```

Tool filtering (Chapter 05's command, MCP objects):

```bash
hermes tools list                        # MCP tools shown as server:tool
hermes tools disable github:create_issue # scope one tool off
```

## Common pitfalls

- **Enabling every tool a server offers.** Each tool's schema rides in the prompt
  (Chapter 03). Configure to the handful you use.
- **OAuth expiry mysteries.** A tool that "stopped working" after weeks is often a stale
  token: `hermes mcp reauth --all` before debugging code.
- **stdio server env confusion.** Local servers inherit the launch environment — secrets
  belong in `.env` and explicit env config, not interactive shell state. Pass them with
  `--env KEY=VALUE` *before* `--args`.
- **A Hermes flag written after `--args`.** It is consumed by the spawned server, not by
  Hermes, and nothing complains. If a flag you passed appears to have been ignored, check
  its position relative to `--args` first.
- **Printing to stdout in your own server.** It is the wire. The server looks broken and no
  log says why. Everything diagnostic goes to stderr.
- **Replying to `notifications/initialized`.** The extra frame becomes the answer to the
  next request and every reply afterwards is off by one. You will debug your tools for an
  hour before suspecting the handshake.
- **Forgetting `capabilities.tools`.** Hermes may never call `tools/list`, so your tools
  are absent with no error to find.
- **Raising a JSON-RPC error when a tool merely failed.** `isError: true` in the result
  lets the model read the reason and recover; a protocol error kills the channel.
- **Skipping `mcp test`.** A server can be configured and still broken (wrong path, dead
  process). Test is the cheapest check.
- **Confusing MCP with plugins.** MCP = external tools over protocol (cross-language,
  cross-process). Plugins = in-process Hermes extensions with hooks/LLM access (Chapter
  12). Choosing wrong costs a rewrite.

## Exercises

Work through `exercises/ex11-mcp-integration.md`. Verification: one catalog MCP
installed+filtered, one custom stdio MCP server written and called by the agent, OAuth
reauth drill done.

### Senior interview probes

1. Describe the MCP stdio transport precisely enough that someone could implement it. What
   is on the wire, and in what order?
2. Your server's tools never appear in the client, and no error is logged anywhere. Name
   two distinct causes and how you would tell them apart.
3. When does a tool return `isError: true`, and when do you send a JSON-RPC error instead?
   What breaks if you choose wrong?
4. Why must a JSON-RPC notification go unanswered, and what is the *observable symptom*
   when a server answers one?
5. MCP versus an in-process plugin (Chapter 12): give two things each can do that the other
   cannot, and name the decision that should drive the choice.
6. You add an MCP server with 40 tools and your agent gets worse. Explain the mechanism and
   the fix.
7. How would you test an MCP server in CI, with no agent and no network? What would an
   in-process test miss?
8. `hermes mcp serve` turns your agent into a tool provider. What are you exposing, who
   authenticates, and what is the blast radius if the key leaks?
