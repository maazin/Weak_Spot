"""Voyage embeddings.

voyage-3 emits exactly 1024 dimensions, which is what `problems.embedding` and
`patterns.embedding` are declared as — no truncation or padding anywhere.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import voyageai

from .config import get_settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 128

# A Voyage account with no payment method is capped at 3 requests/minute. The seed run
# is only a handful of requests, so waiting is cheaper and simpler than asking everyone
# to put a card on file — but it has to be bounded, or a genuinely exhausted quota looks
# like a hang.
RATE_LIMIT_RETRIES = 5
RATE_LIMIT_BACKOFF_SECONDS = 25


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


def _embed_chunk(
    client: voyageai.Client, chunk: list[str], model: str, input_type: str
) -> list[list[float]]:
    """One request, retried on rate limits.

    Voyage's rate-limit error is the only one worth retrying — it clears on its own.
    Anything else (bad key, unknown model, malformed input) will fail identically on a
    second attempt, so it is raised immediately rather than slept over.
    """
    for attempt in range(RATE_LIMIT_RETRIES):
        try:
            return client.embed(chunk, model=model, input_type=input_type).embeddings
        except voyageai.error.RateLimitError:
            if attempt == RATE_LIMIT_RETRIES - 1:
                raise EmbeddingError(
                    f"Voyage rate limit persisted after {RATE_LIMIT_RETRIES} attempts. "
                    "Free accounts are capped at 3 requests/minute; add a payment method "
                    "at https://dashboard.voyageai.com to lift it."
                ) from None
            wait = RATE_LIMIT_BACKOFF_SECONDS * (attempt + 1)
            logger.warning("voyage rate limited; retrying in %ds", wait)
            time.sleep(wait)
    raise AssertionError("unreachable")


def embed(texts: list[str], *, input_type: str = "document") -> list[list[float]]:
    """Embed in batches. `input_type` is 'document' for indexing, 'query' for search."""
    if not texts:
        return []

    settings = get_settings()
    client = _shared.get()
    out: list[list[float]] = []

    for start in range(0, len(texts), BATCH_SIZE):
        chunk = texts[start : start + BATCH_SIZE]
        result = _embed_chunk(client, chunk, settings.embedding_model, input_type)
        out.extend(result)

    for vec in out:
        if len(vec) != settings.embedding_dim:
            raise EmbeddingError(f"expected {settings.embedding_dim}-dim vectors, got {len(vec)}")
    return out


def problem_embedding_text(title: str, tags: list[str], difficulty: str) -> str:
    """Only metadata is ever embedded — never a problem statement.

    Keeping this in one function means the legal constraint has a single place it
    could be violated, and a single place to review.
    """
    return f"{title}. Difficulty: {difficulty}. Topics: {', '.join(tags)}."


def pattern_embedding_text(name: str, correct_approach: str, practice_tags: list[str]) -> str:
    """Tags only — deliberately narrower than it looks.

    This string is compared by cosine against `problem_embedding_text`, which is about
    ten words of metadata. Feeding a whole `correct_approach` paragraph in here made the
    two sides different *kinds* of text, and similarity started tracking length and
    register as much as subject. Tags are the one vocabulary both sides genuinely share:
    problem statements are copyrighted, so a problem's embedding never sees more than
    its title, difficulty and tags.

    Dropping the prose lifted vector-arm precision@3 from 0.348 to 0.420 on Suite C.
    `name` and `correct_approach` stay in the signature because they are the natural
    inputs to this question, and a future embedding model may make them worth including
    again — but on the current evidence they hurt.
    """
    return f"Topics: {', '.join(practice_tags)}."
