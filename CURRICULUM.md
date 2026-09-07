# LearningHermes Curriculum

The canonical syllabus for LearningHermes — a project-based course that takes a working
engineer from "agent user" to **Senior Applied AI Engineer** using Hermes Agent as the
vehicle. Every chapter maps to (a) competencies extracted from real job postings and
(b) Hermes features verified against the official docs and live CLI.

- Job-market evidence: `docs/research/jobs/` (postings, searches, extraction ledger)
- Hermes feature evidence: `docs/research/hermes/` (llms.txt snapshot, verified CLI outputs)
- Update rule: any structural change to chapters must be reflected here, in the root
  `README.md`, and validated by `scripts/validate_course.py`.

## Target Role Profile

Compiled from 20+ postings across five job families (see `docs/research/jobs/`):
Senior Applied AI Engineer, AI/Automation Engineer, AI Agent Engineer, Forward Deployed
Engineer, LLM Quality/Evaluation Engineer.

Recurring requirement clusters, ordered by observed frequency:

1. **Shipping & DevOps** — deploy production systems, Docker/K8s, CI/CD.
2. **Evaluation & observability** — evals, regression tracking, metrics, tracing, monitoring.
3. **Agentic orchestration** — build/operate LLM agents, multi-step workflows, tool use.
4. **API & systems integration** — REST APIs, enterprise platforms, data pipelines.
5. **RAG & context engineering** — embeddings, chunking, retrieval, grounding, context windows.
6. **Security & governance** — secrets handling, approval flows, data privacy, compliance.
7. **Cost & performance optimization** — model routing, caching, latency budgets.
8. **Prompt & context engineering** — system prompts, context files, structured output.
9. **Stakeholder/product skills** — translate business needs into agent capabilities.
10. **Workflow automation platforms** — scheduled jobs, event triggers, integration hubs.

The course teaches each cluster hands-on: you do the work *with* an agent, on a real
machine, with evidence saved under `docs/research/`.

## Course Structure — 5 parts, 16 chapters

### Part I — Foundations (know the machine)

| Ch | Directory | Scope | Primary job competency |
|----|-----------|-------|------------------------|
| 01 | `chapters/01-agent-foundations/` | What an AI agent is; Hermes architecture (agent loop, tools, gateway); install; first sessions; `hermes doctor` | Agent orchestration |
| 02 | `chapters/02-configuration-models/` | `config.yaml` vs `.env`; providers & models; aliases; Mixture of Agents; fallback providers; credential pools; local models | Cost optimization, model routing |
| 03 | `chapters/03-context-memory/` | Context files (AGENTS.md, SOUL.md, USER.md, MEMORY.md); memory system & providers; context references; compression & caching | Prompt/context engineering, RAG-adjacent context skills |

### Part II — Operating the Agent (daily driver)

| Ch | Directory | Scope | Primary job competency |
|----|-----------|-------|------------------------|
| 04 | `chapters/04-cli-sessions-surfaces/` | CLI & slash commands; TUI; desktop app; dashboard; session lifecycle (resume, search, export); checkpoints & rollback | Developer productivity, incident handling |
| 05 | `chapters/05-tools-capabilities/` | Toolsets; web search/extract; browser automation; computer use; vision; document extraction; media (image gen, TTS, voice) | Tool-calling & integration |
| 06 | `chapters/06-messaging-gateway/` | Gateway architecture; Telegram/Discord/Slack/WhatsApp setups; deliverable mode; voice mode; multi-profile gateways | Integration, stakeholder-facing delivery |

### Part III — Automation Engineering (make it run itself)

| Ch | Directory | Scope | Primary job competency |
|----|-----------|-------|------------------------|
| 07 | `chapters/07-cron-scheduled-workflows/` | Cron jobs (LLM & script-only); schedules; delivery targets; notepads & continuity; cron internals & troubleshooting; heartbeats & recurring loops | Workflow automation platforms |
| 08 | `chapters/08-event-driven-automation/` | Webhooks (GitHub & generic); hooks system; `hermes send` from scripts/CI; Microsoft Graph listener; automation blueprints | Event-driven integration |
| 09 | `chapters/09-multi-agent-orchestration/` | `delegate_task` subagents; subagent lifecycle API; kanban multi-agent; bot mode rosters; A2A; git worktrees; batch processing | Agentic orchestration (multi-agent) |

### Part IV — Building & Extending (make it yours)

| Ch | Directory | Scope | Primary job competency |
|----|-----------|-------|------------------------|
| 10 | `chapters/10-skills-engineering/` | SKILL.md format; progressive disclosure; project skills (`.hermes/skills` + trust); curator; publishing; skill audit/diff | Knowledge engineering, internal tooling |
| 11 | `chapters/11-mcp-integration/` | MCP add/config/filter; catalog installs; `hermes mcp serve`; OAuth MCP; building & testing MCP servers | Tool-calling, MCP, integration |
| 12 | `chapters/12-plugins-and-apis/` | Plugin system (tools, hooks, secret sources, provider plugins); OpenAI-compatible API server; ACP for editors; `hermes proxy`; Python library embedding | API & platform engineering |
| 13 | `chapters/13-shipping-agent-products/` | Terminal backends (local, Docker, SSH, Daytona, Modal); GitHub PR workflow via agent; CI/CD integration; profile distributions; deployment checklist | Shipping & DevOps |

### Part V — Production Engineering (make it senior)

| Ch | Directory | Scope | Primary job competency |
|----|-----------|-------|------------------------|
| 14 | `chapters/14-evals-observability/` | Evaluating agent work; trajectory format & replay; `hermes insights`/`monitoring`; logs; regression testing agent behavior; LLM-as-judge patterns | Evaluation & observability |
| 15 | `chapters/15-security-cost-governance/` | Security model & approvals; secrets (Bitwarden, 1Password, .env discipline); egress iron-proxy; managed scope; provider routing & cost control | Security & governance, cost optimization |
| 16 | `chapters/16-capstone-senior-portfolio/` | Capstone: end-to-end enterprise workflow automation built with Hermes; portfolio packaging; competency-to-evidence mapping for interviews | Everything above, synthesized |

## Progression Model

```
Part I   -> Agent Operator      (you can run and steer a production-grade agent)
Part II  -> Agent Power User    (you operate it across surfaces, tools, and chat platforms)
Part III -> Automation Engineer (workflows run without you in the loop)
Part IV  -> Agent Developer     (you extend the platform: skills, MCP, plugins, APIs)
Part V   -> Senior Applied AI Engineer (you ship, measure, secure, and defend the system)
```

## Chapter Contract

Every chapter follows the same contract (enforced by `scripts/validate_course.py`):

1. `README.md` with sections: `## Why this matters (job link)`, `## Concepts`,
   `## Verified commands`, `## Common pitfalls`, `## Exercises` (pointer to the exercise file).
2. One exercise file per chapter: `exercises/chNN-<slug>.md` with objective, tasks, and a
   verification checklist.
3. Commands in chapters must be verified against real Hermes behavior; raw evidence is
   saved under `docs/research/hermes/` and referenced from the chapter.
4. No filler prose. Concept → exact commands → exercise.

## Bilingual Branch Model

- `english` — base branch, authoritative content, English only.
- `farsi` — full translation; Persian prose with standard English technical terms
  (agent, tool, skill, session, cron, webhook, eval, …) left untranslated; code blocks,
  commands, paths, and frontmatter keys stay English.
- Both branches carry identical file trees; `scripts/validate_course.py --root X --other Y`
  checks structural parity (same files, same code-block counts per file).
- Branch-specific `AGENTS.md` rules: on `english`, all repo files are English only;
  on `farsi`, Persian prose is required for `.md` teaching content.

## Sources of Truth

- Hermes docs index: https://hermes-agent.nousresearch.com/docs/llms.txt
- Hermes repo: https://github.com/NousResearch/hermes-agent
- Job evidence: `docs/research/jobs/ledger.json` and sibling files
