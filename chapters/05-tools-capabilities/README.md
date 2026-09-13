# Chapter 05 — Tools and Capabilities

> **Verified:** 2026-09-12 · Hermes Agent v0.20.6 (2026.8.27) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Tool calling is the load-bearing skill in agent postings: Reflection wants engineers
"orchestrating LLM workflows, integrating with enterprise infrastructure"
(`docs/research/jobs/source-04.md`); 100ms wants agent builders who "experiment with
prompting techniques, fine-tuning datasets, retrieval strategies, and model
configurations" (`docs/research/jobs/source-05.md`); Adventus hires for "LLM-powered
applications, workflow automation, API integrations" (`docs/research/jobs/extract-round2.json`).
The applied skill is knowing *what tools exist, what they cost, when they fail, and how to
scope them per task*. This chapter covers Hermes' built-in capability surface: toolsets,
web search/extract, browser, computer use, vision, document extraction, media.

## Concepts

### Toolset taxonomy

Hermes groups capabilities into toolsets (verified via `hermes tools --help`: "Built-in
toolsets use plain names (e.g. web, memory). MCP tools use server:tool notation"). The
daily set:

| Toolset | What it gives the agent | Failure mode to know |
|---|---|---|
| `terminal` | shell, files, processes | destructive commands hit approval flow (Ch 15) |
| `web` | web_search + web_extract | JS-heavy pages return skeletons; use browser instead |
| `browser` | real Chromium via CDP | slow, stateful; close profiles you lock |
| `computer_use` | OS-level mouse/keyboard | needs cua-driver installed (`hermes computer-use install`) |
| `memory` | persistent memory read/write | injected into every future session — write carefully |
| media | image gen, TTS | provider quotas |

Scoping is a first-class flag (`-t terminal,web`) and a cost tool: fewer toolsets →
smaller prompt → fewer wrong-tool detours.

### Web: search vs extract vs browser

Three escalating ways to touch the web (all verified in this course's own workflow):

1. **`web_search`** — query → ranked results with snippets. Cheap, first probe.
2. **`web_extract`** — URL → clean markdown. Works for static pages, blogs, *and PDFs*
   (arxiv papers extract directly). Character-budgeted; huge pages save full text to disk.
3. **Browser** — real Chromium: forms, clicks, JS-heavy apps, screenshots. The agent
   drives it via CDP; cloud-browser providers plug in as alternatives.

Decision rule: search first, extract second, browser last (browser is the slow, expensive
escalation for JS-walled content).

### Computer use

`hermes computer-use install|status|doctor|permissions` (verified) manages the cua-driver
binary that backs the `computer_use` toolset — OS-level control of mouse, keyboard,
screenshots, desktop apps. Use it for the last mile: native apps with no API, legacy
desktop software. It is the highest-risk toolset (it touches the real desktop), so it
pairs with the approval discipline of Chapter 15.

### Vision and document extraction

Vision is multimodal input: paste an image (CLI) or send a photo (Telegram) and the model
reads it — charts, screenshots, photos of whiteboards. Document extraction runs inside
`read_file`: PDFs, Office documents, notebooks auto-convert to text. Know the boundary:
scanned PDFs are images — they need the vision path, not the text-extraction path.

### Media generation

Image generation (FAL.ai models), TTS, and voice transcription are provider-backed
toolsets. They are quotable, low-context tools — good first delegation targets for agents
operating on your behalf.

### The delegation pattern for capabilities

The real skill this chapter builds: **matching capability to task with explicit scope.**

- "Summarize this PDF" → document extraction, no browser.
- "Check this dashboard daily" → browser + cron (Chapters 07).
- "Fill this government form" → computer use + approvals.
- "Find who cited this paper" → web search + extract loop.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt`
(browser/computer-use subcommands, TTY constraint), and this course's own research files
in `docs/research/jobs/extract-round2.json` — produced by exactly the search→extract
pipeline described here.

## Verified commands

Toolset management:

```bash
hermes tools list              # every tool + enabled/disabled status
hermes tools --summary         # enabled tools per platform (human check)
hermes tools enable browser    # opt into a toolset
hermes tools disable computer_use   # opt out — risk reduction
```

Computer use driver:

```bash
hermes computer-use status     # is cua-driver installed?
hermes computer-use install    # fetch/run installer
hermes computer-use doctor     # health matrix: TCC, bundle, platform checks
```

Browser helpers:

```bash
hermes browser close-profile   # release a locked real-profile browser (destructive: unsaved tabs)
```

Per-run scoping (verified flag):

```bash
hermes chat -q "Research X and summarize" -t web
hermes chat -q "Fix the failing test" -t terminal,memory
```

## Common pitfalls

- **Always-on everything.** Enabling all toolsets for all sessions bloats the prompt and
  raises wrong-tool error rates. Scope per task.
- **Browser for what extract handles.** A static docs page does not need Chromium. The
  escalation ladder exists for a reason — each step costs 10× more.
- **Computer use on the wrong machine.** It drives the *real* desktop. On a shared or
  production box, that is a security incident waiting to happen (Chapter 15).
- **Treating scanned PDFs as text.** Extraction returns empty/garbage on image-only PDFs;
  route them to vision.
- **Forgetting MCP is not built-in.** External tools come from MCP servers
  (`server:tool` notation) — Chapter 11. Debugging an "external tool missing" as if it
  were a toolset problem wastes an hour.
- **Locked browser profiles.** A real-profile browser session locks the profile; close it
  (`hermes browser close-profile`) before reusing the profile manually.

## Exercises

Work through `exercises/ex05-tools-capabilities.md`. Verification: scoped run executed,
escalation ladder demonstrated (search→extract→browser), one document extracted, one
vision read.
