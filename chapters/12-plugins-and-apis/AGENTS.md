# Chapter 12 — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Scope boundary

In-process extension and the API surfaces (`serve`, `acp`, `proxy`, embedding). Cross-process
tools are 11.

## Ships

`examples/plugins/egress-guard/` and `examples/embed-agent.py`. Pinned by
`tests/test_plugin_egress_guard.py`.

## Care

- `policy.py` must keep importing nothing from Hermes. That separation is the chapter's
  structural lesson and what makes the plugin testable offline.
- The plugin's implicit tool allowlist is a known limitation the chapter states out loud.
  Do not quietly "fix" it without also rewriting the passage that teaches it.
- `embed-agent.py` documents the checkout-and-`uv sync` path. There is no published wheel.
