# Chapter 02 — Configuration and Models

> **Verified:** 2026-09-13 · Hermes Agent v0.21.2 (2026.9.11) · recheck: `python3 scripts/verify_chapters.py`

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
`vertex/gemini-2.5-pro` = same weights through Google Cloud — different billing, limits,
latency).
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

Both the values and the aliases are a 2026-09-07 snapshot: `hermes config get model` reports
whatever *your* machine is configured for. The three-layer shape (default / provider / aliases)
is the lesson — not the model names.

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

`hermes auth add|list|remove|reset|priority|refresh|status|logout|upgrade` (verified on
v0.21.2): multiple API keys or OAuth tokens per provider, rotated automatically to recover
from per-key rate limits. Use when RPM/TPM caps — not model quality — are the bottleneck.

Three of those subcommands are pool *operations* rather than setup, and they are what you
reach for when a pool misbehaves:

- `hermes auth priority <provider> <target> <priority>` — reorder the pool. Priority 0 is
  tried first under `fill_first` rotation, so this is how you put the paid key in front of
  the free one (or demote a key that is throttling). The other entries are renumbered.
- `hermes auth refresh <provider> [target]` — refresh a pooled **OAuth** credential's
  tokens and clear its cooldown. An expired OAuth token in a pool presents as "the pool is
  smaller than it looks"; refresh is the fix, not remove-and-re-add.
- `hermes auth reset <provider> [target]` — clear exhaustion status. On v0.21.2 it takes an
  optional target, so you can un-exhaust one credential instead of the whole pool.

`target` is a credential index, an entry id, or the exact label — the same three forms
`hermes auth list` prints.

### Nous Portal and account auth

`hermes portal` (subcommands `login|info|status|open|tools`) is the one-shot onboarding
path: log in to Nous Portal, pick a model, set Nous as the provider, and optionally enable
the Tool Gateway. `hermes portal info` prints the auth + Tool Gateway routing summary, and
`hermes portal tools` lists which tools are routed via Nous — useful when you are debugging
*where* a tool call actually went. `hermes auth upgrade` signs you in with a Nous account
while keeping existing connectors.

### Retiring models

Models get retired, and a config that names a dead model fails at run time, not at edit
time. `hermes migrate` diagnoses the active `config.yaml` for retired models and deprecated
settings; `hermes migrate xai --apply` rewrites xAI references to their official
replacements (dry-run by default, with a timestamped backup before any write). Run the
dry-run before every upgrade — it is the cheapest config check there is.

### Auxiliary models

Side-jobs (context compression, vision pre-processing, session titles) run on small
configured aux models, not your main model. Aux misconfiguration is a classic silent cost
leak: a 300B main model titling sessions burns money invisibly. Check them in
`hermes config show`.

### Cost visibility

`hermes insights --days 7` (verified) aggregates token usage, costs, tool patterns from
session history. Routing decisions should be made against this, not vibes.

### The general pattern

Nothing in this chapter is Hermes-specific, and interviews ask it at the general level. Any
system that calls more than one model provider ends up building the same four things, in
roughly this order:

1. **A capability tier**, so a request is routed by what it needs rather than by what is
   configured. Aliases are the cheap version of a routing table.
2. **A failover path**, because providers have incidents and your scheduled work does not
   care. The design question is always *what counts as failure* — a 429 is retryable, a 400
   is not, and treating them the same produces either a stall or a storm.
3. **Credential rotation**, which recovers from rate limits and — the part people miss —
   does *not* recover from expiry. Rotation and refresh are different mechanisms.
4. **A cost view**, because without one every routing decision is taste.

If you can name those four and say which failure each one addresses, the vendor is a
detail. The reverse is the trap: "we use OpenRouter" is not a routing strategy.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b2-config-models.txt`
(subcommand trees for config/model/moa/fallback/auth + live `config get model` output),
`docs/research/hermes/cli-evidence-2026-09-07-b6-security-observability.txt` (insights),
`docs/research/hermes/cli-evidence-2026-09-13-v0.21.2-surface.txt` (`auth`, `auth
priority/refresh/upgrade`, `migrate`, `portal` on v0.21.2 — the `auth` subcommand list grew
between v0.20.6 and v0.21.2).

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
hermes auth priority openrouter 2 0      # promote credential #2 to first-tried
hermes auth refresh nous                 # refresh a pooled OAuth token, clear its cooldown
hermes auth reset openrouter 3           # un-exhaust one credential (omit target for all)
```

Account auth and config migration:

```bash
hermes portal info          # Portal auth + Tool Gateway routing summary
hermes portal tools         # which tools route via Nous
hermes migrate xai          # dry-run: retired xAI models referenced in config.yaml
hermes migrate xai --apply  # rewrite them (backs config.yaml up first)
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
- **Treating a pool as self-healing.** Rotation recovers from rate limits, not from expiry.
  An OAuth credential whose token has lapsed stays in the pool and is skipped — `hermes auth
  status` shows it, `hermes auth refresh` fixes it. Nothing does it for you.
- **Upgrading Hermes without `hermes migrate`.** A retired model in `config.yaml` is a
  runtime failure on the next scheduled job, not a startup error. The dry-run is free.

## Exercises

Work through `exercises/ex02-configuration-models.md`. Verification: fallback chain has a
backup, MoA slots inspected, insights reviewed, config hygiene checks pass.

### Senior interview probes

1. You have three models available and one workload. Design the routing policy. What
   decides which model a given request gets?
2. A provider starts returning 429s at 09:00 every weekday. Walk through what your fallback
   chain does, and what it should do differently from a 500.
3. What does credential rotation protect you from, and what does it explicitly *not*
   protect you from?
4. Your scheduled jobs cost 4x what you expected and the output looks the same. Name three
   candidate causes and how you would tell them apart.
5. When is Mixture-of-Agents worth its cost multiple, and how would you decide rather than
   assert?
6. What is an auxiliary model, and what is the classic failure mode of ignoring it?
7. Someone proposes hand-editing `config.yaml` on a running gateway. What is your objection?
8. You inherit a system where every job runs on the strongest model. What do you measure
   before changing anything?