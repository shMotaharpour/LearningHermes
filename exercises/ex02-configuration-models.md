# تمرین ۰۲ — کانفیگ و Modelها

## Objective

یک setup ی routing شخصی بسازید: aliasهای نام‌دار برای tierهای هزینه، زنجیرهٔ fallback، و
توانایی بازرسیِ خرج.

## Tasks

1. **مبنا.** `hermes config get model` — default و provider فعلی را ثبت کنید.
2. **ناوگان دولایه.** یک مدل قوی/گران و یک مدل سریع/ارزان از کاتالوگ provider تان
   انتخاب کنید (`hermes model` برای مرور).
3. **وضعیت MoA و fallback.** `hermes moa list` و `hermes fallback list` — نقطهٔ شروع را ثبت کنید.
4. **افزودن یک fallback** برای provider ی default:
   `hermes fallback add <provider>/<model>`، سپس تأیید با `hermes fallback list`.
5. **بازبینی هزینه.** `hermes insights --days 7`. پرکاربردترین مدل تان را پیدا کنید و
   تخمین بزنید چه سهمی از callها می‌تواند روی tier ارزان‌تر برود.
6. **بهداشت کانفیگ.** `hermes config check` — موارد علام‌خورده را حل کنید. با
   `hermes config path` مطمئن شوید secretی در config.yaml نیست
   (`grep -iE 'key|token|secret' $(hermes config path)` باید تمیز باشد).

## Verification checklist

- [ ] `hermes fallback list` مدل backup تان را نشان می‌دهد.
- [ ] می‌توانید مدل default فعلی، provider و tier ی حدودی هزینه‌اش را نام ببرید.
- [ ] `hermes config check` پاس می‌شود.
- [ ] هیچ API key داخل config.yaml نیست.
