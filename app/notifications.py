"""Sistema de notificações em tempo real via SSE."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from collections import deque

from . import db


# ---------------------------------------------------------------------------
# Modelo de notificação
# ---------------------------------------------------------------------------

@dataclass
class Notification:
    id: str = ""
    kind: str = ""          # order_filled, order_cancelled, bot_buy, bot_sell, bot_error, hunter_alert, portfolio_change, system
    title: str = ""
    body: str = ""
    icon: str = ""          # emoji ou url
    tone: str = ""          # up, down, warn, info
    ts: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)
    read: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_sse(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False)
        return f"event: notification\ndata: {payload}\n\n"


# ---------------------------------------------------------------------------
# Hub de notificações (pub/sub por user)
# ---------------------------------------------------------------------------

_MAX_HISTORY = 50


class NotificationHub:
    def __init__(self) -> None:
        # user_id -> list of queues (uma por conexão SSE ativa)
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        # user_id -> histórico recente
        self._history: dict[str, deque[Notification]] = {}
        self._counter: int = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"n-{int(time.time())}-{self._counter}"

    def emit(
        self,
        user_id: str,
        *,
        kind: str,
        title: str,
        body: str = "",
        icon: str = "",
        tone: str = "info",
        data: dict[str, Any] | None = None,
    ) -> Notification:
        """Emite uma notificação para um usuário."""
        uid = user_id or "_global"
        notif = Notification(
            id=self._next_id(),
            kind=kind,
            title=title,
            body=body,
            icon=icon,
            tone=tone,
            ts=time.time(),
            data=data or {},
        )
        # Histórico
        hist = self._history.setdefault(uid, deque(maxlen=_MAX_HISTORY))
        hist.appendleft(notif)
        # Broadcast para subscribers ativos
        for queue in self._subscribers.get(uid, []):
            try:
                queue.put_nowait(notif)
            except asyncio.QueueFull:
                pass
        # Broadcast global também
        if uid != "_global":
            for queue in self._subscribers.get("_global", []):
                try:
                    queue.put_nowait(notif)
                except asyncio.QueueFull:
                    pass
        return notif

    def subscribe(self, user_id: str) -> asyncio.Queue:
        """Cria uma fila para receber notificações em tempo real."""
        uid = user_id or "_global"
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        subs = self._subscribers.setdefault(uid, [])
        subs.append(queue)
        return queue

    def unsubscribe(self, user_id: str, queue: asyncio.Queue) -> None:
        uid = user_id or "_global"
        subs = self._subscribers.get(uid, [])
        try:
            subs.remove(queue)
        except ValueError:
            pass

    def history(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        uid = user_id or "_global"
        hist = self._history.get(uid, deque())
        return [n.to_dict() for n in list(hist)[:limit]]

    def mark_read(self, user_id: str, notif_id: str | None = None) -> None:
        uid = user_id or "_global"
        hist = self._history.get(uid, deque())
        for n in hist:
            if notif_id is None or n.id == notif_id:
                n.read = True

    def unread_count(self, user_id: str) -> int:
        uid = user_id or "_global"
        hist = self._history.get(uid, deque())
        return sum(1 for n in hist if not n.read)


# Instância global
hub = NotificationHub()


# ---------------------------------------------------------------------------
# Helpers para emitir de qualquer lugar do app
# ---------------------------------------------------------------------------

def notify_order_filled(user_id: str, inst_id: str, side: str, qty: float, px: float, quote: str = "USDT") -> None:
    verb = "Compra" if side == "buy" else "Venda"
    icon = "🟢" if side == "buy" else "🔴"
    tone = "up" if side == "buy" else "down"
    hub.emit(
        user_id,
        kind="order_filled",
        title=f"{verb} executada",
        body=f"{qty:g} {inst_id.split('-')[0]} @ {px:g} {quote}",
        icon=icon,
        tone=tone,
        data={"inst_id": inst_id, "side": side, "qty": qty, "px": px},
    )


def notify_order_cancelled(user_id: str, inst_id: str, side: str, reason: str = "") -> None:
    hub.emit(
        user_id,
        kind="order_cancelled",
        title="Ordem cancelada",
        body=f"{inst_id} {side}" + (f" — {reason}" if reason else ""),
        icon="⚠️",
        tone="warn",
        data={"inst_id": inst_id, "side": side, "reason": reason},
    )


def notify_bot_trade(user_id: str, bot_name: str, side: str, inst_id: str, qty: float, px: float) -> None:
    verb = "comprou" if side == "buy" else "vendeu"
    icon = "🤖"
    tone = "up" if side == "buy" else "down"
    hub.emit(
        user_id,
        kind=f"bot_{side}",
        title=f"Bot {verb}",
        body=f"{bot_name}: {qty:g} {inst_id.split('-')[0]} @ {px:g}",
        icon=icon,
        tone=tone,
        data={"bot_name": bot_name, "inst_id": inst_id, "side": side, "qty": qty, "px": px},
    )


def notify_bot_error(user_id: str, bot_name: str, error: str) -> None:
    hub.emit(
        user_id,
        kind="bot_error",
        title=f"Erro no bot",
        body=f"{bot_name}: {error[:100]}",
        icon="❌",
        tone="warn",
        data={"bot_name": bot_name, "error": error},
    )


def notify_hunter_alert(user_id: str, inst_id: str, drop_pct: float, price: float) -> None:
    hub.emit(
        user_id,
        kind="hunter_alert",
        title="Dip detectado",
        body=f"{inst_id} caiu {drop_pct:.1f}% — preço {price:g}",
        icon="🎯",
        tone="warn",
        data={"inst_id": inst_id, "drop_pct": drop_pct, "price": price},
    )


def notify_portfolio_change(user_id: str, title: str, body: str, tone: str = "info") -> None:
    hub.emit(
        user_id,
        kind="portfolio_change",
        title=title,
        body=body,
        icon="📊",
        tone=tone,
    )


def notify_system(user_id: str, title: str, body: str, tone: str = "warn") -> None:
    hub.emit(
        user_id,
        kind="system",
        title=title,
        body=body,
        icon="⚙️",
        tone=tone,
    )
