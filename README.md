# LearningHermes

A structured, book-style course for mastering [Hermes Agent](https://github.com/NousResearch/hermes-agent) — from first steps to building production products. Written for AI Engineers who want to use Hermes as their daily autonomous agent.

## Goals

- **Learn**: a complete reference covering every Hermes capability, step by step.
- **Practice**: each chapter has hands-on exercises with real commands.
- **Build**: capstone projects that ship real products with Hermes.

## Repository Layout

```
chapters/
  01-foundations/         # What Hermes is, install, config, sessions, models
  02-daily-usage/         # Slash commands, messaging (Telegram), profiles, skills
  03-agentic-workflow/    # Agentic prompting, tools, debugging, multi-agent
  04-automation/          # Cron jobs, webhooks, monitoring, scheduled briefings
  05-building-products/   # Building/shipping real projects: MVP -> deploy, CI/CD, GitHub
  06-mastery/             # Skills authoring, MCP, plugin/extension, advanced patterns
examples/                 # Runnable sample code / configs referenced by chapters
exercises/                # Hands-on practice tasks per chapter
assets/                   # Diagrams, screenshots
docs/research/            # Raw research notes that feed chapter drafts
```

## How to Read This Course

- Chapters are numbered and self-contained; read `01` first, then any order.
- Every chapter ends with **Exercises** that live in `exercises/`.
- Code blocks are exact, verified commands — prefer copy-paste over retyping.

## Contribution / Workflow

- All files in this repo are **English only**.
- Chapter drafts: write directly in `chapters/NN-topic/`.
- Verify every command against real Hermes behavior before publishing (run it, paste output into `docs/research/` as evidence).
- Keep chapters concise: concept → exact commands → exercise. No marketing prose.
- Commit style: `chNN: <short description>` (e.g. `ch02: add Telegram slash-command reference`).
- Build: this is a Markdown book repo — no build step. Validate links with `grep -rL` spot checks before release.

## Sources of Truth

- Official docs: https://hermes-agent.nousresearch.com/docs/llms.txt (always current)
- Source repo: https://github.com/NousResearch/hermes-agent
