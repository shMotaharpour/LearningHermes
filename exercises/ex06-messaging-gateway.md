# تمرین ۰۶ — پیام‌رسان‌ها و Gateway

## Objective

یک پلتفرم پیام‌رسان واقعی وصل کنید، routing ی session را راستی‌آزمایی کنید و از یک
اسکریپت پیام تحویل دهید — مسیر خروجی که همهٔ اتوماسیون‌های بخش III به آن وابسته‌اند.

## Tasks

1. **وضعیت gateway.** `hermes gateway status` — ثبت کنید: سرویس فعال است؟ linger فعال
   است؟ PID؟ هشداری در خطوط لاگ اخیر؟
2. **اتصال یک پلتفرم.** اگر هیچ‌کدام نیست: `hermes gateway setup` و اتصال Telegram
   (bot token از BotFather) یا پلتفرم دلخواه. یک پیام بفرستید؛ یک جواب بگیرید.
3. **map ی session.** بعد از پیام‌تان: `hermes sessions list` — session جدید پلتفرم را
   پیدا کنید. فرمت ID اش را بنویسید. از topic/chat دوم جواب بدهید؛ ظهور session دوم را
   تأیید کنید.
4. **خروج.** از یک shell (نه agent):
   `hermes send --to <your-platform> "test from CLI"` — تحویل را تأیید کنید.
   بعد یکی پایپ کنید: `uptime | hermes send --to <target>`.
5. **تحویل رسانه.** از agent (در چت پلتفرم) بخواهید یک نمودار بسازد و برگرداند — رسیدنش
   به‌صورت attachment نیتیو را ببینید (deliverable mode).
6. **لاگ‌ها.** بلافاصله بعد از یک پیام زنده: `hermes logs --component gateway -n 50` —
   دریافت، نوبت agent و ارسال را پیدا کنید. با چیزی که در چت دیدید مقایسه کنید.

## Verification checklist

- [ ] وضعیت gateway سالم ثبت شد (سرویس فعال، linger فعال).
- [ ] رفت‌وبرگشت پلتفرم کار می‌کند: پیام در، جواب out.
- [ ] هر chat/topic به ID ی session خودش map می‌شود.
- [ ] `hermes send` هم پیام مستقیم داد هم پایپی.
- [ ] سه خط لاگ را نشان می‌دهید: receive → agent → send.
