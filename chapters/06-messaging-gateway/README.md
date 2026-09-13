# Chapter 06 — Messaging Gateway

> **Verified:** 2026-09-13 · Hermes Agent v0.21.2 (2026.9.11) · recheck: `python3 scripts/verify_chapters.py`

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

**Two topologies, and a migration between them.** Per-profile standalone gateways are one
process, one systemd unit, and one set of platform connections *per profile*. The
alternative, added by v0.21.2's `hermes gateway migrate`, is **multiplexing**: one gateway
on the default profile serves every profile, driven by `gateway.multiplex_profiles`.

```bash
hermes gateway migrate --dry-run     # print the plan and any blockers, change nothing
hermes gateway migrate --multiplex   # default direction: collapse onto one gateway
hermes gateway migrate --standalone  # roll back from the recorded manifest
```

The migration stops and uninstalls each secondary profile's standalone gateway, turns on
`gateway.multiplex_profiles`, and restarts the default profile's gateway. It runs a
preflight first and **changes nothing when blocked** — the two blockers it checks for are
duplicate bot tokens across profiles and port-binding platforms that have no
`/p/<profile>/` ingress. Because the rollback reads a recorded manifest, `--standalone`
only works on a migration Hermes performed; it is not a general "split this gateway" tool.

Pick multiplexed when profiles share a host and you care about memory and unit count; pick
standalone when a profile needs its own blast radius (a customer-facing bot that must not
be restarted because an internal profile changed). Always run `--dry-run` first: the
preflight is the cheapest way to discover that two profiles are sharing a bot token.

### hermes send — the egress side

`hermes send` (verified full help in evidence batch 1) delivers messages *to* platforms
from any script or CI: `hermes send --to telegram "deploy finished"`,
`hermes send --to telegram:chat:thread "MEDIA:/tmp/chart.png"`. No LLM, no gateway needed
for bot-token platforms — it reuses the configured credentials. Chapters 08 uses it as the
universal notification primitive.

### The general pattern

A messaging gateway looks like an integration problem and is really a **routing and state**
problem. These are the questions every such system answers, whatever it is built on:

- **What is a session, in platform terms?** A thread, a channel, a user, a customer? Get it
  wrong and two people share context they should not, or one person loses continuity
  mid-conversation. It is a product decision wearing an engineering costume.
- **Delivery is not receipt.** An accepted message can be muted, filtered or deleted by the
  platform. A system that treats a 200 as "the human knows" will be wrong at the worst
  moment — which is exactly why failure notices need their own target (Chapter 07).
- **Ingress and egress are separable.** `hermes send` needs no agent and no gateway, which
  is what makes it usable from CI. Keeping the notification primitive independent of the
  conversational runtime is worth copying: **the thing that tells you the system is down
  should not require the system to be up.**
- **One process or many?** The multiplex-versus-standalone trade is the isolation question
  every multi-tenant service faces: shared resources and one blast radius, or separate ones
  and n times the operations.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b4-gateway-cron-events.txt`
(live `gateway status` systemd output incl. real 429 retry logs, `send --list` targets),
`docs/research/hermes/cli-evidence-2026-09-07.txt` (full `send --help`),
`docs/research/hermes/cli-evidence-2026-09-13-v0.21.2-surface.txt` (`gateway` and `gateway
migrate` — `migrate` is new since v0.20.6).

## Verified commands

Gateway lifecycle:

```bash
hermes gateway status      # systemd unit state, PID, memory, recent logs (verified live)
hermes gateway start|stop|restart
hermes gateway install     # install as systemd/launchd service
hermes gateway list        # per-profile gateway status
hermes gateway setup       # interactive platform configuration
hermes gateway migrate --dry-run    # multiplex plan + preflight blockers (v0.21.2)
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
- **Multiplexing without the dry run.** `hermes gateway migrate` uninstalls the secondary
  profiles' units. Its preflight refuses on duplicate bot tokens and on port-binding
  platforms with no `/p/<profile>/` ingress, so `--dry-run` tells you in seconds what a
  blind migration would tell you after the outage.

## Exercises

Work through `exercises/ex06-messaging-gateway.md`. Verification: one platform connected,
thread↔session mapping demonstrated, `hermes send` delivered from a script, gateway logs
read after a live message.

### Senior interview probes

1. Three people talk to your agent in one group chat, about two different customers. What is
   a session here? Defend the boundary you chose.
2. `hermes send` returns exit code 0. What do you actually know, and what do you not?
3. Your gateway delivers successful output and failure notices to the same channel. Describe
   the incident that eventually causes.
4. When would you run one multiplexed gateway rather than one per profile, and what is the
   first thing you would check before migrating?
5. A bot token is rotated. What has to happen, and what breaks if you forget it?
6. Sustained 429s from a platform at peak hour, with retries already in place. What now?
7. The notification path that tells you the agent is down runs on the agent. What is wrong
   with that, and what would you change?
8. How would you let an agent in a chat platform hand a user a file, and what are the
   failure modes of the path you chose?
