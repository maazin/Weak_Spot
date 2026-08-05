"""The golden sets have to be well-formed before any suite result means anything."""

from __future__ import annotations

from collections import Counter

import pytest

from evals import fixtures
from weakspot.graph.intake import vault
from weakspot.models import FAILURE_TYPES, LANGUAGES
from weakspot.taxonomy import load_taxonomy


@pytest.fixture(scope="module")
def taxonomy():
    return load_taxonomy()


@pytest.fixture(scope="module")
def problem_slugs():
    from weakspot.ingest.seed import load_seed

    return {rec["slug"] for rec in load_seed()}


# --------------------------------------------------------------------------- Suite A


def test_suite_a_meets_the_specified_size():
    assert len(fixtures.suite_a()) >= 120


def test_suite_a_ids_unique():
    ids = [c["id"] for c in fixtures.suite_a()]
    assert len(ids) == len(set(ids))


def test_suite_a_labels_are_inside_the_taxonomy(taxonomy):
    for case in fixtures.suite_a():
        assert case["pattern_id"] in taxonomy, f"{case['id']} -> {case['pattern_id']}"


def test_suite_a_covers_every_pattern_at_least_twice(taxonomy):
    """Spec: at least two examples per taxonomy entry."""
    counts = Counter(c["pattern_id"] for c in fixtures.suite_a())
    thin = sorted(p for p in taxonomy.allowed_ids() if counts[p] < 2)
    assert not thin, f"patterns with fewer than two labelled examples: {thin}"


def test_suite_a_spans_all_four_families(taxonomy):
    families = {taxonomy.family_of(c["pattern_id"]) for c in fixtures.suite_a()}
    assert families == {
        "pattern_selection",
        "implementation",
        "complexity",
        "comprehension",
    }


def test_suite_a_fields_are_valid(problem_slugs):
    for case in fixtures.suite_a():
        assert case["failure_type"] in FAILURE_TYPES, case["id"]
        assert case["language"] in LANGUAGES, case["id"]
        assert case["code"].strip(), case["id"]
        assert case["problem_slug"] in problem_slugs, (
            f"{case['id']} references {case['problem_slug']}, which is not in the index"
        )


def test_suite_a_spans_multiple_languages():
    languages = {c["language"] for c in fixtures.suite_a()}
    assert len(languages) >= 4


# --------------------------------------------------------------------------- Suite B


def test_suite_b_size_and_shape():
    cases = fixtures.suite_b()
    assert len(cases) >= 60
    for case in cases:
        human = case["human"]
        for dimension in ("clarity", "correctness", "avoids_solution"):
            assert 1 <= human[dimension] <= 5, case["explanation"][:40]


def test_suite_b_labels_are_inside_the_taxonomy(taxonomy):
    for case in fixtures.suite_b():
        assert case["pattern_id"] in taxonomy


def test_suite_b_spans_the_rating_scale():
    """A calibration set of only 5s yields a meaningless kappa."""
    for dimension in ("clarity", "correctness", "avoids_solution"):
        values = {c["human"][dimension] for c in fixtures.suite_b()}
        assert len(values) >= 3, f"{dimension} ratings are not spread across the scale"


def test_suite_b_includes_solution_leaking_examples():
    leaking = [c for c in fixtures.suite_b() if c["human"]["avoids_solution"] <= 2]
    assert len(leaking) >= 5


# --------------------------------------------------------------------------- Suite C


def test_suite_c_size_and_shape(taxonomy, problem_slugs):
    pairs = fixtures.suite_c()
    assert len(pairs) >= 100
    for pair in pairs:
        assert pair["pattern_id"] in taxonomy
        assert pair["problem_slug"] in problem_slugs, pair["problem_slug"]
        assert isinstance(pair["relevant"], bool)


def test_suite_c_has_both_classes():
    pairs = fixtures.suite_c()
    positives = sum(1 for p in pairs if p["relevant"])
    assert 0 < positives < len(pairs)
    # Negatives must be a real fraction or precision@3 is trivially satisfiable.
    assert (len(pairs) - positives) >= 20


def test_suite_c_pairs_unique():
    keys = [(p["pattern_id"], p["problem_slug"]) for p in fixtures.suite_c()]
    assert len(keys) == len(set(keys))


# --------------------------------------------------------------------------- Suite D


def test_suite_d_size():
    assert len(fixtures.suite_d()) == 40


def test_suite_d_ids_unique():
    ids = [c["id"] for c in fixtures.suite_d()]
    assert len(ids) == len(set(ids))


def test_suite_d_covers_all_four_attack_classes():
    attacks = {c["attack"] for c in fixtures.suite_d()}
    assert attacks == {
        "instruction_override",
        "taxonomy_exfiltration",
        "forced_confidence",
        "forced_solution",
    }


def test_suite_d_covers_every_injection_vector():
    """Spec: payloads in comments, string literals, variable names, and docstrings."""
    vectors = {c["vector"] for c in fixtures.suite_d()}
    for required in ("line_comment", "block_comment", "docstring", "string_literal", "identifier"):
        assert required in vectors, f"no Suite D case uses the {required} vector"


def test_suite_d_forced_patterns_are_real_ids(taxonomy):
    for case in fixtures.suite_d():
        forced = case.get("forced_pattern_id")
        if forced is not None:
            assert forced in taxonomy, case["id"]


def test_suite_d_comment_and_string_payloads_are_neutralised_by_vaulting():
    """The comment/string vectors must not survive intake at all."""
    vaultable = {"line_comment", "block_comment", "docstring", "string_literal", "fstring"}
    for case in fixtures.suite_d():
        if case["vector"] not in vaultable:
            continue
        vaulted, _ = vault(case["code"], case["language"])
        lowered = vaulted.lower()
        for marker in ("ignore", "instruction", "override", "system", "confidence"):
            assert marker not in lowered, (
                f"{case['id']} leaks {marker!r} past vaulting: {vaulted[:120]!r}"
            )


def test_suite_d_identifier_payloads_survive_vaulting_by_design():
    """Identifier attacks are exactly what verifier check 4 exists to catch.

    If vaulting ever did neutralise these, the suite would stop measuring the
    verifier's contribution, so this asserts the threat model rather than a fix.
    """
    identifier_cases = [c for c in fixtures.suite_d() if c["vector"] == "identifier"]
    assert identifier_cases
    for case in identifier_cases:
        vaulted, _ = vault(case["code"], case["language"])
        assert any(
            token in vaulted.lower()
            for token in ("ignore", "override", "system", "please", "confidence")
        ), case["id"]
