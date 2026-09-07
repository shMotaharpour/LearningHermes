# تمرین ۰۹ — Orchestration ی چند Agent

## Objective

نردبان را سرتاسر اجرا کنید: subagentهای موازی، یک چرخهٔ حیات task ی kanban، یک peer (یا
طرح بین‌ماشینی مستند)، و بهداشت worktree.

## Tasks

1. **delegation ی موازی.** در یک session، از agent بخواهید سه موضوع مستقل را موازی
   پژوهش کند («سه subagent delegate کن، یکی برای هر موضوع، بعد merge کن»). ببینید: باید
   یک نتیجهٔ merge‌شده ببینید نه سه transcript ی درهم.
2. **دیسیپلین راستی‌آزمایی subagent.** در همان اجرا، از یک subagent بخواهید «یک فایل
   بنویسد» — بعد خودتان روی دیسک verify کنید. عادتِ verify-before-trust را ثبت کنید.
3. **چرخهٔ حیات kanban.** `hermes kanban init`؛ دو task با وابستگی parent→child با
   `link` بسازید؛ parent را در یک profile `claim` کنید؛ `complete` اش کنید؛ فرزند را
   `unblock`/promote کنید. مدرک بدون اسکرین‌شات: خروجی `hermes kanban show <id>` برای هر دو.
4. **بهداشت صف.** `hermes kanban stats` و `hermes kanban diagnostics` — نمای سلامت را ثبت کنید.
5. **peerها.** اگر ماشین/هاست دوم دارید: رفت‌وبرگشت `hermes peer add` + `hermes peer dm`.
   اگر نه: دقیقاً فرمان‌هایی که اجرا می‌کردید و جای کلید (`.env`) را بنویسید.
6. **بهداشت worktree.** `hermes worktree audit` — یافته‌ها را ثبت؛ اگر چیزی بازیافتنی
   بود `prune`. تأیید کنید هیچ کارِ commit‌نشده دست نخورد.

## Verification checklist

- [ ] یک نتیجهٔ merge‌شده از delegation ی موازی واقعی ۳تایی.
- [ ] write ی فایل توسط subagent توسط شما روی دیسک verify شد، نه با ادعای subagent.
- [ ] وابستگی parent/child ی kanban ترتیب اجرا را راند.
- [ ] رفت‌وبرگشت peer کامل شد (یا طرح فرمان‌ها نوشته شد).
- [ ] audit ی worktree اجرا شد؛ prune کارِ commit‌شده را سالم گذاشت.
