"""The pair-curation workflow: export candidates, record decisions, apply them.

Generated links are approximations. These tests cover the mechanism that lets a human
overrule them and, more importantly, that a later reseed does not quietly undo the
correction.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from weakspot.db import SessionLocal
from weakspot.ingest.seed import (
    OVERRIDES_PATH,
    apply_overrides,
    export_for_review,
    load_overrides,
)
from weakspot.models import PatternProblem, Problem
from weakspot.taxonomy import load_taxonomy


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="module")
def seeded(db):
    """CI migrates but does not seed, so index-dependent assertions skip there."""
    if db.query(Problem).first() is None:
        pytest.skip("problem index not seeded; run `make seed`")
    return db


def test_overrides_file_is_wellformed():
    confirmed, rejected = load_overrides()
    # Both lists are keyed the same way and must not contradict each other.
    assert not (confirmed & rejected), "a pair is both confirmed and rejected"


def test_overrides_reference_real_patterns_and_problems(seeded):
    confirmed, rejected = load_overrides()
    if not confirmed and not rejected:
        pytest.skip("no curation decisions recorded yet")

    taxonomy = load_taxonomy()
    slugs = {slug for (slug,) in seeded.query(Problem.slug).all()}
    for pattern_id, slug in confirmed | rejected:
        assert pattern_id in taxonomy, f"unknown pattern in overrides: {pattern_id}"
        assert slug in slugs, f"unknown problem in overrides: {slug}"


def test_confirmed_pairs_are_curated_and_rejected_are_absent(seeded):
    """The seeded database must actually reflect the recorded decisions."""
    confirmed, rejected = load_overrides()
    if not confirmed:
        pytest.skip("no curation decisions recorded yet")

    ids = {slug: pid for pid, slug in seeded.query(Problem.id, Problem.slug).all()}

    for pattern_id, slug in confirmed:
        row = seeded.get(PatternProblem, (pattern_id, ids[slug]))
        assert row is not None, f"confirmed pair missing: {pattern_id} <- {slug}"
        assert row.curated, f"confirmed pair not marked curated: {pattern_id} <- {slug}"

    for pattern_id, slug in rejected:
        row = seeded.get(PatternProblem, (pattern_id, ids[slug]))
        assert row is None, f"rejected pair still linked: {pattern_id} <- {slug}"


def test_review_export_is_readable_and_bounded(db, tmp_path: Path):
    out = tmp_path / "candidates.yaml"
    count = export_for_review(db, out, top_n=25)
    assert count <= 25

    data = yaml.safe_load(out.read_text())["candidates"]
    assert len(data) == count
    for entry in data:
        # Enough context to judge a pair without opening the database.
        assert {"pattern_id", "pattern_name", "problem_slug", "problem_title"} <= entry.keys()

    # Already-decided pairs are not re-offered for review.
    confirmed, _ = load_overrides()
    offered = {(e["pattern_id"], e["problem_slug"]) for e in data}
    assert not (offered & confirmed)


def test_apply_overrides_is_idempotent(db):
    first = apply_overrides(db)
    second = apply_overrides(db)
    # Confirmations reapply harmlessly; rejections have nothing left to delete.
    assert second["confirmed"] == first["confirmed"]
    assert second["rejected"] == 0


def test_overrides_path_is_tracked_beside_the_taxonomy():
    """The decisions belong in git next to patterns.yaml, not in a scratch file."""
    assert OVERRIDES_PATH.exists()
    assert OVERRIDES_PATH.parent.name == "taxonomy"
