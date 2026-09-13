# `examples/retrieval/` — a retrieval pipeline from its parts

The pipeline Chapter 03b builds. Standard library only: **no vector database, no embedding
API, no framework.** BM25 is twenty lines, and writing it is the difference between "we use
a vector DB" and being able to say what your retriever actually ranks on.

```bash
python3 retrieval.py --compare-chunkers                  # chunking strategies, measured
python3 retrieval.py "who can declare an incident?"      # hybrid retrieval
python3 retrieval.py "what is our parental leave allowance?"   # watch it abstain
python3 evaluate.py                                      # recall, MRR, citations, abstention
python3 ground.py "how long are transcripts kept?" --dry # the grounded prompt, no model
```

| File | What it is |
|---|---|
| `retrieval.py` | four chunkers, BM25, a hashing embedder, RRF fusion, the abstention gate |
| `ground.py` | grounded prompt with parseable citations + deterministic citation checking |
| `evaluate.py` | recall@k, MRR, citation precision, abstention rate |
| `corpus/` | four short policy documents |
| `qa.json` | ten labelled questions — **two of them answerless on purpose** |

## The four ideas

1. **Chunking is the decision you cannot undo.** Retrieval can only return what chunking
   produced. Bigger chunks carry context and dilute the match; smaller chunks match
   precisely and arrive without the context that made them meaningful. Compare, don't guess.
2. **Fuse by rank, not by score.** A BM25 score of 2.0 and a cosine of 0.49 are not
   commensurable. RRF reads position only.
3. **Cosine similarity is never zero.** Two unit vectors over real text always overlap, so a
   dense retriever always returns a confident ranking — including for a question your corpus
   has never heard of. Abstention must come from a signal that *can* be zero; here it is
   vocabulary coverage.
4. **A citation nobody verifies is decoration.** `check_citations()` confirms every cited id
   was actually retrieved. Deterministic, free, and it runs before any LLM judge.

## Honest limits

- **The embedder is not semantic.** It hashes character trigrams, so it catches
  `retained`/`retention` but not a true paraphrase. It is here to demonstrate the
  *architecture* of hybrid retrieval and the never-zero property. Swap in a real embedding
  model and nothing else changes — that is task 2 of the exercise.
- **The abstention gate trades recall for safety.** A question asked entirely in synonyms
  will be refused. `min_coverage` is the dial; which error costs you more is a judgement
  about your setting, not a default.
- **The numbers are not a benchmark.** Four documents and ten questions. On this corpus
  every configuration ties, and `evaluate.py` says so rather than picking a winner from a
  tie — the same rule Chapter 14 applies to a pass-rate delta.
