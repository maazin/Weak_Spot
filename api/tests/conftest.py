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
    from weakspot.db import ping, upgrade_to_head

    if not ping():
        pytest.skip("database unreachable", allow_module_level=True)
    upgrade_to_head()
