# Chapter 03b — authoring delta

Shared rules: `chapters/AGENTS.md`. Only what is specific to this chapter belongs here.

## Scope boundary

External retrieval: chunking, ranking, fusion, abstention, grounded citations. Context
assembly and memory stay in 03.

## Ships

`examples/retrieval/` — chunkers, BM25, a hashing embedder, RRF, the abstention gate,
grounding with citation checking, and the eval. Pinned by `tests/test_retrieval.py`.

## Care

- The embedder is not semantic and the chapter says so. Do not claim semantic gains it
  cannot demonstrate.
- `qa.json` must keep its answerless cases: without them the eval cannot measure the
  failure this chapter exists to teach.
- On a corpus this small every configuration ties, and the tools say so. Never replace that
  with a picked winner.
