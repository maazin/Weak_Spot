"""POST /submissions and its reads."""

from __future__ import annotations

import base64
import datetime as dt
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import metrics
from ..auth import current_user
from ..db import get_db
from ..graph.build import run_diagnosis
from ..graph.intake import IntakeError, restore, vault
from ..models import Diagnosis, Problem, ReviewItem, Submission, User
from ..ratelimit import consume_quota, refund_quota
from ..schemas import (
    DiagnosisOut,
    EvidenceSpanOut,
    PatternOut,
    ProblemOut,
    SubmissionAccepted,
    SubmissionCreate,
    SubmissionDetail,
    SubmissionList,
    SubmissionListItem,
    SubmissionOut,
)
from ..taxonomy import get_taxonomy
from ..tracing import tag_trace, trace_id_of, trace_submission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/submissions", tags=["submissions"])


def _problem_out(problem: Problem) -> ProblemOut:
    return ProblemOut(
        id=problem.id,
        slug=problem.slug,
        title=problem.title,
        difficulty=problem.difficulty,
        tags=list(problem.tags),
        url=problem.url,
    )


def _pattern_out(pattern_id: str) -> PatternOut:
    entry = get_taxonomy().get(pattern_id)
    if entry is None:
        raise HTTPException(status_code=500, detail=f"unknown pattern {pattern_id}")
    return PatternOut(
        id=entry.id,
        family=entry.family,
        name=entry.name,
        correct_approach=entry.correct_approach,
        practice_tags=list(entry.practice_tags),
    )


def _diagnosis_out(diagnosis: Diagnosis, submission: Submission) -> DiagnosisOut:
    """Restore vaulted placeholders so the user sees their own text back."""
    _, vault_map = vault(submission.code_text, submission.language)
    lines = submission.code_text.split("\n")

    spans = []
    for span in diagnosis.evidence_spans:
        start = max(1, int(span["start_line"]))
        end = min(len(lines), int(span["end_line"]))
        snippet = "\n".join(lines[start - 1 : end]) if start <= end else None
        spans.append(
            EvidenceSpanOut(
                start_line=start,
                end_line=end,
                why=restore(str(span.get("why", "")), vault_map),
                text=snippet,
            )
        )

    return DiagnosisOut(
        id=diagnosis.id,
        pattern=_pattern_out(diagnosis.pattern_id),
        alternate_pattern_id=diagnosis.alternate_pattern_id,
        confidence=diagnosis.confidence,
        evidence_spans=spans,
        explanation=restore(diagnosis.explanation, vault_map),
        model_tier=diagnosis.model_tier,
        verifier_passed=diagnosis.verifier_passed,
        retry_count=diagnosis.retry_count,
        latency_ms=diagnosis.latency_ms,
        created_at=diagnosis.created_at,
    )


@router.post("", response_model=SubmissionAccepted, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SubmissionAccepted:
    problem = db.query(Problem).filter(Problem.slug == payload.problem_slug).one_or_none()
    if problem is None:
        raise HTTPException(
            status_code=404,
            detail=f"problem {payload.problem_slug!r} is not in the index",
        )

    from ..graph.intake import compute_code_hash, normalize

    normalized = normalize(payload.code)
    code_hash = compute_code_hash(problem.slug, normalized)

    # Cache on code_hash before touching the quota — an identical resubmission is free.
    cached = (
        db.query(Diagnosis)
        .join(Submission, Diagnosis.submission_id == Submission.id)
        .filter(Submission.code_hash == code_hash, Submission.user_id == user.id)
        .first()
    )
    if cached is not None:
        metrics.cache_hits_total.inc()
        return SubmissionAccepted(
            submission_id=cached.submission_id,
            status="cached",
            diagnosis_id=cached.id,
        )

    if not consume_quota(user.id):
        metrics.rate_limited_total.inc()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="daily diagnosis limit reached",
        )

    submission = Submission(
        user_id=user.id,
        problem_id=problem.id,
        language=payload.language,
        failure_type=payload.failure_type,
        code_hash=code_hash,
        code_text=payload.code,
    )
    db.add(submission)
    db.flush()

    try:
        with trace_submission(submission.id, user.id) as trace:
            final = run_diagnosis(
                db,
                {
                    "submission_id": submission.id,
                    "user_id": user.id,
                    "problem_id": problem.id,
                    "problem_slug": problem.slug,
                    "problem_title": problem.title,
                    "problem_tags": list(problem.tags),
                    "problem_difficulty": problem.difficulty,
                    "language": payload.language,
                    "failure_type": payload.failure_type,
                    "code_text": payload.code,
                },
            )
            tag_trace(trace, final)
            trace_id = trace_id_of(trace)
    except IntakeError as exc:
        # Parser failures are rejected before any LLM call, so the quota is returned.
        refund_quota(user.id)
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        refund_quota(user.id)
        db.rollback()
        logger.exception("diagnosis failed for submission %s", submission.id)
        raise HTTPException(status_code=502, detail="diagnosis failed") from exc

    diagnosis = Diagnosis(
        submission_id=submission.id,
        pattern_id=final["pattern_id"],
        alternate_pattern_id=final.get("alternate_pattern_id"),
        confidence=final.get("confidence", 0.0),
        evidence_spans=final.get("evidence_spans", []),
        explanation=final.get("explanation", ""),
        model_tier=final.get("model_tier", ""),
        verifier_passed=final.get("verifier_passed", False),
        verifier_failures=final.get("verifier_failures", []),
        retry_count=final.get("retry_count", 0),
        cost_usd=final.get("cost_usd", 0.0),
        latency_ms=final.get("latency_ms", 0),
        trace_id=trace_id,
    )
    db.add(diagnosis)
    db.commit()

    metrics.record_diagnosis(
        model_tier=diagnosis.model_tier,
        verifier_passed=diagnosis.verifier_passed,
        latency_ms=diagnosis.latency_ms,
        cost_usd=diagnosis.cost_usd,
        failed_checks=[f["check"] for f in diagnosis.verifier_failures],
    )

    return SubmissionAccepted(
        submission_id=submission.id, status="complete", diagnosis_id=diagnosis.id
    )


@router.get("", response_model=SubmissionList)
def list_submissions(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SubmissionList:
    query = db.query(Submission).filter(Submission.user_id == user.id)

    if cursor:
        try:
            # Decoded to a datetime, not left as text: Postgres has no comparison
            # between timestamptz and varchar and will refuse the query outright.
            after = dt.datetime.fromisoformat(base64.urlsafe_b64decode(cursor.encode()).decode())
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid cursor") from exc
        query = query.filter(Submission.created_at < after)

    rows = query.order_by(Submission.created_at.desc()).limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    next_cursor = None
    if has_more and rows:
        next_cursor = base64.urlsafe_b64encode(rows[-1].created_at.isoformat().encode()).decode()

    return SubmissionList(
        items=[
            SubmissionListItem(
                id=s.id,
                problem_slug=s.problem.slug,
                problem_title=s.problem.title,
                failure_type=s.failure_type,
                pattern_id=s.diagnosis.pattern_id if s.diagnosis else None,
                created_at=s.created_at,
            )
            for s in rows
        ],
        next_cursor=next_cursor,
    )


@router.get("/{submission_id}", response_model=SubmissionDetail)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> SubmissionDetail:
    submission = db.get(Submission, submission_id)
    if submission is None or submission.user_id != user.id:
        raise HTTPException(status_code=404, detail="submission not found")

    diagnosis = submission.diagnosis
    recommendations: list[ProblemOut] = []
    if diagnosis is not None:
        items = (
            db.query(ReviewItem)
            .filter(
                ReviewItem.user_id == user.id,
                ReviewItem.pattern_id == diagnosis.pattern_id,
            )
            .order_by(ReviewItem.created_at.desc())
            .limit(3)
            .all()
        )
        recommendations = [_problem_out(i.problem) for i in items]

    return SubmissionDetail(
        submission=SubmissionOut(
            id=submission.id,
            problem=_problem_out(submission.problem),
            language=submission.language,
            failure_type=submission.failure_type,
            code_text=submission.code_text,
            created_at=submission.created_at,
        ),
        diagnosis=_diagnosis_out(diagnosis, submission) if diagnosis else None,
        recommendations=recommendations,
    )
