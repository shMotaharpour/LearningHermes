"""Tests for examples/retrieval-scale/ — Chapter 03c.

Offline and small: sqlite-vec is a pip wheel, the embedder is deterministic, and the IVF
index is pure Python. Nothing here needs PostgreSQL, GCP, or a model download — and the
things that DO need them (schema.sql, PgVectorStore, VertexEmbedder) are asserted to be
documented as unverified rather than silently trusted.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

SCALE = Path(__file__).resolve().parents[1] / "examples" / "retrieval-scale"
sys.path.insert(0, str(SCALE))

try:
    import sqlite_vec  # noqa: F401
    HAVE_SQLITE_VEC = True
except ImportError:  # pragma: no cover
    HAVE_SQLITE_VEC = False

import corpus  # noqa: E402
import embed  # noqa: E402
import store  # noqa: E402


class EmbedderTests(unittest.TestCase):
    def setUp(self):
        self.e = embed.LocalEmbedder()

    def test_dimensions_and_normalisation(self):
        v = self.e.embed(["hello world"])[0]
        self.assertEqual(len(v), embed.DIMS)
        self.assertAlmostEqual(sum(x * x for x in v), 1.0, places=6)

    def test_deterministic(self):
        self.assertEqual(self.e.embed(["same text"]), self.e.embed(["same text"]))

    def test_batching_changes_request_count_not_results(self):
        """The whole point of batching: fewer requests, identical vectors."""
        texts = [f"document {i}" for i in range(10)]
        a = embed.LocalEmbedder()
        b = embed.LocalEmbedder()
        self.assertEqual(a.embed(texts, batch_size=1), b.embed(texts, batch_size=10))
        self.assertEqual(a.usage.requests, 10)
        self.assertEqual(b.usage.requests, 1)

    def test_usage_is_accounted(self):
        self.e.embed(["one two three", "four five"])
        self.assertEqual(self.e.usage.texts, 2)
        self.assertEqual(self.e.usage.tokens, 5)
        self.assertGreater(self.e.usage.cost(per_mtok=1000.0), 0)

    def test_report_names_the_price_it_used(self):
        self.e.embed(["x"])
        self.assertIn("0.15/Mtok", self.e.usage.report(per_mtok=0.15))

    def test_storage_math(self):
        # 384 dims x 4 bytes = 1536 bytes per vector; a million is ~1.5 GB before any index.
        self.assertEqual(embed.storage_bytes(1, 384, 4), 1536)
        self.assertEqual(embed.storage_bytes(1_000_000, 384, 4), 1_536_000_000)

    def test_backend_selection(self):
        self.assertIsInstance(embed.get_embedder("local"), embed.LocalEmbedder)
        with self.assertRaises(ValueError):
            embed.get_embedder("nope")

    def test_vertex_backend_refuses_without_a_project(self):
        import os
        saved = os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
        try:
            with self.assertRaises(RuntimeError):
                embed.VertexEmbedder()
        finally:
            if saved is not None:
                os.environ["GOOGLE_CLOUD_PROJECT"] = saved


class CorpusTests(unittest.TestCase):
    def test_size_and_determinism(self):
        self.assertEqual(len(corpus.build(500)), 500)
        self.assertEqual(corpus.build(50), corpus.build(50))

    def test_topics_repeat_so_near_duplicates_exist(self):
        """A corpus of unrelated documents makes ANN recall trivially perfect."""
        texts = [t for _, t in corpus.build(200)]
        topics = [t.split(" policy")[0] for t in texts]
        self.assertLess(len(set(topics)), len(topics) / 4)


class IVFTests(unittest.TestCase):
    def setUp(self):
        self.e = embed.LocalEmbedder()
        docs = corpus.build(600)
        self.ids = [i for i, _ in docs]
        self.vectors = self.e.embed([t for _, t in docs])
        self.by_id = dict(zip(self.ids, self.vectors))
        self.index = store.IVFIndex(dims=embed.DIMS, nlist=16)
        self.index.build(self.ids, self.vectors, iterations=2)

    def test_every_vector_lands_in_exactly_one_list(self):
        assigned = [i for members in self.index.lists.values() for i in members]
        self.assertEqual(sorted(assigned), sorted(self.ids))

    def test_build_time_is_recorded(self):
        self.assertGreater(self.index.build_seconds, 0)

    def test_more_probes_never_reduces_recall(self):
        """The knob has to be monotone, or it is not a knob."""
        query = self.e.embed(["what does the incident response procedure require"])[0]
        truth = store.python_exact_search(query, self.by_id, 10)
        recalls = [store.recall_at_k(self.index.search(query, 10, nprobe=n), truth, 10)
                   for n in (1, 2, 4, 8, 16)]
        self.assertEqual(recalls, sorted(recalls))
        self.assertAlmostEqual(recalls[-1], 1.0)  # probing every list is exact

    def test_probing_every_list_is_exhaustive(self):
        self.assertAlmostEqual(self.index.probed_fraction(self.index.nlist), 1.0, places=6)

    def test_fewer_probes_looks_at_less_of_the_corpus(self):
        self.assertLess(self.index.probed_fraction(1), self.index.probed_fraction(8))

    def test_search_returns_at_most_k(self):
        query = self.e.embed(["anything"])[0]
        self.assertLessEqual(len(self.index.search(query, k=5, nprobe=2)), 5)


class RecallTests(unittest.TestCase):
    def test_perfect_and_zero_and_partial(self):
        exact = [(1, 0.1), (2, 0.2), (3, 0.3), (4, 0.4)]
        self.assertEqual(store.recall_at_k(exact, exact, 4), 1.0)
        self.assertEqual(store.recall_at_k([(9, 0.1)], exact, 4), 0.0)
        self.assertEqual(store.recall_at_k([(1, 0.1), (2, 0.2)], exact, 4), 0.5)

    def test_empty_truth_is_zero_not_a_crash(self):
        self.assertEqual(store.recall_at_k([(1, 0.1)], [], 10), 0.0)

    def test_order_within_k_does_not_matter(self):
        exact = [(1, 0.1), (2, 0.2)]
        self.assertEqual(store.recall_at_k([(2, 0.2), (1, 0.1)], exact, 2), 1.0)


class PythonExactTests(unittest.TestCase):
    def test_returns_the_true_nearest(self):
        e = embed.LocalEmbedder()
        texts = ["incident response policy", "budget approval policy", "backup rotation"]
        vectors = e.embed(texts)
        by_id = dict(enumerate(vectors))
        hits = store.python_exact_search(vectors[0], by_id, 1)
        self.assertEqual(hits[0][0], 0)  # a vector is nearest to itself


@unittest.skipUnless(HAVE_SQLITE_VEC, "sqlite-vec not installed")
class SqliteVecTests(unittest.TestCase):
    def setUp(self):
        self.e = embed.LocalEmbedder()
        docs = corpus.build(400)
        self.ids = [i for i, _ in docs]
        self.vectors = self.e.embed([t for _, t in docs])
        self.s = store.SqliteVecStore(embed.DIMS)
        self.s.add(self.ids, self.vectors)

    def test_all_rows_stored(self):
        self.assertEqual(self.s.count(), 400)

    def test_knn_returns_k_ordered_by_distance(self):
        hits = self.s.search(self.vectors[0], k=5)
        self.assertEqual(len(hits), 5)
        self.assertEqual([d for _, d in hits], sorted(d for _, d in hits))

    def test_a_vector_is_its_own_nearest_neighbour(self):
        self.assertEqual(self.s.search(self.vectors[7], k=1)[0][0], 7)

    def test_c_and_python_exact_search_agree(self):
        """Two implementations of the same definition must return the same answer."""
        by_id = dict(zip(self.ids, self.vectors))
        query = self.e.embed(["what does the data retention procedure require"])[0]
        c_hits = {i for i, _ in self.s.search(query, k=10)}
        py_hits = {i for i, _ in store.python_exact_search(query, by_id, 10)}
        self.assertEqual(c_hits, py_hits)


class UnverifiedSurfacesTests(unittest.TestCase):
    """What this repo CANNOT test must say so, in the file itself."""

    def test_schema_declares_that_it_is_not_executed_here(self):
        text = (SCALE / "schema.sql").read_text(encoding="utf-8")
        self.assertIn("NOT executed by this repo's tests", text)
        self.assertIn("CREATE EXTENSION IF NOT EXISTS vector", text)

    def test_schema_documents_both_index_families(self):
        text = (SCALE / "schema.sql").read_text(encoding="utf-8").lower()
        for knob in ("ivfflat", "hnsw", "lists", "probes", "ef_search"):
            self.assertIn(knob, text)

    def test_vertex_embedder_is_marked_unverified(self):
        text = (SCALE / "embed.py").read_text(encoding="utf-8")
        self.assertIn("Not exercised by this repo's tests", text)

    def test_readme_states_the_limits(self):
        text = (SCALE / "README.md").read_text(encoding="utf-8")
        self.assertIn("not semantic", text)
        self.assertIn("verified by you, not by this repo", text)


if __name__ == "__main__":
    unittest.main()
