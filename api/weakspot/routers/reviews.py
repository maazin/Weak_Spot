"""Review queue routes."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..graph.scheduler import apply_review
from ..models import ReviewItem, User
from ..schemas import (
    ProblemOut,
    ReviewComplete,
    ReviewCompleted,
    ReviewItemOut,
    ReviewList,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _item_out(item: ReviewItem) -> ReviewItemOut:
    return ReviewItemOut(
        id=item.id,
        problem=ProblemOut(
            id=item.problem.id,
            slug=item.problem.slug,
            title=item.problem.title,
            difficulty=item.problem.difficulty,
            tags=list(item.problem.tags),
            url=item.problem.url,
        ),
        pattern_id=item.pattern_id,
        pattern_name=item.pattern.name,
        due_at=item.due_at,
        interval_days=item.interval_days,
        repetitions=item.repetitions,
        last_result=item.last_result,
    )


@router.get("/due", response_model=ReviewList)
def due_reviews(db: Session = Depends(get_db), user: User = Depends(current_user)) -> ReviewList:
    now = dt.datetime.now(dt.UTC)
    due = (
        db.query(ReviewItem)
        .filter(ReviewItem.user_id == user.id, ReviewItem.due_at <= now)
        .order_by(ReviewItem.due_at.asc())
        .all()
    )
    total = db.query(ReviewItem).filter(ReviewItem.user_id == user.id).count()
    return ReviewList(items=[_item_out(i) for i in due], total_items=total)


@router.post("/{item_id}/complete", response_model=ReviewCompleted)
def complete_review(
    item_id: str,
    payload: ReviewComplete,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> ReviewCompleted:
    item = db.get(ReviewItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="review item not found")

    apply_review(db, item, payload.result)
    db.commit()
    return ReviewCompleted(next_due_at=item.due_at, interval_days=item.interval_days)
