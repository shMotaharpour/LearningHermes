# فصل ۱۰ — مهندسی Skill

## Why this matters (job link)

آگهی‌ها مدام آدم‌هایی می‌خواهند که *tooling و سیستم‌های دانش داخلی* بسازند: 100ms —
«توسعهٔ tooling ی داخلی برای تسریع چرخه‌های evaluation، annotation و iteration»
(`docs/research/jobs/source-05.md`)؛ پارامونت — «ساخت LLM tool برای تولید test case...
ساخت دادهٔ تست سنتتیک» (`docs/research/jobs/source-01.md`). جواب هیرمس skillهاست:
بسته‌های رویه‌ای قابل استفادهٔ مجدد که خودِ agent می‌نویسد، on-demand لود می‌کند و در طول
زمان بهتر می‌کند. بعد از این فصل می‌توانید هر workflow ی که دو بار تکرار کرده‌اید به یک
asset ی نصب‌شدنی تبدیل کنید — همان‌طور که این ریپوی دوره به agentها یاد می‌دهد خودش را
نگه دارد (`.hermes/skills/learninghermes-authoring/`).

## Concepts

### skill چیست

skill یک دایرکتوری با `SKILL.md` است: frontmatter ی YAML (name، description) + بدنهٔ
markdown ی رویه. **description** در index ی skillهای هر session سوار است (فصل ۰۳ نشان داد
~10.6K chars برای ~۹۰ skill)؛ **بدنه** فقط وقتی لود می‌شود که agent (یا شما، با `/skill`)
بکشد. skillها می‌توانند فایل‌های پیوسته داشته باشند — reference، template، script — که
نسبت به دایرکتوری skill resolve می‌شوند.

```markdown
---
name: my-deploy-runbook
description: "Use when deploying the api service — steps, checks, rollback."
---
# Deploy runbook
1. ...
```

### skillها کجا زندگی می‌کنند

| محل | scope | کِی لود می‌شود |
|---|---|---|
| `~/.hermes/skills/` | global ی کاربر | هر session |
| `<repo>/.hermes/skills/` | پروژه | sessionهای همان repo **بعد از trust** |
| کاتالوگ‌های bundled/optional | همراه هیرمس | فعال‌سازی با config |

مدل trust صریح است (verified `hermes skills trust/untrust`): skillهای repo-محل فقط برای
ریپوهای trusted لود می‌شوند — یک دفاع prompt-injection، نه یک راحتی.

### اقتصاد progressive disclosure

خط index = فقط description (شروعش را ~۵۷ کاراکترِ trigger ی خودکفا کنید: «Use when X.
Behavior.»). بدنه = رویهٔ کامل، هزینهٔ ایستا صفر. همان معاملهٔ index/payload ی RAG است؛
descriptionها را مثل کوئریِ بهینه‌شده برای retrieval بنویسید.

### curator: skillها به‌عنوان سیستمِ نگهداری‌شده

`hermes curator` (verified) نگهداری پس‌زمینه است: ردیابی استفاده، تشخیص کهنگی، آرشیو، و
review ی LLM-محور skillهای agent-ساخته. با `hermes skills check|update|audit|diff|
list-modified`، skillها به زیرساختِ نسخه‌دار تبدیل می‌شوند — نه حال‌وهوایی در یک پوشهٔ prompt.

### رجیستری و publish

`hermes skills search|install|inspect|publish` (verified) به رجیستری‌ها می‌رسد
(skills.sh، endpointهای well-known، GitHub). نصب قبل از فرود قابل بازرسی است:
`hermes skills inspect <id>` محتوا را بدون نصب پیش‌نمایش می‌کند — skillها را مثل
dependency بخوانید.

### دیسیپلین نگارش (قرارداد خود این دوره)

1. description = شرط trigger، نه تبلیغ.
2. بدنه = رویه با دستورات verified ی دقیق — همان قاعدهٔ فصل‌ها.
3. فایل پیوسته برای reference/template/script؛ SKILL.md را لاغر نگه دارید.
4. name = lowercase-hyphen، پایدار؛ rename یعنی شکستن هر ارجاع.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b5-skills-mcp-plugins.txt`
(جدول زندهٔ skills list شامل ستون‌های Trust/Status، help ی inspect)،
`docs/research/hermes/cli-evidence-2026-09-07.txt` (درخت کامل skills با
trust/publish/audit). مدرک زندهٔ وجود-در-عمل: فایل
`.hermes/skills/learninghermes-authoring/SKILL.md` در همین repo.

## Verified commands

فهرست و چرخهٔ حیات:

```bash
hermes skills list              # جدول name/category/source/trust/status
hermes skills search <query>    # رجیستری‌ها
hermes skills inspect <id>      # پیش‌نمایش بدون نصب
hermes skills install <id>      # نصب از رجیستری
hermes skills uninstall <id>
hermes skills config            # enable/disable تعاملی
```

trust و skillهای پروژه:

```bash
hermes skills trust <repo>      # اجازهٔ لود skillهای repo-محل
hermes skills untrust <repo>    # لغو
```

نگهداری:

```bash
hermes skills check             # skillهای hub: آپدیت هست؟
hermes skills update            # اعمال آپدیت‌ها
hermes skills audit             # re-scan ی skillهای نصب‌شده
hermes skills diff <skill>      # ویرایش‌های شما در برابر نسخهٔ اصلی
hermes skills list-modified     # چه چیزهایی را شخصی‌سازی کرده‌اید
hermes skills publish           # انتشار skill به رجیستری
```

## Common pitfalls

- **چاقی description.** description ی پاراگرافی، index ی هر session را چاق می‌کند. یک
  خط: trigger + behavior.
- **رویه در SOUL.md/MEMORY.md به‌جای skill.** memory برای fact است؛ skill برای رویه.
  runbook ای که در memory زندگی کند غیرقابل‌بازبینی و غیرقابل‌اشتراک است.
- **رد کردن `inspect` قبل از install.** skillهای ثالث context ی تزریقی‌اند — مثل کدِ
  غریبه بخوانیدشان.
- **skill ی پروژه بدون trust بی‌صدا لود نمی‌شود.** repo ی جدید با skill + هیچی لود
  نشد؟ `hermes skills trust` را نزده‌اید.
- **ویرایش skillهای bundled درجا.** `update` با شما می‌جنگد؛ آگاهانه از
  `list-modified`/`diff` استفاده کنید یا به skill ی خودتان fork کنید.
- **رانش نام.** ارجاع به `my-skill` در promptهای cron بعد از rename به `my-skill-v2`
  اتوماسیون را می‌شکند — نام‌ها را پایدار نگه دارید.

## Exercises

تمرین `exercises/ex10-skills-engineering.md` را انجام دهید. راستی‌آزمایی: یک skill ی
تألیفی، لود on-demand، یک skill ی رجیستری inspect-سپس-install، تمرین مدل trust.
