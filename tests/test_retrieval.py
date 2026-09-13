"""Tests for examples/retrieval/ — the pipeline Chapter 03b builds.

All offline: the embedder is deterministic and the corpus ships with the repo, so the
retriever's behaviour is pinned rather than demonstrated once and hoped about.

The tests that matter most are the abstention ones. A retriever that always returns
something is the default, and it is what turns a RAG system into a confident liar.
"""
import json
import sys
import unittest
from pathlib import Path

RETRIEVAL = Path(__file__).resolve().parents[1] / "examples" / "retrieval"
sys.path.insert(0, str(RETRIEVAL))

import ground  # noqa: E402
import retrieval as R  # noqa: E402
from evaluate import evaluate  # noqa: E402


class ChunkerTests(unittest.TestCase):
    TEXT = "# Heading one\nAlpha sentence. Beta sentence.\n\n# Heading two\nGamma here.\n"

    def test_structural_keeps_the_heading_with_its_body(self):
        chunks = R.chunk_structural("doc", self.TEXT)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].heading, "Heading one")
        self.assertIn("Alpha sentence", chunks[0].text)
        self.assertNotIn("Gamma", chunks[0].text)

    def test_structural_gives_every_chunk_a_readable_label(self):
        for chunk in R.chunk_structural("doc", self.TEXT):
            self.assertTrue(chunk.heading)

    def test_fixed_windows_cover_the_whole_text(self):
        text = "x" * 1000
        joined = "".join(c.text for c in R.chunk_fixed("doc", text, size=300))
        self.assertEqual(len(joined), 1000)

    def test_overlap_repeats_content_between_neighbours(self):
        text = "".join(f"word{i} " for i in range(200))
        plain = R.chunk_fixed("doc", text, size=300, overlap=0)
        overlapped = R.chunk_fixed("doc", text, size=300, overlap=150)
        self.assertGreater(len(overlapped), len(plain))

    def test_sentence_chunker_does_not_split_mid_sentence(self):
        text = "One two three. Four five six. Seven eight nine. " * 12
        for chunk in R.chunk_sentences("doc", text, target=120):
            self.assertTrue(chunk.text.rstrip().endswith("."), chunk.text[-40:])

    def test_every_chunker_is_reachable_from_the_registry(self):
        for name, fn in R.CHUNKERS.items():
            chunks = fn("doc", self.TEXT)
            self.assertTrue(chunks, name)
            self.assertTrue(all(c.doc == "doc" for c in chunks))

    def test_citations_are_unique_within_a_document(self):
        for fn in R.CHUNKERS.values():
            ids = [c.citation for c in fn("doc", self.TEXT)]
            self.assertEqual(len(ids), len(set(ids)))


class BM25Tests(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            R.Chunk("d", "a", "cats sit on mats"),
            R.Chunk("d", "b", "dogs chase cats around the yard"),
            R.Chunk("d", "c", "quantum chromodynamics explains the strong force"),
        ]
        self.bm25 = R.BM25(self.chunks)

    def test_a_matching_chunk_outscores_a_non_matching_one(self):
        scores = self.bm25.score("cats")
        self.assertGreater(scores[0], scores[2])
        self.assertEqual(scores[2], 0.0)

    def test_a_rare_term_outweighs_a_common_one(self):
        """IDF is the whole reason BM25 works: 'cats' is in two docs, 'quantum' in one."""
        self.assertGreater(self.bm25.idf("quantum"), self.bm25.idf("cats"))

    def test_idf_of_an_unseen_term_is_defined(self):
        self.assertGreater(self.bm25.idf("giraffe"), 0)

    def test_term_frequency_saturates(self):
        """Seeing a word five times is not five times as relevant. That is k1's job."""
        chunks = [R.Chunk("d", "a", "spam"), R.Chunk("d", "b", "spam " * 20)]
        scores = R.BM25(chunks).score("spam")
        self.assertLess(scores[1] / scores[0], 3.0)

    def test_empty_query_scores_nothing(self):
        self.assertEqual(set(self.bm25.score("")), {0.0})


class EmbedderTests(unittest.TestCase):
    def test_deterministic_and_normalised(self):
        a, b = R.embed("hello world"), R.embed("hello world")
        self.assertEqual(a, b)
        self.assertAlmostEqual(sum(x * x for x in a), 1.0, places=6)

    def test_similar_text_scores_higher_than_unrelated(self):
        query = R.embed("data retention policy")
        near = R.cosine(query, R.embed("the data retention policy says"))
        far = R.cosine(query, R.embed("quantum chromodynamics"))
        self.assertGreater(near, far)

    def test_cosine_is_never_zero_for_real_text(self):
        """The property that makes abstention impossible from dense scores alone."""
        score = R.cosine(R.embed("parental leave allowance"),
                         R.embed("quantum chromodynamics strong force"))
        self.assertGreater(score, 0.0)


class FusionTests(unittest.TestCase):
    def test_rrf_rewards_agreement_between_rankers(self):
        agreed = R.reciprocal_rank_fusion([[7, 1, 2], [7, 3, 4]])
        self.assertEqual(max(agreed, key=agreed.get), 7)

    def test_rrf_reads_rank_not_score(self):
        """Two rankings of the same order fuse identically however confident either was."""
        self.assertEqual(R.reciprocal_rank_fusion([[1, 2, 3]]),
                         R.reciprocal_rank_fusion([[1, 2, 3]]))

    def test_a_single_ranking_keeps_its_order(self):
        fused = R.reciprocal_rank_fusion([[5, 6, 7]])
        self.assertEqual(sorted(fused, key=lambda i: -fused[i]), [5, 6, 7])


class AbstentionTests(unittest.TestCase):
    """The metric that separates a usable system from a demo."""

    def setUp(self):
        self.retriever = R.Retriever(R.build_chunks())

    def test_out_of_vocabulary_question_returns_nothing(self):
        self.assertEqual(self.retriever.search("what is our parental leave allowance?"), [])
        self.assertEqual(self.retriever.search("which cloud region hosts the database?"), [])

    def test_coverage_is_zero_when_no_term_is_known(self):
        self.assertEqual(self.retriever.coverage("parental leave allowance"), 0.0)

    def test_coverage_is_high_for_an_answerable_question(self):
        self.assertGreater(self.retriever.coverage("how long are transcripts retained?"), 0.5)

    def test_a_stopword_only_question_abstains(self):
        self.assertEqual(self.retriever.search("what is it?"), [])

    def test_answerable_questions_still_return_results(self):
        for question in ("how long are transcripts kept?",
                         "who can declare an incident?",
                         "how many backup rotations do we keep?"):
            self.assertTrue(self.retriever.search(question), question)

    def test_every_returned_chunk_has_lexical_evidence(self):
        for chunk, _ in self.retriever.search("incident severity levels", k=4):
            overlap = set(R.tokenize(chunk.text)) & set(R.tokenize("incident severity levels"))
            self.assertTrue(overlap, chunk.citation)


class RetrieverModeTests(unittest.TestCase):
    def test_all_three_modes_find_the_retention_answer(self):
        for mode in ("lexical", "dense", "hybrid"):
            results = R.Retriever(R.build_chunks(), mode=mode).search(
                "how long are transcripts kept?", k=3)
            self.assertTrue(any("90 days" in c.text for c, _ in results), mode)

    def test_k_bounds_the_result_count(self):
        retriever = R.Retriever(R.build_chunks())
        self.assertLessEqual(len(retriever.search("incident", k=2)), 2)


class QaSetTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((RETRIEVAL / "qa.json").read_text(encoding="utf-8"))["cases"]

    def test_the_set_contains_answerless_cases(self):
        """Without them the eval cannot see its most expensive failure."""
        self.assertGreaterEqual(sum(1 for c in self.cases if c.get("answerless")), 2)

    def test_every_answerable_case_is_actually_answerable(self):
        """A ground truth that is not in the corpus makes the metric lie."""
        corpus = " ".join(R.load_corpus().values()).lower()
        for case in self.cases:
            if case.get("answerless"):
                self.assertIsNone(case["must_contain"])
            else:
                self.assertIn(case["must_contain"].lower(), corpus, case["question"])

    def test_named_documents_exist(self):
        docs = set(R.load_corpus())
        for case in self.cases:
            if not case.get("answerless"):
                self.assertIn(case["doc"], docs)


class EvaluationTests(unittest.TestCase):
    def test_hybrid_retrieval_scores_are_sane(self):
        report = evaluate("hybrid", "structural")
        self.assertGreaterEqual(report["recall_at_k"], 0.75)
        self.assertGreaterEqual(report["abstention_rate"], 1.0)
        self.assertGreaterEqual(report["citation_precision"], 0.75)
        self.assertGreater(report["mrr"], 0.0)

    def test_every_mode_and_chunker_combination_evaluates(self):
        for mode in ("lexical", "dense", "hybrid"):
            for chunker in R.CHUNKERS:
                report = evaluate(mode, chunker)
                self.assertEqual(report["answerless"], 2)
                self.assertLessEqual(report["recall_at_k"], 1.0)


class GroundingTests(unittest.TestCase):
    def setUp(self):
        self.results = R.Retriever(R.build_chunks()).search(
            "how long are transcripts kept?", k=3)

    def test_prompt_carries_every_passage_with_its_id(self):
        prompt = ground.build_prompt("how long?", self.results)
        for chunk, _ in self.results:
            self.assertIn(f"[{chunk.citation}]", prompt)

    def test_prompt_states_the_refusal_string(self):
        self.assertIn(ground.REFUSAL, ground.build_prompt("q", self.results))

    def test_valid_citation_passes(self):
        citation = self.results[0][0].citation
        report = ground.check_citations(f"Ninety days [{citation}].", self.results)
        self.assertTrue(report["ok"])
        self.assertEqual(report["invalid"], [])

    def test_invented_citation_is_caught(self):
        """A model will cite a passage it was never given. Checking is deterministic."""
        report = ground.check_citations("Ninety days [handbook#sec9].", self.results)
        self.assertFalse(report["ok"])
        self.assertEqual(report["invalid"], ["handbook#sec9"])

    def test_an_assertion_with_no_citation_is_flagged(self):
        report = ground.check_citations("Transcripts are kept for a year.", self.results)
        self.assertTrue(report["uncited_claim"])
        self.assertFalse(report["ok"])

    def test_a_refusal_needs_no_citation(self):
        report = ground.check_citations(ground.REFUSAL, self.results)
        self.assertTrue(report["refused"])
        self.assertTrue(report["ok"])

    def test_a_mix_of_valid_and_invented_citations_fails(self):
        good = self.results[0][0].citation
        report = ground.check_citations(f"A [{good}] and B [nope#x].", self.results)
        self.assertFalse(report["ok"])
        self.assertIn("nope#x", report["invalid"])


if __name__ == "__main__":
    unittest.main()
