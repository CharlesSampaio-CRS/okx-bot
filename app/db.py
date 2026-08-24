from __future__ import annotations

import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from pymongo import ASCENDING, DESCENDING, ReturnDocument

from .models import BotConfig, Event, Position, Trade
from .mongo import BOT_ID, col, ping
from .strategies import MARKET_STRATEGIES

_BUILTIN_STRATEGY_IDS = {str(s["id"]) for s in MARKET_STRATEGIES}

DEFAULT_POSITION = {
    "bot_id": BOT_ID,
    "state": "flat",
    "ref_price": None,
    "entry_price": None,
    "qty": None,
    "cost_total": None,
    "buy_fee": None,
    "buy_fee_ccy": None,
    "buy_fee_usdt": None,
    "opened_at": None,
    "cascade_buy_step": 0,
    "cascade_sell_step": 0,
    "cycle_budget": None,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _next_id(name: str) -> int:
    doc = col("counters").find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc["seq"])


def _uid() -> str:
    from .context import current_user_id
    return current_user_id.get() or ""


def _auth_on() -> bool:
    from . import auth as authmod
    return authmod.enabled()


def _active_account_id() -> str:
    try:
        from . import credentials
        return credentials.active_id()
    except Exception:
        return ""


def _scope_q(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    q = dict(extra or {})
    uid = _uid()
    if uid:
        q["user_id"] = uid
        return q
    if _auth_on():
        q["user_id"] = "__none__"
        return q
    aid = _active_account_id()
    if aid:
        q["okx_account_id"] = aid
    return q


def _stamp_owner(doc: dict[str, Any]) -> dict[str, Any]:
    uid = _uid()
    if uid:
        doc["user_id"] = uid
    aid = _account_id_for_bot(str(doc.get("bot_id") or "")) or _active_account_id()
    if aid:
        doc["okx_account_id"] = aid
    return doc


def _settings_id(kind: str) -> str:
    uid = _uid()
    return f"{kind}:{uid}" if uid else kind


def peek_bot_user(bot_id: str) -> str:
    row = col("bots").find_one({"bot_id": bot_id}, {"user_id": 1})
    return str((row or {}).get("user_id") or "")


def backfill_user_ids() -> None:
    """Copia user_id da conta OKX para documentos que já têm okx_account_id."""
    for acct in col("okx_accounts").find({"user_id": {"$nin": [None, ""]}}):
        uid = str(acct.get("user_id") or "")
        aid = str(acct.get("account_id") or "")
        if not uid or not aid:
            continue
        q = {
            "okx_account_id": aid,
            "$or": [{"user_id": {"$exists": False}}, {"user_id": None}, {"user_id": ""}],
        }
        for name in (
            "bots",
            "positions",
            "trades",
            "events",
            "executions",
            "order_origins",
            "portfolio_snapshots",
            "hunter_rotations",
            "hunter_cooldowns",
        ):
            col(name).update_many(q, {"$set": {"user_id": uid}})
        col("positions").update_many(
            {
                "bot_id": {"$in": [b["bot_id"] for b in col("bots").find({"user_id": uid}, {"bot_id": 1})]},
                "$or": [{"user_id": {"$exists": False}}, {"user_id": None}, {"user_id": ""}],
            },
            {"$set": {"user_id": uid}},
        )


def _account_id_for_bot(bot_id: str | None) -> str:
    bid = (bot_id or "").strip()
    if bid and bid not in {"system", "wallet"}:
        row = col("bots").find_one({"bot_id": bid}, {"okx_account_id": 1})
        aid = str((row or {}).get("okx_account_id") or "")
        if aid:
            return aid
    return _active_account_id()


def _missing_account_q() -> dict[str, Any]:
    return {
        "$or": [
            {"okx_account_id": {"$exists": False}},
            {"okx_account_id": None},
            {"okx_account_id": ""},
        ]
    }


def stamp_existing_okx_account_id(account_id: str) -> dict[str, int]:
    """Só marca documentos do usuário atual (não pinta o banco inteiro)."""
    aid = (account_id or "").strip()
    uid = _uid()
    if not aid or not uid:
        return {}
    q = {"$and": [_missing_account_q(), {"user_id": uid}]}
    names = (
        "bots",
        "positions",
        "trades",
        "events",
        "executions",
        "order_origins",
        "portfolio_snapshots",
        "hunter_rotations",
        "hunter_cooldowns",
    )
    out: dict[str, int] = {}
    for name in names:
        res = col(name).update_many(q, {"$set": {"okx_account_id": aid}})
        out[name] = int(res.modified_count)
    return out


def _wallet_snap_q(**extra: Any) -> dict[str, Any]:
    q: dict[str, Any] = {"bot_id": "wallet", **extra}
    uid = _uid()
    aid = _active_account_id()
    if uid:
        owners: list[dict[str, Any]] = [{"user_id": uid}]
        if aid:
            owners.append(
                {
                    "okx_account_id": aid,
                    "$or": [
                        {"user_id": {"$exists": False}},
                        {"user_id": None},
                        {"user_id": ""},
                    ],
                }
            )
        if len(owners) == 1:
            q["user_id"] = uid
        else:
            q["$or"] = owners
        return q
    if aid:
        q["okx_account_id"] = aid
    elif _auth_on():
        q["user_id"] = "__none__"
    return q


def init_db() -> None:
    ping()
    col("bots").create_index("bot_id", unique=True)
    col("positions").create_index("bot_id", unique=True)
    col("credentials").create_index("bot_id", unique=True)
    col("okx_accounts").create_index("account_id", unique=True)
    from . import auth as authmod
    authmod.init_auth_indexes()
    backfill_user_ids()
    col("bots").create_index("okx_account_id")
    col("positions").create_index("okx_account_id")
    col("trades").create_index([("bot_id", ASCENDING), ("id", DESCENDING)])
    col("trades").create_index("order_id")
    col("trades").create_index([("okx_account_id", ASCENDING), ("id", DESCENDING)])
    col("events").create_index([("bot_id", ASCENDING), ("id", DESCENDING)])
    col("events").create_index("okx_account_id")
    col("portfolio_snapshots").create_index([("bot_id", ASCENDING), ("ts", DESCENDING)])
    col("portfolio_snapshots").create_index([("okx_account_id", ASCENDING), ("ts", DESCENDING)])
    try:
        col("order_origins").drop_index("ord_id_1")
    except Exception:
        pass
    col("order_origins").create_index("ord_id", unique=True, sparse=True)
    col("order_origins").create_index("cl_ord_id")
    col("order_origins").create_index("okx_account_id")
    col("executions").create_index([("bot_id", ASCENDING), ("id", DESCENDING)])
    col("executions").create_index("okx_account_id")
    col("hunter_rotations").create_index([("okx_account_id", ASCENDING), ("ts", DESCENDING)])
    col("custom_strategies").create_index("id", unique=True)
    if not col("settings").find_one({"_id": "order_limits"}):
        col("settings").insert_one(
            {"_id": "order_limits", "min_usd": 5.0, "max_usd": 100.0, "updated_at": _now()}
        )
    col("api_cache").create_index("kind")
    col("api_cache").create_index("ts")
    col("hunter_rotations").create_index([("ts", DESCENDING)])
    # testes não devem ficar no banco / na tela Bot
    col("executions").delete_many({"mode": {"$in": ["test", "dry", "lab"]}})
    col("executions").delete_many({"reason": {"$regex": r"^cenário \+|\[teste\]"}})

    # Não recria bot "default" automaticamente — a lista pode ficar vazia.
    # (antes: seed Spot Bot/BTC-USDT voltava após apagar)
    if not col("positions").find_one({"bot_id": BOT_ID}) and col("bots").find_one({"bot_id": BOT_ID}):
        col("positions").insert_one(dict(DEFAULT_POSITION))
    col("bots").update_many({"name": {"$exists": False}}, {"$set": {"name": "Spot Bot"}})
    names = {
        b["bot_id"]: (b.get("name") or b["bot_id"])
        for b in col("bots").find({}, {"bot_id": 1, "name": 1})
        if b.get("bot_id")
    }
    for row in col("trades").find({"order_id": {"$nin": [None, ""]}}):
        oid = str(row.get("order_id") or "")
        if not oid or col("order_origins").find_one({"ord_id": oid}):
            continue
        bid = row.get("bot_id")
        origin = row.get("origin") or ("bot" if bid else "user")
        remember_order_origin(
            oid,
            origin="user" if origin == "user" else "bot",
            bot_id=None if origin == "user" else bid,
            bot_name=None if origin == "user" else (row.get("bot_name") or names.get(bid) or bid),
        )


def list_bots() -> list[dict[str, Any]]:
    rows = list(col("bots").find(_scope_q(), {"_id": 0}).sort("updated_at", DESCENDING))
    return rows or []


def _near(a: Any, b: Any, eps: float = 1e-6) -> bool:
    try:
        return abs(float(a) - float(b)) <= eps
    except (TypeError, ValueError):
        return False


def find_duplicate_bot(
    *,
    inst_id: str,
    buy_pct: float,
    profit_target_pct: float,
    fee_rate_pct: float,
    quote_amount: float,
) -> dict[str, Any] | None:
    """Mesmo par + mesmas regras de trade = bot duplicado (não faz sentido 2 ativos)."""
    inst = (inst_id or "").strip().upper()
    q = _scope_q({"inst_id": inst})
    for row in col("bots").find(q, {"_id": 0}):
        if (
            _near(row.get("buy_pct"), buy_pct)
            and _near(row.get("profit_target_pct"), profit_target_pct)
            and _near(row.get("fee_rate_pct"), fee_rate_pct)
            and _near(row.get("quote_amount"), quote_amount)
        ):
            return row
    return None


def _interval_min_from_row(row: dict[str, Any]) -> float:
    if row.get("interval_min") is not None:
        return max(1.0, float(row["interval_min"]))
    # legado: poll_interval era segundos
    sec = float(row.get("poll_interval") or 300.0)
    return max(1.0, round(sec / 60.0, 2))




def list_custom_strategies() -> list[dict[str, Any]]:
    rows = list(col("custom_strategies").find(_scope_q(), {"_id": 0}).sort("created_at", DESCENDING))
    for r in rows:
        r["custom"] = True
        r["builtin"] = False
    return rows


def create_custom_strategy(payload: dict[str, Any]) -> dict[str, Any]:
    name = (payload.get("name") or "").strip() or "Estratégia"
    base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "custom"
    sid = f"custom_{base}"[:40]
    n = 1
    while col("custom_strategies").find_one({"id": sid}) or sid in _BUILTIN_STRATEGY_IDS:
        n += 1
        sid = f"custom_{base}_{n}"[:48]
    doc = {
        "id": sid,
        "name": name[:60],
        "style": str(payload.get("style") or "custom")[:40],
        "focus": str(payload.get("focus") or "")[:200],
        "buy_pct": float(payload.get("buy_pct") or 2.0),
        "profit_target_pct": float(payload.get("profit_target_pct") or 1.0),
        "fee_rate_pct": float(payload.get("fee_rate_pct") or 0.10),
        "risk": str(payload.get("risk") or "médio")[:40],
        "best_for": str(payload.get("best_for") or "")[:120],
        "tag": str(payload.get("tag") or "custom")[:40],
        "custom": True,
        "builtin": False,
        "created_at": _now(),
    }
    _stamp_owner(doc)
    col("custom_strategies").insert_one(doc)
    doc.pop("_id", None)
    return doc


def delete_custom_strategy(strategy_id: str) -> bool:
    sid = (strategy_id or "").strip().lower()
    if not sid.startswith("custom_"):
        return False
    res = col("custom_strategies").delete_one({"id": sid, **_scope_q()})
    return res.deleted_count > 0

def create_bot(
    *,
    name: str,
    inst_id: str = "BTC-USDT",
    strategy_id: str | None = None,
    buy_pct: float = 2.0,
    profit_target_pct: float = 1.0,
    fee_rate_pct: float = 0.10,
    quote_amount: float = 0.0,
    entry_mode: str = "quote",
    interval_min: float = 30.0,
    run_days: float = 7.0,
    portfolio_interval_min: float = 2.0,
    cascade_enabled: bool = False,
    cascade_buy_pct: float = 20.0,
    cascade_sell_pct: float = 25.0,
    cascade_buy_pcts: list[float] | None = None,
    cascade_sell_pcts: list[float] | None = None,
    okx_account_id: str | None = None,
) -> dict[str, Any]:
    bot_id = f"bot{_next_id('bot_seq')}"
    mode = (entry_mode or "quote").lower()
    if mode not in {"quote", "base"}:
        mode = "quote"
    doc = {
        "bot_id": bot_id,
        "name": (name or "").strip() or f"Bot {bot_id}",
        "inst_id": inst_id.strip().upper(),
        "strategy_id": (strategy_id or "").strip().lower() or None,
        "buy_pct": buy_pct,
        "profit_target_pct": profit_target_pct,
        "fee_rate_pct": fee_rate_pct,
        "quote_amount": max(0.0, float(quote_amount or 0)),
        "entry_mode": mode,
        "interval_min": interval_min,
        "run_days": run_days,
        "portfolio_interval_min": portfolio_interval_min,
        "cascade_enabled": bool(cascade_enabled),
        "cascade_buy_pct": float(cascade_buy_pct),
        "cascade_sell_pct": float(cascade_sell_pct),
        "cascade_buy_pcts": cascade_buy_pcts,
        "cascade_sell_pcts": cascade_sell_pcts,
        "updated_at": _now(),
    }
    aid = (okx_account_id or "").strip()
    if aid:
        doc["okx_account_id"] = aid
    from .context import current_user_id
    uid = current_user_id.get()
    if uid:
        doc["user_id"] = uid
    col("bots").insert_one(doc)
    pos = dict(DEFAULT_POSITION)
    pos["bot_id"] = bot_id
    if aid:
        pos["okx_account_id"] = aid
    if uid:
        pos["user_id"] = uid
    col("positions").insert_one(pos)
    doc.pop("_id", None)
    return doc


def delete_bot(bot_id: str) -> None:
    col("bots").delete_one({"bot_id": bot_id})
    col("positions").delete_one({"bot_id": bot_id})
    col("executions").delete_many({"bot_id": bot_id})
    col("events").delete_many({"bot_id": bot_id})


def get_bot_doc(bot_id: str) -> dict[str, Any]:
    bid = (bot_id or "").strip()
    if not bid:
        raise KeyError("bot_id obrigatório")
    row = col("bots").find_one({"bot_id": bid}, {"_id": 0})
    if not row:
        raise KeyError(f"bot {bid} não encontrado")
    uid = _uid()
    owner = str(row.get("user_id") or "")
    if uid and owner and owner != uid:
        raise KeyError(f"bot {bid} não encontrado")
    return row


def set_bot_account(bot_id: str, account_id: str) -> None:
    bid = (bot_id or "").strip()
    aid = (account_id or "").strip()
    if not bid or not aid:
        return
    col("bots").update_one(
        {"bot_id": bid},
        {"$set": {"okx_account_id": aid, "updated_at": _now()}},
    )
    col("positions").update_one({"bot_id": bid}, {"$set": {"okx_account_id": aid}})


def get_config(bot_id: str) -> BotConfig:
    """Carrega config de um bot existente. Não inventa bot 'default' fantasma."""
    bid = (bot_id or "").strip()
    if not bid:
        raise KeyError("bot_id obrigatório")
    row = col("bots").find_one({"bot_id": bid})
    if not row:
        raise KeyError(f"bot {bid} não encontrado")
    entry_mode = str(row.get("entry_mode") or "quote").lower()
    if entry_mode not in {"quote", "base"}:
        entry_mode = "quote"
    return BotConfig(
        bot_id=row.get("bot_id") or bid,
        name=row.get("name") or "Spot Bot",
        inst_id=row.get("inst_id") or "BTC-USDT",
        strategy_id=(str(row.get("strategy_id")).strip().lower() if row.get("strategy_id") else None),
        buy_pct=float(row.get("buy_pct") or 2.0),
        profit_target_pct=float(row.get("profit_target_pct") or 1.0),
        fee_rate_pct=float(row.get("fee_rate_pct") or 0.10),
        quote_amount=float(row.get("quote_amount") if row.get("quote_amount") is not None else 0.0),
        entry_mode=entry_mode,  # type: ignore[arg-type]
        interval_min=_interval_min_from_row(row),
        run_days=float(row["run_days"]) if row.get("run_days") is not None else 7.0,
        portfolio_interval_min=float(row.get("portfolio_interval_min") or 2.0),
        cascade_enabled=bool(row.get("cascade_enabled")),
        cascade_buy_pct=float(row.get("cascade_buy_pct") or 20.0),
        cascade_sell_pct=float(row.get("cascade_sell_pct") or 25.0),
        cascade_buy_pcts=row.get("cascade_buy_pcts") or None,
        cascade_sell_pcts=row.get("cascade_sell_pcts") or None,
    )


def portfolio_interval_min() -> float:
    """Intervalo do watcher de carteira (global): usa o bot mais recente, senão 2 min."""
    row = col("bots").find_one(
        {},
        {"portfolio_interval_min": 1},
        sort=[("updated_at", DESCENDING)],
    )
    if row and row.get("portfolio_interval_min") is not None:
        try:
            return max(1.0, min(60.0, float(row["portfolio_interval_min"])))
        except (TypeError, ValueError):
            pass
    return 2.0


def save_config(cfg: BotConfig, bot_id: str | None = None) -> BotConfig:
    bid = (bot_id or cfg.bot_id or "").strip()
    if not bid:
        raise KeyError("bot_id obrigatório")
    res = col("bots").update_one(
        {"bot_id": bid},
        {
            "$set": {
                "bot_id": bid,
                "name": (cfg.name or "Spot Bot").strip(),
                "inst_id": cfg.inst_id.strip().upper(),
                "strategy_id": cfg.strategy_id,
                "buy_pct": cfg.buy_pct,
                "profit_target_pct": cfg.profit_target_pct,
                "fee_rate_pct": cfg.fee_rate_pct,
                "quote_amount": cfg.quote_amount,
                "entry_mode": cfg.entry_mode,
                "interval_min": cfg.interval_min,
                "run_days": cfg.run_days,
                "portfolio_interval_min": cfg.portfolio_interval_min,
                "cascade_enabled": cfg.cascade_enabled,
                "cascade_buy_pct": cfg.cascade_buy_pct,
                "cascade_sell_pct": cfg.cascade_sell_pct,
                "cascade_buy_pcts": cfg.cascade_buy_pcts,
                "cascade_sell_pcts": cfg.cascade_sell_pcts,
                "updated_at": _now(),
            },
            "$unset": {"poll_interval": ""},
        },
        upsert=False,
    )
    if res.matched_count == 0:
        raise KeyError(f"bot {bid} não encontrado")
    if not col("positions").find_one({"bot_id": bid}):
        pos = dict(DEFAULT_POSITION)
        pos["bot_id"] = bid
        col("positions").insert_one(pos)
    return get_config(bid)


def set_run_window(bot_id: str, started_at: str | None, run_until: str | None) -> None:
    col("bots").update_one(
        {"bot_id": bot_id},
        {"$set": {"run_started_at": started_at, "run_until": run_until}},
    )


def clear_run_window(bot_id: str) -> None:
    col("bots").update_one(
        {"bot_id": bot_id},
        {"$unset": {"run_started_at": "", "run_until": ""}},
    )


def get_run_window(bot_id: str) -> dict[str, Any]:
    row = col("bots").find_one({"bot_id": bot_id}, {"_id": 0, "run_started_at": 1, "run_until": 1}) or {}
    started = row.get("run_started_at")
    until = row.get("run_until")
    remaining = None
    if until:
        try:
            end = datetime.fromisoformat(str(until).replace("Z", "+00:00"))
            remaining = max(0.0, (end - datetime.now(timezone.utc)).total_seconds())
        except ValueError:
            remaining = None
    return {"run_started_at": started, "run_until": until, "run_remaining_sec": remaining}


def run_window_expired(bot_id: str) -> bool:
    win = get_run_window(bot_id)
    rem = win.get("run_remaining_sec")
    if rem is None and not win.get("run_until"):
        return False
    return rem is not None and rem <= 0


def bot_has_trades(bot_id: str) -> bool:
    """True se o bot já executou ao menos 1 compra/venda (ciclo já começou)."""
    doc = col("trades").find_one(
        {"bot_id": bot_id, "side": {"$in": ["buy", "sell"]}},
        {"_id": 1},
    )
    return doc is not None


def get_position(bot_id: str = BOT_ID) -> Position:
    row = col("positions").find_one({"bot_id": bot_id}) or DEFAULT_POSITION
    return Position(
        state=row.get("state") or "flat",
        ref_price=row.get("ref_price"),
        entry_price=row.get("entry_price"),
        qty=row.get("qty"),
        cost_total=row.get("cost_total"),
        buy_fee=row.get("buy_fee"),
        buy_fee_ccy=row.get("buy_fee_ccy"),
        buy_fee_usdt=row.get("buy_fee_usdt"),
        opened_at=row.get("opened_at"),
        cascade_buy_step=int(row.get("cascade_buy_step") or 0),
        cascade_sell_step=int(row.get("cascade_sell_step") or 0),
        cycle_budget=row.get("cycle_budget"),
    )


def save_position(pos: Position, bot_id: str = BOT_ID) -> Position:
    col("positions").update_one(
        {"bot_id": bot_id},
        {
            "$set": {
                "bot_id": bot_id,
                "state": pos.state,
                "ref_price": pos.ref_price,
                "entry_price": pos.entry_price,
                "qty": pos.qty,
                "cost_total": pos.cost_total,
                "buy_fee": pos.buy_fee,
                "buy_fee_ccy": pos.buy_fee_ccy,
                "buy_fee_usdt": pos.buy_fee_usdt,
                "opened_at": pos.opened_at,
                "cascade_buy_step": pos.cascade_buy_step,
                "cascade_sell_step": pos.cascade_sell_step,
                "cycle_budget": pos.cycle_budget,
                "updated_at": _now(),
                **({"okx_account_id": aid} if (aid := _account_id_for_bot(bot_id)) else {}),
            }
        },
        upsert=True,
    )
    return get_position(bot_id)


def make_cl_ord_id(origin: str, bot_id: str | None = None) -> str:
    ts = f"{int(time.time() * 1000) % 10_000_000_000:010d}"
    nonce = secrets.token_hex(2)
    if origin == "user":
        return f"okU{ts}{nonce}"[:32]
    bid = re.sub(r"[^A-Za-z0-9]", "", bot_id or "bot")[:12] or "bot"
    return f"okB{bid}{ts}{nonce}"[:32]


def remember_order_origin(
    ord_id: str | None,
    *,
    origin: str,
    bot_id: str | None = None,
    bot_name: str | None = None,
    cl_ord_id: str | None = None,
) -> None:
    oid = str(ord_id or "").strip() or None
    cl = str(cl_ord_id or "").strip() or None
    if not oid and not cl:
        return
    origin = "user" if origin == "user" else "bot"
    label = "Usuário" if origin == "user" else (bot_name or bot_id or "Bot")
    query = {"ord_id": oid} if oid else {"cl_ord_id": cl}
    doc = {
        "origin": origin,
        "origin_label": label,
        "bot_id": None if origin == "user" else bot_id,
        "bot_name": None if origin == "user" else (bot_name or bot_id),
        "cl_ord_id": cl,
        "ts": _now(),
    }
    if oid:
        doc["ord_id"] = oid
    aid = _account_id_for_bot(bot_id)
    if aid:
        doc["okx_account_id"] = aid
    col("order_origins").update_one(query, {"$set": doc}, upsert=True)


def _bot_names() -> dict[str, str]:
    out: dict[str, str] = {}
    for row in list_bots():
        bid = str(row.get("bot_id") or "")
        if bid:
            out[bid] = str(row.get("name") or bid)
    return out


def infer_origin(
    *,
    origin: str | None = None,
    origin_label: str | None = None,
    bot_id: str | None = None,
    bot_name: str | None = None,
    cl_ord_id: str | None = None,
    names: dict[str, str] | None = None,
) -> tuple[str, str]:
    names = names or {}
    cl = str(cl_ord_id or "")
    if origin == "user" or cl.startswith("okU"):
        return "user", "Usuário"
    if origin == "bot" or bot_id or cl.startswith("okB"):
        label = origin_label or bot_name or (names.get(str(bot_id)) if bot_id else None)
        if not label and cl.startswith("okB"):
            rest = cl[3:]
            for bid, name in names.items():
                key = re.sub(r"[^A-Za-z0-9]", "", bid)
                if key and rest.startswith(key):
                    label = name
                    break
        return "bot", str(label or "Bot")
    if origin_label:
        return origin or "unknown", origin_label
    return "unknown", "—"


def origins_by_keys(keys: list[str]) -> dict[str, dict[str, Any]]:
    keys = [str(k) for k in keys if k]
    if not keys:
        return {}
    rows = col("order_origins").find({"$or": [{"ord_id": {"$in": keys}}, {"cl_ord_id": {"$in": keys}}]})
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("ord_id"):
            out[str(row["ord_id"])] = row
        if row.get("cl_ord_id"):
            out.setdefault(str(row["cl_ord_id"]), row)
    return out


def trades_by_order_ids(ids: list[str]) -> dict[str, dict[str, Any]]:
    ids = [str(i) for i in ids if i]
    if not ids:
        return {}
    rows = col("trades").find({"order_id": {"$in": ids}})
    return {str(row.get("order_id")): row for row in rows if row.get("order_id")}


def attach_origins(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys: list[str] = []
    for order in orders:
        if order.get("ord_id"):
            keys.append(str(order["ord_id"]))
        if order.get("cl_ord_id"):
            keys.append(str(order["cl_ord_id"]))
    metas = origins_by_keys(keys)
    tmetas = trades_by_order_ids([str(o.get("ord_id") or "") for o in orders])
    names = _bot_names()
    out: list[dict[str, Any]] = []
    for order in orders:
        row = dict(order)
        oid = str(row.get("ord_id") or "")
        cl = str(row.get("cl_ord_id") or "")
        meta = metas.get(oid) or metas.get(cl) or tmetas.get(oid) or {}
        origin, label = infer_origin(
            origin=meta.get("origin") or row.get("origin"),
            origin_label=meta.get("origin_label") or meta.get("bot_name"),
            bot_id=meta.get("bot_id"),
            bot_name=meta.get("bot_name"),
            cl_ord_id=cl or meta.get("cl_ord_id"),
            names=names,
        )
        trade = tmetas.get(oid)
        if origin == "unknown":
            if trade and (trade.get("origin") == "bot" or trade.get("bot_id")):
                origin, label = infer_origin(
                    origin="bot",
                    bot_id=trade.get("bot_id"),
                    bot_name=trade.get("bot_name") or trade.get("origin_label"),
                    names=names,
                )
            else:
                origin, label = "user", "Usuário"
            remember_order_origin(
                oid,
                origin=origin,
                bot_id=trade.get("bot_id") if origin == "bot" else None,
                bot_name=label if origin == "bot" else None,
                cl_ord_id=cl or None,
            )
        row["origin"] = origin
        row["origin_label"] = label
        row["bot_id"] = meta.get("bot_id") or row.get("bot_id")
        row["bot_name"] = label if origin == "bot" else None
        if trade:
            # PnL realizado do bot tem prioridade sobre estimativa OKX/histórico
            if trade.get("pnl_realized") is not None:
                row["pnl"] = trade.get("pnl_realized")
                row["pnl_realized"] = trade.get("pnl_realized")
                if row.get("pnl_pct") is None:
                    cost = None
                    try:
                        qty = float(trade.get("qty") or row.get("fill_sz") or row.get("sz") or 0)
                        avg = float(trade.get("avg_px") or row.get("avg_px") or 0)
                        fee = float(trade.get("fee_usdt") or 0)
                        if qty > 0 and avg > 0:
                            proceeds = avg * qty - abs(fee)
                            cost = proceeds - float(trade["pnl_realized"])
                            if cost and cost > 0:
                                row["pnl_pct"] = (float(trade["pnl_realized"]) / cost) * 100.0
                    except (TypeError, ValueError):
                        pass
            elif row.get("pnl") is None and trade.get("pnl_realized") is not None:
                row["pnl"] = trade.get("pnl_realized")
            if row.get("fee_usdt") is None and trade.get("fee_usdt") is not None:
                row["fee_usdt"] = trade.get("fee_usdt")
        out.append(row)
    return out


def order_as_trade(order: dict[str, Any], idx: int = 0) -> dict[str, Any]:
    origin = order.get("origin") or "unknown"
    label = order.get("origin_label") or "—"
    return {
        "id": idx,
        "ts": order.get("updated_at") or order.get("created_at") or "",
        "side": order.get("side") or "",
        "inst_id": order.get("inst_id") or "",
        "qty": order.get("fill_sz") or order.get("sz"),
        "avg_px": order.get("avg_px") or order.get("px"),
        "fee": order.get("fee"),
        "fee_ccy": order.get("fee_ccy"),
        "fee_usdt": order.get("fee_usdt"),
        "pnl_realized": order.get("pnl_realized") if order.get("pnl_realized") is not None else order.get("pnl"),
        "order_id": order.get("ord_id"),
        "status": order.get("state") or "filled",
        "origin": origin,
        "origin_label": label,
        "bot_id": order.get("bot_id"),
        "bot_name": order.get("bot_name"),
    }


def add_trade(
    *,
    side: str,
    inst_id: str,
    qty: Optional[float],
    avg_px: Optional[float],
    fee: Optional[float],
    fee_ccy: Optional[str],
    fee_usdt: Optional[float],
    pnl_realized: Optional[float],
    order_id: Optional[str],
    status: str = "filled",
    bot_id: Optional[str] = None,
    origin: str = "bot",
    origin_label: Optional[str] = None,
    bot_name: Optional[str] = None,
    cl_ord_id: Optional[str] = None,
) -> None:
    origin = "user" if origin == "user" else "bot"
    if origin == "user":
        bot_id = None
        bot_name = None
        label = "Usuário"
    else:
        label = origin_label or bot_name
        if not label and bot_id:
            try:
                label = get_config(bot_id).name
            except KeyError:
                label = bot_id
        label = label or "Bot"
        bot_name = label
    col("trades").insert_one(
        {
            "id": _next_id("trades"),
            "bot_id": bot_id,
            "ts": _now(),
            "side": side,
            "inst_id": inst_id,
            "qty": qty,
            "avg_px": avg_px,
            "fee": fee,
            "fee_ccy": fee_ccy,
            "fee_usdt": fee_usdt,
            "pnl_realized": pnl_realized,
            "order_id": order_id,
            "status": status,
            "origin": origin,
            "origin_label": label,
            "bot_name": bot_name,
            **({"okx_account_id": aid} if (aid := _account_id_for_bot(bot_id)) else {}),
            **({"user_id": uid} if (uid := _uid()) else {}),
        }
    )
    remember_order_origin(
        order_id,
        origin=origin,
        bot_id=bot_id,
        bot_name=bot_name,
        cl_ord_id=cl_ord_id,
    )


def list_trades(limit: int = 50, bot_id: str | None = None) -> list[Trade]:
    q = _scope_q({"bot_id": bot_id} if bot_id else None)
    rows = list(col("trades").find(q).sort("id", DESCENDING).limit(limit))
    names = _bot_names()
    trades: list[Trade] = []
    for row in rows:
        origin, label = infer_origin(
            origin=row.get("origin"),
            origin_label=row.get("origin_label") or row.get("bot_name"),
            bot_id=row.get("bot_id"),
            bot_name=row.get("bot_name"),
            names=names,
        )
        trades.append(
            Trade(
                id=int(row.get("id") or 0),
                ts=row.get("ts") or "",
                side=row.get("side") or "",
                inst_id=row.get("inst_id") or "",
                qty=row.get("qty"),
                avg_px=row.get("avg_px"),
                fee=row.get("fee"),
                fee_ccy=row.get("fee_ccy"),
                fee_usdt=row.get("fee_usdt"),
                pnl_realized=row.get("pnl_realized"),
                order_id=row.get("order_id"),
                status=row.get("status") or "filled",
                origin=origin,
                origin_label=label,
                bot_id=row.get("bot_id"),
                bot_name=label if origin == "bot" else None,
            )
        )
    return trades


def realized_pnl_sum(bot_id: str | None = None) -> float:
    match: dict[str, Any] = {"pnl_realized": {"$ne": None}}
    if bot_id:
        match["bot_id"] = bot_id
    match.update(_scope_q())
    rows = list(
        col("trades").aggregate(
            [{"$match": match}, {"$group": {"_id": None, "total": {"$sum": "$pnl_realized"}}}]
        )
    )
    if not rows:
        return 0.0
    return float(rows[0].get("total") or 0)


def add_event(message: str, level: str = "info", bot_id: str = "system") -> None:
    bid = (bot_id or "system").strip() or "system"
    ev: dict[str, Any] = {
        "id": _next_id("events"),
        "bot_id": bid,
        "ts": _now(),
        "level": level,
        "message": message,
    }
    aid = _account_id_for_bot(bid)
    if aid:
        ev["okx_account_id"] = aid
    _stamp_owner(ev)
    col("events").insert_one(ev)
    extra = list(col("events").find({"bot_id": bid}).sort("id", DESCENDING).skip(200))
    if extra:
        col("events").delete_many({"_id": {"$in": [e["_id"] for e in extra]}})


def list_events(limit: int = 40, bot_id: str = "system") -> list[Event]:
    rows = list(col("events").find(_scope_q({"bot_id": bot_id})).sort("id", DESCENDING).limit(limit))
    return [
        Event(
            id=int(r.get("id") or 0),
            ts=r.get("ts") or "",
            level=r.get("level") or "info",
            message=r.get("message") or "",
        )
        for r in rows
    ]


def add_execution(
    *,
    bot_id: str,
    mode: str,
    action: str,
    reason: str,
    would_trade: bool = False,
    executed: bool = False,
    inst_id: str | None = None,
    price: float | None = None,
    state: str | None = None,
    drop_pct: float | None = None,
    pnl_pct: float | None = None,
    pnl: float | None = None,
    target_price: float | None = None,
    poll_interval: float | None = None,
    checks: list[dict[str, Any]] | None = None,
    bot_name: str | None = None,
    trigger: str = "auto",
) -> dict[str, Any]:
    trig = str(trigger or "auto").strip().lower() or "auto"
    if trig not in {"auto", "manual"}:
        trig = "auto"
    reason_s = str(reason or "")
    if trig == "manual" and not reason_s.lower().startswith("[manual]"):
        reason_s = f"[manual] {reason_s}".strip()
    doc = {
        "id": _next_id("executions"),
        "bot_id": bot_id,
        "bot_name": bot_name,
        "ts": _now(),
        "mode": mode,
        "action": action,
        "reason": reason_s,
        "would_trade": bool(would_trade),
        "executed": bool(executed),
        "inst_id": inst_id,
        "price": price,
        "state": state,
        "drop_pct": drop_pct,
        "pnl_pct": pnl_pct,
        "pnl": pnl,
        "target_price": target_price,
        "poll_interval": poll_interval,
        "checks": checks or [],
        "trigger": trig,
        "manual": trig == "manual",
    }
    aid = _account_id_for_bot(bot_id)
    if aid:
        doc["okx_account_id"] = aid
    _stamp_owner(doc)
    col("executions").insert_one(doc)
    extra = list(col("executions").find({"bot_id": bot_id}).sort("id", DESCENDING).skip(80))
    if extra:
        col("executions").delete_many({"_id": {"$in": [e["_id"] for e in extra]}})
    doc.pop("_id", None)
    return doc


def cleanup_executions(
    *,
    wait_max_age_hours: float = 6.0,
    executed_max_age_days: float = 14.0,
) -> dict[str, int]:
    """
    Limpa log de decisões do bot (não mexe em trades/ordens reais).
    - waits (não executados): remove após wait_max_age_hours
    - executados: remove após executed_max_age_days
    """
    now = datetime.now(timezone.utc)
    wait_cut = (now - timedelta(hours=max(1.0, float(wait_max_age_hours)))).isoformat(
        timespec="seconds"
    )
    exec_cut = (now - timedelta(days=max(1.0, float(executed_max_age_days)))).isoformat(
        timespec="seconds"
    )
    r_wait = col("executions").delete_many(
        {
            "executed": {"$ne": True},
            "ts": {"$lt": wait_cut},
        }
    )
    r_done = col("executions").delete_many(
        {
            "executed": True,
            "ts": {"$lt": exec_cut},
        }
    )
    return {
        "deleted_waits": int(r_wait.deleted_count or 0),
        "deleted_executed": int(r_done.deleted_count or 0),
    }


_BOT_DEFAULTS: dict[str, Any] = {
    "default_interval_min": 30.0,
    "exec_cleanup_wait_hours": 6.0,
    "exec_cleanup_executed_days": 14.0,
    "portfolio_interval_min": 2.0,
}


def get_bot_defaults() -> dict[str, Any]:
    row = col("settings").find_one({"_id": _settings_id("bot_defaults")}) or {}
    out = dict(_BOT_DEFAULTS)
    for k, v in row.items():
        if k in {"_id", "updated_at"}:
            continue
        if k in out:
            out[k] = v
    out["default_interval_min"] = max(1.0, min(1440.0, float(out.get("default_interval_min") or 30)))
    out["exec_cleanup_wait_hours"] = max(1.0, min(168.0, float(out.get("exec_cleanup_wait_hours") or 6)))
    out["exec_cleanup_executed_days"] = max(1.0, min(90.0, float(out.get("exec_cleanup_executed_days") or 14)))
    return out


def save_bot_defaults(patch: dict[str, Any]) -> dict[str, Any]:
    cur = get_bot_defaults()
    for k in _BOT_DEFAULTS:
        if k in (patch or {}) and patch[k] is not None:
            cur[k] = patch[k]
    cur["default_interval_min"] = max(1.0, min(1440.0, float(cur["default_interval_min"])))
    cur["exec_cleanup_wait_hours"] = max(1.0, min(168.0, float(cur["exec_cleanup_wait_hours"])))
    cur["exec_cleanup_executed_days"] = max(1.0, min(90.0, float(cur["exec_cleanup_executed_days"])))
    col("settings").update_one(
        {"_id": _settings_id("bot_defaults")},
        {"$set": {**cur, "updated_at": _now()}},
        upsert=True,
    )
    return get_bot_defaults()


def list_executions(limit: int = 50, bot_id: str | None = None) -> list[dict[str, Any]]:
    q = _scope_q({"mode": "live"})
    if bot_id:
        q["bot_id"] = bot_id
    rows = list(col("executions").find(q, {"_id": 0}).sort("id", DESCENDING).limit(limit))
    return rows


def save_portfolio_snapshot(
    total_eq: float,
    assets: list[dict[str, Any]],
    usdt_brl: float | None = None,
) -> None:
    doc: dict[str, Any] = {"bot_id": "wallet", "ts": _now(), "total_eq": total_eq, "assets": assets}
    if usdt_brl is not None and float(usdt_brl) > 0:
        doc["usdt_brl"] = float(usdt_brl)
    aid = _active_account_id()
    if aid:
        doc["okx_account_id"] = aid
    _stamp_owner(doc)
    col("portfolio_snapshots").insert_one(doc)
    _adopt_legacy_wallet_snapshots()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(timespec="seconds")
    col("portfolio_snapshots").delete_many(_wallet_snap_q(ts={"$lt": cutoff}))


def _adopt_legacy_wallet_snapshots() -> None:
    uid = _uid()
    aid = _active_account_id()
    if not uid or not aid:
        return
    col("portfolio_snapshots").update_many(
        {
            "bot_id": "wallet",
            "okx_account_id": aid,
            "$or": [{"user_id": {"$exists": False}}, {"user_id": None}, {"user_id": ""}],
        },
        {"$set": {"user_id": uid}},
    )


def _parse_snap_ts(ts: Any) -> Optional[datetime]:
    if isinstance(ts, datetime):
        dt = ts
    else:
        raw = str(ts or "").strip().replace("Z", "+00:00")
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _period_now() -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Sao_Paulo"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=-3)))


def period_starts() -> dict[str, datetime]:
    """Início de hoje / semana (seg) / mês no horário de Brasília."""
    now = _period_now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "today": today,
        "week": today - timedelta(days=now.weekday()),
        "month": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        "h24": datetime.now(timezone.utc) - timedelta(hours=24),
    }


def portfolio_eq_at(hours_ago: float) -> Optional[float]:
    _adopt_legacy_wallet_snapshots()
    target = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat(timespec="seconds")
    row = col("portfolio_snapshots").find_one(
        _wallet_snap_q(ts={"$lte": target}),
        sort=[("ts", DESCENDING)],
    )
    return float(row["total_eq"]) if row else None


def portfolio_eq_since(start: datetime) -> Optional[float]:
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    row = col("portfolio_snapshots").find_one(
        _wallet_snap_q(ts={"$gte": start.astimezone(timezone.utc).isoformat(timespec="seconds")}),
        sort=[("ts", ASCENDING)],
    )
    return float(row["total_eq"]) if row else None


def portfolio_eq_open(start: datetime) -> Optional[float]:
    """Saldo na abertura do período.

    Usa o último snapshot ≤ início. Se não houver, só aceita o primeiro
    snapshot posterior quando ainda é do mesmo dia — senão semana/mês
    copiavam o saldo de hoje.
    """
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    start_utc = start.astimezone(timezone.utc)
    start_iso = start_utc.isoformat(timespec="seconds")
    row = col("portfolio_snapshots").find_one(
        _wallet_snap_q(ts={"$lte": start_iso}),
        sort=[("ts", DESCENDING)],
    )
    if row is not None and row.get("total_eq") is not None:
        return float(row["total_eq"])
    row = col("portfolio_snapshots").find_one(
        _wallet_snap_q(ts={"$gte": start_iso}),
        sort=[("ts", ASCENDING)],
    )
    if not row or row.get("total_eq") is None:
        return None
    ts = _parse_snap_ts(row.get("ts"))
    if ts is None or ts.date() != start_utc.date():
        return None
    return float(row["total_eq"])


def portfolio_eq_today_open() -> Optional[float]:
    start = _period_now().replace(hour=0, minute=0, second=0, microsecond=0)
    return portfolio_eq_open(start)


def portfolio_eq_week_open() -> Optional[float]:
    now = _period_now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
    return portfolio_eq_open(start)


def portfolio_eq_month_open() -> Optional[float]:
    now = _period_now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return portfolio_eq_open(start)


def _snapshot_point(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ts": row.get("ts"),
        "total_eq": float(row.get("total_eq") or 0),
    }
    rate = row.get("usdt_brl")
    if rate is not None:
        try:
            r = float(rate)
            if r > 0:
                out["usdt_brl"] = r
                out["total_eq_brl"] = out["total_eq"] * r
        except (TypeError, ValueError):
            pass
    return out


def list_portfolio_history(limit: int = 200) -> list[dict[str, Any]]:
    """Últimos N snapshots (mais recentes), em ordem cronológica."""
    lim = max(2, min(int(limit), 2000))
    rows = list(
        col("portfolio_snapshots")
        .find(_wallet_snap_q(), {"_id": 0, "ts": 1, "total_eq": 1, "usdt_brl": 1})
        .sort("ts", DESCENDING)
        .limit(lim)
    )
    rows.reverse()
    return [_snapshot_point(r) for r in rows]


def list_portfolio_daily(days: int = 45) -> list[dict[str, Any]]:
    """Último saldo de cada dia UTC."""
    return list_portfolio_series(days=days, grain="day")


def list_portfolio_series(days: int = 45, grain: str = "auto") -> list[dict[str, Any]]:
    """Série de patrimônio local (a OKX não expõe histórico na API).

    grain:
      - day: 1 ponto/dia (estilo OKX em períodos longos)
      - hour: 1 ponto/hora (7D mais contínuo)
      - auto: hour se days<=7, senão day
    """
    d = max(1, min(int(days), 180))
    g = (grain or "auto").lower()
    if g == "auto":
        g = "hour" if d <= 7 else "day"
    if g not in {"day", "hour"}:
        g = "day"
    cutoff = (datetime.now(timezone.utc) - timedelta(days=d)).isoformat(timespec="seconds")
    rows = list(
        col("portfolio_snapshots")
        .find(
            _wallet_snap_q(ts={"$gte": cutoff}),
            {"_id": 0, "ts": 1, "total_eq": 1, "usdt_brl": 1},
        )
        .sort("ts", ASCENDING)
    )
    buckets: dict[str, dict[str, Any]] = {}
    for r in rows:
        ts = str(r.get("ts") or "")
        if g == "hour":
            key = ts[:13] if len(ts) >= 13 else ""  # YYYY-MM-DDTHH
        else:
            key = ts[:10] if len(ts) >= 10 else ""
        if not key:
            continue
        buckets[key] = r  # último do bucket
    return [_snapshot_point(buckets[k]) for k in sorted(buckets.keys())]


def get_order_limits() -> dict[str, float]:
    from .order_limits import DEFAULT_MAX_USD, DEFAULT_MIN_USD, limits_from_row

    row = col("settings").find_one({"_id": _settings_id("order_limits")})
    out = limits_from_row(row)
    if not row:
        return {"min_usd": DEFAULT_MIN_USD, "max_usd": DEFAULT_MAX_USD}
    return out


def save_order_limits(min_usd: float, max_usd: float) -> dict[str, float]:
    lo = float(min_usd)
    hi = float(max_usd)
    if lo > hi:
        raise ValueError("Mínimo não pode ser maior que o máximo")
    col("settings").update_one(
        {"_id": _settings_id("order_limits")},
        {"$set": {"min_usd": lo, "max_usd": hi, "updated_at": _now()}},
        upsert=True,
    )
    return get_order_limits()


def _mongo_get_api_cache(key: str, ttl_s: float) -> Optional[dict[str, Any]]:
    row = col("api_cache").find_one({"_id": key})
    if not row:
        return None
    ts = float(row.get("ts") or 0)
    if time.time() - ts > float(ttl_s):
        col("api_cache").delete_one({"_id": key})
        return None
    payload = row.get("payload")
    if not isinstance(payload, dict):
        col("api_cache").delete_one({"_id": key})
        return None
    return {"ts": ts, "payload": payload}


def _mongo_set_api_cache(key: str, payload: dict[str, Any], *, kind: str = "") -> None:
    col("api_cache").update_one(
        {"_id": key},
        {"$set": {"ts": time.time(), "payload": payload, "kind": kind, "updated_at": _now()}},
        upsert=True,
    )


def _mongo_clear_api_cache(*, kind: Optional[str] = None) -> None:
    if kind:
        col("api_cache").delete_many({"kind": kind})
    else:
        col("api_cache").delete_many({})


def get_api_cache(key: str, ttl_s: float) -> Optional[dict[str, Any]]:
    from . import cache as api_cache

    return api_cache.get_api_cache(key, ttl_s)


def set_api_cache(key: str, payload: dict[str, Any], *, kind: str = "") -> None:
    from . import cache as api_cache

    api_cache.set_api_cache(key, payload, kind=kind)


def clear_api_cache(*, kind: Optional[str] = None) -> None:
    from . import cache as api_cache

    api_cache.clear_api_cache(kind=kind)


_HUNTER_DEFAULTS: dict[str, Any] = {
    "enabled": False,
    "auto_rotate": False,
    "bot_id": None,
    "quote": "USDT",
    "min_drop_pct": 1.5,
    "max_drop_pct": 35.0,
    "min_vol_usd": 80_000.0,
    "max_spread_pct": 1.0,
    "require_tradeable": True,
    "top_n": 10,
    "strategy_id": "deep_dip",
    "scan_interval_min": 10.0,
    "cooldown_min": 90,
    "cache_ttl_s": 1800,
    "quote_amount": 0.0,
    "budget_ccy": "BRL",
    "bot_interval_min": 3.0,
    "run_days": 90.0,
    "validate_days": 90,
    "horizon": "all",
    "blacklist": [],
}


def get_hunter_settings() -> dict[str, Any]:
    row = col("settings").find_one({"_id": _settings_id("hunter")}) or {}
    out = dict(_HUNTER_DEFAULTS)
    for k, v in row.items():
        if k in {"_id", "updated_at"}:
            continue
        out[k] = v
    out["blacklist"] = [str(x).upper() for x in (out.get("blacklist") or []) if str(x).strip()]
    # Cache do radar: 30 min (migra default antigo de 3 min)
    ttl = int(out.get("cache_ttl_s") or 1800)
    if ttl <= 180:
        ttl = 1800
    out["cache_ttl_s"] = max(300, min(3600, ttl))
    return out


def save_hunter_settings(patch: dict[str, Any]) -> dict[str, Any]:
    cur = get_hunter_settings()
    allowed = set(_HUNTER_DEFAULTS.keys())
    for k, v in (patch or {}).items():
        if k not in allowed:
            continue
        cur[k] = v
    if cur.get("bot_id"):
        cur["bot_id"] = str(cur["bot_id"]).strip() or None
    cur["quote"] = str(cur.get("quote") or "USDT").upper()
    cur["strategy_id"] = str(cur.get("strategy_id") or "deep_dip").strip().lower()
    cur["min_drop_pct"] = float(cur.get("min_drop_pct") or 5)
    cur["max_drop_pct"] = float(cur.get("max_drop_pct") or 28)
    if cur["min_drop_pct"] > cur["max_drop_pct"]:
        cur["min_drop_pct"], cur["max_drop_pct"] = cur["max_drop_pct"], cur["min_drop_pct"]
    cur["min_vol_usd"] = max(0.0, float(cur.get("min_vol_usd") or 0))
    cur["max_spread_pct"] = max(0.05, min(5.0, float(cur.get("max_spread_pct") or 0.8)))
    cur["require_tradeable"] = bool(cur.get("require_tradeable"))
    cur["top_n"] = max(1, min(10, int(cur.get("top_n") or 10)))
    cur["scan_interval_min"] = max(1.0, min(60.0, float(cur.get("scan_interval_min") or 5)))
    cur["cooldown_min"] = max(0, min(24 * 60, int(cur.get("cooldown_min") or 90)))
    cur["cache_ttl_s"] = max(300, min(3600, int(cur.get("cache_ttl_s") or 1800)))
    cur["quote_amount"] = max(0.0, float(cur.get("quote_amount") or 0))
    cur["budget_ccy"] = str(cur.get("budget_ccy") or "BRL").upper()
    if cur["budget_ccy"] not in {"BRL", "USDT", "USDC", "USD"}:
        cur["budget_ccy"] = "BRL"
    cur.pop("budget_brl", None)
    cur["blacklist"] = [str(x).upper() for x in (cur.get("blacklist") or []) if str(x).strip()]
    # Permitir habilitar o auto-scan do radar
    cur["enabled"] = bool(cur.get("enabled"))
    cur["auto_rotate"] = False
    vd = int(cur.get("validate_days") or 90)
    cur["horizon"] = "all"
    cur["validate_days"] = vd if vd in {7, 30, 60, 90} else 90
    cur["run_days"] = float(cur.get("run_days") or cur["validate_days"])
    col("settings").update_one(
        {"_id": _settings_id("hunter")},
        {"$set": {**cur, "updated_at": _now()}, "$unset": {"budget_brl": ""}},
        upsert=True,
    )
    return get_hunter_settings()


def add_hunter_rotation(
    *,
    bot_id: str,
    from_inst: str,
    to_inst: str,
    score: Any = None,
    reason: str = "",
) -> None:
    rot: dict[str, Any] = {
        "bot_id": bot_id,
        "from_inst": str(from_inst or "").upper(),
        "to_inst": str(to_inst or "").upper(),
        "score": score,
        "reason": reason,
        "ts": _now(),
    }
    aid = _account_id_for_bot(bot_id) or _active_account_id()
    if aid:
        rot["okx_account_id"] = aid
    _stamp_owner(rot)
    col("hunter_rotations").insert_one(rot)
    if from_inst:
        inst_u = str(from_inst).upper()
        uid = _uid()
        cool: dict[str, Any] = {"ts": time.time(), "bot_id": bot_id, "inst": inst_u}
        if aid:
            cool["okx_account_id"] = aid
        if uid:
            cool["user_id"] = uid
        col("hunter_cooldowns").update_one(
            {"_id": f"{uid}:{inst_u}" if uid else inst_u},
            {"$set": cool},
            upsert=True,
        )


def hunter_cooldown_insts(cooldown_min: int) -> list[str]:
    cutoff = time.time() - max(0, int(cooldown_min)) * 60
    out = []
    for row in col("hunter_cooldowns").find(_scope_q()):
        if float(row.get("ts") or 0) >= cutoff:
            inst = str(row.get("inst") or row.get("_id") or "")
            if ":" in inst and _uid() and inst.startswith(_uid() + ":"):
                inst = inst.split(":", 1)[-1]
            out.append(inst.upper())
    return [x for x in out if x]


def list_hunter_rotations(limit: int = 30) -> list[dict[str, Any]]:
    rows = list(
        col("hunter_rotations")
        .find(_scope_q(), {"_id": 0})
        .sort("ts", DESCENDING)
        .limit(max(1, min(int(limit), 100)))
    )
    return rows
