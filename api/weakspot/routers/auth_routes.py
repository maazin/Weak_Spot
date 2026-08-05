"""GitHub OAuth flow, session, and the dev bypass."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import (
    clear_session,
    current_user,
    exchange_github_code,
    get_or_create_user,
    github_authorize_url,
    issue_session,
)
from ..config import get_settings
from ..db import get_db
from ..models import User
from ..schemas import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

_STATE_COOKIE = "weakspot_oauth_state"


@router.get("/github/start")
def github_start() -> RedirectResponse:
    settings = get_settings()
    if not settings.github_client_id:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")

    state = secrets.token_urlsafe(24)
    response = RedirectResponse(github_authorize_url(state))
    response.set_cookie(
        _STATE_COOKIE,
        state,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
    )
    return response


@router.get("/github/callback")
async def github_callback(
    request: Request, code: str, state: str, db: Session = Depends(get_db)
) -> RedirectResponse:
    settings = get_settings()
    expected = request.cookies.get(_STATE_COOKIE)
    if not expected or not secrets.compare_digest(expected, state):
        raise HTTPException(status_code=400, detail="OAuth state mismatch")

    github_id, handle = await exchange_github_code(code)
    user = get_or_create_user(db, github_id=github_id, handle=handle)
    db.commit()

    response = RedirectResponse(settings.web_origin)
    response.delete_cookie(_STATE_COOKIE)
    issue_session(response, user.id)
    return response


@router.post("/dev-login", response_model=UserOut)
def dev_login(response: Response, db: Session = Depends(get_db)) -> UserOut:
    """Mint a local session without GitHub.

    Refused unless DEV_AUTH_BYPASS is on, and `get_settings()` refuses to construct at
    all when the bypass is enabled in production — so this cannot be reached there even
    if the flag is set by accident.
    """
    settings = get_settings()
    if not settings.dev_auth_bypass:
        raise HTTPException(status_code=404, detail="not found")

    user = get_or_create_user(db, github_id="dev-local", handle="dev")
    db.commit()
    issue_session(response, user.id)
    return UserOut(id=user.id, handle=user.handle)


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    clear_session(response)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut(id=user.id, handle=user.handle)


@router.post("/token/rotate")
def rotate_token(
    db: Session = Depends(get_db), user: User = Depends(current_user)
) -> dict[str, str]:
    """Rotate the API token used by MCP clients."""
    import secrets as _secrets

    user.api_token = _secrets.token_urlsafe(32)
    db.commit()
    return {"api_token": user.api_token}
