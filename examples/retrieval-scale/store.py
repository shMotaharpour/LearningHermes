#!/usr/bin/env python3
"""Vector stores, and an ANN index built from its parts. Chapter 03c.

Two stores and one index:

* ``SqliteVecStore`` — exact KNN via sqlite-vec. Runs anywhere, no server, and is the
  GROUND TRUTH the approximate index is measured against.
* ``PgVectorStore`` — the deployment target. pgvector is what Cloud SQL and AlloyDB give
  you, and what most teams end up on. The schema and the index DDL are in `schema.sql`;
  this class is the thin client. It needs a running PostgreSQL, so the repo's tests skip
  it — say so out loud rather than implying coverage.
* ``IVFIndex`` — an inverted-file approximate index, written out rather than imported.

Building the ANN index by hand is the point of the chapter. "We use HNSW" is not an answer
if you cannot say what it approximates or what it costs you, and the cheapest way to learn
that is to implement the simplest real ANN structure and measure the recall you gave away.
"""
from __future__ import annotations

import math
import random
import sqlite3
import struct
import time
from dataclasses import dataclass


def pack(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# --- exact ----------------------------------------------------------------------------


class SqliteVecStore:
    """Exact KNN. Brute force over every vector, every query.

    Brute force is not a toy: it is correct by construction, it needs no tuning, and on
    modest corpora it is fast enough that an approximate index is pure added risk. The
    chapter's job is to find the N where that stops being true on YOUR hardware, rather
    than to assume it.
    """

    name = "sqlite-vec (exact)"

    def __init__(self, dims: int, path: str = ":memory:"):
        import sqlite_vec

        self.dims = dims
        self.db = sqlite3.connect(path)
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.db.enable_load_extension(False)
        self.db.execute(
            f"create virtual table vectors using vec0(id integer primary key, "
            f"embedding float[{dims}])"
        )

    def add(self, ids: list[int], vectors: list[list[float]], batch_size: int = 1000) -> float:
        started = time.monotonic()
        for start in range(0, len(ids), batch_size):
            chunk = list(zip(ids[start:start + batch_size],
                             vectors[start:start + batch_size]))
            self.db.executemany("insert into vectors(id, embedding) values (?, ?)",
                                [(i, pack(v)) for i, v in chunk])
        self.db.commit()
        return time.monotonic() - started

    def search(self, vector: list[float], k: int = 10) -> list[tuple[int, float]]:
        rows = self.db.execute(
            "select id, distance from vectors where embedding match ? and k = ? "
            "order by distance", (pack(vector), k),
        ).fetchall()
        return [(int(i), float(d)) for i, d in rows]

    def count(self) -> int:
        return self.db.execute("select count(*) from vectors").fetchone()[0]


# --- approximate -----------------------------------------------------------------------


@dataclass
class IVFIndex:
    """Inverted file index: cluster the vectors, then search only the nearest clusters.

    The whole idea in three steps:

    1. Pick ``nlist`` centroids and assign every vector to its nearest one.
    2. At query time, find the ``nprobe`` centroids nearest the query.
    3. Search only the vectors in those lists.

    You look at roughly ``nprobe / nlist`` of the corpus, so the speedup is the inverse of
    that fraction — and the recall you lose is the answers that were sitting in a list you
    did not probe. **That is the trade, and it is not hidden: it is arithmetic you control.**

    This is what pgvector's ``ivfflat`` does with a better implementation. HNSW is a
    different structure with the same bargain: a tunable knob (``ef_search``) that buys
    recall with latency.
    """

    dims: int
    nlist: int = 64
    seed: int = 0
    centroids: list[list[float]] = None
    lists: dict[int, list[int]] = None
    vectors: dict[int, list[float]] = None
    build_seconds: float = 0.0

    def build(self, ids: list[int], vectors: list[list[float]], iterations: int = 5) -> float:
        """k-means over a sample. Index build is not free, and this measures it."""
        started = time.monotonic()
        rng = random.Random(self.seed)
        self.vectors = dict(zip(ids, vectors))

        # Seed centroids from a sample rather than from the whole corpus: k-means over
        # every vector is the part that makes index builds expensive at scale, and
        # sampling is what real implementations do.
        sample = rng.sample(vectors, min(len(vectors), max(self.nlist * 20, 1000)))
        self.centroids = [list(v) for v in rng.sample(sample, min(self.nlist, len(sample)))]

        for _ in range(iterations):
            buckets: dict[int, list[list[float]]] = {i: [] for i in range(len(self.centroids))}
            for vector in sample:
                buckets[self._nearest_centroid(vector)].append(vector)
            for index, members in buckets.items():
                if members:
                    self.centroids[index] = [sum(col) / len(members) for col in zip(*members)]

        self.lists = {i: [] for i in range(len(self.centroids))}
        for identifier, vector in zip(ids, vectors):
            self.lists[self._nearest_centroid(vector)].append(identifier)

        self.build_seconds = time.monotonic() - started
        return self.build_seconds

    def _nearest_centroid(self, vector: list[float]) -> int:
        best, best_score = 0, -2.0
        for index, centroid in enumerate(self.centroids):
            score = dot(vector, centroid)
            if score > best_score:
                best, best_score = index, score
        return best

    def search(self, vector: list[float], k: int = 10, nprobe: int = 4
               ) -> list[tuple[int, float]]:
        ranked = sorted(range(len(self.centroids)),
                        key=lambda i: -dot(vector, self.centroids[i]))[:nprobe]
        candidates: list[int] = []
        for index in ranked:
            candidates.extend(self.lists[index])
        scored = [(i, 1.0 - dot(vector, self.vectors[i])) for i in candidates]
        scored.sort(key=lambda pair: pair[1])
        return scored[:k]

    def probed_fraction(self, nprobe: int) -> float:
        """Share of the corpus an nprobe query actually looks at. The speedup, predicted."""
        total = sum(len(v) for v in self.lists.values()) or 1
        largest = sorted((len(v) for v in self.lists.values()), reverse=True)[:nprobe]
        return sum(largest) / total


# --- the deployment target --------------------------------------------------------------


class PgVectorStore:
    """pgvector client. The target this chapter designs for; NOT exercised by the tests.

        docker run -e POSTGRES_PASSWORD=x -p 5432:5432 pgvector/pgvector:pg16
        psql ... -f schema.sql
        pip install psycopg[binary]
        PGVECTOR_DSN=postgresql://... python3 bench.py --store pgvector

    On GCP this is Cloud SQL for PostgreSQL or AlloyDB with the `vector` extension enabled,
    which is why the schema rather than the client is the artifact worth carrying: the
    client is twenty lines and the index decisions in `schema.sql` are the ones you live
    with.
    """

    name = "pgvector"

    def __init__(self, dims: int, dsn: str):
        import psycopg  # optional dependency; absent in this repo's environment

        self.dims, self.conn = dims, psycopg.connect(dsn)

    def add(self, ids: list[int], vectors: list[list[float]], batch_size: int = 1000) -> float:
        started = time.monotonic()
        with self.conn.cursor() as cur:
            for start in range(0, len(ids), batch_size):
                chunk = list(zip(ids[start:start + batch_size],
                                 vectors[start:start + batch_size]))
                cur.executemany(
                    "insert into documents (id, embedding) values (%s, %s) "
                    "on conflict (id) do update set embedding = excluded.embedding",
                    [(i, str(v)) for i, v in chunk],
                )
        self.conn.commit()
        return time.monotonic() - started

    def search(self, vector: list[float], k: int = 10) -> list[tuple[int, float]]:
        with self.conn.cursor() as cur:
            cur.execute(
                "select id, embedding <=> %s::vector as distance from documents "
                "order by embedding <=> %s::vector limit %s",
                (str(vector), str(vector), k),
            )
            return [(int(i), float(d)) for i, d in cur.fetchall()]


def python_exact_search(query: list[float], vectors: dict[int, list[float]],
                        k: int = 10) -> list[tuple[int, float]]:
    """Brute force in pure Python — the SAME-LANGUAGE baseline for the IVF index.

    This exists because of a result that is easy to get wrong. Compare a hand-written
    Python ANN index against sqlite-vec and the ANN index loses at every setting, because
    you are measuring C against Python and not approximate against exact. The honest
    comparison needs both baselines:

      * against Python brute force, IVF shows the ALGORITHMIC win (it looks at less data);
      * against C brute force, it usually still loses at modest N, which is the
        IMPLEMENTATION-QUALITY win and the reason "just use brute force" is good advice
        for longer than people expect.

    Report both or you will draw a confident conclusion from the wrong variable.
    """
    scored = [(i, 1.0 - dot(query, v)) for i, v in vectors.items()]
    scored.sort(key=lambda pair: pair[1])
    return scored[:k]


def recall_at_k(approximate: list[tuple[int, float]],
                exact: list[tuple[int, float]], k: int = 10) -> float:
    """Share of the true top-k the approximate index actually returned.

    This is the number an ANN index costs you, and the one nobody measures. An index that
    is ten times faster and returns 60% of the right answers is not ten times faster.
    """
    truth = {i for i, _ in exact[:k]}
    if not truth:
        return 0.0
    got = {i for i, _ in approximate[:k]}
    return len(truth & got) / len(truth)
