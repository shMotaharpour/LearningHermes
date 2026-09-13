# `examples/mcp-notes-server/` — a minimal MCP server

`notes_mcp.py` is a complete MCP stdio server in standard-library Python. No SDK, no
framework — so nothing hides what the protocol actually requires.

```bash
python3 notes_mcp.py --selftest    # drive the whole protocol in-process, no agent needed
```

Then wire it into Hermes:

```bash
hermes mcp add notes --command python3 --args "$PWD/notes_mcp.py"
hermes mcp test notes
hermes tools list | grep notes:
```

Three tools: `note_add`, `note_list`, `note_search`. Notes live in a JSON file
(`NOTES_MCP_STORE`, default `~/.hermes/notes-mcp.json`).

## The transport, in one sentence

An MCP stdio server reads line-delimited JSON-RPC 2.0 from stdin and writes responses to
stdout. That is all. The handshake Hermes performs is `initialize` →
`notifications/initialized` → `tools/list` → `tools/call`.

## Four rules — three of them are how a first server breaks

| Rule | What goes wrong |
|---|---|
| **stdout is the protocol** | One stray `print()` and the client reads your debug line where a JSON-RPC frame should be. Log to stderr. |
| **never reply to a notification** | A message with no `id` is a notification. Answer it and you put an extra frame on the wire, which the client reads as the answer to its *next* request. Every later reply is off by one, and the symptom looks like nonsense rather than a protocol error. |
| **declare `capabilities.tools`** | A client may skip `tools/list` entirely when the capability is absent. Omit it and your tools never appear — with no error anywhere. |
| **a tool failure is not a protocol failure** | A tool that cannot do its job returns a normal result with `isError: true`, so the model reads why and recovers. A JSON-RPC error means the *request* was malformed. Confusing the two turns a recoverable situation into a dead connection. |

That last one is Chapter 01's loop lesson in a different costume: errors the model can read
are recoverable; errors that kill the channel are not.

## Tested at two layers

`tests/test_mcp_notes_server.py` runs in-process tests over `handle()` for the protocol
rules and tool behaviour, **and** a subprocess test that speaks real JSON-RPC over a real
pipe. The second layer exists because the three failure modes above — stdout pollution, an
extra frame, a missing capability — are all invisible in-process.

The frame-count assertion is the one worth copying: four messages in, one of them a
notification, means **exactly three frames out**. That single number catches rule 2.
