# Exercise 11 — MCP Integration

## Objective

Consume, filter, expose: install a catalog MCP, scope its tools, write a minimal custom
MCP server the agent can call, and flip into server mode once.

## Tasks

1. **Catalog install.** `hermes mcp catalog` → pick a server matching something you use
   (or a harmless read-only one); `hermes mcp install <name>`; complete auth if OAuth.
2. **Call it.** In a session, invoke one of its tools through the agent. Record the
   `server:tool` name it used.
3. **Filter.** `hermes tools list` — find the server's tools; disable all but two via
   `hermes tools disable`. Measure prompt-size before/after (`hermes prompt-size`).
4. **Custom server.** Write a 30-line stdio MCP server with one tool (`roll_dice` or
   `now_in_city` — deterministic, no secrets). `hermes mcp add` it, `hermes mcp test`,
   then have the agent call it. Keep the file in `examples/mcp-notes-server/`.
5. **Failure ladder.** Break the custom server (bad path), observe: `mcp list` ok →
   `mcp test` fails → agent call fails. Fix, re-test.
6. **Server mode (read-only).** Run `hermes mcp serve --help`; document (don't leave
   running) how another agent would connect and what `API_SERVER_KEY` protects.

## Verification checklist

- [ ] Catalog server installed, tool called, tools filtered (prompt-size delta recorded).
- [ ] Custom stdio server added, tested, and successfully invoked by the agent.
- [ ] You can walk the four-step debug ladder from memory.
- [ ] Server-mode exposure plan written (who authenticates, what's exposed).
