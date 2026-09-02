"""Seeding must be idempotent: the link table reflects current inputs, not history.

Regression test. `link_by_similarity` originally only ever inserted or updated, so
seeding once with `--no-embed` (tag-overlap links) and again with embeddings
(similarity links) left both sets in the table. The result depended on the order
someone happened to run commands in, and the extra links surfaced as recommendations
the current strategy would never have produced.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

import pytest

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://weakspot:weakspot@localhost:5433/weakspot"
)
os.environ.setdefault("ENV", "test")

from weakspot.db import ping  # noqa: E402

pytestmark = pytest.mark.skipif(not ping(), reason="no database available")

from weakspot.db import SessionLocal  # noqa: E402
from weakspot.ingest.seed import link_by_similarity  # noqa: E402
from weakspot.models import Pattern, PatternProblem, Problem  # noqa: E402


@contextmanager
def _scratch_session():
    """A session whose writes are always rolled back.

    These tests call the linker directly, and the linker regenerates every pair
    similarity endorses — including pairs recorded as rejected, which only
    `apply_overrides` removes afterwards. Committing that would resurrect rejected
    links and fail test_curation on the next run against the same database. It did.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def _has_embeddings(db) -> bool:
    return (
        db.query(Pattern).filter(Pattern.embedding.isnot(None)).count() > 0
        and db.query(Problem).filter(Problem.embedding.isnot(None)).count() > 0
    )


def test_similarity_linking_removes_links_it_no_longer_endorses():
    with _scratch_session() as db:
        if not _has_embeddings(db):
            pytest.skip("no embeddings seeded; run `make seed EMBED=1` first")

        pattern = db.query(Pattern).filter(Pattern.embedding.isnot(None)).first()
        problem = db.query(Problem).filter(Problem.embedding.isnot(None)).first()

        # Stand in for a link some earlier strategy wrote. Deliberately not curated.
        planted = (pattern.id, problem.id)
        if db.get(PatternProblem, planted) is None:
            db.add(
                PatternProblem(
                    pattern_id=pattern.id,
                    problem_id=problem.id,
                    strength=0.0,
                    curated=False,
                )
            )
            db.flush()

        link_by_similarity(db)

        survivor = db.get(PatternProblem, planted)
        # It may legitimately survive if similarity *would* produce it — in that case
        # the strength must have been rewritten, not left at the planted 0.0.
        if survivor is not None:
            assert survivor.strength > 0.0, (
                "a stale non-curated link survived with its original strength"
            )


def test_curated_links_survive_relinking():
    """The whole point of the curated flag: hand decisions outlive a re-seed."""
    with _scratch_session() as db:
        if not _has_embeddings(db):
            pytest.skip("no embeddings seeded; run `make seed EMBED=1` first")

        pattern = db.query(Pattern).filter(Pattern.embedding.isnot(None)).first()
        # A problem that similarity is very unlikely to pick for this pattern.
        problem = (
            db.query(Problem)
            .filter(Problem.embedding.isnot(None))
            .order_by(Problem.slug.desc())
            .first()
        )

        key = (pattern.id, problem.id)
        existing = db.get(PatternProblem, key)
        if existing is None:
            db.add(
                PatternProblem(
                    pattern_id=pattern.id,
                    problem_id=problem.id,
                    strength=0.5,
                    curated=True,
                )
            )
        else:
            existing.curated = True
        db.flush()

        link_by_similarity(db)

        assert db.get(PatternProblem, key) is not None, "a curated link was deleted"

        # Leave the table as we found it.
        row = db.get(PatternProblem, key)
        if existing is None and row is not None:
            db.delete(row)
