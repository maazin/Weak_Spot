"""Graph state — carries the submission, intermediate findings, and the retry counter."""

from __future__ import annotations

from typing import Any, TypedDict


class EvidenceSpan(TypedDict):
    start_line: int
    end_line: int
    why: str


class VerifierFailure(TypedDict):
    check: str
    detail: str


class GraphState(TypedDict, total=False):
    # --- inputs ---
    submission_id: str
    user_id: str
    problem_id: str
    problem_slug: str
    problem_title: str
    problem_tags: list[str]
    problem_difficulty: str
    language: str
    failure_type: str
    code_text: str

    # --- intake ---
    normalized_code: str
    vaulted_code: str
    vault: dict[str, str]
    structural_signals: list[str]
    code_hash: str
    cached_diagnosis_id: str | None
    intake_error: str | None

    # --- diagnoser ---
    pattern_id: str
    alternate_pattern_id: str | None
    confidence: float
    evidence_spans: list[EvidenceSpan]
    explanation: str
    model_tier: str

    # --- verifier ---
    verifier_passed: bool
    verifier_failures: list[VerifierFailure]
    retry_count: int

    # --- retriever ---
    prewarmed: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]

    # --- accounting ---
    cost_usd: float
    latency_ms: int
    trace_id: str | None
