"""Autenticação direta com Google OAuth 2.0 (sem Cognito)."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from .config import settings
from .context import current_user_id
from .mongo import col

COOKIE = "okbot_session"
STATE_COOKIE = "okbot_oauth_state"
SESSION_DAYS = 14

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def enabled() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def init_auth_indexes() -> None:
    col("users").create_index("user_id", unique=True)
    col("users").create_index("email", unique=True)
    col("sessions").create_index("session_id", unique=True)
    col("sessions").create_index("expires_at", expireAfterSeconds=0)
    try:
        col("okx_accounts").drop_index("user_id_1")
    except Exception:
        pass
    try:
        col("okx_accounts").create_index("user_id", unique=True, sparse=True)
    except Exception:
        col("okx_accounts").create_index("user_id")
    col("bots").create_index("user_id")


def redirect_uri(request: Request) -> str:
    configured = (settings.google_redirect_uri or "").strip()
    if configured:
        return configured
    return str(request.base_url).rstrip("/") + "/api/auth/callback"


def _app_origin(request: Request) -> str:
    configured = (settings.google_redirect_uri or "").strip()
    if configured:
        from urllib.parse import urlsplit
        parsed = urlsplit(configured)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    return str(request.base_url).rstrip("/")


def login_url(request: Request) -> str:
    """Gera URL do Google OAuth com account picker."""
    state = secrets.token_urlsafe(24)
    request.state.oauth_state = state
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code(request: Request, code: str) -> dict[str, Any]:
    """Troca code por access_token e busca dados do usuário no Google."""
    data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code": code,
        "redirect_uri": redirect_uri(request),
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(GOOGLE_TOKEN_URL, data=data)
    if res.status_code >= 400:
        raise HTTPException(400, "Falha ao trocar código com Google")
    tokens = res.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(400, "Google não retornou access_token")

    # Buscar perfil do usuário
    async with httpx.AsyncClient(timeout=10.0) as client:
        user_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if user_res.status_code >= 400:
        raise HTTPException(400, "Falha ao buscar perfil Google")
    return user_res.json()


def upsert_user(userinfo: dict[str, Any]) -> dict[str, Any]:
    """Cria ou atualiza usuário a partir do Google userinfo."""
    google_id = str(userinfo.get("id") or "").strip()
    email = str(userinfo.get("email") or "").strip().lower()
    if not google_id or not email:
        raise HTTPException(400, "login Google sem e-mail")
    now = _now().isoformat(timespec="seconds")
    existing = col("users").find_one({"$or": [{"user_id": google_id}, {"email": email}]})
    user_id = str((existing or {}).get("user_id") or google_id)
    google_name = str(userinfo.get("name") or userinfo.get("given_name") or email.split("@")[0])
    # Preservar nome customizado se o usuário já editou
    name = google_name
    if existing and existing.get("name") and existing.get("name_edited"):
        name = existing["name"]
    doc = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "google_name": google_name,
        "picture": str(userinfo.get("picture") or ""),
        "google_id": google_id,
        "provider": "google",
        "updated_at": now,
    }
    if not existing:
        doc["created_at"] = now
        doc["name_edited"] = False
        col("users").insert_one(doc)
        _claim_legacy(user_id)
    else:
        col("users").update_one({"user_id": user_id}, {"$set": doc})
    doc.pop("_id", None)
    return {k: doc.get(k) or (existing or {}).get(k) for k in ("user_id", "email", "name", "picture")}


def _claim_legacy(user_id: str) -> None:
    """O primeiro usuário logado herda bots/chaves que ainda não têm dono."""
    if col("okx_accounts").count_documents({"user_id": user_id}) > 0:
        return
    if col("users").count_documents({}) > 1:
        return
    if col("okx_accounts").count_documents({"user_id": {"$nin": [None, "", user_id]}}) > 0:
        return
    q = {"$or": [{"user_id": {"$exists": False}}, {"user_id": None}, {"user_id": ""}]}
    for name in (
        "okx_accounts",
        "bots",
        "positions",
        "trades",
        "events",
        "executions",
        "order_origins",
        "portfolio_snapshots",
        "hunter_rotations",
        "hunter_cooldowns",
        "custom_strategies",
    ):
        col(name).update_many(q, {"$set": {"user_id": user_id}})
    for kind in ("hunter", "order_limits", "bot_defaults"):
        if col("settings").find_one({"_id": f"{kind}:{user_id}"}):
            continue
        old = col("settings").find_one({"_id": kind})
        if not old:
            continue
        doc = dict(old)
        doc["_id"] = f"{kind}:{user_id}"
        col("settings").insert_one(doc)


def create_session(user_id: str) -> str:
    sid = secrets.token_urlsafe(32)
    exp = _now() + timedelta(days=SESSION_DAYS)
    col("sessions").insert_one(
        {
            "session_id": sid,
            "user_id": user_id,
            "expires_at": exp,
            "created_at": _now(),
        }
    )
    return sid


def user_from_session(session_id: str | None) -> Optional[dict[str, Any]]:
    sid = (session_id or "").strip()
    if not sid:
        return None
    row = col("sessions").find_one({"session_id": sid})
    if not row:
        return None
    exp = row.get("expires_at")
    if isinstance(exp, datetime) and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if not exp or exp < _now():
        col("sessions").delete_one({"session_id": sid})
        return None
    user = col("users").find_one({"user_id": row.get("user_id")}, {"_id": 0})
    return user


def drop_session(session_id: str | None) -> None:
    sid = (session_id or "").strip()
    if sid:
        col("sessions").delete_one({"session_id": sid})


def public_user(user: dict[str, Any] | None) -> dict[str, Any]:
    if not user:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture") or "",
    }


def bind_user(user: dict[str, Any] | None):
    uid = str((user or {}).get("user_id") or "")
    return current_user_id.set(uid)


def user_from_request(request: Request) -> Optional[dict[str, Any]]:
    return user_from_session(request.cookies.get(COOKIE))


def set_session_cookie(response, session_id: str) -> None:
    response.set_cookie(
        COOKIE,
        session_id,
        httponly=True,
        samesite="lax",
        max_age=SESSION_DAYS * 86400,
        secure=bool(getattr(settings, "auth_cookie_secure", False)),
        path="/",
    )


def set_state_cookie(response, state: str) -> None:
    response.set_cookie(
        STATE_COOKIE,
        state,
        httponly=True,
        samesite="lax",
        max_age=600,
        secure=bool(getattr(settings, "auth_cookie_secure", False)),
        path="/",
    )


def clear_session_cookie(response) -> None:
    response.delete_cookie(COOKIE, path="/")
    response.delete_cookie(STATE_COOKIE, path="/")


def unauthorized() -> JSONResponse:
    return JSONResponse({"detail": "faça login com Google"}, status_code=401)
