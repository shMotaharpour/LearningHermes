# فصل ۱۱ — یکپارچه‌سازی MCP

## Why this matters (job link)

MCP حالا نیازمندیِ نام‌بردهٔ آگهی‌هاست: «Senior AI Software Engineer - MCP & Agentic
Systems»، «Senior Python MCP Engineer»، «Senior Software Developer - MCP and Agentic AI —
Autodesk» (`docs/research/jobs/search-round3-mcp-evals.json`). tool calling شما را اینجا
آورد؛ MCP اقتصاد استانداردِ tool روی آن است. هیرمس MCP را درجه‌یک می‌گیرد: client
(مصرف serverهای خارجی)، filter (کنترل اینکه کدام toolها لود شوند) و server (`hermes mcp
serve` — رساندن agent خودتان به agentهای دیگر). این فصل شما را در هر سه روان می‌کند —
دقیقاً چیزی که آن آگهی‌ها غربال می‌کنند.

## Concepts

### Model Context Protocol

MCP نحوهٔ کشف و فراخوانی toolهای خارجی توسط agent را استاندارد می‌کند: یک **server** ی
MCP toolها (و resourceها) را expose می‌کند؛ **client** ی MCP (agent شما) آن‌ها را لیست و
invoke می‌کند. clientهای هیرمس با فرمت `server:tool` در namespace ی tool ظاهر می‌شوند
(verified در `hermes tools --help`) — مثلاً `github:create_issue` — یک server، چند tool،
هزینهٔ prompt به‌ازای هر tool ی فعال (درس بودجهٔ فصل ۰۳ اینجا هم هست).

### سمت client: add، configure، filter

درخت فرمان verified (evidence b5): `hermes mcp add <name> --url <endpoint>` برای
serverهای remote، `--command <cmd> --args` برای serverهای محلی stdio، به‌علاوهٔ
`list/test/configure/login/reauth`. فیلتر toolها per-server است: server را enable کنید،
بعد toolهای پرصدا را disable کنید — scope کردن به سبک `hermes tools disable
github:create_issue` ی فصل ۰۵ روی toolهای MCP هم کار می‌کند.

### مسیر کاتالوگ

`hermes mcp catalog` (verified زنده) serverهای تأییدشدهٔ Nous را برای نصب یک‌کلیکی لیست
می‌کند — airtable، asana، amplitude، algolia و ده‌ها مورد دیگر — و `hermes mcp install
<name>` کشف + auth + کانفیگ را در یک قدم انجام می‌دهد. serverهای OAuth-محور state ی
login دارند: `hermes mcp login/reauth` (verified) تازه‌اش می‌کند.

### سمت server: agent شما به‌عنوان provider ی tool

`hermes mcp serve` (verified: «Run Hermes as an MCP server — expose conversations to other
agents») جهت را برمی‌گرداند: instance ی هیرمس شما یک endpoint ی MCP می‌شود که agentهای
دیگر مصرفش می‌کنند. مکملِ A2A ی peerهای فصل ۰۹ — استاندارد-محور، نه platform-خاص.

### دیسیپلین تست

`hermes mcp test <name>` (verified) اتصال را با callهای سنتتیک ورز می‌دهد. نردبان دیباگ
وقتی یک tool بدرفتار می‌کند: `hermes mcp list` (کانفیگ شده؟) → `hermes mcp test`
(در دسترس؟) → `hermes tools list` (فعال؟) → خودِ call (آرگومان‌ها درست؟).

### نوشتن MCP server ی خودتان

هر زبانی با SDK ی MCP کار می‌کند — یک server ی stdio اسکریپتی است که JSON-RPC روی stdio
حرف می‌زند؛ یک server ی HTTP یک URL expose می‌کند. برای هیرمس مهم نیست کجا اجرا شود؛
قرارداد، پروتکل است. حداقلِ server ی عملی: یک tool، ورودی‌های JSON-Schema شده، خروجی
قطعی. سیستم plugin ی فصل ۱۲ جایگزین in-process است وقتی integration ی عمیق‌تر از tool می‌خواهید.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b5-skills-mcp-plugins.txt`
(درخت کامل `hermes mcp`، خروجی زندهٔ `mcp list` ی خالی + جدول `mcp catalog` با entryهای واقعی).

## Verified commands

چرخهٔ حیات client:

```bash
hermes mcp list                          # serverهای کانفیگ‌شده (متن empty-state ی verified)
hermes mcp add notes --command ./notes-mcp --args --port 8321
hermes mcp add github --url https://mcp.github.dev/sse
hermes mcp test notes                    # چک ی اتصال سنتتیک
hermes mcp configure notes               # انتخاب per-tool
hermes mcp login github / reauth --all   # نگهداری OAuth
hermes mcp remove notes
```

کاتالوگ:

```
$ hermes mcp catalog
  Name        Status      Description
  airtable    available   Bases, tables, and records from your Airtable workspace.
  asana       available   Tasks, projects, and goals from your Asana workspace.
  ...                                  (جدول زنده ی verified)
```

```bash
hermes mcp install airtable              # نصب یک‌کلیکی از کاتالوگ
```

حالت server:

```bash
hermes mcp serve                         # expose کردن این agent روی MCP
```

فیلتر tool (فرمان فصل ۰۵، شیء MCP):

```bash
hermes tools list                        # toolهای MCP به شکل server:tool
hermes tools disable github:create_issue # خاموش کردن یک tool
```

## Common pitfalls

- **فعال‌کردن هر toolی که server می‌دهد.** schema ی هر tool در prompt سوار است (فصل ۰۳).
  به چندتایی که استفاده می‌کنید کانفیگ کنید.
- **معمای انقضای OAuth.** tool ای که بعد از هفته‌ها «کارش را کرد» اغلب token ی کهنه است:
  قبل از دیباگِ کد `hermes mcp reauth --all`.
- **سردرگمی env ی server ی stdio.** serverهای محلی محیط launch را به ارث می‌برند — secretها
  در `.env` و env ی صریح، نه shell ی تعاملی.
- **رد کردن `mcp test`.** server می‌تواند کانفیگ شده باشد و باز هم خراب (مسیر اشتباه،
  پروسهٔ مرده). تست ارزان‌ترین چک است.
- **اشتباه MCP با plugin.** MCP = toolهای خارجی روی پروتکل (چندزبانه، چندپروسه). plugin =
  افزونهٔ in-process ی هیرمس با hook/LLM access (فصل ۱۲). انتخاب اشتباه یعنی rewrite.

## Exercises

تمرین `exercises/ex11-mcp-integration.md` را انجام دهید. راستی‌آزمایی: یک MCP ی کاتالوگ
نصب+فیلتر شده، یک stdio server ی سفارشی نوشته و توسط agent صدا زده‌شده، رزمایش reauth.
