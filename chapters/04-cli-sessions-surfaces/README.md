# فصل ۰۴ — CLI، Sessionها و Surfaceها

## Why this matters (job link)

«بهره‌وری توسعه‌دهنده» و «مدیریت incident» تمایزدهنده‌های خاموش آگهی‌های senior هستند:
True Zero مهندسانی می‌خواهد که «مستندسازی فنی معماری... deployment» را در تمام چرخهٔ حیات
نگه دارند (`docs/research/jobs/source-03.md`)؛ نقش FDE ی Reflection مالکیت تحویل «از
discovery ی مشتری تا production launch» است (`docs/research/jobs/source-04.md`). loop ی
روزانهٔ یک مهندس applied: کار را اجرا کن، ببین چه شد، از جایی که شکست ادامه بده، لازم شد
بازیابی کن. هیرمس به هر session هویت، transcript و یک تور ایمنی (checkpoint) می‌دهد. این
فصل شما را روی هر پنج surface سریع و امن می‌کند: CLI، TUI، desktop، dashboard، پلتفرم‌های gateway.

## Concepts

### یک agent، پنج surface

همان هسته با این شکل‌ها اجرا می‌شود:

| Surface | اجرا | مناسب برای |
|---|---|---|
| CLI ی تعاملی | `hermes` | کار روزمره، اسکریپت، اتوماسیون |
| Ink TUI | `hermes --tui` | sessionهای طولانی مرئی، widget، ماوس |
| Desktop app | `hermes desktop` | drag-drop فایل، پیش‌نمایش کنار‌هم، voice |
| Web dashboard | `hermes dashboard` | ادمین: کانال‌ها، MCP، cron، memory، لاگ‌ها |
| پلتفرم‌های gateway | فصل ۰۶ | Telegram/Discord/Slack... — چت به‌عنوان رابط |

sessionها زیرساخت مشترک‌اند: یک گفتگوی Telegram و یک session ی terminal هر دو در همان
استور SQLite (`~/.hermes/state.db`) می‌روند و از هر surface قابل resume هستند.

### هویت session و استور

از استور زنده (evidence b3) verified: هر session عنوان، workspace، آخرین فعالیت و ID ای
مثل `20260906_231510_f4298797` دارد (تاریخ UTC، زمان، پسوند تصادفی). `hermes sessions
stats` جمع استور را می‌دهد — روی این ماشین: `21 sessions, 5972 messages, 29.5 MB` با تفکیک
پلتفرم (16 telegram، 2 cli). استور با FTS5 index شده: عنوان‌ها و محتوا قابل جستجو هستند.

### checkpointها — تور ایمنی filesystem

قبل از اینکه `write_file`/`patch`/`terminal` دایرکتوری کاری‌تان را تغییر دهند، هیرمس از آن
در یک **repo ی سایه** snapshot می‌گیرد (عین تعریف در `hermes checkpoints --help`).
`/rollback` داخل session وضعیتِ پیش از خطا را برمی‌گرداند؛ `hermes checkpoints
status|prune|clear` هزینهٔ دیسکی را مدیریت می‌کنند. معناشناسی که باید درونی شود:

- checkpoint در برابر تغییراتِ **agent** بین snapshotها محافظت است — دیسیپلین git خودتان
  همچنان الزامی است.
- استور با فعالیت رشد می‌کند؛ `prune` بهداشت روتین است، `clear` کل تاریخچهٔ rollback را
  نابود می‌کند (verified: «Delete the entire checkpoint base (all /rollback history)») —
  `clear` آخرین راه‌حل است.

### slash commandها — کنترل‌پنل درون-session

`/model`، `/new`، `/compact`، `/skills`، `/heartbeat`، `/rollback`، `/export`... روی هر
surface ی چتی از جمله topicهای Telegram کار می‌کنند. این‌ها REPL ی agent هستند: تعویض
مدل، فورس‌کردن compression، لود skill بدون ترک گفتگو. مرجع کامل در صفحهٔ slash-commands
مستندات رسمی است؛ پنج تای بالا ۸۰٪ استفادهٔ روزمره را پوشش می‌دهند.

### معناشناسی resume

`hermes --continue` جدیدترین session را ادامه می‌دهد؛ `hermes --resume <ID>` با ID ی دقیق.
در setupهای چند-پلتفرمی، «جدیدترین» هر session ای است — CLI یا هر topic ی Telegram — که
آخرین بار نوشته. برای هر کاری که مهم است، با ID resume کنید.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt`
(`sessions list` زنده با IDهای واقعی، `sessions stats`، help ی checkpoints، محدودیت TTY)،
`docs/research/hermes/cli-evidence-2026-09-07-b7-multiagent-shipping.txt` (dashboard/backup).

## Verified commands

چرخهٔ حیات session:

```bash
hermes sessions list                 # sessionهای اخیر، عنوان‌ها، IDها
hermes sessions stats                # جمع کل + تفکیک پلتفرم + حجم DB
hermes sessions browse               # picker ی تعاملی: جستجو، خواندن، resume
hermes --resume 20260906_231510_f4298797    # resume با ID
hermes --continue                            # resume ی جدیدترین
hermes sessions rename 20260906_231510_f4298797 "Q3 eval work"   # عنوان منتخب
hermes sessions pin <id> / unpin / pinned      # معافیت از آرشیو خودکار
hermes sessions export               # خروجی JSONL / Markdown / QMD
hermes sessions archive              # مخفی‌سازی نرم، بدون حذف
hermes sessions prune --older-than 30d         # بهداشت سخت (اول --help را ببینید)
```

checkpointها:

```bash
hermes checkpoints status    # حجم استور، تعداد پروژه، تفکیک per-project
hermes checkpoints prune     # GC ی snapshotهای کهنه
```

Surfaceها:

```bash
hermes --tui                 # ترمینال UI ی Ink
hermes desktop               # اپ نیتیو (toolهای streaming، file browser، voice)
hermes dashboard             # پنل ادمین وب (کانفیگ، کانال‌ها، MCP، cron، لاگ‌ها)
hermes dashboard --status    # در حال سرو است یا نه
```

خانه‌داری:

```bash
hermes backup -o ~/hermes-backup.zip    # آرشیو کامل config+skills+sessions
hermes logs -n 100                       # tail ی agent.log / errors.log
hermes logs --level error --since 1h     # نمای فیلترشده برای incident
```

## Common pitfalls

- **sessionها مجانی نیستند.** sessionهای آزمایشی هرس‌نشده، جستجو را شلوغ و DB را بزرگ
  می‌کنند. مهم‌ها را pin کنید، بقیه را archive، prune را زمان‌بندی کنید (فصل ۰۷ اتوماتش می‌کند).
- **rollback یعنی git نیست.** checkpoint فقط تغییرات agent بین snapshotها را پوشش می‌دهد.
  ریپوهای شما هنوز به دیسیپلین معمولی git نیاز دارند.
- **UIهای تعاملی در اسکریپت.** verified: رابط کانفیگ `hermes tools` ورودی non-TTY را رد
  می‌کند. مسیرهای اسکریپت‌پذیر: `hermes tools list|enable|disable`؛ `hermes sessions
  browse` فقط برای انسان.
- **افشای dashboard.** dashboard یک پنل ادمین کامل است — روی localhost ببندید یا پشت
  احراز هویت بگذارید؛ port-forward ی عادی ممنوع.
- **ابهام `--continue`.** در setupهای چند-پلتفرمی «جدیدترین» مبهم است. IDها ارزان‌اند؛
  استفاده کنید.
- **نخواندن `hermes logs` هنگام incident.** transcript نشان می‌دهد agent چه کرد؛
  `hermes logs` نشان می‌دهد runtime چه کرد (gateway، خطای provider، شکست tool). incident
  به هر دو نیاز دارد.

## Exercises

تمرین `exercises/ex04-cli-sessions-surfaces.md` را انجام دهید. راستی‌آزمایی: resume با ID،
یک rollback ی checkpoint، یک export تولیدشده، خواندن لاگ در حین یک کار واقعی.
