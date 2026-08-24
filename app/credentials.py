from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from .config import settings
from .context import current_user_id
from .mongo import BOT_ID, col

_legacy = {
    "okx_api_key": "",
    "okx_secret_key": "",
    "okx_passphrase": "",
    "okx_flag": "0",
    "account_id": "",
    "account_name": "",
}
_by_user: dict[str, dict[str, str]] = {}


def _empty() -> dict[str, str]:
    return dict(_legacy)


def _st() -> dict[str, str]:
    uid = current_user_id.get()
    if uid:
        if uid not in _by_user:
            hydrate_user(uid)
        return _by_user[uid]
    return _legacy


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _accounts():
    return col("okx_accounts")


def _uid() -> str:
    return current_user_id.get() or ""


def _auth_on() -> bool:
    from . import auth as authmod
    return authmod.enabled()


def _owner_q() -> dict[str, Any]:
    uid = _uid()
    if uid:
        return {"user_id": uid}
    if _auth_on():
        return {"user_id": "__none__"}
    return {}


def _active_setting_id() -> str:
    return f"okx_active_account:{_uid() or 'legacy'}"


def hydrate_user(user_id: str) -> None:
    uid = (user_id or "").strip()
    st = _by_user.setdefault(uid, _empty())
    for k in _empty():
        st[k] = ""
    row = col("settings").find_one({"_id": f"okx_active_account:{uid}"}) or {}
    aid = str(row.get("account_id") or "")
    acct = _accounts().find_one({"account_id": aid, "user_id": uid}) if aid else None
    if not acct:
        acct = _accounts().find_one({"user_id": uid}, sort=[("created_at", 1)])
    if acct:
        _apply_row_to(st, acct)


hydrate_user = hydrate_user


def _new_id() -> str:
    return "acct_" + secrets.token_hex(8)


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:4]}••••{value[-4:]}"


def _apply_row_to(st: dict[str, str], row: dict[str, Any] | None) -> None:
    if not row:
        return
    for key in ("okx_api_key", "okx_secret_key", "okx_passphrase", "okx_flag"):
        if row.get(key) is not None:
            st[key] = str(row.get(key) or "")
    if row.get("account_id"):
        st["account_id"] = str(row.get("account_id") or "")
    if row.get("name") is not None:
        st["account_name"] = str(row.get("name") or "")


def _apply_row(row: dict[str, Any] | None) -> None:
    _apply_row_to(_st(), row)


def _persist_legacy() -> None:
    if _uid():
        return
    col("credentials").update_one(
        {"bot_id": BOT_ID},
        {
            "$set": {
                "bot_id": BOT_ID,
                "okx_api_key": _st()["okx_api_key"],
                "okx_secret_key": _st()["okx_secret_key"],
                "okx_passphrase": _st()["okx_passphrase"],
                "okx_flag": _st()["okx_flag"],
                "account_id": _st().get("account_id") or "",
                "updated_at": _now(),
            }
        },
        upsert=True,
    )


def _get_active_id() -> str:
    row = col("settings").find_one({"_id": _active_setting_id()}) or {}
    if not row and not _uid():
        row = col("settings").find_one({"_id": "okx_active_account"}) or {}
    return str(row.get("account_id") or "")


def _set_active_id(account_id: str) -> None:
    col("settings").update_one(
        {"_id": _active_setting_id()},
        {"$set": {"account_id": account_id, "updated_at": _now()}},
        upsert=True,
    )
    _st()["account_id"] = account_id


def _public_account(row: dict[str, Any], active_id: str) -> dict[str, Any]:
    aid = str(row.get("account_id") or "")
    return {
        "account_id": aid,
        "name": row.get("name") or "Conta",
        "api_key_masked": _mask(str(row.get("okx_api_key") or "")),
        "secret_set": bool(row.get("okx_secret_key")),
        "passphrase_set": bool(row.get("okx_passphrase")),
        "okx_flag": str(row.get("okx_flag") or "0"),
        "active": aid == active_id,
        "updated_at": row.get("updated_at"),
    }


def _migrate_if_needed() -> None:
    if _auth_on():
        return
    if _accounts().count_documents({}) > 0:
        return
    if not configured():
        return
    aid = _new_id()
    _accounts().insert_one(
        {
            "account_id": aid,
            "name": "Conta 1",
            "okx_api_key": _st()["okx_api_key"],
            "okx_secret_key": _st()["okx_secret_key"],
            "okx_passphrase": _st()["okx_passphrase"],
            "okx_flag": _st()["okx_flag"] or "0",
            "created_at": _now(),
            "updated_at": _now(),
        }
    )
    _set_active_id(aid)
    _st()["account_name"] = "Conta 1"


def _activate(account_id: str) -> None:
    row = _accounts().find_one({"account_id": account_id, **_owner_q()})
    if not row:
        raise KeyError("conta não encontrada")
    if not (row.get("okx_api_key") and row.get("okx_secret_key") and row.get("okx_passphrase")):
        raise ValueError("conta sem API Key, Secret e Passphrase")
    _apply_row(row)
    _set_active_id(account_id)
    _persist_legacy()


def load() -> None:
    if _auth_on():
        return
    row = col("credentials").find_one({"bot_id": BOT_ID})
    if row:
        _apply_row(row)
    else:
        seeded = {
            "okx_api_key": settings.okx_api_key or "",
            "okx_secret_key": settings.okx_secret_key or "",
            "okx_passphrase": settings.okx_passphrase or "",
            "okx_flag": settings.okx_flag or "0",
        }
        _st().update(seeded)
        if seeded["okx_api_key"] and seeded["okx_secret_key"] and seeded["okx_passphrase"]:
            _persist_legacy()
    _migrate_if_needed()
    active = _get_active_id() or str(_st().get("account_id") or "")
    acct = _accounts().find_one({"account_id": active, **_owner_q()}) if active else None
    if not acct:
        acct = _accounts().find_one(_owner_q(), sort=[("created_at", 1)])
        if acct:
            _set_active_id(str(acct["account_id"]))
    if acct:
        _apply_row(acct)
        _persist_legacy()


def get(key: str) -> str:
    return str(_st().get(key) or "")


def configured() -> bool:
    return bool(_st()["okx_api_key"] and _st()["okx_secret_key"] and _st()["okx_passphrase"])


def active_id() -> str:
    return str(_st().get("account_id") or "")


def account_name(account_id: str | None = None) -> str:
    aid = str(account_id or "").strip()
    if not aid:
        return str(_st().get("account_name") or "")
    if aid == _st().get("account_id"):
        return str(_st().get("account_name") or "")
    row = _accounts().find_one({"account_id": aid, **_owner_q()}, {"name": 1})
    return str((row or {}).get("name") or "")


def status() -> dict:
    active = active_id() or _get_active_id()
    rows = list(_accounts().find(_owner_q(), {"_id": 0}).sort("created_at", 1))
    if _uid() and len(rows) > 1:
        keep = str(active or rows[0].get("account_id") or "")
        rows = [r for r in rows if str(r.get("account_id")) == keep] or rows[:1]
    accounts = [_public_account(r, active) for r in rows]
    return {
        "configured": configured(),
        "api_key_masked": _mask(_st()["okx_api_key"]),
        "secret_set": bool(_st()["okx_secret_key"]),
        "passphrase_set": bool(_st()["okx_passphrase"]),
        "okx_flag": _st()["okx_flag"] or "0",
        "active_account_id": active,
        "account_name": str(_st().get("account_name") or ""),
        "accounts": accounts,
    }


def save(
    *,
    api_key: str | None = None,
    secret: str | None = None,
    passphrase: str | None = None,
    flag: str | None = None,
    name: str | None = None,
) -> dict:
    if api_key is not None and api_key.strip():
        _st()["okx_api_key"] = api_key.strip()
    if secret is not None and secret.strip():
        _st()["okx_secret_key"] = secret.strip()
    if passphrase is not None and passphrase.strip():
        _st()["okx_passphrase"] = passphrase.strip()
    if flag is not None and str(flag) in {"0", "1"}:
        _st()["okx_flag"] = str(flag)
    if name is not None and str(name).strip():
        _st()["account_name"] = str(name).strip()[:60]
    if not configured():
        raise ValueError("informe API Key, Secret e Passphrase")
    aid = str(_st().get("account_id") or "")
    if not aid:
        return add_account(
            name=_st().get("account_name") or "Conta 1",
            api_key=_st()["okx_api_key"],
            secret=_st()["okx_secret_key"],
            passphrase=_st()["okx_passphrase"],
            flag=_st()["okx_flag"],
            activate=True,
        )
    patch = {
        "okx_api_key": _st()["okx_api_key"],
        "okx_secret_key": _st()["okx_secret_key"],
        "okx_passphrase": _st()["okx_passphrase"],
        "okx_flag": _st()["okx_flag"],
        "updated_at": _now(),
    }
    if _st().get("account_name"):
        patch["name"] = _st()["account_name"]
    if _uid():
        patch["user_id"] = _uid()
    filt = {"account_id": aid, **_owner_q()}
    res = _accounts().update_one(filt, {"$set": patch})
    if res.matched_count == 0:
        _accounts().update_one({"account_id": aid}, {"$set": patch}, upsert=not _auth_on())
    _persist_legacy()
    return status()


def add_account(
    *,
    name: str,
    api_key: str,
    secret: str,
    passphrase: str,
    flag: str = "0",
    activate: bool = True,
) -> dict:
    api_key = (api_key or "").strip()
    secret = (secret or "").strip()
    passphrase = (passphrase or "").strip()
    if not (api_key and secret and passphrase):
        raise ValueError("informe API Key, Secret e Passphrase")
    flag_s = str(flag or "0")
    if flag_s not in {"0", "1"}:
        flag_s = "0"
    existing = _accounts().find_one(_owner_q(), sort=[("created_at", 1)]) if _uid() else None
    if existing:
        return update_account(
            str(existing["account_id"]),
            name=name,
            api_key=api_key,
            secret=secret,
            passphrase=passphrase,
            flag=flag_s,
        )
    n = _accounts().count_documents(_owner_q()) + 1
    label = (name or "").strip()[:60] or f"Conta {n}"
    aid = _new_id()
    doc: dict[str, Any] = {
        "account_id": aid,
        "name": label,
        "okx_api_key": api_key,
        "okx_secret_key": secret,
        "okx_passphrase": passphrase,
        "okx_flag": flag_s,
        "created_at": _now(),
        "updated_at": _now(),
    }
    if _uid():
        doc["user_id"] = _uid()
    _accounts().insert_one(doc)
    if activate or not active_id():
        _activate(aid)
    return status()


def update_account(
    account_id: str,
    *,
    name: str | None = None,
    api_key: str | None = None,
    secret: str | None = None,
    passphrase: str | None = None,
    flag: str | None = None,
) -> dict:
    row = _accounts().find_one({"account_id": account_id, **_owner_q()})
    if not row:
        raise KeyError("conta não encontrada")
    patch: dict[str, Any] = {"updated_at": _now()}
    if name is not None and str(name).strip():
        patch["name"] = str(name).strip()[:60]
    if api_key is not None and api_key.strip():
        patch["okx_api_key"] = api_key.strip()
    if secret is not None and secret.strip():
        patch["okx_secret_key"] = secret.strip()
    if passphrase is not None and passphrase.strip():
        patch["okx_passphrase"] = passphrase.strip()
    if flag is not None and str(flag) in {"0", "1"}:
        patch["okx_flag"] = str(flag)
    res = _accounts().update_one({"account_id": account_id, **_owner_q()}, {"$set": patch})
    if res.matched_count == 0:
        raise KeyError("conta não encontrada")
    if account_id == active_id():
        _activate(account_id)
        if patch.get("name"):
            _st()["account_name"] = patch["name"]
            _persist_legacy()
    return status()


def activate(account_id: str) -> dict:
    _activate(account_id)
    return status()


def delete_account(account_id: str) -> dict:
    row = _accounts().find_one({"account_id": account_id, **_owner_q()})
    if not row:
        raise KeyError("conta não encontrada")
    was_active = account_id == active_id()
    _accounts().delete_one({"account_id": account_id, **_owner_q()})
    if was_active or _accounts().count_documents(_owner_q()) == 0:
        nxt = _accounts().find_one(_owner_q(), sort=[("created_at", 1)])
        if nxt:
            _activate(str(nxt["account_id"]))
        else:
            st = _st()
            for k in _empty():
                st[k] = ""
            col("settings").delete_one({"_id": _active_setting_id()})
    return status()
