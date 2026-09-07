# Exercise 06 — Messaging Gateway

## Objective

Connect a real messaging platform, verify session routing, and deliver messages from a
script — the egress path every automation in Part III depends on.

## Tasks

1. **Gateway state.** `hermes gateway status` — record: service active? linger enabled?
   PID? Any warnings in the recent log lines?
2. **Connect a platform.** If none: `hermes gateway setup` and attach Telegram (bot token
   via BotFather) or another platform of your choice. Send it one message; get one reply.
3. **Session mapping.** After your message: `hermes sessions list` — find the new
   platform session. Note its ID format. Reply from a second topic/chat; confirm a second
   session appears.
4. **Egress.** From a shell (not the agent):
   `hermes send --to <your-platform> "test from CLI"` — confirm delivery.
   Then pipe one: `uptime | hermes send --to <target>`.
5. **Media delivery.** Ask the agent (in the platform chat) to generate a chart and send
   it back — observe it arrive as a native attachment (deliverable mode).
6. **Logs.** `hermes logs --component gateway -n 50` right after a live message — identify
   the receive, the agent turn, and the send. Compare with what you saw in the chat.

## Verification checklist

- [ ] Gateway status healthy (service active, linger enabled) recorded.
- [ ] Platform round-trip works: message in, reply out.
- [ ] Each chat/topic maps to its own session ID.
- [ ] `hermes send` delivered both a literal message and a piped one.
- [ ] You can point to the three log lines: receive → agent → send.
