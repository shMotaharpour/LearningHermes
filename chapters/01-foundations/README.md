# Chapter 1 — Foundations

## What is Hermes Agent?

Hermes is an autonomous AI agent with full tool access (terminal, files, web) that runs in your terminal and 21+ messaging platforms. Unlike chat-only assistants, it executes real work: runs commands, edits files, ships products.

Core concepts:

- **Main model** — the model the agent thinks with (set via `hermes model` or `/model`).
- **Auxiliary models** — small models for side-jobs (compression, vision, titles).
- **Session** — one conversation with its own context and model.
- **config.yaml** — all settings (no secrets). Lives in `~/.hermes/`.
- **.env** — API keys and secrets only.

## Install / Health Check

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes doctor        # full health check
hermes setup         # interactive wizard (providers, keys, platform)
```

## First Commands

```bash
hermes               # interactive chat
hermes chat -q "..." # one-shot query, exits after answering
hermes model         # pick provider + model
hermes config get model   # inspect current model config
```

## Switching Models

```bash
# In chat (Telegram or CLI):
/model                       # interactive picker, fuzzy-filter by typing
/model <name>                # session-only switch
/model <name> --global       # persist to config.yaml
/model --refresh             # re-fetch provider model list (e.g. OpenRouter)
```

Cost note: a mid-session model switch resets the prompt cache — the next message re-reads the whole conversation at full input price.

## Key Paths

```
~/.hermes/config.yaml    settings
~/.hermes/.env           secrets only
~/.hermes/skills/        installed skills
~/.hermes/state.db       session store (SQLite)
~/.hermes/logs/          gateway logs
```

## Exercises

See `exercises/ch01.md`.

---
Next: [Chapter 2 — Daily Usage](../02-daily-usage/)
