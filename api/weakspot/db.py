"""Engine, session factory, and schema bootstrap."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings

_settings = get_settings()

engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_extensions() -> None:
    """pgvector lives in the same Postgres instance; no separate vector service.

    The initial migration creates both extensions, so this is only needed by tooling
    that touches the database before migrations have ever run.
    """
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))


def _alembic_config() -> Config:
    root = Path(__file__).resolve().parent.parent
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "weakspot" / "migrations"))
    config.set_main_option("sqlalchemy.url", _settings.database_url)
    return config


def upgrade_to_head() -> None:
    """Bring the database to the latest revision. Used by tooling and tests."""
    command.upgrade(_alembic_config(), "head")


def schema_is_current() -> bool | None:
    """True at head, False if migrations are pending, None if the DB is unreachable.

    Reported by /healthz so a deploy that skipped its migration step is visible rather
    than surfacing later as a confusing query error.
    """
    try:
        head = ScriptDirectory.from_config(_alembic_config()).get_current_head()
        with engine.connect() as conn:
            current = MigrationContext.configure(conn).get_current_revision()
        return current == head
    except Exception:
        return None


def ping() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
