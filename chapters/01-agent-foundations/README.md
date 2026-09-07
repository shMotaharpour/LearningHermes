# فصل ۰۱ — پایه‌های Agent

## Why this matters (job link)

هر آگهی «Senior Applied AI Engineer» فرض می‌کند شما می‌توانید یک agent مستقل را عملیاتی
*به‌کار بگیرید*، نه فقط با یک مدل گفتگو کنید. آگهی Forward Deployed Engineer شرکت
Reflection: «ساخت سیستم‌های agentic با مدل‌های روز، orchestration ی workflowهای LLM ...
و deploy سیستم‌های قابل‌اتکا در production» (`docs/research/jobs/source-04.md`). شرکت
100ms: «ساخت و نگهداری workflowهای agentic ... تعریف و پیاده‌سازی metricهای کارایی LLM»
(`docs/research/jobs/source-05.md`). دیتابریکس: «ساخت feature و اجرای سیستم‌های
end-to-end» (`docs/research/jobs/source-02.md`). قبل از orchestrate کردن agentها باید
ماشین را بشناسید: agent loop، toolها، toolsetها، تزریق context و state ی session. همه‌چیز
در این دوره — cron، MCP، multi-agent، evals — یک تغییرشکل از همین loop است.

## Concepts

### agent loop

یک chat completion فقط متن برمی‌گرداند؛ یک agent *action* برمی‌گرداند. هیرمس این loop را
اجرا می‌کند:

1. **سرهم‌کردن context.** System prompt (هویت + قواعد) + skills index + memory + پروفایل
   کاربر + schema ی toolها + تاریخچهٔ گفتگو. قابل اندازه‌گیری: `hermes prompt-size`.
2. **نوبت مدل.** مدل یا جواب می‌دهد یا tool call صادر می‌کند.
3. **اجرای tool.** هیرمس tool را واقعاً اجرا می‌کند — shell، فایل، شبکه — و خروجی را به
   مدل برمی‌گرداند.
4. **تکرار تا جواب.** مدل نتیجه را می‌بیند و دوباره تصمیم می‌گیرد. یک پیام کاربر می‌تواند
   ده‌ها tool call بDrive.

دو ویژگی این loop برای ادامهٔ مسیر حیاتی است:

- **state ی انباشتی.** tool callها سیستم واقعی را تغییر می‌دهند (فایل، repo، سرور).
  اشتباهات دقیقاً مثل باگ نرم‌افزاری انباشته می‌شوند — به همین دلیل checkpoint و approval
  وجود دارد (فصل‌های ۰۴ و ۱۵).
- **هزینه به‌ازای هر iteration.** هر iteration کل context را دوباره می‌فرستد. loopهای
  طولانی روی مدل گران یعنی پول واقعی؛ prompt caching (فصل ۰۳) و routing (فصل ۰۲) به‌خاطر
  همین وجود دارند.

### Toolset نه فقط tool

toolها در گروه‌های toolset عرضه می‌شوند: `terminal`، `web`، `memory`، `browser`،
`computer_use` و مجموعه‌های مخصوص هر پلتفرم. انتخاب per-run یک flag است:

```bash
hermes chat -q "..." -t terminal,web     # فقط این toolsetها load می‌شوند
```

toolset کمتر = prompt کوچک‌تر = حواس‌پرتی و هزینهٔ کمتر. `hermes tools list` (verified)
وضعیت همهٔ toolها را نشان می‌دهد؛ toolهای MCP با فرمت `server:tool` می‌آیند (فصل ۱۱).

### سه سطح کانفیگ

این تفکیک را حفظ باشید؛ نقضش رایج‌ترین خطای تازه‌کارهاست:

| سطح | مسیر | محتوا |
|---|---|---|
| تنظیمات | `~/.hermes/config.yaml` | هر چیزی که secret نیست |
| Secrets | `~/.hermes/.env` | فقط API key و token |
| کد | `~/.hermes/hermes-agent/` | برنامهٔ نصب‌شده |

Profile ها (`~/.hermes/profiles/<name>/`) همین چیدمان را برای instanceهای ایزوله تکرار
می‌کنند — config، session و memory مستقل (فصل‌های ۰۴ و ۰۹).

### Session ها

یک گفتگو = یک session: context، مدل و working directory مستقل خودش. sessionها در
`~/.hermes/state.db` (SQLite + جستجوی full-text) ماندگارند. یک استور واقعی برای این فصل
بررسی شد (evidence b3): `21 sessions, 5972 messages, 29.5 MB` — sessionهای CLI و Telegram
کنار هم در یک استور و قابل resume از هر surface.

### چرا هیرمس یک پلتفرم applied است

سه قابلیت او را از یک chat app جدا می‌کند و کل این دوره را سازمان می‌دهد:

1. **Skillها** — سندهای رویه‌ای که خود agent می‌سازد و on-demand لود می‌شوند (فصل ۱۰).
2. **Memory ی ماندگار** — هویت و factهایی که از session عبور می‌کنند (فصل ۰۳).
3. **Gateway** — همان هستهٔ agent روی ۲۱+ پلتفرم پیام‌رسان، cron و webhook (فصل‌های ۰۶–۰۸).

### نقشهٔ subcommand ها

`hermes --help` (verified در evidence batch 1) بیش از ۶۰ subcommand دارد. حفظ نکنید؛
گروه‌به‌گروه ناوبری کنید:

- **هسته:** `chat`، `model`، `moa`، `fallback`، `config`، `doctor`، `status`
- **session/داده:** `sessions`، `checkpoints`، `backup`، `insights`
- **اتوماسیون:** `cron`، `webhook`، `hooks`، `send`، `gateway`
- **multi-agent:** `kanban`، `peer`، delegate (درون-session)، `profile`
- **افزونه:** `skills`، `plugins`، `mcp`، `serve`، `acp`، `proxy`
- **امنیت:** `security`، `approvals`، `secrets`، `egress`، `auth`

هر گروه فصل مخصوص خودش را در ادامه دارد.

**شواهد این فصل:** `docs/research/hermes/cli-evidence-2026-09-07.txt`،
`docs/research/hermes/cli-evidence-2026-09-07-b1-foundations-core.txt`،
`docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt` (خروجی خام CLI،
Hermes v0.20.6، استور واقعی).

## Verified commands

نصب (Linux/macOS/WSL2):

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Health check و setup — خروجی `hermes doctor` یک پنل سلامت per-component رندر می‌کند
(evidence b7):

```bash
hermes doctor        # بررسی سلامت مؤلفه‌به‌مؤلفه
hermes setup         # ویزارد تعاملی: provider، کلید، پلتفرم
hermes status        # خلاصهٔ وضعیت مؤلفه‌ها (--all برای جزئیات)
```

اولین گفتگو — سه حالت، verified:

```bash
hermes               # چت تعاملی (surface پیش‌فرض)
hermes chat -q "What is 17*23?"    # one-shot: جواب می‌دهد و خارج می‌شود
hermes chat -q "Count files here, report the largest" -t terminal
                     # اجرا با toolset محدود — اجرای tool call را ببینید
```

درخت `--help` (نمونهٔ verified):

```
usage: hermes [-h] [--version] [-z PROMPT] [-m MODEL] [--provider PROVIDER]
              [-t TOOLSETS] [--resume SESSION] [--continue [SESSION_NAME]]
              [--worktree] [--skills SKILLS] [--safe-mode] [--tui] [--cli] ...
{chat,model,moa,fallback,worktree,browser,secrets,egress,migrate,gateway,
 proxy,lsp,setup,send,auth,status,cron,sync,webhook,peer,portal,kanban,
 project,hooks,doctor,security,approvals,backup,checkpoints,import,config,
 skills,plugins,curator,memory,tools,computer-use,mcp,sessions,insights,
 monitoring,dashboard,desktop,logs,prompt-size, ...}
```

انتخاب مدل و شناسهٔ نسخه:

```bash
hermes model                # picker ی تعاملی provider+model
hermes config get model     # خروجی زندهٔ verified:
# default: minimax/minimax-m3:free
# provider: openrouter
hermes --version
# Hermes Agent v0.20.6 (2026.8.27) · upstream 25fcc8ad · local 7d1c9aea
```

## Common pitfalls

- **Secret در config.yaml.** کلیدها فقط در `~/.hermes/.env`. ترکیب‌شان باعث نشت
  credential به آرشیوهای `hermes backup` و اسکرین‌شات‌ها می‌شود.
- **مصرف هیرمس به‌عنوان chatbot.** استفادهٔ chat-only هزینهٔ agent را برای ارزش chatbot
  می‌پردازد. مزیت واقعی دسترسی به tool است.
- **رد کردن `hermes doctor` بعد از نصب.** کلید provider خراب یا dependency ی گم‌شده
  همان‌جا ظاهر می‌شود، نه در اولین استفادهٔ واقعی.
- **اشتباه one-shot با تعاملی.** `hermes chat -q` بعد از جواب خارج می‌شود و slash command
  ندارد؛ `hermes` تعاملی `/model`، `/skills`، `/new` را پشتیبانی می‌کند.
- **پایپ‌کردن UIهای تعاملی.** verified: رابط کانفیگ `hermes tools` ورودی non-TTY را رد
  می‌کند. در اسکریپت از `hermes tools list/enable/disable` استفاده کنید.
- **بی‌توجهی به scope ی `-t`.** لودکردن همهٔ toolsetها برای یک سؤال ساده، بودجهٔ prompt را
  هدر می‌دهد و احتمال فراخوانی tool ی اشتباه را بالا می‌برد.

## Exercises

تمرین `exercises/ex01-agent-foundations.md` را انجام دهید. راستی‌آزمایی: `hermes doctor`
بدون خطای بازدارنده، یک اجرای tool-دار دیده و به زبان loop توضیح‌داده‌شده، سه سطح کانفیگ
پیدا‌شده، هویت مدل تأییدشده.
