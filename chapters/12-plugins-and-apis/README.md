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

### Authoring one: the four registration surfaces

Installing plugins is recon. Writing one is the chapter. `examples/plugins/egress-guard/`
is a complete, installable plugin — read it alongside this section.

A plugin is a directory with a `plugin.yaml` manifest and a `register(ctx)` entry point,
dropped into `~/.hermes/plugins/` (user-global) or `./.hermes/plugins/` (project-local).
`register` is called once per process at discovery, and `ctx` is the whole surface:

| Call | Registers | In `egress-guard` |
|---|---|---|
| `ctx.register_hook(name, fn)` | a lifecycle callback | `pre_tool_call` gates outbound calls |
| `ctx.register_tool(...)` | a tool the model can call | `egress_check` |
| `ctx.register_command(...)` | an in-session slash command | `/egress`, `/egress policy` |
| `ctx.register_cli_command(...)` | `hermes <name> ...` | `hermes egress-guard --json` |

That last one is worth noticing: a plugin adds an argparse subtree to the `hermes` CLI at
startup **without touching core**. The rule upstream states plainly — a plugin must never
modify `run_agent.py`, `cli.py`, or `hermes_cli/main.py`; if it needs something the
framework lacks, the *generic* surface widens. That is the discipline that keeps an
extension point from rotting into a pile of special cases.

### `pre_tool_call`: the only hook that is a control

Most hooks observe. `pre_tool_call` runs **before dispatch** and its return value decides
what happens:

```python
{"action": "block",   "message": "..."}                  # veto; message becomes the tool result
{"action": "approve", "message": "...", "rule_key": "..."}  # route to the human approval gate
{"action": "modify",  "args": {...}}                      # shallow-merged into the tool's args
```

First valid `block`/`approve` wins; `modify` directives accumulate and are applied even
when a later hook blocks. A `block` without a message is ignored — the message *is* the
tool result, so there is nothing to hand back without one.

Two properties of the contract matter more than the syntax:

- **Callbacks are signature-inspected.** A callback declaring only the kwargs it wants
  receives only those; a `**kwargs` callback gets the full payload. This is what makes the
  hook contract *additive*: new payload fields cannot break an existing narrow callback.
  Write `**_` anyway.
- **The approval gate is fail-closed.** An `approve` directive whose gate errors, denies,
  or times out is **blocked**. A plugin that flags an action for approval never silently
  executes it because the gate broke.

Contrast `post_tool_call`, which `egress-guard` registers and deliberately leaves empty of
policy: by the time it fires, the bytes have already left. It is for observation. Nothing
you do there is a control.

### Structure: keep the policy out of the runtime

The single most useful structural choice in a plugin is the one `egress-guard` makes:
`policy.py` imports **nothing from Hermes**. Every decision that could be wrong is a pure
function over plain dicts, covered by `tests/test_plugin_egress_guard.py` with no agent, no
network, and no Hermes install. `__init__.py` only translates hook payloads into policy
calls and verdicts back into directives.

Do this in every plugin you write. The runtime surface is the part you cannot test cheaply,
so keep it thin enough that there is nothing in it to test.

Three decisions in that plugin are worth arguing with, because they are the decisions every
policy gate faces:

1. **Order.** Secrets are checked before destination: a credential going to an *allowed*
   host is still a credential leaving.
2. **`host_allowed` matches on a dot boundary.** `example.com` allows `api.example.com` and
   rejects `example.com.evil.tld`. A substring check here is the whole vulnerability.
3. **`rule_key` groups the approval allowlist by destination, not by tool.** Approving
   `web_fetch` once must not approve every host forever — the grain of an allowlist entry
   is a security decision.

And one thing it gets deliberately, instructively wrong: its `EGRESS_TOOLS` map is an
**implicit allowlist**, so a tool Hermes adds tomorrow is ungated until someone adds it.
That is why the plugin is defence in depth and not a boundary — real egress control is
`hermes egress` (Chapter 15), enforced *below* the agent rather than inside it. Knowing
which of your controls can be walked around, and saying so, is the senior part.

### Trust: what you are actually installing

A plugin runs **in-process, with your credentials in reach**, which is why `register_tool`
has an `override=True` that requires operator opt-in
(`plugins.entries.<id>.allow_tool_override: true`) before a plugin may replace a built-in
like `write_file`. Without that gate any enabled plugin could silently substitute a
privileged built-in. Read that as the general rule: **the dangerous capability exists, and
it is gated on an explicit operator decision recorded in config** — not on a plugin's good
manners.

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
from "community index" to "curated catalog"). The `register(ctx)` surface, the
`pre_tool_call` directive shape, and the `AIAgent` arguments used in
`examples/embed-agent.py` were read from the Hermes source at v0.21.2 rather than
paraphrased; `tests/test_plugin_egress_guard.py` pins the plugin's behaviour offline.

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

Author and install one (`examples/plugins/egress-guard/`):

```bash
cp -r examples/plugins/egress-guard ~/.hermes/plugins/
hermes plugins list                        # it appears
hermes plugins capabilities egress-guard   # what it registers — read BEFORE enabling
hermes plugins doctor                      # against the real runtime contracts
hermes plugins validate --json examples/plugins/egress-guard   # the CI gate
hermes egress-guard --json                 # plugin: egress-guard
```

Embed the loop in Python (`examples/embed-agent.py`, run from a Hermes checkout):

```bash
git clone https://github.com/NousResearch/hermes-agent.git && cd hermes-agent
uv sync
uv run python /path/to/LearningHermes/examples/embed-agent.py
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
- **Policy logic inside the hook callback.** It welds your decisions to the runtime and
  makes them untestable. Pure module, thin adapter.
- **A hook that can raise.** A guard that crashes is a guard that is not running, and the
  agent carries on without it. Wrap every callback.
- **Treating `post_tool_call` as a control.** The bytes have already left.
- **A `block` directive with no message.** Hermes ignores it, because the message *is* the
  tool result. Your veto silently does nothing.
- **An implicit tool allowlist.** A gate keyed on a fixed list of tool names fails open the
  day a new tool ships. Know which of your controls degrade silently.
- **`pip install hermes-agent` for embedding.** There is no supported wheel; run from a
  checkout with `uv sync`. A script that assumes otherwise works on your machine only.
- **Serving without a key.** `hermes serve` without `API_SERVER_KEY` on a reachable
  interface hands your machine's tool access to whoever finds the port.
- **Proxy scope confusion.** The proxy fronts *providers you're logged into*; it is not
  a general LLM gateway. Rate limits and terms of the upstream apply.
- **Editor sessions vs gateway sessions.** ACP runs create sessions like any other
  surface — don't be surprised when `sessions list` shows editor IDs.

## Exercises

Work through `exercises/ex12-plugins-and-apis.md`. Verification: a plugin you authored is
installed and observed blocking a real tool call, API server round-trip with key, ACP or
proxy demo, `examples/embed-agent.py` runs.

### Senior interview probes

1. A plugin and an MCP server can both add a tool. Name three things a plugin can do that
   an MCP server cannot, and one thing MCP gives you that a plugin does not.
2. Your `pre_tool_call` hook returns `{"action": "block"}` with no message. What happens,
   and why is that the right behaviour rather than a silent veto?
3. Why is an `approve` directive whose approval gate times out treated as a block? What
   class of bug does that choice prevent?
4. A plugin wants to replace the built-in `write_file` tool. Walk through what has to be
   true for that to work, and explain the design reasoning behind the gate.
5. You are reviewing a third-party plugin before installing it in a team's environment.
   What do you run, in what order, and what would make you say no?
6. Explain why `hermes plugins install --ref <sha>` is not merely a convenience. What is
   the failure mode without it?
7. Your plugin's policy gate has an allowlist of tool names it inspects. What happens when
   the platform adds a new tool, and how would you design around it?
8. When would you embed `AIAgent` in Python instead of putting `hermes serve` behind your
   application? What do you take on by doing so?
