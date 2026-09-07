# Chapter 03 — Context and Memory

## Why this matters (job link)

RAG and context engineering show up in nearly every applied AI posting: Paramount wants
"chunking and retrieval optimization... hallucination mitigation and grounding techniques"
(`docs/research/jobs/source-01.md`); 100ms wants "retrieval strategies... ensure agent
behaviour aligns with user expectations" (`docs/research/jobs/source-05.md`). Before vector
databases, master the simpler truth: **the agent's context window is the retrieval system.**
Hermes implements a complete context stack — project files, memory, profiles, references,
compression — and engineers it well. This chapter teaches you to reason about every token
in the prompt, which is the skill RAG design generalizes.

## Concepts

**The four context files** (who writes them, when the agent sees them):

| File | Written by | Role |
|---|---|---|
| `SOUL.md` | you (global) | identity, voice, standing rules — prepended to every session |
| `USER.md` | agent | durable facts about the user across sessions |
| `MEMORY.md` | agent | session-independent notes the agent saves to stay consistent |
| `AGENTS.md` / `.hermes.md` / `CLAUDE.md` | project authors | repo-specific rules, injected when working in that project |

This course repo ships its own `AGENTS.md` — that file *is* chapter 03 applied: any agent
entering the repo inherits the authoring contract without being told twice.

**Prompt budget is measurable.** `hermes prompt-size --json` (verified, evidence b8) breaks
the fixed system prompt into layers: `system_prompt` (~28.7K chars), `skills_index`
(~10.6K), `memory` (~3.6K), `user_profile` (~1.4K), plus per-tool JSON schemas. Two
platforms differ slightly (CLI vs telegram counts differ by ~280 chars). This is the tool
that answers "why did my agent get dumber?" — layers compete for the same window.

**Session memory vs persistent memory.** Within a session, context grows message by
message and Hermes compresses when pressure rises (compression preserves a summary, drops
verbatim history). Across sessions, `MEMORY.md`/`USER.md` give continuity. External memory
provider plugins (honcho, mem0, hindsight, byterover, ...) replace the built-in store when
you need cross-profile or structured memory (`hermes memory status` lists them — verified).

**Context references.** `@`-syntax attaches material inline: files, folders, git diffs,
URLs. Prefer an explicit reference over hoping the agent re-reads a file.

**Skills are lazy context.** The skills *index* rides in every prompt (~10K chars here);
skill *bodies* load on demand. This progressive-disclosure pattern is why a hundred
installed skills don't wreck the window — the same trade RAG makes between index and
payload.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b8-context-memory.txt`
(live `memory status`, `prompt-size` JSON, `~/.hermes/` layout).

## Verified commands

Measure your prompt budget:

```bash
hermes prompt-size                  # human-readable breakdown
hermes prompt-size --json           # machine-readable layers
hermes prompt-size --platform telegram --json   # platform-specific delta
```

Memory subsystem:

```bash
hermes memory status     # injection on/off, active provider, installed plugins
hermes memory setup      # configure an external provider
hermes memory off        # disable memory injection (privacy mode)
```

Session store (the memory of record):

```bash
hermes sessions stats    # verified: 21 sessions, 5972 messages, 29.5 MB DB
hermes sessions list     # titles + last-active + IDs
hermes sessions browse   # interactive picker, search, resume
hermes sessions export   # JSONL / Markdown export for analysis
```

Config-file discipline:

```bash
hermes config path                 # settings live here, not in the project
ls ~/.hermes/                      # observe: SOUL.md, AGENTS.md, config.yaml, state DB...
```

## Common pitfalls

- **Stuffing MEMORY.md.** Memory injects into *every* future session; a bloated memory
  file taxes all of them. Prune ruthlessly; delete what re-derives from a quick lookup.
- **Project rules in global SOUL.md.** Repo conventions belong in the repo's `AGENTS.md`;
  global identity rules in `SOUL.md`. Cross-contamination makes the agent misbehave in
  unrelated projects.
- **Assuming the agent remembers last week.** Without memory writes, each session starts
  blank. If continuity matters, tell the agent to save the fact, or script the memory tool.
- **Ignoring prompt-size after installs.** Each MCP server, toolset, and skill index grows
  the fixed budget. After adding integrations, re-measure.
- **Confusing compression with memory.** Compression is lossy, in-session, emergency
  relief. It is not a substitute for writing durable facts to memory.

## Exercises

Work through `exercises/ex03-context-memory.md`. Verification: prompt-size JSON understood
layer by layer, a project AGENTS.md authored, one deliberate memory write observed.
