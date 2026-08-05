"""Phase 1 gate: every taxonomy entry is well-formed."""

from __future__ import annotations

import pytest

from weakspot.taxonomy import FAMILIES, PatternEntry, load_taxonomy


@pytest.fixture(scope="module")
def taxonomy():
    return load_taxonomy()


def test_loads_and_is_substantial(taxonomy):
    assert len(taxonomy) >= 40, "spec calls for roughly 40 failure modes"


def test_all_four_families_populated(taxonomy):
    for family in FAMILIES:
        assert len(taxonomy.by_family(family)) >= 8, f"{family} is thin"


def test_ids_unique_and_namespaced(taxonomy):
    ids = taxonomy.allowed_ids()
    assert len(ids) == len(set(ids))
    for pattern_id in ids:
        family, _, slug = pattern_id.partition(".")
        assert family in FAMILIES
        assert slug and slug.replace("_", "").isalnum()


def test_every_entry_has_checkable_signals(taxonomy):
    for e in taxonomy.entries:
        assert e.signals, f"{e.id} has no signals"
        for signal in e.signals:
            # Signals feed both the diagnoser prompt and the verifier's grounding check,
            # so a one-word signal is not actionable.
            assert len(signal.split()) >= 3, f"{e.id} signal is too terse: {signal!r}"


def test_correct_approach_is_original_prose_not_code(taxonomy):
    for e in taxonomy.entries:
        assert len(e.correct_approach) >= 120, f"{e.id} approach too short"
        assert "```" not in e.correct_approach, f"{e.id} approach contains a code block"


def test_related_patterns_resolve(taxonomy):
    for e in taxonomy.entries:
        for rel in e.related_patterns:
            assert rel in taxonomy, f"{e.id} -> {rel} does not resolve"


def test_practice_tags_present(taxonomy):
    for e in taxonomy.entries:
        assert e.practice_tags, f"{e.id} has no practice tags"


def test_prompt_block_is_deterministic(taxonomy):
    """An unstable block destroys the prompt cache hit rate."""
    assert taxonomy.as_prompt_block() == taxonomy.as_prompt_block()
    block = taxonomy.as_prompt_block()
    for pattern_id in taxonomy.allowed_ids():
        assert pattern_id in block


def test_rejects_family_id_mismatch():
    with pytest.raises(ValueError):
        PatternEntry.model_validate(
            {
                "id": "complexity.some_slug",
                "family": "implementation",
                "name": "mismatched",
                "signals": ["a signal with words"],
                "correct_approach": "x" * 200,
                "practice_tags": ["array"],
            }
        )


def test_rejects_approach_containing_code():
    with pytest.raises(ValueError):
        PatternEntry.model_validate(
            {
                "id": "complexity.some_slug",
                "family": "complexity",
                "name": "has code",
                "signals": ["a signal with words"],
                "correct_approach": "Here is the fix: ```python\nreturn 1\n``` " + "x" * 200,
                "practice_tags": ["array"],
            }
        )
