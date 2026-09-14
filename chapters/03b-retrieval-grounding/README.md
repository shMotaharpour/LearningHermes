# Chapter 03b — Retrieval and Grounding

> **Verified:** 2026-09-14 · Hermes Agent v0.21.3 (2026.9.14) · recheck: `python3 scripts/verify_chapters.py`

## Why this matters (job link)

Retrieval is named in the job evidence and then asked about in the loop. Paramount wants
"chunking and retrieval optimization... hallucination mitigation and grounding techniques"
(`docs/research/jobs/source-01.md`); 100ms wants "retrieval strategies... ensure agent
behaviour aligns with user expectations" (`docs/research/jobs/source-05.md`).

Chapter 03 made the case that the context window *is* the retrieval system, and that
argument holds: most "we need RAG" problems are context-assembly problems, and solving them
with a vector database is how teams end up with an expensive index nobody can debug. But
that is an argument for learning context engineering **first**, not instead. A candidate who
says "I think about context budget rather than vector DBs" and has never built a retrieval
pipeline reads as someone who has never shipped one.

So this chapter builds one, from its parts, and then evaluates it. The parts are the
questions you get asked: how you split documents, what you rank on, how you combine two
rankings that disagree, and — the one that separates people who have run this in production
— how the system decides it has no answer.

## Concepts

Everything below is implemented in `examples/retrieval/`, in standard-library Python: no
vector database, no embedding API, no framework. That is deliberate. BM25 is twenty lines,
and writing it is the difference between "we use a vector DB" and being able to say what
your retriever actually ranks on.

### Chunking is the decision you cannot undo

Retrieval can only return what chunking produced. Get it wrong and no reranker repairs it.
The trade never changes: **bigger chunks carry more context per hit and dilute the match;
smaller chunks match precisely and arrive without the context that made them meaningful.**

Four strategies ship in `retrieval.py`, so you can compare rather than believe:

| Strategy | What it does | Where it hurts |
|---|---|---|
| `fixed` | fixed character windows | cuts mid-sentence; a chunk can end mid-clause |
| `fixed-overlap` | windows sharing 120 chars | a fact straddling a boundary is retrievable from either side, at the cost of near-duplicate chunks that compete for the same rank |
| `sentence` | whole sentences packed to a budget, with sentence overlap | needs sentence splitting, which is language-specific |
| `structural` | split on markdown headings, heading kept with body | needs documents that actually have structure |

```bash
cd examples/retrieval
python3 retrieval.py --compare-chunkers
```

`structural` is the one people skip and usually the one that wins on real documents: the
author already marked where the topics are, and the heading gives every chunk a label —
which is what makes a citation readable to a human reviewing the answer.

Read the **recall@1** column, not recall@3. On a corpus this small everything ties at k=3,
and the tool says so: *a measurement that cannot separate your options has not measured
anything.* That is Chapter 14's rule arriving early, and it is the same reason `--compare-chunkers`
prints a warning that four documents and eight questions are not a benchmark.

### What you rank on: BM25, and why it is still the baseline

`BM25` in `retrieval.py` is the whole classical ranker in twenty lines. Two parameters carry
the ideas:

- **`k1` saturates term frequency.** Seeing a word five times is not five times as relevant
  as seeing it once. Without saturation, keyword-stuffed text wins everything.
- **`b` normalises by length.** Without it, long documents win by accumulating matches.

And `idf` is why it works at all: a term that appears in one chunk out of sixteen is worth
more than one that appears in twelve. If you cannot explain IDF, you cannot explain why your
retriever returned what it did.

BM25 is a strong baseline in 2026. A great many production "RAG" systems would score better
by replacing their embedding search with it and spending the saved effort on chunking.

### Dense retrieval, and the property nobody mentions

`embed()` hashes character trigrams into a fixed vector. It is a real dense representation
and a deliberately weak one — it matches on shared character shape, so it connects
"retained" and "retention" where BM25 sees two unrelated tokens. Swap it for a real
embedding model and nothing else in the pipeline changes; that substitution is the exercise.

But it demonstrates the property that matters, and it is one people discover in production:
**cosine similarity is never zero.** Two unit vectors over real text always overlap
somewhat. A dense retriever therefore *always* returns a confidently ranked list, including
for a question about something your corpus has never heard of. Rank is relative. It cannot
express "none of these".

Hold onto that. It is why the abstention section below exists.

### Combining rankings: reciprocal rank fusion

Lexical and dense retrievers disagree, and their scores are not on the same scale — a BM25
score of 2.0 and a cosine of 0.49 cannot be added, and normalising them means inventing a
weighting you cannot defend to a reviewer.

RRF sidesteps the problem by reading **position only**: each item scores `1/(k + rank)` in
each list, summed. An item both retrievers rank highly wins; the constant `k` (60 here)
dampens the top of each list so one retriever's confident first place cannot dominate.

```bash
python3 retrieval.py "transcript retention period" --mode lexical
python3 retrieval.py "transcript retention period" --mode dense
python3 retrieval.py "transcript retention period" --mode hybrid
```

Three rankings, three different answers. That disagreement is the thing hybrid retrieval
exists to exploit, and seeing it is worth more than reading that hybrid is better.

### Abstention: the part that separates production from a demo

Every retriever returns a top result. That is what ranking *is*. So a RAG system asked "what
is our parental leave allowance?" over a corpus with no HR documents will retrieve
something, rank it first, hand it to a model, and receive a fluent answer with a citation
attached. Nothing in the pipeline so far objects.

Abstention has to come from a signal that **can be zero**, and ranking never is. The one
implemented here is vocabulary coverage: what share of the query's distinctive terms occur
anywhere in the corpus? If none of "parental", "leave", "allowance" appears in any document,
there is nothing to retrieve, and no amount of reranking changes that.

```bash
python3 retrieval.py "what is our parental leave allowance?"
# nothing retrieved above threshold — the corpus does not answer this.
```

Two gates, applied in order:

1. **Before ranking** — coverage below the threshold, return nothing at all.
2. **Per chunk** — require some lexical evidence. A chunk riding on dense similarity alone
   is riding on a number that is never zero.

**This trade is real and you should state it out loud**: a strict vocabulary gate costs you
recall on genuine paraphrases — a question asked entirely in synonyms will be refused. Tune
`min_coverage` against your own corpus, and know which way you are erring. In most business
settings a refusal is cheap and a confident wrong answer is expensive, which is the argument
for erring toward abstention. Say that in an interview and you will sound like someone who
has run one of these.

### Grounding: the three decisions, and the one people skip

`ground.py` turns retrieved chunks into a cited answer. Grounding is won here, and it has
nothing to do with vector math:

1. **What the model may use.** The prompt says: only these passages; if they do not contain
   the answer, reply exactly `NOT IN THE DOCUMENTS`.
2. **How citations are requested.** Every claim carries `[doc#chunk]` — a form you can
   *parse*. Asking for citations in prose makes step 3 impossible.
3. **Whether the citations are checked.** This is the skipped one. A model will cite a
   passage that does not support its claim, and **a citation nobody verifies is decoration
   that makes a wrong answer look sourced.**

`check_citations()` does step 3 deterministically: every cited id must be one that was
actually retrieved, and an answer that asserts something while citing nothing is flagged.
Both checks are free. Run them before you reach for an LLM judge (Chapter 14) — the judge is
for whether the passage *supports* the claim, which is genuinely hard; whether the passage
*exists* is not.

One more thing `ground.py` does: when retrieval returns nothing, **the model is never
called**. A generator handed no passages still writes something plausible, so the cheapest
defence against an invented answer is not to ask the question.

### Evaluating retrieval: three numbers, because there are three failures

```bash
python3 evaluate.py
```

| Metric | The failure it catches |
|---|---|
| `recall@k` | the supporting passage never came back — nothing downstream can repair it, because the generator cannot cite what it never saw |
| `MRR` | it came back, but ranked low; recall alone hides a system that always needs k=5 |
| `citation precision` | the top chunk is from the wrong document — a right answer with a wrong source |
| `abstention rate` | it answered a question the corpus cannot answer |

`qa.json` carries **answerless questions on purpose**. An eval set built only from questions
your corpus answers is structurally unable to measure the failure that costs the most, and
that omission is the most common flaw in a homegrown RAG eval.

These metrics feed Chapter 14 directly: they are deterministic checks, they run in
milliseconds, and they belong in the frozen set before any judge is involved.

**The general pattern.** None of this is Hermes-specific, and interviews ask it that way:
chunking as an irreversible decision, lexical versus dense and why you would keep both,
fusing rankings you cannot compare by score, abstention as a signal that can be zero, and
citation verification as a deterministic check rather than a vibe. Swap in a real embedding
model and a real vector store and every one of those questions has the same answer.

**Evidence:** `docs/research/jobs/source-01.md` and `docs/research/jobs/source-05.md` (the
postings quoted above); the pipeline's behaviour is pinned by `tests/test_retrieval.py`,
which runs offline — including that `cosine` is never zero, which is the claim the
abstention design rests on.

## Verified commands

The pipeline (standard library only; no `hermes` required):

```bash
cd examples/retrieval
python3 retrieval.py --compare-chunkers                  # chunking strategies, measured
python3 retrieval.py "who can declare an incident?"      # hybrid retrieval
python3 retrieval.py "how many backup rotations?" --mode lexical
python3 retrieval.py "what is our parental leave allowance?"   # watch it abstain
python3 evaluate.py                                      # recall, MRR, citations, abstention
python3 ground.py "how long are transcripts kept?" --dry # the grounded prompt, no model
```

Grounding against a real model, and Hermes' own context surfaces from Chapter 03:

```bash
python3 ground.py "how long are transcripts kept?"
hermes prompt-size                # what retrieval is competing with for context budget
hermes memory status              # the built-in alternative to an external index
```

## Common pitfalls

- **Reaching for a vector database first.** Chapter 03's argument stands: most retrieval
  problems are context-assembly problems. Build the lexical baseline, measure it, and make
  the index earn its place.
- **Chunking by character count because it is easy.** Retrieval can only return what
  chunking produced, and you cannot undo it downstream. Measure at least two strategies.
- **Overlap as a free win.** It costs index size and creates near-duplicate chunks that
  compete for the same rank — visible in `--compare-chunkers` as a *lower* recall@1.
- **Averaging scores from two retrievers.** BM25 scores and cosines are not commensurable.
  Fuse by rank.
- **Believing a dense score means relevance.** Cosine is never zero. Every question gets a
  confident ranking, including the ones your corpus cannot answer.
- **An eval set with no answerless questions.** It cannot measure your most expensive
  failure, so you will not know you have it.
- **Citations nobody parses.** If the format is not machine-checkable, step 3 of grounding
  silently does not happen, and the citations are decoration.
- **Calling the model when retrieval returned nothing.** It will still answer. Refuse before
  the call, not after.
- **Reporting a tie as a winner.** When every configuration scores the same, the corpus is
  too small to separate them. Say "inconclusive" and enlarge the set.

## Exercises

Work through `exercises/ex03b-retrieval-grounding.md`. Verification: chunking strategies
compared with a decision recorded, a question the lexical retriever misses and the dense one
finds, the abstention gate tuned against a paraphrase you wrote, an invented citation caught
by the checker, and the eval numbers carried into Chapter 14's frozen set.

### Senior interview probes

1. Walk me through your chunking strategy. What did you compare it against, and what did
   you measure?
2. Why is BM25 still a reasonable baseline, and when does a dense retriever actually beat
   it? What would you measure to find out?
3. You have a BM25 score of 2.0 and a cosine of 0.49 for the same document. Combine them.
   Defend your method.
4. How does your RAG system decide it does not know? Be specific about the signal, and
   explain why a similarity threshold alone does not work.
5. What does a strict abstention gate cost you, and how would you pick the threshold?
6. Your users report that answers are right but cite the wrong paragraph. Which metric
   catches that, and where in the pipeline is the bug likely to be?
7. Design an eval set for a retrieval system over a company handbook. What goes in it that a
   naive set would omit?
8. When would you *not* build retrieval, and put the material in the context window instead?
