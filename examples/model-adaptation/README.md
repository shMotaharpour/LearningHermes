# `examples/model-adaptation/` — LoRA, learned on a model you can see all of

Chapter 03d. A base model is pretrained; the task shifts; you must change the
model's behaviour without losing what it already knew. This module is the
smallest setting where that trade is real and every number in it is computable
by hand: a linear model `y = W0 @ x`, a new domain living on a slice of the
input space, and a required edit `delta_W` of known true rank. Three knobs
vary, and keeping them separate is the whole chapter:

* **Freezing** — full fine-tuning moves every entry of W0, so afterwards the
  base model no longer exists. LoRA freezes W0 and learns `delta_W = B @ A`;
  the base is bit-identical after training *by construction*, not by tuning.
* **Rank** — the adapter can only express edits of rank ≤ r. Rank is a
  capacity knob: below the true rank of the needed edit it underfits; at the
  true rank the new-domain error bottoms out; above it, spare capacity fits
  label noise — the new domain gets worse again, and fitting noise in
  directions the old domain shares *is* forgetting.
* **Base precision** — QLoRA's premise. Quantizing the frozen base is a
  different knob from rank: it sets an error floor that exists before any
  adapter does, and no adapter setting shrinks it.

```bash
python3 lora.py                 # head-to-head + rank sweep + floor (~7 s)
python3 lora.py --quick         # fewer steps, same story (~1 s)
python3 lora.py --json          # machine-readable report
python3 lora.py --ranks 0 1 2 3 4 6 --steps 2400
```

| File | What it is |
|---|---|
| `lora.py` | The model, the adapters, the training loops, the synthetic task, and the demo CLI. Stdlib only — no numpy, on purpose: at 12×6 you should be able to *read* every multiplication. |

## What the demo shows (seed 0, defaults)

```
head to head:
                    method  trainable  new-domain mse  old-domain mse
             base (frozen)          0          2.3695          0.0000
            full fine-tune         72          0.0564          0.0262
                  lora r=2         36          0.0343          0.0074
    qlora r=2 (4-bit base)         36          0.0369          0.0127
    qlora r=3 (4-bit base)         54          0.0458          0.0201

rank sweep (one adapter per rank, same data, same steps):
  rank  trainable   train mse   new-domain   old-domain
     0          0      2.3581       2.3695       0.0000
     1         18      0.5473       0.3212       0.0031
     2         36      0.2073       0.0357       0.0076
     3         54      0.2019       0.0400       0.0114
     4         72      0.1966       0.0483       0.0198
     6        108      0.1895       0.0566       0.0262

base-precision floor (4-bit base, before any adapter):
  quantization error on new-domain inputs: 0.0075
  quantization error on old-domain inputs: 0.0074
```

Read it in three passes, one per knob:

1. **Freezing, head-to-head.** Here LoRA beats full fine-tuning on *both*
   columns. That is not LoRA being magical — it is what this task's geometry
   buys: the true edit is exactly rank 2 and invisible to the old domain, so
   the rank constraint costs nothing, while full fine-tuning's 72 free
   parameters spent their freedom fitting label noise. This is the bet you
   make when you choose LoRA — *the edit is low-rank* — and this demo is the
   case where the bet pays. W0 is bit-identical afterwards either way you
   serve it (adapter, or merged into the weights; the tests pin that the two
   agree exactly).
2. **Rank, the sweep.** The U-curve is the lesson. Rank 1 cannot express a
   rank-2 edit and plateaus at nine times the minimum. Rank 2 bottoms out.
   Ranks 3–6 get *worse* on the new domain while train mse keeps falling —
   past the label-noise floor (0.25): that is noise being memorized, which is
   what spare capacity is for. And the old-domain column climbs the whole
   way: capacity turned up is forgetting turned up.
3. **Base precision, the floor.** The quantization error exists before any
   adapter and no rank setting shrinks it — only bits do (run `--bits 3` to
   watch it grow twenty-fold). And compare the two qlora rows: more rank on
   the same 4-bit base made *both* columns worse. Extra capacity does not buy
   back base precision; it just chases the same noise harder.

## The geometry, because nothing here is hidden

One random orthonormal frame spans R^12. The new domain uses 9 directions,
the old domain a *different* 9, overlapping in 6 **shared** directions. The
true edit's row space lives entirely in the 3 **new-only** directions, so a
model that learned it perfectly would be invisible on the old domain — every
old-domain mse above is training drift, not task geometry. Gradients can only
point along the new domain's span, so the edit cannot leak into the 3
old-only directions at all; forgetting happens in the shared directions,
where fitting label noise moves old behaviour. The `A`-zeros init makes the
off-span guarantee exact (rows of A stay in the data span forever); the
honest limits below say what real LoRA's `B`-zeros init does differently.

## Honest limits

- **A linear model is not a transformer.** The freeze, the rank cap, and the
  parameter arithmetic transfer exactly. What does not: nonlinearity, layers,
  and optimizer dynamics. In particular this toy's forgetting is noise-fitting
  in shared directions, because full-batch GD on a linear model provably keeps
  the learned delta inside the span of the training inputs — real LLM
  forgetting also involves SGD noise and drift in directions the data does not
  span. Same conclusion, smaller mechanism, and here you can check it by hand.
- **The base model is random, not pretrained.** W0 is a seeded Gaussian matrix.
  It plays the role of a pretrained model (you get weights, not their history),
  but nothing about it is *learned*, so "what the base knew" is only as
  structured as a Gaussian is.
- **Quantization is simulated, not packed.** `quantize_matrix` rounds to a
  per-row-scaled integer grid and dequantizes; real int4 kernels store packed
  integers and fuse the scale multiply. The rounding-error model is the part
  that matters; the memory savings are not modeled at all (weights stay float).
- **This task is LoRA's home turf, and that is a choice.** The true edit is
  exactly low-rank and orthogonal to everything the old domain uses; on a task
  whose needed edit is dense or touches shared directions, full fine-tuning
  wins the new domain and no rank keeps the old one intact. The demo shows the
  favourable case on purpose — the sweep is how you find out which case you
  are actually in.
- **Eval targets are noiseless on purpose.** Training labels carry noise (as
  few-shot data always does); the eval sets hold the expected targets, so the
  tables measure what a model learned rather than how unlucky one noisy draw
  was. Compare against a noisy eval and the sweet spot drowns in eval noise.
- **`--quick` changes conclusions, as fewer steps always do.** It exists for
  smoke tests; the numbers in the tables above come from the full run.
