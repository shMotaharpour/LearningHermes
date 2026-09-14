# Exercise 03d — Model Adaptation

## Objective

Produce the three artifacts the decision frame needs, from your own runs rather than the
chapter's tables: a rank sweep with its U-curve explained, a QLoRA floor demonstrated, and
a written fine-tune-vs-RAG decision for one real candidate task.

Budget: 2–3 hours (the demo is ~7 s per run; the thinking is the work).

## Tasks

1. **Run the demo and own the numbers.**

   ```bash
   cd examples/model-adaptation
   python3 lora.py
   ```

   Before reading further in the output, predict: which method wins the new-domain column,
   and which wins the old-domain column? Then check. If both predictions were wrong, write
   down why the freeze guarantee plus a low-rank edit beats more freedom on both.

2. **Find the U-curve on paper.** Run

   ```bash
   python3 lora.py --ranks 0 1 2 3 4 6 --json
   ```

   and plot (paper is fine) new-domain MSE against rank. Mark the true rank (2) and the
   label-noise floor. In two sentences: why does the curve bottom out exactly there, and
   what does the train-MSE column do past the floor?

3. **Read the preservation column.** From the same sweep, compare old-domain MSE at rank 2
   and rank 6. The base weights are frozen in both — so *what* moved, and why is "the base
   is frozen" not a safety argument? Write the one-sentence version you would say to a
   reviewer who claimed LoRA needs no eval.

4. **Demonstrate the QLoRA floor.**

   ```bash
   python3 lora.py --bits 3 --ranks 2
   python3 lora.py --bits 4 --ranks 2
   python3 lora.py --bits 8 --ranks 2
   ```

   Record the new-domain MSE at each precision before and after adaptation. Which part of
   the error shrank with bits, and which part needed the adapter? One sentence on why
   doubling rank on a 3-bit base would have been the wrong move.

5. **Serve a local model and reach it from Hermes.** Any GGUF works; a tiny one is fine
   (the chapter verified the path with a 105 MB SmolLM2 on CPU-only):

   ```bash
   llama-server --model your-model.gguf --host 127.0.0.1 --port 8080 --jinja
   curl -s http://127.0.0.1:8080/v1/models     # note meta.n_ctx
   CUSTOM_BASE_URL=http://127.0.0.1:8080/v1 \
     hermes chat --provider custom --model <model-id> -q "one-shot probe"
   ```

   Two things to record. **The refusal** (if your model reports < 64K): quote the exact
   error and explain in one sentence why `--ctx-size 65536` on the server did not change
   what Hermes saw. **The override**: add the `providers.custom.models.<model>.
   context_length` block in a throwaway profile, rerun, and record whether the session
   completes. Then answer: what did your override change, and what did it not?

6. **Write the decision frame for a real candidate.** Pick one behaviour change from your
   own work (a format, a domain voice, a classification). One page:
   - why prompt/retrieval alone is insufficient (or — honest outcome — sufficient, which
     is an acceptable answer and a cheaper one),
   - what labelled probe set you would freeze BEFORE training, and its pass bar,
   - the rank sweep plan (ranks, metric, preservation column),
   - serving: merged or multi-adapter, endpoint, fallback for scheduled work.

## Verification checklist

- [ ] Demo run archived; predictions written before reading the output.
- [ ] U-curve plotted from `--json` output; bottom-out rank matches the true rank.
- [ ] One-sentence answer on why frozen-base ≠ safety, grounded in the preservation column.
- [ ] Floor demonstrated at three precisions; the bits-vs-rank attribution written down.
- [ ] Local endpoint served; `/v1/models` metadata recorded; Hermes one-shot completed.
- [ ] The refusal (or its absence) explained, including what `--ctx-size` does and does not do.
- [ ] Decision frame written for a real candidate, with the eval set named before training.
