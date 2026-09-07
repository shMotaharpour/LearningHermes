# فصل ۱۵ — امنیت، هزینه و Governance

## Why this matters (job link)

امنیت و governance با ۲۱+ ارجاع، دروازهٔ همه‌چیز دیگر است: مهندس True Zero باید همهٔ
راه‌حل‌های AI/ML را با «الزامات امنیت، هندل داده، compliance و Zero Trust» هم‌راستا کند
(`docs/research/jobs/source-03.md`)؛ پارامونت «با تیم‌های DevOps، SRE و Infosec» شریک
می‌شود (`docs/research/jobs/source-01.md`). agentی با دسترسی shell یک workload ی ممتاز
است — اجرای یکی بدون مدل امنیتی بی‌احتیاطی است و مصاحبه‌های senior دقیقاً همین را
می‌سننجند. نیمهٔ دوم این فصل governance ی هزینه است: تصمیم‌های routing ی فصل ۰۲ اینجا
به سیاست بودجه تبدیل می‌شوند.

## Concepts

### مدل تهدید agent

agent شما می‌تواند: فرمان اجرا کند، فایل بخواند/بنویسد، به شبکه برسد، پول API خرج کند و
به آدم‌ها پیام بدهد. هر قابلیت یک سطح حمله است:

- **prompt injection** — محتوای مخرب در صفحات وب، ایمیل‌ها، فایل‌های repo، حتی پیام‌های
  Telegram که agent می‌خواند، آن را به ضرر شما می‌رانَد. AGENTS.md ی این دوره صراحتاً
  metadata را untrusted علام می‌زند؛ آن خودش governance است.
- **exfiltration** — agent یک secret می‌خواند، بعد tool ی web/search «کمکمندانه» آن را در
  یک درخواست می‌گنجاند. کنترل egress برای همین است.
- **اجرای مخرب** — `rm -rf`، force-push، deploy به هاست اشتباه.
- **زنجیرهٔ تأمین** — skill/plugin/MCP serverهای نصب‌شده کد و context ای هستند که شما
  ننوشته‌اید (قواعد vet ی فصل‌های ۱۰/۱۱/۱۲).

### لایه‌های دفاع، verified

1. **سیستم approval** — دستورات خطرناک approval ی صریح کاربر می‌خواهند؛ `hermes approvals
   suggest` (verified) تصمیم‌های گذشته را به allowlist مبدل می‌کند تا کارهای مورد اعتماد
   مزاحم نکنند و بقیه gate بمانند.
2. **دیسیپلین secrets** — کلیدها فقط در `.env`؛ secret managerهای خارجی
   (`hermes secrets bitwarden|onepassword` — verified) کلیدها را در startup می‌کشند به‌جای
   ذخیره روی دیسک؛ managed scope (مستندات) کانفیگ را برای ناوگان‌های operator-محور pin می‌کند.
3. **firewall ی egress** — `hermes egress` مدیریت iron-proxy است (verified: «the optional
   TLS-intercepting egress firewall... credential-injection») — callهای HTTP ی agent از
   proxyای می‌گذرند که credentialها را *بدون دیدن مدل* تزریق می‌کند و می‌تواند مقصدها را ببندد.
4. **ایزولگی** — backendهای Docker/SSH/cloud (فصل ۱۳) شعاع انفجار را می‌بندند؛
   checkpointها (فصل ۰۴) آسیب mutation را؛ `hermes security` (verified) venv و
   dependencyهای plugin را مقابل OSV.dev اسکن می‌کند.
5. **کمترین امتیاز** — scope ی toolset per-run (فصل ۰۵)، فیلتر tool ی MCP (فصل ۱۱)،
   MCPهای read-only کاتالوگ هرجا ممکن.

### governance ی هزینه

از routing ی فصل ۰۲ به یک سیاست واقعی:

- **tierها:** پیش‌فرض ارزان/سریع؛ مدل قوی فقط برای taskهای استدلال‌سنگین (لیست trigger ی
  صریح)؛ MoA فقط برای قضاوت‌ها.
- **بودجه per-surface:** jobهای بدون‌نظارت (cron، webhook) روی tier ارزان با خروجی محدود؛
  کار تعاملی tier قوی.
- **بهداشت aux:** مدل‌های کوچک برای compression/title (فصل ۰۲).
- **اندازه‌گیری:** review ی هفتگی `hermes insights`؛ هشدار روی پرش week-over-week (یک
  job ی script-only — فصل ۰۷).

### آرتیفکت‌های governance که یک senior نگه می‌دارد

allowlist ی approval با توجیه، inventory ی secrets (چه چیزی کجا، چرخش)، سیاست egress
(مقصدهای مجاز)، baseline ی eval (فصل ۱۴) به‌عنوان gate ی تغییر، و runbook ی incident
(لاگ‌های فصل ۰۴ + incidents ی فصل ۰۷).

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b6-security-observability.txt`
(درخت‌های فرمان security/approvals/secrets/egress)،
`docs/research/hermes/cli-evidence-2026-09-07.txt` (auth poolها)، به‌علاوهٔ لاگ‌های
429-retry ی gateway در evidence b4 به‌عنوان زمینهٔ هزینه/rate.

## Verified commands

approvalها:

```bash
hermes approvals suggest      # استخراج تصمیم‌های گذشته → allowlist پیشنهادی
hermes security               # اسکن OSV.dev: venv + dependencyهای plugin (verified)
```

secrets:

```bash
hermes secrets bitwarden      # کشیدن کلیدها از Bitwarden در startup
hermes secrets onepassword
hermes config env-path        # محل secrets ی محلی
```

egress:

```bash
hermes egress status          # وضعیت iron-proxy
hermes egress install / setup / start
hermes egress config          # سیاست مقصدها/credentialها
```

هزینه:

```bash
hermes insights --days 7      # review ی هفتگی
hermes fallback list          # تاب‌آوری سیاست tier
hermes auth list              # وضعیت credentialهای pooled
```

## Common pitfalls

- **approve ی ابدی برای رفع مزاحمت.** هر approval ی دائمی ریسک ایستاده است؛ فقط چیزهایی
  را allowlist کنید که واقعاً روتین‌اند و هر فصل بازبینی کنید.
- **secret در prompt.** اگر prompt حاوی کلید باشد، الان در transcriptها، لاگ‌ها و سرورهای
  provider است. credential از مسیر egress injection/secret source می‌رود، هرگز نثر.
- **بدون سیاست egress برای agentهای data-دار.** agentی که دادهٔ خصوصی می‌خواند و دسترسی
  بازِ شبکه دارد یک مسیر exfiltration است؛ iron-proxy یا سیاست شبکه ی scoped می‌بنددش.
- **tier ی ارزان-به-production.** ارزان‌کردن با اجرای اتوماسیون‌های بدون‌نظارت روی مدل ضعیف،
  خروجِ مطمئنِ غلط می‌سازد — سیاست tier را با gate ی eval ی فصل ۱۴ جفت کنید.
- **اعتماد به skill/plugin/MCP چون کار می‌کند.** قبل از نصب vet کنید (inspect،
  capabilities، review ی سورس)؛ بعدش audit کنید (`hermes skills audit`، `plugins doctor`،
  `security`).
- **سند governance که هیچ‌کس دوباره نمی‌خواند.** اسناد allowlist/egress/budget runbook های
  زنده‌اند — روی incidentها و هر فصل بازبینی شوند.

## Exercises

تمرین `exercises/ex15-security-cost-governance.md` را انجام دهید. راستی‌آزمایی:
allowlist ی approval با توجیه، ارزیابی egress، inventory ی secrets، سیاست هزینه ی
مستند و منعکس در config.
