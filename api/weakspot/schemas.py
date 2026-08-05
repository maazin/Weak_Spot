"""Request and response bodies for /api/v1."""

from __future__ import annotations

import datetime as dt
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .config import get_settings
from .models import FAILURE_TYPES, LANGUAGES, REVIEW_RESULTS

FailureType = Literal[FAILURE_TYPES]  # type: ignore[valid-type]
Language = Literal[LANGUAGES]  # type: ignore[valid-type]
ReviewResult = Literal[REVIEW_RESULTS]  # type: ignore[valid-type]

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
URL_SLUG_RE = re.compile(r"/problems/([a-z0-9-]+)")


class SubmissionCreate(BaseModel):
    problem_slug: str = Field(max_length=300)
    code: str
    language: str
    failure_type: str

    @field_validator("problem_slug")
    @classmethod
    def _accept_slug_or_url(cls, v: str) -> str:
        """The UI lets users paste either a slug or the problem URL."""
        v = v.strip()
        match = URL_SLUG_RE.search(v)
        if match:
            return match.group(1)
        v = v.rstrip("/").split("/")[-1]
        if not SLUG_RE.match(v):
            raise ValueError("problem_slug must be a slug or a problem URL")
        return v

    @field_validator("language")
    @classmethod
    def _known_language(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in LANGUAGES:
            raise ValueError(f"language must be one of {LANGUAGES}")
        return v

    @field_validator("failure_type")
    @classmethod
    def _known_failure(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in FAILURE_TYPES:
            raise ValueError(f"failure_type must be one of {FAILURE_TYPES}")
        return v

    @field_validator("code")
    @classmethod
    def _within_caps(cls, v: str) -> str:
        settings = get_settings()
        if not v.strip():
            raise ValueError("code must not be empty")
        if len(v.encode("utf-8")) > settings.max_code_bytes:
            raise ValueError(f"code exceeds {settings.max_code_bytes} bytes")
        if v.count("\n") + 1 > settings.max_code_lines:
            raise ValueError(f"code exceeds {settings.max_code_lines} lines")
        return v


class SubmissionAccepted(BaseModel):
    submission_id: str
    status: Literal["processing", "cached", "complete"]
    diagnosis_id: str | None = None


class ProblemOut(BaseModel):
    id: str
    slug: str
    title: str
    difficulty: str
    tags: list[str]
    url: str


class PatternOut(BaseModel):
    id: str
    family: str
    name: str
    correct_approach: str
    practice_tags: list[str]


class EvidenceSpanOut(BaseModel):
    start_line: int
    end_line: int
    why: str
    # Restored from the vault so the user sees their own comment text back.
    text: str | None = None


class DiagnosisOut(BaseModel):
    id: str
    pattern: PatternOut
    alternate_pattern_id: str | None
    confidence: float
    evidence_spans: list[EvidenceSpanOut]
    explanation: str
    model_tier: str
    verifier_passed: bool
    retry_count: int
    latency_ms: int
    created_at: dt.datetime


class SubmissionOut(BaseModel):
    id: str
    problem: ProblemOut
    language: str
    failure_type: str
    code_text: str
    created_at: dt.datetime


class SubmissionDetail(BaseModel):
    submission: SubmissionOut
    diagnosis: DiagnosisOut | None
    recommendations: list[ProblemOut]


class SubmissionListItem(BaseModel):
    id: str
    problem_slug: str
    problem_title: str
    failure_type: str
    pattern_id: str | None
    created_at: dt.datetime


class SubmissionList(BaseModel):
    items: list[SubmissionListItem]
    next_cursor: str | None


class ReviewItemOut(BaseModel):
    id: str
    problem: ProblemOut
    pattern_id: str
    pattern_name: str
    due_at: dt.datetime
    interval_days: float
    repetitions: int
    last_result: str | None


class ReviewList(BaseModel):
    items: list[ReviewItemOut]
    # Distinguishes "queue exists, nothing due" from "no queue at all", which is what
    # picks between the two empty-state illustrations.
    total_items: int


class ReviewComplete(BaseModel):
    result: str

    @field_validator("result")
    @classmethod
    def _known_result(cls, v: str) -> str:
        if v not in REVIEW_RESULTS:
            raise ValueError(f"result must be one of {REVIEW_RESULTS}")
        return v


class ReviewCompleted(BaseModel):
    next_due_at: dt.datetime
    interval_days: float


class WeakPattern(BaseModel):
    pattern: PatternOut
    occurrences: int
    last_seen_at: dt.datetime
    trend: Literal["up", "down", "flat"]


class WeakPatternList(BaseModel):
    items: list[WeakPattern]


class PatternList(BaseModel):
    patterns: list[PatternOut]


class ProblemList(BaseModel):
    results: list[ProblemOut]


class UserOut(BaseModel):
    id: str
    handle: str


class HealthOut(BaseModel):
    status: str
    database: bool
    redis: bool
    schema_current: bool
    taxonomy_entries: int
