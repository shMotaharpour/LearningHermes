# تمرین ۱۳ — Shipping ی محصولات Agent

## Objective

یک تغییر کاملِ agent-رانده بشماص (repo → PR)، یک profile distribution بسته‌بندی کنید،
اعلان CI را سیم‌کشی کنید و checklist ی deployment برای یک اتوماسیون واقعی بنویسید.

## Tasks

1. **تغییر agent-authored.** در یک repo ی آزمایشی (یا همین repo روی branch): از agent
   بخواهید یک تغییر کوچک طبق قراردادهای AGENTS.md پیاده کند، با قراردادِ درست commit کند
   و PR باز کند (`gh pr create`). شما PR را مثل یک reviewer ی انسانی review کنید.
2. **انتخاب backend.** یک کار آزمایشی فصل ۰۵ را با backend ی Docker دوباره اجرا کنید
   (در صورت موجود بودن) — ثبت کنید از نظر ریسک چه فرقی کرد.
3. **توزیع.** `hermes profile export` از setup تان؛ محتوای آرشیو را بازرسی کنید (آیا
   memory/sessionها هست؟ باید باشد؟)؛ در صورت امکان در یک `$HERMES_HOME` ی آزمایشی نصبش
   کنید؛ وگرنه فرمان install را برای هم‌تیمی مستند کنید.
4. **سیم‌کشی CI.** `hermes send ... || true` را به یک اسکریپت/workflow تان اضافه کنید و
   trigger اش کنید؛ تحویل را تأیید کنید.
5. **checklist.** checklist ی deployment ی فصل ۱۳ را برای job ی cron ی فصل ۰۷ تان بنویسید
   (scope، fallback، target، approvals، observability، rollback) — شش خط، هر خط به
   فرمانی که اثباتش می‌کند اشاره کند.

## Verification checklist

- [ ] PR توسط agent باز شد، توسط شما review شد، با دلیل merge یا reject شد.
- [ ] export ی profile بازرسی و پاکسازی شد (یا آگاهانه توجیه شد).
- [ ] اعلان CI/اسکریپت با تحمل کد خروج تحویل شد.
- [ ] checklist ی شش‌خطی نوشته شد؛ هر خط به فرمانِ راستی‌آزمایی متصل است.
