#!/usr/bin/env python3
"""A synthetic corpus with enough structure to be worth retrieving from. Chapter 03c."""
from __future__ import annotations

import random

TOPICS = [
    "incident response", "data retention", "engineer onboarding", "model cost policy",
    "access review", "backup rotation", "release process", "on-call rotation",
    "vendor assessment", "capacity planning", "privacy review", "key rotation",
    "disaster recovery", "change management", "security training", "budget approval",
]
VERBS = ["requires", "prohibits", "recommends", "documents", "schedules", "audits"]
OBJECTS = ["a written approval", "an owner and an expiry date", "a quarterly review",
           "a postmortem within five days", "an automated check", "a named deputy"]


def build(count: int, seed: int = 0) -> list[tuple[int, str]]:
    """(id, text) pairs. Topics repeat so near-duplicates exist — which is what makes an
    approximate index's recall interesting rather than trivially perfect."""
    rng = random.Random(seed)
    docs = []
    for i in range(count):
        topic = TOPICS[i % len(TOPICS)]
        docs.append((i, f"{topic} policy section {i // len(TOPICS)}: the {topic} procedure "
                        f"{rng.choice(VERBS)} {rng.choice(OBJECTS)} before it is considered "
                        f"complete, and names {rng.choice(OBJECTS)} as the fallback."))
    return docs


def queries(count: int, seed: int = 1) -> list[str]:
    rng = random.Random(seed)
    return [f"what does the {rng.choice(TOPICS)} procedure require" for _ in range(count)]
