# Exercise 12 — Plugins and APIs

## Objective

Touch every integration contract once: inspect a plugin, serve the agent over an
OpenAI-compatible API and call it, connect an editor or proxy, embed the loop in Python.

## Tasks

1. **Plugin recon.** `hermes plugins list`; pick one (built-in or installed) and run
   `hermes plugins capabilities` + `hermes plugins doctor` — record what it registers.
2. **API server round-trip.** `hermes serve --port 8377` (localhost). From another
   shell, POST an OpenAI-shaped chat request (curl or python) with `API_SERVER_KEY`;
   get a completion that used a tool. Stop the server after.
3. **ACP or proxy.** Choose one: connect an editor via `hermes acp`, or point an
   OpenAI-SDK CLI (e.g. aider) at `hermes proxy`. Record the working config.
4. **Embedding.** Write `examples/embed-agent.py` following the official python-library
   guide: one programmatic agent call with tools. Run it.
5. **Decision memo.** For a hypothetical product ("support-bot reading our docs"),
   write 5 lines: which extension point (MCP/plugin/API/embed) and why.

## Verification checklist

- [ ] Plugin capabilities + doctor output recorded.
- [ ] API round-trip succeeded with auth, stopped cleanly afterwards.
- [ ] Editor/proxy path produced a working agent-backed session.
- [ ] `examples/embed-agent.py` runs and returns a tool-using result.
- [ ] Decision memo picks one contract and defends it.
