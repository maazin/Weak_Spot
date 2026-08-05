"""MCP server mounted at /mcp, plus a plain REST mirror for tests and curl.

`/mcp` speaks the real MCP protocol over Streamable HTTP, so Claude Desktop, Cursor and
any other MCP client can connect to it directly. The REST mirror under
`/api/v1/mcp-tools` calls exactly the same functions; it exists because exercising a
JSON-RPC session from the test suite obscures what is being asserted, and because a
plain POST is easier to debug against a deployed instance.

Both surfaces share the four functions below, so there is one implementation of each
tool and no way for the two to drift. Tool descriptions are written for a model to read,
arguments are constrained by schema rather than by prose, and every list is capped so a
tool call cannot blow out a client's context.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.applications import Starlette

from .config import get_settings
from .db import SessionLocal, get_db
from .models import PatternProblem, Problem, User
from .taxonomy import get_taxonomy

CAP = get_settings().mcp_list_cap

Difficulty = Literal["easy", "medium", "hard"]
Family = Literal["pattern_selection", "implementation", "complexity", "comprehension"]


class TokenRequired(Exception):
    """Raised by the shared logic; each surface renders it in its own idiom."""


# --------------------------------------------------------------------- shared logic


def _authenticate(db: Session, authorization: str | None) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise TokenRequired("an API token is required")
    user = db.query(User).filter(User.api_token == authorization[7:].strip()).one_or_none()
    if user is None:
        raise TokenRequired("invalid API token")
    return user


def search_problems(
    db: Session,
    pattern_id: str,
    difficulty: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    if pattern_id not in get_taxonomy():
        raise ValueError("unknown pattern_id")

    query = (
        db.query(Problem)
        .join(PatternProblem, PatternProblem.problem_id == Problem.id)
        .filter(PatternProblem.pattern_id == pattern_id)
    )
    if difficulty:
        query = query.filter(Problem.difficulty == difficulty)

    rows = (
        query.order_by(PatternProblem.curated.desc(), PatternProblem.strength.desc())
        .limit(max(1, min(limit, CAP)))
        .all()
    )
    return {
        "results": [
            {
                "slug": p.slug,
                "title": p.title,
                "difficulty": p.difficulty,
                "tags": list(p.tags),
                "url": p.url,
            }
            for p in rows
        ]
    }


def pattern_taxonomy(family: str | None = None) -> dict[str, Any]:
    taxonomy = get_taxonomy()
    entries = taxonomy.by_family(family) if family else taxonomy.entries
    return {
        "patterns": [
            {
                "id": e.id,
                "family": e.family,
                "name": e.name,
                "practice_tags": list(e.practice_tags),
            }
            for e in entries
        ]
    }


def weak_patterns(db: Session, user: User, limit: int = 10) -> dict[str, Any]:
    rows = db.execute(
        text(
            """
            SELECT d.pattern_id, COUNT(*) AS occurrences, MAX(s.created_at) AS last_seen
              FROM diagnoses d
              JOIN submissions s ON s.id = d.submission_id
             WHERE s.user_id = :uid
             GROUP BY d.pattern_id
             ORDER BY occurrences DESC
             LIMIT :limit
            """
        ),
        {"uid": user.id, "limit": max(1, min(limit, CAP))},
    ).fetchall()

    taxonomy = get_taxonomy()
    return {
        "items": [
            {
                "pattern_id": pattern_id,
                "name": entry.name if (entry := taxonomy.get(pattern_id)) else pattern_id,
                "family": entry.family if entry else None,
                "occurrences": int(occurrences),
                "last_seen_at": last_seen.isoformat() if last_seen else None,
            }
            for pattern_id, occurrences, last_seen in rows
        ]
    }


# ------------------------------------------------------------------- MCP protocol

mcp = MCPServer(
    name="weakspot",
    title="Weakspot",
    version="0.1.0",
    instructions=(
        "Weakspot diagnoses why a coding-problem attempt failed at the conceptual level "
        "and recommends problems that drill the same failure pattern. Call "
        "get_pattern_taxonomy first to learn the valid pattern ids, then "
        "search_problems_by_pattern to find practice problems. Problem statements are "
        "never returned — only metadata and a link to the original."
    ),
)


@mcp.tool(
    name="search_problems_by_pattern",
    title="Search problems by failure pattern",
)
def _search_problems_by_pattern(
    pattern_id: Annotated[
        str,
        Field(
            description=(
                "A taxonomy pattern id, e.g. "
                "'implementation.binary_search_bounds_off_by_one'. Call "
                "get_pattern_taxonomy for the valid ids."
            )
        ),
    ],
    difficulty: Annotated[
        Difficulty | None, Field(description="Optional difficulty filter.")
    ] = None,
    limit: Annotated[
        int, Field(ge=1, le=CAP, description=f"Maximum results, capped at {CAP}.")
    ] = 5,
) -> dict[str, Any]:
    """Find practice problems that exercise a specific conceptual failure pattern.

    Use this when a user has been diagnosed with a pattern and wants problems that drill
    the same idea. Returns problem metadata and a link to the original problem — never
    the problem statement itself.
    """
    with SessionLocal() as db:
        return search_problems(db, pattern_id, difficulty, limit)


@mcp.tool(name="get_pattern_taxonomy", title="List the failure-pattern taxonomy")
def _get_pattern_taxonomy(
    family: Annotated[Family | None, Field(description="Optional: restrict to one family.")] = None,
) -> dict[str, Any]:
    """List the closed set of conceptual failure patterns Weakspot can diagnose.

    Patterns are grouped into four families: pattern_selection (wrong algorithmic shape),
    implementation (right shape, wrong details), complexity (correct but too slow), and
    comprehension (misread the problem). Call this before search_problems_by_pattern to
    learn the valid pattern ids.
    """
    return pattern_taxonomy(family)


@mcp.tool(name="get_my_weak_patterns", title="Get the caller's recurring weak patterns")
def _get_my_weak_patterns(
    ctx: Context,
    limit: Annotated[
        int, Field(ge=1, le=CAP, description=f"Maximum patterns, capped at {CAP}.")
    ] = 10,
) -> dict[str, Any]:
    """Return the authenticated user's recurring failure patterns, most frequent first.

    Includes occurrence counts and when each was last seen. Requires an API token sent as
    an Authorization: Bearer header. Use this to tailor practice recommendations to what
    this specific user keeps getting wrong.
    """
    headers = ctx.headers or {}
    authorization = headers.get("authorization") or headers.get("Authorization")
    with SessionLocal() as db:
        try:
            user = _authenticate(db, authorization)
        except TokenRequired as exc:
            # Surfaced to the client as a tool error, which is how MCP reports a failed
            # call — there is no HTTP status code to return at this layer.
            raise ValueError(str(exc)) from exc
        return weak_patterns(db, user, limit)


def mcp_app() -> Starlette:
    """Build the Streamable HTTP ASGI app. Mounted at /mcp, so the path here is root.

    Each call constructs a fresh session manager, and a manager's `run()` may only be
    entered once, so this is called from the lifespan rather than at import — otherwise
    a second app startup in one process (every extra TestClient) dies on a reused
    manager.

    DNS-rebinding protection is off because it defaults to allowing only localhost
    Host headers, which is wrong for a mounted app served under a real domain. The
    parent app's CORS middleware restricts browser origins, and the one tool that
    exposes user data requires a bearer token regardless of origin.
    """
    return mcp.streamable_http_app(
        streamable_http_path="/",
        stateless_http=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )


# --------------------------------------------------------------------- REST mirror

router = APIRouter(prefix="/api/v1/mcp-tools", tags=["mcp"])


class SearchProblemsArgs(BaseModel):
    pattern_id: str = Field(description="A taxonomy pattern id.")
    difficulty: Difficulty | None = None
    limit: int = Field(default=5, ge=1, le=CAP)


class TaxonomyArgs(BaseModel):
    family: Family | None = None


class WeakPatternsArgs(BaseModel):
    limit: int = Field(default=10, ge=1, le=CAP)


@router.get("/tools")
async def list_tools() -> dict[str, Any]:
    """Mirror of MCP tools/list, read straight off the registered tools."""
    tools = await mcp.list_tools()
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                # Named input_schema on the model, inputSchema on the wire.
                "inputSchema": t.input_schema,
            }
            for t in tools
        ]
    }


@router.post("/tools/search_problems_by_pattern")
def rest_search_problems(args: SearchProblemsArgs, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        return search_problems(db, args.pattern_id, args.difficulty, args.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tools/get_pattern_taxonomy")
def rest_pattern_taxonomy(args: TaxonomyArgs | None = None) -> dict[str, Any]:
    return pattern_taxonomy(args.family if args else None)


@router.post("/tools/get_my_weak_patterns")
def rest_weak_patterns(
    args: WeakPatternsArgs | None = None,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        user = _authenticate(db, authorization)
    except TokenRequired as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return weak_patterns(db, user, args.limit if args else 10)
