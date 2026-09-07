---
name: learninghermes-authoring
description: "Use when authoring or editing LearningHermes course content — chapter contract, evidence rules, parity checks."
---

# نگارش LearningHermes

داخل ریپوی دورهٔ LearningHermes هستی. AGENTS.md در ریشهٔ ریپو را رعایت کن.

مرجع سریع قرارداد:
1. فصل = chapters/NN-slug/README.md با دقیقاً پنج سکشن:
   Why this matters (job link) / Concepts / Verified commands / Common pitfalls / Exercises.
2. هر دستور Hermes اول به‌صورت زنده اجرا می‌شود؛ خروجی خام در docs/research/hermes/ ذخیره و
   در فصل به آن ارجاع داده می‌شود.
3. هر فصل یک فایل تمرین دارد: exercises/exNN-<slug>.md.
4. ایندکس مستندات برای ادعاهای feature: https://hermes-agent.nousresearch.com/docs/llms.txt
5. اعتبارسنجی: python3 scripts/validate_course.py --root .
6. برابری (farsi در برابر english): python3 scripts/validate_course.py --root . --other <other-checkout>
7. Commitها: 'chNN: <description>' (انگلیسی)؛ برنچ english فقط انگلیسی،
   برنچ farsi نثر فارسی + اصطلاحات فنی انگلیسی.
