# Chapter 11 — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Scope boundary

MCP in both directions: consuming servers, and writing one. In-process extension is 12.

## Ships

`examples/mcp-notes-server/notes_mcp.py` — a complete stdio server, no SDK. Pinned by
`tests/test_mcp_notes_server.py`, which tests in-process *and* over a real pipe.

## Care

- No SDK, deliberately: the point is that nothing hides what the protocol requires.
- The subprocess layer is not optional. Stdout pollution, an extra frame, and a missing
  capability are all invisible to an in-process test.
- `hermes egress-guard` and other plugin-registered subcommands carry `# plugin: <name>`.
