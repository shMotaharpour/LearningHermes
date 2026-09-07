# تمرین ۰۸ — اتوماسیون Event-Driven

## Objective

هر سه صفحهٔ رویداد را لمس کنید: رفت‌وبرگشت webhook ی ورودی، یک hook ی lifecycle با گزارش
doctor تمیز، و اعلان اسکریپت/CI با هندل درست کد خروج.

## Tasks

1. **رفت‌وبرگشت webhook.** یک route ی تست با prompt ی payload-آگاه subscribe کنید
   («repository و event در payload را خلاصه کن»)، با `hermes webhook test` بزنید و جواب
   agent را روی تارگت تحویل بخوانید. بعد از تست، subscription را حذف کنید.
2. **الگوی GitHub (کاغذی).** یک blueprint ی واقعی PR-review را بخوانید؛ subscription ای
   که برای ریپوی تان می‌سازید را طرح بزنید (route، فیلتر، فیلدهای prompt، تارگت). هنوز
   ریپوی واقعی وصل نکنید.
3. **hook ی lifecycle.** بنویسید `audit_hook.sh` (نام رویداد + timestamp را به یک لاگ
   اضافه کند)، برای یک رویداد tool در کانفیگ declare کنید، `hermes hooks doctor` را تا
   تمیز شدن اجرا کنید، بعد trigger اش کنید و خط اضافه‌شده را نشان دهید. اگر نمی‌خواهید
   زنده بماند، revoke کنید.
4. **خروجی از CI/اسکریپت.** به یک اسکریپت/workflow تان اضافه کنید:
   `hermes send --to <target> --subject "[ops]" "task done"`؛ `$?` را بگیرید و روی آن
   branch کنید (echo ی موفقیت در برابر شکست). هر دو مسیر را اجرا کنید.
5. **چک idempotency.** همان webhook test را دو بار بزنید؛ ثبت کنید agent دو بار چه کرد و
   dedupe تان چطور می‌بود (کلید روی event ID).

## Verification checklist

- [ ] تست webhook یک جواب payload-آگاه روی تارگت داد.
- [ ] `hermes hooks doctor` برای hook ی شما تمیز؛ خط لاگ روی trigger ی واقعی اضافه شد.
- [ ] اعلان اسکریپت کدهای خروج 0 و 1 را متمایز هندل کرد.
- [ ] شکاف idempotency شناسایی و استراتژی dedupe نوشته شد.
