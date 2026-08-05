"""SM-2 with the reduced parameter set (spec section 5)."""

from __future__ import annotations

import pytest

from weakspot.graph.scheduler import (
    EASE_FLOOR,
    INITIAL_EASE,
    INITIAL_INTERVAL_DAYS,
    next_schedule,
)


def test_success_multiplies_interval_by_ease():
    interval, ease, reps = next_schedule(
        result="solved",
        interval_days=INITIAL_INTERVAL_DAYS,
        ease=INITIAL_EASE,
        repetitions=0,
    )
    assert interval == pytest.approx(7.5)
    assert ease == INITIAL_EASE
    assert reps == 1


def test_failure_resets_interval_and_decrements_ease():
    interval, ease, reps = next_schedule(
        result="failed", interval_days=30.0, ease=2.5, repetitions=4
    )
    assert interval == 1.0
    assert ease == pytest.approx(2.3)
    assert reps == 0


def test_ease_is_floored():
    ease = 2.5
    for _ in range(20):
        _, ease, _ = next_schedule(
            result="failed", interval_days=10.0, ease=ease, repetitions=1
        )
    assert ease == pytest.approx(EASE_FLOOR)


def test_skip_moves_the_item_without_penalising_ease():
    """Putting something off should not permanently punish that pattern's schedule."""
    interval, ease, reps = next_schedule(
        result="skipped", interval_days=12.0, ease=2.5, repetitions=3
    )
    assert interval == 1.0
    assert ease == 2.5
    assert reps == 3


def test_repeated_success_grows_the_interval():
    interval, ease, reps = INITIAL_INTERVAL_DAYS, INITIAL_EASE, 0
    for _ in range(4):
        interval, ease, reps = next_schedule(
            result="solved", interval_days=interval, ease=ease, repetitions=reps
        )
    assert interval > 100
    assert reps == 4


def test_unknown_result_rejected():
    with pytest.raises(ValueError):
        next_schedule(result="maybe", interval_days=3.0, ease=2.5, repetitions=0)
