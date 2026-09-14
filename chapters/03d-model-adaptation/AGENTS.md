# Chapter 03d — Model Adaptation: fine-tuning, LoRA, and serving your own weights

Scope for this chapter is defined in CURRICULUM.md (Part I mapping table).

## Scope boundary

Adapting model *weights* and serving them locally: what full fine-tuning changes, what LoRA
constrains, what QLoRA buys, and how a fine-tune reaches a Hermes session as a provider.
Retrieval-based knowledge injection stays in 03b/03c; routing *between* adapted and base
models stays in 02.

## Ships

`examples/model-adaptation/` — a stdlib-only LoRA on a linear model with rank sweeps, a
catastrophic-forgetting demonstration, a QLoRA error-floor experiment, and an adapter file
format. Pinned by `tests/test_model_adaptation.py`.

## Care

- The teaching model is a linear model, on purpose. Do not describe it as a language model
  or claim the numbers transfer to transformers; the *mechanisms* transfer, the digits do not.
- The demo task must keep its two conflicting behaviours (main task + retained capability).
  Without the second behaviour there is nothing to forget, and the chapter's central
  demonstration quietly stops demonstrating.
- No GPU and no real training run is available in this repo. Real-model training and the
  llama.cpp / vLLM serving walkthrough are documented with the exact commands but marked as
  **verified by you, not by this repo** — keep that distinction in the text.
