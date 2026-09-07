# تمرین ۱۲ — Pluginها و APIها

## Objective

هر قرارداد integration را یک بار لمس کنید: بازرسی plugin، سروکردن agent روی API ی
سازگار با OpenAI و call کردنش، وصل‌کردن editor یا proxy، embed ی loop در Python.

## Tasks

1. **recon ی plugin.** `hermes plugins list`؛ یکی بردارید (داخلی یا نصب‌شده) و
   `hermes plugins capabilities` + `hermes plugins doctor` را اجرا کنید — ثبت کنید چه
   چیزی register می‌کند.
2. **رفت‌وبرگشت API server.** `hermes serve --port 8377` (localhost). از shell ی دیگر،
   یک درخواست chat به شکل OpenAI بزنید (curl یا python) با `API_SERVER_KEY`؛ یک
   completion بگیرید که tool استفاده کرده. بعدش server را ببندید.
3. **ACP یا proxy.** یکی را انتخاب کنید: وصل‌کردن editor با `hermes acp`، یا نشانه‌روی
   یک CLI با OpenAI-SDK (مثلاً aider) به `hermes proxy`. کانفیگ کارکننده را ثبت کنید.
4. **embed.** `examples/embed-agent.py` را طبق guide ی رسمی python-library بنویسید: یک
   call ی برنامه‌نویسی‌شده با tool. اجرا کنید.
5. **یادداشت تصمیم.** برای یک محصول فرضی («support-bot که مستندات ما را می‌خواند») ۵
   خط بنویسید: کدام نقطهٔ افزودن (MCP/plugin/API/embed) و چرا.

## Verification checklist

- [ ] خروجی capabilities + doctor ی plugin ثبت شد.
- [ ] رفت‌وبرگشت API با auth موفق و بعدش تمیز بسته شد.
- [ ] مسیر editor/proxy یک session ی agent-پشتیبانِ کارکننده داد.
- [ ] `examples/embed-agent.py` اجرا شد و نتیجهٔ tool-دار برگرداند.
- [ ] یادداشت تصمیم یک قرارداد را انتخاب و دفاع کرد.
