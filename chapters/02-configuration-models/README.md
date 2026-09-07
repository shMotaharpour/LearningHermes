# Chapter 02 — Configuration and Models

## Why this matters (job link)

Cost and performance optimization appears in most senior postings — Paramount wants
"scalable, resilient, and impactful AI solutions" (`docs/research/jobs/source-01.md`);
100ms asks for metric-driven work on "correctness, latency, hallucination control"
(`docs/research/jobs/source-05.md`). The cheapest lever an applied AI engineer owns is
**model routing**: right model, right task, right price, with a failover path. Hermes makes
routing a first-class configuration concern — providers, aliases, Mixture of Agents,
fallback chains, credential pools, auxiliary models — and this chapter makes you fluent in
all six.

## Concepts

### Provider vs model

A **provider** is an API surface: OpenRouter, Anthropic, OpenAI, Google, Nous Portal, an
Ollama server on localhost, any OpenAI-compatible endpoint. A **model** is an identifier a
provider serves (`gemini/gemini-2.5-pro` = Google model via OpenRouter;
`vertex/gemini-2.5-pro` = same weights via Vertex AI — different billing, limits, latency).
Hermes resolves `provider/model` pairs at runtime and supports three auth patterns: API
keys (`.env`), OAuth browser logins, pooled credentials.

### The three-layer model resolution

`hermes config get model` (verified, evidence b2) shows how a request resolves:

```
default: minimax/minimax-m3:free      <- layer 1: what runs now
provider: openrouter                  <- layer 2: which API surface
aliases:
  gemini-pro: gemini/gemini-2.5-pro   <- layer 3: your routing vocabulary
  gemini-flash: gemini/gemini-2.5-flash
  vertex-pro: vertex/gemini-2.5-pro
  vertex-flash: vertex/gemini-2.5-flash
```

Aliases are the routing vocabulary you will use everywhere: `/model gemini-flash` in
sessions, `model: gemini-pro` in cron prompts, `-m $FAST` in scripts. Define once, rename
providers later in one line.

### Scope: session vs global

`/model X` in a session changes that session only; `--global` persists to config.yaml.
Scripts and cron always use the default unless the prompt overrides it. Rule of thumb:
experiment in session scope, commit choices in global scope.

### Mixture of Agents (MoA)

`hermes moa list|configure|delete` (verified). `/moa <prompt>` fans one prompt out to
several configured models and synthesizes their answers. Model *disagreement* is the
signal you are buying — use it for high-stakes judgments (eval design, architecture
reviews), never for routine work (cost multiplies by slot count).

### Fallback chain

`hermes fallback list|add|remove|clear` (verified): providers tried in order when the
primary fails with rate-limit, overload, or connection errors. Production rule: **every
scheduled/unsupervised job assumes a fallback exists.** A 6am cron briefing on a single
rate-limited provider is a silent missed deliverable.

### Credential pools

`hermes auth add|list|remove|reset|status` (verified): multiple API keys or OAuth tokens
per provider, rotated automatically to recover from per-key rate limits. Use when RPM/TPM
caps — not model quality — are the bottleneck.

### Auxiliary models

Side-jobs (context compression, vision pre-processing, session titles) run on small
configured aux models, not your main model. Aux misconfiguration is a classic silent cost
leak: a 300B main model titling sessions burns money invisibly. Check them in
`hermes config show`.

### Cost visibility

`hermes insights --days 7` (verified) aggregates token usage, costs, tool patterns from
session history. Routing decisions should be made against this, not vibes.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b2-config-models.txt`
(subcommand trees for config/model/moa/fallback/auth + live `config get model` output),
`docs/research/hermes/cli-evidence-2026-09-07-b6-security-observability.txt` (insights).

## Verified commands

Inspect configuration — use commands, never hand-edit while the gateway runs:

```bash
hermes config show          # full resolved config
hermes config get model     # default + provider + aliases (live output above)
hermes config path          # settings file location
hermes config env-path      # secrets file location
hermes config check         # missing/outdated options
hermes config set model gemini/gemini-2.5-flash    # direct set
hermes config unset display.skin                   # remove a key
```

Routing infrastructure:

```bash
hermes moa list                          # inspect MoA slots
hermes moa configure                     # interactive slot editor
hermes fallback list                     # current chain
hermes fallback add openrouter/meta-llama/llama-3.3-70b-instruct
hermes auth list                         # pooled credentials per provider
hermes auth status                       # pool health
```

Cost awareness:

```bash
hermes insights --days 7     # tokens, cost trends, tool usage patterns
```

## Common pitfalls

- **Wrong scope.** `/model X` without `--global` reverts next session — the classic "why
  did it switch back?" ticket.
- **No fallback on scheduled jobs.** Chapter 07 depends on this chapter: cron jobs with a
  single provider fail silently at 6am.
- **MoA as default.** MoA multiplies cost by slot count per prompt. Judgment tool only.
- **Hand-editing config.yaml with a live gateway.** Prefer `hermes config set`; if you
  must edit, run `hermes config check` immediately after.
- **Secrets misplacement.** `hermes config env-path` is where keys go — never config.yaml,
  never git, never screenshots in docs.
- **Aux model neglect.** Unreviewed aux models quietly burn tokens on every compression
  and title operation.

## Exercises

Work through `exercises/ex02-configuration-models.md`. Verification: fallback chain has a
backup, MoA slots inspected, insights reviewed, config hygiene checks pass.
