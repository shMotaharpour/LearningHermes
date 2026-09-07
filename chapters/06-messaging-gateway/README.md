# فصل ۰۶ — پیام‌رسان‌ها و Gateway

## Why this matters (job link)

یکپارچه‌سازی با سیستم‌هایی که آدم‌ها واقعاً استفاده می‌کنند، نان‌وشام مهندس applied است:
Adventus برای «یکپارچه‌سازی قابلیت‌های AI با پلتفرم‌هایی مثل Dynamics 365، SAP،
ServiceNow، Azure» استخدام می‌کند (`docs/research/jobs/extract-round2.json`)؛ Minted
«دستیارهای هوشمندی برای HR، Finance، Operations... یکپارچه‌سازی راه‌حل‌های LLM با ابزارهای
سازمانی» می‌خواهد (`docs/research/jobs/extract-round2.json`). gateway کلاسِ درسِ
یکپارچه‌سازیِ هیرمس است: یک هستهٔ agent، ۲۱+ آداپتور پلتفرم، routing ی session، تضمین
تحویل. یادگیری طرز فکر gateway به شما یاد می‌دهد *هر* سیستم AI را به *هر* سطح ارتباطی
وصل کنید — دقیقاً همان شایستگی‌ای که آگهی‌های automation-engineer توصیف می‌کنند.

## Concepts

### معماری gateway

gateway یک سرویس دائمی است (`hermes-gateway.service`، سرویس systemd کاربر — وضعیت زنده
در evidence b4 verified) که:

1. به آداپتورهای پلتفرم وصل می‌شود (Telegram، Discord، Slack، WhatsApp، Signal، Matrix،
   Email، Teams، ...) و credential هر پلتفرم را از `.env` می‌گیرد.
2. هر پیام ورودی را با هویت platform+chat+thread به یک **session** route می‌کند.
3. همان agent loop ی CLI — با ابزار کامل — را روی آن session اجرا می‌کند.
4. پاسخ‌ها (و deliverableها: فایل، تصویر، صوت) را به پلتفرم برمی‌گرداند.

ضروریات ops از سرویس زنده verified: با logout زنده می‌ماند (systemd linger)، زیرِ کاپوت
`hermes gateway run` اجرا می‌کند و مشکلات runtime (retryهای 429، خطای tool، هشدار تحویل)
در `hermes logs` دیده می‌شوند — transcript گفتگو را نشان می‌دهد، لاگ‌ها سرویس را.

### routing ی session

هر گفتگوی پلتفرم یک هویت session ی قطعی (`platform:chat:thread`) می‌گیرد، پس
topic/threadها به sessionهای جدا هیرمس map می‌شوند. به همین دلیل memory و تعویض مدل
per-topic کار می‌کند. index ی routing قابل ترمیم است (`hermes sessions repair-routing`).

### پلتفرم‌های قابل اتصال

جریان setup هر پلتفرم (با `hermes gateway setup` یا مستندات مخصوص): Telegram (bot token)،
Discord (bot)، Slack (Socket Mode)، WhatsApp (bridge یا Business Cloud API)، Signal
(signal-cli daemon)، Email (IMAP/SMTP)، SMS (Twilio)، Matrix، Mattermost، Teams، Google
Chat، LINE، IRC و بیشتر. دو الگو همه‌جا هست: **پلتفرم‌های bot-token** (credential ساده +
polling/webhook) و **پلتفرم‌های daemon-bridge** (یک daemon محلی که پروتکل پلتفرم را حرف می‌زند).

### deliverable mode

agent آرتیفکت را به‌صورت attachment نیتیو تحویل می‌دهد: نمودار به‌صورت عکس، گزارش به‌صورت
سند، صوت به‌صورت voice bubble (سینتکس `MEDIA:`). این همان چیزی است که agent را از
متن‌گوی به endpoint ی تحویل تبدیل می‌کند — jobهای cron در فصل ۰۷ به آن وابسته‌اند.

### profileها و multi-gateway

هر profile (`~/.hermes/profiles/<name>/`) می‌تواند gateway خودش را داشته باشد — اجرای
هم‌زمان چند gateway توپولوژی پشتیبانی‌شده است (botهای متفاوت، پلتفرم‌های متفاوت،
شخصیت‌های متفاوت). `hermes gateway list` وضعیت هر profile را نشان می‌دهد.

### hermes send — سمت خروج

`hermes send` (help کامل verified در evidence batch 1) پیام را از هر اسکریپت یا CI به
پلتفرم‌ها می‌رساند: `hermes send --to telegram "deploy finished"`،
`hermes send --to telegram:chat:thread "MEDIA:/tmp/chart.png"`. بدون LLM و بدون نیاز به
gateway برای پلتفرم‌های bot-token — از credentialهای کانفیگ‌شده استفاده می‌کند. فصل ۰۸
آن را primitive ی جهانی اعلان می‌کند.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b4-gateway-cron-events.txt`
(خروجی systemd ی `gateway status` زنده با لاگ‌های واقعی retry ی 429، تارگت‌های
`send --list`)، `docs/research/hermes/cli-evidence-2026-09-07.txt` (help کامل `send`).

## Verified commands

چرخهٔ حیات gateway:

```bash
hermes gateway status      # state ی systemd، PID، memory، لاگ‌های اخیر (verified زنده)
hermes gateway start|stop|restart
hermes gateway install     # نصب به‌عنوان سرویس systemd/launchd
hermes gateway list        # وضعیت gateway ی هر profile
hermes gateway setup       # کانفیگ تعاملی پلتفرم‌ها
```

تارگت‌های تحویل:

```
$ hermes send --list
Available messaging targets:
Telegram:
  telegram:Hermes / topic 1178 (group)
  telegram:Hermes / topic 1 (group)
  ...
```

```bash
hermes send --to telegram "build finished"              # کانال خانگی
hermes send --to telegram:-100123:17585 "hi"            # chat:thread ی صریح
hermes send --to discord:#ops --file /tmp/report.md     # پیوست
hermes send --to telegram "MEDIA:/tmp/chart.png"        # تحویل رسانه
echo "RAM 92%" | hermes send --to telegram               # پایپ از stdin
```

دیباگ:

```bash
hermes logs --component gateway -n 100    # نمای runtime از سمت gateway
hermes sessions list                      # تأیید رسیدن sessionهای پلتفرم
hermes sessions repair-routing            # ترمیم هویت گم‌شدهٔ routing
```

## Common pitfalls

- **اجرای lifecycle از درون gateway.** روی نصب‌های systemd، فرمانِ lifecycle ی اجراشده از
  داخل خود پروسهٔ gateway، فرمان را پیش از اتمام می‌کُشد (SIGTERM به فرزندان هم می‌رسد).
  همیشه از shell ی جدا بیرون gateway اجرا کنید.
- **credential در فایل اشتباه.** tokenهای پلتفرم در `~/.hermes/.env` می‌روند؛ gateway در
  boot می‌خواندشان. چرخش token یعنی یک بار راه‌اندازی دوبارهٔ سرویس.
- **اشتباه thread با session.** یک *topic* ی Telegram session ی خودش با context و مدل
  خودش است. پست در topic ی اشتباه = صحبت با state ی اشتباه agent.
- **تحویل یعنی دیده‌نشده.** کد خروج 0 در `hermes send` یعنی پلتفرم پذیرفت. تحویل مجدد،
  mute و تنظیمات اعلان سمت پلتفرم است.
- **فراموش‌کردن linger.** بدون systemd linger، gateway با logout می‌میرد.
  `hermes gateway status` تأییدش می‌کند (verified: «Systemd linger is enabled»).
- **429 در ساعات پیک.** gateway خودش retry می‌کند (verified در لاگ‌های زنده: «Retrying
  API call in 2.4s (attempt 1/3)») — ولی 429 پایدار با زنجیرهٔ fallback ی فصل ۰۲ حل
  می‌شود نه با امید.

## Exercises

تمرین `exercises/ex06-messaging-gateway.md` را انجام دهید. راستی‌آزمایی: یک پلتفرم متصل،
نمایش map شدن thread↔session، تحویل `hermes send` از یک اسکریپت، خواندن لاگ‌های gateway
بعد از یک پیام زنده.
