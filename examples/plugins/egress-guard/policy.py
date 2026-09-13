"""Policy engine for egress-guard. No Hermes imports: pure, and therefore testable.

Keeping the decision logic free of the plugin runtime is the single most useful structural
choice in a plugin. `__init__.py` translates hook payloads into calls here and translates
verdicts back into directives; everything that could be *wrong* lives in this file and is
covered by tests that need no agent, no network, and no Hermes install.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

# Tools that can move bytes off this machine. A tool absent from this map is not gated —
# that is deliberate and is the thing to re-read when Hermes adds a tool: a guard with an
# implicit allowlist fails open.
EGRESS_TOOLS: dict[str, tuple[str, ...]] = {
    "web_search": ("query",),
    "web_fetch": ("url",),
    "browser_navigate": ("url",),
    "send_message": ("text", "message"),
    "terminal": ("command",),
}

# Patterns that must never leave, whatever the destination. Ordered most-specific first so
# the reported reason names the narrowest thing that matched.
SECRET_PATTERNS: tuple[tuple[str, str], ...] = (
    ("AWS access key id", r"\bAKIA[0-9A-Z]{16}\b"),
    ("GitHub token", r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    ("Slack token", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    ("private key block", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ("bearer token", r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b"),
    ("generic api key assignment", r"\b(?:api[_-]?key|secret|token|password)\s*[=:]\s*\S{12,}"),
)

# Commands that exfiltrate by design. Matched on the command string, which is why
# `terminal` is gated at all.
EXFIL_COMMAND = re.compile(
    r"\b(?:curl|wget|scp|rsync|nc|ncat|netcat)\b|\|\s*(?:curl|wget|nc)\b", re.I
)

DEFAULT_ALLOWED_HOSTS = ("localhost", "127.0.0.1")
URL_HOST = re.compile(r"https?://([^/\s:]+)", re.I)


@dataclass(frozen=True)
class Verdict:
    """What to do, and why. `reason` is user-facing: it becomes the tool result on a block."""

    action: str  # "allow" | "block" | "approve" | "modify"
    reason: str = ""
    rule: str = ""
    redactions: dict[str, str] = field(default_factory=dict)


@dataclass
class Policy:
    """Operator-declared policy. Defaults are the safe reading of each question."""

    allowed_hosts: tuple[str, ...] = DEFAULT_ALLOWED_HOSTS
    # Unknown host: "approve" asks a human; "block" refuses; "allow" is the off switch.
    unknown_host: str = "approve"
    # A secret in an outbound payload is never merely approved. Choose how it fails:
    # "block" refuses the call; "redact" rewrites the argument and lets it through.
    on_secret: str = "block"
    # Controls the COMMAND-PATTERN heuristic only (curl/wget/scp/nc). Turning it off does
    # not turn off destination checking: a terminal command naming an unknown host is still
    # caught by the generic host gate below. Two independent layers, deliberately — a
    # switch that silently disabled both would be a switch nobody could reason about.
    gate_terminal_exfil: bool = True

    def __post_init__(self) -> None:
        if self.unknown_host not in {"approve", "block", "allow"}:
            raise ValueError(f"unknown_host must be approve|block|allow, got {self.unknown_host!r}")
        if self.on_secret not in {"block", "redact"}:
            raise ValueError(f"on_secret must be block|redact, got {self.on_secret!r}")


def find_secrets(text: str) -> list[str]:
    """Names of secret kinds present in `text`. Never returns the secret itself."""
    return [label for label, pattern in SECRET_PATTERNS if re.search(pattern, text)]


def redact(text: str) -> str:
    out = text
    for label, pattern in SECRET_PATTERNS:
        out = re.sub(pattern, f"[REDACTED {label}]", out)
    return out


def hosts_in(text: str) -> list[str]:
    return [h.lower() for h in URL_HOST.findall(text)]


def host_allowed(host: str, allowed: Iterable[str]) -> bool:
    """Exact match, or a subdomain of an allowed suffix.

    `example.com` allows `api.example.com` but NOT `example.com.evil.tld` — the check is
    on a dot boundary, because a substring check here is the whole vulnerability.
    """
    host = host.lower().strip().rstrip(".")
    for entry in allowed:
        entry = entry.lower().strip().lstrip(".").rstrip(".")
        if host == entry or host.endswith("." + entry):
            return True
    return False


def _payload(tool: str, args: dict[str, Any]) -> tuple[str, dict[str, str]]:
    """Concatenated text of the gated fields, plus field -> value for redaction."""
    fields = {}
    for key in EGRESS_TOOLS.get(tool, ()):
        value = args.get(key)
        if isinstance(value, str) and value:
            fields[key] = value
    return "\n".join(fields.values()), fields


def evaluate(tool: str, args: dict[str, Any], policy: Policy) -> Verdict:
    """The whole decision, in one pure function.

    Order matters and encodes the priorities: secrets first (a secret going to an ALLOWED
    host is still a secret leaving), then explicit exfiltration, then destination.
    """
    if tool not in EGRESS_TOOLS:
        return Verdict("allow")
    if not isinstance(args, dict):
        return Verdict("allow")

    text, fields = _payload(tool, args)
    if not text:
        return Verdict("allow")

    found = find_secrets(text)
    if found:
        names = ", ".join(found)
        if policy.on_secret == "redact":
            return Verdict(
                "modify",
                reason=f"redacted {names} before the call left the machine",
                rule="secret-redacted",
                redactions={k: redact(v) for k, v in fields.items()},
            )
        return Verdict(
            "block",
            reason=(f"BLOCKED by egress-guard: the {tool} payload contains {names}. "
                    "Credentials reach services through egress injection or a secret "
                    "source, never through a tool argument."),
            rule="secret-in-payload",
        )

    # Layer 1: the command-pattern heuristic. Catches an exfil command whose destination
    # is not a parseable URL, which the generic host gate below cannot see.
    if tool == "terminal" and policy.gate_terminal_exfil:
        command = args.get("command", "")
        if isinstance(command, str) and EXFIL_COMMAND.search(command):
            unknown = [h for h in hosts_in(command)
                       if not host_allowed(h, policy.allowed_hosts)]
            if unknown or not hosts_in(command):
                return Verdict(
                    "approve",
                    reason=f"network command to {', '.join(unknown) or 'an unparsed destination'}",
                    rule="terminal-egress",
                )

    # Layer 2: destination. Applies to every gated tool, terminal included, regardless of
    # gate_terminal_exfil.
    unknown = [h for h in hosts_in(text) if not host_allowed(h, policy.allowed_hosts)]
    if unknown and policy.unknown_host != "allow":
        destination = ", ".join(sorted(set(unknown)))
        if policy.unknown_host == "block":
            return Verdict(
                "block",
                reason=f"BLOCKED by egress-guard: {destination} is not in allowed_hosts.",
                rule="unknown-host",
            )
        return Verdict(
            "approve",
            reason=f"{tool} would contact {destination}, which is not in allowed_hosts",
            # rule_key groups the [a]lways allowlist by DESTINATION, not by tool: approving
            # "web_fetch" once should not approve every host forever.
            rule=f"egress:{destination}",
        )

    return Verdict("allow")
