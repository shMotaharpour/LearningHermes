# تمرین ۱۵ — امنیت، هزینه و Governance

## Objective

چهار آرتیفکت governance ی که یک senior نگه می‌دارد تولید کنید — allowlist ی approval،
inventory ی secrets، ارزیابی egress، سیاست هزینه — و یک workflow ی واقعی را سخت کنید.

## Tasks

1. **audit ی approval.** approvalهای دستورات خطرناکتان را بازبینی کنید؛ `hermes approvals
   suggest` را اجرا کنید؛ allowlist را حداقلی نگه دارید با یک خط توجیه برای هر entry. یک
   approval ی بی‌نیاز را حذف کنید.
2. **inventory ی secrets.** هر credential ی setup ی agent تان را لیست کنید: فایلی که در
   آن است (`.env`/Bitwarden/1Password)، provider، تاریخ چرخش. اگر available است یک کلید
   را از `.env` به یک secret source ی خارجی منتقل کنید (`hermes secrets ...`).
3. **ارزیابی egress.** `hermes egress status` — اگر نصب نیست، سیاستی که deploy می‌کردید
   را بنویسید (مقصدهای مجاز برای agent ی data-دار) و فرمان enforce اش.
4. **اسکن امنیتی.** `hermes security` را اجرا کنید (اسکن OSV)؛ هرچه علام زد triage کنید.
5. **سیاست هزینه.** سیاست tier تان (default/strong/بدون‌نظارت) را در ۵ خط بنویسید؛
   تأیید کنید config بازتابش دارد (`hermes config get model`، `hermes fallback list`)؛
   یادآور review ی هفتگی `hermes insights` را cron کنید.
6. **سخت‌کردن یک workflow.** job ی cron ی فصل ۰۷ تان را بردارید: toolsetهایش را به حداقل
   scope کنید، تارگت تحویل را تأیید کنید و مسیر rollback اش را مستند کنید.

## Verification checklist

- [ ] allowlist حداقلی؛ هر entry توجیه دارد.
- [ ] inventory ی secrets کامل با محل‌ها؛ یک مهاجرت به source ی خارجی انجام شد یا
      توجیه شد.
- [ ] وضعیت egress ارزیابی شد (یا سیاست نوشته شد)؛ اسکن OSV اجرا و triage شد.
- [ ] سیاست هزینه نوشته و در config ی زنده دیده شد.
- [ ] workflow ی سخت‌شده با scope ی کاهش‌یافته و rollback ی مستند اجرا می‌شود.
