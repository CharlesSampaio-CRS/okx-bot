from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from . import db
from .cascade import (
    buy_drop_trigger_pct,
    buy_pcts,
    buy_tranche_quote,
    cascade_enabled,
    cascade_steps,
    sell_pcts,
    sell_pnl_trigger_pct,
    sell_tranche_qty,
)
from .models import Position
from .okx_client import OkxClient, OkxError, parse_inst
from .order_limits import clamp_spend_quote, quote_to_usd, validate_order_usd
from .pnl import (
    DEFAULT_SELL_SLIPPAGE_PCT,
    estimate_net_pnl,
    fee_to_quote,
    min_net_sell_pnl_pct,
    net_base_qty,
    net_sell_proceeds,
    position_cost_basis,
    quote_cost,
)


class TradingEngine:
    def __init__(self, bot_id: str = "default", okx: Optional[OkxClient] = None) -> None:
        self.bot_id = bot_id
        self.okx = okx or OkxClient()
        self._own_okx = okx is None
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()
        self.last_price: Optional[float] = None
        self.last_error: Optional[str] = None
        self.okx_fee_rate: Optional[float] = None
        self._busy = asyncio.Lock()
        self._min_sz: Optional[float] = None
        self._min_sz_inst: Optional[str] = None
        self._token_detail: dict[str, Any] = {}
        self._token_view_ts: float = 0.0
        self._last_log_key: Optional[str] = None
        self._tick_trigger: str = "auto"

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def _log(self, message: str, level: str = "info", *, force: bool = False) -> None:
        key = f"{level}:{message}"
        if not force and key == self._last_log_key and level == "info":
            return
        self._last_log_key = key
        db.add_event(message, level, bot_id=self.bot_id)

    async def start(self) -> None:
        async with self._busy:
            if self.running:
                return
            if self._task and self._task.done():
                self._task = None
            self._stop.clear()
            self.last_error = None
            self._last_log_key = None
            cfg = db.get_config(self.bot_id)
            started = datetime.now(timezone.utc)
            if float(cfg.run_days or 0) > 0:
                until = started + timedelta(days=float(cfg.run_days))
                until_s = until.isoformat(timespec="seconds")
            else:
                until_s = None
            db.set_run_window(self.bot_id, started.isoformat(timespec="seconds"), until_s)
            self._task = asyncio.create_task(self._loop(), name=f"okx-engine-{self.bot_id}")
            dur = f"{cfg.run_days:g} dia(s)" if cfg.run_days else "sem limite"
            self._log(
                f"engine iniciado · a cada {cfg.interval_min:g} min · duração {dur}",
                force=True,
            )

    async def stop(self) -> None:
        self._stop.set()
        task = self._task
        if task:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=8)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                task.cancel()
            self._task = None
        db.clear_run_window(self.bot_id)
        self._log("engine parado", force=True)

    def _bind_bot_user(self):
        from .context import current_user_id
        from . import credentials as creds
        uid = ""
        try:
            uid = str((db.get_bot_doc(self.bot_id) or {}).get("user_id") or "")
        except KeyError:
            uid = ""
        token = current_user_id.set(uid) if uid else None
        if uid:
            creds.hydrate_user(uid)
        return token

    @staticmethod
    def _unbind_bot_user(token) -> None:
        from .context import current_user_id
        if token is not None:
            current_user_id.reset(token)

    async def tick_once(self, *, manual: bool = True) -> dict[str, Any]:
        """Roda um ciclo imediato (compra/venda se as regras fecharem). Não inicia o loop."""
        token = self._bind_bot_user()
        try:
            async with self._busy:
                cfg = db.get_config(self.bot_id)
                self._tick_trigger = "manual" if manual else "auto"
                try:
                    await self._tick(cfg)
                    self.last_error = None
                    self._log(
                        "ciclo manual executado"
                        if manual
                        else "ciclo sob demanda executado",
                        force=True,
                    )
                except Exception:
                    raise
                finally:
                    self._tick_trigger = "auto"
            return self.snapshot()
        finally:
            self._unbind_bot_user(token)

    def snapshot(self) -> dict[str, Any]:
        cfg = db.get_config(self.bot_id)
        pos = db.get_position(self.bot_id)
        price = self.last_price or 0.0
        detail = self._token_detail or {}
        qty = float(detail.get("qty") or pos.qty or 0) or pos.qty
        avg = detail.get("avg_px") or pos.entry_price
        cost = None
        if avg and qty:
            fee_rate = self.okx_fee_rate if self.okx_fee_rate is not None else cfg.fee_rate
            cost = position_cost_basis(
                okx_avg=float(avg),
                okx_qty=float(qty),
                local_cost=pos.cost_total if pos.state == "long" else None,
                local_qty=pos.qty if pos.state == "long" else None,
                fee_rate=fee_rate,
            )
        elif pos.cost_total:
            cost = pos.cost_total
        state = pos.state
        if qty and float(qty) > 0 and (avg or pos.cost_total):
            state = "long"
        drop_pct = None
        pnl_snap = None
        if state != "long" and pos.ref_price and price:
            drop_pct = ((pos.ref_price - price) / pos.ref_price) * 100.0
        if state == "long" and qty and cost and price:
            fr = self.okx_fee_rate if self.okx_fee_rate is not None else cfg.fee_rate
            pnl_snap = estimate_net_pnl(
                price, float(qty), float(cost), fr, cfg.profit_target_pct
            )
        buy_trigger = None
        if state != "long" and pos.ref_price:
            buy_trigger = float(pos.ref_price) * (1.0 - float(cfg.buy_pct) / 100.0)
        token_upl = detail.get("upl")
        token_upl_pct = None
        if detail.get("upl_ratio") is not None:
            token_upl_pct = float(detail["upl_ratio"]) * 100.0
        elif token_upl is not None and cost:
            token_upl_pct = float(token_upl) / float(cost) * 100.0
        return {
            "bot_id": self.bot_id,
            "name": cfg.name,
            "running": self.running,
            "inst_id": cfg.inst_id,
            "price": price or None,
            "state": state,
            "ref_price": pos.ref_price,
            "entry_price": float(avg) if avg else pos.entry_price,
            "qty": float(qty) if qty else pos.qty,
            "cost_total": float(cost) if cost else pos.cost_total,
            "buy_fee_usdt": pos.buy_fee_usdt,
            "buy_fee_ccy": pos.buy_fee_ccy,
            "opened_at": pos.opened_at,
            "buy_pct": cfg.buy_pct,
            "profit_target_pct": cfg.profit_target_pct,
            "fee_rate_pct": cfg.fee_rate_pct,
            "okx_fee_rate_pct": (self.okx_fee_rate * 100.0) if self.okx_fee_rate else None,
            "quote_amount": cfg.quote_amount,
            "entry_mode": getattr(cfg, "entry_mode", "quote"),
            "strategy_id": getattr(cfg, "strategy_id", None),
            "cascade_enabled": cascade_enabled(cfg),
            "cascade_buy_pct": getattr(cfg, "cascade_buy_pct", None),
            "cascade_sell_pct": getattr(cfg, "cascade_sell_pct", None),
            "cascade_buy_pcts": getattr(cfg, "cascade_buy_pcts", None),
            "cascade_sell_pcts": getattr(cfg, "cascade_sell_pcts", None),
            "cascade_buy_step": pos.cascade_buy_step,
            "cascade_sell_step": pos.cascade_sell_step,
            "interval_min": cfg.interval_min,
            "run_days": cfg.run_days,
            "poll_interval": cfg.poll_interval,
            "portfolio_interval_min": getattr(cfg, "portfolio_interval_min", None),
            **db.get_run_window(self.bot_id),
            "drop_pct": drop_pct,
            "buy_trigger_price": buy_trigger,
            "break_even": pnl_snap.break_even if pnl_snap else None,
            "target_price": pnl_snap.target_price if pnl_snap else None,
            "pnl": pnl_snap.pnl if pnl_snap else None,
            "pnl_pct": pnl_snap.pnl_pct if pnl_snap else None,
            "token_upl": token_upl,
            "token_upl_pct": token_upl_pct,
            "sell_fee_est": pnl_snap.sell_fee_est if pnl_snap else None,
            "realized_pnl": db.realized_pnl_sum(self.bot_id),
            "last_error": self.last_error,
            "events": [e.model_dump() for e in db.list_events(20, self.bot_id)],
            "executions": db.list_executions(40, self.bot_id),
        }

    def _save_execution(
        self,
        cfg,
        decision: dict[str, Any],
        *,
        mode: str,
        executed: bool = False,
        price: float | None = None,
        state: str | None = None,
        force: bool = False,
    ) -> dict[str, Any] | None:
        action = str(decision.get("action") or "unknown")
        would_trade = bool(decision.get("would_trade"))
        checks = decision.get("checks") or []
        failed_gate = any(not c.get("ok") for c in checks if isinstance(c, dict))
        # Falha de regra “de verdade” grava sempre; wait_buy/wait_sell só a cada ~intervalo
        # (senão cada tick enche Mongo com “ainda não caiu o suficiente”).
        # Tick manual: sempre grava (e marca trigger=manual).
        is_manual = str(getattr(self, "_tick_trigger", "") or "") == "manual"
        if is_manual:
            force = True
        routine_wait = action in {"wait_buy", "wait_sell"} and not executed and not would_trade
        if failed_gate and not routine_wait:
            force = True
        if mode == "live" and not force and not executed and not would_trade:
            last = getattr(self, "_last_exec_key", None)
            last_ts = getattr(self, "_last_exec_ts", 0.0)
            key = f"{action}|{state}|{would_trade}|{decision.get('failed_step')}"
            # Throttle ≈ intervalo do bot (mín. 5 min) — evita flood de “ainda espera queda”
            throttle_s = max(300.0, float(cfg.poll_interval) * 0.9)
            if key == last and (time.time() - last_ts) < throttle_s:
                return None
        doc = db.add_execution(
            bot_id=self.bot_id,
            bot_name=cfg.name,
            mode=mode,
            action=action,
            reason=str(decision.get("reason") or ""),
            would_trade=would_trade,
            executed=executed,
            inst_id=cfg.inst_id,
            price=price if price is not None else self.last_price,
            state=state,
            drop_pct=decision.get("drop_pct"),
            pnl_pct=decision.get("pnl_pct"),
            pnl=decision.get("pnl"),
            target_price=decision.get("target_price"),
            poll_interval=cfg.poll_interval,
            checks=decision.get("checks") or [],
            trigger=str(getattr(self, "_tick_trigger", None) or "auto"),
        )
        self._last_exec_key = f"{action}|{state}|{would_trade}"
        self._last_exec_ts = time.time()
        return doc

    async def refresh_token_view(self, force: bool = False) -> None:
        if not force and time.time() - self._token_view_ts < 15:
            return
        cfg = db.get_config(self.bot_id)
        try:
            self.last_price = await self.okx.get_last_price(cfg.inst_id)
            base, _quote = parse_inst(cfg.inst_id)
            self._token_detail = await self.okx.get_ccy_detail(base)
            self._token_view_ts = time.time()
        except (OkxError, ValueError):
            pass

    async def _loop(self) -> None:
        token = self._bind_bot_user()
        expired = False
        try:
            try:
                await self._hydrate()
            except Exception as exc:
                self.last_error = str(exc)
                self._log(f"falha ao iniciar: {exc}", "error", force=True)

            while not self._stop.is_set():
                if db.run_window_expired(self.bot_id):
                    expired = True
                    self._log("duração esgotada — pausando automaticamente", force=True)
                    break
                cfg = db.get_config(self.bot_id)
                try:
                    async with self._busy:
                        self._tick_trigger = "auto"
                        await self._tick(cfg)
                    self.last_error = None
                except OkxError as exc:
                    self.last_error = str(exc)
                    self._log(f"OKX: {exc}", "error", force=True)
                except Exception as exc:
                    self.last_error = str(exc)
                    self._log(f"erro: {exc}", "error", force=True)
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=cfg.poll_interval)
                except asyncio.TimeoutError:
                    pass

            if expired:
                db.clear_run_window(self.bot_id)
                self._log("engine parado (fim da duração)", force=True)
        finally:
            self._unbind_bot_user(token)

    async def _min_size(self, inst_id: str) -> float:
        if self._min_sz is None or self._min_sz_inst != inst_id:
            inst = await self.okx.get_instrument(inst_id)
            self._min_sz = float(inst.get("minSz") or 0)
            self._min_sz_inst = inst_id
        return float(self._min_sz or 0)

    async def _sync_from_okx(self, cfg, price: float) -> Position:
        base, _quote = parse_inst(cfg.inst_id)
        detail = await self.okx.get_ccy_detail(base)
        self._token_detail = detail
        self._token_view_ts = time.time()
        dust = max(await self._min_size(cfg.inst_id), 0.0)
        qty = float(detail.get("qty") or 0)
        pos = db.get_position(self.bot_id)
        if qty <= dust:
            if pos.state == "long":
                db.save_position(self._flat_position(price), self.bot_id)
                self._log(f"saldo {base} zerado na OKX → flat", force=True)
            elif not pos.ref_price:
                db.save_position(self._flat_position(price), self.bot_id)
            return db.get_position(self.bot_id)

        avg = detail.get("avg_px")
        if not avg or avg <= 0:
            avg = pos.entry_price or price
        avg = float(avg)
        fee_rate = self.okx_fee_rate if self.okx_fee_rate is not None else cfg.fee_rate
        cost = position_cost_basis(
            okx_avg=avg,
            okx_qty=qty,
            local_cost=pos.cost_total if pos.state == "long" else None,
            local_qty=pos.qty if pos.state == "long" else None,
            fee_rate=fee_rate,
        )
        opened = pos.opened_at if pos.state == "long" else datetime.now(timezone.utc).isoformat(timespec="seconds")
        changed = (
            pos.state != "long"
            or abs(float(pos.qty or 0) - qty) > max(qty * 1e-8, 1e-12)
            or abs(float(pos.entry_price or 0) - avg) > max(avg * 1e-8, 1e-12)
            or abs(float(pos.cost_total or 0) - cost) > max(cost * 1e-8, 1e-12)
        )
        db.save_position(
            Position(
                state="long",
                ref_price=pos.ref_price or avg,
                entry_price=avg,
                qty=qty,
                cost_total=cost,
                buy_fee=pos.buy_fee,
                buy_fee_ccy=pos.buy_fee_ccy,
                buy_fee_usdt=pos.buy_fee_usdt,
                opened_at=opened,
                cascade_buy_step=pos.cascade_buy_step,
                cascade_sell_step=pos.cascade_sell_step,
                cycle_budget=pos.cycle_budget,
            ),
            self.bot_id,
        )
        if pos.state != "long":
            self._log(
                f"token {base} na OKX: {qty} @ méd. {avg} · PnL do token",
                force=True,
            )
        elif changed and abs(float(pos.qty or 0) - qty) > max(qty * 0.001, dust):
            self._log(
                f"nova compra no token: {qty} {base} · custo médio {avg}",
                force=True,
            )
        return db.get_position(self.bot_id)

    async def _hydrate(self) -> None:
        cfg = db.get_config(self.bot_id)
        price = await self.okx.get_last_price(cfg.inst_id)
        self.last_price = price
        try:
            self.okx_fee_rate = await self.okx.get_trade_fee(cfg.inst_id)
        except OkxError:
            self.okx_fee_rate = None
        pos = await self._sync_from_okx(cfg, price)
        if pos.state == "long":
            self._log(
                f"retomando {pos.qty} {cfg.inst_id} @ méd. {pos.entry_price}",
                force=True,
            )
            return
        self._log(f"sem posição. referência inicial = {price}", force=True)

    async def _quote_avail(self, quote: str) -> float:
        try:
            account = await self.okx.get_trading_account()
        except OkxError:
            return 0.0
        for item in account.get("details") or []:
            if str(item.get("ccy") or "").upper() == quote.upper():
                return float(self.okx._f(item.get("availBal")) or 0.0)
        return 0.0

    def _planned_spend(self, cfg, price: float, quote_avail: float) -> tuple[float, str]:
        """Retorna (valor em quote a gastar, detalhe). 0 amount = usa saldo disponível."""
        mode = str(getattr(cfg, "entry_mode", "quote") or "quote").lower()
        raw = float(getattr(cfg, "quote_amount", 0) or 0)
        if mode == "base":
            if raw > 0:
                spend = float(raw) * float(price)
                detail = f"{raw:g} token ≈ {spend:.4f} quote @ {price:g}"
            else:
                spend = float(quote_avail)
                detail = f"auto token · usa saldo quote {spend:.4f}"
        else:
            if raw > 0:
                spend = float(raw)
                detail = f"entrada {spend:g} quote"
            else:
                spend = float(quote_avail)
                detail = f"auto · usa saldo disponível {spend:.4f}"
        spend = max(0.0, min(spend, float(quote_avail)))
        return spend, detail

    async def _usdt_brl_rate(self) -> float | None:
        try:
            from .portfolio import PortfolioWatcher

            tickers = await self.okx.get_ticker_map()
            return PortfolioWatcher._usdt_brl_rate(tickers)
        except Exception:
            return None

    async def _apply_order_limits(
        self, spend: float, quote: str
    ) -> tuple[float, str | None, str | None]:
        if spend <= 0:
            return 0.0, None, None
        limits = db.get_order_limits()
        usdt_brl = await self._usdt_brl_rate()
        capped, note = clamp_spend_quote(
            spend,
            quote,
            min_usd=limits["min_usd"],
            max_usd=limits["max_usd"],
            usdt_brl=usdt_brl,
        )
        try:
            usd = quote_to_usd(capped, quote, usdt_brl)
            validate_order_usd(
                usd,
                min_usd=limits["min_usd"],
                max_usd=limits["max_usd"],
                label="Compra",
            )
        except ValueError as exc:
            return 0.0, note, str(exc)
        return capped, note, None

    def _flat_position(self, ref_price: float | None) -> Position:
        return Position(state="flat", ref_price=ref_price, cascade_buy_step=0, cascade_sell_step=0, cycle_budget=None)

    async def _decide(self, cfg, price: float, pos: Position) -> dict[str, Any]:
        """Validações em cadeia: para no 1º fail e devolve mensagem clara."""
        fee_rate = self.okx_fee_rate if self.okx_fee_rate is not None else cfg.fee_rate
        base, quote = parse_inst(cfg.inst_id)
        checks: list[dict[str, Any]] = []

        def fail(step: str, action: str, reason: str, **extra: Any) -> dict[str, Any]:
            return {
                "action": action,
                "reason": reason,
                "would_trade": False,
                "side": None,
                "drop_pct": extra.get("drop_pct"),
                "pnl_pct": extra.get("pnl_pct"),
                "pnl": extra.get("pnl"),
                "break_even": extra.get("break_even"),
                "target_price": extra.get("target_price"),
                "checks": checks,
                "failed_step": step,
                "planned_spend": extra.get("planned_spend"),
            }

        buy_n, sell_n = cascade_steps(cfg)
        has_pos = bool(pos.qty and pos.cost_total and pos.state == "long")
        can_add_more = cascade_enabled(cfg) and has_pos and int(pos.cascade_buy_step or 0) < buy_n

        if has_pos:
            snap = estimate_net_pnl(
                price,
                float(pos.qty),
                float(pos.cost_total),
                fee_rate,
                cfg.profit_target_pct,
                slippage_pct=DEFAULT_SELL_SLIPPAGE_PCT,
            )
            sell_step = int(pos.cascade_sell_step or 0)
            raw_target = sell_pnl_trigger_pct(cfg, sell_step)
            floor_pct = min_net_sell_pnl_pct(fee_rate, DEFAULT_SELL_SLIPPAGE_PCT)
            target_pnl = max(raw_target, floor_pct)
            hit = snap.pnl_pct >= target_pnl
            cascade_sell_note = ""
            if cascade_enabled(cfg):
                sp = sell_pcts(cfg)
                pct = sp[sell_step] if sell_step < len(sp) else sp[-1]
                cascade_sell_note = f" · cascata venda {sell_step + 1}/{sell_n} ({pct:g}%)"
            slip_note = f" · slip −{DEFAULT_SELL_SLIPPAGE_PCT:g}%"
            checks.append(
                {
                    "ok": hit,
                    "label": "PnL líquido ≥ alvo (c/ slip)",
                    "detail": (
                        f"{snap.pnl_pct:.2f}% / alvo {target_pnl:.2f}%"
                        f"{cascade_sell_note}{slip_note} ({snap.pnl:.4f} {quote})"
                    ),
                }
            )
            if hit:
                no_loss = snap.pnl >= 0
                checks.append(
                    {
                        "ok": no_loss,
                        "label": "Não vende no prejuízo (c/ slip)",
                        "detail": (
                            f"PnL {snap.pnl:.4f} · BE {snap.break_even:g}"
                            f" · px eff {snap.eff_price:g}"
                        ),
                    }
                )
                if no_loss:
                    avail = float((self._token_detail or {}).get("avail") or pos.qty or 0)
                    sell_qty = sell_tranche_qty(cfg, avail, sell_step) if cascade_enabled(cfg) else avail
                    sell_qty = min(sell_qty, avail)
                    checks.append(
                        {
                            "ok": sell_qty > 0,
                            "label": f"Saldo {base} para venda",
                            "detail": f"{avail:g} disponível · venderia {sell_qty:g}",
                        }
                    )
                    if sell_qty > 0:
                        reason = (
                            f"PnL líquido {snap.pnl_pct:.2f}% ≥ {target_pnl:.2f}%"
                            f" (slip {DEFAULT_SELL_SLIPPAGE_PCT:g}%) · venderia {sell_qty:g} {base}"
                        )
                        if cascade_enabled(cfg):
                            reason += f" (cascata {sell_step + 1}/{sell_n})"
                        return {
                            "action": "sell",
                            "reason": reason,
                            "would_trade": True,
                            "side": "sell",
                            "drop_pct": None,
                            "pnl_pct": snap.pnl_pct,
                            "pnl": snap.pnl,
                            "break_even": snap.break_even,
                            "target_price": snap.target_price,
                            "checks": checks,
                            "failed_step": None,
                            "sell_qty": sell_qty,
                        }
            if not can_add_more:
                if not hit:
                    return fail(
                        "pnl",
                        "wait_sell",
                        f"sem venda: PnL {snap.pnl_pct:.2f}% < alvo {target_pnl:.2f}% "
                        f"(tranche {sell_step + 1}/{sell_n}) · preço alvo {snap.target_price:g}",
                        pnl_pct=snap.pnl_pct,
                        pnl=snap.pnl,
                        break_even=snap.break_even,
                        target_price=snap.target_price,
                    )
                return fail(
                    "base_balance",
                    "wait_sell",
                    f"sem venda: saldo {base} insuficiente",
                    pnl_pct=snap.pnl_pct,
                    pnl=snap.pnl,
                    break_even=snap.break_even,
                    target_price=snap.target_price,
                )
            checks.clear()

        if not has_pos or can_add_more:
            if not pos.ref_price:
                checks.append(
                    {
                        "ok": False,
                        "label": "Referência de preço",
                        "detail": f"definir referência em {price:g} antes de comprar",
                    }
                )
                return fail(
                    "ref",
                    "set_ref",
                    f"definir referência em {price:g}",
                    drop_pct=0.0,
                )

            ref = float(pos.ref_price)
            step_idx = int(pos.cascade_buy_step or 0)
            trigger_pct = buy_drop_trigger_pct(cfg, step_idx)
            drop_pct = ((ref - price) / ref) * 100.0 if ref else 0.0
            # 1º ciclo sem token: entra na hora. Depois: só na queda vs ref (máxima recente).
            first_entry = (
                step_idx == 0
                and not has_pos
                and not db.bot_has_trades(self.bot_id)
            )
            need_drop = drop_pct >= trigger_pct or first_entry
            cascade_note = ""
            if cascade_enabled(cfg):
                bp = buy_pcts(cfg)
                pct = bp[step_idx] if step_idx < len(bp) else bp[-1]
                cascade_note = f" · cascata compra {step_idx + 1}/{buy_n} ({pct:g}%)"
            if first_entry:
                checks.append(
                    {
                        "ok": True,
                        "label": "Entrada inicial",
                        "detail": (
                            f"sem token e 1º ciclo → compra agora @ {price:g} "
                            f"(próximos ciclos: queda ≥ {trigger_pct:.2f}% vs ref)"
                        ),
                    }
                )
            else:
                buy_px = ref * (1.0 - trigger_pct / 100.0)
                checks.append(
                    {
                        "ok": need_drop,
                        "label": "Queda vs referência",
                        "detail": (
                            f"{drop_pct:.2f}% / alvo {trigger_pct:.2f}%{cascade_note} "
                            f"(ref {ref:g} → agora {price:g} · compra ≤ {buy_px:g})"
                        ),
                    }
                )
            if not need_drop:
                buy_px = ref * (1.0 - trigger_pct / 100.0)
                return fail(
                    "drop",
                    "wait_buy",
                    f"sem compra: espera queda {trigger_pct:.2f}% vs ref {ref:g} "
                    f"(agora {drop_pct:.2f}% · gatilho ≤ {buy_px:g})",
                    drop_pct=drop_pct,
                )

            self.okx.invalidate_private()
            quote_avail = await self._quote_avail(quote)
            planned, plan_detail = self._planned_spend(cfg, price, quote_avail)
            budget = float(pos.cycle_budget or planned)
            if cascade_enabled(cfg):
                spend = buy_tranche_quote(cfg, budget, step_idx)
                spend = min(spend, quote_avail)
                plan_detail = f"{plan_detail} · tranche {step_idx + 1}/{buy_n} = {spend:g} {quote}"
            else:
                spend = planned
            limit_note = None
            spend, limit_note, limit_err = await self._apply_order_limits(spend, quote)
            if limit_err:
                checks.append(
                    {
                        "ok": False,
                        "label": "Limite USD",
                        "detail": limit_err,
                    }
                )
                return fail(
                    "order_limit",
                    "wait_buy",
                    f"sem compra: {limit_err}",
                    drop_pct=drop_pct,
                )
            spend = min(spend, quote_avail)
            if limit_note:
                plan_detail = f"{plan_detail} · {limit_note}"
            enough = spend > 0 and quote_avail >= spend and spend >= 1e-8
            raw = float(getattr(cfg, "quote_amount", 0) or 0)
            mode = str(getattr(cfg, "entry_mode", "quote") or "quote")
            needed = (raw * price) if (mode == "base" and raw > 0) else (raw if raw > 0 else spend)
            if raw > 0 and quote_avail < needed and step_idx == 0:
                checks.append(
                    {
                        "ok": False,
                        "label": f"Saldo {quote} para compra",
                        "detail": f"{quote_avail:.4f} disponível < necessário {needed:.4f} · não executa",
                    }
                )
                return fail(
                    "balance",
                    "wait_buy",
                    f"sem compra: saldo {quote} insuficiente ({quote_avail:.4f} < {needed:.4f})",
                    drop_pct=drop_pct,
                )
            if not enough:
                checks.append(
                    {
                        "ok": False,
                        "label": f"Saldo {quote} para compra",
                        "detail": f"{quote_avail:.4f} disponível · sem valor utilizável · não executa",
                    }
                )
                return fail(
                    "balance",
                    "wait_buy",
                    f"sem compra: saldo {quote} insuficiente ({quote_avail:.4f})",
                    drop_pct=drop_pct,
                )
            checks.append(
                {
                    "ok": True,
                    "label": f"Saldo {quote} para compra",
                    "detail": f"{quote_avail:.4f} disponível · {plan_detail}",
                }
            )

            min_sz = None
            try:
                inst = await self.okx.get_instrument(cfg.inst_id)
                min_sz = self.okx._f(inst.get("minSz"))
            except Exception:
                min_sz = None
            est_base = spend / price if price else 0.0
            if min_sz and est_base < float(min_sz):
                checks.append(
                    {
                        "ok": False,
                        "label": "Tamanho mínimo OKX",
                        "detail": f"≈{est_base:g} {base} < min {min_sz} · não executa",
                    }
                )
                return fail(
                    "min_size",
                    "wait_buy",
                    f"sem compra: tamanho ≈{est_base:g} < mínimo {min_sz}",
                    drop_pct=drop_pct,
                    planned_spend=spend,
                )
            checks.append(
                {
                    "ok": True,
                    "label": "Tamanho mínimo OKX",
                    "detail": f"≈{est_base:g} {base}" + (f" ≥ min {min_sz}" if min_sz else " (min n/d)"),
                }
            )

            reason = (
                f"entrada inicial @ {price:g} · compraria {spend:g} {quote}"
                if first_entry
                else f"queda {drop_pct:.2f}% ≥ {trigger_pct:.2f}% · compraria {spend:g} {quote}"
            )
            if cascade_enabled(cfg):
                reason += f" (cascata {step_idx + 1}/{buy_n})"
            return {
                "action": "buy",
                "reason": reason,
                "would_trade": True,
                "side": "buy",
                "drop_pct": drop_pct if not first_entry else 0.0,
                "pnl_pct": None,
                "pnl": None,
                "break_even": None,
                "target_price": None,
                "checks": checks,
                "failed_step": None,
                "planned_spend": spend,
                "cycle_budget": budget if cascade_enabled(cfg) else None,
            }

        return fail("state", "wait_buy", "sem ação disponível", drop_pct=0.0)

    async def _tick(self, cfg) -> None:
        price = await self.okx.get_last_price(cfg.inst_id)
        self.last_price = price
        pos = await self._sync_from_okx(cfg, price)

        if pos.state == "flat" and not pos.ref_price:
            pos.ref_price = price
            db.save_position(pos, self.bot_id)
            first = not db.bot_has_trades(self.bot_id)
            self._log(
                f"referência = {price}"
                + (" · 1º ciclo sem token → compra na próxima checagem" if first else f" · espera queda {cfg.buy_pct:g}%"),
                force=True,
            )
            self._save_execution(
                cfg,
                {
                    "action": "set_ref",
                    "reason": (
                        f"referência {price:g} · entrada inicial (sem token)"
                        if first
                        else f"referência {price:g} · compra se cair ≥ {cfg.buy_pct:g}% (≤ {price * (1 - cfg.buy_pct / 100):g})"
                    ),
                    "would_trade": False,
                    "checks": [],
                },
                mode="live",
                executed=False,
                price=price,
                state=pos.state,
                force=True,
            )
            # 1º ciclo: segue o tick e compra; senão aguarda
            if not first:
                return
            pos = db.get_position(self.bot_id)

        # Flat aguardando: ref sobe com o preço (base = máxima recente)
        if pos.state == "flat" and pos.ref_price and price > float(pos.ref_price) * 1.00005:
            if db.bot_has_trades(self.bot_id):
                old = float(pos.ref_price)
                pos.ref_price = price
                db.save_position(pos, self.bot_id)
                self._log(
                    f"ref atualizada {old:g} → {price:g} (máx. recente) · "
                    f"compra se cair ≥ {cfg.buy_pct:g}%",
                    force=True,
                )

        if pos.state == "long" and (not pos.qty or not pos.cost_total):
            self._log("posição long inconsistente, resetando para flat", "warn", force=True)
            db.save_position(self._flat_position(price), self.bot_id)
            self._save_execution(
                cfg,
                {
                    "action": "wait_buy",
                    "reason": "posição long inconsistente, reset para flat",
                    "would_trade": False,
                    "checks": [],
                },
                mode="live",
                executed=False,
                price=price,
                state="flat",
                force=True,
            )
            return

        decision = await self._decide(cfg, price, pos)
        action = decision["action"]
        self._log(decision["reason"])
        executed = False

        if action == "buy" and decision["would_trade"]:
            again = await self._decide(cfg, price, db.get_position(self.bot_id))
            if not again.get("would_trade") or again.get("action") != "buy":
                self._log(f"compra abortada na revalidação: {again['reason']}", "warn", force=True)
                self._save_execution(cfg, again, mode="live", executed=False, price=price, state=pos.state)
                return
            self._log(f"executando compra live · {decision['reason']}", force=True)
            await self._buy(
                cfg,
                price,
                decision.get("planned_spend"),
                decision.get("cycle_budget"),
            )
            executed = True
        elif action == "sell" and decision["would_trade"]:
            pos = db.get_position(self.bot_id)
            again = await self._decide(cfg, price, pos)
            if not again.get("would_trade") or again.get("action") != "sell":
                self._log(f"venda abortada na revalidação: {again['reason']}", "warn", force=True)
                self._save_execution(cfg, again, mode="live", executed=False, price=price, state=pos.state)
                return
            min_pnl = max(
                sell_pnl_trigger_pct(cfg, int(pos.cascade_sell_step or 0)),
                min_net_sell_pnl_pct(
                    self.okx_fee_rate if self.okx_fee_rate is not None else cfg.fee_rate,
                    DEFAULT_SELL_SLIPPAGE_PCT,
                ),
            )
            if float(again.get("pnl_pct") or 0) < min_pnl:
                self._log("venda bloqueada: PnL abaixo do alvo", "warn", force=True)
                blocked = {**again, "action": "wait_sell", "reason": "venda bloqueada: PnL abaixo do alvo", "would_trade": False}
                self._save_execution(cfg, blocked, mode="live", executed=False, price=price, state=pos.state)
                return
            self._log(f"executando venda live · {decision['reason']}", force=True)
            await self._sell(cfg, price, pos, decision.get("sell_qty"))
            executed = True

        self._save_execution(
            cfg,
            decision,
            mode="live",
            executed=executed,
            price=price,
            state=pos.state,
        )

    async def _buy(
        self,
        cfg,
        price: float,
        spend_quote: float | None = None,
        cycle_budget: float | None = None,
    ) -> None:
        base, quote = parse_inst(cfg.inst_id)
        self.okx.invalidate_private()
        quote_avail = await self._quote_avail(quote)
        planned, _ = self._planned_spend(cfg, price, quote_avail)
        spend = float(spend_quote if spend_quote is not None else planned)
        spend, _note, limit_err = await self._apply_order_limits(spend, quote)
        if limit_err:
            raise OkxError(limit_err)
        if spend <= 0:
            raise OkxError(f"sem valor de compra utilizável em {quote}")
        if quote_avail <= 1e-12 or spend > quote_avail + 1e-8:
            raise OkxError(
                f"saldo trading {quote} insuficiente para comprar "
                f"(disponível {quote_avail:g}, pedido {spend:g}) — ordem não enviada"
            )
        cl_ord_id = db.make_cl_ord_id("bot", self.bot_id)
        # place_market_buy faz pré-check fresco de saldo/mínimo e aborta sem POST se falhar
        order = await self.okx.place_market_buy(cfg.inst_id, spend, cl_ord_id=cl_ord_id)
        ord_id = str(order.get("ordId") or "")
        fill = await self.okx.wait_fill(cfg.inst_id, ord_id) if ord_id else order
        state = str(fill.get("state") or "")
        avg_px = float(fill.get("avgPx") or price or 0)
        acc = float(fill.get("accFillSz") or 0)
        fee_raw = fill.get("fee")
        fee = float(fee_raw) if fee_raw not in (None, "") else None
        fee_ccy = fill.get("feeCcy") or None

        if acc <= 0 and avg_px > 0:
            acc = spend / avg_px

        qty = net_base_qty(acc, fee, fee_ccy, base)
        if qty <= 0:
            qty = acc
        cost = quote_cost(avg_px, acc, fee, fee_ccy, quote)
        if fee is None:
            cost = cost + (avg_px * acc * cfg.fee_rate)
        fee_usdt = fee_to_quote(fee, fee_ccy, avg_px, quote, base)
        if fee is None:
            fee_usdt = avg_px * acc * cfg.fee_rate
            cost = avg_px * acc + fee_usdt

        fill_qty, fill_avg, fill_fee_usdt = qty, avg_px, fee_usdt
        prev = db.get_position(self.bot_id)
        if prev.state == "long" and prev.qty and prev.cost_total:
            qty = float(prev.qty) + qty
            cost = float(prev.cost_total) + cost
            avg_px = cost / qty if qty else avg_px
            fee_usdt = float(prev.buy_fee_usdt or 0) + fee_usdt
            opened = prev.opened_at
        else:
            opened = datetime.now(timezone.utc).isoformat(timespec="seconds")

        buy_step = int(prev.cascade_buy_step or 0) + 1 if cascade_enabled(cfg) else 0
        budget = prev.cycle_budget or cycle_budget
        if cascade_enabled(cfg) and not budget:
            quote_avail = await self._quote_avail(quote)
            planned, _ = self._planned_spend(cfg, price, quote_avail)
            budget = float(planned)

        db.save_position(
            Position(
                state="long",
                ref_price=prev.ref_price or avg_px,
                entry_price=avg_px,
                qty=qty,
                cost_total=cost,
                buy_fee=fee,
                buy_fee_ccy=fee_ccy,
                buy_fee_usdt=fee_usdt,
                opened_at=opened,
                cascade_buy_step=buy_step,
                cascade_sell_step=0 if buy_step <= 1 else int(prev.cascade_sell_step or 0),
                cycle_budget=budget,
            ),
            self.bot_id,
        )
        try:
            await self._sync_from_okx(cfg, avg_px)
        except OkxError:
            pass
        db.add_trade(
            side="buy",
            inst_id=cfg.inst_id,
            qty=fill_qty,
            avg_px=fill_avg,
            fee=fee,
            fee_ccy=fee_ccy,
            fee_usdt=fill_fee_usdt,
            pnl_realized=None,
            order_id=ord_id or None,
            status=state or "filled",
            bot_id=self.bot_id,
            origin="bot",
            bot_name=cfg.name,
            cl_ord_id=cl_ord_id,
        )
        self._log(
            f"compra fill {fill_qty} @ {fill_avg} | posição {qty} @ méd. {avg_px} | custo {cost:.4f} | fee ≈ {fill_fee_usdt:.4f}",
            force=True,
        )

    async def _sell(self, cfg, price: float, pos: Position, sell_qty: float | None = None) -> None:
        base, quote = parse_inst(cfg.inst_id)
        avail = float((self._token_detail or {}).get("avail") or pos.qty or 0)
        if sell_qty is None:
            sell_qty = avail if avail > 0 else float(pos.qty or 0)
        else:
            sell_qty = min(float(sell_qty), avail if avail > 0 else float(pos.qty or 0))
        if sell_qty <= 0:
            sell_qty = float(pos.qty or 0)
        cl_ord_id = db.make_cl_ord_id("bot", self.bot_id)
        order = await self.okx.place_market_sell(cfg.inst_id, sell_qty, cl_ord_id=cl_ord_id)
        ord_id = str(order.get("ordId") or "")
        fill = await self.okx.wait_fill(cfg.inst_id, ord_id) if ord_id else order
        state = str(fill.get("state") or "")
        avg_px = float(fill.get("avgPx") or price or 0)
        acc = float(fill.get("accFillSz") or pos.qty or 0)
        fee_raw = fill.get("fee")
        fee = float(fee_raw) if fee_raw not in (None, "") else None
        fee_ccy = fill.get("feeCcy") or None

        proceeds = net_sell_proceeds(
            avg_px, acc, fee, fee_ccy, quote, base, avg_px
        )
        if fee is None:
            proceeds = avg_px * acc * (1.0 - cfg.fee_rate)
        fee_usdt = fee_to_quote(fee, fee_ccy, avg_px, quote, base)
        if fee is None:
            fee_usdt = avg_px * acc * cfg.fee_rate

        cost = float(pos.cost_total or 0)
        total_qty = float(pos.qty or acc or 1)
        cost_share = cost * (acc / total_qty) if total_qty else cost
        pnl = proceeds - cost_share

        db.add_trade(
            side="sell",
            inst_id=cfg.inst_id,
            qty=acc,
            avg_px=avg_px,
            fee=fee,
            fee_ccy=fee_ccy,
            fee_usdt=fee_usdt,
            pnl_realized=pnl,
            order_id=ord_id or None,
            status=state or "filled",
            bot_id=self.bot_id,
            origin="bot",
            bot_name=cfg.name,
            cl_ord_id=cl_ord_id,
        )
        remaining_qty = max(0.0, total_qty - acc)
        dust = max(await self._min_size(cfg.inst_id), 0.0)
        if remaining_qty <= dust:
            db.save_position(self._flat_position(avg_px), self.bot_id)
        else:
            remaining_cost = max(0.0, cost - cost_share)
            sell_step = int(pos.cascade_sell_step or 0) + 1 if cascade_enabled(cfg) else 0
            db.save_position(
                Position(
                    state="long",
                    ref_price=pos.ref_price,
                    entry_price=remaining_cost / remaining_qty if remaining_qty else avg_px,
                    qty=remaining_qty,
                    cost_total=remaining_cost,
                    buy_fee=pos.buy_fee,
                    buy_fee_ccy=pos.buy_fee_ccy,
                    buy_fee_usdt=pos.buy_fee_usdt,
                    opened_at=pos.opened_at,
                    cascade_buy_step=int(pos.cascade_buy_step or 0),
                    cascade_sell_step=sell_step,
                    cycle_budget=pos.cycle_budget,
                ),
                self.bot_id,
            )
        self._log(
            f"venda fill {acc} @ {avg_px} | PnL realizado {pnl:.4f} | fee ≈ {fee_usdt:.4f}"
            + (f" | restam {remaining_qty:g} {base}" if remaining_qty > dust else " | flat"),
            force=True,
        )
