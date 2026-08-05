"""Redis-backed daily diagnosis quota and the code_hash diagnosis cache.

Cached diagnoses do not consume quota: a resubmitted identical attempt costs nothing to
serve, so charging for it would only punish users for re-reading their own result.
"""

from __future__ import annotations

import datetime as dt
import logging

import redis

from .config import get_settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    global _client
    if _client is None:
        try:
            _client = redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
            _client.ping()
        except Exception:
            logger.warning("redis unavailable; rate limiting is disabled")
            return None
    return _client


def _quota_key(user_id: str) -> str:
    today = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    return f"weakspot:quota:{user_id}:{today}"


def remaining_quota(user_id: str) -> int:
    settings = get_settings()
    client = get_redis()
    if client is None:
        return settings.free_diagnoses_per_day
    used = int(client.get(_quota_key(user_id)) or 0)
    return max(0, settings.free_diagnoses_per_day - used)


def consume_quota(user_id: str) -> bool:
    """Increment and report whether the request is allowed. Fails open if Redis is down."""
    settings = get_settings()
    client = get_redis()
    if client is None:
        return True

    key = _quota_key(user_id)
    pipe = client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60 * 60 * 26)  # comfortably past the UTC day boundary
    used, _ = pipe.execute()
    return int(used) <= settings.free_diagnoses_per_day


def refund_quota(user_id: str) -> None:
    """Give the quota back when a diagnosis failed before any model call."""
    client = get_redis()
    if client is not None:
        client.decr(_quota_key(user_id))


def ping() -> bool:
    client = get_redis()
    if client is None:
        return False
    try:
        client.ping()
        return True
    except Exception:
        return False
