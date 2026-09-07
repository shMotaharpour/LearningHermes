# فصل ۱۳ — Shipping ی محصولات Agent

## Why this matters (job link)

Deployment پرتقاضاترین مهارت در پیکرهٔ تحقیق است — ۹۳ ارجاع: دیتابریکس: «معماری و
پیاده‌سازی زیرساخت ML ی مقیاس‌پذیر و مقاوم ... برای یکپارچه‌سازی بی‌درز مدل‌های AI/ML در
production» (`docs/research/jobs/source-02.md`)؛ Reflection: «deploy ی سیستم‌های
production ی قابل‌اتکا ... شیوه‌های مدرن DevOps (Docker، Kubernetes و CI/CD)»
(`docs/research/jobs/source-04.md`). agentها نرم‌افزارند: backend، بسته‌بندی، CI و
checklist ی deployment می‌خواهند. این فصل اجرای workloadهای هیرمس روی backend درست،
شipping ی محصولات agent-ساخته از طریق GitHub و توزیعِ setupهای کامل agent را پوشش می‌دهد.

## Concepts

### backendهای terminal: agent کجا اجرا شود

verified از `hermes --help`/مستندات: اجرای toolها روی backendهای قابل‌تعویض است —
**local** (ماشین شما)، **Docker** (کانتینر ایزوله)، **SSH** (هاست‌های remote)،
**Daytona/Modal/Singularity** (sandboxهای cloud). قواعد انتخاب:

- local: تمام قدرت، تمام ریسک — filesystem و credentialهای واقعی شما.
- Docker: کد غیرقابل‌اعتماد، آزمایش‌ها، CI — ایزولگی به‌عنوان پیش‌فرض.
- SSH: agent روی *سرورهای شما* کار می‌کند (runbookها، اتوماسیون ops).
- sandboxهای cloud: کارهای batch ی مقیاس‌پذیرِ گذرا (جفتِ batch processing ی فصل ۰۹).

### شipping ی محصولِ agent-ساخته

حلقهٔ محصولی که خود این دوره دنبال می‌کند:

1. **repo با AGENTS.md** — agentها قرارداد را به ارث می‌برند (فصل ۰۳).
2. **skillها برای رویه‌ها** — runbookها در `.hermes/skills/` نه تاریخچهٔ چت (فصل ۱۰).
3. **شواهد راستی‌آزمایی** — دستورات اثبات‌شده، خروجی‌های ذخیره‌شده (`docs/research/` همین repo).
4. **integration با CI** — `hermes send` برای اعلان‌ها (فصل ۰۸)؛ agent در CI با one-shot
   ی `hermes chat -q` با toolsetهای scoped.
5. **workflow ی PR توسط agent** — branch، commit، PR، review؛ کاتالوگ skillهای GitHub
   (code review، issue-to-PR) کارهای کسل‌کننده را اتومات می‌کند.

### profile distribution: ship کردن کل agent

`hermes profile export|import|install` (verified) یک profile را بسته‌بندی می‌کند — config،
skillها، AGENTS.md، سیاست memory — برای هم‌تیمی‌ها یا سرورها. `hermes profile update`
آپدیت را دوباره می‌کشد و دادهٔ کاربر را حفظ می‌کند؛ `hermes backup` (verified) همه‌چیز را
برای بازیابی از فاجعه آرشیو می‌کند. مهندس senior فقط خروجی agent را نمی‌فرستد؛ *setup ی
agent* را می‌فرستد.

### import و مهاجرت

`hermes import-agent claude-code|codex` (verified: «One-command import of a Claude Code or
OpenAI Codex CLI setup into Hermes — instructions, allowlists, MCP servers, skills, and
memories») — رمپ ورود کاربران فعلی agent و ابزار مهاجرت شما هنگام استانداردسازی تیم روی
یک runtime.

### checklist ی deployment (عادت senior)

قبل از زنده شدن هر اتوماسیون agent: scope ی toolset حداقلی (فصل ۰۵)، زنجیرهٔ fallback
(فصل ۰۲)، تارگت تحویل تأییدشده (فصل ۰۷)، بازبینی approval/egress (فصل ۱۵)، قابل‌مشاهده
بودن logs/incidents (فصل ۰۴/۱۴)، مسیر rollback ی شناخته‌شده (فصل ۰۴).

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b7-multiagent-shipping.txt`
(help ی backup/profile/portal/project)، `docs/research/hermes/cli-evidence-2026-09-07.txt`
(gateway/run/send برای مسیرهای CI)، `docs/research/hermes/cli-evidence-2026-09-07-b1-foundations-core.txt`
(import-agent).

## Verified commands

backendها و ایزولگی:

```bash
hermes --worktree                  # -w: ایزولگی git-worktree برای کار ی repo
hermes chat -q "run tests" -t terminal   # one-shot ی scoped در CI
```

حلقهٔ محصول:

```bash
git checkout -b feature/x
hermes chat -q "Implement feature X per AGENTS.md, commit as chNN" -t terminal,memory
gh pr create --fill                # یا بگذارید agent با skillهای GitHub انجام دهد
```

توزیع:

```bash
hermes profile export my-setup -o my-setup.tar
hermes profile install https://github.com/org/team-agent-setup
hermes profile update
hermes backup -o ~/hermes-$(date +%F).zip
```

مهاجرت:

```bash
hermes import-agent claude-code --dry-run   # پیش‌نمایش اینکه چه چیزی منتقل می‌شود
hermes import-agent claude-code
```

## Common pitfalls

- **backend ی local برای کد غیرقابل‌اعتماد.** agentی که ریپوی غریبه را روی backend ی local
  اجرا کند credentialهای واقعی شما در دسترسش است. Docker backend پیش‌فرضِ آن کار است.
- **agent ی CI با toolهای unscoped.** `hermes chat -q` در CI بدون `-t` همه‌چیز را لود
  می‌کند؛ به CI فقط دو toolset ی مورد نیازش را بدهید.
- **backup های حاوی secret.** `hermes backup` آرشیو `.env` هم هست — آرشیو را رمزنگاری و
  هرگز share نکنید.
- **profile distribution به‌عنوان dump ی کانفیگ.** قبل از `export` حافظه/sessionها را
  پاکسازی کنید؛ توزیع، skill+قواعد می‌فرستد نه تاریخچهٔ گفتگوهای شما.
- **رد کردن dry-run در import.** `--dry-run` وجود دارد (verified) — قبل از overwrite ی
  setup ی موجود استفاده کنید.

## Exercises

تمرین `exercises/ex13-shipping-agent-products.md` را انجام دهید. راستی‌آزمایی: یک feature
از repo تا PR توسط agent، یک profile distribution نصب‌شده در جای دیگر (یا export شده +
manifest بازرسی‌شده)، اعلان CI سیم‌کشی‌شده، checklist ی deployment نوشته‌شده برای یک کار واقعی.
