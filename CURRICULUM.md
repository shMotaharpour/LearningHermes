# CURRICULUM.md — سرفصل کامل LearningHermes

سرفصل مرجع (canonical) برای LearningHermes — دوره‌ای پروژه‌محور که یک مهندس کارآزموده را از
«کاربر agent» به **Senior Applied AI Engineer** می‌رساند و Hermes Agent وسیلهٔ این مسیر است.
هر فصل به (الف) شایستگی‌هایی که از آگهی‌های شغلی واقعی استخراج شده و (ب) قابلیت‌های Hermes
که در برابر مستندات رسمی و CLI زنده راستی‌آزمایی شده، نگاشت می‌شود.

- شواهد بازار کار: `docs/research/jobs/` (آگهی‌ها، سرچ‌ها، ledger)
- شواهد قابلیت‌های Hermes: `docs/research/hermes/` (snapshot ای از llms.txt، خروجی‌های verified از CLI)
- قانون به‌روزرسانی: هر تغییر ساختاری در فصل‌ها باید هم‌زمان در این فایل، `README.md` ریشه و
  `scripts/validate_course.py` اعمال شود.

## پروفایل نقش هدف (Target Role)

جمع‌بندی از بیش از ۲۰ آگهی در پنج خانوادهٔ شغلی (ببینید `docs/research/jobs/`):
Senior Applied AI Engineer، AI/Automation Engineer، AI Agent Engineer،
Forward Deployed Engineer، LLM Quality/Evaluation Engineer.

خوشه‌های تکرارشوندهٔ نیازمندی‌ها به ترتیب فراوانی مشاهده‌شده:

1. **Shipping و DevOps** — deploy سیستم‌های production، Docker/K8s، CI/CD.
2. **Evaluation و observability** — evals، ردیابی regression، metrics، tracing، monitoring.
3. **Orchestration ای agentic** — ساخت و بهره‌برداری از LLM agentها، workflowهای چندمرحله‌ای، tool use.
4. **یکپارچه‌سازی API و سیستم‌ها** — REST API، پلتفرم‌های enterprise، data pipeline.
5. **RAG و context engineering** — embedding، chunking، retrieval، grounding، context window.
6. **امنیت و governance** — مدیریت secrets، جریان‌های approval، حریم داده، compliance.
7. **بهینه‌سازی هزینه و کارایی** — model routing، caching، بودجهٔ latency.
8. **Prompt و context engineering** — system prompt، context file، structured output.
9. **مهارت‌های stakeholder و محصول** — تبدیل نیاز کسب‌وکار به قابلیت agent.
10. **پلتفرم‌های workflow automation** — jobهای زمان‌بندی‌شده، triggerهای رویدادی، hubهای یکپارچه‌سازی.

این دوره هر خوشه را عملی تدریس می‌کند: کار را *با* یک agent، روی ماشین واقعی و با ذخیرهٔ
شواهد در `docs/research/` انجام می‌دهید.

## ساختار دوره — ۵ بخش، ۱۶ فصل

### بخش I — Foundations (شناخت ماشین)

| فصل | دایرکتوری | دامنه | شایستگی شغلی اصلی |
|----|-----------|-------|------------------------|
| 01 | `chapters/01-agent-foundations/` | agent چیست؛ معماری Hermes (agent loop، tools، gateway)؛ install؛ اولین sessionها؛ `hermes doctor` | Agent orchestration |
| 02 | `chapters/02-configuration-models/` | `config.yaml` در برابر `.env`؛ providerها و modelها؛ aliasها؛ Mixture of Agents؛ fallback providerها؛ credential poolها؛ local modelها | بهینه‌سازی هزینه، model routing |
| 03 | `chapters/03-context-memory/` | Context fileها (AGENTS.md، SOUL.md، USER.md، MEMORY.md)؛ سیستم memory و providerهای آن؛ context referenceها؛ compression و caching | Prompt/context engineering، مهارت‌های مجاور RAG |

### بخش II — Operating the Agent (استفادهٔ روزمره)

| فصل | دایرکتوری | دامنه | شایستگی شغلی اصلی |
|----|-----------|-------|------------------------|
| 04 | `chapters/04-cli-sessions-surfaces/` | CLI و slash commandها؛ TUI؛ desktop app؛ dashboard؛ چرخهٔ session (resume، search، export)؛ checkpoint و rollback | بهره‌وری توسعه‌دهنده، مدیریت incident |
| 05 | `chapters/05-tools-capabilities/` | Toolsetها؛ web search/extract؛ browser automation؛ computer use؛ vision؛ document extraction؛ رسانه (image generation، TTS، voice) | Tool-calling و integration |
| 06 | `chapters/06-messaging-gateway/` | معماری gateway؛ راه‌اندازی Telegram/Discord/Slack/WhatsApp؛ deliverable mode؛ voice mode؛ gatewayهای multi-profile | Integration، تحویل رو به ذی‌نفعان |

### بخش III — Automation Engineering (کاری که خودش اجرا می‌شود)

| فصل | دایرکتوری | دامنه | شایستگی شغلی اصلی |
|----|-----------|-------|------------------------|
| 07 | `chapters/07-cron-scheduled-workflows/` | Cron jobها (LLM دار و script-only)؛ scheduleها؛ targetهای تحویل؛ notepad و continuity؛ cron internals و troubleshooting؛ heartbeat و recurring loop | پلتفرم‌های workflow automation |
| 08 | `chapters/08-event-driven-automation/` | Webhookها (GitHub و generic)؛ سیستم hooks؛ `hermes send` از script/CI؛ Microsoft Graph listener؛ automation blueprintها | یکپارچه‌سازی event-driven |
| 09 | `chapters/09-multi-agent-orchestration/` | subagentهای `delegate_task`؛ subagent lifecycle API؛ kanban multi-agent؛ rosterهای bot mode؛ A2A؛ git worktree؛ batch processing | Agentic orchestration (چند agentی) |

### بخش IV — Building & Extending (شخصی‌سازی پلتفرم)

| فصل | دایرکتوری | دامنه | شایستگی شغلی اصلی |
|----|-----------|-------|------------------------|
| 10 | `chapters/10-skills-engineering/` | فرمت SKILL.md؛ progressive disclosure؛ skillهای پروژه‌ای (`.hermes/skills` + trust)؛ curator؛ publish؛ audit/diff ای skill | مهندسی دانش، tooling داخلی |
| 11 | `chapters/11-mcp-integration/` | افزودن/config/فیلتر MCP؛ نصب از catalog؛ `hermes mcp serve`؛ MCP ای OAuth؛ ساخت و تست MCP server | Tool-calling، MCP، integration |
| 12 | `chapters/12-plugins-and-apis/` | سیستم plugin (tool، hook، secret source، provider plugin)؛ API server سازگار با OpenAI؛ ACP برای editorها؛ `hermes proxy`؛ embed کردن به‌صورت Python library | API و platform engineering |
| 13 | `chapters/13-shipping-agent-products/` | Terminal backendها (local، Docker، SSH، Daytona، Modal)؛ workflow ی GitHub PR با agent؛ یکپارچگی CI/CD؛ profile distribution؛ checklist ی deploy | Shipping و DevOps |

### بخش V — Production Engineering (رسیدن به سطح senior)

| فصل | دایرکتوری | دامنه | شایستگی شغلی اصلی |
|----|-----------|-------|------------------------|
| 14 | `chapters/14-evals-observability/` | ارزیابی کارِ agent؛ trajectory format و replay؛ `hermes insights`/`monitoring`؛ logها؛ regression testing ی رفتار agent؛ الگوهای LLM-as-judge | Evaluation و observability |
| 15 | `chapters/15-security-cost-governance/` | مدل امنیتی و approvalها؛ secrets (Bitwarden، 1Password، انضباط `.env`)؛ egress iron-proxy؛ managed scope؛ provider routing و کنترل هزینه | امنیت و governance، بهینه‌سازی هزینه |
| 16 | `chapters/16-capstone-senior-portfolio/` | Capstone: اتوماسیون یک workflow ی enterprise از ابتدا تا انتها با Hermes؛ بسته‌بندی portfolio؛ نگاشت شایستگی به شواهد برای interview | همهٔ موارد بالا، در کنار هم |

## مدل پیشرفت (Progression)

```
بخش I   -> Agent Operator       (یک agent در سطح production را می‌توانی اجرا و هدایت کنی)
بخش II  -> Agent Power User     (آن را روی همهٔ surfaceها، toolها و پلتفرم‌های پیام‌رسان بهره‌برداری می‌کنی)
بخش III -> Automation Engineer (workflowها بدون حضور تو در حلقه اجرا می‌شوند)
بخش IV  -> Agent Developer     (پلتفرم را گسترش می‌دهی: skill، MCP، plugin، API)
بخش V   -> Senior Applied AI Engineer (سیستم را ship، اندازه‌گیری، امن و پشتیبانی می‌کنی)
```

## قرارداد فصل (Chapter Contract)

هر فصل همین قرارداد را دنبال می‌کند (با `scripts/validate_course.py` چک می‌شود):

1. `README.md` با این سکشن‌ها: `## Why this matters (job link)`، `## Concepts`،
   `## Verified commands`، `## Common pitfalls`، `## Exercises` (اشاره به فایل تمرین).
2. یک فایل تمرین برای هر فصل: `exercises/exNN-<slug>.md` شامل هدف، taskها و
   checklist ی راستی‌آزمایی.
3. دستورات فصل باید در برابر رفتار واقعی Hermes راستی‌آزمایی شوند؛ شواهد خام زیر
   `docs/research/hermes/` ذخیره و از داخل فصل به آن ارجاع داده شود.
4. بدون نثر پرکننده. مفهوم ← دستور دقیق ← تمرین.

## مدل برنچ دوزبانه

- `english` — برنچ مبنا، محتوای مرجع، فقط انگلیسی.
- `farsi` — ترجمهٔ کامل؛ نثر فارسی با حفظ اصطلاحات متداول و تخصصی انگلیسی
  (agent، tool، skill، session، cron، webhook، eval، ...)؛ بلوک‌های کد، دستورات،
  pathها و کلیدهای frontmatter انگلیسی می‌مانند.
- هر دو برنچ درخت فایل یکسان دارند؛ `scripts/validate_course.py --root X --other Y`
  برابری ساختاری را چک می‌کند (فایل‌های یکسان، تعداد code block برابر در هر فایل).
- قواعد `AGENTS.md` ی مخصوص هر برنچ: در `english` همهٔ فایل‌ها فقط انگلیسی؛ در `farsi`
  نثر فارسی برای محتوای آموزشی `.md` الزامی است.

## منابع اصلی (Sources of Truth)

- ایندکس مستندات Hermes: https://hermes-agent.nousresearch.com/docs/llms.txt
- ریپوی Hermes: https://github.com/NousResearch/hermes-agent
- شواهد بازار کار: `docs/research/jobs/ledger.json` و فایل‌های هم‌مسیر
