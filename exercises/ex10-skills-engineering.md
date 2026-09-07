# تمرین ۱۰ — مهندسی Skill

## Objective

از workflow ای که واقعاً دوبار تکرار کرده‌اید یک skill ی اصیل بنویسید، یک skill ی ثالث
با بازرسی کامل نصب کنید، و مدل trust را تمرین کنید.

## Tasks

1. **استخراج workflow.** کاری که ≥۲ بار با هیرمس کرده‌اید (گزارش، چک ی deploy، خط لولهٔ
   تحلیل) بردارید. `SKILL.md` اش را بنویسید: description ی trigger ی یک‌خطی، مراحل
   verified ی شماره‌دار، یک فایل reference ی پیوسته.
2. **نصب.** زیر `~/.hermes/skills/<name>/` (یا `.hermes/skills/` ی repo + trust)
   بگذارید. تأیید با `hermes skills list`.
3. **تست trigger.** session ی جدید؛ trigger ی زبان‌طبیعی را بگویید («دوباره api را deploy
   کن») — agent باید بدون گفتن skill را لود کند. اگر نشد، description را تیز کنید.
4. **skill ی رجیستری.** `hermes skills search` برای چیزی مرتبط؛ `hermes skills inspect`؛
   بدنه را نقادانه بخوانید؛ فقط بعد `install`. چیزهایی که چک کردید را ثبت کنید.
5. **رزمایش trust.** در repo ی untrusted حاوی skill، تأیید کنید لود نمی‌شوند؛
   `hermes skills trust` را بزنید؛ دوباره چک کنید.
6. **نگهداری.** اگر skill ی bundled را ویرایش کرده‌اید: `hermes skills list-modified` +
   `hermes skills diff`. وگرنه `hermes skills check` را اجرا و آپدیت‌های موجود را ثبت کنید.

## Verification checklist

- [ ] skill ی شما روی عبارت trigger در session ی تازه لود شد.
- [ ] description با الگوی «Use when X. Behavior.» در یک خط است.
- [ ] skill ی ثالث قبل از install بازرسی (خواندن بدنه) شد.
- [ ] مدل trust هر دو طرفه نمایش داده شد (مسدود، بعد مجاز).
