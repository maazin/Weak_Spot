"""MCP server mounted at /mcp — three tools, all responses bounded.

Tool descriptions are written for a model to read, arguments are constrained, and every
list is capped at 20 items so a tool call cannot blow out a client's context.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import PatternProblem, Problem, User
from .taxonomy import get_taxonomy

router = APIRouter(prefix="/mcp", tags=["mcp"])

CAP = get_settings().mcp_list_cap


class SearchProblemsArgs(BaseModel):
    pattern_id: str = Field(
        description="A taxonomy pattern id, e.g. 'implementation.binary_search_bounds_off_by_one'."
    )
    difficulty: str | None = Field(
        default=None, description="Optional filter: 'easy', 'medium', or 'hard'."
    )
    limit: int = Field(default=5, ge=1, le=CAP, description=f"Max results, up to {CAP}.")


TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_problems_by_pattern",
        "description": (
            "Find practice problems that exercise a specific conceptual failure pattern "
            "from the Weakspot taxonomy. Use this when a user has been diagnosed with a "
            "pattern and wants problems that drill the same idea. Returns problem "
            "metadata and a link to the original problem — never the problem statement."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern_id": {
                    "type": "string",
                    "description": "A taxonomy pattern id. Call get_pattern_taxonomy for valid ids.",
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["easy", "medium", "hard"],
                    "description": "Optional difficulty filter.",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": CAP,
                    "description": f"Maximum results to return, capped at {CAP}.",
                },
            },
            "required": ["pattern_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_pattern_taxonomy",
        "description": (
            "List the closed set of conceptual failure patterns Weakspot can diagnose, "
            "grouped into four families: pattern_selection (wrong algorithmic shape), "
            "implementation (right shape, wrong details), complexity (correct but too "
            "slow), and comprehension (misread the problem). Call this before "
            "search_problems_by_pattern to learn the valid pattern ids."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "family": {
                    "type": "string",
                    "enum": [
                        "pattern_selection",
                        "implementation",
                        "complexity",
                        "comprehension",
                    ],
                    "description": "Optional: restrict to one family.",
                }
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_my_weak_patterns",
        "description": (
            "Return the authenticated user's recurring failure patterns, most frequent "
            "first, with occurrence counts and when each was last seen. Requires an API "
            "token. Use this to tailor practice recommendations to what this specific "
            "user keeps getting wrong."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": CAP,
                    "description": f"Maximum patterns to return, capped at {CAP}.",
                }
            },
            "additionalProperties": False,
        },
    },
]


def _require_token(db: Session, authorization: str | None) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="an API token is required")
    token = authorization[7:].strip()
    user = db.query(User).filter(User.api_token == token).one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="invalid API token")
    return user


@router.get("/tools")
def list_tools() -> dict[str, Any]:
    return {"tools": TOOLS}


@router.post("/tools/search_problems_by_pattern")
def search_problems_by_pattern(
    args: SearchProblemsArgs, db: Session = Depends(get_db)
) -> dict[str, Any]:
    if args.pattern_id not in get_taxonomy():
        raise HTTPException(status_code=400, detail="unknown pattern_id")

    query = (
        db.query(Problem)
        .join(PatternProblem, PatternProblem.problem_id == Problem.id)
        .filter(PatternProblem.pattern_id == args.pattern_id)
    )
    if args.difficulty:
        query = query.filter(Problem.difficulty == args.difficulty)

    rows = (
        query.order_by(PatternProblem.curated.desc(), PatternProblem.strength.desc())
        .limit(min(args.limit, CAP))
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


@router.post("/tools/get_pattern_taxonomy")
def get_pattern_taxonomy(payload: dict | None = None) -> dict[str, Any]:
    taxonomy = get_taxonomy()
    family = (payload or {}).get("family")
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


@router.post("/tools/get_my_weak_patterns")
def get_my_weak_patterns(
    payload: dict | None = None,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    user = _require_token(db, authorization)
    limit = min(int((payload or {}).get("limit", 10)), CAP)

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
        {"uid": user.id, "limit": limit},
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
