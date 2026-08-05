"""`scheduler` — SM-2 with the reduced parameter set from spec section 5.

Initial interval 3 days. On a successful review `interval *= ease`; on failure the
interval resets to 1 day and `ease` drops by 0.2, floored at 1.3. A skip is deliberately
not a failure: it moves the item without touching `ease`, so putting something off does
not permanently penalise the schedule for that pattern.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from ..models import ReviewItem
from .state import GraphState

INITIAL_INTERVAL_DAYS = 3.0
INITIAL_EASE = 2.5
EASE_PENALTY = 0.2
EASE_FLOOR = 1.3
FAILURE_INTERVAL_DAYS = 1.0
SKIP_INTERVAL_DAYS = 1.0


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def next_schedule(
    *, result: str, interval_days: float, ease: float, repetitions: int
) -> tuple[float, float, int]:
    """Pure SM-2 step. Returns (interval_days, ease, repetitions)."""
    if result == "solved":
        return interval_days * ease, ease, repetitions + 1
    if result == "failed":
        return FAILURE_INTERVAL_DAYS, max(EASE_FLOOR, ease - EASE_PENALTY), 0
    if result == "skipped":
        return SKIP_INTERVAL_DAYS, ease, repetitions
    raise ValueError(f"unknown review result {result!r}")


def apply_review(db: Session, item: ReviewItem, result: str) -> ReviewItem:
    interval, ease, repetitions = next_schedule(
        result=result,
        interval_days=item.interval_days,
        ease=item.ease,
        repetitions=item.repetitions,
    )
    item.interval_days = interval
    item.ease = ease
    item.repetitions = repetitions
    item.last_result = result
    item.due_at = _now() + dt.timedelta(days=interval)
    db.add(item)
    db.flush()
    return item


def enqueue(
    db: Session, *, user_id: str, problem_id: str, pattern_id: str
) -> ReviewItem | None:
    """Add a recommended problem to the queue. Idempotent per (user, problem)."""
    existing = (
        db.query(ReviewItem)
        .filter(ReviewItem.user_id == user_id, ReviewItem.problem_id == problem_id)
        .one_or_none()
    )
    if existing is not None:
        return None

    item = ReviewItem(
        user_id=user_id,
        problem_id=problem_id,
        pattern_id=pattern_id,
        due_at=_now() + dt.timedelta(days=INITIAL_INTERVAL_DAYS),
        interval_days=INITIAL_INTERVAL_DAYS,
        ease=INITIAL_EASE,
        repetitions=0,
    )
    db.add(item)
    db.flush()
    return item


def scheduler_node(state: GraphState, db: Session) -> GraphState:
    for rec in state.get("recommendations", []):
        enqueue(
            db,
            user_id=state["user_id"],
            problem_id=rec["id"],
            pattern_id=state["pattern_id"],
        )
    return state
