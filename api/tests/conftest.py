"""Test schema setup.

The app no longer creates its own tables, so the suite runs the migrations. That also
means every test run exercises the migration path — a migration that does not apply
cleanly fails the suite rather than being discovered on a deploy.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://weakspot:weakspot@localhost:5433/weakspot"
)
os.environ.setdefault("ENV", "test")


@pytest.fixture(scope="session", autouse=True)
def _migrate() -> None:
    """Bring the schema to head when a database is reachable.

    This deliberately does not skip when the database is down. It used to, and because
    it is autouse and session-scoped that skipped *every* test — including the taxonomy,
    scoring, cost, prompt and verifier tests, none of which touch Postgres. Running the
    suite without Docker produced an all-skipped run that looks green and asserts
    nothing.

    Modules that genuinely need the database carry their own
    `pytestmark = pytest.mark.skipif(not ping(), ...)`, so they still skip cleanly on
    their own terms.
    """
    from weakspot.db import ping, upgrade_to_head

    if ping():
        upgrade_to_head()
