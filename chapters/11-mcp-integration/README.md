# Chapter 11 — MCP Integration

## Why this matters (job link)

MCP is now a named requirement in postings: "Senior AI Software Engineer - MCP & Agentic
Systems", "Senior Python MCP Engineer", "Senior Software Developer - MCP and Agentic AI —
Autodesk" (`docs/research/jobs/search-round3-mcp-evals.json`). Tool calling got you here;
MCP is the standardized tool economy on top of it. Hermes treats MCP as first-class:
client (consume external servers), filter (control which tools load), and server (`hermes
mcp serve` — expose your agent to other agents). This chapter makes you fluent in all
three, which is precisely what those postings screen for.

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
the protocol. Minimum viable server: one tool, JSON-schema'd inputs, deterministic
output. Chapter 12's plugin system is the in-process alternative when you want deeper
integration than tools.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b5-skills-mcp-plugins.txt`
(full `hermes mcp` command tree, live `mcp list` empty-state + `mcp catalog` table with
real entries).

## Verified commands

Client lifecycle:

```bash
hermes mcp list                          # configured servers (verified empty-state text)
hermes mcp add notes --command ./notes-mcp --args --port 8321
hermes mcp add github --url https://mcp.github.dev/sse
hermes mcp test notes                    # synthetic connection check
hermes mcp configure notes               # toggle per-tool selection
hermes mcp login github / reauth --all   # OAuth maintenance
hermes mcp remove notes
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
  belong in `.env` and explicit env config, not interactive shell state.
- **Skipping `mcp test`.** A server can be configured and still broken (wrong path, dead
  process). Test is the cheapest check.
- **Confusing MCP with plugins.** MCP = external tools over protocol (cross-language,
  cross-process). Plugins = in-process Hermes extensions with hooks/LLM access (Chapter
  12). Choosing wrong costs a rewrite.

## Exercises

Work through `exercises/ex11-mcp-integration.md`. Verification: one catalog MCP
installed+filtered, one custom stdio MCP server written and called by the agent, OAuth
reauth drill done.
