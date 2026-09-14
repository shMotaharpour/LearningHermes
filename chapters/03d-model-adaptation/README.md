# Chapter 03d — Model Adaptation: fine-tuning, LoRA, and serving your own weights

> **Verified:** 2026-09-14 · Hermes Agent v0.21.3 (2026.9.14) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

"Model adaptation & local serving" language appears in 3 of 18 postings with extracted body
text (10 mentions; `docs/research/jobs/stats-2026-09-14.txt`) — and all three are the
postings this course weighs most: Paramount lists "LLM fine-tuning (full-model, LoRA/QLoRA,
instruction tuning) and determine when fine-tuning is appropriate vs. RAG-only or hybrid
approaches" as a core responsibility (`docs/research/jobs/source-01.md`); Reflection wants a
Forward Deployed Engineer who will "adapt and fine-tune models for customer-specific needs"
with "hands-on experience with... vector databases, RAG pipelines, agent orchestration,
evaluations, and fine-tuning" (`docs/research/jobs/source-04.md`); 100ms asks for people who
"experiment with prompting techniques, fine-tuning datasets, retrieval strategies, and model
configurations" (`docs/research/jobs/source-05.md`). Note what is *not* asked: "knows the
PyTorch training API". What is asked is judgment — when to adapt weights at all, what rank
and precision mean, how an adapted model reaches production. That judgment is what this
chapter builds, on a model small enough to see all of.

## Concepts

### The three-way decision: prompt, retrieve, adapt

Every behaviour change to a model is one of three escalating moves:

| Move | Changes | Costs | Fails when |
|---|---|---|---|
| **Prompt / context** (Ch 03) | what the model reads this turn | nothing but tokens | the knowledge or style must be *default* |
| **Retrieve** (Ch 03b/03c) | what the model can look up | index + re-embed economics | the behaviour is a *skill*, not *knowledge* |
| **Adapt weights** (this chapter) | the model itself | training run + serving + eval | — |

Adapt when the behaviour must be default and format-like (a dialect, a JSON schema, a
classifier head over latent features), not when facts change — facts belong to retrieval
because they keep changing. The full-frame section at the end makes this decision explicit.

### Freezing is a by-construction guarantee, and that is the point

Full fine-tuning moves **every** entry of the base weight matrix `W0`. After it, the base
model no longer exists — nothing to compose, nothing to roll back, nothing to un-learn.

LoRA freezes `W0` and learns the edit as a low-rank product `delta_W = B @ A`, where
`A` is `r × in` and `B` is `out × r`. Two properties follow *from the constraint, not from
careful training*:

1. **The base is bit-identical after training.** `W0` is never touched; adapters stack and
   un-stack like lenses.
2. **The edit is capacity-bounded.** The adapter can only express edits of rank ≤ r. That
   cap is a *feature*: capacity you do not spend on the task cannot be spent memorizing
   noise in directions the old task shares — which is what forgetting is made of here.

`examples/model-adaptation/` makes every claim above checkable by hand:

```bash
cd examples/model-adaptation
python3 lora.py                 # head-to-head + rank sweep + floor (~7 s)
python3 lora.py --quick         # ~1 s, same story
python3 lora.py --json
python3 lora.py --ranks 0 1 2 3 4 6
```

A real run (seed 0, defaults, 1200 steps — archived:
`docs/research/model-adaptation/lora-demo-output-2026-09-14.txt`; it is a seeded
computation, yours will match):

```
head to head:
                    method  trainable  new-domain mse  old-domain mse
             base (frozen)          0          2.3695          0.0000
            full fine-tune         72          0.0564          0.0262
                  lora r=2         36          0.0343          0.0074
    qlora r=2 (4-bit base)         36          0.0369          0.0127
```

Read it the way the chapter intends: full fine-tuning moved all 72 base weights and did
* worse on both columns* — the task's true edit is rank 2, so LoRA's constraint cost
nothing while full fine-tuning's extra freedom went to fitting label noise. When the bet
"the edit is low-rank" pays, LoRA wins on accuracy *and* on preservation simultaneously.

### Rank is a capacity knob — sweep it, never assume it

Same data, one adapter per rank:

```
  rank  trainable   train mse   new-domain   old-domain
     0          0      2.3581       2.3695       0.0000
     1         18      0.5473       0.3212       0.0031
     2         36      0.2073       0.0357       0.0076
     3         54      0.2019       0.0400       0.0114
     4         72      0.1966       0.0483       0.0198
     6        108      0.1895       0.0566       0.0262
```

Below the true rank, underfit (rank 1 cannot express the edit). At the true rank, the
new-domain error bottoms out. Above it, watch two columns move in opposite directions:
train MSE keeps falling *past* the label-noise floor — memorization — while the new domain
worsens and the old domain drifts. The right rank is the size of the edit, which you find
by sweeping on a labelled probe set, the same way Chapter 14 freezes eval tasks before a
model change.

### Base precision is a different knob (the QLoRA premise)

QLoRA quantizes the frozen base (4-bit) and adapts on top. The quantization error exists
*before any adapter*, is set by BITS, and forms a floor no rank setting removes:

```
python3 lora.py --bits 3 --ranks 2   # coarser base -> higher floor
```

In the archived run, rank 3 on the same quantized base was worse on **both** columns than
rank 2 — spare capacity just chased the same noise harder. If your adapter has plateaued
and the base itself is the limitation, more rank will not help; more bits will. Two knobs,
two different failures, one table.

### From adapter weights to a Hermes session — the local serving path

An adapter is only useful once a session can reach the merged model. The path this chapter
verifies: merge adapter into base → GGUF → `llama-server` (OpenAI-compatible, loopback) →
Hermes custom endpoint. Verified live on 2026-09-14 against llama.cpp 0.4.1-dev
(commit 7cf1c54, CPU-only) and Hermes v0.21.3 — evidence:
`docs/research/hermes/cli-evidence-2026-09-14-local-endpoint.txt` and
`docs/research/hermes/local-endpoint-context-2026-09-14.md`.

```bash
# 1. serve (verified with SmolLM2-135M-Instruct, Q4_K_M, 105 MB, CPU-only ~50 tok/s)
llama-server --model your-model.gguf --host 127.0.0.1 --port 8080 --jinja
curl -s http://127.0.0.1:8080/v1/models        # the metadata Hermes will read

# 2. one-shot Hermes session against it (verified rc=0, evidence transcript)
CUSTOM_BASE_URL=http://127.0.0.1:8080/v1 \
  hermes chat --provider custom --model <model-id> -q "..."
```

**The 64K gate is the lesson, not a footnote.** Hermes refuses to start an agent on a
model whose reported context is below 64,000 tokens, and SmolLM2 reports 8,192
(`meta.n_ctx` in `/v1/models` — its *training* window). Raising the server's
`--ctx-size` does not fix it: llama.cpp caps the slot at `n_ctx_train` and logs
"the slot context (65536) exceeds the training context of the model (8192) - capping".
The documented remedy is a per-model capability override in config:

```yaml
providers:
  custom:
    api: http://127.0.0.1:8080/v1
    models:
      SmolLM2:
        context_length: 65536
```

Understand what you just did: the *gate* opens, the *model* does not get smarter — past
8,192 tokens a 135M model degrades, and no config entry changes physics. Declaring a
context the weights cannot use is a config-level lie with a runtime bill. Real local agent
work needs weights whose training window is genuinely ≥ 64K (or an agentic server that
compresses).

**Verified here vs. verified by you:** the serving path, the refusal, the override, and a
one-shot completed session are verified on this machine (evidence above). Training a real
transformer with PEFT/LoRA and merging to GGUF are NOT executed by this repo — the exact
commands are in `examples/model-adaptation/README.md`'s "Real model walkthrough" section,
marked *verified by you, not by this repo*, the same distinction Chapter 03c draws.

### Cost and routing integration

An adapted model is a model like any other — Chapter 02's machinery applies unchanged:
`hermes fallback add custom/<model>` for scheduled work, `hermes insights --days 7` to see
whether local traffic actually displaced paid tokens. The economics that make local serving
worth it: token price zero, latency the inverse of your CPU/GPU, and a fresh failure mode —
the box is down. The 6am-cron rule from Chapter 02 holds: no unsupervised job on a single
endpoint without a fallback.

### The decision frame (the interview answer)

1. Does the behaviour need to be default, or can it live in context/retrieval? → Ch 03/03b.
2. Are the examples *knowledge* (changes weekly → index it) or a *skill/format* (stable
   shape → candidate for adaptation)?
3. Budget: labelled examples exist? If not, adaptation has nothing to learn from — build
   the eval set first (Ch 14), which you need for the regression gate anyway.
4. Sweep rank against that probe set; check the preservation column, not just accuracy.
5. Serve, gate on evals (Ch 14's regression discipline), route with fallback (Ch 02),
   watch cost/latency (Ch 14b).

### The general pattern

Strip the toy and the serving path, and this chapter is one claim: **a constrained edit
beats an unconstrained one when you can name the constraint's size, and measuring that size
is the engineering.** LoRA names it (rank), QLoRA adds the second axis (base bits), and the
decision frame says when *not* to edit weights at all. The same shape recurs outside ML:
migrations with a written-down blast radius, config changes behind flags, feature work with
a rollback — capacity you cannot name is drift you cannot bound.

**Evidence:** `docs/research/jobs/source-01.md`, `source-04.md`, `source-05.md` (the three
postings quoted above); `docs/research/jobs/stats-2026-09-14.txt` (cluster counts);
`docs/research/model-adaptation/lora-demo-output-2026-09-14.txt` (archived seeded demo run,
reproducible with `python3 lora.py`); `tests/test_model_adaptation.py` (39 offline tests
pinning the freeze guarantee, rank effects, QLoRA floor, and CLI determinism);
`docs/research/hermes/cli-evidence-2026-09-14-local-endpoint.txt` +
`docs/research/hermes/local-endpoint-context-2026-09-14.md` (live serving path).

## Verified commands

The teaching demo (stdlib only, no dependencies, no GPU):

```bash
cd examples/model-adaptation
python3 lora.py                 # head-to-head + rank sweep + floor (~7 s)
python3 lora.py --quick         # ~1 s
python3 lora.py --json          # machine-readable
python3 lora.py --ranks 0 1 2 3 4 6    # reproduce the sweep table
python3 lora.py --bits 3 --ranks 2     # coarser base, higher floor
python3 -m unittest discover -s ../../tests -k model_adaptation
```

The local serving path (verified live against llama.cpp 0.4.1-dev + Hermes v0.21.3;
evidence: `docs/research/hermes/cli-evidence-2026-09-14-local-endpoint.txt`):

```bash
llama-server --model your-model.gguf --host 127.0.0.1 --port 8080 --jinja
curl -s http://127.0.0.1:8080/health            # {"status":"ok"}
curl -s http://127.0.0.1:8080/v1/models         # n_ctx is what Hermes reads
CUSTOM_BASE_URL=http://127.0.0.1:8080/v1 \
  hermes chat --provider custom --model <model-id> -q "one-shot probe"
```

Routing an adapted model into the fleet (Chapter 02 commands, unchanged):

```bash
hermes fallback add custom/<model-id>
hermes insights --days 7
```

## Common pitfalls

- **Fine-tuning to add facts.** Facts change; a changed fact orphans a training run.
  Facts belong in retrieval (03b/03c). Adaptation is for stable *behaviour*.
- **Rank by vibes.** "Bigger model of the same thing" is the same mistake at adapter
  scale. The sweep is one command; the preservation column (old-domain MSE) is the one
  people skip — accuracy can improve while the old capability quietly rots.
- **Reading the freeze as safety.** The base weights are bit-identical, yes — but a
  rank-1 adapter that deletes a refusal behaviour is still a refusal-behaviour deletion.
  The guarantee bounds *parameters*, not *behaviour*. Evals (Ch 14) remain the gate.
- **Declaring a context the weights cannot use.** The 64K override makes Hermes start;
  it does not make an 8K model hold 64K. Past the training window quality degrades and
  llama.cpp warns in its logs. Match the declaration to `n_ctx_train`, and pick models
  whose training window is agentic-grade.
- **Treating QLoRA's floor as a rank problem.** More rank on a quantized base chases the
  same quantization noise harder (verified in the demo). Floor is a BITS decision.
- **Serving without a fallback.** Local endpoint means one box. Chapter 02's scheduled-job
  rule applies verbatim: unsupervised work assumes a fallback chain exists.
- **Skipping the merge decision.** Multi-adapter serving keeps bases hot and swaps lenses;
  merging bakes one lens in. Composability is worth RAM until it is not — decide per
  deployment, not per fashion.

## Exercises

Work through `exercises/ex03d-model-adaptation.md`. Verification: rank sweep run and the
U-curve explained from your own output, preservation column read, QLoRA floor demonstrated,
a local endpoint served and probed, and a written decision frame for one real candidate.

### Senior interview probes

1. Your fine-tune made the target task better and support tickets went up. What column did
   nobody read, and what does its movement tell you?
2. Why is "the base weights are frozen" NOT a safety argument? What is it an argument for?
3. Someone proposes rank 256 "because it fits". What is the failure mode, and what sweep
   would you demand before accepting any rank?
4. QLoRA plateaus. The team doubles the rank. Predict the result and name the knob that
   would actually move the error.
5. When is fine-tuning the wrong tool against RAG, and what one question separates the
   candidates? Give an example of each side.
6. You must serve three adapters over one base. Merge or multi-serve? What drives the call?
7. llama-server reports n_ctx 8,192; the product needs 64K. Why does `--ctx-size 65536`
   not solve it, and what does "declaring 64K in config" actually change?
8. Where does the regression gate for a fine-tune live, and what freezes before training
   starts?
