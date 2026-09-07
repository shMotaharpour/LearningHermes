# فصل ۱۴ — Evals و Observability

## Why this matters (job link)

evaluation سریع‌الرشدترین نیازمندی پیکره است — ۸۱ ارجاع و یک خانوادهٔ شغلی کامل
(LLM Quality/Evaluation Engineer): 100ms — «اجرای systematic ی LLM evaluations، ردیابی
regressionها و اطمینان از رسیدن مدل‌ها به quality barها ... تعریف و پیاده‌سازی metricهای
کارایی (correctness، latency، کنترل hallucination، safety)» (`docs/research/jobs/source-05.md`)؛
پارامونت — «تقویت تشخیص defect و ارائهٔ بینش‌های پیش‌بین کیفیت»
(`docs/research/jobs/source-01.md`). agentها بی‌صدا شکست می‌خورند: stack trace ندارند،
فقط جواب بدتر می‌دهند. observability باعث می‌شود ببینید؛ eval اثبات می‌کند تغییر چیزی را
بهتر کرده. این فصل هر دو عادت را روی instrumentation ی بومی هیرمس می‌سازد.

## Concepts

### روی یک agent چه چیزی observe کنیم

چهار لایه، هرکدام با tool ی بومی:

| لایه | سؤال | ابزار هیرمس |
|---|---|---|
| runtime | سرویس سالم است؟ | `hermes monitoring status`، `hermes logs` |
| هزینه/مصرف | چقدر خرج می‌کند؟ | `hermes insights --days N` |
| رفتار | واقعاً چه کرد؟ | transcriptهای session، `hermes sessions export` |
| کیفیت | کار *خوب* بود؟ | evalها (شما می‌سازید، همین فصل) |

verified: `hermes monitoring` metricهای سلامتِ حذف‌شدهٔ محتوا را روی OTLP export می‌کند —
ساخته برای operatorها، به‌طور ساختاری بی‌خطر. `hermes logs` بر اساس level/component/زمان
فیلتر می‌کند — نمای incident. `hermes insights` توکن/هزینه/الگوی tool را جمع می‌کند —
نمای خرج.

### trajectory: آرتیفکت eval

هر اجرای agent یک trajectory است: prompt → tool callها → نتایج → جواب. مستندات هیرمس
فرمت trajectory و batch processing (فصل ۰۹) را برای تولید در مقیاس دارد. یک eval set عبارت
است از: N task + ویژگی‌های مورد انتظار + یک judge. سه الگوی judge:

1. **چک‌های قطعی** — فایل ظاهر شد؟ تست‌ها پاس شد؟ خروجی parse شد؟ اسکریپتی، ارزان‌ترین،
   اول اجرا شود.
2. **LLM-as-judge ی rubric-based** — یک مدل قوی transcriptها را مقابل rubric نمره می‌دهد
   (grounding، completeness، safety). برای داوری پرمخاطره از MoA (فصل ۰۲) استفاده کنید.
3. **suiteهای regression** — task sets ی فریز‌شده که بعد از هر تغییر (تعویض مدل، ویرایش
   prompt، آپدیت skill) دوباره اجرا می‌شوند: نمره‌ها نباید بیفتند. این همان CI برای
   agentهاست.

### دیسیپلین regression

هر تغییری در سیستم — مدل، system prompt، memory، skill، toolset ی MCP — می‌تواند رفتار را
بی‌صدا degrade کند. عادت senior: اجرای قبل/بعد روی task set ی فریز‌شده، یک metric (همان‌قدر
«تمام شد» که «token/call خرج شد»)، یک diff، و یک go/no-go. فایل‌های شواهد
`docs/research/hermes/` همین دوره *هستند* baseline ی regression برای ادعاهای tooling ی
خود دوره.

### هزینه به‌عنوان metric ی کیفیت

latency و خرج token در هر eval هستند: جوابِ «بهتر» که هزینه را دوبرابر کند دلیل می‌خواهد.
`hermes insights` قبل/بعد از تغییر routing، آن را کمیت‌بندی می‌کند.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b6-security-observability.txt`
(help ی insights/monitoring/logs)، `docs/research/hermes/cli-evidence-2026-09-07-b3-sessions-tools.txt`
(سطح export)، به‌علاوهٔ فایل‌های تحقیق خود دوره به‌عنوان نمونه‌های اجراشده.

## Verified commands

observability:

```bash
hermes monitoring status       # metricهای سلامت gateway (قابل export روی OTLP)
hermes logs -n 100 --level warning          # پویش incident
hermes logs --component gateway --since 30m
hermes insights --days 7       # توکن، هزینه، الگوی toolها
hermes insights --days 30 --source telegram # تفکیک per-source
```

مواد eval:

```bash
hermes sessions export         # transcriptها → corpus برای داوری
hermes sessions stats          # نمای جمعیتی
```

harness ی داور (cron ی script-only از فصل ۰۷ ارزان نگهش می‌دارد):

```bash
hermes cron create --name "nightly-eval" --schedule "0 3 * * *" \
  --script eval_runner.sh --deliver telegram   # stdout فقط روی regression
```

## Common pitfalls

- **eval های vibes-محور.** «حس می‌شود باهوش‌تر شد» metric نیست. taskها را فریز کنید،
  bar ی پاس را تعریف کنید، بشمارید.
- **داوری با همان مدل.** self-grading نمره‌ها را باد می‌کند؛ با مدلی متفاوت (معمولاً
  قوی‌تر) از مدلِ تحت‌تست داوری کنید.
- **فقط مشاهدهٔ مسیر خوشحالی.** `hermes logs --level error` و `cron incidents` محل
  شکست‌هاست؛ review ی که فقط transcript می‌خواند شکست‌های runtime را از دست می‌دهد.
- **بدون baseline قبل از تغییر.** regression test بدون اجرای *پیش از تغییر* نمایش است.
  قبل/بعد را همیشه بگیرید.
- **کیفیتِ کور به هزینه.** token per task را کنار pass rate ردیابی کنید؛ regressionها در
  پرش هزینه پنهان می‌شوند حتی وقتی pass rate می‌ایستد.
- **eval ی one-shot.** یک اجرا per task نویز است؛ N≥۳ per task یا نوسان را بپذیرید.

## Exercises

تمرین `exercises/ex14-evals-observability.md` را انجام دهید. راستی‌آزمایی: یک eval set ی
۵-task با چک‌های قطعی + judge ی LLM، یک اجرای regression ی قبل/بعد، ثبت تفاضل هزینه،
ساخت job ی nightly eval.
