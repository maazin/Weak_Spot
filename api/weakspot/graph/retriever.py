"""`retriever` — hybrid search with reciprocal rank fusion. No LLM in the search itself.

Two arms, fused with RRF at k=60:

  * keyword — Postgres full-text over title plus tags, and exact overlap against the
    pattern's `practice_tags`
  * vector  — pgvector cosine between `problems.embedding` and `patterns.embedding`

RRF is used rather than score blending because the two arms produce scores on
incomparable scales; ranks are the only thing that is safe to combine without tuning a
weight per arm. Suite C publishes this against keyword-only and vector-only baselines so
the fusion has to justify itself with a number.

The tag-based pre-warm runs concurrently with the diagnoser. It uses only the failed
problem's own tags, which are known at intake, so by the time `pattern_id` lands the
expensive half of the work is already done and the wait is hidden inside the LLM call.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import Pattern, Problem
from .state import GraphState

logger = logging.getLogger(__name__)

RRF_K = 60
ARM_LIMIT = 50
FINAL_LIMIT = 3

DIFFICULTY_RANK = {"easy": 0, "medium": 1, "hard": 2}


def _excluded_problem_ids(db: Session, user_id: str) -> set[str]:
    """Problems the user already solved or has queued — never recommend these."""
    rows = db.execute(
        text(
            """
            SELECT problem_id FROM review_items WHERE user_id = :uid
            UNION
            SELECT s.problem_id
              FROM submissions s
              JOIN diagnoses d ON d.submission_id = s.id
             WHERE s.user_id = :uid
            """
        ),
        {"uid": user_id},
    ).fetchall()
    return {row[0] for row in rows}


def keyword_arm(
    db: Session, *, query_terms: list[str], practice_tags: list[str], limit: int = ARM_LIMIT
) -> list[str]:
    """Full-text over title, plus array overlap on tags. Returns problem ids, best first."""
    if not query_terms and not practice_tags:
        return []

    tsquery = " | ".join(t.replace(":", " ").strip() for t in query_terms if t.strip())
    rows = db.execute(
        text(
            """
            SELECT id,
                   ts_rank(to_tsvector('english', title),
                           to_tsquery('english', :tsquery)) AS text_rank,
                   cardinality(ARRAY(SELECT UNNEST(tags::text[]) INTERSECT
                                     SELECT UNNEST(CAST(:tags AS text[])))) AS tag_overlap
              FROM problems
             WHERE (:tsquery = '' OR to_tsvector('english', title) @@
                    to_tsquery('english', :tsquery))
                OR tags::text[] && CAST(:tags AS text[])
             ORDER BY tag_overlap DESC, text_rank DESC
             LIMIT :limit
            """
        ),
        {"tsquery": tsquery, "tags": practice_tags or [], "limit": limit},
    ).fetchall()
    return [row[0] for row in rows]


def vector_arm(db: Session, *, pattern_id: str, limit: int = ARM_LIMIT) -> list[str]:
    """Cosine nearest problems to the pattern's own embedding."""
    pattern = db.get(Pattern, pattern_id)
    if pattern is None or pattern.embedding is None:
        return []

    rows = db.execute(
        text(
            """
            SELECT id
              FROM problems
             WHERE embedding IS NOT NULL
             ORDER BY embedding <=> CAST(:vec AS vector)
             LIMIT :limit
            """
        ),
        {"vec": list(pattern.embedding), "limit": limit},
    ).fetchall()
    return [row[0] for row in rows]


def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = RRF_K) -> list[str]:
    """Standard RRF: each list contributes 1/(k + rank), ranks starting at 1."""
    scores: dict[str, float] = {}
    for ranking in ranked_lists:
        for position, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + position)
    return [item for item, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)]


def _mix_difficulty(
    problems: list[Problem], failed_difficulty: str, limit: int = FINAL_LIMIT
) -> list[Problem]:
    """One at or below the failed problem's difficulty, two at or above.

    Falls back to plain fusion order when the pool cannot satisfy the mix, rather than
    returning fewer than three.
    """
    base = DIFFICULTY_RANK.get(failed_difficulty, 1)
    at_or_below = [p for p in problems if DIFFICULTY_RANK.get(p.difficulty, 1) <= base]
    at_or_above = [p for p in problems if DIFFICULTY_RANK.get(p.difficulty, 1) >= base]

    picked: list[Problem] = []
    if at_or_below:
        picked.append(at_or_below[0])
    for candidate in at_or_above:
        if len(picked) >= limit:
            break
        if candidate.id not in {p.id for p in picked}:
            picked.append(candidate)
    for candidate in problems:
        if len(picked) >= limit:
            break
        if candidate.id not in {p.id for p in picked}:
            picked.append(candidate)
    return picked[:limit]


def prewarm(db: Session, *, tags: list[str], user_id: str) -> list[str]:
    """Tag-only keyword pass, runnable before `pattern_id` exists."""
    excluded = _excluded_problem_ids(db, user_id)
    ids = keyword_arm(db, query_terms=tags, practice_tags=tags)
    return [pid for pid in ids if pid not in excluded]


def search(
    db: Session,
    *,
    pattern_id: str,
    user_id: str,
    failed_difficulty: str,
    exclude_problem_id: str | None = None,
    prewarmed: list[str] | None = None,
    limit: int = FINAL_LIMIT,
) -> list[Problem]:
    pattern = db.get(Pattern, pattern_id)
    practice_tags = list(pattern.practice_tags) if pattern else []

    keyword_ids = keyword_arm(db, query_terms=practice_tags, practice_tags=practice_tags)
    vector_ids = vector_arm(db, pattern_id=pattern_id)

    arms = [keyword_ids, vector_ids]
    if prewarmed:
        arms.append(prewarmed)

    fused = reciprocal_rank_fusion(arms)

    excluded = _excluded_problem_ids(db, user_id)
    if exclude_problem_id:
        excluded.add(exclude_problem_id)
    candidate_ids = [pid for pid in fused if pid not in excluded]
    if not candidate_ids:
        return []

    found = {p.id: p for p in db.query(Problem).filter(Problem.id.in_(candidate_ids[:40]))}
    ordered = [found[pid] for pid in candidate_ids if pid in found]
    return _mix_difficulty(ordered, failed_difficulty, limit)


def retriever_node(state: GraphState, db: Session) -> GraphState:
    problems = search(
        db,
        pattern_id=state["pattern_id"],
        user_id=state["user_id"],
        failed_difficulty=state.get("problem_difficulty", "medium"),
        exclude_problem_id=state.get("problem_id"),
        prewarmed=[p["id"] for p in state.get("prewarmed", [])] or None,
    )

    if not problems:
        logger.warning(
            "retriever found no recommendations: pattern=%s user=%s",
            state["pattern_id"],
            state["user_id"],
        )

    return {
        **state,
        "recommendations": [
            {
                "id": p.id,
                "slug": p.slug,
                "title": p.title,
                "difficulty": p.difficulty,
                "tags": list(p.tags),
                "url": p.url,
            }
            for p in problems
        ],
    }
