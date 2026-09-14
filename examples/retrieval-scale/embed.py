#!/usr/bin/env python3
"""Embedding with the three things that matter at scale: batching, dimensions, and cost.

Chapter 03c. Chapter 03b built a retriever from its parts with a deliberately weak
embedder. This module is the seam where a real model goes, and most of the engineering
around it — usage accounting, retry granularity, cost-per-corpus — is unchanged by the
swap. Two things are NOT, and both are documented below rather than glossed over:
dimensionality, and how many texts fit in one request.

Two backends:

* ``LocalEmbedder`` — deterministic, standard library, runs anywhere and in CI. Not
  semantic, and this module never pretends otherwise.
* ``GeminiEmbedder`` — the real one, against Google's text-embedding endpoint. It needs
  your own GCP project and credentials, so it is *structurally* documented here and
  verified by you, not by this repo. The chapter says so rather than implying a test ran.

The rule this file exists to make concrete: an embedding backend is an interface with a
price and a set of provider limits attached. Treat it like any other paid dependency —
measure it, and know what a re-embed of the whole corpus costs before you need one.

A note on the class name. It used to be ``VertexEmbedder``, after the product. The product
was renamed (Vertex AI became the Gemini Enterprise Agent Platform in April 2026) and the
name in this file became wrong without a single line of behaviour changing. That is the
argument for naming a class after the durable thing — here the model family — rather than
the vendor's current marketing. ``VertexEmbedder`` survives as an alias at the bottom,
which is the other half of the same lesson: you do not get to break your callers because
someone else rebranded.
"""
from __future__ import annotations

import hashlib
import math
import os
import re
import time
from dataclasses import dataclass, field

DIMS = 384  # matches the common small open models; storage math below assumes float32
WORD = re.compile(r"[a-z0-9]+")


@dataclass
class Usage:
    """What the embedder spent. The reason this is a class and not a counter: at scale the
    interesting number is not the total, it is the total per batch size."""

    texts: int = 0
    tokens: int = 0          # approximate: whitespace tokens, good enough for a budget
    seconds: float = 0.0
    requests: int = 0

    def cost(self, per_mtok: float) -> float:
        return self.tokens / 1_000_000 * per_mtok

    def report(self, per_mtok: float | None = None) -> str:
        rate = self.texts / self.seconds if self.seconds else 0
        line = (f"{self.texts:,} texts in {self.requests:,} requests, "
                f"{self.tokens:,} tokens, {self.seconds:.2f}s ({rate:,.0f} texts/s)")
        if per_mtok is not None:
            line += f", ~{self.cost(per_mtok):.4f} at {per_mtok}/Mtok"
        return line


class LocalEmbedder:
    """Deterministic character-trigram hashing into DIMS, L2-normalised.

    Runs anywhere, needs nothing, and is NOT semantic. It is here so the scale engineering
    — batching, index build, recall measurement — can be tested offline and in CI.

    DIMS is 384, which is a small-open-model size and is NOT one of the sizes Google
    recommends for gemini-embedding-001 (768, 1536, 3072). That mismatch is deliberate and
    is the point: swapping embedders changes the vector width, and changing the vector
    width means re-embedding the corpus and rebuilding every index. An embedder is not a
    drop-in dependency, and anyone who tells you the swap is free has never done one on a
    corpus that costs money to re-embed.
    """

    name = "local-hash"
    dims = DIMS

    def __init__(self):
        self.usage = Usage()

    def embed(self, texts: list[str], batch_size: int = 256) -> list[list[float]]:
        out: list[list[float]] = []
        started = time.monotonic()
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            self.usage.requests += 1
            for text in batch:
                out.append(self._one(text))
                self.usage.tokens += len(text.split())
            self.usage.texts += len(batch)
        self.usage.seconds += time.monotonic() - started
        return out

    def _one(self, text: str) -> list[float]:
        vector = [0.0] * self.dims
        normalized = " ".join(WORD.findall(text.lower()))
        for i in range(max(1, len(normalized) - 2)):
            gram = normalized[i:i + 3]
            slot = int(hashlib.md5(gram.encode()).hexdigest(), 16) % self.dims
            vector[slot] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class GeminiEmbedder:
    """Google text embeddings via the Gen AI SDK. Requires YOUR GCP project and credentials.

        pip install google-genai                  # NOT google-cloud-aiplatform
        gcloud auth application-default login
        EMBED_BACKEND=gemini GOOGLE_CLOUD_PROJECT=... python3 bench.py

    Not exercised by this repo's tests — no GCP project is available to them — so treat the
    call shape as documented-and-unverified and confirm it against the current reference
    before relying on it. That distinction is the whole reason this chapter carries a
    different evidence header from the rest of the course. The names and limits below come
    from `docs/research/google/ai-stack-2026-09-14.md`, which is dated research, not a run.

    This class was rewritten once already. The previous version called
    `vertexai.language_models.TextEmbeddingModel`, which Google deprecated in June 2025 and
    removes in June 2026 — so code that worked when it was written stops importing on a
    date somebody else picked. Two habits follow, and they are the transferable part:
    **pin the SDK**, and **read the deprecation page of any vendor library you depend on**,
    because the removal date is published long before it bites.

    Four things are the actual lesson:

    1. **The per-request limit is the provider's, not yours.** `text-embedding-005` took up
       to 250 segments per call. `gemini-embedding-001` takes exactly ONE — for throughput
       you use the asynchronous Batch API instead. So this backend cannot honour a
       `batch_size` above 1, and it **refuses** one rather than accepting the argument and
       ignoring it. A parameter that is silently dropped is how you end up with a capacity
       plan built on a batch size that never existed; `Usage.requests` will equal
       `Usage.texts` here, and that is the real number. Notice what it does to a corpus of
       a million documents: the round-trip count, not the token bill, becomes the
       constraint. Never assume a batch limit carries across models in the same family —
       this one does not even carry across two models from the same vendor.
    2. **Dimensions are a choice with a storage bill.** `gemini-embedding-001` returns 3072
       dimensions by default and truncates cleanly (Matryoshka) to 1536 or 768. At float32
       that is 12 KB, 6 KB or 3 KB per vector — see `storage_bytes`. Pick the smallest
       width that holds your recall, and measure recall to find out which that is
       (`evaluate.py`); do not take the default because it is the default.
    3. **Retry the unit, not the corpus.** A failure at document 40,000 should cost you
       document 40,000.
    4. **Record usage.** A re-embed of the corpus is a purchase, and you should be able to
       price it before someone asks. At list price (2026-09) this model is about $0.15 per
       million input tokens, halved on the Batch API, with a 2,048-token cap per text.
    """

    name = "gemini"

    def __init__(
        self,
        model: str = "gemini-embedding-001",
        dims: int = 768,
        location: str = "us-central1",
    ):
        self.model, self.dims, self.usage = model, dims, Usage()
        self.location = location
        self.project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not self.project:
            raise RuntimeError("set GOOGLE_CLOUD_PROJECT to use the Gemini backend")

    def embed(self, texts: list[str], batch_size: int = 1) -> list[list[float]]:
        """One request per text. `batch_size` exists only for interface parity with
        LocalEmbedder, and anything above 1 is refused rather than quietly ignored."""
        if batch_size != 1:
            raise ValueError(
                f"{self.model} accepts one text per request; batch_size={batch_size} "
                "cannot be honoured. Use the asynchronous Batch API for bulk throughput."
            )
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - needs the optional dependency
            raise RuntimeError(
                "pip install google-genai, then gcloud auth application-default login"
            ) from exc
        client = genai.Client(
            vertexai=True, project=self.project, location=self.location
        )
        config = types.EmbedContentConfig(output_dimensionality=self.dims)
        out: list[list[float]] = []
        started = time.monotonic()
        for text in texts:
            result = client.models.embed_content(
                model=self.model, contents=text, config=config
            )
            out.append(list(result.embeddings[0].values))
            self.usage.requests += 1
            self.usage.texts += 1
            self.usage.tokens += len(text.split())  # provider reports the real count
        self.usage.seconds += time.monotonic() - started
        return out


# The old name, kept working. A rebrand upstream is not a reason to break your callers —
# and leaving the alias in is cheaper than the pull request that renames it everywhere.
VertexEmbedder = GeminiEmbedder


def get_embedder(backend: str | None = None):
    backend = backend or os.environ.get("EMBED_BACKEND", "local")
    if backend in ("gemini", "vertex"):  # "vertex" accepted: old name, same backend
        return GeminiEmbedder()
    if backend == "local":
        return LocalEmbedder()
    raise ValueError(f"unknown embedding backend: {backend!r}")


def storage_bytes(count: int, dims: int = DIMS, bytes_per_value: int = 4) -> int:
    """Raw vector storage. The number people are surprised by.

    float32 at 384 dims is 1,536 bytes per vector before any index, id, or payload. A
    million documents is ~1.5 GB of vectors alone — which is the argument for caring about
    dimensionality, and for knowing whether your store keeps the index in memory.

    Run the same million at gemini-embedding-001's default 3,072 dimensions and it is
    ~12 GB. That is the whole argument for Matryoshka truncation in one line: the default
    width costs eight times the storage of a 384-dim vector, and whether it buys you eight
    times anything is a recall question you can answer (`evaluate.py`) before you pay it.
    """
    return count * dims * bytes_per_value
