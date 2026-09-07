# فصل ۰۹ — Orchestration ی چند Agent

## Why this matters (job link)

کار multi-agent مرز ۲۰۲۶ آگهی‌های applied AI است: 100ms «سیستم‌ها، metricها و حلقه‌های
feedback ای که agentها را در طول زمان بهتر می‌کنند» می‌سازد (`docs/research/jobs/source-05.md`)؛
Reflection «سیستم‌های agentic ... orchestration ی workflowهای LLM» را در مشتریان enterprise
شipping می‌کند (`docs/research/jobs/source-04.md`). orchestrate کردن چند agent ی تخصصی —
پژوهش موازی، لِین‌های code review، worker swarm — نسخهٔ senior ی loop ی فصل ۰۱ است.
هیرمس کل نردبان را دارد: subagentهای درون-session، task board ی ماندگار چند-profile،
rosterهای bot، peer gatewayها، و batch processing.

## Concepts

### نردبان orchestration (از ضعیف به قوی)

1. **subagentها (`delegate_task`)** — گفتگوهای فرزند ایزوله داخل session ی شما برای
   subtaskهای موازی/استدلال‌سنگین؛ فقط خلاصهٔ نهایی برمی‌گردد. مناسب کارهایی که context ی
   شما را سیل می‌زنند (خوانش‌های حجیم، جریان‌های پژوهشی مستقل).
2. **kanban چند-agent** — task board ی SQLite ی ماندگار مشترک بین profileها. taskها
   اتمیک claim می‌شوند، به هم وابسته‌اند و توسط profileهای نام‌دار در workspaceهای ایزوله
   اجرا می‌شوند (verified `hermes kanban --help`: «Durable SQLite-backed task board...
   claimed atomically»). سازندهٔ swarm هم دارد: `hermes kanban swarm` — گرافِ workerهای
   موازی → verifier → synthesizer.
3. **bot mode** — profileها به‌عنوان botهای نام‌دار با chat/role/model/memory/skills ی
   خودش؛ روتین اجرا می‌کنند، چت گروهی را share می‌کنند، به هم پیام می‌دهند.
4. **peerها (A2A)** — gatewayهای هیرمس دیگر روی ماشین‌های دیگر: `hermes peer add spark
   --url http://spark.lan:8377 --key <KEY>`، بعد `hermes peer dm spark "disk status?"`
   (help کامل با کدهای خروج 0/1/2 verified). پیام agent-به-agent بین‌ماشینی.
5. **batch processing** — تولید trajectory ی agent در مقیاس: پردازش موازی با checkpoint.
   روی‌گرد تولید دادهٔ orchestration.

### کِی multi-agent نکنیم

subagent هزینهٔ هماهنگی دارد. برای کارهای کوچک، session ی تک با scope ی خوب toolها
(فصل ۰۵) از swarm می‌برد. زمان بالا بروید که: کار واقعاً موازی است، subtaskها ایزولگی از
context شما لازم دارند، یا ماندگاری در طول ساعت‌ها/روزها لازم است (kanban، نه subagent).

### مکانیک ایزولگی

- **worktreeها:** `hermes -w` agentها را در git worktree اجرا می‌کند — چند agent روی یک
  repo بدون لگد زدن به هم؛ `hermes worktree audit|prune` انباشت را پس می‌گیرد
  (subcommandهای verified).
- **profileها:** `hermes profile create/use/list` (verified) — config+session+skill مستقل
  برای هر profile؛ workerهای kanban profileهای نام‌دارند.
- **projectها:** `hermes project create|bind-board` دایرکتوری‌ها را به boardها گره می‌زند (verified).

### kanban به‌عنوان صف production

لیست subcommandهای verified مثل spec ی یک task-queue می‌ماند: `create, assign, claim,
block, schedule, link (parent→child), request-review, promote, archive, reclaim, reassign,
dispatch, daemon, watch, stats, gc, repair`. ستون آخر مهم است: reclaim (worker مُرد)،
block/unblock (وابستگی‌ها)، diagnostics — این orchestration ی ماندگار است، نه تختهٔ چسب‌نوشت.

**شواهد:** `docs/research/hermes/cli-evidence-2026-09-07-b7-multiagent-shipping.txt`
(help ی کامل peer با مثال‌ها، مجموعهٔ کامل kanban شامل swarm)، به‌علاوهٔ `hermes profile
--help` و فرمان‌های worktree در evidence batches ی 1/b7.

## Verified commands

subagentها (درون-session، با ابزارهای خود agent):

```
"Research X, Y, and Z in parallel and give me one combined brief."
# agent سه subagent ی ایزوله می‌سازد؛ شما یک نتیجهٔ merge‌شده می‌بینید
```

kanban:

```bash
hermes kanban init && hermes kanban boards
hermes kanban create --title "Port CLI tests" --board main
hermes kanban link <parent> <child>          # وابستگی
hermes kanban swarm --spec swarm.md          # workerها → verifier → synthesizer
hermes kanban claim                          # claim ی اتمیک (مسیر workspace را چاپ می‌کند)
hermes kanban stats / diagnostics            # سلامت صف
hermes kanban daemon / watch / dispatch      # مدهای اجرا
```

peerها:

```bash
hermes peer add spark --url http://spark.lan:8377 --key <API_SERVER_KEY>
hermes peer list
hermes peer dm spark/researcher "summarize today's CI failures"
```

profileها و worktreeها:

```bash
hermes profile create researcher && hermes profile list
hermes -w                  # حالت worktree برای agentهای repo-ویرایشگر
hermes worktree audit      # یافتن worktreeهای کهنه
hermes worktree prune      # بازپس‌گیری (هرگز کارِ commit‌نشده/unpushed را پاک نمی‌کند — verified)
```

## Common pitfalls

- **subagent برای یک‌خطی.** یک tool call ی تنها delegation نمی‌خواهد؛ هزینهٔ spawn از کار
  بیشتر می‌شود. فقط برای کارِ استدلال‌سنگین یا context-سیل‌کن delegate کنید.
- **گزارش خودِ subagent به‌جای fact.** فرزندی که می‌گوید «با موفقیت upload شد» ممکن است
  اشتباه باشد — اثر بیرونی را خودتان verify کنید قبل از اعتماد به خلاصه.
- **kanban بدون وابستگی.** workerهای موازی که در taskهای وابستهٔ link‌نشده می‌دوند، merge
  آشوب می‌سازند. اول یال‌های `link` را مدل کنید.
- **گورستان worktreeها.** هر اجرای `-w` انباشته می‌کند؛ audit+prune طبق زمان‌بندی.
- **کلید peer در فایل اشتباه.** credentialهای peer مال `.env` اند (verified: «stored
  locally as a credential in ~/.hermes/.env»)؛ نه config.yaml، نه shell history.
- **فرض memory ی مشترک.** subagentها، profileها و peerها به‌طور پیش‌فرض هیچ‌چیز share
  نمی‌کنند — همهٔ context لازم را صریح در task/prompt بدهید.

## Exercises

تمرین `exercises/ex09-multi-agent-orchestration.md` را انجام دهید. راستی‌آزمایی: یک
delegation ی موازی ۳تایی مشاهده‌شده، یک task ی kanban از claim تا complete، یک رفت‌وبرگشت
peer (یا طرح مستند)، بهداشت worktree.
