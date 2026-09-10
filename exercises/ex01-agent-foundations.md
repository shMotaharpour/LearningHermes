# تمرین ۰۱ — پایه‌های Agent

## Objective

به خودتان ثابت کنید هیرمس یک سیستمِ اجرایی است نه یک chatbot: نصب/راستی‌آزمایی، اجرای
agent loop با و بدون tool، و پیدا کردن هر سه سطح کانفیگ.

## Tasks

1. **راستی‌آزمایی نصب.** `hermes --version` و `hermes doctor` را اجرا کنید. هر چیزی که
   doctor علام می‌زند را قبل از ادامه درست کنید.
2. **نقشهٔ CLI.** `hermes --help` را اجرا کنید. سه subcommand ناآشنا بردارید و `--help`
   آن‌ها را ببینید (پیشنهاد: `moa`، `egress`، `checkpoints`).
3. **agent loop بدون tool.** `hermes chat -q "Explain what a tool call is in one sentence."`
4. **agent loop با tool.** در یک دایرکتوری پر از فایل:
   `hermes chat -q "Count the files in the current directory and report the largest one."`
   در transcript دنبال کنید: مدل باید terminal را صدا بزند، خروجی را بخواند، بعد جواب دهد.
5. **یافتن سه سطح.** `hermes config path` و `hermes config env-path`. روی دیسک تأیید
   کنید: `config.yaml` (تنظیمات)، `.env` (secretها)، `hermes-agent/` (کد).
6. **مدل فعلی.** `hermes config get model` — provider و نام مدل را یادداشت کنید.
7. **جای‌گذاری هیرمس در landscape ابزارها.** از جدول مقایسه در فصل ۰۱ (Concepts ←
   «Hermes در برابر ابزارهای هم‌خانواده») یک coding-agent CLI و یک gateway agent انتخاب
   کنید. برای هرکدام در یک جمله بگویید به کدام خانواده تعلق دارد و مستنداتش چه surface
   اصلی‌ای فهرست کرده. جمله‌تان را با
   `docs/research/hermes/tool-landscape-evidence-2026-09-10.txt` چک صحرایی کنید.

## Verification checklist

- [ ] `hermes doctor` بدون خطای بازدارنده.
- [ ] می‌توانید اتفاق task 4 را به زبان loop توضیح دهید: model → tool call → result → answer.
- [ ] خروجی `hermes config get model` با مدلی که انتظار هزینه‌اش را دارید یکی است.
- [ ] می‌دانید برای تغییر یک تنظیم کدام فایل را ویرایش می‌کنید (و کلید API هرگز در کدام
      نمی‌رود).
- [ ] می‌توانید دو خانوادهٔ agent (coding-agent CLI و gateway agent) را نام ببرید و از هر
      کدام یک مثال بزنید، همراه با فایل شواهدی که این ادعا را مستند می‌کند.
