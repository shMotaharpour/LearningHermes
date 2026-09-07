# Chapter 01 — Agent Foundations

## Why this matters (job link)

Every "Senior Applied AI Engineer" posting assumes you can operate an autonomous agent,
not just chat with a model. Reflection's Forward Deployed Engineer posting: *"Build agentic
systems using state-of-the-art models, orchestrating LLM workflows... deploying reliable
production systems"* (`docs/research/jobs/source-04.md`). 100ms' AI Engineer posting: *"Build,
curate, and maintain agentic workflows"* (`docs/research/jobs/source-05.md`). Before you can
orchestrate agents, you must understand the machine: what an agent loop is, what tools are,
and how Hermes wires model + tools + context into an executing system.

## Concepts

**Agent = LLM + tools + loop.** A chat completion returns text; an agent returns *actions*.
The runtime difference:

1. The model receives a system prompt (identity, rules, tool schemas, context files).
2. The model decides: reply, or call a tool.
3. Hermes executes the tool (real shell, real files, real network), returns the result.
4. The model sees the result and decides again — until it answers without tool calls.

This is the **agent loop**. Everything else in this course hangs off it.

**What Hermes Agent is.** An open-source autonomous coding/task agent by Nous Research.
Terminal-native, runs headless or interactive, and bridges into 21+ messaging platforms via
its gateway. Provider-agnostic: OpenRouter, Anthropic, OpenAI, Google, local models, any
OpenAI-compatible endpoint. Key differentiators you will use throughout this course:

- **Skills** — agent-created procedure documents loaded on demand (Chapter 10).
- **Persistent memory** — survives across sessions (Chapter 03).
- **Gateway** — same agent core on Telegram, Discord, Slack, ... (Chapter 06).

**The three configuration surfaces** (memorize this split; violating it is the #1 beginner error):

| Surface | Path | Holds |
|---|---|---|
| Settings | `~/.hermes/config.yaml` | everything that is NOT a secret |
| Secrets | `~/.hermes/.env` | API keys, tokens only |
| Code | `~/.hermes/hermes-agent/` | the installed program |

**Sessions.** One conversation = one session with its own context, model, and working
directory. Sessions persist in `~/.hermes/state.db` (SQLite) and can be resumed, searched,
exported. Profiles (`~/.hermes/profiles/<name>/`) are fully isolated Hermes instances —
own config, sessions, skills, memory (Chapter 04/09).

**Evidence base for this chapter:** `docs/research/hermes/cli-evidence-2026-09-07.txt` and
`docs/research/hermes/cli-evidence-2026-09-07-b1-foundations-core.txt` (raw CLI outputs,
Hermes v0.20.6).

## Verified commands

Install (Linux/macOS/WSL2):

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Health check and interactive setup (verified output in evidence batch b1):

```bash
hermes doctor        # component-by-component health check
hermes setup         # interactive wizard: provider, keys, platform
hermes status        # component status summary
```

First conversation — three modes:

```bash
hermes                      # interactive chat (default surface)
hermes chat -q "What is 17*23?"   # one-shot query: answers, exits
hermes chat -q "Summarize ~/notes.md" -t web,terminal   # restrict toolsets for the run
```

The `--help` tree is the real feature map (verified `hermes --help`, evidence batch 1 —
66 subcommands incl. `chat, model, moa, fallback, gateway, proxy, cron, webhook, kanban,
skills, plugins, mcp, sessions, insights, monitoring, security, approvals, secrets, egress,
checkpoints, doctor`). Do not memorize it; navigate it:

```bash
hermes --help               # all subcommands
hermes chat --help          # flags for chat mode: -q, -m MODEL, -t TOOLSETS, --resume ...
hermes config --help        # show/get/set/unset/path/check
```

Model selection:

```bash
hermes model                # interactive provider+model picker
hermes config get model     # current default (verified: shows provider + aliases)
```

Version identity:

```bash
hermes --version
# Hermes Agent v0.20.6 (2026.8.27) · upstream 25fcc8ad · local 7d1c9aea
```

## Common pitfalls

- **Secrets in config.yaml.** Keys belong in `~/.hermes/.env` only. `hermes config set`
  is for settings. Mixing them leaks credentials into backups (`hermes backup`).
- **Treating Hermes as a chatbot.** If you only ever use it in a chat window with no tool
  access, you are paying agent costs for chatbot value. The leverage is tool access.
- **Skipping `hermes doctor` after install.** A broken provider key or missing optional
  dependency shows up there, not at first use.
- **One-shot vs interactive confusion.** `hermes chat -q` exits after answering and has no
  slash commands; interactive `hermes` supports `/model`, `/skills`, etc.
- **Piping `hermes tools`** — the interactive tool config UI refuses non-TTY stdin (verified:
  "requires an interactive terminal"). Use `hermes tools list/enable/disable` in scripts.

## Exercises

Work through `exercises/ex01-agent-foundations.md`. Verification: `hermes doctor` clean,
one-shot query answered, `hermes config get model` returns your chosen model.
