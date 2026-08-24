from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from . import credentials, db
from .okx_client import OkxClient, OkxError, icon_urls


class PortfolioWatcher:
    def __init__(self, okx: OkxClient) -> None:
        self.okx = okx
        self._tasks: dict[str, asyncio.Task] = {}
        self._stops: dict[str, asyncio.Event] = {}
        self._last: dict[str, dict[str, Any]] = {}
        self._errors: dict[str, Optional[str]] = {}

    def _key(self) -> str:
        from .context import current_user_id
        return current_user_id.get() or "_"

    @property
    def running(self) -> bool:
        task = self._tasks.get(self._key())
        return task is not None and not task.done()

    async def start(self) -> None:
        await self.ensure_started()

    async def ensure_started(self) -> None:
        if not credentials.configured():
            return
        key = self._key()
        if key == "_":
            from . import auth as authmod
            if authmod.enabled():
                return
        task = self._tasks.get(key)
        if task and not task.done():
            return
        stop = asyncio.Event()
        self._stops[key] = stop
        self._tasks[key] = asyncio.create_task(self._loop_for(key), name=f"okx-portfolio-{key[:12]}")

    async def stop(self) -> None:
        for ev in self._stops.values():
            ev.set()
        tasks = [t for t in self._tasks.values() if t and not t.done()]
        for task in tasks:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=6)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                task.cancel()
        self._tasks.clear()
        self._stops.clear()

    def snapshot(self) -> dict[str, Any]:
        key = self._key()
        data = dict(self._last.get(key) or {})
        data.setdefault("assets", [])
        data.setdefault("total_eq", None)
        if data.get("total_eq") is not None:
            data.setdefault("spot_upl", 0.0)
            data.setdefault("pnl_today", 0.0)
            data.setdefault("pnl_24h", 0.0)
            data.setdefault("pnl_week", 0.0)
            data.setdefault("pnl_month", 0.0)
        else:
            data.setdefault("spot_upl", None)
            data.setdefault("pnl_today", None)
            data.setdefault("pnl_24h", None)
            data.setdefault("pnl_week", None)
            data.setdefault("pnl_month", None)
        data["interval_min"] = db.portfolio_interval_min()
        data["watching"] = self.running
        data["last_error"] = self._errors.get(key)
        data["keys_configured"] = credentials.configured()
        data.setdefault("usdt_brl", None)
        return data

    @staticmethod
    def _usdt_brl_rate(tickers: dict[str, dict[str, Any]]) -> float | None:
        def _num(value: Any) -> float | None:
            if value is None or value == "":
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        direct = tickers.get("USDT-BRL") or {}
        rate = _num(direct.get("last"))
        if rate and rate > 0:
            return float(rate)
        inv = tickers.get("BRL-USDT") or {}
        inv_last = _num(inv.get("last"))
        if inv_last and inv_last > 0:
            return 1.0 / float(inv_last)
        return None

    async def _okx_period_pnl(
        self,
        assets: list[dict[str, Any]],
        when: datetime,
        usdt_brl: float | None,
    ) -> Optional[float]:
        """PnL do patrimônio vs preço OKX no início do período (candles), não snapshot local."""
        age_h = (datetime.now(timezone.utc) - when.astimezone(timezone.utc)).total_seconds() / 3600.0
        bar = "1H" if age_h <= 48 else "1D"

        async def one(row: dict[str, Any]) -> Optional[float]:
            ccy = str(row.get("ccy") or "").upper()
            if row.get("is_stable") and ccy in {"USDT", "USDC", "USD"}:
                return 0.0
            inst = str(row.get("spot_inst") or "")
            qty = float(row.get("total_bal") or 0)
            last = row.get("last")
            if not inst or qty <= 0 or last is None:
                return None
            try:
                last_f = float(last)
            except (TypeError, ValueError):
                return None
            if last_f <= 0:
                return None
            try:
                px_then = await self.okx.price_at(inst, when, bar=bar)
            except OkxError:
                return None
            if px_then is None or px_then <= 0:
                return None
            raw = (last_f - float(px_then)) * qty
            if inst.endswith("-BRL"):
                if not usdt_brl or usdt_brl <= 0:
                    return None
                raw = raw / usdt_brl
            return raw

        parts = await asyncio.gather(*[one(row) for row in assets])
        usable = [p for p in parts if p is not None]
        if not usable:
            return None
        return float(sum(usable))

    async def refresh_now(self) -> dict[str, Any]:
        from .context import current_user_id
        uid = current_user_id.get()
        if uid:
            credentials.hydrate_user(uid)
        if not credentials.configured():
            raise OkxError("Credenciais OKX ausentes")
        self.okx.invalidate_private()
        self.okx.invalidate_tickers()
        account = await self.okx.get_trading_account()
        funding = await self.okx.get_funding_balances()
        tickers = await self.okx.get_ticker_map()
        spot_sets = await self.okx.get_spot_ccy_sets()

        total_eq_acct = self.okx._f(account.get("totalEq")) or 0.0
        merged: dict[str, dict[str, Any]] = {}

        for item in account.get("details") or []:
            ccy = str(item.get("ccy") or "").upper()
            if not ccy or not self.okx.is_spot_wallet_ccy(ccy, spot_sets):
                continue
            bal = self.okx._f(item.get("eq") or item.get("cashBal") or item.get("availBal")) or 0.0
            eq_usd = self.okx._f(item.get("eqUsd")) or 0.0
            if bal <= 0 and eq_usd < 0.05:
                continue
            icon, icon_alt = icon_urls(ccy)
            merged[ccy] = {
                "ccy": ccy,
                "trading_bal": bal,
                "funding_bal": 0.0,
                "total_bal": bal,
                "avail": self.okx._f(item.get("availBal")) or 0.0,
                "eq_usd": eq_usd,
                "avg_px": self.okx._f(item.get("accAvgPx")),
                "spot_upl": self.okx._f(item.get("spotUpl") or item.get("upl")),
                "spot_upl_ratio": self.okx._f(item.get("spotUplRatio")),
                "icon": icon,
                "icon_alt": icon_alt,
                "spot": True,
            }

        for item in funding:
            ccy = str(item.get("ccy") or "").upper()
            if not ccy or not self.okx.is_spot_wallet_ccy(ccy, spot_sets):
                continue
            bal = self.okx._f(item.get("bal") or item.get("availBal")) or 0.0
            if bal <= 0:
                continue
            row = merged.setdefault(
                ccy,
                {
                    "ccy": ccy,
                    "trading_bal": 0.0,
                    "funding_bal": 0.0,
                    "total_bal": 0.0,
                    "avail": 0.0,
                    "eq_usd": 0.0,
                    "avg_px": None,
                    "spot_upl": None,
                    "spot_upl_ratio": None,
                    "icon": icon_urls(ccy)[0],
                    "icon_alt": icon_urls(ccy)[1],
                    "spot": True,
                },
            )
            row["funding_bal"] = bal
            row["total_bal"] = float(row.get("trading_bal") or 0) + bal
            row["spot"] = True
            if ccy in {"USDT", "USDC", "USD"} and not row.get("eq_usd"):
                row["eq_usd"] = row["total_bal"]

        assets = []
        spot_upl_sum = 0.0
        est_24h = 0.0
        for ccy, row in merged.items():
            # Prefere ticker Spot USDT; fallback USDC/BRL
            tick = (
                tickers.get(f"{ccy}-USDT")
                or tickers.get(f"{ccy}-USDC")
                or tickers.get(f"{ccy}-BRL")
                or {}
            )
            last = self.okx._f(tick.get("last"))
            open24 = self.okx._f(tick.get("open24h"))
            chg24 = None
            if last is not None and open24:
                chg24 = ((last - open24) / open24) * 100.0
            if (not row.get("eq_usd")) and last is not None:
                row["eq_usd"] = float(row["total_bal"]) * last
            row["last"] = last
            row["chg24"] = chg24
            # Par Spot de referência para gráfico/ordem
            # Stables NÃO apontam para BTC — usam par FX (ex. USDT-BRL) ou null
            if ccy in {"USDT", "USDC", "USD"}:
                if tickers.get(f"{ccy}-BRL"):
                    row["spot_inst"] = f"{ccy}-BRL"
                elif tickers.get("USDT-BRL") and ccy == "USDT":
                    row["spot_inst"] = "USDT-BRL"
                elif tickers.get(f"{ccy}-EUR"):
                    row["spot_inst"] = f"{ccy}-EUR"
                else:
                    row["spot_inst"] = None
                row["is_stable"] = True
            elif ccy == "BRL":
                row["spot_inst"] = "USDT-BRL" if tickers.get("USDT-BRL") else None
                row["is_stable"] = True
            elif tickers.get(f"{ccy}-USDT"):
                row["spot_inst"] = f"{ccy}-USDT"
                row["is_stable"] = False
            elif tickers.get(f"{ccy}-USDC"):
                row["spot_inst"] = f"{ccy}-USDC"
                row["is_stable"] = False
            elif tickers.get(f"{ccy}-BRL"):
                row["spot_inst"] = f"{ccy}-BRL"
                row["is_stable"] = False
            else:
                row["spot_inst"] = None
                row["is_stable"] = False
            upl = row.get("spot_upl")
            if upl is None and row.get("avg_px") and last is not None:
                upl = (last - float(row["avg_px"])) * float(row.get("total_bal") or 0)
            if upl is None and chg24 is not None and row.get("eq_usd"):
                upl = float(row["eq_usd"]) * chg24 / 100.0
            row["spot_upl"] = upl
            if upl is not None:
                spot_upl_sum += float(upl)
            if chg24 is not None and row.get("eq_usd"):
                est_24h += float(row["eq_usd"]) * chg24 / 100.0
            if float(row.get("total_bal") or 0) <= 0 and float(row.get("eq_usd") or 0) < 0.05:
                continue
            assets.append(row)

        assets.sort(key=lambda a: -float(a.get("eq_usd") or 0))
        total_eq = sum(float(a.get("eq_usd") or 0) for a in assets)
        if not total_eq and total_eq_acct:
            # fallback se conversões falharam
            total_eq = total_eq_acct

        usdt_brl = self._usdt_brl_rate(tickers)
        db.save_portfolio_snapshot(total_eq, assets, usdt_brl=usdt_brl)
        starts = db.period_starts()
        pnl_today, pnl_week, pnl_month = await asyncio.gather(
            self._okx_period_pnl(assets, starts["today"], usdt_brl),
            self._okx_period_pnl(assets, starts["week"], usdt_brl),
            self._okx_period_pnl(assets, starts["month"], usdt_brl),
        )
        # 24h: open24h dos tickers OKX (já é histórico da exchange)
        pnl_24h = est_24h

        key = self._key()
        self._last[key] = {
            "total_eq": total_eq,
            "spot_upl": spot_upl_sum,
            "pnl_today": pnl_today,
            "pnl_24h": pnl_24h,
            "pnl_week": pnl_week,
            "pnl_month": pnl_month,
            "usdt_brl": usdt_brl,
            "assets": assets,
            "market": "spot",
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self._errors[key] = None
        return self.snapshot()

    async def _loop_for(self, key: str) -> None:
        from .context import current_user_id
        token = current_user_id.set(key) if key != "_" else None
        stop = self._stops.get(key) or asyncio.Event()
        try:
            if key != "_":
                credentials.hydrate_user(key)
            try:
                await self.refresh_now()
            except Exception as exc:
                self._errors[key] = str(exc)

            while not stop.is_set():
                try:
                    await asyncio.wait_for(
                        stop.wait(),
                        timeout=max(60.0, float(db.portfolio_interval_min()) * 60.0),
                    )
                except asyncio.TimeoutError:
                    pass
                if stop.is_set():
                    break
                try:
                    await self.refresh_now()
                except OkxError as exc:
                    self._errors[key] = str(exc)
                except Exception as exc:
                    self._errors[key] = str(exc)
        finally:
            if token is not None:
                current_user_id.reset(token)
