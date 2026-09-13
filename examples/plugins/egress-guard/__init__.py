"""egress-guard — a worked Hermes plugin. Chapter 12.

Four registration surfaces in one plugin, because they are the four ways a plugin reaches
the agent and you should see them together:

    ctx.register_hook("pre_tool_call", ...)   veto / escalate / rewrite a tool call
    ctx.register_tool(...)                     a new tool the model can call
    ctx.register_command("egress", ...)        an in-session slash command
    ctx.register_cli_command("egress-guard")   a `hermes egress-guard ...` subcommand

Install by copying this directory to ~/.hermes/plugins/egress-guard/ (user-global) or
./.hermes/plugins/egress-guard/ (project-local), then `hermes plugins list`.

Contract notes, verified against the Hermes source at v0.21.2:

* `pre_tool_call` callbacks return a dict directive. Three actions matter:
    {"action": "block",   "message": str}          message becomes the tool result
    {"action": "approve", "message": str,
                          "rule_key": str}          routes to the human-approval gate
    {"action": "modify",  "args": {...}}            shallow-merged into the tool's args
  First valid block/approve wins; `modify` directives accumulate and are applied even
  when a later hook blocks. Anything else is ignored.

* Hook callbacks are SIGNATURE-INSPECTED. A callback declaring only the kwargs it wants
  receives only those; a `**kwargs` callback receives the full payload. This is what makes
  the hook contract additive: new payload fields cannot break a narrow callback. Declare
  `**_` anyway, so a future field does not surprise you.

* Hooks must never raise. A guard that crashes is a guard that is not running, and the
  agent keeps going. Every callback here is wrapped.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from . import policy as P

logger = logging.getLogger(__name__)

CONFIG_NAME = "egress-guard.json"

# Decisions made this process, for `/egress` and the session-end summary. An in-memory
# counter is enough here; anything you need after a crash belongs in ctx storage.
_ledger: list[dict] = []
_policy: P.Policy = P.Policy()


def _load_policy() -> P.Policy:
    """Read the operator's policy, or fall back to the safe defaults.

    Order: project-local, then user-global. A malformed file is a LOUD fallback to
    defaults — never a silent disable, which is how a guard stops guarding without
    anybody noticing.
    """
    for candidate in (Path.cwd() / ".hermes" / CONFIG_NAME,
                      Path.home() / ".hermes" / CONFIG_NAME):
        if not candidate.is_file():
            continue
        try:
            raw = json.loads(candidate.read_text(encoding="utf-8"))
            return P.Policy(
                allowed_hosts=tuple(raw.get("allowed_hosts", P.DEFAULT_ALLOWED_HOSTS)),
                unknown_host=raw.get("unknown_host", "approve"),
                on_secret=raw.get("on_secret", "block"),
                gate_terminal_exfil=bool(raw.get("gate_terminal_exfil", True)),
            )
        except (OSError, ValueError) as exc:
            logger.warning(
                "egress-guard: %s is unreadable (%s). Falling back to DEFAULT policy — "
                "the gate is still on, but it is not the policy you wrote.", candidate, exc)
            return P.Policy()
    return P.Policy()


def _record(tool: str, verdict: P.Verdict) -> None:
    _ledger.append({"tool": tool, "action": verdict.action,
                    "rule": verdict.rule, "reason": verdict.reason})


def _on_pre_tool_call(tool_name: str = "", args: Optional[Dict[str, Any]] = None,
                      **_: Any) -> Optional[dict]:
    """Gate one tool call. Returns a directive dict, or None to let it through."""
    try:
        verdict = P.evaluate(tool_name, args or {}, _policy)
    except Exception:  # a broken guard must not break the agent
        logger.exception("egress-guard: policy evaluation failed; allowing the call")
        return None

    if verdict.action == "allow":
        return None
    _record(tool_name, verdict)

    if verdict.action == "block":
        return {"action": "block", "message": verdict.reason}
    if verdict.action == "modify":
        logger.info("egress-guard: %s", verdict.reason)
        return {"action": "modify", "args": verdict.redactions}
    return {"action": "approve", "message": verdict.reason, "rule_key": verdict.rule}


def _on_post_tool_call(tool_name: str = "", **_: Any) -> None:
    """Deliberately empty of policy.

    Registered to make one point: post_tool_call is for observation. By the time it fires
    the bytes have already left. Nothing you do here is a control.
    """
    return None


def _on_session_end(**_: Any) -> None:
    if not _ledger:
        return
    blocked = sum(1 for e in _ledger if e["action"] == "block")
    approved = sum(1 for e in _ledger if e["action"] == "approve")
    redacted = sum(1 for e in _ledger if e["action"] == "modify")
    logger.info("egress-guard: %d blocked, %d sent for approval, %d redacted this session",
                blocked, approved, redacted)


# --- a tool the model can call -------------------------------------------------------

EGRESS_CHECK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "egress_check",
        "description": (
            "Check whether sending the given text to the given host would be allowed by "
            "the egress policy. Use this BEFORE composing an outbound request when you "
            "are unsure, rather than attempting the call and being blocked."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The payload you intend to send."},
                "host": {"type": "string", "description": "Destination hostname."},
            },
            "required": ["text", "host"],
        },
    },
}


def _egress_check(text: str = "", host: str = "", **_: Any) -> str:
    """Let the model ask the policy a question instead of discovering it by being blocked.

    Note what this tool does NOT do: it never reports the secret it found, only its kind.
    A tool that echoes a matched credential back into the transcript has moved the secret
    into the context window, which is the thing the plugin exists to prevent.
    """
    found = P.find_secrets(text or "")
    if found:
        return f"NOT ALLOWED: payload contains {', '.join(found)}; policy is {_policy.on_secret}."
    if host and not P.host_allowed(host, _policy.allowed_hosts):
        return (f"NOT ALLOWED WITHOUT APPROVAL: {host} is not in allowed_hosts "
                f"({', '.join(_policy.allowed_hosts)}); policy is {_policy.unknown_host}.")
    return "ALLOWED: destination is in allowed_hosts and no secret pattern matched."


# --- slash command and CLI subcommand ------------------------------------------------

def _handle_slash(raw_args: str = "") -> str:
    arg = (raw_args or "").strip()
    if arg == "policy":
        return (f"allowed_hosts={', '.join(_policy.allowed_hosts)}\n"
                f"unknown_host={_policy.unknown_host}\n"
                f"on_secret={_policy.on_secret}\n"
                f"gate_terminal_exfil={_policy.gate_terminal_exfil}")
    if not _ledger:
        return "egress-guard: nothing gated this session."
    lines = [f"{e['action']:<8} {e['tool']:<18} {e['rule']}" for e in _ledger[-20:]]
    return "\n".join(lines)


def _setup_cli(subparser) -> None:
    subparser.add_argument("--json", action="store_true", help="machine-readable output")


def _run_cli(args) -> int:
    payload = {
        "policy": {
            "allowed_hosts": list(_policy.allowed_hosts),
            "unknown_host": _policy.unknown_host,
            "on_secret": _policy.on_secret,
            "gate_terminal_exfil": _policy.gate_terminal_exfil,
        },
        "decisions": _ledger,
    }
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2))
    else:
        print(_handle_slash("policy"))
    return 0


def register(ctx) -> None:
    """Entry point. Hermes calls this once per process, at discovery."""
    global _policy
    _policy = _load_policy()

    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    ctx.register_hook("post_tool_call", _on_post_tool_call)
    ctx.register_hook("on_session_end", _on_session_end)

    ctx.register_tool(
        name="egress_check",
        toolset="security",
        schema=EGRESS_CHECK_SCHEMA,
        handler=_egress_check,
        description="Ask the egress policy whether a payload may be sent to a host.",
        emoji="🛡️",
    )

    ctx.register_command(
        "egress", handler=_handle_slash,
        description="Show egress-guard decisions this session (`/egress policy` for the policy).",
        args_hint="[policy]",
    )

    ctx.register_cli_command(
        "egress-guard", help="Show the active egress policy and this process's decisions.",
        setup_fn=_setup_cli, handler_fn=_run_cli,
    )
