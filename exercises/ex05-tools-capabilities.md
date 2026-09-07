# Exercise 05 — Tools and Capabilities

## Objective

Practice the capability-matching discipline: scope toolsets per task, walk the web
escalation ladder, and exercise the document/vision/media paths.

## Tasks

1. **Inventory.** `hermes tools list` — record which toolsets are enabled. Disable one
   you do not use this week; note the prompt-size effect (`hermes prompt-size`).
2. **Scoped run.** Same question twice: once `-t web`, once with all toolsets. Compare
   answers, latency, and any wrong-tool detours you observe in the transcript.
3. **Escalation ladder.** Pick a factual research question:
   - `web_search` it → note snippets and URLs.
   - `web_extract` the top URL → note what the clean markdown gained.
   - Find one JS-heavy page and let the browser read it — the only step that works there.
4. **Document extraction.** Feed the agent a real PDF (a paper or report). Ask for a
   structured summary with page references. Then try a scanned PDF — observe the
   image-only failure, re-run via vision.
5. **Vision.** Send the agent a screenshot (CLI paste or Telegram photo) and ask a
   question answerable only from pixels (e.g. "what is the error banner saying?").
6. **Computer use status.** `hermes computer-use status` — if the driver is installed,
   run `hermes computer-use doctor` and read the check matrix. Do not drive the desktop
   yet; that lands with the security chapter.

## Verification checklist

- [ ] One toolset disabled, prompt-size delta measured.
- [ ] Escalation ladder demonstrated with a real question (all three steps).
- [ ] Text-layer PDF extracted with citations; scanned PDF correctly routed to vision.
- [ ] Vision question answered that was impossible from text alone.
