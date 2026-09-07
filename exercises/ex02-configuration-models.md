# Exercise 02 — Configuration and Models

## Objective

Build a personal routing setup: named aliases for cost tiers, a fallback chain, and the
ability to inspect what you are spending.

## Tasks

1. **Baseline.** `hermes config get model` — record current default and provider.
2. **Pick a two-tier fleet.** Choose one strong/expensive model and one fast/cheap one
   from your provider's catalog (`hermes model` to browse).
3. **Inspect MoA and fallback state.** `hermes moa list` and `hermes fallback list` —
   record the starting point.
4. **Add one fallback** for your default provider:
   `hermes fallback add <provider>/<model>`, then confirm with `hermes fallback list`.
5. **Cost review.** Run `hermes insights --days 7`. Identify your most-used model and
   estimate which share of calls could run on the cheaper tier.
6. **Config hygiene.** `hermes config check` — resolve anything flagged. Run
   `hermes config path` and confirm no secrets are inside config.yaml
   (`grep -iE 'key|token|secret' $(hermes config path)` should be clean).

## Verification checklist

- [ ] `hermes fallback list` shows your backup model.
- [ ] You can name your current default model, its provider, and its rough cost tier.
- [ ] `hermes config check` passes.
- [ ] No API keys in config.yaml.
