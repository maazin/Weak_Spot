"""Golden fixture loaders for the four evaluation suites."""

from __future__ import annotations

from . import (
    suite_a_complexity,
    suite_a_comprehension,
    suite_a_implementation,
    suite_a_pattern_selection,
    suite_b_judge,
    suite_c_retrieval,
    suite_d_injection,
)


def suite_a() -> list[dict]:
    """120+ hand-labelled failing submissions."""
    return [
        *suite_a_pattern_selection.CASES,
        *suite_a_implementation.CASES,
        *suite_a_complexity.CASES,
        *suite_a_comprehension.CASES,
    ]


def suite_b() -> list[dict]:
    """60 human-rated explanations for judge calibration."""
    return list(suite_b_judge.CASES)


def suite_c() -> list[dict]:
    """100 labelled (pattern, problem) relevance pairs."""
    return list(suite_c_retrieval.PAIRS)


def suite_d() -> list[dict]:
    """40 adversarial submissions. Hard gate."""
    return list(suite_d_injection.CASES)


__all__ = ["suite_a", "suite_b", "suite_c", "suite_d"]
