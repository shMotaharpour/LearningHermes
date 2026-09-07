# فصل ۰۲ — کانفیگ و Modelها

## Why this matters (job link)

بهینه‌سازی هزینه و کارایی در بیشتر آگهی‌های senior دیده می‌شود — پارامونت مهندسانی
می‌خواهد که راه‌حل‌های «مقیاس‌پذیر، تاب‌آور و اثرگذار» بسازند
(`docs/research/jobs/source-01.md`)؛ 100ms کار روی «correctness، latency، کنترل
hallucination» با رویکرد metric-محور می‌خواهد (`docs/research/jobs/source-05.md`). ارزان‌ترین
اهرم یک مهندس applied **model routing** است: مدلِ درست، کارِ درست، قیمتِ درست، با مسیر
failover. هیرمس routing را یک دغدغهٔ کانفیگِ درجه‌اول کرده — providerها، aliasها، Mixture
of Agents، زنجیرهٔ fallback، credential pool، مدل‌های کمکی — و این فصل شما را در هر شش مورد روان می‌کند.

## Concepts

### Provider در برابر model

**Provider** یک سطح API است: OpenRouter، Anthropic، OpenAI، Google، Nous Portal، سرور
Ollama روی localhost، هر endpoint سازگار با OpenAI. **Model** یک شناسه است که provider
سرو می‌کند (`gemini/gemini-2.5-pro` = مدل گوگل از طریق OpenRouter؛ `vertex/gemini-2.5-pro`
= همان وزن‌ها از طریق Vertex AI — صورتحساب و محدودیت و latency متفاوت). هیرمس جفت‌های
`provider/model` را در runtime resolve می‌کند و سه الگوی احراز دارد: API key (در `.env`)،
login ی OAuth مرورگری، credentialهای pooled.

### resolve سه‌لایهٔ مدل

`hermes config get model` (verified در evidence b2) نشان می‌دهد یک درخواست چطور resolve می‌شود:

```
default: minimax/minimax-m3:free      <- لایهٔ 1: چیزی که الان اجرا می‌شود
provider: openrouter                  <- لایهٔ 2: کدام سطح API
aliases:
  gemini-pro: gemini/gemini-2.5-pro   <- لایهٔ 3: واژگان routing ی شما
  gemini-flash: gemini/gemini-2.5-flash
  vertex-pro: vertex/gemini-2.5-pro
  vertex-flash: vertex/gemini-2.5-flash
```

Alias ها واژگان routing ی شماست: یک‌بار `cheap`، `smart`، `fast` را تعریف کنید و در slash
command ها، prompt های cron و اسکریپت‌ها استفاده کنید. بعداً تعویض provider یک‌خطی می‌شود.

### Scope: session یا global

`/model X` فقط همان session را عوض می‌کند؛ `--global` در config.yaml ماندگار می‌شود.
اسکریپت و cron همیشه از default استفاده مگر prompt خودش override کند. قاعده: آزمایش در
session scope، تثبیت انتخاب در global scope.

### Mixture of Agents (MoA)

`hermes moa list|configure|delete` (verified). `/moa <prompt>` یک prompt را به چند مدلِ
تنظیم‌شده هم‌زمان می‌فرستد و پاسخ‌ها را ترکیب می‌کند. *اختلاف نظر* مدل‌ها سیگنالی است که
می‌خرید — برای قضاوت‌های پرمخاطره (طراحی eval، review ی معماری) استفاده کنید، نه کار روتین
(هزینه ضربدر تعداد slot می‌شود).

### زنجیرهٔ fallback

`hermes fallback list|add|remove|clear` (verified): providerها به‌ترتیب امتحان می‌شوند وقتی
مدل اصلی با rate-limit، overload یا خطای اتصال شکست بخورد. قاعدهٔ production: **هر job
زمان‌بندی‌شده/بدون‌نظارت یک fallback فرض می‌کند.** بriefing ی cron ساعت ۶ صبح روی یک provider
تک، یعنی تحویل ازدست‌رفتهٔ بی‌صدا.

### Credential pool

`hermes auth add|list|remove|reset|status` (verified): چند API key یا OAuth token برای هر
provider، با چرخش خودکار برای رد شدن از محدودیت per-key. وقتی گلوگاه RPM/TPM است نه کیفیت
مدل، این راه‌حل است.

### مدل‌های کمکی (Aux)

کارهای جانبی (compression ی context، پیش‌پردازش vision، عنوان session) با مدل‌های کوچکِ
تنظیم‌شده اجرا می‌شوند نه مدل اصلی. کانفیگ اشتباه aux یک نشتی هزینهٔ بی‌صدا است: مدل
300B که عنوان session می‌سازد پول می‌سوزاند. در `hermes config show` چک کنید.

### دید هزینه

`hermes insights --days 7` (verified) مصرف token، هزینه و الگوی toolها را از تاریخچهٔ
session جمع می‌کند. تصمیم‌های routing باید به این داده تکیه کنند نه حس‌وحال.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b2-config-models.txt` (درخت
subcommand ها برای config/model/moa/fallback/auth + خروجی زندهٔ `config get model`)،
`docs/research/hermes/cli-evidence-2026-09-07-b6-security-observability.txt` (insights).

## Verified commands

بازرسی کانفیگ — به‌جای ویرایش دستی، از command استفاده کنید:

```bash
hermes config show          # کانفیگ کامل resolve شده
hermes config get model     # default + provider + aliases
hermes config path          # محل فایل تنظیمات
hermes config env-path      # محل فایل secrets
hermes config check         # گزینه‌های گم‌شده/قدیمی
hermes config set model gemini/gemini-2.5-flash    # set مستقیم
hermes config unset display.skin                   # حذف یک کلید
```

زیرساخت routing:

```bash
hermes moa list                          # بررسی slotهای MoA
hermes moa configure                     # ویرایشگر تعاملی slotها
hermes fallback list                     # زنجیرهٔ فعلی
hermes fallback add openrouter/meta-llama/llama-3.3-70b-instruct
hermes auth list                         # credentialهای pooled هر provider
hermes auth status                       # سلامت pool
```

آگاهی هزینه:

```bash
hermes insights --days 7     # token، روند هزینه، الگوی استفادهٔ tool
```

## Common pitfalls

- **scope ی اشتباه.** `/model X` بدون `--global` در session بعدی برمی‌گردد — تیکت کلاسیک
  «چرا برگشت؟»
- **بدون fallback در jobهای زمان‌بندی‌شده.** فصل ۰۷ به این فصل وابسته است: cron با provider
  تک ساعت ۶ صبح بی‌صدا شکست می‌خورد.
- **MoA به‌عنوان پیش‌فرض.** MoA هزینه را در تعداد slot ضرب می‌کند. فقط ابزار قضاوت.
- **ویرایش دستی config.yaml با gateway ی روشن.** ترجیحاً `hermes config set`؛ اگر مجبورید،
  بلافاصله `hermes config check`.
- **جابه‌جایی secrets.** `hermes config env-path` می‌گوید کلیدها کجا می‌روند — هرگز
  config.yaml، هرگز git، هرگز اسکرین‌شات.
- **رهاکردن مدل‌های aux.** مدل‌های بازبینی‌نشده روی هر compression و title آرام token
  می‌سوزانند.

## Exercises

تمرین `exercises/ex02-configuration-models.md` را انجام دهید. راستی‌آزمایی: زنجیرهٔ
fallback یک backup دارد، slotهای MoA بازرسی شده، insights مرور شده، چک‌های بهداشت کانفیگ پاس.
