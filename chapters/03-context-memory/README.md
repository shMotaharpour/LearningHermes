# Chapter 03 — Context and Memory

## Why this matters (job link)

RAG and context engineering appear in nearly every applied AI posting: Paramount wants
"chunking and retrieval optimization... hallucination mitigation and grounding techniques"
(`docs/research/jobs/source-01.md`); 100ms wants "retrieval strategies... ensure agent
behaviour aligns with user expectations" (`docs/research/jobs/source-05.md`). Before vector
databases, master the simpler truth: **the agent's context window is the retrieval
system.** Hermes implements a complete context stack — context files, persistent memory,
memory providers, references, compression, caching — and this chapter teaches you to reason
about every token in the prompt. That skill generalizes directly to RAG design: what to
inject, what to index, what to retrieve, what to drop.

## Concepts

### The four context files — who writes what, when it's seen

| File | Written by | Seen when | Role |
|---|---|---|---|
| `SOUL.md` | you (global) | every session, all projects | identity, voice, standing rules |
| `USER.md` | agent | every session | durable facts about the user |
| `MEMORY.md` | agent | every session | agent's own notes for cross-session consistency |
| `AGENTS.md` / `.hermes.md` / `CLAUDE.md` | project authors | sessions in that project only | repo rules, conventions, commands |

This course repo ships `chapters/NN-*/AGENTS.md` files — that *is* chapter 03 applied:
any agent entering a chapter directory inherits the authoring contract without being told
twice. Placement discipline: **repo conventions in the repo, identity in SOUL.md, facts in
memory.** Cross-contamination (project rules in SOUL.md) makes the agent misbehave
everywhere else.

### The prompt budget, measured

`hermes prompt-size --json` (verified live, evidence b8) decomposes the fixed system
prompt on this machine:

```
system_prompt   28,738 chars   <- identity + rules + tool docs
skills_index    10,627 chars   <- one line per installed skill (~90 skills)
memory           3,556 chars   <- MEMORY.md + USER.md injection
user_profile     1,426 chars
tools (count 21) + JSON schemas
```

Platform matters: telegram measures ~280 chars less system prompt than CLI (platform
layer differs). Two consequences:

1. **Everything competes for one window.** Installing another MCP server or 20 more
   skills taxes every future session. Re-measure after integrations.
2. **"My agent got dumber" is usually arithmetic.** A bloated memory file or skills index
   crowds out room for the actual task. Diagnose with `prompt-size`, not superstition.

### Session compression vs persistent memory

Within a session, context grows every message; under pressure Hermes **compresses** —
replacing verbatim history with a summary. Compression is lossy, in-session, emergency
relief. It never substitutes for writing durable facts to memory. Across sessions,
`MEMORY.md`/`USER.md` carry continuity. External **memory provider plugins** (honcho,
mem0, hindsight, byterover, holographic, openviking — verified via `hermes memory status`)
replace the built-in store when you need structured or cross-profile memory.

### Skills are lazy context

The skills *index* rides in every prompt (~10.6K chars); skill *bodies* load only when
used (progressive disclosure). The same economics govern RAG: index small, payload on
demand. Internalize this pattern here; Chapter 10 exploits it.

### Context references

`@`-syntax attaches material inline — files, folders, git diffs, URLs — instead of hoping
the agent re-reads the right file. Explicit beats ambient: reference the exact thing.

### Prompt caching

Providers cache unchanged prompt prefixes; Hermes preserves cache stability by not
reordering the system prompt mid-session. Practical rules: don't churn global context
files mid-conversation, don't toggle toolsets between messages, batch related questions
into one session. Cache hits are the difference between full-price and discount tokens.

**Evidence:** `docs/research/hermes/cli-evidence-2026-09-07-b8-context-memory.txt`
(live `memory status` with provider plugins listed, full `prompt-size --json` for CLI and
telegram, `~/.hermes/` directory layout).

## Verified commands

Measure the prompt budget:

```bash
hermes prompt-size                    # human-readable layer breakdown
hermes prompt-size --json             # machine-readable
hermes prompt-size --platform telegram --json   # platform delta (verified: ~280 chars less)
```

Memory subsystem (verified output):

```
$ hermes memory status
  Built-in (MEMORY.md / USER.md):
    Memory injection:   enabled ✓
    User profile:       enabled ✓
    Memory tool:        enabled ✓
  Provider:  (none — built-in only)
  Installed plugins: byterover, hindsight, holographic ...
```

```bash
hermes memory setup        # configure an external provider
hermes memory off          # privacy mode: no memory injection
```

Session store (the memory of record):

```bash
hermes sessions stats      # verified: 21 sessions, 5972 messages, 29.5 MB
hermes sessions list       # titles + last-active + IDs
hermes sessions browse     # interactive search + resume
hermes sessions export     # JSONL/Markdown export for analysis
```

## Common pitfalls

- **Stuffing MEMORY.md.** Memory injects into every future session; bloat taxes all of
  them. Prune ruthlessly; delete anything re-derivable from a quick lookup.
- **Project rules in global files.** SOUL.md is for identity, not for `pytest` conventions
  of one repo. Repo rules live in the repo.
- **Assuming the agent remembers last week.** Without an explicit memory write, sessions
  start blank. Make the agent save facts, or script the memory tool.
- **Ignoring prompt-size after installs.** Every MCP server, toolset, and skill grows the
  fixed budget. Measure before/after every integration change.
- **Confusing compression with memory.** Compressed summaries are lossy session glue, not
  durable knowledge.
- **Mid-session context churn.** Editing SOUL.md or toggling toolsets mid-conversation
  breaks prompt caching and re-prices the whole session.

## Exercises

Work through `exercises/ex03-context-memory.md`. Verification: prompt-size JSON explained
layer by layer, a project AGENTS.md authored and obeyed, one memory write + one prune
measured.
