# `egress-guard` — a worked Hermes plugin

The plugin Chapter 12 authors. It gates outbound tool calls against a declared policy:
block, escalate to the human-approval gate, or redact.

## Install

```bash
cp -r examples/plugins/egress-guard ~/.hermes/plugins/     # user-global
# or
cp -r examples/plugins/egress-guard ./.hermes/plugins/     # project-local

hermes plugins list                       # it should appear
hermes plugins capabilities egress-guard  # what it registers — read before enabling
hermes plugins doctor                     # against the real runtime contracts
```

## Policy

Optional `~/.hermes/egress-guard.json` (or `./.hermes/egress-guard.json`, which wins):

```json
{
  "allowed_hosts": ["localhost", "127.0.0.1", "api.githubinternal.example"],
  "unknown_host": "approve",
  "on_secret": "block",
  "gate_terminal_exfil": true
}
```

| Key | Meaning |
|---|---|
| `allowed_hosts` | Exact host, or any subdomain of it on a dot boundary |
| `unknown_host` | `approve` (ask a human) · `block` · `allow` (off switch) |
| `on_secret` | `block` the call, or `redact` the argument and continue |
| `gate_terminal_exfil` | The `curl`/`wget`/`scp`/`nc` command heuristic. **Off does not mean unguarded** — destination checking still applies to terminal commands. |

A malformed policy file is a **loud fallback to defaults**, never a silent disable. A guard
that turns itself off because of a typo is worse than no guard, because you think you have
one.

## What it demonstrates

| Surface | Here |
|---|---|
| `ctx.register_hook("pre_tool_call")` | veto / escalate / rewrite a tool call before dispatch |
| `ctx.register_tool` | `egress_check` — the model can ask the policy instead of being blocked |
| `ctx.register_command` | `/egress`, `/egress policy` |
| `ctx.register_cli_command` | `hermes egress-guard --json` |

## The structural choice worth copying

`policy.py` imports nothing from Hermes. All the logic that could be *wrong* is pure
functions over plain dicts, so `tests/test_plugin_egress_guard.py` covers it with no agent,
no network, and no Hermes install. `__init__.py` only translates hook payloads into policy
calls and verdicts back into directives.

Do this in every plugin you write. The runtime surface is the part you cannot test cheaply;
keep it thin enough that there is nothing in it to test.

## Three details that are load-bearing

1. **Order of checks.** Secrets are checked before destination, because a credential going
   to an *allowed* host is still a credential leaving.
2. **`host_allowed` matches on a dot boundary.** `example.com` allows `api.example.com` and
   rejects `example.com.evil.tld`. A substring check here is the whole vulnerability.
3. **`rule_key` groups the approval allowlist by destination, not by tool.** Approving
   `web_fetch` once should not approve every host forever.
4. **Two independent layers, not one switch.** The command heuristic catches
   `nc 10.0.0.5 4444` — a destination that is not a URL and that host matching cannot see.
   Destination checking catches everything with a hostname. `gate_terminal_exfil: false`
   turns off only the first. A switch that silently disabled both would be a switch nobody
   could reason about.

## Limits — read before trusting it

This is a teaching plugin, not a security boundary. It is a *policy gate*, and it can be
walked around: base64 a secret, split a payload across two calls, use a tool that is not in
`EGRESS_TOOLS`. That last one is the important failure mode — the tool map is an implicit
allowlist, so a tool Hermes adds tomorrow is ungated until someone adds it here.

Real egress control is `hermes egress` (Chapter 15): a TLS-intercepting proxy that injects
credentials the model never sees, enforced below the agent rather than inside it. This
plugin is defence in depth above that, and a good way to learn the hook contract.
