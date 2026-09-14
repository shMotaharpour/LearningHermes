#!/usr/bin/env python3
"""Measure a retrieval system instead of asserting things about it. Chapter 03c.

    python3 bench.py                      # 5,000 documents, the default sweep
    python3 bench.py --n 20000            # where brute force starts to hurt
    python3 bench.py --n 20000 --nlist 128
    python3 bench.py --json

Five numbers, because five different things go wrong at scale:

  embedding throughput   what a re-embed of the corpus costs you, in time and money
  index build time       an approximate index is not free to create, and it scales
  storage                float32 x dims x N, before any index
  query latency p50/p95  the mean hides the incident (Chapter 14b)
  recall@k               what the approximate index GAVE AWAY for that speed

The last one is the one teams skip, and skipping it is how "we switched to ANN and it got
faster" becomes "and quietly worse". Exact search is the ground truth here, which is the
only reason recall can be measured at all — keep a brute-force path in production for
exactly this.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import corpus  # noqa: E402
import embed as embedding  # noqa: E402
import store as stores  # noqa: E402


def percentile(values: list[float], p: float) -> float:
    import math
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, math.ceil(p / 100 * len(ordered)) - 1))]


def run(n: int, nlist: int, k: int, queries: int, probes: list[int],
        price_per_mtok: float) -> dict:
    docs = corpus.build(n)
    ids = [i for i, _ in docs]
    texts = [t for _, t in docs]

    embedder = embedding.get_embedder()
    vectors = embedder.embed(texts)
    dims = len(vectors[0])

    exact = stores.SqliteVecStore(dims)
    add_seconds = exact.add(ids, vectors)

    index = stores.IVFIndex(dims=dims, nlist=nlist)
    build_seconds = index.build(ids, vectors)

    query_texts = corpus.queries(queries)
    query_vectors = embedder.embed(query_texts)

    exact_latency, truth = [], []
    for vector in query_vectors:
        started = time.monotonic()
        hits = exact.search(vector, k)
        exact_latency.append((time.monotonic() - started) * 1000)
        truth.append(hits)

    # Same-language baseline. Without it the sweep below compares C against Python and
    # calls the result "ANN is slower", which is a conclusion about the wrong variable.
    by_id = dict(zip(ids, vectors))
    python_latency = []
    for vector in query_vectors:
        started = time.monotonic()
        stores.python_exact_search(vector, by_id, k)
        python_latency.append((time.monotonic() - started) * 1000)

    sweep = []
    for nprobe in probes:
        latency, recalls = [], []
        for vector, reference in zip(query_vectors, truth):
            started = time.monotonic()
            hits = index.search(vector, k, nprobe=nprobe)
            latency.append((time.monotonic() - started) * 1000)
            recalls.append(stores.recall_at_k(hits, reference, k))
        sweep.append({
            "nprobe": nprobe,
            "probed_fraction": index.probed_fraction(nprobe),
            "recall_at_k": statistics.fmean(recalls),
            "p50_ms": percentile(latency, 50),
            "p95_ms": percentile(latency, 95),
        })

    return {
        "documents": n, "dims": dims, "k": k, "queries": queries, "nlist": nlist,
        "embedder": embedder.name,
        "embed_report": embedder.usage.report(price_per_mtok),
        "embed_seconds": embedder.usage.seconds,
        "insert_seconds": add_seconds,
        "index_build_seconds": build_seconds,
        "vector_bytes": embedding.storage_bytes(n, dims),
        "exact_p50_ms": percentile(exact_latency, 50),
        "exact_p95_ms": percentile(exact_latency, 95),
        "python_exact_p50_ms": percentile(python_latency, 50),
        "python_exact_p95_ms": percentile(python_latency, 95),
        "sweep": sweep,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=5000, help="documents")
    parser.add_argument("--nlist", type=int, default=64, help="IVF centroids")
    parser.add_argument("-k", type=int, default=10)
    parser.add_argument("--queries", type=int, default=40)
    parser.add_argument("--probes", type=int, nargs="+", default=[1, 2, 4, 8, 16])
    parser.add_argument("--price-per-mtok", type=float, default=0.025,
                        help="YOUR provider's embedding price; the default is a placeholder")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run(args.n, args.nlist, args.k, args.queries, args.probes, args.price_per_mtok)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"corpus: {result['documents']:,} documents · {result['dims']} dims · "
          f"embedder: {result['embedder']}")
    print(f"embedding:   {result['embed_report']}")
    print(f"insert:      {result['insert_seconds']:.2f}s into sqlite-vec")
    print(f"index build: {result['index_build_seconds']:.2f}s for {result['nlist']} lists")
    print(f"vectors:     {result['vector_bytes'] / 1e6:,.1f} MB "
          f"({result['vector_bytes'] / result['documents']:,.0f} bytes/vector, before any index)")
    print()
    print("exact search, both implementations — recall 1.00 by definition:")
    print(f"  sqlite-vec (C):   p50 {result['exact_p50_ms']:.2f}ms   "
          f"p95 {result['exact_p95_ms']:.2f}ms")
    print(f"  pure Python:      p50 {result['python_exact_p50_ms']:.2f}ms   "
          f"p95 {result['python_exact_p95_ms']:.2f}ms   <- same language as the IVF below")
    print()
    print(f"{'nprobe':>7}{'probed':>9}{'recall@' + str(result['k']):>11}"
          f"{'p50 ms':>9}{'p95 ms':>9}{'vs py':>8}{'vs C':>8}")
    print("-" * 61)
    for row in result["sweep"]:
        vs_python = (result["python_exact_p50_ms"] / row["p50_ms"]) if row["p50_ms"] else 0
        vs_c = (result["exact_p50_ms"] / row["p50_ms"]) if row["p50_ms"] else 0
        print(f"{row['nprobe']:>7}{row['probed_fraction']:>8.0%}"
              f"{row['recall_at_k']:>11.2f}{row['p50_ms']:>9.2f}{row['p95_ms']:>9.2f}"
              f"{vs_python:>7.1f}x{vs_c:>7.1f}x")
    print()
    print("Read the recall column against the speedup column. That is the entire ANN")
    print("bargain, and it is the trade every vector database makes for you silently —")
    print("pgvector's `lists`/`probes`, HNSW's `ef_search`, the same knob under a new name.")
    print("An index ten times faster that returns 60% of the right answers is not faster.")
    print()
    print("Now read the last two columns against each other. The IVF beats Python brute")
    print("force — that is the algorithmic win, and it is real. It probably still loses to")
    print("sqlite-vec's C scan at this N, which is the other half of the lesson: a good")
    print("brute-force implementation beats a mediocre index for longer than anyone")
    print("expects. Scale until that flips on YOUR data, and do not assume it already has.")
    print()
    print("The price above is a PLACEHOLDER. Pass --price-per-mtok with your provider's")
    print("published rate before quoting a cost to anyone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
