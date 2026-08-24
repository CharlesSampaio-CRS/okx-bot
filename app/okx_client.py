from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from typing import Any, Optional

import httpx

from . import credentials
from .config import settings


OKX_ERR_PT: dict[str, str] = {
    "51001": "Par inválido ou inexistente na OKX — use formato BASE-QUOTE (ex. SOL-USDT), confira demo/live e se o par existe em Spot.",
    "51155": "Este par ou cripto não pode ser negociado na sua região por restrições de compliance local da OKX.",
    "51008": "USDT/saldo insuficiente na conta trading. Transfira do funding ou reduza o valor da ordem (este app não usa empréstimo/margem).",
    "51009": "Envio de ordens bloqueado pela OKX nesta conta.",
    "51020": "Quantidade/valor abaixo do mínimo permitido para este par (minSz).",
    "51120": "Quantidade abaixo do mínimo permitido para este par.",
    "51121": "Quantidade deve ser múltiplo do lot size do par.",
    "51127": "Saldo disponível é zero na conta trading.",
    "51000": "Parâmetro inválido na ordem.",
    "51131": "Preço da ordem fora dos limites permitidos.",
    "51147": "Ordem rejeitada — verifique parâmetros e saldo.",
    "50011": "Limite de taxa de requisições atingido — tente novamente em instantes.",
    "50026": "Limite de taxa de requisições atingido — tente novamente em instantes.",
    "50061": "Limite de taxa de ordens da conta atingido — aguarde e tente de novo.",
    "51400": "Ordem já executada ou cancelada",
    "51401": "Ordem já cancelada",
    "51402": "Ordem já executada",
}

# Cancelamento: ordem já preenchida/cancelada/inexistente (situação esperada, não erro crítico)
OKX_CANCEL_GONE_SCODES = frozenset({"51400", "51401", "51402"})


class OkxError(RuntimeError):
    def __init__(self, message: str, code: str = "", payload: Any = None):
        super().__init__(message)
        self.code = str(code or "").strip()
        self.payload = payload

    def _payload_dict(self) -> dict[str, Any]:
        return self.payload if isinstance(self.payload, dict) else {}

    def primary_message(self) -> str:
        payload = self._payload_dict()
        data = payload.get("data")
        if isinstance(data, list):
            for row in data:
                if not isinstance(row, dict):
                    continue
                sm = str(row.get("sMsg") or row.get("msg") or "").strip()
                if not sm:
                    continue
                sc = str(row.get("sCode") or row.get("code") or "").strip()
                if sc and sc not in {"0", ""}:
                    return f"{sm} (OKX {sc})"
                return sm
        sm = str(payload.get("sMsg") or payload.get("msg") or "").strip()
        if sm:
            sc = str(payload.get("sCode") or payload.get("code") or self.code or "").strip()
            if sc and sc not in {"0", ""}:
                return f"{sm} (OKX {sc})"
            return sm
        msg = super().__str__().strip()
        code = self.code or str(payload.get("code") or "").strip()
        if code and code not in {"0", ""}:
            if msg:
                return f"{msg} (OKX {code})"
            return f"erro OKX {code}"
        return msg or "erro OKX"

    def __str__(self) -> str:
        friendly = self.friendly_pt()
        return friendly or self.primary_message()

    def _operation_scodes(self) -> list[str]:
        codes: list[str] = []
        payload = self._payload_dict()
        data = payload.get("data")
        if isinstance(data, list):
            for row in data:
                if not isinstance(row, dict):
                    continue
                sc = str(row.get("sCode") or row.get("code") or "").strip()
                if sc and sc not in {"0", ""} and sc not in codes:
                    codes.append(sc)
        for sc in (self.code, str(payload.get("sCode") or ""), str(payload.get("code") or "")):
            sc = str(sc or "").strip()
            if sc and sc not in {"0", ""} and sc not in codes:
                codes.append(sc)
        return codes

    def friendly_pt(self) -> str:
        for sc in self._operation_scodes():
            hit = OKX_ERR_PT.get(sc)
            if hit:
                # Mensagem OKX às vezes cita a moeda (ex. USDT)
                pm = self.primary_message()
                if sc == "51008" and pm:
                    m = re.search(r"available\s+(\w+)\s+balance", pm, re.I)
                    if m:
                        ccy = m.group(1).upper()
                        return (
                            f"Saldo de {ccy} insuficiente na conta trading. "
                            f"Transfira {ccy} do funding → trading ou reduza a ordem "
                            f"(sem empréstimo/margem neste app)."
                        )
                return hit
        pm = self.primary_message().lower()
        if "compliance restrictions" in pm or "local compliance" in pm:
            return OKX_ERR_PT["51155"]
        if "insufficient" in pm and "balance" in pm:
            return OKX_ERR_PT["51008"]
        if "minimum amount" in pm or "min size" in pm or "greater than the min" in pm:
            return OKX_ERR_PT["51020"]
        if "order cancellation failed" in pm or (
            "filled" in pm and "canceled" in pm and "does not exist" in pm
        ):
            return OKX_ERR_PT["51400"]
        if "request too frequent" in pm or "rate limit" in pm:
            return OKX_ERR_PT["50011"]
        if "doesn't exist" in pm or "does not exist" in pm:
            return OKX_ERR_PT["51001"]
        return ""

    def is_cancel_gone(self) -> bool:
        return bool(OKX_CANCEL_GONE_SCODES.intersection(self._operation_scodes()))

    def format_full(self) -> str:
        lines: list[str] = []
        payload = self._payload_dict()
        top_msg = str(payload.get("msg") or super().__str__() or "").strip()
        top_code = str(payload.get("code") or "").strip()
        if top_msg:
            lines.append(top_msg)
        if top_code and top_code not in {"0", ""}:
            lines.append(f"Código OKX (resposta): {top_code}")
        code = self.code
        if code and code not in {"0", ""} and code != top_code:
            lines.append(f"Código OKX (operação): {code}")
        base = super().__str__().strip()
        if base and base not in {top_msg} and not any(base in x for x in lines):
            lines.append(base)

        data = payload.get("data")
        if isinstance(data, list) and data:
            lines.append("")
            lines.append("Detalhes por operação:")
            for i, row in enumerate(data, 1):
                if not isinstance(row, dict):
                    continue
                sc = row.get("sCode") or row.get("code") or "—"
                sm = row.get("sMsg") or row.get("msg") or "—"
                lines.append(f"  {i}. [{sc}] {sm}")
                extras = []
                for key in ("instId", "ordId", "clOrdId", "tag", "ts"):
                    val = row.get(key)
                    if val not in (None, ""):
                        extras.append(f"{key}={val}")
                if extras:
                    lines.append(f"     {' · '.join(extras)}")
        elif payload.get("sMsg") or payload.get("sCode"):
            sc = payload.get("sCode") or payload.get("code") or "—"
            sm = payload.get("sMsg") or payload.get("msg") or "—"
            if not any(str(sm) in line for line in lines):
                lines.append(f"[{sc}] {sm}")

        if payload:
            try:
                lines.append("")
                lines.append("Resposta completa OKX:")
                lines.append(json.dumps(payload, ensure_ascii=False, indent=2))
            except Exception:
                pass

        text = "\n".join(lines).strip()
        return text or self.primary_message()

    def as_detail(self) -> dict[str, Any]:
        friendly = self.friendly_pt()
        primary = self.primary_message()
        scodes = self._operation_scodes()
        # Erros conhecidos (ex. 51400): só mensagem amigável — sem dump JSON da OKX
        if friendly:
            technical = ""
        else:
            technical = self.format_full()
        return {
            "message": friendly or primary,
            "summary": friendly or primary,
            "friendly": friendly,
            "technical": technical,
            "full": technical,
            "code": self.code or str(self._payload_dict().get("code") or ""),
            "scode": scodes[0] if scodes else "",
            "cancel_gone": self.is_cancel_gone(),
        }


def _order_err(row: dict[str, Any], fallback: str) -> OkxError:
    scode = str(row.get("sCode") or row.get("code") or "").strip()
    smsg = str(row.get("sMsg") or row.get("msg") or "").strip()
    return OkxError(smsg or fallback, code=scode, payload=row)


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _sign(timestamp: str, method: str, path: str, body: str, secret: str) -> str:
    prehash = f"{timestamp}{method.upper()}{path}{body}"
    digest = hmac.new(secret.encode(), prehash.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def icon_urls(ccy: str) -> tuple[str, str]:
    symbol = (ccy or "").strip()
    lower = symbol.lower()
    upper = symbol.upper()
    return (
        f"https://www.okx.com/cdn/oksupport/asset/currency/icon/{lower}.png",
        f"https://static.okx.com/cdn/wallet/logo/{upper}.png",
    )


def parse_inst(inst_id: str) -> tuple[str, str]:
    """Aceita só par Spot BASE-QUOTE (ex. SOL-USDT). Rejeita SWAP/FUTURES/OPTION."""
    raw = (inst_id or "").strip().upper()
    if not raw:
        raise ValueError("par inválido: vazio")
    parts = raw.split("-")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"par inválido «{inst_id}» — este app usa só Spot (BASE-QUOTE), "
            "não SWAP/Futures (ex. BTC-USDT-SWAP)"
        )
    suffix_block = {"SWAP", "FUTURES", "OPTION", "PERP"}
    if parts[0] in suffix_block or parts[1] in suffix_block:
        raise ValueError(f"par inválido «{inst_id}» — somente Spot")
    return parts[0], parts[1]


def is_spot_inst_id(inst_id: str) -> bool:
    try:
        parse_inst(inst_id)
        return True
    except ValueError:
        return False


SPOT_QUOTE_CCYS = {"USDT", "USDC", "BRL", "BTC", "ETH", "USD", "EUR", "TRY"}
SPOT_STABLE_CCYS = {"USDT", "USDC", "BRL", "USD", "EUR", "TRY", "DAI", "BUSD", "TUSD", "FDUSD"}


def round_to_lot(size: float, lot_sz: str, min_sz: str) -> str:
    lot = Decimal(str(lot_sz))
    minimum = Decimal(str(min_sz))
    val = Decimal(str(size))
    steps = (val / lot).to_integral_value(rounding=ROUND_DOWN)
    rounded = steps * lot
    if rounded < minimum:
        raise OkxError(f"tamanho {rounded} abaixo do mínimo {minimum}")
    text = format(rounded, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def round_to_tick(price: float, tick_sz: str, side: str = "buy") -> str:
    from decimal import ROUND_CEILING

    tick = Decimal(str(tick_sz or "0.00000001"))
    if tick <= 0:
        tick = Decimal("0.00000001")
    val = Decimal(str(price))
    steps = val / tick
    if (side or "buy").lower() == "sell":
        rounded = steps.to_integral_value(rounding=ROUND_CEILING) * tick
    else:
        rounded = steps.to_integral_value(rounding=ROUND_DOWN) * tick
    if rounded <= 0:
        raise OkxError("preço inválido após arredondar o tick")
    text = format(rounded, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _fmt_sz(value: float) -> str:
    text = f"{float(value):.12f}".rstrip("0").rstrip(".")
    return text or "0"


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ms_iso(ms: Any) -> Optional[str]:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).isoformat(timespec="seconds")
    except Exception:
        return None


def _fill_pct(
    sz: Optional[float],
    fill_sz: Optional[float],
    *,
    ord_type: Optional[str] = None,
    tgt_ccy: Optional[str] = None,
    side: Optional[str] = None,
    avg_px: Optional[float] = None,
) -> Optional[float]:
    if sz is None or sz <= 0:
        return None
    filled = float(fill_sz or 0.0)
    market_quote_buy = (
        str(ord_type or "").lower() == "market"
        and str(tgt_ccy or "").lower() == "quote_ccy"
        and str(side or "").lower() == "buy"
    )
    if market_quote_buy:
        if not avg_px or avg_px <= 0:
            return None
        filled = filled * float(avg_px)
    pct = (filled / float(sz)) * 100.0
    return max(0.0, min(100.0, pct))


def normalize_order(row: dict[str, Any]) -> dict[str, Any]:
    sz = _to_float(row.get("sz"))
    fill_sz = _to_float(row.get("accFillSz") or row.get("fillSz"))
    avg_px = _to_float(row.get("avgPx"))
    ord_type = row.get("ordType")
    tgt_ccy = row.get("tgtCcy") or None
    side = row.get("side")
    remaining = None
    if sz is not None:
        remaining = max(sz - (fill_sz or 0.0), 0.0)
    return {
        "ord_id": str(row.get("ordId") or ""),
        "cl_ord_id": row.get("clOrdId") or None,
        "inst_id": row.get("instId"),
        "side": side,
        "ord_type": ord_type,
        "tgt_ccy": tgt_ccy,
        "sz": sz,
        "px": _to_float(row.get("px")),
        "fill_sz": fill_sz,
        "remaining": remaining,
        "fill_pct": _fill_pct(sz, fill_sz, ord_type=ord_type, tgt_ccy=tgt_ccy, side=side, avg_px=avg_px),
        "avg_px": avg_px,
        "state": row.get("state"),
        "fee": _to_float(row.get("fee")),
        "fee_ccy": row.get("feeCcy") or None,
        "created_at": _ms_iso(row.get("cTime")),
        "updated_at": _ms_iso(row.get("uTime")),
    }


def _fee_num(raw: Any) -> Optional[float]:
    if raw is None or raw == "":
        return None
    try:
        return abs(float(raw))
    except (TypeError, ValueError):
        return None


class OkxClient:
    def __init__(self) -> None:
        self.base = settings.okx_base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=20.0)
        self._spot_cache: dict[str, Any] = {"ts": 0.0, "instruments": None, "tickers": None}
        self._tradable_spot_cache: dict[str, dict[str, Any]] = {}
        self._acct_cache: dict[str, dict[str, Any]] = {}
        self._fund_cache: dict[str, dict[str, Any]] = {}
        self._inst_cache: dict[str, dict[str, Any]] = {}
        self._px_cache: dict[str, dict[str, Any]] = {}
        self._candle_memo: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    def _uid(self) -> str:
        from .context import current_user_id
        return current_user_id.get() or "_"

    def _priv(self, store: dict[str, dict[str, Any]], empty: dict[str, Any]) -> dict[str, Any]:
        uid = self._uid()
        bucket = store.get(uid)
        if bucket is None:
            bucket = dict(empty)
            store[uid] = bucket
        return bucket

    def invalidate_private(self) -> None:
        uid = self._uid()
        self._acct_cache.pop(uid, None)
        self._fund_cache.pop(uid, None)
        self._tradable_spot_cache.pop(uid, None)
        self._px_cache = {}

    def invalidate_tickers(self) -> None:
        self._spot_cache["ts"] = 0.0
        self._spot_cache["tickers"] = None
        self._px_cache = {}

    async def aclose(self) -> None:
        await self._client.aclose()

    def _headers(self, method: str, path_with_query: str, body: str = "") -> dict[str, str]:
        key = credentials.get("okx_api_key")
        secret = credentials.get("okx_secret_key")
        passphrase = credentials.get("okx_passphrase")
        flag = credentials.get("okx_flag") or "0"
        if not key or not secret or not passphrase:
            raise OkxError("Credenciais OKX ausentes. Cadastre em API Keys.")
        timestamp = _ts()
        sign = _sign(timestamp, method, path_with_query, body, secret)
        return {
            "OK-ACCESS-KEY": key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphrase,
            "Content-Type": "application/json",
            "x-simulated-trading": str(flag),
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json_body: Optional[dict[str, Any] | list[Any]] = None,
        auth: bool = True,
    ) -> Any:
        query = ""
        if params:
            query = "?" + "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        full_path = path + query
        body = json.dumps(json_body) if json_body is not None else ""
        headers = self._headers(method, full_path, body) if auth else {}
        url = self.base + full_path
        resp = await self._client.request(
            method,
            url,
            headers=headers,
            content=body if json_body is not None else None,
        )
        try:
            payload = resp.json()
        except Exception as exc:
            raise OkxError(f"resposta inválida OKX HTTP {resp.status_code}") from exc
        code = str(payload.get("code", ""))
        if code != "0":
            raise OkxError(
                payload.get("msg") or f"erro OKX code={code}",
                code=code,
                payload=payload,
            )
        data = payload.get("data") or []
        return data

    async def get_ticker(self, inst_id: str) -> dict[str, Any]:
        inst_id = (inst_id or "").upper()
        now = time.time()
        hit = self._px_cache.get(inst_id)
        if hit and now - float(hit.get("ts") or 0) < 3:
            return hit["row"]
        tickers = self._spot_cache.get("tickers")
        if tickers and now - float(self._spot_cache.get("ts") or 0) < 15:
            for row in tickers:
                if str(row.get("instId") or "").upper() == inst_id and row.get("last"):
                    self._px_cache[inst_id] = {"ts": now, "row": row}
                    return row
        data = await self._request(
            "GET",
            "/api/v5/market/ticker",
            params={"instId": inst_id},
            auth=False,
        )
        if not data:
            raise OkxError(f"ticker vazio para {inst_id}")
        self._px_cache[inst_id] = {"ts": now, "row": data[0]}
        return data[0]

    async def get_last_price(self, inst_id: str) -> float:
        ticker = await self.get_ticker(inst_id)
        return float(ticker["last"])

    async def get_candles(
        self,
        inst_id: str,
        bar: str = "1D",
        limit: int = 300,
        days: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        # Case-sensitive: OKX "1m" = 1 minuto, "1M" = 1 mês
        allowed = {"1m", "5m", "15m", "1H", "4H", "1D", "1W"}
        bar = (bar or "1D").strip()
        if bar == "1M":
            # nunca tratar minuto como mês por acidente de case
            bar = "1D"
        if bar not in allowed:
            bar = "1D"
        max_points = max(20, min(int(limit), 800))
        now_ms = int(time.time() * 1000)
        start_ms = now_ms - int(float(days) * 24 * 60 * 60 * 1000) if days else None
        collected: dict[int, dict[str, Any]] = {}

        def ingest(raw: Any) -> None:
            for item in raw or []:
                ts = int(item[0])
                if start_ms and ts < start_ms:
                    continue
                collected[ts] = {
                    "ts": ts,
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4]),
                    "vol": float(item[5]) if len(item) > 5 and item[5] not in (None, "") else None,
                    "vol_ccy": float(item[6]) if len(item) > 6 and item[6] not in (None, "") else None,
                }

        latest_limit = "300" if days else str(min(max_points, 300))
        ingest(
            await self._request(
                "GET",
                "/api/v5/market/candles",
                params={"instId": inst_id, "bar": bar, "limit": latest_limit},
                auth=False,
            )
        )
        oldest = min(collected) if collected else None
        # 1m/5m precisam de mais páginas para cobrir 24h
        max_pages = 20 if bar in {"1m", "5m", "15m"} else 12
        pages = 0
        while (
            days
            and oldest
            and start_ms
            and oldest > start_ms
            and len(collected) < max_points
            and pages < max_pages
        ):
            hist = await self._request(
                "GET",
                "/api/v5/market/history-candles",
                params={
                    "instId": inst_id,
                    "bar": bar,
                    "limit": "100",
                    "after": str(oldest),
                },
                auth=False,
            )
            pages += 1
            if not hist:
                break
            before = len(collected)
            ingest(hist)
            new_oldest = min(collected) if collected else oldest
            if new_oldest >= oldest or len(collected) == before:
                break
            oldest = new_oldest
        rows = [collected[k] for k in sorted(collected)]
        if len(rows) > max_points:
            rows = rows[-max_points:]
        return rows

    async def price_at(
        self,
        inst_id: str,
        when: datetime,
        *,
        bar: str = "1H",
    ) -> Optional[float]:
        """Preço de fechamento da vela OKX no instante (histórico da exchange)."""
        inst = (inst_id or "").strip().upper()
        if not inst:
            return None
        when_utc = when if when.tzinfo else when.replace(tzinfo=timezone.utc)
        when_utc = when_utc.astimezone(timezone.utc)
        when_ms = int(when_utc.timestamp() * 1000)
        now_ms = int(time.time() * 1000)
        if when_ms > now_ms:
            when_ms = now_ms
        age_h = max(1.0, (now_ms - when_ms) / 3_600_000)
        days = 3.0 if bar == "1H" else max(8.0, age_h / 24.0 + 2.0)
        ttl = 120.0 if bar == "1H" else 600.0
        memo_key = f"{inst}|{bar}|{int(days)}"
        hit = self._candle_memo.get(memo_key)
        now = time.time()
        if hit and now - hit[0] < ttl:
            candles = hit[1]
        else:
            candles = await self.get_candles(inst, bar=bar, days=days, limit=400 if bar == "1H" else 60)
            self._candle_memo[memo_key] = (now, candles)
        chosen: Optional[dict[str, Any]] = None
        for row in candles:
            if int(row.get("ts") or 0) <= when_ms:
                chosen = row
            else:
                break
        if chosen is None:
            return None
        close = chosen.get("close")
        try:
            px = float(close)
        except (TypeError, ValueError):
            return None
        return px if px > 0 else None

    async def get_account_tradable_spot_ids(self, *, force: bool = False) -> Optional[set[str]]:
        """
        Pares Spot que a conta pode negociar (compliance regional).
        None = sem API keys / falha → não filtra.
        """
        if not credentials.configured():
            return None
        now = time.time()
        ttl = 300.0
        cache = self._priv(self._tradable_spot_cache, {"ts": 0.0, "ids": None})
        cached = cache.get("ids")
        if (
            not force
            and cached is not None
            and now - float(cache.get("ts") or 0) < ttl
        ):
            return set(cached)
        try:
            rows = await self._request(
                "GET",
                "/api/v5/account/instruments",
                params={"instType": "SPOT"},
                auth=True,
            )
        except OkxError:
            return None
        ids: set[str] = set()
        for row in rows or []:
            inst = str(row.get("instId") or "").upper()
            if not is_spot_inst_id(inst):
                continue
            state = str(row.get("state") or "live").lower()
            if state and state not in {"live", ""}:
                continue
            ids.add(inst)
        cache["ts"] = now
        cache["ids"] = ids
        return set(ids)

    async def is_spot_tradable_for_account(self, inst_id: str) -> bool:
        """False se a conta/região não pode negociar o par Spot."""
        inst = str(inst_id or "").strip().upper()
        if not is_spot_inst_id(inst):
            return False
        allowed = await self.get_account_tradable_spot_ids()
        if allowed is None:
            return True
        return inst in allowed

    async def list_spot_pairs(self, quote: str = "USDT", query: str = "") -> list[dict[str, Any]]:
        quote = (quote or "USDT").upper()
        all_quotes = quote in {"", "ALL", "*"}
        q = (query or "").strip().upper().replace("/", "-")
        now = time.time()
        if now - float(self._spot_cache["ts"] or 0) > 60 or not self._spot_cache["instruments"]:
            self._spot_cache["instruments"] = await self._request(
                "GET",
                "/api/v5/public/instruments",
                params={"instType": "SPOT"},
                auth=False,
            )
            self._spot_cache["tickers"] = await self._request(
                "GET",
                "/api/v5/market/tickers",
                params={"instType": "SPOT"},
                auth=False,
            )
            self._spot_cache["ts"] = now
        instruments = self._spot_cache["instruments"]
        tickers = self._spot_cache["tickers"]
        last_by_id = {str(t.get("instId")): t for t in tickers or []}
        # Só pares negociáveis na região/conta (evita OKX 51155)
        tradable = await self.get_account_tradable_spot_ids()
        from .hunter import listing_age_days, listing_iso

        out: list[dict[str, Any]] = []
        for row in instruments or []:
            if str(row.get("state")) != "live":
                continue
            if str(row.get("instType") or "SPOT").upper() != "SPOT":
                continue
            qccy = str(row.get("quoteCcy", "")).upper()
            if not all_quotes and qccy != quote:
                continue
            inst_id = str(row.get("instId") or "")
            if not is_spot_inst_id(inst_id):
                continue
            if tradable is not None and inst_id.upper() not in tradable:
                continue
            base = str(row.get("baseCcy") or "")
            if q and q not in inst_id.upper() and q not in base.upper() and q not in qccy:
                continue
            tick = last_by_id.get(inst_id) or {}
            last = float(tick["last"]) if tick.get("last") else None
            open24 = float(tick["open24h"]) if tick.get("open24h") else None
            vol = float(tick["volCcy24h"]) if tick.get("volCcy24h") else 0.0
            bid = float(tick["bidPx"]) if tick.get("bidPx") else None
            ask = float(tick["askPx"]) if tick.get("askPx") else None
            spr = None
            if bid and ask and bid > 0 and ask >= bid:
                mid = (bid + ask) / 2.0
                if mid > 0:
                    spr = ((ask - bid) / mid) * 100.0
            chg = None
            if last is not None and open24:
                chg = ((last - open24) / open24) * 100.0
            primary, fallback = icon_urls(base)
            list_time = row.get("listTime")
            age_days = listing_age_days(list_time)
            listed_at = listing_iso(list_time)
            out.append(
                {
                    "inst_id": inst_id,
                    "base": base,
                    "quote": qccy,
                    "icon": primary,
                    "icon_alt": fallback,
                    "last": last,
                    "bid": bid,
                    "ask": ask,
                    "spread_pct": round(spr, 4) if spr is not None else None,
                    "chg24": chg,
                    "vol": vol,
                    "inst_type": "SPOT",
                    "region_ok": True,
                    "list_time": list_time,
                    "listed_at": listed_at,
                    "age_days": round(age_days, 2) if age_days is not None else None,
                }
            )
        out.sort(key=lambda x: (-float(x.get("vol") or 0), x["inst_id"]))
        return out

    async def get_spot_ccy_sets(self) -> dict[str, set[str]]:
        """Bases e quotes com instrumento Spot live na OKX."""
        now = time.time()
        if now - float(self._spot_cache["ts"] or 0) > 60 or not self._spot_cache["instruments"]:
            await self.list_spot_pairs(quote="ALL")
        bases: set[str] = set()
        quotes: set[str] = set()
        for row in self._spot_cache.get("instruments") or []:
            if str(row.get("state")) != "live":
                continue
            if str(row.get("instType") or "SPOT").upper() != "SPOT":
                continue
            inst = str(row.get("instId") or "")
            if not is_spot_inst_id(inst):
                continue
            b = str(row.get("baseCcy") or "").upper()
            q = str(row.get("quoteCcy") or "").upper()
            if b:
                bases.add(b)
            if q:
                quotes.add(q)
        return {"bases": bases, "quotes": quotes}

    def is_spot_wallet_ccy(self, ccy: str, spot_sets: dict[str, set[str]] | None = None) -> bool:
        """Saldo relevante para Spot: stable/quote conhecida ou base de algum par Spot."""
        c = (ccy or "").upper()
        if not c:
            return False
        if c in SPOT_STABLE_CCYS or c in SPOT_QUOTE_CCYS:
            return True
        if not spot_sets:
            return True  # sem catálogo ainda — não bloqueia
        return c in spot_sets.get("bases", set()) or c in spot_sets.get("quotes", set())

    async def get_order_book_usd(self, inst_id: str, depth: int = 5) -> dict[str, Any]:
        """Soma aproximada do livro (bids+asks top N) em quote USD-ish."""
        inst_id = (inst_id or "").strip().upper()
        data = await self._request(
            "GET",
            "/api/v5/market/books",
            params={"instId": inst_id, "sz": str(max(1, min(int(depth), 25)))},
            auth=False,
        )
        row = (data or [{}])[0] or {}
        bids = row.get("bids") or []
        asks = row.get("asks") or []

        def side_usd(levels: list) -> float:
            total = 0.0
            for lv in levels:
                try:
                    px = float(lv[0])
                    sz = float(lv[1])
                except (TypeError, ValueError, IndexError):
                    continue
                total += px * sz
            return total

        bid_usd = side_usd(bids)
        ask_usd = side_usd(asks)
        return {
            "inst_id": inst_id,
            "bid_usd": bid_usd,
            "ask_usd": ask_usd,
            "book_usd": bid_usd + ask_usd,
        }

    async def ensure_spot_instrument(self, inst_id: str) -> dict[str, Any]:
        """Valida par spot na OKX; mensagem clara se 51001."""
        try:
            parse_inst(inst_id)
        except ValueError as exc:
            raise OkxError(str(exc), code="51001") from exc
        inst_id = (inst_id or "").strip().upper()
        try:
            row = await self.get_instrument(inst_id)
            if str(row.get("instType") or "SPOT").upper() != "SPOT":
                raise OkxError(
                    f"«{inst_id}» não é Spot — este app opera só Spot",
                    code="51001",
                )
            return row
        except OkxError as exc:
            codes = exc._operation_scodes()
            if exc.code == "51001" or "51001" in codes or "não encontrado" in str(exc).lower():
                base = inst_id.split("-")[0] if "-" in inst_id else inst_id
                extra = ""
                if inst_id.endswith("-BRL") and base not in {"BTC", "ETH", "SOL", "USDT", "USDC", "XRP", "DOGE"}:
                    extra = f" Tokens como {base} costumam só ter par em USDT (ex. {base}-USDT), não em BRL."
                raise OkxError(
                    f"O par «{inst_id}» não existe na OKX Spot.{extra} "
                    "Confira demo/live das API Keys e escolha o par na lista de tokens.",
                    code="51001",
                    payload=exc.payload,
                ) from exc
            raise

    async def get_instrument(self, inst_id: str) -> dict[str, Any]:
        inst_id = (inst_id or "").upper()
        now = time.time()
        cached = self._inst_cache.get(inst_id)
        if cached and now - float(cached.get("ts") or 0) < 600:
            return cached["row"]
        for row in self._spot_cache.get("instruments") or []:
            if str(row.get("instId") or "").upper() == inst_id:
                self._inst_cache[inst_id] = {"ts": now, "row": row}
                return row
        data = await self._request(
            "GET",
            "/api/v5/public/instruments",
            params={"instType": "SPOT", "instId": inst_id},
            auth=False,
        )
        if not data:
            raise OkxError(f"instrumento não encontrado: {inst_id}")
        self._inst_cache[inst_id] = {"ts": now, "row": data[0]}
        return data[0]

    def _f(self, value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    async def get_trading_account(self) -> dict[str, Any]:
        now = time.time()
        cache = self._priv(self._acct_cache, {"ts": 0.0, "data": None})
        if cache.get("data") is not None and now - float(cache.get("ts") or 0) < 8:
            return cache["data"]
        data = await self._request("GET", "/api/v5/account/balance")
        row = data[0] if data else {}
        cache["ts"] = now
        cache["data"] = row
        return row

    async def get_funding_balances(self) -> list[dict[str, Any]]:
        now = time.time()
        cache = self._priv(self._fund_cache, {"ts": 0.0, "data": None})
        if cache.get("data") is not None and now - float(cache.get("ts") or 0) < 20:
            return cache["data"]
        try:
            data = await self._request("GET", "/api/v5/asset/balances")
            rows = data or []
        except OkxError:
            rows = []
        cache["ts"] = now
        cache["data"] = rows
        return rows

    async def get_ticker_map(self) -> dict[str, dict[str, Any]]:
        now = time.time()
        if now - float(self._spot_cache["ts"] or 0) > 60 or not self._spot_cache.get("tickers"):
            self._spot_cache["tickers"] = await self._request(
                "GET",
                "/api/v5/market/tickers",
                params={"instType": "SPOT"},
                auth=False,
            )
            self._spot_cache["ts"] = now
        return {str(t.get("instId")): t for t in (self._spot_cache.get("tickers") or [])}

    async def get_balance(self, ccy: str) -> float:
        detail = await self.get_ccy_detail(ccy)
        return float(detail.get("avail") or 0.0)

    async def get_funding_avail(self, ccy: str) -> float:
        try:
            rows = await self.get_funding_balances()
        except OkxError:
            return 0.0
        for item in rows or []:
            if str(item.get("ccy") or "").upper() == str(ccy or "").upper():
                return float(self._f(item.get("availBal") or item.get("bal")) or 0.0)
        return 0.0

    def _balance_short_msg(self, ccy: str, avail: float, need: float, funding: float = 0.0) -> str:
        tip = (
            f" Há ≈ {funding:g} {ccy} no funding — transfira para a conta trading na OKX."
            if funding > 1e-8
            else " Deposite ou transfira para a conta trading (este app não usa margem/empréstimo)."
        )
        if avail <= 1e-12:
            return f"Sem saldo trading de {ccy}.{tip}"
        return (
            f"Saldo trading de {ccy} insuficiente: disponível {avail:g}, "
            f"ordem pede ≈ {need:g}.{tip}"
        )

    async def precheck_spot_buy(
        self,
        inst_id: str,
        quote_amount: float,
        *,
        price: float | None = None,
        fresh_balance: bool = True,
    ) -> float:
        """Valida saldo trading + mínimo OKX antes de comprar. Retorna sz em quote seguro."""
        spend = float(quote_amount or 0)
        if not math.isfinite(spend) or spend <= 0:
            raise OkxError("valor de compra inválido (≤ 0)")
        base, quote = parse_inst(inst_id)
        if fresh_balance:
            self.invalidate_private()
        try:
            avail = float(await self.get_balance(quote))
        except OkxError as exc:
            raise OkxError(f"não foi possível ler saldo trading de {quote}: {exc}") from exc
        funding = await self.get_funding_avail(quote)
        if avail <= 1e-12:
            raise OkxError(self._balance_short_msg(quote, avail, spend, funding), code="51008")
        if spend > avail + 1e-8:
            raise OkxError(self._balance_short_msg(quote, avail, spend, funding), code="51008")
        # Folga mínima de arredondamento — nunca acima do disponível
        safe = min(spend, avail * 0.999999)
        safe = float(Decimal(str(safe)).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN))
        if safe <= 0:
            raise OkxError(self._balance_short_msg(quote, avail, spend, funding), code="51008")

        last = float(price or 0)
        if last <= 0:
            try:
                last = float(await self.get_last_price(inst_id) or 0)
            except Exception:
                last = 0.0
        if last <= 0:
            raise OkxError(f"preço indisponível para {inst_id} — não envia compra")

        inst = await self.get_instrument(inst_id)
        min_sz = float(inst.get("minSz") or 0)
        est_base = safe / last
        # Folga de arredondamento: exigir quote arredondado para cima cobre o minSz
        need_quote = (min_sz * last) if min_sz > 0 else 0.0
        need_quote_ceil = float(Decimal(str(need_quote)).quantize(Decimal("0.01"), rounding=ROUND_UP)) if need_quote else 0.0
        if min_sz > 0 and safe + 1e-12 < need_quote_ceil and est_base + 1e-12 < min_sz:
            raise OkxError(
                f"compra ≈ {est_base:g} {base} abaixo do mínimo OKX {min_sz:g} {base} "
                f"(use pelo menos {need_quote_ceil:.2f} {quote}; saldo {avail:g})",
                code="51020",
            )
        if safe < 1e-8:
            raise OkxError(f"valor de compra demasiado pequeno em {quote}")
        return safe

    async def precheck_spot_sell(
        self,
        inst_id: str,
        base_qty: float,
        *,
        fresh_balance: bool = True,
    ) -> float:
        """Valida saldo trading do token antes de vender. Retorna qty base segura."""
        qty = float(base_qty or 0)
        if not math.isfinite(qty) or qty <= 0:
            raise OkxError("quantidade de venda inválida (≤ 0)")
        base, _quote = parse_inst(inst_id)
        if fresh_balance:
            self.invalidate_private()
        try:
            avail = float(await self.get_balance(base))
        except OkxError as exc:
            raise OkxError(f"não foi possível ler saldo trading de {base}: {exc}") from exc
        funding = await self.get_funding_avail(base)
        if avail <= 1e-12:
            raise OkxError(self._balance_short_msg(base, avail, qty, funding), code="51008")
        if qty > avail + 1e-12:
            raise OkxError(self._balance_short_msg(base, avail, qty, funding), code="51008")
        inst = await self.get_instrument(inst_id)
        try:
            rounded = float(
                round_to_lot(min(qty, avail), inst.get("lotSz") or "0.00000001", inst.get("minSz") or "0")
            )
        except OkxError:
            raise
        if rounded <= 0:
            raise OkxError(f"quantidade de {base} inválida após arredondar o lote")
        return rounded

    def _empty_ccy(self, ccy: str) -> dict[str, Any]:
        return {
            "ccy": ccy,
            "qty": 0.0,
            "avail": 0.0,
            "avg_px": None,
            "upl": None,
            "upl_ratio": None,
            "eq_usd": None,
        }

    def _ccy_from_item(self, ccy: str, item: dict[str, Any]) -> dict[str, Any]:
        qty = self._f(item.get("eq") or item.get("cashBal") or item.get("availBal")) or 0.0
        return {
            "ccy": ccy,
            "qty": qty,
            "avail": self._f(item.get("availBal")) or 0.0,
            "avg_px": self._f(item.get("accAvgPx")),
            "upl": self._f(item.get("spotUpl") or item.get("upl")),
            "upl_ratio": self._f(item.get("spotUplRatio")),
            "eq_usd": self._f(item.get("eqUsd")),
        }

    def avg_cost_in_quote(
        self,
        avg_px: Optional[float],
        quote: str,
        tickers: dict[str, dict[str, Any]] | None = None,
    ) -> Optional[float]:
        """
        OKX accAvgPx do spot costuma vir em USDT/USD.
        Converte para a quote do par (ex. BRL) antes de calcular PnL.
        """
        if avg_px is None or avg_px <= 0:
            return None
        q = (quote or "").upper()
        if q in {"USDT", "USD", "USDC"}:
            return float(avg_px)
        tickers = tickers or {}
        # USDT -> quote (ex. USDT-BRL)
        direct = tickers.get(f"USDT-{q}") or {}
        fx = self._f(direct.get("last"))
        if fx and fx > 0:
            return float(avg_px) * fx
        # quote -> USDT invertido
        inv = tickers.get(f"{q}-USDT") or {}
        fx_inv = self._f(inv.get("last"))
        if fx_inv and fx_inv > 0:
            return float(avg_px) / fx_inv
        return None

    async def get_ccy_detail(self, ccy: str) -> dict[str, Any]:
        ccy = (ccy or "").upper()
        account = await self.get_trading_account()
        for item in account.get("details") or []:
            if str(item.get("ccy") or "").upper() == ccy:
                return self._ccy_from_item(ccy, item)
        return self._empty_ccy(ccy)

    async def get_trade_fee(self, inst_id: str) -> Optional[float]:
        """Retorna taker rate em decimal (ex.: 0.001). None se indisponível."""
        try:
            data = await self._request(
                "GET",
                "/api/v5/account/trade-fee",
                params={"instType": "SPOT", "instId": inst_id},
            )
        except OkxError:
            return None
        if not data:
            return None
        taker = data[0].get("taker")
        rate = _fee_num(taker)
        return rate

    async def place_market_buy(
        self, inst_id: str, quote_amount: float, cl_ord_id: Optional[str] = None
    ) -> dict[str, Any]:
        # Pré-check: sem saldo / abaixo do mínimo → não envia à OKX
        spend = await self.precheck_spot_buy(inst_id, quote_amount, fresh_balance=True)
        sz = _fmt_sz(spend)
        body = {
            "instId": inst_id,
            "tdMode": "cash",
            "side": "buy",
            "ordType": "market",
            "sz": sz,
            "tgtCcy": "quote_ccy",
        }
        if cl_ord_id:
            body["clOrdId"] = cl_ord_id
        data = await self._request("POST", "/api/v5/trade/order", json_body=body)
        if not data:
            raise OkxError("ordem de compra sem retorno")
        order = data[0]
        if order.get("sCode") not in (None, "", "0"):
            raise _order_err(order, "falha ao enviar compra")
        self.invalidate_private()
        return order

    async def place_market_sell(
        self, inst_id: str, base_qty: float, cl_ord_id: Optional[str] = None
    ) -> dict[str, Any]:
        qty = await self.precheck_spot_sell(inst_id, base_qty, fresh_balance=True)
        inst = await self.get_instrument(inst_id)
        sz = round_to_lot(qty, inst.get("lotSz") or "0.00000001", inst.get("minSz") or "0")
        body = {
            "instId": inst_id,
            "tdMode": "cash",
            "side": "sell",
            "ordType": "market",
            "sz": sz,
            "tgtCcy": "base_ccy",
        }
        if cl_ord_id:
            body["clOrdId"] = cl_ord_id
        data = await self._request("POST", "/api/v5/trade/order", json_body=body)
        if not data:
            raise OkxError("ordem de venda sem retorno")
        order = data[0]
        if order.get("sCode") not in (None, "", "0"):
            raise _order_err(order, "falha ao enviar venda")
        self.invalidate_private()
        return order

    async def place_order(
        self,
        inst_id: str,
        side: str,
        ord_type: str,
        sz: float,
        px: Optional[float] = None,
        tgt_ccy: Optional[str] = None,
        cl_ord_id: Optional[str] = None,
    ) -> dict[str, Any]:
        side = (side or "").lower()
        if side not in {"buy", "sell"}:
            raise OkxError("lado inválido: use buy ou sell")
        ord_type = (ord_type or "limit").lower()
        if ord_type not in {"market", "limit", "post_only", "fok", "ioc"}:
            raise OkxError(f"tipo inválido: {ord_type}")
        inst = await self.get_instrument(inst_id)
        body: dict[str, Any] = {
            "instId": inst_id,
            "tdMode": "cash",
            "side": side,
            "ordType": ord_type,
        }
        if cl_ord_id:
            body["clOrdId"] = cl_ord_id
        if ord_type == "market":
            tgt = (tgt_ccy or ("quote_ccy" if side == "buy" else "base_ccy")).lower()
            if tgt not in {"quote_ccy", "base_ccy"}:
                tgt = "base_ccy" if side == "sell" else "quote_ccy"
            body["tgtCcy"] = tgt
            if tgt == "base_ccy":
                if side == "sell":
                    qty = await self.precheck_spot_sell(inst_id, sz, fresh_balance=True)
                    body["sz"] = round_to_lot(
                        qty, inst.get("lotSz") or "0.00000001", inst.get("minSz") or "0"
                    )
                else:
                    # compra em base: precisa ter quote suficiente ≈ sz * preço
                    last = float(px or 0) if px else 0.0
                    if last <= 0:
                        last = float(await self.get_last_price(inst_id) or 0)
                    need_quote = float(sz) * float(last)
                    await self.precheck_spot_buy(inst_id, need_quote, price=last, fresh_balance=True)
                    body["sz"] = round_to_lot(
                        sz, inst.get("lotSz") or "0.00000001", inst.get("minSz") or "0"
                    )
            else:
                # quote_ccy buy — pré-check saldo + mínimo antes do POST
                last = float(px or 0) if px else 0.0
                if last <= 0:
                    try:
                        last = float(await self.get_last_price(inst_id) or 0)
                    except Exception:
                        last = 0.0
                safe = await self.precheck_spot_buy(inst_id, sz, price=last, fresh_balance=True)
                body["sz"] = _fmt_sz(safe)
        else:
            # Limite: OKX exige sz em base. Compra com tgt_ccy=quote_ccy = valor em USDT.
            if px is None or float(px) <= 0:
                raise OkxError("preço obrigatório para ordem limite")
            px_f = float(px)
            tgt = (tgt_ccy or "").lower().strip()
            if side == "buy" and tgt == "quote_ccy":
                quote_spend = float(sz)
                await self.precheck_spot_buy(inst_id, quote_spend, price=px_f, fresh_balance=True)
                base_sz = quote_spend / px_f if px_f > 0 else 0.0
                body["sz"] = round_to_lot(
                    base_sz, inst.get("lotSz") or "0.00000001", inst.get("minSz") or "0"
                )
            elif side == "buy":
                need_quote = float(sz) * px_f
                await self.precheck_spot_buy(inst_id, need_quote, price=px_f, fresh_balance=True)
                body["sz"] = round_to_lot(
                    sz, inst.get("lotSz") or "0.00000001", inst.get("minSz") or "0"
                )
            else:
                await self.precheck_spot_sell(inst_id, sz, fresh_balance=True)
                body["sz"] = round_to_lot(
                    sz, inst.get("lotSz") or "0.00000001", inst.get("minSz") or "0"
                )
            body["px"] = round_to_tick(px_f, inst.get("tickSz") or "0.0001", side)
        data = await self._request("POST", "/api/v5/trade/order", json_body=body)
        if not data:
            raise OkxError("ordem sem retorno")
        order = data[0]
        if order.get("sCode") not in (None, "", "0"):
            raise _order_err(order, "falha ao enviar ordem")
        self.invalidate_private()
        ord_id = str(order.get("ordId") or "")
        if ord_id:
            try:
                return normalize_order(await self.get_order(inst_id, ord_id))
            except OkxError:
                pass
        return normalize_order({**order, "instId": inst_id, "side": side, "ordType": ord_type})

    async def cancel_order(self, inst_id: str, ord_id: str) -> dict[str, Any]:
        try:
            data = await self._request(
                "POST",
                "/api/v5/trade/cancel-order",
                json_body={"instId": inst_id, "ordId": ord_id},
            )
        except OkxError as exc:
            if exc.is_cancel_gone():
                self.invalidate_private()
                return {
                    "ok": True,
                    "already_gone": True,
                    "message": OKX_ERR_PT["51400"],
                    "ord_id": ord_id,
                    "inst_id": inst_id,
                }
            raise
        if not data:
            raise OkxError("cancelamento sem retorno")
        row = data[0]
        scode = str(row.get("sCode") or "").strip()
        if scode in OKX_CANCEL_GONE_SCODES:
            self.invalidate_private()
            return {
                "ok": True,
                "already_gone": True,
                "message": OKX_ERR_PT.get(scode) or OKX_ERR_PT["51400"],
                "ord_id": str(row.get("ordId") or ord_id),
                "inst_id": inst_id,
            }
        if row.get("sCode") not in (None, "", "0"):
            raise _order_err(row, "falha ao cancelar")
        self.invalidate_private()
        return {"ok": True, "ord_id": str(row.get("ordId") or ord_id), "inst_id": inst_id}

    async def enrich_orders(self, orders: list[dict[str, Any]], fee_rate: float = 0.001) -> list[dict[str, Any]]:
        if not orders:
            return []
        tickers = await self.get_ticker_map()
        try:
            account = await self.get_trading_account()
        except OkxError:
            account = {}
        avg_map: dict[str, Optional[float]] = {}
        for item in account.get("details") or []:
            ccy = str(item.get("ccy") or "").upper()
            if ccy:
                avg_map[ccy] = self._f(item.get("accAvgPx"))
        out: list[dict[str, Any]] = []
        for order in orders:
            row = dict(order)
            inst = str(row.get("inst_id") or "")
            try:
                base, quote = parse_inst(inst)
            except ValueError:
                base, quote = "", ""
            last = self._f((tickers.get(inst) or {}).get("last"))
            px = row.get("px") or row.get("avg_px") or last
            sz = float(row.get("sz") or 0)
            remaining = float(row.get("remaining") or sz or 0)
            market_quote_buy = (
                str(row.get("ord_type") or "") == "market"
                and str(row.get("side") or "") == "buy"
                and str(row.get("tgt_ccy") or "") == "quote_ccy"
            )
            if market_quote_buy:
                value = remaining or sz
                qty_base = (value / last) if last else None
            else:
                qty_base = remaining
                value = remaining * float(px) if px else None
            avg_raw = avg_map.get(base) if base else None
            avg = self.avg_cost_in_quote(avg_raw, quote, tickers)
            side = str(row.get("side") or "")
            state = str(row.get("state") or "").lower()
            filled = state in {"filled", "partially_filled"}
            pnl = None
            pnl_pct = None
            if qty_base and px:
                if side == "sell" and not filled and avg and avg > 0:
                    # Venda aberta: estimativa com custo médio atual da conta
                    cost = float(avg) * float(qty_base)
                    pnl = float(px) * float(qty_base) * (1.0 - fee_rate) - cost
                    pnl_pct = (pnl / cost) * 100.0 if cost else None
                elif side == "buy" and last and not filled:
                    cost = float(px) * qty_base
                    pnl = (last - float(px)) * qty_base * (1.0 - fee_rate)
                    pnl_pct = (pnl / cost) * 100.0 if cost else None
                # Venda filled: PnL via FIFO das compras (_apply_fifo_sell_pnl)
            row.update(
                {
                    "base": base,
                    "quote": quote,
                    "last": last,
                    "value": value,
                    "avg_cost": avg,
                    "avg_cost_raw": avg_raw,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "icon": icon_urls(base)[0] if base else None,
                    "icon_alt": icon_urls(base)[1] if base else None,
                }
            )
            out.append(row)
        return _apply_fifo_sell_pnl(out, fee_rate=fee_rate)

    async def list_pending(self, inst_id: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"instType": "SPOT", "limit": str(max(1, min(int(limit), 100)))}
        if inst_id:
            params["instId"] = inst_id
        data = await self._request("GET", "/api/v5/trade/orders-pending", params=params)
        return [normalize_order(r) for r in data or []]

    async def list_history(
        self,
        inst_id: Optional[str] = None,
        limit: int = 1000,
        days: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Ordens finalizadas com filtro de período.

        A API OKX só cobre no máximo ~3 meses (archive). Pedidos maiores
        retornam o máximo disponível e devem ser sinalizados pelo caller.
        """
        import asyncio

        max_total = max(1, min(int(limit), 3000))
        want_days = float(days if days is not None else 90)
        want_days = max(1 / 24, min(want_days, 365.0))
        # OKX: orders-history = 7d · orders-history-archive = 3m
        fetch_days = min(want_days, 90.0)
        now_ms = int(time.time() * 1000)
        begin_ms = now_ms - int(fetch_days * 24 * 60 * 60 * 1000)
        by_id: dict[str, dict[str, Any]] = {}

        async def pull(path: str, pages_cap: int, *, with_begin: bool = True) -> None:
            after: Optional[str] = None
            pages = 0
            while len(by_id) < max_total and pages < pages_cap:
                batch = min(100, max_total - len(by_id))
                if batch <= 0:
                    break
                params: dict[str, Any] = {"instType": "SPOT", "limit": str(batch)}
                if inst_id:
                    params["instId"] = inst_id
                if with_begin:
                    params["begin"] = str(begin_ms)
                    params["end"] = str(now_ms)
                if after:
                    params["after"] = after
                data = await self._request("GET", path, params=params)
                pages += 1
                rows = data or []
                if not rows:
                    break
                for raw in rows:
                    # filtro local por uTime/cTime (ms)
                    ts_raw = raw.get("uTime") or raw.get("cTime")
                    try:
                        ts_ms = int(ts_raw) if ts_raw is not None else None
                    except (TypeError, ValueError):
                        ts_ms = None
                    if ts_ms is not None and ts_ms < begin_ms:
                        continue
                    norm = normalize_order(raw)
                    key = str(norm.get("ord_id") or raw.get("ordId") or "")
                    if not key:
                        key = f"{norm.get('cl_ord_id')}|{norm.get('created_at')}|{norm.get('inst_id')}"
                    by_id[key] = norm
                next_after = str(rows[-1].get("ordId") or "")
                # se o lote mais antigo já passou do begin, para
                oldest_ts = None
                try:
                    oldest_ts = int(rows[-1].get("uTime") or rows[-1].get("cTime") or 0)
                except (TypeError, ValueError):
                    oldest_ts = 0
                if not next_after or next_after == after or len(rows) < batch:
                    break
                if oldest_ts and oldest_ts < begin_ms:
                    break
                after = next_after
                if pages % 4 == 0:
                    await asyncio.sleep(0.05)

        if fetch_days <= 7:
            await pull("/api/v5/trade/orders-history", pages_cap=10)
        else:
            await pull("/api/v5/trade/orders-history-archive", pages_cap=40)
            await pull("/api/v5/trade/orders-history", pages_cap=5)

        def sort_key(row: dict[str, Any]) -> str:
            return str(row.get("updated_at") or row.get("created_at") or "")

        ordered = sorted(by_id.values(), key=sort_key, reverse=True)
        return ordered[:max_total]

    async def cancel_all_pending(self, inst_id: Optional[str] = None) -> dict[str, Any]:
        pending = await self.list_pending(inst_id)
        if not pending:
            return {"canceled": 0, "failed": 0, "already_gone": 0, "orders": []}
        results: list[dict[str, Any]] = []
        canceled = 0
        failed = 0
        already_gone = 0
        for i in range(0, len(pending), 20):
            chunk = pending[i : i + 20]
            body = [{"instId": o["inst_id"], "ordId": o["ord_id"]} for o in chunk if o.get("ord_id")]
            if not body:
                continue
            try:
                data = await self._request("POST", "/api/v5/trade/cancel-batch-orders", json_body=body)
            except OkxError as exc:
                # OKX code 1 (todas falharam) / 2 (parcial): ainda há linhas em data
                payload = exc.payload if isinstance(exc.payload, dict) else {}
                data = payload.get("data") if isinstance(payload.get("data"), list) else None
                if not data:
                    raise
            for row in data or []:
                scode = str(row.get("sCode") or "0").strip()
                if scode in {"0", ""}:
                    canceled += 1
                elif scode in OKX_CANCEL_GONE_SCODES:
                    already_gone += 1
                else:
                    failed += 1
                results.append(row)
        self.invalidate_private()
        return {
            "canceled": canceled,
            "failed": failed,
            "already_gone": already_gone,
            "orders": results,
        }

    async def get_order(self, inst_id: str, ord_id: str) -> dict[str, Any]:
        data = await self._request(
            "GET",
            "/api/v5/trade/order",
            params={"instId": inst_id, "ordId": ord_id},
        )
        if not data:
            raise OkxError(f"ordem {ord_id} não encontrada")
        return data[0]

    async def wait_fill(
        self, inst_id: str, ord_id: str, timeout_s: float = 20.0, interval_s: float = 0.6
    ) -> dict[str, Any]:
        import asyncio

        deadline = asyncio.get_event_loop().time() + timeout_s
        last: dict[str, Any] = {}
        while asyncio.get_event_loop().time() < deadline:
            last = await self.get_order(inst_id, ord_id)
            state = str(last.get("state", ""))
            if state in {"filled", "canceled"}:
                return last
            await asyncio.sleep(interval_s)
        return last

    async def health(self) -> dict[str, Any]:
        usdt = await self.get_balance("USDT")
        return {"ok": True, "usdt": usdt, "flag": credentials.get("okx_flag") or "0"}


def _order_ts_key(order: dict[str, Any]) -> str:
    return str(
        order.get("created_at")
        or order.get("updated_at")
        or order.get("ts")
        or order.get("c_time")
        or ""
    )


def _apply_fifo_sell_pnl(orders: list[dict[str, Any]], fee_rate: float = 0.001) -> list[dict[str, Any]]:
    """Para vendas filled sem PnL, estima realizado via FIFO das compras do mesmo par."""
    if not orders:
        return orders
    indexed = list(enumerate(orders))
    indexed.sort(key=lambda it: _order_ts_key(it[1]))
    inventory: dict[str, list[dict[str, float]]] = {}

    for idx, row in indexed:
        inst = str(row.get("inst_id") or "").upper()
        if not inst:
            continue
        side = str(row.get("side") or "").lower()
        state = str(row.get("state") or "").lower()
        if state not in {"filled", "partially_filled"}:
            continue
        try:
            base, quote = parse_inst(inst)
        except ValueError:
            continue
        qty = float(row.get("fill_sz") or row.get("sz") or 0)
        px = float(row.get("avg_px") or row.get("px") or 0)
        if qty <= 0 or px <= 0:
            continue
        fee_abs = abs(float(row.get("fee") or 0))
        fee_ccy = str(row.get("fee_ccy") or "").upper()

        if side == "buy":
            net_qty = qty
            cost = qty * px
            if fee_ccy == base.upper() and fee_abs > 0:
                net_qty = max(0.0, qty - fee_abs)
            elif fee_ccy == quote.upper() and fee_abs > 0:
                cost += fee_abs
            if net_qty > 0:
                inventory.setdefault(inst, []).append({"qty": net_qty, "cost": cost})
            continue

        if side != "sell":
            continue

        lots = inventory.setdefault(inst, [])
        need = qty
        cost_share = 0.0
        while need > 1e-12 and lots:
            lot = lots[0]
            lot_qty = float(lot["qty"])
            if lot_qty <= 1e-12:
                lots.pop(0)
                continue
            take = min(need, lot_qty)
            cost_share += float(lot["cost"]) * (take / lot_qty)
            remain = lot_qty - take
            if remain <= 1e-12:
                lots.pop(0)
            else:
                lot["cost"] = float(lot["cost"]) * (remain / lot_qty)
                lot["qty"] = remain
            need -= take

        if row.get("pnl") is not None:
            continue
        if cost_share <= 0:
            continue
        if fee_ccy == quote.upper() and fee_abs > 0:
            proceeds = px * qty - fee_abs
        else:
            proceeds = px * qty * (1.0 - fee_rate)
        pnl = proceeds - cost_share
        orders[idx]["pnl"] = pnl
        orders[idx]["pnl_pct"] = (pnl / cost_share) * 100.0
        orders[idx]["pnl_source"] = "fifo_buys"
        if orders[idx].get("pnl_realized") is None:
            orders[idx]["pnl_realized"] = pnl
    return orders
