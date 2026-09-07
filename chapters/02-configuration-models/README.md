# Chapter 02 — Configuration and Models

## Why this matters (job link)

Cost and performance optimization appears in most senior postings — Paramount wants
engineers who optimize "scalable, resilient, and impactful AI solutions"
(`docs/research/jobs/source-01.md`); 100ms asks for metric-driven improvement of "correctness,
latency, hallucination control" (`docs/research/jobs/source-05.md`). The cheapest lever an
applied AI engineer owns is **model routing**: right model, right task, right price. Hermes
makes routing a first-class configuration concern — providers, aliases, Mixture of Agents,
fallback chains, credential pools — and this chapter makes you fluent in all of it.

## Concepts

**Provider vs model.** A provider is an API surface (OpenRouter, Anthropic, OpenAI, Google,
Nous Portal, a local Ollama server, ...). A model is an identifier served by a provider
(`gemini/gemini-2.5-pro` = Google model via OpenRouter). Hermes resolves `provider/model`
pairs at runtime and supports per-provider auth: API keys (`.env`), OAuth logins
(`hermes model` with browser flow), or pooled credentials.

**The model alias layer.** `hermes config get model` (verified, evidence b2) shows the
three-layer resolution:

```
default: minimax/minimax-m3:free      <- what runs now
provider: openrouter                  <- which API surface
aliases:
  gemini-pro: gemini/gemini-2.5-pro   <- friendly names you define
  gemini-flash: gemini/gemini-2.5-flash
  vertex-pro: vertex/gemini-2.5-pro
```

Aliases are your routing vocabulary: define `cheap`, `smart`, `fast` once, then use them in
slash commands, cron prompts, and scripts. Renaming providers later becomes a one-line fix.

**Mixture of Agents (MoA).** `/moa <prompt>` fans one prompt out to several configured
models and synthesizes. Configure slots with `hermes moa configure` (verified subcommands:
`list, configure, delete`). Use it for high-stakes answers where model disagreement is a
signal, not for routine work.

**Fallback chain.** `hermes fallback add/list/remove/clear` (verified). Providers are tried
in order when the primary fails with rate-limit, overload, or connection errors. This is
production hygiene: a cron briefing that must fire every morning needs a fallback path.

**Credential pools.** `hermes auth add/list/remove/status` (verified). Multiple API keys or
OAuth tokens per provider, rotated automatically to survive per-key rate limits. This is
what you use when one key's RPM cap is the bottleneck.

**Auxiliary models.** Beyond the main model, Hermes uses small models for side-jobs
(compression, vision, titles). They are configured in `config.yaml` and cost a fraction of
main-model calls. Routing discipline: main model for reasoning, aux for volume work.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b2-config-models.txt` (all
subcommand trees + live `config get model` output).

## Verified commands

Inspect configuration (never open config.yaml directly when a command exists):

```bash
hermes config show          # full resolved config
hermes config get model     # default model + provider + aliases
hermes config path          # where config.yaml lives
hermes config env-path      # where .env lives
hermes config check         # missing/outdated options
```

Change model — two scopes:

```bash
hermes model                            # interactive picker (provider + model)
hermes config set model gemini/gemini-2.5-flash    # direct set
```

In a session (Telegram or CLI), `/model <name>` switches session-only; `--global` persists.

Routing infrastructure:

```bash
hermes moa list             # inspect MoA slots
hermes fallback list        # current fallback chain
hermes fallback add openrouter/meta-llama/llama-3.3-70b-instruct   # append a fallback
hermes auth list            # pooled credentials per provider
```

Cost awareness in-session:

```bash
hermes insights --days 7    # token usage + cost trends from session history (verified subcommand)
```

## Common pitfalls

- **Setting model in the wrong scope.** `/model X` in a Telegram topic changes that session
  only; forgetting `--global` means "why did it revert?" the next session.
- **No fallback on scheduled jobs.** A 6am cron job with a single provider is a single
  point of failure; rate-limit at 6am means silent missed delivery.
- **MoA for everything.** MoA multiplies token cost by the slot count. It is a judgment
  tool, not a default.
- **Editing config.yaml by hand while the gateway runs.** Prefer `hermes config set`; a
  stray indent corrupts live config. `hermes config check` after any manual edit.
- **Forgetting `.env` discipline.** `hermes config env-path` tells you where keys go; they
  never go in config.yaml, git, or screenshots.

## Exercises

Work through `exercises/ex02-configuration-models.md`. Verification: alias routing works,
fallback chain has ≥1 backup, you can explain your current default model's cost tier.
