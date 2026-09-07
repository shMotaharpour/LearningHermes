# فصل ۰۸ — اتوماسیون Event-Driven

## Why this matters (job link)

یکپارچه‌سازی event-driven نیمهٔ دوم هر نقش اتوماسیون است: Adventus — «integration ی API و
orchestration ی سیستم‌های سازمانی» (`docs/research/jobs/extract-round2.json`)؛ پارامونت AI
را «مستقیم در SDLC با پلتفرم‌های مدرن» همراه تیم‌های DevOps و SRE تزریق می‌کند
(`docs/research/jobs/source-01.md`). cron به «کِی» جواب می‌دهد؛ webhook و hook به «چه
اتفاقی افتاد». push ی GitHub → agent ی review. شکست CI → خلاصهٔ incident. رسیدن ایمیل →
triage. این فصل هیرمس را به رویدادهای بیرون (webhook ی GitHub و generic)، رویدادهای
درونِ خودش (hookها) و هر اسکریپتی (با `hermes send`) سیم‌کشی می‌کند.

## Concepts

### سه صفحهٔ رویداد

1. **webhookهای ورودی** — سرویس‌های خارجی به هیرمس POST می‌زنند؛ یک subscription رویداد
   را به اجرای agent map می‌کند. `hermes webhook subscribe|list|test` (verified). رویدادهای
   PR/push/issue ی GitHub و GitLab درجه‌یک‌اند: الگوی PR-review-agent (گرفتن diff، review،
   پست کامنت) یک blueprint ی مستند است.
2. **hookهای lifecycle** — اسکریپت‌های shell در کانفیگ شما که در رویدادهای درونی agent
   (tool callها، رویدادهای session) با payload ی JSON روی stdin اجرا می‌شوند. مدیریت با
   `hermes hooks list|test|doctor|revoke` (verified — شامل allowlist ی consent و چک‌های
   «exec bit، allowlist، mtime drift، اعتبار JSON»). برای audit لاگ، هشدار و guardrail ی
   سفارشی.
3. **اعلان خروجی** — هر اسکریپت، job ی CI یا daemon با `hermes send` به پلتفرم‌های شما
   پیام می‌دهد (کدهای خروج verified: 0 موفق، 1 خطای تحویل، 2 خطای استفاده — امن برای CI).

### کالبدشناسی webhook subscription

یک subscription این‌ها را می‌بندد: source/route → فیلتر → prompt/session → تارگت تحویل.
اجرای agent تازه است (بدون تاریخچهٔ چت)، پس *payload* کلِ context است: prompt باید دقیقاً
بگوید با فیلدهای `{{payload}}` چه کند. `hermes webhook test` یک POST ی سنتتیک می‌زند —
قبل از اشاره‌کردن ریپوی واقعی GitHub به سرورتان از آن استفاده کنید.

### hookها: مدل consent

shell hookها کد دلخواه را در نقاط lifecycle ی agent اجرا می‌کنند، پس هیرمس gate‌شان
می‌کند: هر فرمان به entry ی allowlist نیاز دارد (`~/.hermes/shell-hooks-allowlist.json`
— verified)، consent ی اولین‌استفاده صریح است و `--accept-hooks` فقط hookهای دیده‌نشده را
وقتی خودتان تصمیم گرفتید auto-approve می‌کند. `hermes hooks doctor` پیش‌پرواز است:
مجوزها، allowlist، drift، اعتبار JSON، تایمینگ.

### Blueprintها

هیرمس کاتالوگ automation-blueprint دارد — الگوهای آماده برای taskهای زمان‌بندی‌شده،
triggerهای رویداد GitHub، webhook ی API و workflowهای multi-skill. آن‌ها را به‌عنوان نمونه‌های
کارشده از ترکیب سه صفحهٔ همین فصل بخوانید.

### طراحی agentهای event-driven

- **Idempotency.** GitHub تحویل‌ها را retry می‌کند؛ agent ی review که روی retry دوبار
  پست کند باگ است. actionها را روی event ID کلید بزنید.
- **کمترین context.** اجرای webhook تاریخچهٔ گفتگو ندارد — payload + prompt کل دنیاست.
  فیلدهای دقیق را نام ببرید؛ «در runtime بفهم» نکنید.
- **دیسیپلین fan-out.** یک رویداد → یک اجرای agent → یک deliverable. استدلال عمیق‌تر را
  با delegation (فصل ۰۹) زنجیر کنید، نه با چاق‌کردن prompt.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b4-gateway-cron-events.txt`
(درخت‌های فرمان webhook و hooks با معناشناسی کامل)،
`docs/research/hermes/cli-evidence-2026-09-07.txt` (help ی hermes send + کدهای خروج).

## Verified commands

webhook ورودی:

```bash
hermes webhook list                 # همهٔ subscriptionهای پویا
hermes webhook subscribe            # ساخت: route، فیلتر، prompt، تارگت
hermes webhook test <route>         # POST ی سنتتیک — قبل از سورس واقعی راستی‌آزمایی
hermes webhook remove <id>
```

hookهای lifecycle:

```bash
hermes hooks list                   # matcher، timeout، وضعیت consent
hermes hooks test <event>           # اجرا روی payload ی سنتتیک
hermes hooks doctor                 # exec bit، allowlist، drift، JSON، تایمینگ
hermes hooks revoke <command>       # حذف entry ی allowlist (با ری‌استارت اعمال می‌شود)
```

خروجی از هر جا (نمونهٔ CI):

```bash
# .github/workflows/deploy.yml — بعد از مرحلهٔ deploy:
#   run: hermes send --to telegram "#deploy finished on $GITHUB_REF" || true
hermes send --to telegram "build ok"         # exit 0 = پذیرفته شد
echo "err" | hermes send --to telegram --subject "[CI]"   # خط موضوع
```

## Common pitfalls

- **افشای خام endpoint ی webhook.** subscription باید سورس را validate کند (secret
  token/path)؛ trigger ی عمومی agent یعنی تزریق prompt به‌عنوان RCE. سخت‌سازی کامل در فصل ۱۵.
- **prompt ی ناآگاه از payload.** subscription ای که payload را نادیده می‌گیرد جواب‌های
  generic می‌دهد. فیلدهای مورد انتظار را نام ببرید.
- **اسکریپت hook بدون exec bit / نسخهٔ کهنه.** `hermes hooks doctor` دقیقاً برای همین
  است که این‌ها بی‌صدا شکست می‌خورند — بعد از هر ویرایش hook اجرایش کنید.
- **accept کردن reflexive ی hookها.** `--accept-hooks` consent ی اولین‌استفاده را رد
  می‌کند — در ایمیج‌های CI ی خودتان استفاده کنید، روی ماشینی که مال شما نیست هرگز.
- **fire-and-forget بدون چک کد خروج.** در CI، exit 1 ی `hermes send` حداقل یک هشدار build
  است؛ گم‌شدن بی‌صدای اعلان، incident ها را پنهان می‌کند.
- **تحویل مضاعف روی retry.** agent ی غیر-idempotent + retry ی پلتفرم = کامنت/پیام تکراری.
  روی event ID dedupe کنید.

## Exercises

تمرین `exercises/ex08-event-driven-automation.md` را انجام دهید. راستی‌آزمایی: subscribe و
test ی webhook، یک hook با وضعیت doctor ی تمیز، یک اعلان CI/اسکریپت با هندل کد خروج.
