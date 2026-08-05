"""FastAPI application. All routes under /api/v1; MCP mounted at /mcp."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from . import metrics, ratelimit
from .config import get_settings
from .db import ping, schema_is_current
from .mcp_server import mcp_app
from .mcp_server import router as mcp_tools_router
from .routers import auth_routes, catalog, reviews, submissions
from .schemas import HealthOut
from .taxonomy import get_taxonomy

if TYPE_CHECKING:
    from starlette.applications import Starlette

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


class _MCPMount:
    """Delegates /mcp to the app the current lifespan built.

    The mount has to exist at import time for routing, but the MCP session manager
    inside it is single-use, so the app itself is rebuilt on every startup and swapped
    in here. Without the indirection a second startup in one process reuses a spent
    manager and every MCP request fails.
    """

    def __init__(self) -> None:
        self.inner: Starlette | None = None

    async def __call__(self, scope, receive, send) -> None:
        if self.inner is None:
            raise RuntimeError("the MCP app is unavailable; the lifespan did not run")
        await self.inner(scope, receive, send)


_mcp_mount = _MCPMount()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    # Loading the taxonomy at startup means a malformed file fails the deploy rather
    # than the first diagnosis.
    taxonomy = get_taxonomy()
    logger.info("taxonomy loaded: %d patterns", len(taxonomy))

    # The app does not create its own schema. `alembic upgrade head` owns that, so a
    # deployed database can be migrated deliberately instead of being mutated by
    # whichever process happened to boot first.
    current = schema_is_current()
    if current is None:
        logger.error("database unreachable or schema unreadable; /healthz will report it")
    elif not current:
        logger.error("database schema is behind; run 'alembic upgrade head'")

    if settings.dev_auth_bypass:
        logger.warning("DEV_AUTH_BYPASS is enabled — never do this in production")

    # Starlette does not run a mounted app's lifespan, so the MCP session manager has to
    # be started here or every /mcp request fails on an unstarted task group.
    inner = mcp_app()
    _mcp_mount.inner = inner
    try:
        async with inner.router.lifespan_context(inner):
            yield
    finally:
        _mcp_mount.inner = None


app = FastAPI(
    title="Weakspot",
    description=(
        "Diagnoses why a failed coding-problem attempt failed at the conceptual level, "
        "then schedules same-pattern problems for spaced review."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

v1 = APIRouter(prefix="/api/v1")
v1.include_router(auth_routes.router)
v1.include_router(submissions.router)
v1.include_router(reviews.router)
v1.include_router(catalog.router)
app.include_router(v1)

# The REST mirror of the MCP tools. Lives under /api/v1 so it cannot shadow the mount
# below, which has to own /mcp outright for clients to find it.
app.include_router(mcp_tools_router)

# The real MCP endpoint, outside the versioned prefix per spec. An MCP client is
# configured with this URL and speaks Streamable HTTP to it.
app.mount("/mcp", _mcp_mount)


@app.get("/healthz", response_model=HealthOut, tags=["ops"])
def healthz() -> HealthOut:
    database_ok = ping()
    redis_ok = ratelimit.ping()
    migrated = schema_is_current()
    return HealthOut(
        status="ok" if database_ok and migrated else "degraded",
        database=database_ok,
        redis=redis_ok,
        schema_current=bool(migrated),
        taxonomy_entries=len(get_taxonomy()),
    )


@app.get("/metrics", response_class=PlainTextResponse, tags=["ops"])
def prometheus_metrics() -> PlainTextResponse:
    return PlainTextResponse(
        metrics.render(), media_type="text/plain; version=0.0.4; charset=utf-8"
    )
