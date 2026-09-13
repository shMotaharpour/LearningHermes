# Exercise 03b — Retrieval and Grounding

## Objective

Build a retrieval system you can defend: compare chunking strategies with numbers, watch
lexical and dense retrievers disagree, make the system refuse a question it cannot answer,
and catch a model citing a passage it was never given.

You finish with retrieval metrics that belong in Chapter 14's frozen eval set.

Budget: 3–4 hours.

## Tasks

1. **Compare chunkers, then decide.**

   ```bash
   cd examples/retrieval
   python3 retrieval.py --compare-chunkers
   ```

   Record recall@1 for all four. Explain why `fixed-overlap` scores *lower* at k=1 than
   plain `fixed` despite indexing more chunks — the answer is the point of the exercise.
   Then pick a strategy for the rest of this exercise and write one sentence defending it.

2. **Watch the retrievers disagree.** Run the same query in all three modes:

   ```bash
   python3 retrieval.py "transcript retention period" --mode lexical
   python3 retrieval.py "transcript retention period" --mode dense
   python3 retrieval.py "transcript retention period" --mode hybrid
   ```

   Then **find your own query** where lexical and dense return different top results, and
   explain the mechanism — what does each one actually rank on?

3. **Prove cosine is never zero.** In a Python shell:

   ```python
   from retrieval import embed, cosine
   cosine(embed("parental leave allowance"), embed("quantum chromodynamics"))
   ```

   Write down the number. Then explain, in two sentences, why this single fact means a
   similarity threshold cannot be your abstention mechanism.

4. **Break the abstention gate, both ways.**
   - Write a question the corpus *can* answer, phrased entirely in synonyms, and confirm the
     gate refuses it. That is a false refusal — the cost of the design.
   - Lower `min_coverage` until it answers. Now find an answerless question it wrongly
     answers at that setting.
   - Pick a value and justify it in terms of which error is more expensive in your setting.

5. **Add a document, and predict before you measure.** Drop a new markdown file into
   `corpus/`, add two answerable questions and one answerless question to `qa.json`.
   **Write down your predicted recall@1 before running anything.** Then:

   ```bash
   python3 evaluate.py
   python3 -m unittest discover -s ../../tests -k retrieval
   ```

   If a test fails, read it before you change it — `test_every_answerable_case_is_actually_answerable`
   exists because ground truth that isn't in the corpus makes every metric lie.

6. **Catch an invented citation.** Look at the grounded prompt:

   ```bash
   python3 ground.py "how long are transcripts kept?" --dry
   ```

   Then run it for real against a model. Afterwards, hand `check_citations()` an answer with
   a citation that was never retrieved and confirm it is caught. Explain why this check
   should run before any LLM judge.

7. **Make the model misbehave on purpose.** Weaken the prompt in `ground.py` — delete the
   "reply with exactly NOT IN THE DOCUMENTS" rule — and ask a question whose passages do not
   contain the answer. Record what it does. Restore the rule. This is the difference between
   an instruction and an enforcement, and it is why the retrieval gate exists ahead of it.

8. **Hand off to Chapter 14.** Export your metrics:

   ```bash
   python3 evaluate.py --json > retrieval-baseline.json
   ```

   Write two sentences on which of these numbers belong in a nightly regression gate and
   which are one-off design decisions. Commit the baseline.

## Verification checklist

- [ ] Recall@1 recorded for all four chunkers, the `fixed-overlap` result explained, and a
      strategy chosen with a stated reason.
- [ ] A query found where lexical and dense disagree, with the mechanism explained.
- [ ] The non-zero cosine measured, and its consequence for abstention written down.
- [ ] `min_coverage` tuned with both a false refusal and a false answer observed, and a
      value defended in terms of which error costs more.
- [ ] A document and three questions added; predicted recall@1 written down *before*
      measuring; tests passing.
- [ ] An invented citation caught by `check_citations()`, and the reason it precedes a judge
      stated.
- [ ] The weakened-prompt experiment run, showing instruction ≠ enforcement.
- [ ] `retrieval-baseline.json` committed, with a note on what belongs in a regression gate.
