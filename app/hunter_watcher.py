"""Watcher do Caçador: radar de dips Spot + melhor estratégia por token (sem automação)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from . import db, hunter as hunter_scan
from . import lab as lab_sim
from . import strategies as strat_catalog
from .okx_client import OkxClient, OkxError, parse_inst


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def budget_to_quote_amount(okx: OkxClient, cfg: dict[str, Any], inst_id: str) -> float:
    """Converte valor do ciclo (BRL/USDT) para quote_amount do par Spot (ex. USDT). 0 = saldo livre."""
    budget = float(cfg.get("quote_amount") or 0)
    if budget <= 0:
        return 0.0
    ccy = str(cfg.get("budget_ccy") or "BRL").upper()
    quote = ""
    try:
        _b, quote = parse_inst(inst_id)
    except ValueError:
        quote = "USDT"
    quote = (quote or "USDT").upper()
    if ccy == quote or (ccy in {"USD", "USDT", "USDC"} and quote in {"USDT", "USDC", "USD"}):
        return budget
    try:
        tickers = await okx.get_ticker_map()
    except Exception:
        tickers = {}
    if ccy == "BRL" and quote in {"USDT", "USDC", "USD"}:
        rate = okx._f((tickers.get("USDT-BRL") or {}).get("last"))
        if not rate:
            inv = okx._f((tickers.get("BRL-USDT") or {}).get("last"))
            rate = (1.0 / inv) if inv and inv > 0 else None
        if rate and rate > 0:
            return budget / rate
    if ccy in {"USDT", "USDC", "USD"} and quote == "BRL":
        rate = okx._f((tickers.get("USDT-BRL") or {}).get("last"))
        if rate and rate > 0:
            return budget * rate
    return budget


def _best_strategy_payload(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    strat = row.get("strategy") or {}
    summary = row.get("summary") or {}
    params = row.get("params") or {}
    return {
        "id": strat.get("id"),
        "name": strat.get("name"),
        "buy_pct": params.get("buy_pct", strat.get("buy_pct")),
        "profit_target_pct": params.get("profit_target_pct", strat.get("profit_target_pct")),
        "fee_rate_pct": params.get("fee_rate_pct", strat.get("fee_rate_pct")),
        "capital_return_pct": summary.get("capital_return_pct"),
        "assertiveness": summary.get("assertiveness"),
        "grade": summary.get("grade"),
        "verdict": summary.get("verdict"),
        "recommend_create": bool(summary.get("recommend_create")),
        "cycles_closed": summary.get("cycles_closed"),
        "wins": summary.get("wins"),
        "losses": summary.get("losses"),
        "days": params.get("days"),
        "aporte": params.get("aporte"),
        "aporte_ccy": params.get("aporte_ccy"),
        "note": summary.get("note"),
    }


def _validation_checks(candidate: dict[str, Any], *, order_usd: float, max_spread: float) -> list[dict[str, Any]]:
    """Checklist de validações para o modal de detalhes."""
    rent = candidate.get("rentability") or {}
    drop = float(candidate.get("drop_pct") or 0)
    vol = float(candidate.get("vol") or 0)
    spr = candidate.get("spread_pct")
    book = candidate.get("book_usd")
    liq = str(candidate.get("liquidity") or "D")
    bs = candidate.get("best_strategy") or {}
    checks = [
        {
            "id": "region",
            "ok": True,
            "label": "Negociável na sua região",
            "detail": "Par liberado em /account/instruments (evita OKX 51155)",
        },
        {
            "id": "spot",
            "ok": True,
            "label": "Somente Spot",
            "detail": f"Par {candidate.get('inst_id')}",
        },
        {
            "id": "drop",
            "ok": drop >= 2,
            "label": f"Queda 24h {drop:.2f}%",
            "detail": "Dip Spot nas últimas 24h",
        },
        {
            "id": "volume",
            "ok": vol >= float(candidate.get("vol_min_effective") or 50_000),
            "label": f"Volume 24h ≈ ${vol:,.0f}",
            "detail": (
                f"Mín. efetivo ≈ ${float(candidate.get('vol_min_effective') or 50_000):,.0f}"
                + (
                    f" · listagem ~{float(candidate['age_days']):.1f}d"
                    if candidate.get("age_days") is not None
                    else ""
                )
                + (" · token novo" if candidate.get("is_new") else "")
            ),
        },
        {
            "id": "age",
            "ok": True,
            "label": (
                f"Idade no Spot ≈ {float(candidate['age_days']):.1f}d"
                if candidate.get("age_days") is not None
                else "Idade no Spot —"
            ),
            "detail": (
                (
                    f"Listado {candidate.get('listed_at')}"
                    if candidate.get("listed_at")
                    else "listTime OKX"
                )
                + (" · novo (<14d): vol menor é esperado" if candidate.get("is_new") else "")
            ),
        },
        {
            "id": "spread",
            "ok": spr is not None and float(spr) <= max_spread,
            "label": f"Spread {float(spr):.2f}%" if spr is not None else "Spread —",
            "detail": f"Máx. filtro {max_spread:g}% · bid/ask do ticker",
        },
        {
            "id": "liquidity",
            "ok": liq in {"A", "B", "C"},
            "label": f"Liquidez {liq}",
            "detail": candidate.get("liquidity_tip") or "",
        },
        {
            "id": "book",
            "ok": book is None or float(book) <= 0 or order_usd <= 0 or float(book) >= order_usd,
            "label": f"Livro ≈ ${float(book):,.0f}" if book is not None else "Livro (sem amostra)",
            "detail": f"Referência de ordem ≈ ${order_usd:.2f}",
        },
        {
            "id": "edge",
            "ok": bool(rent.get("tradeable")),
            "label": (
                f"Edge líquido ≈ {rent.get('net_edge_pct')}%"
                if rent.get("net_edge_pct") is not None
                else "Edge / viabilidade"
            ),
            "detail": "; ".join(rent.get("issues") or []) or f"Custo ida+volta ≈ {rent.get('cost_pct')}%",
        },
        {
            "id": "strategy",
            "ok": bool(bs.get("id")),
            "label": f"Estratégia: {bs.get('name') or '—'}",
            "detail": (
                f"Retorno {bs.get('capital_return_pct')}% · assert. {bs.get('assertiveness')}"
                if bs.get("id")
                else (candidate.get("best_strategy_error") or "Sem backtest")
            ),
        },
        {
            "id": "recommend",
            "ok": bool(bs.get("recommend_create")),
            "label": "Qualidade ok p/ criar bot" if bs.get("recommend_create") else "Qualidade frágil p/ bot",
            "detail": str(bs.get("verdict") or bs.get("note") or ""),
        },
    ]
    return checks


class HunterWatcher:
    def __init__(self, okx: OkxClient, hub: Any) -> None:
        self.okx = okx
        self.hub = hub
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()
        self.last_error: Optional[str] = None
        self.last_scan: Optional[dict[str, Any]] = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._loop(), name="hunter-auto-scan")

    async def _loop(self) -> None:
        """Loop de auto-scan: verifica se está habilitado e executa a cada scan_interval_min."""
        while not self._stop.is_set():
            cfg = db.get_hunter_settings()
            if not cfg.get("enabled"):
                # Se desabilitado, espera 30s e checa de novo
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=30.0)
                except asyncio.TimeoutError:
                    pass
                continue
            interval = max(1.0, float(cfg.get("scan_interval_min") or 10)) * 60.0
            try:
                await self.scan_now(force=False)
            except Exception as exc:
                self.last_error = str(exc)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    async def stop(self) -> None:
        self._stop.set()
        task = self._task
        if task:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=4)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                task.cancel()
            self._task = None

    async def _attach_best_strategies(
        self,
        candidates: list[dict[str, Any]],
        *,
        cfg: dict[str, Any],
        order_usd: float,
        budget: float,
        budget_ccy: str,
    ) -> list[dict[str, Any]]:
        # Candles longos (90d) cobrem diário/semanal/mensal numa só descarga
        days_max = 90
        bar = lab_sim.bar_for_days(days_max)
        catalog = strat_catalog.list_strategies(db.list_custom_strategies())
        sem = asyncio.Semaphore(3)

        async def one(c: dict[str, Any]) -> dict[str, Any]:
            out = dict(c)
            inst = str(c.get("inst_id") or "").upper()
            if not inst:
                out["best_strategy"] = None
                out["best_strategy_error"] = "sem par"
                return out
            async with sem:
                try:
                    candles = await self.okx.get_candles(
                        inst, bar=bar, days=days_max, limit=800
                    )
                    if not candles:
                        out["best_strategy"] = None
                        out["best_strategy_error"] = "sem candles"
                        return out
                    aporte_quote = await budget_to_quote_amount(self.okx, cfg, inst)
                    if aporte_quote <= 0:
                        aporte_quote = float(order_usd or 50)
                    aporte_input = budget if budget > 0 else aporte_quote
                    if budget_ccy == "BRL" and budget > 0:
                        aporte_ccy_lab = "USDT"
                        aporte_input_lab = aporte_quote
                    elif budget_ccy in {"USDT", "USDC", "USD"}:
                        aporte_ccy_lab = "USDT"
                        aporte_input_lab = aporte_input
                    else:
                        aporte_ccy_lab = "USDT"
                        aporte_input_lab = aporte_quote

                    strategies_by_hz: dict[str, dict[str, Any] | None] = {}
                    tops_by_hz: dict[str, list] = {}
                    for hz, preset in hunter_scan.HORIZONS.items():
                        days = int(preset["validate_days"])
                        ranked = lab_sim.rank_strategies_on_candles(
                            catalog,
                            candles,
                            inst_id=inst,
                            aporte_quote=aporte_quote,
                            days=days,
                            aporte_input=aporte_input_lab,
                            aporte_ccy=aporte_ccy_lab,
                            sort="profit",
                        )
                        best = ranked[0] if ranked else None
                        strategies_by_hz[hz] = _best_strategy_payload(best)
                        tops_by_hz[hz] = [
                            _best_strategy_payload(r) for r in ranked[:3] if r
                        ]

                    bundle = hunter_scan.pick_best_horizon_bundle(
                        spot_score=float(out.get("score") or 0),
                        tradeable=bool(out.get("tradeable")),
                        candles=candles,
                        strategies_by_horizon=strategies_by_hz,
                    )
                    out["horizons"] = {
                        k: {
                            "id": v["id"],
                            "short": v["short"],
                            "label": v["label"],
                            "validate_days": v["validate_days"],
                            "sell_fitness": v["sell_fitness"],
                            "bounce_prob_pct": v["bounce_prob_pct"],
                            "cycles_per_day": v["cycles_per_day"],
                            "fitness_label": v["fitness_label"],
                            "strategy_name": (v.get("best_strategy") or {}).get("name")
                            or (v.get("best_strategy") or {}).get("id"),
                            "capital_return_pct": (v.get("best_strategy") or {}).get(
                                "capital_return_pct"
                            ),
                        }
                        for k, v in (bundle.get("horizons") or {}).items()
                    }
                    out["best_horizon"] = bundle["best_horizon"]
                    out["best_horizon_short"] = bundle["best_horizon_short"]
                    out["best_horizon_label"] = bundle["best_horizon_label"]
                    out["prediction"] = bundle["prediction"]
                    out["candle_features"] = bundle["candle_features"]
                    out["best_strategy"] = bundle["best_strategy"]
                    out["best_strategy_id"] = (bundle.get("best_strategy") or {}).get("id")
                    out["strategies_top"] = tops_by_hz.get(bundle["best_horizon"]) or []
                    if out.get("prediction"):
                        out["prob_up_pct"] = out["prediction"].get("bounce_prob_pct")
                        out["sell_fitness"] = out["prediction"].get("sell_fitness")
                        out["cycles_per_day"] = out["prediction"].get("cycles_per_day")
                    bs = out.get("best_strategy") or {}
                    out.update(
                        hunter_scan.suggested_levels(
                            out.get("last"),
                            profit_target_pct=bs.get("profit_target_pct"),
                            fee_rate_pct=float(bs.get("fee_rate_pct") or 0.10),
                            spread_pct_val=out.get("spread_pct"),
                            horizon=out.get("best_horizon"),
                            features=out.get("candle_features"),
                            drop_pct=out.get("drop_pct"),
                        )
                    )
                    net = out.get("suggested_target_pct")
                    if net is not None:
                        rent = hunter_scan.rentability_check(
                            profit_target_pct=float(net),
                            fee_rate_pct=float(bs.get("fee_rate_pct") or 0.10),
                            spread_pct_val=out.get("spread_pct"),
                            order_usd=order_usd,
                            vol_24h=float(out.get("vol") or 0),
                            book_usd=out.get("book_usd"),
                        )
                        out["rentability"] = rent
                        out["tradeable"] = bool(rent.get("tradeable"))
                    out["checks"] = _validation_checks(
                        out,
                        order_usd=order_usd,
                        max_spread=float(cfg.get("max_spread_pct") or 0.8),
                    )
                    out["validation_score"] = sum(1 for ch in out["checks"] if ch.get("ok"))
                    out["validation_total"] = len(out["checks"])
                except Exception as exc:
                    out["best_strategy"] = None
                    out["best_strategy_error"] = str(exc)[:160]
                    out["strategies_top"] = []
                    out["horizons"] = {}
                    out["checks"] = _validation_checks(
                        out,
                        order_usd=order_usd,
                        max_spread=float(cfg.get("max_spread_pct") or 0.8),
                    )
                    out["validation_score"] = sum(1 for ch in out["checks"] if ch.get("ok"))
                    out["validation_total"] = len(out["checks"])
                    out.update(
                        hunter_scan.suggested_levels(
                            out.get("last"),
                            profit_target_pct=None,
                            fee_rate_pct=0.10,
                            spread_pct_val=out.get("spread_pct"),
                            drop_pct=out.get("drop_pct"),
                        )
                    )
                return out

        return list(await asyncio.gather(*[one(c) for c in candidates]))

    async def scan_now(self, *, force: bool = False) -> dict[str, Any]:
        cfg = db.get_hunter_settings()
        limits = db.get_order_limits()
        # Target/fee neutros só para checagem de liquidez no score
        profit_target = 3.0
        fee_pct = 0.10
        budget = float(cfg.get("quote_amount") or 0)
        budget_ccy = str(cfg.get("budget_ccy") or "BRL").upper()
        usdt_brl = None
        try:
            tickers = await self.okx.get_ticker_map()
            usdt_brl = self.okx._f((tickers.get("USDT-BRL") or {}).get("last"))
            if not usdt_brl:
                inv = self.okx._f((tickers.get("BRL-USDT") or {}).get("last"))
                if inv and inv > 0:
                    usdt_brl = 1.0 / inv
        except Exception:
            usdt_brl = None
        if budget > 0:
            if budget_ccy == "BRL" and usdt_brl and usdt_brl > 0:
                order_usd = budget / usdt_brl
            elif budget_ccy in {"USDT", "USDC", "USD"}:
                order_usd = budget
            else:
                order_usd = budget
        else:
            order_usd = float(limits.get("max_usd") or 50)
        lo = float(limits.get("min_usd") or 5)
        hi = float(limits.get("max_usd") or 100)
        order_usd = max(lo, min(hi, order_usd))
        # União dos 3 horizontes como faixa base; filtros avançados do user sobrescrevem
        band = hunter_scan.union_horizon_filters()
        min_drop = float(cfg.get("min_drop_pct") or band["min_drop_pct"])
        max_drop = float(cfg.get("max_drop_pct") or band["max_drop_pct"])
        min_vol = float(cfg.get("min_vol_usd") or band["min_vol_usd"])
        max_spread = float(cfg.get("max_spread_pct") or band["max_spread_pct"])
        require_tradeable = bool(cfg.get("require_tradeable"))
        top_n = max(1, min(30, int(cfg.get("top_n") or 30)))
        validate_days = 90  # multi-horizonte: candles cobrem até mensal

        cache_key = (
            f"hunter_scan_v10|all|{cfg.get('quote')}|{min_drop}|{max_drop}|"
            f"{min_vol}|{max_spread}|{order_usd:.2f}|{require_tradeable}|{top_n}|{budget}|{budget_ccy}"
        )
        if not force:
            hit = db.get_api_cache(cache_key, float(cfg.get("cache_ttl_s") or 1800))
            if hit:
                payload = dict(hit["payload"])
                payload["cached"] = True
                payload["cache_age_s"] = round(
                    __import__("time").time() - float(hit["ts"]), 1
                )
                self.last_scan = payload
                return payload

        pairs = await self.okx.list_spot_pairs(quote=str(cfg.get("quote") or "USDT"))
        tradable_ids = await self.okx.get_account_tradable_spot_ids()
        exclude: set[str] = set()

        # Funil diagnóstico (por que a lista pode ficar vazia)
        in_drop = 0
        in_drop_vol = 0
        for p in pairs:
            chg = p.get("chg24")
            if chg is None:
                continue
            drop = -float(chg)
            if drop < min_drop or drop > max_drop:
                continue
            in_drop += 1
            age = p.get("age_days")
            if age is None and p.get("list_time"):
                age = hunter_scan.listing_age_days(p.get("list_time"))
            vol_need = hunter_scan.effective_min_vol(min_vol, age)
            if float(p.get("vol") or 0) >= vol_need:
                in_drop_vol += 1

        pre = hunter_scan.scan_dips(
            pairs,
            min_drop_pct=min_drop,
            max_drop_pct=max_drop,
            min_vol=min_vol,
            max_spread_pct=max_spread,
            profit_target_pct=profit_target,
            fee_rate_pct=fee_pct,
            order_usd=order_usd,
            blacklist=list(cfg.get("blacklist") or []),
            exclude_inst=exclude,
            top_n=min(50, top_n + 10),
            require_tradeable=False,
        )

        enrich_n = min(len(pre), top_n)
        books: dict[str, float] = {}
        if enrich_n:
            results = await asyncio.gather(
                *[self.okx.get_order_book_usd(c["inst_id"], depth=5) for c in pre[:enrich_n]],
                return_exceptions=True,
            )
            for c, res in zip(pre[:enrich_n], results):
                if isinstance(res, Exception):
                    continue
                depth = float(res.get("book_usd") or 0)
                if depth > 0:
                    books[str(c["inst_id"])] = depth

        by_inst = {str(p.get("inst_id") or "").upper(): p for p in pairs}
        enriched_pairs = []
        for c in pre:
            inst = c["inst_id"]
            base_row = dict(by_inst.get(inst) or {})
            base_row.update(
                {
                    "inst_id": inst,
                    "base": c.get("base"),
                    "quote": c.get("quote"),
                    "icon": c.get("icon"),
                    "icon_alt": c.get("icon_alt"),
                    "last": c.get("last"),
                    "bid": c.get("bid"),
                    "ask": c.get("ask"),
                    "chg24": c.get("chg24"),
                    "vol": c.get("vol"),
                    "book_usd": books.get(inst),
                    "list_time": c.get("list_time") or base_row.get("list_time"),
                    "listed_at": c.get("listed_at") or base_row.get("listed_at"),
                    "age_days": c.get("age_days") if c.get("age_days") is not None else base_row.get("age_days"),
                }
            )
            enriched_pairs.append(base_row)

        candidates = hunter_scan.scan_dips(
            enriched_pairs,
            min_drop_pct=min_drop,
            max_drop_pct=max_drop,
            min_vol=min_vol,
            max_spread_pct=max_spread,
            profit_target_pct=profit_target,
            fee_rate_pct=fee_pct,
            order_usd=order_usd,
            blacklist=list(cfg.get("blacklist") or []),
            exclude_inst=exclude,
            top_n=top_n,
            require_tradeable=require_tradeable,
        )
        # Filtro «viáveis» não pode esvaziar o radar: mostra os dips que já passaram
        # queda/volume/spread, só ordenados com os viáveis na frente.
        if require_tradeable and not candidates and pre:
            candidates = hunter_scan.scan_dips(
                enriched_pairs,
                min_drop_pct=min_drop,
                max_drop_pct=max_drop,
                min_vol=min_vol,
                max_spread_pct=max_spread,
                profit_target_pct=profit_target,
                fee_rate_pct=fee_pct,
                order_usd=order_usd,
                blacklist=list(cfg.get("blacklist") or []),
                exclude_inst=exclude,
                top_n=top_n,
                require_tradeable=False,
            )
        candidates = await self._attach_best_strategies(
            candidates,
            cfg=cfg,
            order_usd=order_usd,
            budget=budget,
            budget_ccy=budget_ccy,
        )
        candidates = hunter_scan.rank_by_sell_fitness(candidates)
        for c in candidates:
            if not c.get("checks"):
                c["checks"] = _validation_checks(
                    c, order_usd=order_usd, max_spread=max_spread
                )
                c["validation_score"] = sum(1 for ch in c["checks"] if ch.get("ok"))
                c["validation_total"] = len(c["checks"])
        tradeable_n = sum(1 for c in candidates if c.get("tradeable"))
        empty_hint = None
        if not candidates:
            if in_drop == 0:
                empty_hint = (
                    f"Nenhum par Spot negociável na sua região com queda entre "
                    f"{min_drop:g}% e {max_drop:g}% agora."
                )
            elif in_drop_vol == 0:
                empty_hint = (
                    f"{in_drop} par(es) na faixa de queda, mas nenhum com vol ≥ "
                    f"${min_vol:,.0f}. Baixe «Vol. mín. USD» nos filtros."
                )
            elif require_tradeable:
                empty_hint = (
                    f"{in_drop_vol} candidato(s) com volume, mas nenhum passou em "
                    f"«Só listar viáveis» (alvo não cobre taxa+spread ou a ordem não cabe no livro). "
                    f"Desligue o filtro ou afrouxe o spread / o valor de referência."
                )
            else:
                empty_hint = (
                    f"{in_drop} na faixa de queda · {in_drop_vol} com volume · "
                    f"nenhum passou no filtro de spread (máx {max_spread:g}%)."
                )
        payload = {
            "candidates": candidates,
            "count": len(candidates),
            "tradeable_count": tradeable_n,
            "quote": cfg.get("quote") or "USDT",
            "min_drop_pct": min_drop,
            "max_drop_pct": max_drop,
            "min_vol_usd": min_vol,
            "max_spread_pct": max_spread,
            "order_usd": order_usd,
            "budget": budget,
            "budget_ccy": budget_ccy,
            "usdt_brl": usdt_brl,
            "validate_days": validate_days,
            "horizon": "all",
            "horizon_label": "Dia · Semana · Mês",
            "horizon_mode": "all",
            "top_n": top_n,
            "region_filter": tradable_ids is not None,
            "region_tradable_count": len(tradable_ids) if tradable_ids is not None else None,
            "pairs_scanned": len(pairs),
            "funnel": {
                "pairs": len(pairs),
                "in_drop_band": in_drop,
                "in_drop_and_vol": in_drop_vol,
                "pre_candidates": len(pre),
                "final": len(candidates),
            },
            "empty_hint": empty_hint,
            "scanned_at": _now(),
            "cached": False,
            "cache_age_s": 0,
            "mode": "radar",
        }
        db.set_api_cache(cache_key, payload, kind="hunter_scan")
        # Notificar novos dips (não vistos no scan anterior)
        prev_insts = set()
        if self.last_scan and self.last_scan.get("candidates"):
            prev_insts = {str(c.get("inst_id") or "") for c in self.last_scan["candidates"]}
        if candidates:
            from .notifications import notify_hunter_alert
            from .context import current_user_id
            uid = current_user_id.get() or "_global"
            for c in candidates[:3]:  # Max 3 alertas por scan
                cid = str(c.get("inst_id") or "")
                if cid and cid not in prev_insts:
                    drop = abs(float(c.get("chg24") or 0))
                    price = float(c.get("last") or 0)
                    if drop > 0 and price > 0:
                        notify_hunter_alert(uid, cid, drop, price)
        self.last_scan = payload
        self.last_error = None
        return payload

    async def ensure_hunter_bot(self) -> str:
        raise RuntimeError("Caçador não cria bot automático — use Criar bot na lista")

    async def maybe_rotate(self) -> Optional[dict[str, Any]]:
        return None
