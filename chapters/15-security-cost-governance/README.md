# Chapter 15 — Security, Cost, and Governance

> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Security and governance language appears in 5 of 18 postings with extracted body text (23 mentions; `docs/research/jobs/stats-2026-09-12.txt`) and gates everything else: True Zero's
engineer must align "all AI/ML solutions align with applicable security, data handling,
compliance, and Zero Trust requirements" (`docs/research/jobs/source-03.md`); Paramount
partners "with DevOps, SRE, and Infosec teams" (`docs/research/jobs/source-01.md`). An agent
with shell access is a privileged workload — running one without a security model is
negligence, and senior interviews probe exactly this. The second half of this chapter is cost
governance: the routing decisions of Chapter 02 become a budget policy here.

## Concepts

### The agent threat model

Your agent can: execute commands, read/write files, reach the network, spend API money,
and message people. Each capability is an attack surface:

- **Prompt injection** — malicious content in web pages, emails, repo files, even
  Telegram messages the agent reads, steering it to act against you. The course repo's
  AGENTS.md explicitly marks metadata as untrusted; that is governance.
- **Exfiltration** — agent reads a secret, then a web/search tool "helpfully" includes it
  in a request. Egress control exists for this.
- **Destructive execution** — `rm -rf`, force-push, wrong-host deploys.
- **Supply chain** — installed skills/plugins/MCP servers are code and context you didn't
  write (Chapters 10/11/12 vetting rules).

### Defense layers, verified

1. **Approval system** — dangerous commands require explicit user approval;
   `hermes approvals suggest` (verified) mines past decisions into an allowlist so the
   prompts you trust stop interrupting and the rest keep gating.
2. **Secrets discipline** — keys in `.env` only; external secret managers
   (`hermes secrets bitwarden|onepassword` — verified) pull keys at startup instead of
   storing them on disk; managed scope (docs) pins config for operator-controlled fleets.
3. **Egress firewall** — `hermes egress` manages iron-proxy (verified: "the optional
   TLS-intercepting egress firewall... credential-injection") — the agent's HTTP calls
   route through a proxy that injects credentials *without the model ever seeing them* and
   can block destinations.
4. **Isolation** — Docker/SSH/cloud terminal backends (Ch 13) bound blast radius;
   checkpoints (Ch 04) bound mutation damage; `hermes security` (verified) scans the venv
   and plugin deps against OSV.dev.
5. **Least privilege** — toolset scoping per run (Ch 05), MCP tool filtering (Ch 11),
   read-only catalog MCPs where possible.

### Cost governance

From Chapter 02's routing to an actual policy:

- **Tiers:** cheap/fast default; strong model only for reasoning-heavy tasks (explicit
  trigger list); MoA only for judgment calls.
- **Budgets per surface:** unsupervised jobs (cron, webhooks) run on the cheap tier with
  capped output; interactive work gets the strong tier.
- **Aux-model hygiene:** small models for compression/titles (Ch 02).
- **Measurement:** `hermes insights` weekly review; alert on week-over-week jumps (a
  script-only cron job — Chapter 07).

### Governance artifacts a senior engineer maintains

An approval allowlist with rationale, a secrets inventory (what lives where, rotation),
an egress policy (allowed destinations), an eval baseline (Ch 14) as the change gate, and
an incident runbook (Ch 04 logs + Ch 07 incidents).

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b6-security-observability.txt`
(security/approvals/secrets/egress command trees), `docs/research/hermes/cli-evidence-2026-09-07.txt`
(auth pools), plus gateway 429-retry logs in evidence b4 as cost/rate context.

## Verified commands

Approvals:

```bash
hermes approvals suggest      # mine past decisions -> proposed allowlist
hermes security               # OSV.dev scan: venv + plugin deps (verified)
```

Secrets:

```bash
hermes secrets bitwarden      # pull keys from Bitwarden at startup
hermes secrets onepassword
hermes config env-path        # where local secrets live
```

Egress:

```bash
hermes egress status          # iron-proxy state
hermes egress install / setup / start
hermes egress config          # destinations/credentials policy
```

Cost:

```bash
hermes insights --days 7      # weekly review
hermes fallback list          # resilience of the tier policy
hermes auth list              # pooled credentials state
```

## Common pitfalls

- **Approving forever to stop interruptions.** Every permanent approval is standing
  risk; allowlist only what is genuinely routine and re-review quarterly.
- **Secrets in prompts.** If a prompt contains a key, it's now in transcripts, logs,
  provider servers. Credentials flow via egress injection/secret sources, never prose.
- **No egress policy on data-touching agents.** An agent reading private data with open
  network access is an exfiltration path; iron-proxy or scoped network policies close it.
- **Cheap-tier-into-production.** Saving cost by running unsupervised automations on a
  weak model produces confident wrong output — pair tier policy with the eval gate of
  Chapter 14.
- **Trusting a skill/plugin/MCP because it works.** Vet before install (inspect,
  capabilities, source review); audit after (`hermes skills audit`, `plugins doctor`,
  `security`).
- **Governance documents nobody re-reads.** The allowlist/egress/budget docs are living
  runbooks — review on incidents and quarterly.

## Exercises

Work through `exercises/ex15-security-cost-governance.md`. Verification: approval
allowlist curated with rationale, egress status assessed, secrets inventory written,
cost policy documented and reflected in config.
