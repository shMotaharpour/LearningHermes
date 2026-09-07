# تمرین ۰۴ — CLI، Sessionها و Surfaceها

## Objective

سرعت و ایمنی بسازید: resume ی session با ID، rollback ی checkpoint، export ی transcript،
و خواندن لاگ در حین یک کار واقعی.

## Tasks

1. **فهرست‌برداری.** `hermes sessions stats` — جمع کل و تفکیک پلتفرم را ثبت کنید. دو
   session ای که بیشتر استفاده می‌کنید را پیدا کنید.
2. **انتخابی‌سازی.** عنوان یک session را معنادار rename کنید؛ pin اش کنید. تأیید با
   `hermes sessions pinned`.
3. **resume با ID.** `hermes --resume <ID>` روی یک session قدیمی؛ از agent بپرسید session
   درباره چه بود تا بازیابی context ثابت شود. خارج شوید.
4. **ایمنی checkpoint.** در یک دایرکتوری آزمایشی، از agent بخواهید `notes.txt` بسازد، بعد
   خرابش کند، بعد `/rollback`. بازگشت محتوا را تأیید کنید.
5. **export.** یک session را با `hermes sessions export` به Markdown ببرید؛ فایل را باز کنید.
6. **لاگ‌ها.** یک کار agent اجرا کنید، بعد `hermes logs -n 50 --since 10m` — یک خط runtime
   (gateway/provider/tool) پیدا کنید که transcript نشان نمی‌داد.
7. **بهداشت.** `hermes checkpoints status` — حجم استور را ثبت کنید. اگر بزرگ بود
   `hermes checkpoints prune` و دوباره اندازه بگیرید.

## Verification checklist

- [ ] resume ی یک session با ID ی صریح و تأیید context ی بازیابی‌شده.
- [ ] `/rollback` فایل را به وضعیت پیش از تغییر برگرداند.
- [ ] فایل export موجود و شامل transcript ی کامل.
- [ ] حداقل یک خط لاگ runtime پیدا شده که در transcript چت نبود.
- [ ] حجم استور checkpoint ثبت شده (در صورت نیاز prune شده).
