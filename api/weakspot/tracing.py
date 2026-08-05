"""Langfuse tracing — one trace per submission, one span per graph node.

Degrades to a no-op when Langfuse is not configured, so local development and CI do not
need credentials and no call site has to guard on availability.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

from .config import get_settings

logger = logging.getLogger(__name__)

_client: Any = None
_initialised = False


def get_client() -> Any:
    global _client, _initialised
    if _initialised:
        return _client
    _initialised = True

    settings = get_settings()
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None
    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception:
        logger.warning("Langfuse unavailable; tracing disabled")
        _client = None
    return _client


class _NullTrace:
    id = None

    def span(self, **_: Any) -> _NullTrace:
        return self

    def update(self, **_: Any) -> None:
        return None

    def end(self, **_: Any) -> None:
        return None


@contextmanager
def trace_submission(submission_id: str, user_id: str):
    client = get_client()
    if client is None:
        yield _NullTrace()
        return

    trace = client.trace(
        name="diagnosis",
        id=submission_id,
        user_id=user_id,
        metadata={"submission_id": submission_id},
    )
    try:
        yield trace
    finally:
        try:
            client.flush()
        except Exception:
            pass


def tag_trace(trace: Any, final_state: dict) -> None:
    """Tag with pattern_id, model_tier, verifier_passed, retry_count (spec section 9)."""
    if trace is None or isinstance(trace, _NullTrace):
        return
    try:
        trace.update(
            metadata={
                "pattern_id": final_state.get("pattern_id"),
                "model_tier": final_state.get("model_tier"),
                "verifier_passed": final_state.get("verifier_passed"),
                "retry_count": final_state.get("retry_count", 0),
                "cost_usd": final_state.get("cost_usd"),
                "latency_ms": final_state.get("latency_ms"),
            }
        )
    except Exception:
        pass


def trace_id_of(trace: Any) -> str | None:
    return getattr(trace, "id", None)
