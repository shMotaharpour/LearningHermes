# LearningHermes

یک دورهٔ ساختارمند و پروژه‌محور برای تسلط بر [Hermes Agent](https://github.com/NousResearch/hermes-agent)
و رسیدن به سطح **Senior Applied AI Engineer** — از اولین session تا shipping سیستم‌های agent
در production. هر فصل به شایستگی‌هایی نگاشت شده که از آگهی‌های شغلی واقعی استخراج شده و
دستوراتش با رفتار واقعی Hermes راستی‌آزمایی شده است.

**دورهٔ دوزبانه:** برنچ `english` مبنا (base) است؛ برنچ `farsi` ترجمهٔ کامل فارسی است
(اصطلاحات تخصصی انگلیسی حفظ شده‌اند). محتوای دو برنچ از نظر ساختار کاملاً برابر است.

## دوره

- **سرفصل کامل:** [CURRICULUM.md](CURRICULUM.md) — ۵ بخش، ۱۶ فصل، نگاشت شایستگی‌ها.
- **مسیر پیشرفت:** Agent Operator ← Agent Power User ← Automation Engineer ←
  Agent Developer ← Senior Applied AI Engineer.

## ساختار ریپو (agent-based)

```
AGENTS.md                  # دستورالعمل root برای هر agentی که در این ریپو کار می‌کند
chapters/                  # ۱۶ فصل در ۵ بخش — یک دایرکتوری برای هر فصل
  NN-slug/
    README.md              # محتوای فصل: مفاهیم ← دستورات verified ← pitfalls ← exercises
    AGENTS.md              # قواعد نگارش همان فصل برای agentها
    notes.md               # (اختیاری) یادداشت‌های پیش‌نویس؛ قبل از انتشار حذف می‌شود
exercises/                 # یک تمرین عملی برای هر فصل (exNN-<slug>.md)
examples/                  # کانفیگ‌ها، promptها و اسکریپت‌های قابل اجرا
assets/                    # نمودارها و اسکرین‌شات‌ها
docs/
  research/
    hermes/                # خروجی‌های verified از CLI هیرمس + snapshot ای از llms.txt
    jobs/                  # تحقیق بازار کار: آگهی‌ها، سرچ‌ها، ledger
scripts/                   # ابزارهای ریپو (validate_course.py و ...)
tests/                     # تست اسکریپت‌های ریپو
.hermes/
  skills/                  # skillهای project-local که agentها هنگام کار اینجا load می‌کنند
  settings.json            # تنظیمات project-scoped
```

## روش مطالعهٔ دوره

- اول `CURRICULUM.md` را بخوان، بعد فصل‌ها را به‌ترتیب داخل هر بخش پیش برو.
- هر فصل با exercises در `exercises/` تمام می‌شود — آن‌ها را روی یک ماشین واقعی انجام بده.
- بلوک‌های کد، دستوراتِ دقیق و verified هستند. سند هر ادعا در `docs/research/` موجود است.

## برای agentهایی که در این ریپو کار می‌کنند

قبل از هر کاری `AGENTS.md` (در root) را بخوان — workflow نگارش، الزامات راستی‌آزمایی،
قواعد commit و قواعد برنچ‌های دوزبانه همان‌جا تعریف شده است.

## مشارکت / Workflow

- برنچ مبنا: `english`. برنچ ترجمه: `farsi`.
- هر دستور Hermes را قبل از ورود به فصل با رفتار واقعی راستی‌آزمایی کن؛ خروجی خام را در
  `docs/research/hermes/` ذخیره کن.
- فصل‌ها فشرده بمانند: مفهوم ← دستور دقیق ← تمرین. بدون نثر تبلیغاتی.
- فرمت commit: `chNN: <short description>` (مثلاً `ch07: add cron notepad reference`).
- اعتبارسنجی ساختار/برابری: `python3 scripts/validate_course.py --root .` (برای مقایسهٔ
  دو checkout با `--other <path>`).

## منابع اصلی (Sources of Truth)

- ایندکس مستندات رسمی: https://hermes-agent.nousresearch.com/docs/llms.txt
- سورس Hermes: https://github.com/NousResearch/hermes-agent
- شواهد بازار کار: `docs/research/jobs/`
