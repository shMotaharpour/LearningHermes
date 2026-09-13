#!/usr/bin/env python3
"""A retrieval pipeline built from its parts. Chapter 03b.

    python3 retrieval.py --compare-chunkers
    python3 retrieval.py "how long are transcripts kept?"
    python3 retrieval.py "how long are transcripts kept?" --mode lexical

Standard library only — no numpy, no vector database, no embedding API. That is a teaching
decision, not a limitation: BM25 is twenty lines, and writing it is the difference between
"we use a vector DB" and being able to say what your retriever actually ranks on.

Everything here is the part of a RAG system you get asked about in an interview: how you
split documents, what you rank with, how you combine two rankings that disagree, and how
you decide there is no good answer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

CORPUS = Path(__file__).parent / "corpus"
WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return WORD.findall(text.lower())


@dataclass
class Chunk:
    doc: str
    chunk_id: str
    text: str
    heading: str = ""

    @property
    def citation(self) -> str:
        return f"{self.doc}#{self.chunk_id}"


# --- chunking ------------------------------------------------------------------------
#
# Three strategies, so they can be COMPARED rather than asserted. The trade is always the
# same: bigger chunks carry more context per hit and dilute the match; smaller chunks match
# precisely and arrive without the context that made them meaningful.


def chunk_fixed(doc: str, text: str, size: int = 400, overlap: int = 0) -> list[Chunk]:
    """Fixed character windows. The baseline, and the one that cuts mid-sentence."""
    out, start, n = [], 0, 0
    step = max(1, size - overlap)
    while start < len(text):
        piece = text[start:start + size].strip()
        if piece:
            out.append(Chunk(doc, f"fixed{n}", piece))
            n += 1
        start += step
    return out


def chunk_sentences(doc: str, text: str, target: int = 400, overlap: int = 1) -> list[Chunk]:
    """Pack whole sentences up to a budget, carrying `overlap` sentences into the next.

    Overlap exists so a fact that straddles a boundary is retrievable from either side. It
    costs index size, and it is usually worth it.
    """
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    out, current, n = [], [], 0
    for sentence in sentences:
        current.append(sentence)
        if sum(len(s) for s in current) >= target:
            out.append(Chunk(doc, f"sent{n}", " ".join(current)))
            n += 1
            current = current[-overlap:] if overlap else []
    if current and (not out or " ".join(current) != out[-1].text):
        out.append(Chunk(doc, f"sent{n}", " ".join(current)))
    return out


def chunk_structural(doc: str, text: str) -> list[Chunk]:
    """Split on markdown headings, keeping the heading with its body.

    This is the one people skip and the one that usually wins on real documents: the author
    already marked where the topics are. The heading also gives every chunk a label, which
    is what makes a citation readable.
    """
    out, heading, buffer, n = [], "", [], 0

    def flush():
        nonlocal buffer, n
        body = " ".join(buffer).strip()
        if body:
            out.append(Chunk(doc, f"sec{n}", f"{heading}\n{body}" if heading else body,
                             heading=heading))
            n += 1
        buffer = []

    for line in text.splitlines():
        if line.startswith("#"):
            flush()
            heading = line.lstrip("#").strip()
        else:
            buffer.append(line)
    flush()
    return out


CHUNKERS = {
    "fixed": lambda d, t: chunk_fixed(d, t),
    "fixed-overlap": lambda d, t: chunk_fixed(d, t, overlap=120),
    "sentence": lambda d, t: chunk_sentences(d, t),
    "structural": chunk_structural,
}


def load_corpus(root: Path = CORPUS) -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(root.glob("*.md"))}


def build_chunks(strategy: str = "structural", root: Path = CORPUS) -> list[Chunk]:
    chunker = CHUNKERS[strategy]
    return [c for doc, text in load_corpus(root).items() for c in chunker(doc, text)]


# --- lexical ranking: BM25 -----------------------------------------------------------


@dataclass
class BM25:
    """Okapi BM25. Twenty lines, and it is still a strong baseline in 2026.

    k1 controls how fast term frequency saturates: seeing a word five times is not five
    times as relevant as seeing it once. b controls length normalisation: without it, long
    documents win everything by accumulating matches.
    """

    chunks: list[Chunk]
    k1: float = 1.5
    b: float = 0.75
    docs: list[list[str]] = field(default_factory=list)
    df: Counter = field(default_factory=Counter)
    avgdl: float = 0.0

    def __post_init__(self):
        self.docs = [tokenize(c.text) for c in self.chunks]
        for tokens in self.docs:
            self.df.update(set(tokens))
        self.avgdl = (sum(len(d) for d in self.docs) / len(self.docs)) if self.docs else 0.0

    def idf(self, term: str) -> float:
        n, df = len(self.docs), self.df.get(term, 0)
        # The +0.5 smoothing keeps a term present in every document from going negative.
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def score(self, query: str) -> list[float]:
        terms = tokenize(query)
        out = []
        for tokens in self.docs:
            counts, length, total = Counter(tokens), len(tokens), 0.0
            for term in terms:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * length / (self.avgdl or 1))
                total += self.idf(term) * (tf * (self.k1 + 1)) / denom
            out.append(total)
        return out


# --- dense ranking: a hashing embedder ------------------------------------------------


def embed(text: str, dims: int = 256) -> list[float]:
    """Character-trigram hashing into a fixed vector, L2-normalised.

    This is a real dense representation and a deliberately weak one. It is here because it
    is deterministic, needs no API, and — the point — it matches on SHARED CHARACTER SHAPE,
    so it finds "retained"/"retention" where BM25 sees two unrelated tokens. That is the
    whole argument for hybrid retrieval, demonstrated rather than asserted.

    Swap this for a real embedding model in production. The pipeline below does not change.
    """
    vector = [0.0] * dims
    normalized = " ".join(tokenize(text))
    for i in range(max(1, len(normalized) - 2)):
        gram = normalized[i:i + 3]
        slot = int(hashlib.md5(gram.encode()).hexdigest(), 16) % dims
        vector[slot] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # both are unit vectors


# --- fusion ---------------------------------------------------------------------------


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> dict[int, float]:
    """Combine rankings by RANK, not by score. The standard answer to a real problem.

    BM25 scores and cosine similarities are not on the same scale and never will be, so
    adding or averaging them means inventing a weighting you cannot defend. RRF only reads
    position: an item's contribution is 1/(k + rank). The k dampens the top of each list so
    one retriever's confident first place cannot dominate the fusion.
    """
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, index in enumerate(ranking, start=1):
            scores[index] = scores.get(index, 0.0) + 1.0 / (k + rank)
    return scores


# Words carrying no topical signal. A query made only of these has no distinctive terms,
# and "coverage" below would be undefined rather than zero.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for", "from",
    "how", "i", "in", "is", "it", "long", "many", "much", "my", "of", "on", "or", "our",
    "should", "that", "the", "their", "to", "we", "what", "when", "where", "which", "who",
    "why", "will", "with", "you", "your",
}


@dataclass
class Retriever:
    chunks: list[Chunk]
    mode: str = "hybrid"  # lexical | dense | hybrid
    min_coverage: float = 0.34

    def __post_init__(self):
        self.bm25 = BM25(self.chunks)
        self.vectors = [embed(c.text) for c in self.chunks]

    def coverage(self, query: str) -> float:
        """Share of the query's distinctive terms that occur anywhere in the corpus.

        This is the abstention signal, and it exists because of a property that surprises
        people: COSINE SIMILARITY IS NEVER ZERO. Two unit vectors over hashed character
        trigrams always overlap somewhat, so a dense retriever ALWAYS returns a ranked list,
        confidently, for a question about something the corpus has never heard of. Rank is
        relative; it cannot express "none of these".

        So abstention has to come from a signal that CAN be zero. Vocabulary coverage is the
        cheapest honest one: if none of "parental", "leave", "allowance" appears in any
        document, there is nothing to retrieve and no amount of ranking will change that.
        """
        terms = [t for t in tokenize(query) if t not in STOPWORDS]
        if not terms:
            return 0.0
        return sum(1 for t in terms if self.bm25.df.get(t, 0) > 0) / len(terms)

    def search(self, query: str, k: int = 4) -> list[tuple[Chunk, float]]:
        # Gate before ranking, not after. Ranking a corpus that cannot answer the question
        # produces a plausible top result every time, and that result is what a RAG system
        # then cites.
        if self.coverage(query) < self.min_coverage:
            return []

        lexical = self.bm25.score(query)
        query_vector = embed(query)
        dense = [cosine(query_vector, v) for v in self.vectors]

        if self.mode == "lexical":
            ranked = sorted(range(len(self.chunks)), key=lambda i: -lexical[i])
            scored = [(i, lexical[i]) for i in ranked]
        elif self.mode == "dense":
            ranked = sorted(range(len(self.chunks)), key=lambda i: -dense[i])
            scored = [(i, dense[i]) for i in ranked]
        else:
            lex_rank = sorted(range(len(self.chunks)), key=lambda i: -lexical[i])
            den_rank = sorted(range(len(self.chunks)), key=lambda i: -dense[i])
            fused = reciprocal_rank_fusion([lex_rank, den_rank])
            scored = sorted(fused.items(), key=lambda kv: -kv[1])

        # Per-chunk gate: a chunk with zero lexical overlap is riding on dense similarity
        # alone, which — see coverage() — is never zero. Requiring some lexical evidence is
        # what stops a fluent-but-unrelated passage from becoming a citation.
        out = [(self.chunks[i], score) for i, score in scored[:k] if lexical[i] > 0]
        return out


# --- CLI -------------------------------------------------------------------------------


def compare_chunkers() -> int:
    corpus = load_corpus()
    questions = json.loads((Path(__file__).parent / "qa.json").read_text(encoding="utf-8"))
    print(f"{'strategy':<16}{'chunks':>8}{'avg chars':>11}{'recall@1':>10}{'recall@3':>10}")
    print("-" * 55)
    # Recall is only defined where an answer exists; the answerless cases measure
    # abstention instead (evaluate.py), and averaging the two would hide both.
    answerable = [c for c in questions["cases"] if not c.get("answerless")]
    for name in CHUNKERS:
        chunks = [c for doc, text in corpus.items() for c in CHUNKERS[name](doc, text)]
        retriever = Retriever(chunks)
        def recall(k: int) -> float:
            hits = sum(
                any(case["must_contain"].lower() in c.text.lower()
                    for c, _ in retriever.search(case["question"], k=k))
                for case in answerable
            )
            return hits / len(answerable)

        avg = sum(len(c.text) for c in chunks) / len(chunks)
        print(f"{name:<16}{len(chunks):>8}{avg:>11.0f}"
              f"{recall(1):>10.0%}{recall(3):>10.0%}")
    print(f"\nRecall@k = share of the {len(answerable)} answerable questions whose "
          "supporting text appeared in the top k.")
    print("Read recall@1, not recall@3: at k=3 this corpus is too small to separate the")
    print("strategies, and a metric that cannot tell your options apart is not measuring.")
    print("More chunks is not better — it is more index, more embeddings, and more ways to")
    print("retrieve a fragment that no longer says what the author meant.")
    print("\nAnd these numbers are NOT a benchmark: 4 documents and 8 questions. The method")
    print("transfers; the numbers do not. Re-run it on your own corpus, which is the point.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", nargs="?")
    parser.add_argument("--mode", choices=["lexical", "dense", "hybrid"], default="hybrid")
    parser.add_argument("--chunker", choices=list(CHUNKERS), default="structural")
    parser.add_argument("-k", type=int, default=4)
    parser.add_argument("--compare-chunkers", action="store_true")
    args = parser.parse_args()

    if args.compare_chunkers:
        return compare_chunkers()
    if not args.query:
        parser.error("give a query, or use --compare-chunkers")

    retriever = Retriever(build_chunks(args.chunker), mode=args.mode)
    results = retriever.search(args.query, k=args.k)
    if not results:
        print("nothing retrieved above threshold — the corpus does not answer this.")
        return 0
    for chunk, score in results:
        print(f"\n[{chunk.citation}]  score {score:.4f}")
        print("  " + chunk.text.replace("\n", " ")[:220])
    return 0


if __name__ == "__main__":
    sys.exit(main())
