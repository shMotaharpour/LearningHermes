# Exercise 12 — Plugins and APIs

## Objective

Stop consuming extension points and build on them. You author a plugin, watch it veto a
real tool call, then touch the other three integration contracts — API server, editor/proxy,
and embedding — so you can defend a choice between them.

Budget: 3–4 hours.

## Tasks

1. **Plugin recon.** `hermes plugins list`; pick one and run `hermes plugins capabilities`
   + `hermes plugins doctor`. Record what it registers — hooks, tools, commands. This is
   the shape you are about to produce.

2. **Install the worked plugin and prove it gates.**

   ```bash
   cp -r examples/plugins/egress-guard ~/.hermes/plugins/
   hermes plugins capabilities egress-guard
   hermes egress-guard --json   # plugin: egress-guard
   ```

   Then make the agent try something the policy refuses — ask it to fetch a URL on a host
   that is not in `allowed_hosts` — and record what came back. Run `/egress` in the session
   to see the decision. Write down **which of the three directives** fired and why.

3. **Read the policy before you change it.** `python3 -m unittest tests.test_plugin_egress_guard`.
   Find the test named `test_suffix_lookalike_is_rejected` and explain, in one sentence,
   what bug it exists to prevent. Then find the test proving the block message never
   contains the secret it detected, and say why that matters.

4. **Author your own rule.** Extend `policy.py` with one rule of your own — a payload size
   cap, a time-of-day gate, a per-tool destination list, whatever your context needs. It
   must be a pure function, and it must come with a test that runs offline. Then run the
   plugin and trigger it for real.

   If your rule needs something `pre_tool_call` does not give you, say so explicitly:
   "this needs X, which the hook payload lacks" is the correct finding, and it is how
   extension points get widened.

5. **Break it on purpose.** Point `~/.hermes/egress-guard.json` at malformed JSON, restart,
   and observe what the plugin does. Explain why a *loud fallback to defaults* is the right
   behaviour and a silent disable is not. Then make your rule raise an exception and
   confirm the agent keeps running.

6. **API server round-trip.** `hermes serve --port 8377` on localhost. From another shell,
   POST an OpenAI-shaped chat request with `API_SERVER_KEY` and get a completion that used
   a tool. Stop the server afterwards.

7. **ACP or proxy.** Pick one: connect an editor via `hermes acp`, or point an OpenAI-SDK
   client at `hermes proxy`. Record the working config.

8. **Embedding.** Run `examples/embed-agent.py` from a Hermes checkout (`uv sync` first).
   Then change one thing: swap `enabled_toolsets` for `disabled_toolsets` and write down
   why the allowlist is the safer default for an embedded agent.

9. **Decision memo.** For a real product of your choosing — not a hypothetical — write ten
   lines picking **one** of MCP / plugin / `hermes serve` / embedding, with the two
   strongest arguments against your choice and why you accept them.

## Verification checklist

- [ ] `capabilities` + `doctor` output recorded for an existing plugin.
- [ ] `egress-guard` installed and observed **blocking or escalating a real tool call**,
      with the directive named.
- [ ] `test_suffix_lookalike_is_rejected` explained; the no-secret-in-the-message test found
      and its purpose stated.
- [ ] Your own rule in `policy.py` with an offline test, triggered live.
- [ ] Malformed-policy behaviour observed and defended; a raising rule proven not to take
      the agent down with it.
- [ ] API round-trip succeeded with auth, server stopped cleanly.
- [ ] Editor/proxy path produced a working agent-backed session.
- [ ] `examples/embed-agent.py` runs; allowlist-vs-denylist reasoning written down.
- [ ] Decision memo names one contract and argues the strongest case *against* it.
