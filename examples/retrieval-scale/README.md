# `examples/retrieval-scale/` — retrieval that has to hold up

Chapter 03b built a retriever from its parts on four documents. This is the same pipeline
with the parts that only matter once the corpus is real: a vector store, an approximate
index, and measurement of what the approximation cost you.

```bash
pip install sqlite-vec
python3 bench.py                 # 5,000 documents, the nprobe sweep
python3 bench.py --n 20000       # watch the numbers move
python3 bench.py --json
```

| File | What it is |
|---|---|
| `embed.py` | Pluggable embedder with batching and usage accounting. `LocalEmbedder` runs anywhere; `VertexEmbedder` is the real one and needs your GCP project. |
| `store.py` | `SqliteVecStore` (exact, runnable), `IVFIndex` (approximate, hand-written), `PgVectorStore` (the target), plus `recall_at_k`. |
| `schema.sql` | **The artifact that transfers.** pgvector DDL with IVFFlat and HNSW, and what each knob costs. This is what you run on Cloud SQL or AlloyDB. |
| `bench.py` | The measurement: embedding throughput, index build, storage, latency percentiles, recall. |
| `corpus.py` | Synthetic documents with repeating topics, so near-duplicates exist and recall is non-trivial. |

## The result the chapter is built on

```
exact search, both implementations — recall 1.00 by definition:
  sqlite-vec (C):   p50 1.87ms
  pure Python:      p50 60.19ms   <- same language as the IVF below

 nprobe   probed  recall@10   p50 ms   vs py    vs C
      1      6%       0.54     2.18   27.6x    0.9x
      2      9%       0.83     3.58   16.8x    0.5x
      4     15%       1.00     5.29   11.4x    0.4x
```

Two lessons, and you only get both by keeping both baselines:

1. **Against Python brute force the IVF index wins by up to 28x.** That is the algorithmic
   win and it is real: it looks at 6% of the corpus.
2. **Against sqlite-vec's C scan it loses at every setting.** That is the implementation
   -quality win, and it is why "just use brute force" is good advice for far longer than
   people expect. A good simple implementation beats a mediocre clever one.

Compare a hand-written Python index against a C library and conclude "ANN is slower" and
you have measured the wrong variable. Keep the same-language baseline.

And read the recall column: at `nprobe=1` the index returns **just over half** the right
answers, for a speed it does not even win. That is the bargain every vector database makes
for you silently — pgvector's `probes`, HNSW's `ef_search`, the same knob renamed.

## Honest limits

- **The embedder is not semantic.** `LocalEmbedder` is a hashing trick, here so the scale
  engineering is testable offline. The chapter's claims are about batching, index build,
  storage, latency and recall — none of which change when you swap it. `VertexEmbedder`
  is documented and **verified by you, not by this repo**.
- **`schema.sql` and `PgVectorStore` are not executed by the tests.** No PostgreSQL is
  available to them. Run them yourself against your own pgvector version.
- **The IVF index is a teaching implementation.** It is correct and it is slow. Production
  belongs to pgvector, and the reason to write this one is to know what pgvector is doing.
