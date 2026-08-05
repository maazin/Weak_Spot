"""Voyage embeddings.

voyage-3 emits exactly 1024 dimensions, which is what `problems.embedding` and
`patterns.embedding` are declared as — no truncation or padding anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import voyageai

from .config import get_settings

BATCH_SIZE = 128


class EmbeddingError(RuntimeError):
    pass


@dataclass
class _Client:
    _client: voyageai.Client | None = field(default=None, repr=False)

    def get(self) -> voyageai.Client:
        if self._client is None:
            settings = get_settings()
            if not settings.voyage_api_key:
                raise EmbeddingError("VOYAGE_API_KEY is not set; cannot embed")
            self._client = voyageai.Client(api_key=settings.voyage_api_key)
        return self._client


_shared = _Client()


def embed(texts: list[str], *, input_type: str = "document") -> list[list[float]]:
    """Embed in batches. `input_type` is 'document' for indexing, 'query' for search."""
    if not texts:
        return []

    settings = get_settings()
    client = _shared.get()
    out: list[list[float]] = []

    for start in range(0, len(texts), BATCH_SIZE):
        chunk = texts[start : start + BATCH_SIZE]
        result = client.embed(chunk, model=settings.embedding_model, input_type=input_type)
        out.extend(result.embeddings)

    for vec in out:
        if len(vec) != settings.embedding_dim:
            raise EmbeddingError(f"expected {settings.embedding_dim}-dim vectors, got {len(vec)}")
    return out


def embed_one(text: str, *, input_type: str = "query") -> list[float]:
    return embed([text], input_type=input_type)[0]


def problem_embedding_text(title: str, tags: list[str], difficulty: str) -> str:
    """Only metadata is ever embedded — never a problem statement.

    Keeping this in one function means the legal constraint has a single place it
    could be violated, and a single place to review.
    """
    return f"{title}. Difficulty: {difficulty}. Topics: {', '.join(tags)}."


def pattern_embedding_text(name: str, correct_approach: str, practice_tags: list[str]) -> str:
    return f"{name}. {correct_approach} Topics: {', '.join(practice_tags)}."
