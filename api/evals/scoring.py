"""Metric implementations shared by the four suites.

Written out rather than pulled from scikit-learn so the definitions in the README are
inspectable — a reader can check exactly what "macro F1" or "kappa" means here.
"""

from __future__ import annotations

from collections import Counter, defaultdict


def accuracy(pairs: list[tuple[str, str]]) -> float:
    """pairs of (true, predicted)."""
    if not pairs:
        return 0.0
    return sum(1 for t, p in pairs if t == p) / len(pairs)


def top_2_accuracy(triples: list[tuple[str, str, str | None]]) -> float:
    """(true, predicted, alternate) — counts a hit on either slot."""
    if not triples:
        return 0.0
    return sum(1 for t, p, a in triples if t == p or (a is not None and t == a)) / len(
        triples
    )


def per_class_f1(pairs: list[tuple[str, str]]) -> dict[str, float]:
    classes = {t for t, _ in pairs} | {p for _, p in pairs}
    scores: dict[str, float] = {}
    for cls in classes:
        tp = sum(1 for t, p in pairs if t == cls and p == cls)
        fp = sum(1 for t, p in pairs if t != cls and p == cls)
        fn = sum(1 for t, p in pairs if t == cls and p != cls)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        scores[cls] = (
            2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        )
    return scores


def macro_f1(pairs: list[tuple[str, str]]) -> float:
    """Macro over classes that actually appear as ground truth.

    Averaging over predicted-only classes would let a model inflate the score by
    never predicting a hard class.
    """
    truth_classes = {t for t, _ in pairs}
    if not truth_classes:
        return 0.0
    scores = per_class_f1(pairs)
    return sum(scores[c] for c in truth_classes) / len(truth_classes)


def confusion_matrix(pairs: list[tuple[str, str]]) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for true, predicted in pairs:
        matrix[true][predicted] += 1
    return {k: dict(v) for k, v in matrix.items()}


def cohens_kappa(pairs: list[tuple[int, int]]) -> float:
    """Cohen's kappa for two raters over the same items.

    Returns 0.0 when both raters are constant and identical: agreement is total but
    chance agreement is also total, so the statistic is undefined. Reporting 1.0 there
    would overstate a judge that simply always answers the same number.
    """
    if not pairs:
        return 0.0
    n = len(pairs)
    observed = sum(1 for a, b in pairs if a == b) / n

    a_counts = Counter(a for a, _ in pairs)
    b_counts = Counter(b for _, b in pairs)
    categories = set(a_counts) | set(b_counts)
    expected = sum((a_counts[c] / n) * (b_counts[c] / n) for c in categories)

    if expected >= 1.0:
        return 0.0
    return (observed - expected) / (1 - expected)


def exact_agreement(pairs: list[tuple[int, int]]) -> float:
    if not pairs:
        return 0.0
    return sum(1 for a, b in pairs if a == b) / len(pairs)


def adjacent_agreement(pairs: list[tuple[int, int]]) -> float:
    """Within one point — the usual bar for ordinal rubric scoring."""
    if not pairs:
        return 0.0
    return sum(1 for a, b in pairs if abs(a - b) <= 1) / len(pairs)


def precision_at_k(retrieved: list[str], relevant: set[str], k: int = 3) -> float:
    if k == 0:
        return 0.0
    top = retrieved[:k]
    if not top:
        return 0.0
    return sum(1 for item in top if item in relevant) / k


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for position, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / position
    return 0.0


def mean_reciprocal_rank(runs: list[tuple[list[str], set[str]]]) -> float:
    if not runs:
        return 0.0
    return sum(reciprocal_rank(r, rel) for r, rel in runs) / len(runs)
