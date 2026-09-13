# Chapter 01 — Agent Foundations

> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Every "Senior Applied AI Engineer" posting assumes you can *operate* an autonomous agent,
not just chat with a model. Reflection's Forward Deployed Engineer posting: *"Build agentic
systems using state-of-the-art models, orchestrating LLM workflows... deploying reliable
production systems"* (`docs/research/jobs/source-04.md`). 100ms: *"Build, curate, and
maintain agentic workflows... define and implement LLM performance metrics"*
(`docs/research/jobs/source-05.md`). Databricks: *"Build features and run end-to-end
systems"* (`docs/research/jobs/source-02.md`). Before orchestrating agents you must
understand the machine: the agent loop, tools, toolsets, context injection, session state.
Everything in this course — cron, MCP, multi-agent, evals — is a modification of the loop
you learn here.

## Concepts

### The agent loop

A chat completion returns text; an agent returns *actions*. Hermes runs this loop:

1. **Assemble context.** System prompt (identity + rules) + skills index + memory +
   user profile + tool schemas + conversation history. Measure it: `hermes prompt-size`
   (Chapter 03 dissects every layer).
2. **Model turn.** The model either answers or emits tool calls.
3. **Tool execution.** Hermes runs the tool for real — shell commands, file writes, web
   requests — and returns the output to the model.
4. **Repeat until answer.** The model sees each result and decides again. One user message
   can drive dozens of tool calls.

Two properties of this loop matter for everything that follows:

- **Compounding state.** Tool calls mutate real systems (files, repos, servers). Mistakes
  compound exactly like code bugs — hence checkpoints and approvals (Chapters 04, 15).
- **Cost per loop iteration.** Every iteration re-sends context. Long loops on expensive
  models cost real money; prompt caching (Chapter 03) and routing (Chapter 02) exist
  because of this.

### Toolsets, not just tools

Tools ship in groups (toolsets): `terminal`, `web`, `memory`, `browser`, `computer_use`,
platform-specific sets. Per-run selection is a flag:

```bash
hermes chat -q "..." -t terminal,web     # only these toolsets load
```

Fewer toolsets = smaller prompt, fewer distractions, lower cost. `hermes tools list`
(verified) shows every tool and its enabled state; MCP tools appear as `server:tool`
(Chapter 11).

### The three configuration surfaces

Memorize this split; violating it is the #1 beginner error:

| Surface | Path | Holds |
|---|---|---|
| Settings | `~/.hermes/config.yaml` | everything that is NOT a secret |
| Secrets | `~/.hermes/.env` | API keys, tokens only |
| Code | `~/.hermes/hermes-agent/` | the installed program |

Profiles (`~/.hermes/profiles/<name>/`) replicate this layout for isolated instances —
own config, own sessions, own memory (Chapters 04, 09).

### Sessions

One conversation = one session: own context, model, working directory. Sessions persist in
`~/.hermes/state.db` (SQLite + full-text search). A live store inspected for this chapter
(evidence b3): `21 sessions, 5972 messages, 29.5 MB` (2026-09-07 snapshot; your store will
differ) — CLI and Telegram sessions side by side in one store, resumable from any surface.

### What makes Hermes an *applied* platform

Three capabilities separate it from a chat app, and they organize this whole course:

1. **Skills** — agent-created procedure documents, loaded on demand (Chapter 10).
2. **Persistent memory** — identity and facts that survive sessions (Chapter 03).
3. **Gateway** — the same agent core serving 21+ messaging platforms, cron, webhooks
   (Chapters 06–08).

### Hermes vs the peer tools

Before choosing a tool, know the families that exist. Five well-known tools in this space
fall into two families (all quotes from official documentation, verified in
`docs/research/hermes/tool-landscape-evidence-2026-09-10.txt`):

| Tool | Family | Model access | Key point |
|---|---|---|---|
| Claude Code | Coding-agent CLI | Anthropic models; IDE/CLI also take third-party providers | terminal + IDE + desktop + web; GitHub/Slack ecosystem |
| Codex CLI | Coding-agent CLI | OpenAI models (ChatGPT plans) | open source, Rust; terminal-first |
| OpenCode | Coding-agent CLI | any provider (API key) | open source; TUI + desktop + IDE extension |
| Gemini CLI | Coding-agent CLI | Gemini models (Code Assist quotas) | open source; ReAct loop with MCP |
| OpenClaw | Gateway agent | any provider (API key) | self-hosted gateway on 10+ messaging platforms |
| Hermes | Gateway agent | 20+ providers; fallback chains and credential pools | gateway on 21+ platforms + built-in cron/webhooks |

The split between these two families is an architecture decision, not a marketing label:

- **Coding-agent CLIs** (Claude Code, Codex, OpenCode, Gemini CLI) are terminal-first and
  repo-centric: the best fit for code work inside one repository. Their automation story is
  mostly CI/CD integration or scheduled desktop tasks, not a built-in scheduler.
- **Gateway agents** (Hermes, OpenClaw) are a resident process that bridges messaging
  platforms to the agent core; sessions, cron, webhooks, and multi-agent routing are
  first-class citizens. Hermes's difference from OpenClaw is self-improvement depth:
  agent-created skills, persistent memory, and profile export (Chapters 03, 10, 13) versus
  static instruction files the user maintains (like `CLAUDE.md`).

A practical migration note: if a team already invested in Claude Code or Codex,
`hermes import-agent claude-code|codex` (verified, Chapter 13) imports that setup into
Hermes in one command. When a coding agent alone is enough, the simple test is: work
inside one repo → coding-agent CLI; work on the real machine, from messaging, with
scheduled automation → gateway agent.

### The subcommand map

`hermes --help` (verified, evidence batch 1) exposes 60+ subcommands. You do not memorize
them; you navigate by group:

- **Core:** `chat`, `model`, `moa`, `fallback`, `config`, `doctor`, `status`
- **Sessions/data:** `sessions`, `checkpoints`, `backup`, `insights`
- **Automation:** `cron`, `webhook`, `hooks`, `send`, `gateway`
- **Multi-agent:** `kanban`, `peer`, `delegate` (in-session), `profile`
- **Extension:** `skills`, `plugins`, `mcp`, `serve`, `acp`, `proxy`
- **Security:** `security`, `approvals`, `secrets`, `egress`, `auth`

Each group gets its own chapter(s) ahead.

**Evidence for this chapter:** `docs/research/hermes/cli-evidence-2026-09-07.txt`,
`docs/research/hermes/cli-evidence-2026-09-07-b1-foundations-core.txt`,
`docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt` (raw CLI outputs,
Hermes v0.20.6, live store).

## Verified commands

Install (Linux/macOS/WSL2):

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Health check and interactive setup — `hermes doctor` verified rendering a component
health panel (evidence b7):

```bash
hermes doctor        # component-by-component health check
hermes setup         # interactive wizard: provider, keys, platform
hermes status        # component status summary (--all for detail)
```

First conversation — three modes, verified:

```bash
hermes               # interactive chat (default surface)
hermes chat -q "What is 17*23?"    # one-shot: answers, exits — no slash commands
hermes chat -q "Count files here, report the largest" -t terminal
                     # restricted toolset run — watch the tool call happen
```

The `--help` tree (verified excerpt):

```
usage: hermes [-h] [--version] [-z PROMPT] [-m MODEL] [--provider PROVIDER]
              [-t TOOLSETS] [--resume SESSION] [--continue [SESSION_NAME]]
              [--worktree] [--skills SKILLS] [--safe-mode] [--tui] [--cli] ...
{chat,model,moa,fallback,worktree,browser,secrets,egress,migrate,gateway,
 proxy,lsp,setup,send,auth,status,cron,sync,webhook,peer,portal,kanban,
 project,hooks,doctor,security,approvals,backup,checkpoints,import,config,
 skills,plugins,curator,memory,tools,computer-use,mcp,sessions,insights,
 monitoring,dashboard,desktop,logs,prompt-size, ...}
```

Model selection and identity:

```bash
hermes model                # interactive provider+model picker
hermes config get model     # verified live output:
# default: minimax/minimax-m3:free
# provider: openrouter
# aliases: gemini-pro, gemini-flash, vertex-pro, vertex-flash ...
hermes --version
# Hermes Agent v0.20.6 (2026.8.27) · upstream 25fcc8ad · local 7d1c9aea
```

## Common pitfalls

- **Secrets in config.yaml.** Keys belong in `~/.hermes/.env` only. Mixing them leaks
  credentials into `hermes backup` archives and screenshots.
- **Treating Hermes as a chatbot.** Chat-only use pays agent costs for chatbot value.
  The leverage is tool access — always think "which toolset does this task need?"
- **Skipping `hermes doctor` after install.** A broken provider key or missing optional
  dependency surfaces there, not at first real use.
- **One-shot vs interactive confusion.** `hermes chat -q` exits after answering and has
  no slash commands; interactive `hermes` supports `/model`, `/skills`, `/new`.
- **Confusing the tool families.** Comparing Hermes to Claude Code as "which is better" is
  meaningless; they are different families (coding-agent CLI vs gateway agent). The right
  question: is your work repo-centric or machine-and-messaging-centric? The comparison
  table is in Concepts; evidence in
  `docs/research/hermes/tool-landscape-evidence-2026-09-10.txt`.
- **Piping interactive UIs.** Verified: `hermes tools` (config UI) refuses non-TTY stdin —
  "requires an interactive terminal". Scripts use `hermes tools list/enable/disable`.
- **Ignoring `-t` toolset scoping.** Loading every toolset for a trivial question wastes
  prompt budget and invites wrong-tool calls.

## Exercises

Work through `exercises/ex01-agent-foundations.md`. Verification: `hermes doctor` clean,
one tool-using run observed and explained in loop terms, three config surfaces located,
model identity confirmed, and one peer tool from the "Hermes vs the peer tools" table
picked and its family stated in one sentence.
