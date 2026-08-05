"""GitHub OAuth, signed session cookies, and API tokens for MCP.

The dev bypass exists so the app is runnable and testable without registering an OAuth
application. It refuses to load in production — `get_settings()` raises at startup rather
than at first use, so a misconfigured deploy fails immediately instead of quietly
accepting unauthenticated sessions.
"""

from __future__ import annotations

import secrets

import httpx
from fastapi import Depends, HTTPException, Request, Response, status
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import User

GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_USER = "https://api.github.com/user"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().session_secret, salt="weakspot-session")


def issue_session(response: Response, user_id: str) -> None:
    settings = get_settings()
    token = _serializer().dumps({"uid": user_id})
    response.set_cookie(
        settings.session_cookie,
        token,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(get_settings().session_cookie, path="/")


def _user_id_from_cookie(request: Request) -> str | None:
    settings = get_settings()
    raw = request.cookies.get(settings.session_cookie)
    if not raw:
        return None
    try:
        payload = _serializer().loads(raw, max_age=settings.session_max_age)
    except BadSignature:
        return None
    return payload.get("uid")


def get_or_create_user(db: Session, *, github_id: str, handle: str) -> User:
    user = db.query(User).filter(User.github_id == github_id).one_or_none()
    if user is None:
        user = User(github_id=github_id, handle=handle, api_token=secrets.token_urlsafe(32))
        db.add(user)
        db.flush()
    else:
        user.handle = handle
    return user


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Session cookie, or a bearer API token for MCP clients."""
    user_id = _user_id_from_cookie(request)
    if user_id:
        user = db.get(User, user_id)
        if user is not None:
            return user

    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        user = db.query(User).filter(User.api_token == token).one_or_none()
        if user is not None:
            return user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    try:
        return current_user(request, db)
    except HTTPException:
        return None


def github_authorize_url(state: str) -> str:
    settings = get_settings()
    return (
        f"{GITHUB_AUTHORIZE}?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_callback_url}"
        f"&scope=read:user&state={state}"
    )


async def exchange_github_code(code: str) -> tuple[str, str]:
    """Swap the OAuth code for the GitHub id and handle."""
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.post(
            GITHUB_TOKEN,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_callback_url,
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="GitHub did not return a token")

        user_response = await client.get(
            GITHUB_USER,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        user_response.raise_for_status()
        payload = user_response.json()

    return str(payload["id"]), payload.get("login") or f"user{payload['id']}"
