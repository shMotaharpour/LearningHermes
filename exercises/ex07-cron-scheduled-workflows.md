# تمرین ۰۷ — Cron و Workflowهای زمان‌بندی‌شده

## Objective

دو job ی scheduled ی production-grade بسازید — یک watchdog ی script-only و یک job ی agent —
و آن‌ها را عملیاتی کنید: تست، ویرایش، بررسی incident.

## Tasks

1. **وضعیت scheduler.** `hermes cron status` و `hermes cron list` — jobهای فعال،
   scheduleها و تارگت‌های تحویل را ثبت کنید.
2. **watchdog ی script-only.** بنویسید `disk_check.sh`: خلاصهٔ مصرف دیسک چاپ کند؛
   سکوت-در-حالت-سالم ممنوع — در مسیر خوب هم «all clear» چاپ کند. job را بسازید
   (`--schedule "every 1h" --script ... --deliver <target>`)، بعد با `hermes cron tick`
   همین حالا آتشش بزنید. تحویل را تأیید کنید.
3. **job ی agent.** یک job ی روزانهٔ پژوهش/briefing بسازید: prompt ی خودکفا، فرمت خروجی
   صریح (حداکثر ۵ bullet + لینک)، تحویل به پلتفرم تان. با `hermes cron run <id>` تست کنید.
4. **ویرایش درجا.** schedule ی job ی agent را با `hermes cron edit` عوض کنید (نه
   delete/recreate). با `hermes cron list` تأیید کنید.
5. **رزمایش شکست.** موقتاً یک job ی اسکریپت را به اسکریپتی خطاخیز pointing کنید؛ اجرا
   کنید؛ شکست را در `hermes cron runs` و `hermes cron incidents` پیدا کنید؛ acknowledge
   کنید؛ اسکریپت را درست کنید؛ دوباره اجرا کنید.
6. **Notepad.** یک مقدار در notepad ی job بنویسید (`hermes cron notepad <id> write ...`)،
   برگردانید بخوانید — این‌طور jobها بین اجراها state به یاد می‌آورند.

## Verification checklist

- [ ] job ی اسکریپت خروجی داد، شامل مسیر «all clear».
- [ ] job ی agent نتیجهٔ فرمت‌شده به تارگت درست داد.
- [ ] schedule درجا ویرایش شد؛ list بازتابش دارد.
- [ ] یک شکست واقعی در runs/incidents پیدا و acknowledge شد.
- [ ] رفت‌وبرگشت notepad کار می‌کند.
