# فصل ۰۵ — Toolها و قابلیت‌ها

## Why this matters (job link)

Tool calling مهارتِ زیربنایی در آگهی‌های agent است: Reflection مهندسانی می‌خواهد که
«workflowهای LLM را orchestrate کنند و با زیرساخت enterprise یکپارچه کنند»
(`docs/research/jobs/source-04.md`)؛ 100ms سازندگانی می‌خواهد که با «تکنیک‌های prompting،
datasetهای fine-tuning، استراتژی‌های retrieval و کانفیگ مدل» آزمایش کنند
(`docs/research/jobs/source-05.md`)؛ Adventus برای «اپلیکیشن‌های LLM-محور، اتوماسیون
workflow، integration ی API» استخدام می‌کند (`docs/research/jobs/extract-round2.json`).
مهارت applied این است که بدانید: چه toolهایی وجود دارند، چه هزینه‌ای دارند، کجا شکست
می‌خورند، و چطور برای هر کار scope شوند. این فصل سطح قابلیت‌های داخلی هیرمس را پوشش
می‌دهد: toolsetها، web search/extract، browser، computer use، vision، استخراج سند، رسانه.

## Concepts

### رده‌شناسی toolset

قابلیت‌ها در toolset عرضه می‌شوند (verified با `hermes tools --help`: «toolsetهای داخلی
نام ساده دارند (web, memory). toolهای MCP با فرمت server:tool می‌آیند»). مجموعهٔ روزمره:

| Toolset | چه می‌دهد | حالت شکست شناخته‌شده |
|---|---|---|
| `terminal` | shell، فایل، پروسه | دستورهای مخرب به جریان approval می‌خورند (فصل ۱۵) |
| `web` | web_search + web_extract | صفحات JS-سنگین اسکلت برمی‌گردانند؛ browser جایگزین است |
| `browser` | Chromium واقعی با CDP | کند و state دار؛ profile قفل‌شده را ببندید |
| `computer_use` | ماوس/کیبورد سطح OS | به نصب cua-driver نیاز دارد (`hermes computer-use install`) |
| `memory` | خواندن/نوشتن memory ماندگار | به هر session آینده تزریق می‌شود — محتاطانه بنویسید |
| media | تولید تصویر، TTS | سهمیهٔ provider |

scope کردن flag ی درجه‌اول است (`-t terminal,web`) و ابزار هزینه: toolset کمتر → prompt
کوچک‌تر → انحراف کمتر به سمت toolهای اشتباه.

### وب: search در برابر extract در برابر browser

سه پلهٔ فزاینده برای وب (همه در workflow ی همین دوره verified شده):

1. **`web_search`** — کوئری → نتایج رتبه‌دار با snippet. ارزان، اولین کاوش.
2. **`web_extract`** — URL → markdown تمیز. برای صفحات ایستا، وبلاگ‌ها و حتی PDF ها
   (مقالات arxiv مستقیم extract می‌شوند) کار می‌کند. بودجهٔ کاراکتری دارد؛ صفحات بزرگ متن
   کامل را روی دیسک ذخیره می‌کنند.
3. **Browser** — Chromium واقعی: فرم‌ها، کلیک، اپ‌های JS-سنگین، اسکرین‌شات. agent از طریق
   CDP می‌رانَد؛ providerهای cloud-browser هم plug می‌شوند.

قاعدهٔ تصمیم: اول search، بعد extract، آخر browser (browser پلهٔ کند و گرانِ محتوای
پشت‌دیوارِ JS است).

### Computer use

`hermes computer-use install|status|doctor|permissions` (verified) باینری cua-driver پشت
toolset ی `computer_use` را مدیریت می‌کند — کنترل سطح OS ی ماوس، کیبورد، اسکرین‌شات،
اپ‌های دسکتاپ. برای آخرین مایل: اپ‌های نیتیو بدون API، نرم‌افزار دسکتاپ قدیمی. پرریسک‌ترین
toolset است (دسکتاپ واقعی را لمس می‌کند) و با دیسیپلین approval ی فصل ۱۵ جفت می‌شود.

### Vision و استخراج سند

vision ورودی چندوجهی است: تصویر paste کنید (CLI) یا عکس بفرستید (Telegram) و مدل
می‌خواندش — نمودار، اسکرین‌شات، عکس وایت‌برد. استخراج سند داخل `read_file` است: PDF،
اسناد Office، notebookها خودکار به متن تبدیل می‌شوند. مرز را بشناسید: PDF ی اسکن‌شده
تصویر است — مسیر vision می‌خواهد نه استخراج متن.

### تولید رسانه

تولید تصویر (مدل‌های FAL.ai)، TTS و transcription ی voice، toolsetهای پشتیبانی‌شده توسط
provider هستند. ابزارهای کم‌context و قابل‌قیمت‌گذاری — هدف‌های خوب اولیه برای کارهای
واگذارشده به agent.

### الگوی واگذاری برای قابلیت‌ها

مهارت واقعی این فصل: **تطبیق قابلیت با کار با scope ی صریح.**

- «این PDF را خلاصه کن» → استخراج سند، بدون browser.
- «این dashboard را روزانه چک کن» → browser + cron (فصل ۰۷).
- «این فرم دولتی را پر کن» → computer use + approvalها.
- «چه کسی به این مقاله ارجاع داده» → حلقهٔ web search + extract.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt`
(subcommandهای browser/computer-use، محدودیت TTY)، و فایل‌های تحقیق خودِ دوره در
`docs/research/jobs/extract-round2.json` — دقیقاً با همین خط لولهٔ search→extract تولید شده‌اند.

## Verified commands

مدیریت toolset:

```bash
hermes tools list              # هر tool + وضعیت enabled/disabled
hermes tools --summary         # toolهای فعال هر پلتفرم (چک انسانی)
hermes tools enable browser    # ورود به یک toolset
hermes tools disable computer_use   # خروج — کاهش ریسک
```

درایور computer use:

```bash
hermes computer-use status     # cua-driver نصب است؟
hermes computer-use install    # گرفتن/اجرای installer
hermes computer-use doctor     # ماتریس سلامت: TCC، bundle، پشتیبانی پلتفرم
```

کمک‌های browser:

```bash
hermes browser close-profile   # آزادسازی profile قفل‌شده (مخرب: تب‌های ذخیره‌نشده)
```

scope ی per-run (flag ی verified):

```bash
hermes chat -q "Research X and summarize" -t web
hermes chat -q "Fix the failing test" -t terminal,memory
```

## Common pitfalls

- **همیشه-همه‌چیز روشن.** فعال‌بودن همهٔ toolsetها برای همهٔ sessionها prompt را چاق و
  نرخ فراخوانی اشتباه tool را بالا می‌برد. برای هر کار scope کنید.
- **browser برای کاری که extract هندل می‌کند.** یک صفحهٔ مستندات ایستا Chromium نمی‌خواهد.
  نردبان escalation به همین دلیل هست — هر پله ۱۰ برابر گران‌تر.
- **computer use روی ماشین اشتباه.** دسکتاپ *واقعی* را می‌رانَد. روی ماشین اشتراکی یا
  production این یک incident ی امنیتی در انتظار است (فصل ۱۵).
- **PDF ی اسکن‌شده به‌عنوان متن.** استخراج روی PDF های تصویری خالی/زباله برمی‌گرداند؛ به
  vision بدهید.
- **اشتباه MCP با داخلی.** toolهای خارجی از MCP server می‌آیند (`server:tool`) — فصل ۱۱.
  دیباگِ «tool خارجی غایب» به‌عنوان مشکل toolset یک ساعت وقت می‌برد.
- **profile های browser قفل‌شده.** session ی browser با profile واقعی، profile را قفل
  می‌کند؛ قبل از استفادهٔ دستی، ببندیدش (`hermes browser close-profile`).

## Exercises

تمرین `exercises/ex05-tools-capabilities.md` را انجام دهید. راستی‌آزمایی: یک اجرای
scope‌شده، نمایش نردبان escalation (search→extract→browser)، استخراج یک سند، یک خوانش vision.
