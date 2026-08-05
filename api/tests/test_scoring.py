"""Metric definitions — the README quotes these, so they need to be right."""

from __future__ import annotations

import pytest

from evals import scoring


def test_accuracy():
    assert scoring.accuracy([("a", "a"), ("b", "b"), ("c", "x")]) == pytest.approx(2 / 3)
    assert scoring.accuracy([]) == 0.0


def test_top_2_accuracy_counts_the_alternate_slot():
    triples = [("a", "x", "a"), ("b", "b", None), ("c", "y", "z")]
    assert scoring.top_2_accuracy(triples) == pytest.approx(2 / 3)


def test_macro_f1_is_not_inflated_by_class_imbalance():
    """Nine easy hits and one missed rare class should not read as ~90%."""
    pairs = [("common", "common")] * 9 + [("rare", "common")]
    assert scoring.accuracy(pairs) == pytest.approx(0.9)
    assert scoring.macro_f1(pairs) < 0.6


def test_macro_f1_perfect():
    pairs = [("a", "a"), ("b", "b")]
    assert scoring.macro_f1(pairs) == pytest.approx(1.0)


def test_macro_f1_averages_over_truth_classes_only():
    """Predicting a class that never appears must not add a free 0 or 1."""
    pairs = [("a", "a"), ("a", "zzz")]
    assert set(scoring.per_class_f1(pairs)) == {"a", "zzz"}
    assert scoring.macro_f1(pairs) == pytest.approx(scoring.per_class_f1(pairs)["a"])


def test_confusion_matrix_counts():
    matrix = scoring.confusion_matrix([("a", "a"), ("a", "b"), ("b", "b")])
    assert matrix["a"] == {"a": 1, "b": 1}
    assert matrix["b"] == {"b": 1}


def test_kappa_perfect_agreement_with_spread():
    pairs = [(1, 1), (3, 3), (5, 5), (2, 2)]
    assert scoring.cohens_kappa(pairs) == pytest.approx(1.0)


def test_kappa_is_zero_for_chance_agreement():
    pairs = [(1, 1), (1, 2), (2, 1), (2, 2)]
    assert scoring.cohens_kappa(pairs) == pytest.approx(0.0, abs=1e-9)


def test_kappa_refuses_to_reward_a_constant_judge():
    """A judge that always answers 5 agrees perfectly and has learned nothing."""
    pairs = [(5, 5)] * 20
    assert scoring.cohens_kappa(pairs) == 0.0


def test_kappa_negative_when_worse_than_chance():
    pairs = [(1, 2), (2, 1), (1, 2), (2, 1)]
    assert scoring.cohens_kappa(pairs) < 0


def test_exact_and_adjacent_agreement():
    pairs = [(3, 3), (3, 4), (1, 5)]
    assert scoring.exact_agreement(pairs) == pytest.approx(1 / 3)
    assert scoring.adjacent_agreement(pairs) == pytest.approx(2 / 3)


def test_precision_at_k():
    assert scoring.precision_at_k(["a", "b", "c"], {"a", "c"}, 3) == pytest.approx(2 / 3)
    assert scoring.precision_at_k([], {"a"}, 3) == 0.0


def test_precision_at_k_divides_by_k_not_by_hits():
    """Returning one relevant item out of three is 1/3, not 1.0."""
    assert scoring.precision_at_k(["a", "x", "y"], {"a"}, 3) == pytest.approx(1 / 3)


def test_reciprocal_rank_and_mrr():
    assert scoring.reciprocal_rank(["x", "a"], {"a"}) == pytest.approx(0.5)
    assert scoring.reciprocal_rank(["x", "y"], {"a"}) == 0.0
    runs = [(["a"], {"a"}), (["x", "b"], {"b"})]
    assert scoring.mean_reciprocal_rank(runs) == pytest.approx(0.75)
