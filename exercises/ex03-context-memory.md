# تمرین ۰۳ — Context و Memory

## Objective

پنجرهٔ context را مرئی کنید و عامدانه مدیریتش کنید: اندازه‌گیری لایه‌ها، نگارش context ی
پروژه، و تمرین کامل سیستم memory.

## Tasks

1. **اندازه‌گیری مبنا.** `hermes prompt-size --json`. تعداد کاراکتر هر لایه را بنویسید:
   system_prompt، skills_index، memory، user_profile، tools.
2. **تفاضل پلتفرم.** دوباره با `--platform telegram` اجرا کنید. کجا فرق دارد و چرا؟
3. **نگارش context ی پروژه.** در یک پروژهٔ واقعی خودتان یک `AGENTS.md` بسازید: پروژه چیست،
   قواعد زبان/فرمت، دستورات تست. یک session ی agent در آن دایرکتوری باز کنید و تأیید کنید
   بدون گفتن، یک قاعدهٔ فایل را رعایت می‌کند.
4. **مشاهدهٔ memory write.** به agent بگویید: «یادت باشد timezone ی من X است.» بعد چک
   کنید کدام فایل تغییر کرد (زیر `~/.hermes/`) و در یک session *جدید* ماندگاری fact را
   تأیید کنید.
5. **بهداشت memory.** فایل memory را audit کنید: یک entry ی قدیمی را حذف و دلیلش را بنویسید.
6. **اندازه‌گیری مجدد.** `hermes prompt-size --json` — مقایسهٔ اندازهٔ لایهٔ memory قبل و
   بعد از write + prune.

## Verification checklist

- [ ] چهار context file را با نویسندهٔ هرکدام نام می‌برید.
- [ ] خروجی `hermes prompt-size --json` را لایه‌به‌لایه به زبان خودتان توضیح می‌دهید.
- [ ] یک AGENTS.md پروژه وجود دارد و رفتار agent در آن پروژه را عوض می‌کند.
- [ ] یک memory write و یک prune انجام شده؛ اثر بودجه اندازه‌گیری شده.
