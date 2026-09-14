#!/usr/bin/env python3
"""Embedding with the two things that matter at scale: batching, and cost. Chapter 03c.

Chapter 03b built a retriever from its parts with a deliberately weak embedder. This module
is the seam where a real model goes, and the point is that **the engineering around the
embedder does not change when you swap it**. Batch size, dimensionality, throughput and
cost behave the same whether the vectors come from a hashing trick or from Vertex AI.

Two backends:

* ``LocalEmbedder`` — deterministic, standard library, runs anywhere and in CI. Not
  semantic, and this module never pretends otherwise.
* ``VertexEmbedder`` — the real one, against Vertex AI's text-embedding endpoint. It needs
  your own GCP project and credentials, so it is *structurally* documented here and
  verified by you, not by this repo. The chapter says so rather than implying a test ran.

The rule this file exists to make concrete: an embedding backend is an interface with a
price attached. Treat it like any other paid dependency — batch it, measure it, and know
what a re-embed of the whole corpus costs before you need one.
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
    — batching, index build, recall measurement — can be tested offline and in CI. Swap it
    for VertexEmbedder and nothing downstream changes, which is the design claim.
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


class VertexEmbedder:
    """Vertex AI text embeddings. Requires YOUR GCP project and credentials.

        pip install google-cloud-aiplatform
        gcloud auth application-default login
        EMBED_BACKEND=vertex GOOGLE_CLOUD_PROJECT=... python3 bench.py

    Not exercised by this repo's tests — no GCP project is available to them — so treat the
    call shape as documented-and-unverified and confirm it against the current Vertex AI
    reference before relying on it. That distinction is the whole reason this chapter
    carries a different evidence header from the rest of the course.

    Three things here are the actual lesson, and all three survive any provider change:

    1. **Batch.** Per-text requests pay round-trip latency per text. The API takes a list;
       use it. Batch size is bounded by the provider's per-request limits, not by taste.
    2. **Retry the whole batch, not the corpus.** A failed batch at document 40,000 should
       cost you that batch.
    3. **Record usage.** A re-embed of the corpus is a purchase, and you should be able to
       price it before someone asks.
    """

    name = "vertex"

    def __init__(self, model: str = "text-embedding-005", dims: int = DIMS):
        self.model, self.dims, self.usage = model, dims, Usage()
        self.project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not self.project:
            raise RuntimeError("set GOOGLE_CLOUD_PROJECT to use the Vertex backend")

    def embed(self, texts: list[str], batch_size: int = 128) -> list[list[float]]:
        try:
            from vertexai.language_models import TextEmbeddingModel
        except ImportError as exc:  # pragma: no cover - needs the optional dependency
            raise RuntimeError(
                "pip install google-cloud-aiplatform, then "
                "gcloud auth application-default login"
            ) from exc
        model = TextEmbeddingModel.from_pretrained(self.model)
        out: list[list[float]] = []
        started = time.monotonic()
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            self.usage.requests += 1
            for embedding in model.get_embeddings(batch):
                out.append(list(embedding.values))
                self.usage.tokens += 0  # provider reports this; see its response metadata
            self.usage.texts += len(batch)
        self.usage.seconds += time.monotonic() - started
        return out


def get_embedder(backend: str | None = None):
    backend = backend or os.environ.get("EMBED_BACKEND", "local")
    if backend == "vertex":
        return VertexEmbedder()
    if backend == "local":
        return LocalEmbedder()
    raise ValueError(f"unknown embedding backend: {backend!r}")


def storage_bytes(count: int, dims: int = DIMS, bytes_per_value: int = 4) -> int:
    """Raw vector storage. The number people are surprised by.

    float32 at 384 dims is 1,536 bytes per vector before any index, id, or payload. A
    million documents is ~1.5 GB of vectors alone — which is the argument for caring about
    dimensionality, and for knowing whether your store keeps the index in memory.
    """
    return count * dims * bytes_per_value
