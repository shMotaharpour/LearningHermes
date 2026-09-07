# Chapter 12 — Plugins and APIs

## Why this matters (job link)

Platform engineering is the senior tier of applied AI: Reflection expects "deploying
reliable production systems" across hybrid environments (`docs/research/jobs/source-04.md`);
100ms wants engineers who build "the systems, metrics, and feedback loops" around agents
(`docs/research/jobs/source-05.md`). When MCP tools are not enough — when you need hooks
into the agent's lifecycle, its LLM access, or secret handling — Hermes' plugin system is
the in-process extension point. And the API surfaces (`hermes serve`, ACP, `hermes proxy`,
Python library) turn the agent into infrastructure other software consumes. This chapter
covers the four integration contracts an applied engineer needs to know.

## Concepts

### Plugins: in-process extension

A plugin bundles custom tools, lifecycle hooks, data files, and skills — running inside
Hermes, not beside it (vs MCP's cross-process model). Verified management surface (evidence
b5): `hermes plugins install|search|update|remove|list|enable|disable|capabilities|doctor|pack|show`.
Plugin kinds documented in the official guides:

- **Tool plugins** — add tools with full Hermes tool runtime semantics.
- **Secret-source plugins** — pull credentials from Bitwarden/1Password/etc. at startup.
- **Model/memory/browser/search provider plugins** — swap entire backends.
- **Context-engine plugins** — replace the built-in context compressor.

Plugins get scoped LLM access (`ctx.llm`) — structured calls with host-owned auth and a
fail-closed trust gate. Built-ins ship via lifecycle hooks (disk-cleanup and friends).

### API server: agent as OpenAI-compatible endpoint

`hermes serve` (verified: OpenAI-compatible API for any frontend) — point Open WebUI,
custom apps, or any OpenAI-SDK client at your agent; tools still fire. `API_SERVER_KEY`
guards it. This is how you give a product an agent backend without writing agent plumbing.

### ACP: agent inside editors

`hermes acp` (verified: "Start Hermes Agent in ACP mode for editor integration — VS Code,
Zed, JetBrains") — the same agent loop, protocol-bridged into your IDE. Editing with
agent tools, approvals surfacing in-editor.

### hermes proxy: OAuth as an API

`hermes proxy start|status|providers` (verified: "local HTTP server that forwards
OpenAI-compatible requests to an OAuth-authenticated provider") — use a subscription/
OAuth login from third-party CLIs (Codex, Aider, Cline) without exposing API keys.

### Python library embedding

The docs' python-library guide embeds `AIAgent` directly in scripts and apps — the agent
loop as a library call. Choose embedding when you need tight control loops; choose the
API server when any OpenAI client will do; choose MCP when tools should live outside.

### Choosing the right extension point

| Need | Use |
|---|---|
| Add tools, cross-language/cross-process | MCP server (Ch 11) |
| Add tools + hooks + LLM access, in-process | Plugin |
| Any OpenAI client to talk to the agent | `hermes serve` |
| IDE integration | ACP |
| OAuth subscription as OpenAI endpoint | `hermes proxy` |
| Agent inside a Python program | Library embedding |

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b5-skills-mcp-plugins.txt`
(full plugins command tree, serve/acp/proxy help).

## Verified commands

Plugin management:

```bash
hermes plugins list                # installed + status
hermes plugins search <term>       # discover
hermes plugins install <name>      # install
hermes plugins capabilities <name> # what it registers
hermes plugins doctor              # health check
hermes plugins enable|disable <name>
hermes plugins pack <dir>          # package your own
```

API surfaces:

```bash
hermes serve --port 8377           # OpenAI-compatible agent endpoint
hermes serve --status
hermes acp                         # editor bridge (VS Code/Zed/JetBrains)
hermes proxy start|status|providers
```

Programmatic:

```python
# examples/embed-agent.py (see docs/guides/python-library)
from hermes_cli.agent import AIAgent   # import path per official guide
# agent = AIAgent(...); result = agent.run("summarize repo state")
```

## Common pitfalls

- **Plugin when MCP suffices.** In-process code is harder to sandbox and harder to
  share. Default to MCP; plugin for lifecycle/deep-integration needs.
- **Unvetted plugin trust.** Plugins execute in-process with secrets nearby — treat
  third-party plugins like pip packages from strangers: review, then install.
- **Serving without a key.** `hermes serve` without `API_SERVER_KEY` on a reachable
  interface hands your machine's tool access to whoever finds the port.
- **Proxy scope confusion.** The proxy fronts *providers you're logged into*; it is not
  a general LLM gateway. Rate limits and terms of the upstream apply.
- **Editor sessions vs gateway sessions.** ACP runs create sessions like any other
  surface — don't be surprised when `sessions list` shows editor IDs.

## Exercises

Work through `exercises/ex12-plugins-and-apis.md`. Verification: one plugin capability
inspect+doctor, API server round-trip with key, ACP or proxy demo, embedding snippet runs.
