from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx
import jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from jwt import PyJWKClient

from .config import settings
from .context import current_user_id
from .mongo import col

COOKIE = "okbot_session"
STATE_COOKIE = "okbot_oauth_state"
SESSION_DAYS = 14

_jwks: PyJWKClient | None = None


def enabled() -> bool:
    return bool(
        settings.cognito_user_pool_id
        and settings.cognito_client_id
        and settings.cognito_domain
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _issuer() -> str:
    return f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}"


def _jwks_client() -> PyJWKClient:
    global _jwks
    if _jwks is None:
        url = f"{_issuer()}/.well-known/jwks.json"
        _jwks = PyJWKClient(url, cache_jwk_set=True)
    return _jwks


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
    configured = (settings.cognito_redirect_uri or "").strip()
    if configured:
        return configured
    return str(request.base_url).rstrip("/") + "/api/auth/callback"


def _app_origin(request: Request) -> str:
    configured = (settings.cognito_redirect_uri or "").strip()
    if configured:
        from urllib.parse import urlsplit
        parsed = urlsplit(configured)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    return str(request.base_url).rstrip("/")


def _cognito_authorize_url(request: Request, state: str) -> str:
    params = {
        "client_id": settings.cognito_client_id,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": redirect_uri(request),
        "identity_provider": "Google",
        "state": state,
        "prompt": "select_account",
    }
    domain = settings.cognito_domain.replace("https://", "").rstrip("/")
    return f"https://{domain}/oauth2/authorize?{urlencode(params)}"


async def _google_url_with_account_picker(cognito_authorize: str) -> str | None:
    """Cognito nem sempre repassa prompt=select_account ao Google. Tenta injetar direto."""
    import logging
    _log = logging.getLogger("okbot.auth")
    _log.info(f"[AUTH] Cognito URL: {cognito_authorize[:200]}")
    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=8.0) as client:
            res = await client.get(
                cognito_authorize,
                headers={"User-Agent": "Mozilla/5.0"},
            )
        loc = res.headers.get("location") or ""
        _log.info(f"[AUTH] Cognito redirect status={res.status_code} location={loc[:200]}")
        if "accounts.google.com" not in loc:
            return None
        parsed = urlparse(loc)
        query = parse_qs(parsed.query, keep_blank_values=True)
        query["prompt"] = ["select_account"]
        flat = {key: values[-1] for key, values in query.items()}
        final = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(flat), "")
        )
        _log.info(f"[AUTH] Google URL with picker: {final[:200]}")
        return final
    except Exception:
        return None


async def login_url(request: Request) -> str:
    state = secrets.token_urlsafe(24)
    request.state.oauth_state = state
    cognito = _cognito_authorize_url(request, state)
    # Tenta pegar URL direta do Google com account picker
    google_url = await _google_url_with_account_picker(cognito)
    if google_url:
        return google_url
    # Fallback: URL do Cognito com identity_provider=Google (vai direto sem hosted UI)
    return cognito


def logout_url(request: Request) -> str:
    domain = settings.cognito_domain.replace("https://", "").rstrip("/")
    params = {
        "client_id": settings.cognito_client_id,
        "logout_uri": _app_origin(request) + "/",
    }
    return f"https://{domain}/logout?{urlencode(params)}"


def _decode_id_token(id_token: str) -> dict[str, Any]:
    key = _jwks_client().get_signing_key_from_jwt(id_token)
    return jwt.decode(
        id_token,
        key.key,
        algorithms=["RS256"],
        audience=settings.cognito_client_id,
        issuer=_issuer(),
    )


async def exchange_code(request: Request, code: str) -> dict[str, Any]:
    domain = settings.cognito_domain.replace("https://", "").rstrip("/")
    url = f"https://{domain}/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.cognito_client_id,
        "code": code,
        "redirect_uri": redirect_uri(request),
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if res.status_code >= 400:
        raise HTTPException(400, "não foi possível concluir o login Google")
    body = res.json()
    id_token = str(body.get("id_token") or "")
    if not id_token:
        raise HTTPException(400, "Cognito não devolveu id_token")
    return _decode_id_token(id_token)


def upsert_user(claims: dict[str, Any]) -> dict[str, Any]:
    sub = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip().lower()
    if not sub or not email:
        raise HTTPException(400, "login Google sem e-mail — permita o e-mail na conta Google")
    now = _now().isoformat(timespec="seconds")
    existing = col("users").find_one({"$or": [{"user_id": sub}, {"email": email}]})
    user_id = str((existing or {}).get("user_id") or sub)
    doc = {
        "user_id": user_id,
        "email": email,
        "name": str(claims.get("name") or claims.get("given_name") or email.split("@")[0]),
        "picture": str(claims.get("picture") or ""),
        "cognito_sub": sub,
        "provider": "google",
        "updated_at": now,
    }
    if not existing:
        doc["created_at"] = now
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


enabled = enabled
user_from_request = user_from_request
unauthorized = unauthorized
bind_user = bind_user
login_url = login_url
set_state_cookie = set_state_cookie
exchange_code = exchange_code
upsert_user = upsert_user
create_session = create_session
set_session_cookie = set_session_cookie
public_user = public_user
drop_session = drop_session
logout_url = logout_url
clear_session_cookie = clear_session_cookie
