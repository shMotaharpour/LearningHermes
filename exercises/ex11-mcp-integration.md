# تمرین ۱۱ — یکپارچه‌سازی MCP

## Objective

مصرف، فیلتر، expose: یک MCP ی کاتالوگ نصب کنید، toolهایش را scope کنید، یک stdio server ی
سفارشی حداقلی بنویسید که agent صدا بزند، و یک بار حالت server را هم ببینید.

## Tasks

1. **نصب از کاتالوگ.** `hermes mcp catalog` → یک server ی منطبق با استفادهٔ تان (یا یکی
   read-only بی‌خطر) بردارید؛ `hermes mcp install <name>`؛ در صورت OAuth احراز را کامل کنید.
2. **صدا بزنید.** در یک session یکی از toolهایش را از طریق agent invoke کنید. نام
   `server:tool` ی استفاده‌شده را ثبت کنید.
3. **فیلتر.** `hermes tools list` — toolهای server را پیدا کنید؛ همه جز دو تا را با
   `hermes tools disable` خاموش کنید. prompt-size را قبل/بعد اندازه بگیرید
   (`hermes prompt-size`).
4. **server ی سفارشی.** یک stdio server ی ~۳۰ خطی با یک tool بنویسید (`roll_dice` یا
   `now_in_city` — قطعی، بدون secret). `hermes mcp add` کنید، `hermes mcp test` کنید،
   بعد agent را وادار به call کنید. فایل را در `examples/mcp-notes-server/` نگه دارید.
5. **نردبان شکست.** server ی سفارشی را خراب کنید (مسیر بد)، ببینید: `mcp list` ok →
   `mcp test` fail → call ی agent fail. درستش کنید، دوباره تست.
6. **حالت server (فقط خواندنی).** `hermes mcp serve --help` را اجرا کنید؛ مستند کنید
   (باقی نگذارید روشن باشد) که agent ی دیگر چطور وصل می‌شود و `API_SERVER_KEY` از چه
   محافظت می‌کند.

## Verification checklist

- [ ] server ی کاتالوگ نصب شد، tool صدا زده شد، toolها فیلتر شدند (تفاضل prompt-size ثبت شد).
- [ ] stdio server ی سفارشی add، test و با موفقیت توسط agent invoke شد.
- [ ] نردبان دیباگ چهارمرحله‌ای را از حافظه می‌روید.
- [ ] طرح expose ی server-mode نوشته شد (چه کسی احراز می‌کند، چه چیزی expose می‌شود).
