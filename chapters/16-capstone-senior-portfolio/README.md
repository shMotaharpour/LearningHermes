# فصل ۱۶ — Capstone: Portfolio ی سطح Senior

## Why this matters (job link)

همهٔ فصل‌های قبل شایستگی بودند؛ این یکی *شواهد* است. مصاحبه‌های senior روی آرتیفکت
می‌چرخند: «سیستمی که شip کرده‌ای را نشان بده، چطور اندازه‌اش گرفتی، چطور امنش کردی.»
آگهی‌هایی که این دوره از آن‌ها معدن‌کاوی کرد حد را تعریف می‌کنند — Reflection: «مالکیت
استراتژی و تحویل فنی سیستم‌های agentic از discovery ی مشتری تا production launch»
(`docs/research/jobs/source-04.md`)؛ 100ms: «ساخت سیستم‌ها، metricها و حلقه‌های feedback
ای که agentها را در طول زمان بهتر می‌کنند» (`docs/research/jobs/source-05.md`). capstone
جواب سرتاسری شماست: یک workflow ی واقعی enterprise اتومات‌شده با هیرمس، ارزیابی‌شده،
سخت‌شده و بسته‌بندی‌شده به‌عنوان portfolio.

## Concepts

### قرارداد capstone

یک workflow ی واقعی با stake ی واقعی بردارید (گزارش‌دهی تیم تان، یک فرایند کسب‌وکار
شخصی، نگهداری یک پروژهٔ open-source) و **هر شش** را تحویل دهید:

1. **اتوماسیون** — زمان‌بندی‌شده و/یا event-driven (cron، webhook، hook) — بخش III.
2. **integration** — حداقل یک سیستم خارجی با MCP/plugin/API (بخش IV).
3. **evaluation** — task set ی فریز + چک قطعی + judge + gate ی regression (فصل ۱۴).
4. **امنیت** — مدل تهدید، approvalها، secrets، egress، کمترین امتیاز (فصل ۱۵).
5. **observability** — logs/insights/monitoring سیم‌کشی‌شده؛ incidents ی acknowledge‌شده (فصل ۱۴).
6. **بسته‌بندی portfolio** — repo، README، یادداشت معماری، زنجیرهٔ شواهد (تمرین‌های همین فصل).

### یادداشت معماری (آرتیفکت مصاحبه)

یک صفحه: نمودار workflow، توپولوژی agent (کدام sessionها/profileها/toolها)، حالت‌های
شکست و نگهبان‌هایشان، مدل هزینه (token/day بر اساس tier)، و gate ی eval برای تغییرها.
سیگنال senior = نگهبان‌ها هستند، نه featureها.

### جدول نگاشت شایستگی-به-شواهد

برای هر یک از ده شایستگی بازار کار در `CURRICULUM.md`، مدرکتان را نام ببرید: commit،
نتیجهٔ eval، incident ای که هندل کردید. جدول نگاشت، index ی portfolio است — همان چیزی که
«Senior Applied AI Engineer» به زبان آرتیفکت یعنی.

### ریپوی خودِ دوره به‌عنوان نمونهٔ اجراشده

این مخزن *خودش* یک capstone از قواعد خودش است: قراردادهای AGENTS.md، فایل‌های شواهد زیر
`docs/research/`، اسکریپت اعتبارسنجی + تست‌ها، خط لولهٔ parity ی دوزبانه، و skillهای
per-chapter. به همین چشم بخوانیدش.

**شواهد:** همهٔ فایل‌های شواهد فصل‌های قبل؛ capstone مال خودتان را زیر
`docs/research/capstone/` اضافه می‌کند.

## Verified commands

capstone هیچ فرمان جدیدی ندارد — verifiedهای قبلی را ترکیب می‌کند:

```bash
hermes cron status && hermes cron incidents        # سلامت اتوماسیون
hermes insights --days 7                           # نمای هزینه
hermes monitoring status                           # نمای runtime
python3 scripts/validate_course.py --root .        # gate ی QA ی repo
hermes backup -o ~/capstone-$(date +%F).zip        # بازیابی از فاجعه
```

## Common pitfalls

- **demo-ware.** workflow ای که فقط با babysitting شما اجرا می‌شود demo است. لایهٔ
  cron/webhook باید دو هفته بدون حضور شما اجرا شود تا اسمش را done بگذارید.
- **نمایشِ eval.** پنج task ی فریزی که هرگز re-run نمی‌شوند تزئین‌اند. gate ی regression
  را به فرایند تغییر گره بزنید (تمرین فصل ۱۴).
- **امنیت به‌عنوان فکرِ بعدی.** retrofit کردن approval/egress بعد از incident در مصاحبه
  دیده می‌شود. از روز اول داخلش بچینید.
- **portfolio بدون شواهد.** اسکرین‌شات چت مدرک نیست؛ فرمان‌ها، خروجی‌های خام، diffهای
  eval و postmortemهای incident مدرک‌اند.
- **انفجار scope.** یک workflow ی کامل بهتر از سه نیمه‌کاره است. scope را ببرید، شش
  deliverable را نه.

## Exercises

capstone خودش تمرین است — ببینید `exercises/ex16-capstone-senior-portfolio.md` برای spec
کامل، milestoneها و checklist دفاع.
