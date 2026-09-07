# Exercise 15 — Security, Cost, and Governance

## Objective

Produce the four governance artifacts a senior engineer maintains — approval allowlist,
secrets inventory, egress assessment, cost policy — and harden one real workflow.

## Tasks

1. **Approval audit.** Review your dangerous-command approvals; run `hermes approvals
   suggest`; keep the allowlist minimal with a one-line rationale per entry. Remove one
   approval you no longer need.
2. **Secrets inventory.** List every credential your agent setup uses: file where it
   lives (`.env`/Bitwarden/1Password), provider, rotation date. Migrate one key from
   `.env` to an external secret source if available (`hermes secrets ...`).
3. **Egress assessment.** `hermes egress status` — if not installed, write the policy you
   would deploy (allowed destinations for a data-touching agent) and the command to
   enforce it.
4. **Security scan.** Run `hermes security` (OSV scan); triage anything it flags.
5. **Cost policy.** Write your tier policy (default/strong/unsupervised) as 5 lines;
   verify config reflects it (`hermes config get model`, `hermes fallback list`); set up
   the weekly `hermes insights` review reminder as a cron job.
6. **Harden one workflow.** Take your Chapter 07 cron job: scope its toolsets to the
   minimum, confirm its delivery target, and document its rollback path.

## Verification checklist

- [ ] Allowlist minimal, every entry has a rationale.
- [ ] Secrets inventory complete with locations; one external-source migration done or
      justified.
- [ ] Egress status assessed (or policy written); OSV scan run and triaged.
- [ ] Cost policy written and visible in live config.
- [ ] The hardened workflow runs with reduced scope and a documented rollback.
