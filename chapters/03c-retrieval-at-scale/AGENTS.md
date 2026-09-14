# Chapter 03c — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Scope boundary

Retrieval once the corpus is real: stores, approximate indexes, recall measurement,
dimensionality, embedding economics, freshness. Chunking, fusion, abstention and grounded
citations stay in 03b — this chapter assumes them.

## Ships

`examples/retrieval-scale/` — pluggable embedder, sqlite-vec exact store, a hand-written IVF
index, `schema.sql` for pgvector, and `bench.py`. Pinned by `tests/test_retrieval_scale.py`.

## Care

- This chapter introduces the course's **only third-party dependency** (`sqlite-vec`). Tests
  skip cleanly without it; do not add a second package without the same treatment.
- `schema.sql`, `PgVectorStore` and `GeminiEmbedder` cannot be executed here. Each states so
  in its own file and a test asserts that the statement is present. Keep both.
- `bench.py` must keep the pure-Python exact baseline. Without it the sweep compares C
  against Python and the chapter's central result becomes a claim about the wrong variable.
- The quoted benchmark numbers are one machine's run and are labelled as such. Re-run rather
  than edit them.
