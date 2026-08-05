"""FastAPI application. All routes under /api/v1; MCP mounted at /mcp."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from . import metrics, ratelimit
from .config import get_settings
from .db import engine, init_extensions, ping
from .models import Base
from .routers import auth_routes, catalog, reviews, submissions
from .schemas import HealthOut
from .taxonomy import get_taxonomy

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    # Loading the taxonomy at startup means a malformed file fails the deploy rather
    # than the first diagnosis.
    taxonomy = get_taxonomy()
    logger.info("taxonomy loaded: %d patterns", len(taxonomy))

    try:
        init_extensions()
        Base.metadata.create_all(engine)
    except Exception:
        logger.exception("database not ready; /healthz will report it")

    if settings.dev_auth_bypass:
        logger.warning("DEV_AUTH_BYPASS is enabled — never do this in production")

    yield


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

# MCP is mounted outside the versioned prefix, per spec.
from .mcp_server import router as mcp_router  # noqa: E402

app.include_router(mcp_router)


@app.get("/healthz", response_model=HealthOut, tags=["ops"])
def healthz() -> HealthOut:
    database_ok = ping()
    redis_ok = ratelimit.ping()
    return HealthOut(
        status="ok" if database_ok else "degraded",
        database=database_ok,
        redis=redis_ok,
        taxonomy_entries=len(get_taxonomy()),
    )


@app.get("/metrics", response_class=PlainTextResponse, tags=["ops"])
def prometheus_metrics() -> PlainTextResponse:
    return PlainTextResponse(
        metrics.render(), media_type="text/plain; version=0.0.4; charset=utf-8"
    )
