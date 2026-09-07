# AGENTS.md — LearningHermes (ریشهٔ ریپو)

ریپوی کتاب‌گونهٔ دورهٔ Hermes Agent. Markdown-محور، بدون build step. هر agent ای
(Hermes، Claude Code، Codex یا ویرایشگر انسانی) که در این ریپو کار می‌کند باید این قواعد را رعایت کند.

## هویت

- دوره: LearningHermes — از Hermes Agent تا Senior Applied AI Engineer.
- سرفصل مرجع: `CURRICULUM.md`. بدون به‌روزرسانی هم‌زمانِ این فایل، `README.md` ریشه و
  `scripts/validate_course.py` فصلی را اضافه/تغییرنام/جابه‌جا نکن.
- برنچ مبنا: `english`. برنچ ترجمه: `farsi`. هر دو برنچ درخت فایل یکسان دارند؛ فقط زبان نثر فرق می‌کند.

## قواعد زبان (وابسته به برنچ)

- برنچ `english`: همهٔ فایل‌ها فقط انگلیسی. هیچ فارسی در هیچ فایل tracked.
- برنچ `farsi`: نثر آموزشی (محتوای `.md` بیرون از کد) فارسی است؛ اصطلاحات متداول و تخصصی
  انگلیسی (agent، tool، skill، session، cron، webhook، eval، RAG، MCP، ...) به انگلیسی می‌مانند؛
  بلوک‌های کد، دستورات، pathها، کلیدهای frontmatter و نام فایل‌ها انگلیسی می‌مانند.
- پیام‌های commit همیشه انگلیسی‌اند، با فرمت `chNN: <description>` یا `repo: <description>`.

## قانون راستی‌آزمایی (اینوariant اصلی)

هرگز ادعای راستی‌آزمایی‌نشده دربارهٔ Hermes را وارد فصل نکن.

1. دستور واقعی را اجرا کن (`hermes ...`) یا صفحهٔ مستندات رسمی را بگیر.
2. شواهد خام را زیر `docs/research/hermes/` ذخیره کن (مثلاً `cli-evidence-YYYY-MM-DD.txt`).
3. از داخل فصلی که از دستورات استفاده می‌کند به فایل شواهد ارجاع بده.
4. اگر قابلیتی به‌صورت زنده قابل راستی‌آزمایی نبود، به‌جای ساخت خروجی، URL صفحهٔ مستندات را
   داخل متن بیاور. ایندکس مستندات: https://hermes-agent.nousresearch.com/docs/llms.txt

## قرارداد فصل

هر دایرکتوری فصل `chapters/NN-slug/` شامل:

- `README.md` با دقیقاً این سکشن‌ها (به همین ترتیب):
  `## Why this matters (job link)` · `## Concepts` · `## Verified commands` ·
  `## Common pitfalls` · `## Exercises`
- اختیاری: `notes.md` برای پیش‌نویس؛ قبل از انتشار حذف شود.
- `AGENTS.md` با قواعد نگارش مخصوص همان فصل و اشاره‌گرهای تحقیق.

هر فصل یک فایل تمرین متناظر دارد: `exercises/exNN-<slug>.md` شامل: هدف، taskهای شماره‌دار،
و checklist ی راستی‌آزمایی (دستوراتی که یادگیرنده برای تأیید موفقیت اجرا می‌کند).

## سبک نگارش

- مفهوم ← دستور دقیق ← تمرین. بدون نثر پرکننده، بدون متن تبلیغاتی.
- paraphrase را به خروجی واقعیِ verified ترجیح بده؛ دستور را نشان بده، بعد خروجی را.
- هر فصل فقط در دامنهٔ CURRICULUM.md خودش بماند؛ به‌جای تکرار، cross-link کن.

## ابزارهای ریپو

- `python3 scripts/validate_course.py --root .` — اعتبارسنجی قرارداد فصل + ارجاع شواهد.
  `--other <path>` برابری ساختاری با checkout ی برنچ دیگر را مقایسه می‌کند
  (فایل‌های یکسان، تعداد code block برابر).
- `python3 -m unittest tests.test_validate_course` — تست اسکریپت‌های ریپو.
- چیزی بیرون از این ریپو را دستکاری نکن (کانفیگ Hermes در `~/.hermes/` فقط مرجعِ
  read-only است، هرگز برای نگارش دوره تغییر داده نمی‌شود).

## Git و تحویل

- روی branch کار کن؛ هر فصل (یا یک تغییر ساختاری) یک سری commit.
- قبل از push کردن برنچ `farsi`، چک parity را در برابر `english` اجرا کن.
- هرگز secret، API key، token یا محتوای شخصی `.env` را commit نکن. فایل‌های تحقیق باید
  عاری از credential باشند.
