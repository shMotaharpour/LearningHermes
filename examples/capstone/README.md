# `examples/capstone/` — the interview-readiness kit

Chapter 16 turns competency into evidence. These are the templates and the one runnable
model that the defence actually needs.

| File | What it is |
|---|---|
| `cost_model.py` | Model what a workflow costs **before** the invoice. Sensitivity ranking and `--what-if`. |
| `workflow.json` | A worked spec. **Prices are placeholders — replace them.** |
| `postmortem-template.md` | Every section, including the three people skip. |
| `postmortem-example.md` | A worked 51-hour silent failure, written out in full. |
| `system-design-briefs.md` | Five under-specified briefs, one per Part, plus the rubric. |
| `competency-map.md` | The portfolio index: cluster → artifact → the question it answers. |

```bash
python3 cost_model.py                              # monthly cost by job
python3 cost_model.py --sensitivity                # which lever actually matters
python3 cost_model.py --what-if pr-triage:tier=strong
```

## Why a cost model rather than `hermes insights`

`insights` tells you what you already spent, on a system that already exists. A model tells
you what a design will cost before you build it and — the useful part — **which lever
moves it**. "How much will this cost to run?" is a senior interview question; "I'd check
insights" is a junior answer to it.

The output to read is the *ranking*, not the numbers. Two findings in the worked spec that
generalise: turning prompt caching off is the single largest mover in the whole table, which
is the size of a saving you already have and can lose by editing a prompt prefix with no
error attached; and a tier swap looks decisive whenever one expensive job dominates, which
is a fact about your workload rather than about model pricing.

## The three sections of a postmortem people skip

`postmortem-template.md` calls them out, and `postmortem-example.md` shows them filled in:

- **"How we knew"** as a column in the timeline. Rows where the answer is "a human noticed,
  later" are your detection gaps, and they are usually the most valuable output.
- **"What went right"** — you are looking for things to invest more in. A postmortem that
  only lists failures teaches a team that safeguards do not matter.
- **"What we are not doing"** — the rejected items, with reasons. It stops the same
  suggestion arriving in three months as if it were new.
