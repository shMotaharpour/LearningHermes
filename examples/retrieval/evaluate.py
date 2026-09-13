#!/usr/bin/env python3
"""Grounding evaluation: retrieval quality, citation validity, and abstention.

    python3 evaluate.py
    python3 evaluate.py --mode lexical --chunker sentence
    python3 evaluate.py --json

Three metrics, because a RAG system fails in three different places and one number hides
which. This is the retrieval half of Chapter 14's eval discipline: deterministic checks
first, and a judge only for what they cannot express.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from retrieval import CHUNKERS, Retriever, build_chunks, tokenize  # noqa: E402

QA = Path(__file__).parent / "qa.json"


def evaluate(mode: str, chunker: str, k: int = 3) -> dict:
    cases = json.loads(QA.read_text(encoding="utf-8"))["cases"]
    retriever = Retriever(build_chunks(chunker), mode=mode)
    answerable = [c for c in cases if not c.get("answerless")]
    answerless = [c for c in cases if c.get("answerless")]

    # 1. RETRIEVAL RECALL. Did the supporting passage come back at all? Nothing downstream
    #    can fix a miss here: the generator cannot cite what it never saw.
    recall_hits, rank_sum, ranked = 0, 0.0, 0
    for case in answerable:
        found = retriever.search(case["question"], k=k)
        for position, (chunk, _) in enumerate(found, start=1):
            if case["must_contain"].lower() in chunk.text.lower():
                recall_hits += 1
                rank_sum += 1 / position  # reciprocal rank
                ranked += 1
                break

    # 2. CITATION VALIDITY. Of the chunks we would cite, how many come from the document
    #    that actually holds the answer? A right answer citing the wrong passage is a
    #    reviewer's nightmare, and it is invisible to an answer-only metric.
    cited, correct_doc = 0, 0
    for case in answerable:
        for chunk, _ in retriever.search(case["question"], k=1):
            cited += 1
            if chunk.doc == case["doc"]:
                correct_doc += 1

    # 3. ABSTENTION. On questions the corpus cannot answer, did the retriever return
    #    nothing? This is the metric that separates a system you can put in front of
    #    people from a demo. It is also the one an answerable-only eval set cannot see —
    #    which is why qa.json carries answerless cases on purpose.
    abstained = sum(1 for case in answerless if not retriever.search(case["question"], k=k))

    return {
        "mode": mode, "chunker": chunker, "k": k,
        "answerable": len(answerable), "answerless": len(answerless),
        "recall_at_k": recall_hits / len(answerable) if answerable else 0.0,
        "mrr": rank_sum / len(answerable) if answerable else 0.0,
        "citation_precision": correct_doc / cited if cited else 0.0,
        "abstention_rate": abstained / len(answerless) if answerless else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["lexical", "dense", "hybrid"])
    parser.add_argument("--chunker", choices=list(CHUNKERS))
    parser.add_argument("-k", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    modes = [args.mode] if args.mode else ["lexical", "dense", "hybrid"]
    chunkers = [args.chunker] if args.chunker else ["structural"]
    rows = [evaluate(m, c, args.k) for c in chunkers for m in modes]

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    print(f"{'chunker':<14}{'mode':<10}{'recall@k':>10}{'MRR':>8}"
          f"{'cite prec':>11}{'abstain':>9}")
    print("-" * 62)
    for row in rows:
        print(f"{row['chunker']:<14}{row['mode']:<10}{row['recall_at_k']:>10.0%}"
              f"{row['mrr']:>8.2f}{row['citation_precision']:>11.0%}"
              f"{row['abstention_rate']:>9.0%}")
    print()
    print("recall@k   did the supporting passage come back at all — nothing downstream")
    print("           can repair a miss, because the generator cannot cite what it never saw")
    print("MRR        how high it ranked; recall alone hides a system that always needs k=5")
    print("cite prec  of the top-1 chunks we would cite, how many are from the right document")
    print("abstain    on questions the corpus CANNOT answer, did it correctly return nothing")
    print()
    print("Abstention is the one to watch. An eval set made only of answerable questions")
    print("cannot see the failure that costs the most in production: a confident citation")
    print("for something nobody ever wrote down.")

    measured = {k: {round(r[k], 3) for r in rows}
                for k in ("recall_at_k", "mrr", "citation_precision", "abstention_rate")}
    if len(rows) > 1 and all(len(v) == 1 for v in measured.values()):
        print()
        print("NOTE: every configuration scored identically. That is a fact about this")
        print("corpus — 4 short documents, 10 questions — not a finding about retrieval.")
        print("A measurement that cannot separate your options has not measured anything;")
        print("report it as inconclusive and enlarge the set, exactly as Chapter 14 says")
        print("about a pass-rate delta. Resist the urge to pick a winner from a tie.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
