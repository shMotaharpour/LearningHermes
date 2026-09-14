# Chapter 03c — Retrieval at Scale

> **Verified:** 2026-09-14 · Hermes Agent v0.21.3 (2026.9.14) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Chapter 03b built a retriever from its parts on four documents. Postings ask for the version
that holds up. Reflection wants "hands-on experience with modern AI stacks, including
**vector databases**, RAG pipelines, agent orchestration, evaluations, and fine-tuning"
(`docs/research/jobs/source-04.md`); Paramount wants work "leveraging modern platforms such
as **Vertex AI** to deliver scalable, resilient, and impactful AI solutions"
(`docs/research/jobs/source-01.md`); Databricks asks you to "architect and implement robust,
**scalable** ML infrastructure" (`docs/research/jobs/source-02.md`).

"We use a vector database" is not an answer to any of those. The answer is: which store,
which index, what recall it costs you, what a re-embed costs, and how you know when it went
stale. This chapter measures all five.

## Concepts

Everything below runs in `examples/retrieval-scale/`. It needs one dependency —
`pip install sqlite-vec` — which is the first third-party package this course asks for, and
it earns it: a real vector store with real KNN, no server.

### What actually changes between four documents and four million

Nothing about chunking or grounding (Chapter 03b) changes. Four things appear that did not
exist before:

| | The question |
|---|---|
| **Storage** | vectors are `dims × 4 bytes × N` before any index; at 384 dims that is 1.5 GB per million |
| **Index** | brute force is O(N) per query — at what N does that stop being fine? |
| **Recall** | every approximate index gives away correctness for speed. How much? |
| **Freshness** | the index is a cache of a model's opinion, and it goes stale two different ways |

### Start exact, and keep it

`SqliteVecStore` is brute-force KNN over every vector. That sounds like the thing you
replace, and mostly it is the thing you keep longer than you expect: it is correct by
construction, it needs no tuning, and it is the **ground truth against which an approximate
index can be measured at all**. Delete it and you lose the ability to know what your ANN
index stopped finding.

### Build the approximate index yourself, once

`IVFIndex` in `store.py` is an inverted-file index, written out rather than imported:

1. Pick `nlist` centroids; assign every vector to its nearest.
2. At query time, find the `nprobe` centroids nearest the query.
3. Search only those lists.

You look at roughly `nprobe / nlist` of the corpus, so the speedup is the inverse of that
fraction and the recall you lose is the answers sitting in a list you did not probe. **The
trade is arithmetic you control, not magic.** pgvector's `ivfflat` is this with a better
implementation; HNSW is a different structure with the same bargain under a different knob.

Writing one is worth an hour because "we use HNSW" is not an answer if you cannot say what
it approximates or what it cost.

### Measuring what the approximation cost

```bash
cd examples/retrieval-scale
pip install sqlite-vec
python3 bench.py --n 5000
```

A real run on 3,000 documents:

```
exact search, both implementations — recall 1.00 by definition:
  sqlite-vec (C):   p50 1.87ms
  pure Python:      p50 60.19ms   <- same language as the IVF below

 nprobe   probed  recall@10   p50 ms   vs py    vs C
      1      6%       0.54     2.18   27.6x    0.9x
      2      9%       0.83     3.58   16.8x    0.5x
      4     15%       1.00     5.29   11.4x    0.4x
```

Read the recall column first. At `nprobe=1` the index returns **just over half the right
answers**. Nothing errors, nothing logs, and every query comes back fast and confident. That
is what an untuned ANN index does to a system, and the only reason you can see it here is
that exact search was kept as ground truth.

### Two baselines, or you measure the wrong variable

Now read the last two columns against each other, because this is the result that surprises
people and it is why `bench.py` keeps a pure-Python exact search nobody would ship:

- **Against Python brute force the IVF wins by up to 28×.** That is the algorithmic win,
  and it is real — it looks at 6% of the corpus.
- **Against sqlite-vec's C scan it loses at every setting.** At this N, a good simple
  implementation beats a mediocre clever one.

Compare a hand-written Python index against a C library, conclude "ANN is slower", and you
have drawn a confident conclusion about the wrong variable. The honest comparison needs a
same-language baseline. This is a general research hygiene point, not a retrieval one:
**when a benchmark changes two things at once, it measures neither.**

It is also the argument for not reaching for an index early. Brute force in a fast
implementation stays viable well past the point where people assume it does not. Find the N
where that flips on your data and your hardware; do not inherit someone's number.

### Dimensionality is a storage decision made at schema time

384 dims × 4 bytes = 1,536 bytes per vector, so a million documents is ~1.5 GB of vectors
before any index, id, or payload. That number drives whether your index fits in memory,
which drives your instance size, which drives your bill.

And in `schema.sql` it is `VECTOR(384)` — a column type. **Changing the embedding model is a
migration**: the table is rewritten and the corpus re-embedded. Decide the model before the
schema, not after.

### Embedding at scale: batch it, and know what a re-embed costs

`embed.py` is the seam where a real model goes, and the engineering around it does not
change when you swap the backend:

- **Batch.** Per-text requests pay a round trip per text. The API takes a list.
- **Retry the batch, not the corpus.** A failure at document 40,000 should cost you that
  batch.
- **Record usage.** `bench.py` reports texts, tokens, throughput and cost, because a
  re-embed of the corpus is a purchase and you should be able to price it before someone
  asks.

`GeminiEmbedder` is the real backend for GCP. It needs your project and credentials, so it
is documented here and **verified by you, not by this repo** — a distinction this course
takes seriously enough to say twice.

Two of this chapter's numbers move when you make that swap, and neither is obvious.
**Dimensions**: the local embedder is 384 wide, `gemini-embedding-001` returns 3072 by
default and truncates cleanly to 1536 or 768 — a different width is a full re-embed and an
index rebuild, and eight times the storage at the default. **Request size**: the
per-request limit is the provider's and does not hold even across one model family — the
older `text-embedding-005` accepted 250 texts per call, `gemini-embedding-001` accepts one,
and bulk throughput moves to an asynchronous batch API. Index build, latency percentiles
and the recall methodology are unchanged. So "the engineering survives the swap" is true of
the method and false of the tuning: measure again rather than carrying the old numbers
across. (Model names and limits here are dated research — `docs/research/google/ai-stack-2026-09-14.md`
— not something this repo ran. That is exactly why they sit in the block below that says so.)

### pgvector is the deployment target

`schema.sql` is the artifact that transfers. The Python client is twenty lines; the index
decisions are what you live with. On GCP this runs on Cloud SQL for PostgreSQL or AlloyDB
with the `vector` extension.

Two index families, both with the knob you now recognise:

| | Buys | Costs | Recall knob |
|---|---|---|---|
| `ivfflat` | fast builds, less memory | lower recall per unit latency | `ivfflat.probes` |
| `hnsw` | better recall per unit latency | slow builds, more memory | `hnsw.ef_search` |

And one trap with no error message: **an IVFFlat index must be built on a table that already
holds representative data.** Build it on an empty or tiny table and the centroids are
meaningless, the lists are lopsided, and recall stays bad no matter how you tune probes.
Nothing fails. You just get worse answers.

### Two kinds of stale, two different responses

The index is a cache of a model's opinion about text:

1. **A document changed** → re-embed that row. Cheap and incremental; `updated_at` is how
   the job that does it knows what to pick up.
2. **The model changed** → re-embed everything. This is a migration and a purchase. Write
   the new vectors into a second column so you can **compare recall before cutting over** —
   a model swap that silently degrades retrieval looks exactly like nothing happening.

The second is where Chapter 14's discipline arrives: a model upgrade is a change, and a
change needs a gate.

### The general pattern

Strip the product names and this chapter is three claims that hold on any stack:

- **An approximate index is a correctness/latency trade with a measurable price, and the
  price is recall.** Every vector database makes it for you; the knob is renamed, never
  removed. If you cannot state your recall, you have not chosen — you have defaulted.
- **Keep an exact path in production.** Not to serve traffic, but so recall stays
  measurable. A system that cannot check its own index will not notice it degrade.
- **Benchmarks that change two variables measure neither.** The same-language baseline is
  the difference between a finding and a story.

**Evidence:** `docs/research/jobs/source-01.md`, `source-02.md`, `source-04.md` (the
postings quoted above). The pipeline's behaviour is pinned by `tests/test_retrieval_scale.py`,
which runs offline. `schema.sql`, `PgVectorStore` and `GeminiEmbedder` are **not executed by
those tests** — no PostgreSQL and no GCP project are available to them — and each says so in
the file itself, with a test asserting that it does.

## Verified commands

The pipeline (one dependency, no server, no cloud account):

```bash
cd examples/retrieval-scale
pip install sqlite-vec
python3 bench.py                      # 5,000 documents, the nprobe sweep
python3 bench.py --n 20000 --nlist 128
python3 bench.py --json
python3 -m unittest discover -s ../../tests -k retrieval_scale
```

Against your own GCP project (your credentials, your verification):

```bash
pip install google-genai      # the Gen AI SDK; google-cloud-aiplatform's GenAI modules
                              # were deprecated in 2025 and removed in June 2026
gcloud auth application-default login
EMBED_BACKEND=gemini GOOGLE_CLOUD_PROJECT=your-project python3 bench.py --n 5000
```

Against pgvector (local container, or Cloud SQL / AlloyDB):

```bash
psql "$PGVECTOR_DSN" -f schema.sql
pip install "psycopg[binary]"
PGVECTOR_DSN=postgresql://... python3 bench.py --store pgvector
```

Feed the result back into the agent's context budget (Chapter 03):

```bash
hermes prompt-size --json
```

## Common pitfalls

- **Reaching for an index before measuring brute force.** It is correct, tuning-free, and
  viable far longer than people assume. Find your crossover; do not inherit one.
- **Deleting the exact path once the index works.** You have just removed the only way to
  know what the index stops finding.
- **Reporting a speedup without a recall number.** An index ten times faster that returns
  60% of the right answers is not ten times faster.
- **Benchmarking across languages.** A Python index against a C library measures the
  language. Keep a same-language baseline.
- **Building an IVFFlat index on an empty table.** No error, permanently bad centroids.
- **Treating dimensionality as a model detail.** It is a column type, an instance size, and
  a migration.
- **Re-embedding in a loop, one text per request.** You are paying a round trip per document
  and you will find out during the migration.
- **Swapping the embedding model in place.** Write to a second column and compare recall
  first. A silent degradation looks exactly like nothing happening.
- **Assuming the index is fresh.** Documents change and models change; those need different
  jobs, and only one of them is cheap.

## Exercises

Work through `exercises/ex03c-retrieval-at-scale.md`. Verification: the crossover N found on
your own hardware, a recall/latency curve you produced, a defended `nprobe`, `schema.sql`
run against a real pgvector, and a re-embed priced before it is scheduled.

### Senior interview probes

1. How large does a corpus have to be before you need an approximate index? Answer with a
   method, not a number.
2. What does an ANN index cost you, and how would you measure it on a system already in
   production?
3. Your ANN index is ten times faster than exact search. What is the next question you ask?
4. IVFFlat or HNSW for a corpus rebuilt nightly, on a memory-constrained instance? Defend it.
5. Someone benchmarked a Python ANN library against a C brute-force scan and concluded ANN
   is slower. What is wrong with the experiment?
6. You are switching embedding models. Walk through the migration, including how you find
   out whether retrieval got worse.
7. A million documents at 768 dimensions. How much storage before any index, and what does
   that imply about your instance?
8. Your IVFFlat recall is poor and tuning `probes` does not help. What do you suspect?
