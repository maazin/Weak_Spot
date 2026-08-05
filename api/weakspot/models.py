"""SQLAlchemy models — spec section 4.

Legal constraint baked in from the first migration: `problems` carries slug, title,
difficulty, tags, and a canonical URL. There is no column for a problem statement or
an editorial, and there never will be. Every problem shown to a user is a link out.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .config import get_settings

EMBED_DIM = get_settings().embedding_dim

FAILURE_TYPES = (
    "wrong_answer",
    "tle",
    "mle",
    "runtime_error",
    "gave_up",
    "looked_at_solution",
)

LANGUAGES = ("python", "java", "cpp", "javascript", "go")

REVIEW_RESULTS = ("solved", "failed", "skipped")


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    github_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    handle: Mapped[str] = mapped_column(String(128))
    api_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    difficulty: Mapped[str] = mapped_column(String(16))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    url: Mapped[str] = mapped_column(String(500))
    embedding: Mapped[Any | None] = mapped_column(Vector(EMBED_DIM), nullable=True)

    __table_args__ = (
        CheckConstraint("difficulty in ('easy','medium','hard')", name="ck_problem_difficulty"),
        Index("ix_problems_fts", func.to_tsvector("english", title), postgresql_using="gin"),
    )


class Pattern(Base):
    __tablename__ = "patterns"

    # Natural key: the taxonomy id, e.g. "implementation.binary_search_bounds_off_by_one".
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    family: Mapped[str] = mapped_column(String(40), index=True)
    name: Mapped[str] = mapped_column(String(300))
    correct_approach: Mapped[str] = mapped_column(Text)
    practice_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    embedding: Mapped[Any | None] = mapped_column(Vector(EMBED_DIM), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "family in ('pattern_selection','implementation','complexity','comprehension')",
            name="ck_pattern_family",
        ),
    )


class PatternProblem(Base):
    __tablename__ = "pattern_problems"

    pattern_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("patterns.id", ondelete="CASCADE"), primary_key=True
    )
    problem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True
    )
    # 0..1. Curated pairs are written at 1.0; embedding-generated pairs keep their score.
    strength: Mapped[float] = mapped_column(Float, default=0.5)
    curated: Mapped[bool] = mapped_column(default=False)


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    problem_id: Mapped[str] = mapped_column(String(36), ForeignKey("problems.id"))
    language: Mapped[str] = mapped_column(String(20))
    failure_type: Mapped[str] = mapped_column(String(32))
    code_hash: Mapped[str] = mapped_column(String(64), index=True)
    code_text: Mapped[str] = mapped_column(Text)  # capped at 32KB by the API layer
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True
    )

    problem: Mapped[Problem] = relationship(lazy="joined")
    diagnosis: Mapped["Diagnosis | None"] = relationship(
        back_populates="submission", uselist=False, lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "failure_type in " + str(FAILURE_TYPES), name="ck_submission_failure_type"
        ),
        CheckConstraint("language in " + str(LANGUAGES), name="ck_submission_language"),
        Index("ix_submissions_user_created", "user_id", "created_at"),
    )


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="CASCADE"), unique=True
    )
    pattern_id: Mapped[str] = mapped_column(String(120), ForeignKey("patterns.id"))
    alternate_pattern_id: Mapped[str | None] = mapped_column(
        String(120), ForeignKey("patterns.id"), nullable=True
    )
    confidence: Mapped[float] = mapped_column(Float)
    evidence_spans: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    explanation: Mapped[str] = mapped_column(Text)
    model_tier: Mapped[str] = mapped_column(String(40))
    verifier_passed: Mapped[bool] = mapped_column(default=False)
    verifier_failures: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    submission: Mapped[Submission] = relationship(back_populates="diagnosis")
    pattern: Mapped[Pattern] = relationship(foreign_keys=[pattern_id], lazy="joined")


class ReviewItem(Base):
    __tablename__ = "review_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    problem_id: Mapped[str] = mapped_column(String(36), ForeignKey("problems.id"))
    pattern_id: Mapped[str] = mapped_column(String(120), ForeignKey("patterns.id"))
    due_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    interval_days: Mapped[float] = mapped_column(Float, default=3.0)
    ease: Mapped[float] = mapped_column(Float, default=2.5)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    last_result: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    problem: Mapped[Problem] = relationship(lazy="joined")
    pattern: Mapped[Pattern] = relationship(lazy="joined")

    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uq_review_user_problem"),
        Index("ix_review_user_due", "user_id", "due_at"),
    )


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    suite: Mapped[str] = mapped_column(String(8))
    commit_sha: Mapped[str] = mapped_column(String(40))
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
