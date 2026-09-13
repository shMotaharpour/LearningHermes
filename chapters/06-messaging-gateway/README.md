# Chapter 06 — Messaging Gateway

> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Integration with the systems people actually use is the applied engineer's bread and
butter: Adventus hires for "integrating AI capabilities with platforms such as Microsoft
Dynamics 365, SAP, ServiceNow, Microsoft Azure" (`docs/research/jobs/extract-round2.json`);
Minted wants "intelligent assistants that serve HR, Finance, Operations... integrating
LLM-based solutions into our corporate tools" (`docs/research/jobs/extract-round2.json`).
The gateway is Hermes' integration masterclass: one agent core, 21+ platform adapters,
session routing, delivery guarantees. Learning how the gateway thinks teaches you how to
integrate *any* AI system with *any* communication surface — the exact competency
automation-engineer postings describe.

## Concepts

### Gateway architecture

The gateway is a long-running service (`hermes-gateway.service`, systemd user service —
verified live status in evidence b4) that:

1. Connects platform adapters (Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email,
   Teams, ...), each holding platform credentials from `.env`.
2. Routes every incoming message to a **session** by platform + chat + thread identity.
3. Runs the same agent loop as the CLI — tools included — against that session.
4. Delivers replies (and deliverables: files, images, audio) back to the platform.

Ops essentials verified from the live service: it survives logout (systemd linger), runs
`hermes gateway run` under the hood, and its runtime problems (429 rate-limit retries,
tool errors, delivery warnings) are visible in `hermes logs` — the transcript shows the
conversation, the logs show the service.

### Session routing

Each platform conversation gets a deterministic session identity
(`platform:chat:thread`), so topics/threads map to separate Hermes sessions. This is why
per-topic memory and per-topic model switching work. The routing index can be repaired
(`hermes sessions repair-routing`) when identity stamps break.

### Platforms you can attach

Setup flows per platform (via `hermes gateway setup` or platform-specific docs):
Telegram (bot token), Discord (bot), Slack (Socket Mode), WhatsApp (bridge or Business
Cloud API), Signal (signal-cli daemon), Email (IMAP/SMTP), SMS (Twilio), Matrix,
Mattermost, Teams, Google Chat, LINE, IRC, and more. Two patterns exist everywhere:
**bot-token platforms** (simple credential + webhook/polling) and **daemon-bridge
platforms** (a local daemon speaking the platform protocol).

### Deliverable mode

The agent ships artifacts as native attachments: charts as photos, reports as documents,
audio as voice bubbles (`MEDIA:` syntax). This is what turns the agent from a text
responder into a delivery endpoint — cron jobs in Chapter 07 depend on it.

### Profiles and multi-gateway

Each profile (`~/.hermes/profiles/<name>/`) can run its own gateway — multiple gateways
at once is a supported topology (different bots, different platforms, different
personalities). `hermes gateway list` shows per-profile status.

### hermes send — the egress side

`hermes send` (verified full help in evidence batch 1) delivers messages *to* platforms
from any script or CI: `hermes send --to telegram "deploy finished"`,
`hermes send --to telegram:chat:thread "MEDIA:/tmp/chart.png"`. No LLM, no gateway needed
for bot-token platforms — it reuses the configured credentials. Chapters 08 uses it as the
universal notification primitive.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b4-gateway-cron-events.txt`
(live `gateway status` systemd output incl. real 429 retry logs, `send --list` targets),
`docs/research/hermes/cli-evidence-2026-09-07.txt` (full `send --help`).

## Verified commands

Gateway lifecycle:

```bash
hermes gateway status      # systemd unit state, PID, memory, recent logs (verified live)
hermes gateway start|stop|restart
hermes gateway install     # install as systemd/launchd service
hermes gateway list        # per-profile gateway status
hermes gateway setup       # interactive platform configuration
```

Delivery targets:

```
$ hermes send --list
Available messaging targets:
Telegram:
  telegram:Hermes / topic 1178 (group)
  telegram:Hermes / topic 1 (group)...
```

```bash
hermes send --to telegram "build finished"              # home channel
hermes send --to telegram:-100123:17585 "hi"            # explicit chat:thread
hermes send --to discord:#ops --file /tmp/report.md     # attachment
hermes send --to telegram "MEDIA:/tmp/chart.png"        # media delivery
echo "RAM 92%" | hermes send --to telegram               # stdin pipe
```

Diagnostics:

```bash
hermes logs --component gateway -n 100    # gateway-side runtime view
hermes sessions list                      # confirm platform sessions landed
hermes sessions repair-routing            # fix lost routing identity
```

## Common pitfalls

- **Restart from inside the gateway.** On systemd installs, an in-process `hermes gateway
  restart` kills its own command. Restart from a separate shell/session.
- **Credentials in the wrong file.** Platform tokens go in `~/.hermes/.env`; the gateway
  reads them at boot. Rotating a token requires a restart.
- **Thread/session confusion.** A Telegram *topic* is its own session with its own context
  and model. Post in the wrong topic, talk to the wrong agent state.
- **Delivery ≠ seen.** `hermes send` exit code 0 means the platform accepted it. Redelivery,
  muting, and notification settings are platform-side.
- **Forgetting linger.** Without systemd linger enabled, your gateway dies at logout.
  `hermes gateway status` verifies it (verified: "Systemd linger is enabled").
- **Peak-hour 429s.** The gateway retries rate-limited calls automatically (verified live
  logs: "Retrying API call in 2.4s (attempt 1/3)") — but sustained 429s need the fallback
  chain from Chapter 02, not hope.

## Exercises

Work through `exercises/ex06-messaging-gateway.md`. Verification: one platform connected,
thread↔session mapping demonstrated, `hermes send` delivered from a script, gateway logs
read after a live message.
