# Chapter 12 — Plugins and APIs

> **Verified:** 2026-09-13 · Hermes Agent v0.21.2 (2026.9.11) · recheck: `python3 scripts/verify_chapters.py`

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
Hermes, not beside it (vs MCP's cross-process model). Verified management surface on
v0.21.2: `hermes plugins
install|search|browse|validate|update|remove|list|enable|disable|capabilities|doctor|compat|pack|show`.
Plugin kinds documented in the official guides:

- **Tool plugins** — add tools with full Hermes tool runtime semantics.
- **Secret-source plugins** — pull credentials from Bitwarden/1Password/etc. at startup.
- **Model/memory/browser/search provider plugins** — swap entire backends.
- **Context-engine plugins** — replace the built-in context compressor.

Plugins get scoped LLM access (`ctx.llm`) — structured calls with host-owned auth and a
fail-closed trust gate. Built-ins ship via lifecycle hooks (disk-cleanup and friends).

### The curated catalog, and pinning what you install

Between v0.20.6 and v0.21.2 the discovery surface changed from a community *index* to a
**curated catalog**, and gained the two commands that make installing a plugin an
engineering decision rather than a leap of faith:

- `hermes plugins search <term>` searches the curated catalog by name, description and
  declared tools; `hermes plugins browse` lists every entry. `--json` on search makes it
  scriptable.
- `hermes plugins install <identifier>` takes a bare catalog name, a Git URL, or
  `owner/repo`. Three flags carry the supply-chain story: **`--ref <40-char SHA>` installs
  exactly one immutable commit** — the only form that is reproducible; `--no-enable`
  installs disabled so you can read `capabilities` before anything runs; and
  `--allow-removed` bypasses the catalog's removed-plugin blocklist, which is the flag you
  should never reach for casually — an entry is on that list because it was pulled.
- `hermes plugins validate <path>` is the CI gate for catalog admission, with `--json` for
  a build step. `hermes plugins doctor` checks a plugin against the real runtime contracts.

**The general pattern:** "curated registry + pin by digest + install disabled by default"
is the same answer npm, PyPI and container registries all converged on, for the same
reason. A plugin runs in-process with your secrets in reach; `--ref` is the difference
between a dependency and a moving target.

### Deprecated import paths (`plugins compat`)

`hermes plugins compat` statically scans enabled external plugins for imports of module
paths removed by the September 2026 decomposition and prints `file:line`, old path → new
path, exiting 1 while anything remains. Plugin authors point it at one directory:
`hermes plugins compat ./my-plugin --json`.

The operational fact behind it is worth more than the command: **an affected plugin stops
loading on the removal date**, and the escape hatch
(`plugins.allow_deprecated_imports: true` in `config.yaml`) is a stay of execution, not a
fix. This is the concrete version of a rule that applies to every in-process extension
point you will ever ship against — internal import paths are not an API, and a compat
shim has an expiry date printed on it.

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
(full plugins command tree, serve/acp/proxy help),
`docs/research/hermes/cli-evidence-2026-09-13-v0.21.2-surface.txt` (`plugins`, `plugins
browse/validate/compat` — all three are new since v0.20.6, and `search`/`install` changed
from "community index" to "curated catalog").

## Verified commands

Plugin management:

```bash
hermes plugins list                # installed + status
hermes plugins search <term>       # discover in the curated catalog
hermes plugins browse              # every catalog entry
hermes plugins install <name> --ref <40-char-sha> --no-enable
                                   # pin an immutable commit, install disabled
hermes plugins capabilities <name> # what it registers — read this before enabling
hermes plugins doctor              # health check against the real runtime contracts
hermes plugins enable|disable <name>
hermes plugins validate <dir>      # CI gate for catalog admission (--json)
hermes plugins compat              # enabled plugins importing removed module paths
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
  third-party plugins like pip packages from strangers: review, then install. Concretely:
  `--no-enable`, read `hermes plugins capabilities`, *then* enable.
- **Installing a moving target.** Without `--ref <SHA>`, "the plugin I reviewed" and "the
  plugin that is running" drift apart on the next update. Pin the commit for anything that
  touches secrets or runs unattended.
- **`--allow-removed` as a workaround.** An entry is on the blocklist because it was
  pulled from the catalog. Bypassing that check is a security decision, not a packaging one.
- **Ignoring `plugins compat` until the removal date.** The warning period ends and the
  plugin simply stops loading; `plugins.allow_deprecated_imports: true` buys time and
  nothing else.
- **Serving without a key.** `hermes serve` without `API_SERVER_KEY` on a reachable
  interface hands your machine's tool access to whoever finds the port.
- **Proxy scope confusion.** The proxy fronts *providers you're logged into*; it is not
  a general LLM gateway. Rate limits and terms of the upstream apply.
- **Editor sessions vs gateway sessions.** ACP runs create sessions like any other
  surface — don't be surprised when `sessions list` shows editor IDs.

## Exercises

Work through `exercises/ex12-plugins-and-apis.md`. Verification: one plugin capability
inspect+doctor, API server round-trip with key, ACP or proxy demo, embedding snippet runs.
