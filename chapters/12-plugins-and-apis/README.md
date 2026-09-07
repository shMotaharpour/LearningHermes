# فصل ۱۲ — Pluginها و APIها

## Why this matters (job link)

مهندسی پلتفرم tier ی senior ی applied AI است: Reflection «deploy ی سیستم‌های production ی
قابل‌اتکا» در محیط‌های hybrid را می‌خواهد (`docs/research/jobs/source-04.md`)؛ 100ms
مهندسانی می‌خواهد که «سیستم‌ها، metricها و حلقه‌های feedback» دور agentها بسازند
(`docs/research/jobs/source-05.md`). وقتی toolهای MCP کافی نیستند — وقتی به hook در
lifecycle ی agent، دسترسی LLM اش یا هندل secret نیاز دارید — سیستم plugin ی هیرمس نقطهٔ
افزودن in-process است. و سطح‌های API (`hermes serve`، ACP، `hermes proxy`، کتابخانهٔ
Python) agent را به زیرساختی تبدیل می‌کنند که نرم‌افزارهای دیگر مصرفش می‌کنند. این فصل
چهار قراردادِ integration ای که یک مهندس applied باید بشناسد را پوشش می‌دهد.

## Concepts

### plugin: افزودن in-process

یک plugin ابزارهای سفارشی، hookهای lifecycle، فایل‌های داده و skillها را یک‌جا بسته
می‌کند — درون هیرمس اجرا می‌شود، نه کنارش (در برابر مدل چند-پروسه‌ای MCP). سطح مدیریت
verified (evidence b5): `hermes plugins install|search|update|remove|list|enable|disable|
capabilities|doctor|pack|show`. انواع مستندشده در guideهای رسمی:

- **tool plugin** — ابزار با معناشناسی کامل runtime ی tool ی هیرمس.
- **secret-source plugin** — کشیدن credential از Bitwarden/1Password/... در startup.
- **provider plugin ی model/memory/browser/search** — تعویض کل backendها.
- **context-engine plugin** — جایگزینی compressor ی داخلی context.

pluginها دسترسی LLM ی scoped دارند (`ctx.llm`) — callهای ساختاریافته با auth ی host-owned
و trust gate ی fail-closed. داخلی‌ها با lifecycle hook اجرا می‌شوند (disk-cleanup و رفقا).

### API server: agent به‌عنوان endpoint سازگار با OpenAI

`hermes serve` (verified: API سازگار با OpenAI برای هر frontend) — Open WebUI، اپ‌های
سفارشی یا هر client با OpenAI-SDK را به agent تان نشانه بروید؛ toolها هم آتش می‌خورند.
`API_SERVER_KEY` محافظش می‌کند. این‌طور به محصولتان backend ی agent می‌دهید بدون نوشتن
plumbing ی agent.

### ACP: agent داخل editorها

`hermes acp` (verified: «Start Hermes Agent in ACP mode for editor integration — VS Code,
Zed, JetBrains») — همان agent loop، protocol-bridged داخل IDE تان. ویرایش با toolهای
agent، approvalها داخل editor.

### hermes proxy: OAuth به‌عنوان API

`hermes proxy start|status|providers` (verified: «local HTTP server that forwards
OpenAI-compatible requests to an OAuth-authenticated provider») — subscription/login ی
OAuth را از CLIs ی ثالث (Codex، Aider، Cline) بدون افشای API key استفاده کنید.

### embed ی کتابخانه‌ای ی Python

guide ی python-library در مستندات، `AIAgent` را مستقیم در اسکریپت‌ها و اپ‌ها embed
می‌کند — loop ی agent به‌صورت library call. embed را وقتی انتخاب کنید که کنترل‌لوپ تنگ
می‌خواهید؛ API server را وقتی هر client ی OpenAI کافی است؛ MCP را وقتی toolها باید بیرون
زندگی کنند.

### انتخاب نقطهٔ افزودن درست

| نیاز | استفاده |
|---|---|
| افزودن tool، چندزبانه/چندپروسه | MCP server (فصل ۱۱) |
| tool + hook + دسترسی LLM، in-process | plugin |
| هر client ی OpenAI با agent حرف بزند | `hermes serve` |
| integration با IDE | ACP |
| subscription ی OAuth به‌عنوان endpoint ی OpenAI | `hermes proxy` |
| agent داخل یک برنامهٔ Python | embed ی کتابخانه‌ای |

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b5-skills-mcp-plugins.txt`
(درخت کامل plugins، help ی serve/acp/proxy).

## Verified commands

مدیریت plugin:

```bash
hermes plugins list                # نصب‌شده‌ها + وضعیت
hermes plugins search <term>       # کشف
hermes plugins install <name>      # نصب
hermes plugins capabilities <name> # چه چیزی register می‌کند
hermes plugins doctor              # چک سلامت
hermes plugins enable|disable <name>
hermes plugins pack <dir>          # بسته‌بندی plugin ی خودتان
```

سطح‌های API:

```bash
hermes serve --port 8377           # endpoint ی agent سازگار با OpenAI
hermes serve --status
hermes acp                         # پل editor (VS Code/Zed/JetBrains)
hermes proxy start|status|providers
```

برنامه‌نویسی‌شده:

```python
# examples/embed-agent.py (ببینید docs/guides/python-library)
from hermes_cli.agent import AIAgent   # مسیر import طبق guide ی رسمی
# agent = AIAgent(...); result = agent.run("summarize repo state")
```

## Common pitfalls

- **plugin وقتی MCP کافی است.** کد in-process سخت‌تر sandbox و سخت‌تر share می‌شود.
  پیش‌فرض MCP؛ plugin برای نیازهای lifecycle/deep-integration.
- **اعتماد به plugin ی بازرسی‌نشده.** pluginها درون-processe با secretهای مجاور — plugin
  ثالث را مثل پکیج pip از غریبه‌ها ببینید: review، بعد install.
- **serve بدون کلید.** `hermes serve` بدون `API_SERVER_KEY` روی اینترفیس قابل‌دسترس،
  دسترسی tool ی ماشین‌تان را به هر کسی که پورت را پیدا کند می‌دهد.
- **سردرگمی scope ی proxy.** proxy جلوی *providerهایی که به آن‌ها login هستید* را
  می‌گیرد؛ gateway ی عمومی LLM نیست. محدودیت و شرایط upstream برقرار است.
- **sessionهای editor در برابر sessionهای gateway.** اجراهای ACP مثل هر surface ی دیگر
  session می‌سازند — تعجب نکنید اگر `sessions list` نشان IDهای editor داد.

## Exercises

تمرین `exercises/ex12-plugins-and-apis.md` را انجام دهید. راستی‌آزمایی: capabilities +
doctor ی یک plugin، رفت‌وبرگشت API server با کلید، demo ی ACP یا proxy، اجرای snippet ی embed.
