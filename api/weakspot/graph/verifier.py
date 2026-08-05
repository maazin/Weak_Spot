"""`verifier` — cheap-tier LLM node running the four checks from spec section 5.

Two of the four have a mechanical component that is cheaper and more reliable to run in
Python than to ask a model about: whether a cited line range exists at all, and whether
the explanation contains a code block longer than three lines. Those run first and
short-circuit — a diagnosis citing line 400 of a 30-line file is rejected without
spending a token. The model then judges the parts that require reading.

Every rejection is logged. Rejection rate is a headline metric, so it is recorded on the
diagnosis row and exported from `/metrics`.
"""

from __future__ import annotations

import logging
import re

from ..config import get_settings
from ..llm import call_structured
from ..prompts import verifier as prompt
from ..taxonomy import get_taxonomy
from .state import GraphState, VerifierFailure

logger = logging.getLogger(__name__)

FENCE_RE = re.compile(r"```[a-zA-Z0-9+]*\n(.*?)```", re.DOTALL)
MAX_CODE_BLOCK_LINES = 3

# Families that cannot coexist with a reported failure type without contradiction.
CONTRADICTIONS: dict[str, set[str]] = {
    "wrong_answer": {"complexity"},
    "tle": {"comprehension"},
    "mle": {"comprehension"},
}


def _mechanical_checks(state: GraphState) -> list[VerifierFailure]:
    failures: list[VerifierFailure] = []
    line_count = len(state["normalized_code"].split("\n"))
    spans = state.get("evidence_spans", [])

    if not spans:
        failures.append({"check": "evidence_grounded", "detail": "no evidence spans were cited"})

    for span in spans:
        start, end = span["start_line"], span["end_line"]
        if start < 1 or end < start or end > line_count:
            failures.append(
                {
                    "check": "evidence_grounded",
                    "detail": (
                        f"span {start}-{end} does not exist in a {line_count}-line submission"
                    ),
                }
            )

    explanation = state.get("explanation", "")
    for block in FENCE_RE.findall(explanation):
        block_lines = [ln for ln in block.strip().split("\n") if ln.strip()]
        if len(block_lines) > MAX_CODE_BLOCK_LINES:
            failures.append(
                {
                    "check": "no_solution_code",
                    "detail": (
                        f"explanation contains a {len(block_lines)}-line code block; "
                        f"the cap is {MAX_CODE_BLOCK_LINES}"
                    ),
                }
            )

    return failures


def verifier_node(state: GraphState) -> GraphState:
    settings = get_settings()
    taxonomy = get_taxonomy()

    failures = _mechanical_checks(state)
    if failures:
        for failure in failures:
            logger.warning(
                "verifier rejected (mechanical): submission=%s check=%s detail=%s",
                state.get("submission_id"),
                failure["check"],
                failure["detail"],
            )
        return {**state, "verifier_passed": False, "verifier_failures": failures}

    entry = taxonomy.get(state["pattern_id"])
    family = entry.family if entry else "unknown"

    # A cheap deterministic contradiction check ahead of the model's judgement.
    if family in CONTRADICTIONS.get(state["failure_type"], set()):
        failure: VerifierFailure = {
            "check": "consistent_with_failure_type",
            "detail": (
                f"a {family} diagnosis contradicts a reported {state['failure_type']} failure"
            ),
        }
        logger.warning(
            "verifier rejected (contradiction): submission=%s %s",
            state.get("submission_id"),
            failure["detail"],
        )
        return {**state, "verifier_passed": False, "verifier_failures": [failure]}

    result = call_structured(
        model=settings.model_tier_verifier,
        cached_system=prompt.INSTRUCTIONS,
        user_content=prompt.build_user_content(
            failure_type=state["failure_type"],
            pattern_id=state["pattern_id"],
            pattern_family=family,
            pattern_name=entry.name if entry else "",
            confidence=state.get("confidence", 0.0),
            explanation=state.get("explanation", ""),
            evidence_spans=state.get("evidence_spans", []),
            vaulted_code=state["vaulted_code"],
        ),
        tool_name=prompt.TOOL_NAME,
        tool_description=prompt.TOOL_DESCRIPTION,
        input_schema=prompt.SCHEMA,
        max_tokens=1024,
    )

    payload = result.tool_input
    model_failures: list[VerifierFailure] = [
        {"check": check, "detail": str(payload.get("reason", "")).strip() or "check failed"}
        for check in prompt.CHECK_NAMES
        if not payload.get(check, False)
    ]
    passed = bool(payload.get("passed", False)) and not model_failures

    if not passed:
        logger.warning(
            "verifier rejected: submission=%s pattern=%s failures=%s",
            state.get("submission_id"),
            state["pattern_id"],
            [f["check"] for f in model_failures],
        )

    return {
        **state,
        "verifier_passed": passed,
        "verifier_failures": model_failures,
        "cost_usd": state.get("cost_usd", 0.0) + result.cost_usd,
        "latency_ms": state.get("latency_ms", 0) + result.latency_ms,
    }
