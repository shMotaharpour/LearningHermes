# تمرین ۱۴ — Evals و Observability

## Objective

یک harness ی eval کوچک ولی واقعی و یک عادت observability بسازید: taskهای فریز، چک‌های
قطعی، judge ی LLM، یک اجرای regression، و job ی nightly eval.

## Tasks

1. **پویش observability.** هر چهار تا را اجرا کنید: `hermes monitoring status`،
   `hermes logs --level warning --since 24h`، `hermes insights --days 7`،
   `hermes sessions stats`. برای هر لایه یک جمله بنویسید: دربارهٔ *استفاده ی خودتان* چه
   می‌گوید.
2. **eval set.** ۵ task ی فریز تعریف کنید (از کارهای فصل ۰۵/۰۷): مثلاً «شمارش فایل‌های
   دایرکتوری X»، «استخراج abstract این PDF»، «گزارش وضعیت cron». برای هرکدام:
   command/prompt و یک چک ی قطعی (فایل موجود، JSON قابل parse، خروجی حاوی Y).
3. **اجرای baseline.** ۵ task را ۳ بار با مدل فعلی اجرا کنید؛ pass/fail + توکن تقریبی هر
   task را ثبت کنید.
4. **judge ی LLM.** برای دو task ی بازتر، judge ی rubric اضافه کنید: transcript را export
   کنید (`hermes sessions export`)، از یک مدلِ *متفاوت* نمرهٔ grounding + completeness
   ۱–۵ بخواهید. نمره‌ها را ثبت کنید.
5. **اجرای regression.** یک تغییر واقعی بدهید (تعویض مدل default با `hermes config set`)؛
   set را دوباره اجرا کنید؛ pass rate و هزینه را diff کنید. اگر regression بود برگردید.
6. **harness ی شبانه.** مراحل ۳–۴ را در `eval_runner.sh` بپیچید که فقط روی regression چاپ
   کند؛ به‌عنوان job ی script-only سیم‌کشی کنید (الگوی فصل ۰۷).

## Verification checklist

- [ ] پویش چهارلایهٔ observability با مشاهدات نوشته‌شده.
- [ ] eval set ی ۵-task با چک قطعی و baseline ی ۳× ثبت شد.
- [ ] نمره‌های judge از مدلی متفاوت از مدلِ تحت‌تست.
- [ ] یک diff ی قبل/بعد شامل تفاضل هزینه، با تصمیمِ مستند.
- [ ] job ی nightly eval زنده و در حالت پاس، ساکت.
