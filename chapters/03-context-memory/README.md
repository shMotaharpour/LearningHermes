# فصل ۰۳ — Context و Memory

## Why this matters (job link)

RAG و context engineering تقریباً در همهٔ آگهی‌های applied هست: پارامونت «بهینه‌سازی
chunking و retrieval ... تکنیک‌های کاهش hallucination و grounding» می‌خواهد
(`docs/research/jobs/source-01.md`)؛ 100ms «استراتژی‌های retrieval ... اطمینان از
هم‌راستایی رفتار agent با انتظارات کاربر» می‌خواهد (`docs/research/jobs/source-05.md`).
قبل از vector database، حقیقت ساده‌تر را مسلط شوید: **پنجرهٔ context ی agent همان سیستم
retrieval است.** هیرمس یک پشتهٔ context کامل دارد — context file، memory ماندگار، memory
provider، reference، compression، caching — و این فصل به شما یاد می‌دهد دربارهٔ تک‌تک
tokenهای prompt استدلال کنید. این مهارت مستقیماً به طراحی RAG تعمیم می‌یابد: چه چیزی تزریق
شود، چه چیزی index شود، چه چیزی retrieve شود، چه چیزی حذف شود.

## Concepts

### چهار context file — چه کسی می‌نویسد، کِی دیده می‌شود

| فایل | نویسنده | کِی دیده می‌شود | نقش |
|---|---|---|---|
| `SOUL.md` | شما (global) | هر session، همهٔ پروژه‌ها | هویت، لحن، قواعد دائمی |
| `USER.md` | agent | هر session | factهای ماندگار دربارهٔ کاربر |
| `MEMORY.md` | agent | هر session | یادداشت‌های خود agent برای سازگاری بین-session |
| `AGENTS.md` / `.hermes.md` / `CLAUDE.md` | نویسندگان پروژه | فقط sessionهای آن پروژه | قواعد repo، قراردادها، دستورات |

این ریپو خودش فایل‌های `chapters/NN-*/AGENTS.md` دارد — این *خودِ* فصل ۰۳ در عمل است:
هر agentی که وارد دایرکتوری فصل شود بدون تکرار، قرارداد نگارش را به ارث می‌برد. قانون
جای‌گذاری: **قراردادهای repo در repo، هویت در SOUL.md، factها در memory.**
آلودگی متقابل (قواعد پروژه در SOUL.md) agent را در پروژه‌های دیگر بدرفتار می‌کند.

### بودجهٔ prompt، اندازه‌گیری‌شده

`hermes prompt-size --json` (verified زنده در evidence b8) system prompt ثابت را روی این
ماشین لایه‌به‌لایه شکست می‌دهد:

```
system_prompt   28,738 chars   <- هویت + قواعد + مستند toolها
skills_index    10,627 chars   <- یک خط به‌ازای هر skill نصب‌شده (~۹۰ skill)
memory           3,556 chars   <- تزریق MEMORY.md + USER.md
user_profile     1,426 chars
tools (count 21) + schemaهای JSON
```

پلتفرم هم مهم است: telegram حدود ۲۸۰ کاراکتر کمتر از CLI اندازه می‌گیرد (لایهٔ پلتفرم
فرق دارد). دو نتیجه:

1. **همه‌چیز برای یک پنجره رقابت می‌کنند.** اضافه‌کردن MCP server جدید یا ۲۰ skill دیگر
   مالیات هر session آینده است. بعد از هر integration دوباره اندازه بگیرید.
2. «agent ام کندتر شده» معمولاً حساب‌وکتاب است، نه شعبده. memory یا skills index چاق،
   جای کارِ واقعی را می‌گیرد. با `prompt-size` تشخیص دهید.

### compression ی session در برابر memory ی ماندگار

درون session، context با هر پیام رشد می‌کند؛ زیر فشار هیرمس **compress** می‌کند — تاریخچهٔ
کلمه‌به‌کلمه را با خلاصه جایگزین می‌کند. compression حدس‌زننده، درون-session و امداد
اضطراری است و هرگز جای نوشتن factهای ماندگار در memory را نمی‌گیرد. بین sessionها،
`MEMORY.md`/`USER.md` پیوستگی می‌دهند. pluginهای **memory provider** خارجی (honcho، mem0،
hindsight، byterover، holographic، openviking — verified با `hermes memory status`) وقتی
memory ی ساختاریافته یا بین-profile می‌خواهید، استور داخلی را جایگزین می‌کنند.

### skillها context ی تنبل هستند

*index* ی skillها در هر prompt سوار است (~10.6K chars)؛ *بدنه* ی skillها فقط هنگام استفاده
لود می‌شود (progressive disclosure). همان اقتصاد RAG است: index کوچک، payload در صورت
نیاز. این الگو را همین‌جا درونی کنید؛ فصل ۱۰ از آن بهره‌برداری می‌کند.

### context reference ها

سینتکس `@` مِترِال را درون پیام ضمیمه می‌کند — فایل، پوشه، git diff، URL — به‌جای این
امید که agent خودش فایل درست را دوباره بخواند. صریح بهتر از محیطی: دقیقاً همان چیز را
reference کنید.

### prompt caching

providerها پیشوندِ تغییریافتهٔ prompt را cache می‌کنند؛ هیرمس با جابه‌جا نکردن system prompt
میان-session پایداری cache را حفظ می‌کند. قواعد عملی: وسط گفتگو فایل‌های global را
دستکاری نکنید، toolsetها را بین پیام‌ها toggle نکنید، سؤال‌های مرتبط را در یک session
انجام دهید. cache hit همان فرق بین token تمام‌قیمت و تخفیفی است.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b8-context-memory.txt`
(`memory status` زنده با لیست providerها، `prompt-size --json` کامل برای CLI و telegram،
چیدمان `~/.hermes/`).

## Verified commands

اندازه‌گیری بودجهٔ prompt:

```bash
hermes prompt-size                    # تفکیک لایه‌ها به‌صورت خوانا
hermes prompt-size --json             # ماشینی‌خوان
hermes prompt-size --platform telegram --json   # تفاوت پلتفرم (verified: ~۲۸۰ char کمتر)
```

زیرسیستم memory (خروجی verified):

```
$ hermes memory status
  Built-in (MEMORY.md / USER.md):
    Memory injection:   enabled ✓
    User profile:       enabled ✓
    Memory tool:        enabled ✓
  Provider:  (none — built-in only)
  Installed plugins: byterover, hindsight, holographic ...
```

```bash
hermes memory setup        # کانفیگ provider خارجی
hermes memory off          # حالت حریم خصوصی: بدون تزریق memory
```

استور session (حافظهٔ سند):

```bash
hermes sessions stats      # verified: 21 sessions, 5972 messages, 29.5 MB
hermes sessions list       # عنوان‌ها + آخرین فعالیت + IDها
hermes sessions browse     # picker ی تعاملی: جستجو + resume
hermes sessions export     # خروجی JSONL/Markdown برای تحلیل
```

## Common pitfalls

- **پرکردن MEMORY.md.** memory به هر session آینده تزریق می‌شود؛ چاقیِ آن مالیات همهٔ
  آن‌هاست. بی‌رحمانه هرس کنید؛ هر چیزی که با یک lookup دوباره ساخته می‌شود حذف شود.
- **قواعد پروژه در فایل‌های global.** SOUL.md برای هویت است نه قراردادهای `pytest` یک
  repo. قواعد repo در خود repo.
- **فرض حافظهٔ هفتهٔ پیش.** بدون memory write صریح، sessionها خالی شروع می‌کنند. به agent
  بگویید fact را ذخیره کند یا memory tool را اسکریپت کنید.
- **بی‌توجهی به prompt-size بعد از نصب‌ها.** هر MCP server، toolset و skill بودجهٔ ثابت را
  زیاد می‌کند. قبل/بعد از هر تغییر integration اندازه بگیرید.
- **اشتباه compression با memory.** خلاصه‌های compress شده چسبِ session هستند، نه دانش
  ماندگار.
- **تغییر context وسط session.** ویرایش SOUL.md یا toggle کردن toolsetها وسط گفتگو cache
  را می‌شکند و کل session را دوباره قیمت‌گذاری می‌کند.

## Exercises

تمرین `exercises/ex03-context-memory.md` را انجام دهید. راستی‌آزمایی: JSON ی prompt-size
لایه‌به‌لایه توضیح‌داده‌شده، یک AGENTS.md پروژه نوشته و اطاعت‌شده، یک memory write و یک
prune اندازه‌گیری‌شده.
