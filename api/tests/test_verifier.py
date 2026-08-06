"""Verifier checks that run without a model call, plus the prompt contract.

The mechanical checks are the ones that must never need a token to reject: a span that
cannot exist, an explanation carrying a pasteable solution, or a diagnosis the model
itself is not confident in.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("ENV", "test")

from weakspot.graph.verifier import (  # noqa: E402
    MAX_CODE_BLOCK_LINES,
    MIN_CONFIDENCE,
    _mechanical_checks,
)
from weakspot.prompts import verifier as prompt  # noqa: E402
from weakspot.taxonomy import load_taxonomy  # noqa: E402

CODE = "def f(xs):\n    for x in xs:\n        pass\n    return 0\n"


def _state(**overrides):
    base = {
        "normalized_code": CODE,
        "vaulted_code": CODE,
        "failure_type": "wrong_answer",
        "pattern_id": "complexity.missing_memoization",
        "confidence": 0.9,
        "explanation": "The recursion recomputes the same subproblem repeatedly.",
        "evidence_spans": [{"start_line": 2, "end_line": 3, "why": "the loop"}],
    }
    base.update(overrides)
    return base


def _checks(state) -> set[str]:
    return {f["check"] for f in _mechanical_checks(state)}


def test_a_sound_diagnosis_passes_the_mechanical_checks():
    assert _mechanical_checks(_state()) == []


def test_span_beyond_the_file_is_rejected_without_a_model_call():
    assert "evidence_grounded" in _checks(
        _state(evidence_spans=[{"start_line": 1, "end_line": 400, "why": "x"}])
    )


def test_missing_evidence_is_rejected():
    assert "evidence_grounded" in _checks(_state(evidence_spans=[]))


def test_inverted_span_is_rejected():
    assert "evidence_grounded" in _checks(
        _state(evidence_spans=[{"start_line": 3, "end_line": 2, "why": "x"}])
    )


def test_pasteable_solution_is_rejected():
    block = "\n".join(f"    line{i} = {i}" for i in range(MAX_CODE_BLOCK_LINES + 2))
    state = _state(explanation=f"Do this:\n```python\n{block}\n```")
    assert "no_solution_code" in _checks(state)


def test_a_short_illustrative_snippet_is_allowed():
    """Naming a technique with a line or two is fine; handing over a solution is not."""
    state = _state(explanation="Use a dict:\n```python\nseen = {}\n```")
    assert "no_solution_code" not in _checks(state)


def test_low_confidence_is_rejected():
    """Regression: a real run served a 0.15-confidence diagnosis with a wrong label.

    Every check passed, because none of them asked whether the diagnoser was sure. A
    rejection here routes it through retry-then-escalate rather than presenting a guess
    as a finding.
    """
    assert "confidence_floor" in _checks(_state(confidence=0.15))
    assert "confidence_floor" not in _checks(_state(confidence=MIN_CONFIDENCE))
    assert "confidence_floor" not in _checks(_state(confidence=0.9))


# ------------------------------------------------------------------ prompt contract


def test_the_fifth_check_is_wired_end_to_end():
    """A check is only real if it is in CHECK_NAMES, the schema, and the instructions.

    Missing any one of the three fails silently: absent from CHECK_NAMES it is never
    read, absent from `required` the model may omit it, and absent from the prompt the
    model is being asked for a judgement it was never briefed on.
    """
    assert "evidence_matches_pattern" in prompt.CHECK_NAMES
    assert "evidence_matches_pattern" in prompt.SCHEMA["properties"]
    assert "evidence_matches_pattern" in prompt.SCHEMA["required"]
    assert "evidence_matches_pattern" in prompt.INSTRUCTIONS


def test_every_declared_check_is_required_by_the_schema():
    for check in prompt.CHECK_NAMES:
        assert check in prompt.SCHEMA["required"], check


def test_pattern_signals_reach_the_verifier():
    """Check 5 is unanswerable without them, and they were not being passed before."""
    taxonomy = load_taxonomy()
    entry = taxonomy.get("complexity.missing_memoization")
    content = prompt.build_user_content(
        failure_type="tle",
        pattern_id=entry.id,
        pattern_family=entry.family,
        pattern_name=entry.name,
        pattern_signals=list(entry.signals),
        confidence=0.8,
        explanation="Recomputes subproblems.",
        evidence_spans=[{"start_line": 2, "end_line": 3, "why": "the loop"}],
        vaulted_code=CODE,
    )
    for signal in entry.signals:
        assert signal in content


@pytest.mark.parametrize("field", ["passed", "reason"])
def test_schema_keeps_its_reporting_fields(field):
    assert field in prompt.SCHEMA["required"]
