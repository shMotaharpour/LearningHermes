# فصل ۰۷ — Cron و Workflowهای زمان‌بندی‌شده

## Why this matters (job link)

آگهی‌های «AI & Automation Engineer» در هسته‌شان همین فصل است: Minted — «طراحی و پیاده‌سازی
اتوماسیون‌های AI-محور و copilotهای داخلی برای بهینه‌سازی workflowها»
(`docs/research/jobs/extract-round2.json`)؛ Adventus — «طراحی، ساخت و deploy ی agentهای
AI ی خودکارکنندهٔ workflowهای سازمانی» (همان فایل). کارِ زمان‌بندی‌شده، قابل‌اتکا و
بدون‌نظارت اولین چیزی است که کسب‌وکارها واقعاً می‌خرند. cron ی هیرمس agent را به یک
scheduler ی production تبدیل می‌کند: jobهای LLM دار، jobهای script-only، تحویل ماندگار،
incident های شکست، memory ی مخصوص هر job. این فصل کل چرخهٔ حیات را پوشش می‌دهد به‌علاوهٔ
جزئیات عملیاتی (internals، notepad، troubleshooting) که demo را از deliverable جدا می‌کند.

## Concepts

### دو نوع cron job

از scheduler ی زنده verified (evidence b4):

1. **jobهای Agent** — یک prompt طبق زمان‌بندی از agent loop می‌گذرد. session ی تازه در هر
   اجرا، ابزار فعال، خروجی تحویل به تارگت پلتفرم.
2. **jobهای script-only (`no_agent`)** — یک اسکریپت طبق زمان‌بندی اجرا می‌شود؛ stdout عیناً
   تحویل می‌شود؛ **stdout ی خالی هیچ چیزی نمی‌فرستد**. بدون هزینهٔ LLM. نمونهٔ زنده روی همین
   ماشین: `docs-folder-watch` — `every 1m`، `Mode: no-agent (script stdout delivered
   directly)`، تحویل به یک topic ی Telegram.

قاعدهٔ طراحی: **watchdog ها اسکریپت‌اند، قضاوت‌ها agent.** هشدار دیسک، ping ی CI، diff ی
تغییر فایل → `no_agent`. خلاصه‌های پژوهشی، briefing روزانه، هر کاری که استدلال می‌خواهد → job ی agent.

### کالبدشناسی یک job

از خروجی verified ی `hermes cron list`، هر job این‌ها را دارد: ID، نام، schedule
(`30m`، `every 2h`، سینتکس cron مثل `0 9 * * *`، یا timestamp ی ISO ی one-shot)، تعداد
تکرار، اجرای بعدی، **تارگت تحویل** (مثل `telegram:-1003924862595:307`)، اسکریپت
(اختیاری)، mode، وضعیت آخرین اجرا و execution ID. jobها خودکفایند — اجرای تازه نمی‌تواند
از شما سؤال بپرسد، پس prompt باید همهٔ context را حمل کند.

### تحویل و پیوستگی

- **تارگت‌های تحویل** همان فرمت `platform:chat[:thread]` ی `hermes send` را دارند.
- **continuity**: job ی agent می‌تواند خروجی قبلی خودش را ببیند — الگوی increment/dedup
  (scout، monitor، digest) روی آن سوار است.
- **Notepadها**: هر job یک notepad ی key-value ی ماندگار دارد که بین اجراها بقا دارد
  (`hermes cron notepad`).

### شکست، درجه‌یک است

`hermes cron runs|history` تلاش‌های اجرای ماندگار را نشان می‌دهد؛ `hermes cron incidents`
شکست‌ها را برای acknowledge فهرست می‌کند. شکستِ یک agent job یک incident ی قابل
acknowledge است، نه رازی در لاگ‌ها.

### Heartbeat و loop (زمان‌بندی محلیِ session)

داخل session ی زنده، `/heartbeat 10m <prompt>` هنگام بیکاری دوباره اجرا می‌شود و `/loop`
یک prompt را روی فاصلهٔ زمانی تکرار می‌کند — خویشاوندان محلیِ session از cron برای
مواردِ watch-while-I-work.

### معناشناسی زمان‌بندی که مهم است

- jobهای cron به gateway (حداقل scheduler) نیاز دارند: verified با `hermes cron status` →
  «Gateway is running — cron jobs will fire automatically; Ticker heartbeat: 1s ago».
- jobهای one-shot timestamp ی ISO می‌گیرند؛ jobهای تکرارشونده فاصله یا عبارت cron.
- `hermes cron tick` jobهای سررسیده را یک بار اجرا و خارج می‌شود — روش قطعی تست.
- `hermes cron pause/resume` بهتر از delete-and-recreate برای ساکت‌کردن موقتی است.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b4-gateway-cron-events.txt`
(درخت کامل cron، لیست زندهٔ jobها با ID/schedule/تارگت واقعی، cron status)،
`docs/research/hermes/cli-evidence-2026-09-07.txt` (cron help).

## Verified commands

بازرسی و تست:

```bash
hermes cron list              # jobها با schedule، تارگت، وضعیت آخرین اجرا
hermes cron status            # scheduler زنده است؟ اجرای بعدی کی؟
hermes cron runs <job-id>     # تلاش‌های اجرای ماندگار
hermes cron incidents         # شکست‌های قابل acknowledge
hermes cron tick              # اجرای یک‌بارهٔ jobهای سررسیده — تست امن
```

ساخت (CLI همان کاری را می‌کند که ابزار cron ی درون-agent می‌کند):

```bash
hermes cron create \
  --name "daily-briefing" \
  --schedule "0 6 * * *" \
  --prompt "Research AI engineering news since yesterday. Summarize top 5 with links. Persian ZWNJ characters are forbidden in automated prompts." \
  --deliver "telegram" \
  --skills grounded-citations
```

job ی script-only (بدون LLM):

```bash
hermes cron create \
  --name "disk-watchdog" \
  --schedule "every 1h" \
  --script /path/to/disk_check.sh \
  --deliver "telegram"          # stdout تحویل می‌شود؛ stdout ی خالی = سکوت
```

مدیریت:

```bash
hermes cron pause <job-id> / resume <job-id>
hermes cron edit <job-id>                # تغییر schedule/prompt/تارگت
hermes cron run <job-id>                 # اجرای فوری در tick ی بعدی
hermes cron remove <job-id>
hermes cron notepad <job-id> read|write  # memory ی ماندگار job
```

## Common pitfalls

- **promptهایی که یک خواننده فرض می‌کنند.** اجراهای cron مستقل‌اند — job نمی‌تواند بپرسد.
  prompt خودکفا، فرمت خروجی صریح، تحویل صریح.
- **ZWNJ ی فارسی در promptهای خودکار.** نیم‌فاصله‌ها در promptهای زمان‌بندی‌شده به‌عنوان
  بردار تزریق تلقی می‌شوند و تحویل را می‌شکنند. promptهای خودکار انگلیسی؛ جواب می‌تواند فارسی باشد.
- **job ی agent برای کارِ اسکریپت.** پرداخت توکن LLM برای `df -h | mail` اتلاف است — برای
  چک‌های قطعی از `no_agent` استفاده کنید.
- **معمای stdout ی خالی.** job ی اسکریپت «تحویل نشد»؟ درست اجرا شده و stdout خالی بوده —
  سکوت رفتار طراحی‌شده است. روی همهٔ مسیرها چیزی چاپ کنید، حتی «all clear».
- **فراموشی تارگت.** job بدون تارگت تحویل، خروجی را فقط محلی ذخیره می‌کند. تارگت را
  تأیید کنید: `hermes send --list`.
- **تست در production.** jobهای جدید اولین بار در schedule واقعی‌شان اجرا می‌شوند. قبل از
  اولین fire ی واقعی، خط لوله را با `hermes cron tick` (یا `cron run`) اثبات کنید.
- **incident های acknowledge نشده.** شکست‌ها تا acknowledge در `hermes cron incidents`
  می‌مانند؛ مثل صف pager با آن رفتار کنید.

## Exercises

تمرین `exercises/ex07-cron-scheduled-workflows.md` را انجام دهید. راستی‌آزمایی: یک job ی
script-only و یک job ی agent فعال، هر دو با tick تست‌شده، نمای incidents تمیز، یک job
بدون حذف‌وساختن ویرایش شده.
