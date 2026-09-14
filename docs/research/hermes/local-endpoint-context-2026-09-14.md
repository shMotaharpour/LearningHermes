# Local endpoint context requirement — verified 2026-09-14, Hermes Agent v0.21.3

Raw transcript: `cli-evidence-2026-09-14-local-endpoint.txt` (probe script output).
Server under test: llama-server 0.4.1-dev (commit 7cf1c54), CPU-only, 127.0.0.1:8080,
model `SmolLM2-135M-Instruct-Q4_K_M.gguf` (GGUF, 105,454,432 bytes).

## The behaviour

1. `hermes chat --provider custom --model SmolLM2 -q ...` with
   `CUSTOM_BASE_URL=http://127.0.0.1:8080/v1` **refuses to start**:

   ```
   Failed to initialize agent: Model SmolLM2 has a context window of 8,192 tokens, which is
   below the minimum 64,000 required by Hermes Agent. Choose a model with at least 64K context.
   If your server reports a window smaller than the model's true window, set
   model.context_length in config.yaml to the real value (this must be at least 64K).
   ```

   The 8,192 figure is what llama-server reports in `/v1/models` (`meta.n_ctx`) — it is the
   model's TRAINING context, not a client preference. `--ctx-size 65536` on the server does
   not change it: llama.cpp caps the slot at `n_ctx_train` (log line: "the slot context
   (65536) exceeds the training context of the model (8192) - capping").

2. The documented remedy works: declaring the per-model capability override in the
   **profile's** config.yaml (a throwaway `lhftprobe` profile, deleted after the probe —
   the default profile was never modified):

   ```yaml
   providers:
     custom:
       api: http://127.0.0.1:8080/v1
       models:
         SmolLM2:
           context_length: 65536
   ```

   Then `hermes chat --provider custom --model SmolLM2 -q "Reply with exactly:
   LOCAL_ENDPOINT_OK"` **starts, runs the agent loop, and completes with rc 0**
   (see the evidence transcript; the tiny model's answer text is irrelevant — the
   transport, auth-free loopback route, and agent loop are what is verified).

## Claim boundaries

- VERIFIED on this machine: the <64K refusal, the exact error text, the override's
  effectiveness, one-shot completion through the profile, profile create/delete lifecycle.
- NOT verified here: long multi-turn sessions against the 135M model (its native window
  is 8,192 — declaring 64K does not give the model more memory than it was trained for;
  quality past the training window degrades and llama.cpp warns accordingly). Real local
  serving for agent work needs a model whose n_ctx_train is genuinely >= 64K.
