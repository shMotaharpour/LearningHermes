# Exercise 03c — Retrieval at Scale

## Objective

Find the numbers rather than inherit them: the corpus size where brute force stops being
fine on *your* hardware, the recall your approximate index actually delivers, and what a
re-embed of your corpus costs before anyone asks.

Budget: 3–4 hours, plus a container if you do task 7.

## Tasks

1. **Get a baseline.**

   ```bash
   cd examples/retrieval-scale
   pip install sqlite-vec
   python3 bench.py --n 5000
   ```

   Record all five numbers: embedding throughput, index build time, storage, latency
   percentiles, and the recall sweep.

2. **Find your crossover.** Run at `--n 1000`, `5000`, `20000`, `50000`. Plot — on paper is
   fine — exact p50 against corpus size. **Where does exact search stop meeting a 50 ms
   budget on your machine?** That number is the answer to "when do I need a vector index",
   and it is yours, not a blog post's.

3. **Read the two speedup columns.** At `--n 20000`, is the IVF index faster than
   sqlite-vec's C scan at any `nprobe` that still gives you recall above 0.9? Write down the
   answer and what it implies about reaching for an index early.

4. **Defend an `nprobe`.** Pick one for a support-search product where a missed answer means
   a customer does not find their policy. Then pick one for an internal "find me something
   like this" tool. Justify the difference in one sentence each — the same index, two
   different correct answers.

5. **Change one variable at a time.** Re-run with `--nlist 16` and `--nlist 256` at fixed
   `--n`. What happened to build time, to recall at fixed `nprobe`, and to `probed`? Explain
   the mechanism rather than the numbers.

6. **Price a re-embed.** Take the token count from the embedding report, find your
   provider's published embedding price, and compute what re-embedding the corpus costs at
   1×, 10× and 100× your current size. Then answer: at what size does a model upgrade need
   sign-off rather than a decision?

7. **Run the real store.** Start pgvector and apply the schema:

   ```bash
   docker run -d -e POSTGRES_PASSWORD=x -p 5432:5432 pgvector/pgvector:pg16
   psql "postgresql://postgres:x@localhost:5432/postgres" -f schema.sql
   ```

   Confirm both index families exist. Then **build an IVFFlat index on an empty table**,
   insert 10,000 rows, and measure recall. Compare with an index built after the insert.
   Record what the failure looked like — that is the point of the exercise.

8. **On GCP, if you have a project.** Point the embedder at a real model:

   ```bash
   pip install google-genai        # NOT google-cloud-aiplatform — see embed.py
   gcloud auth application-default login
   EMBED_BACKEND=gemini GOOGLE_CLOUD_PROJECT=... python3 bench.py --n 2000
   ```

   Three things to record. **Throughput** versus the local embedder — and before you run
   it, predict the number: `gemini-embedding-001` accepts one text per request, so 2,000
   documents is 2,000 round trips. **Recall at fixed `nprobe`** — real embeddings cluster
   differently from a hashing trick, and your tuning may not survive the swap. **Storage**
   — the default output is 3072 dimensions against the local 384, so run
   `embed.storage_bytes` for both and put the two numbers next to the recall you measured.

   Then answer the question that decides the design: at what corpus size does the
   one-request-per-text limit stop being an inconvenience and start being the reason you
   move to the Batch API? Work it out from your measured per-request latency, not from
   intuition.

9. **Write the migration plan.** One page: you are moving from a 384-dim model to a 768-dim
   one. Cover the schema change, where the new vectors live during the transition, how you
   compare recall before cutting over, the cost, and the rollback. This is the artifact an
   interviewer actually wants.

## Verification checklist

- [ ] Five baseline numbers recorded at one corpus size.
- [ ] Crossover N found on your own hardware against a stated latency budget.
- [ ] The IVF-vs-C result recorded, with what it implies about reaching for an index early.
- [ ] Two `nprobe` choices for two products, each defended in one sentence.
- [ ] `nlist` swept, with the mechanism explained rather than the numbers restated.
- [ ] Re-embed priced at 1×, 10× and 100×, with a threshold for needing sign-off.
- [ ] `schema.sql` applied to a real pgvector; both index families confirmed.
- [ ] The empty-table IVFFlat failure reproduced and its symptom written down.
- [ ] A dimensionality-migration plan covering transition, comparison, cost and rollback.
