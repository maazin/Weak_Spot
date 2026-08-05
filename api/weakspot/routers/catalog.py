"""Patterns, pattern-problems, problem search, and the weak-pattern profile."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..models import PatternProblem, Problem, User
from ..schemas import (
    PatternList,
    PatternOut,
    ProblemList,
    ProblemOut,
    WeakPattern,
    WeakPatternList,
)
from ..taxonomy import get_taxonomy

router = APIRouter(tags=["catalog"])


def _problem_out(p: Problem) -> ProblemOut:
    return ProblemOut(
        id=p.id,
        slug=p.slug,
        title=p.title,
        difficulty=p.difficulty,
        tags=list(p.tags),
        url=p.url,
    )


def _pattern_out(pattern_id: str) -> PatternOut:
    entry = get_taxonomy().get(pattern_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="pattern not found")
    return PatternOut(
        id=entry.id,
        family=entry.family,
        name=entry.name,
        correct_approach=entry.correct_approach,
        practice_tags=list(entry.practice_tags),
    )


@router.get("/patterns", response_model=PatternList)
def list_patterns() -> PatternList:
    taxonomy = get_taxonomy()
    return PatternList(patterns=[_pattern_out(p) for p in taxonomy.allowed_ids()])


@router.get("/patterns/{pattern_id}/problems", response_model=ProblemList)
def pattern_problems(
    pattern_id: str,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> ProblemList:
    if pattern_id not in get_taxonomy():
        raise HTTPException(status_code=404, detail="pattern not found")

    rows = (
        db.query(Problem)
        .join(PatternProblem, PatternProblem.problem_id == Problem.id)
        .filter(PatternProblem.pattern_id == pattern_id)
        .order_by(PatternProblem.curated.desc(), PatternProblem.strength.desc())
        .limit(limit)
        .all()
    )
    return ProblemList(results=[_problem_out(p) for p in rows])


@router.get("/problems/search", response_model=ProblemList)
def search_problems(
    q: str | None = None,
    pattern: str | None = None,
    difficulty: str | None = None,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> ProblemList:
    query = db.query(Problem)

    if pattern:
        query = query.join(PatternProblem, PatternProblem.problem_id == Problem.id).filter(
            PatternProblem.pattern_id == pattern
        )
    if difficulty:
        query = query.filter(Problem.difficulty == difficulty)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(text("lower(problems.title) LIKE :like")).params(like=like)

    return ProblemList(results=[_problem_out(p) for p in query.limit(limit).all()])


@router.get("/me/weak-patterns", response_model=WeakPatternList)
def weak_patterns(
    db: Session = Depends(get_db), user: User = Depends(current_user)
) -> WeakPatternList:
    """Occurrence counts with a trend arrow.

    Trend compares the last 30 days against the 30 before that, so a pattern the user
    has since drilled reads as `down` rather than staying permanently near the top.
    """
    rows = db.execute(
        text(
            """
            SELECT d.pattern_id,
                   COUNT(*) AS occurrences,
                   MAX(s.created_at) AS last_seen_at,
                   COUNT(*) FILTER (
                       WHERE s.created_at > NOW() - INTERVAL '30 days') AS recent,
                   COUNT(*) FILTER (
                       WHERE s.created_at <= NOW() - INTERVAL '30 days'
                         AND s.created_at > NOW() - INTERVAL '60 days') AS prior
              FROM diagnoses d
              JOIN submissions s ON s.id = d.submission_id
             WHERE s.user_id = :uid
             GROUP BY d.pattern_id
             ORDER BY occurrences DESC, last_seen_at DESC
            """
        ),
        {"uid": user.id},
    ).fetchall()

    items: list[WeakPattern] = []
    for pattern_id, occurrences, last_seen_at, recent, prior in rows:
        if recent > prior:
            trend = "up"
        elif recent < prior:
            trend = "down"
        else:
            trend = "flat"
        items.append(
            WeakPattern(
                pattern=_pattern_out(pattern_id),
                occurrences=int(occurrences),
                last_seen_at=last_seen_at or dt.datetime.now(dt.UTC),
                trend=trend,
            )
        )

    return WeakPatternList(items=items)
