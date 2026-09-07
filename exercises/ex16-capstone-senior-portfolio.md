# تمرین ۱۶ — Capstone: Portfolio ی سطح Senior

## Objective

تحویل یک اتوماسیون کاملِ مستند به شواهد از یک workflow ی واقعی — قطعهٔ portfolio ای که به
پروفایل Senior Applied AI Engineer نگاشت می‌شود.

## Objective scope

یک workflow ی واقعی بردارید که واقعاً ادامه‌اش می‌دهید (خط لولهٔ گزارش، نگهداری repo،
فرایند کسب‌وکار شخصی، digest پژوهشی). باید حداقل داشته باشد: یک سیستم خارجی، یک trigger
ی بدون‌نظارت، و یک deliverable به انسان‌ها.

## Tasks

### Milestone 1 — Spec و معماری (هفتهٔ ۱)
1. یادداشت معماری را بنویسید (یک صفحه): نمودار workflow، توپولوژی agent، حالت‌های شکست +
   نگهبان‌ها، مدل هزینه، gate ی eval. ذخیره در `docs/research/capstone/architecture.md`.

### Milestone 2 — هستهٔ اتوماسیون (هفته‌های ۲–۳)
2. اتوماسیون را بسازید: jobهای cron و/یا triggerهای webhook؛ agent و/یا script-only طبق
   صلاحدید (فصل‌های ۰۷–۰۸)؛ تارگت‌های تحویل با `hermes send` تأییدشده.
3. یک سیستم خارجی را با MCP/plugin/API integrate کنید (فصل‌های ۱۱–۱۲).

### Milestone 3 — کیفیت و امنیت (هفتهٔ ۴)
4. eval set + gate ی regression بسازید (فصل ۱۴)؛ به فرایند تغییرتان گره بزنید.
5. گذر امنیتی را کامل کنید: allowlist ی approval، inventory ی secrets، تصمیم egress،
   scope ی کمترین امتیاز (تمرین فصل ۱۵ اعمال‌شده روی همین workflow).

### Milestone 4 — بهره‌برداری و بسته‌بندی (هفته‌های ۵–۶)
6. ۱۴ روز بدون حضور اجرا کنید: incidents را acknowledge کنید، insights را هفتگی مرور
   کنید، چیزهایی که شکست را درست کنید (این تست واقعی است).
7. portfolio را بسته‌بندی کنید: README ی repo با یادداشت معماری، زنجیرهٔ شواهد
   (`docs/research/capstone/`)، جدول نگاشت شایستگی-به-شواهد (۱۰ ردیف از CURRICULUM.md)،
   و یک اسکریپت دمو ۵ دقیقه‌ای که در مصاحبه ارائه می‌کنید.

### checklist دفاع (حد قبولی)

- [ ] workflow دو هفتهٔ متوالی بدون حضور اجرا شد؛ لاگ incident با resolutionها وجود دارد.
- [ ] integration ی خارجی زنده است از طریق یک قرارداد مستند (کانفیگ MCP یا plugin).
- [ ] gate ی eval: taskهای فریز + baseline + یک regression ی گرفته‌شده (یا waive ی آگاهانه).
- [ ] آرتیفکت‌های امنیتی: allowlist با توجیه، inventory ی secrets، تصمیم egress.
- [ ] مدل هزینه: token/day با insights اندازه‌گیری شد، داخل tierهای سیاست تان.
- [ ] جدول نگاشت شایستگی-به-شواهد: هر ده شایستگی CURRICULUM.md لینک آرتیفکت دارند.
- [ ] یادداشت معماری در ۵ دقیقه توسط یک غریبه خوانده می‌شود.
