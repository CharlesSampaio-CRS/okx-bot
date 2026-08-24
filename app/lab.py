"""Backtest em memória — sem gravar no Mongo. Foco: gatilhos + motivo de não executar."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import BotConfig
from .okx_client import icon_urls, parse_inst
from .pnl import estimate_net_pnl

# Tokens comuns para o Lab (pares USDT listados na OKX).
LAB_TOKEN_PRESETS: list[dict[str, str]] = [
    {"symbol": "BTC", "inst_id": "BTC-USDT"},
    {"symbol": "ETH", "inst_id": "ETH-USDT"},
    {"symbol": "SOL", "inst_id": "SOL-USDT"},
    {"symbol": "XRP", "inst_id": "XRP-USDT"},
    {"symbol": "DOGE", "inst_id": "DOGE-USDT"},
    {"symbol": "ADA", "inst_id": "ADA-USDT"},
    {"symbol": "AVAX", "inst_id": "AVAX-USDT"},
    {"symbol": "LINK", "inst_id": "LINK-USDT"},
]


def lab_token_catalog(ticker_keys: set[str] | list[str]) -> list[dict[str, Any]]:
    """Marca quais presets têm par spot na OKX (ticker live)."""
    keys = {k.upper() for k in ticker_keys}
    out: list[dict[str, Any]] = []
    for row in LAB_TOKEN_PRESETS:
        inst = row["inst_id"]
        available = inst.upper() in keys
        icon, icon_alt = icon_urls(row["symbol"])
        out.append(
            {
                "symbol": row["symbol"],
                "inst_id": inst,
                "available": available,
                "icon": icon,
                "icon_alt": icon_alt,
                "note": None if available else "Sem par spot na OKX",
            }
        )
    return out


def _ts_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat(timespec="seconds")


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def score_quality(
    *,
    cycles: list[dict[str, Any]],
    buys: int,
    sells: int,
    realized: float,
    capital_start: float,
    capital_end: float,
    capital_ret: float,
    target_pct: float,
    ideal_pnl_pct: float,
    open_pos: dict[str, Any] | None,
    days: int | None = None,
) -> dict[str, Any]:
    """Índice de assertividade (0–100) + veredito de qualidade / lucro no histórico."""
    closed = len(cycles)
    hits = sum(1 for c in cycles if c.get("hit_target"))
    wins = sum(1 for c in cycles if float(c.get("pnl") or 0) > 0)
    losses = sum(1 for c in cycles if float(c.get("pnl") or 0) < 0)
    hit_rate = (hits / closed * 100.0) if closed else 0.0
    win_rate = (wins / closed * 100.0) if closed else 0.0

    # Amostra mínima sobe com o período (mais dias → exige mais ciclos)
    d = int(days or 30)
    min_cycles = 2 if d <= 7 else 3 if d <= 30 else 4 if d <= 60 else 5
    sample_score = _clamp((closed / min_cycles) * 100.0) if min_cycles else 0.0

    # Acertos no alvo
    hit_score = hit_rate

    # Lucro de capital (obrigatório para “garantia”)
    if capital_start > 0 and capital_end >= capital_start and realized >= 0 and losses == 0:
        # bônus se retorno por ciclo médio ≥ ~alvo líquido esperado
        avg_pct = (sum(float(c.get("pnl_pct") or 0) for c in cycles) / closed) if closed else 0.0
        expect = float(ideal_pnl_pct or target_pct or 1.0)
        ratio = (avg_pct / expect) if expect else 0.0
        profit_score = _clamp(55.0 + 45.0 * min(1.2, ratio))
    elif capital_end > capital_start and realized > 0:
        profit_score = _clamp(35.0 + capital_ret * 8.0)
    elif capital_end >= capital_start:
        profit_score = 25.0
    else:
        profit_score = _clamp(15.0 + capital_ret)  # capital_ret negativo puxa para baixo

    # Conclusão de ciclos (não ficar preso em long sem venda)
    if buys <= 0:
        completion_score = 0.0
    else:
        completion_score = _clamp((sells / buys) * 100.0)
        if open_pos and float(open_pos.get("pnl") or 0) < 0:
            completion_score = _clamp(completion_score - 25.0)

    assertiveness = round(
        hit_score * 0.35
        + profit_score * 0.30
        + sample_score * 0.20
        + completion_score * 0.15,
        1,
    )

    profit_locked = (
        closed > 0
        and losses == 0
        and hits == closed
        and realized >= 0
        and capital_end >= capital_start
        and (not open_pos or float(open_pos.get("pnl") or 0) >= 0)
    )
    pnl_validated = profit_locked and closed >= min_cycles
    recommend_create = pnl_validated and assertiveness >= 70.0

    checks = [
        {
            "id": "cycles",
            "ok": closed >= min_cycles,
            "label": f"Amostra ≥ {min_cycles} ciclos",
            "detail": f"{closed} ciclo(s) fechado(s)",
        },
        {
            "id": "hit_target",
            "ok": closed > 0 and hits == closed,
            "label": "Todos os ciclos bateram o alvo",
            "detail": f"{hits}/{closed} no alvo",
        },
        {
            "id": "no_loss",
            "ok": closed > 0 and losses == 0,
            "label": "Sem ciclo com prejuízo",
            "detail": f"{wins} win · {losses} loss",
        },
        {
            "id": "capital",
            "ok": capital_end >= capital_start and realized >= 0,
            "label": "Capital final ≥ aporte (lucro líquido)",
            "detail": f"retorno {capital_ret:+.2f}%",
        },
        {
            "id": "completion",
            "ok": buys > 0 and sells == buys and not (open_pos and float(open_pos.get("pnl") or 0) < 0),
            "label": "Compras concluídas com venda",
            "detail": f"{sells}/{buys} vendidas" + (" · posição aberta" if open_pos else ""),
        },
    ]
    failed = [c["label"] for c in checks if not c["ok"]]

    if pnl_validated and assertiveness >= 85:
        grade = "A"
        verdict = "aprovado"
        note = (
            f"Estratégia assertiva ({assertiveness:.0f}/100): lucro validado no histórico "
            f"com {closed} ciclos sem prejuízo."
        )
    elif recommend_create:
        grade = "B"
        verdict = "aprovado"
        note = (
            f"Qualidade boa ({assertiveness:.0f}/100): PnL e lucro ok no período. "
            f"Pode criar o bot com estes params."
        )
    elif assertiveness >= 50 and capital_end >= capital_start and closed > 0:
        grade = "C"
        verdict = "revisar"
        note = (
            f"Assertividade mediana ({assertiveness:.0f}/100). Lucro frágil ou amostra curta — "
            f"ajuste queda/alvo ou aumente o período."
        )
    else:
        grade = "D"
        verdict = "reprovado"
        why = "; ".join(failed[:3]) if failed else "pouca evidência de lucro"
        note = f"Assertividade baixa ({assertiveness:.0f}/100). Não recomenda criar bot ainda: {why}."

    return {
        "assertiveness": assertiveness,
        "grade": grade,
        "verdict": verdict,
        "profit_locked": profit_locked,
        "pnl_validated": pnl_validated,
        "recommend_create": recommend_create,
        "min_cycles": min_cycles,
        "hit_rate_pct": round(hit_rate, 2),
        "win_rate_pct": round(win_rate, 2),
        "components": {
            "hit_score": round(hit_score, 1),
            "profit_score": round(profit_score, 1),
            "sample_score": round(sample_score, 1),
            "completion_score": round(completion_score, 1),
        },
        "checks": checks,
        "note": note,
    }


def bar_for_days(days: int) -> str:
    if days <= 7:
        return "1H"
    if days <= 30:
        return "1H"
    if days <= 90:
        return "4H"
    return "1D"


def _ideal_cycle(quote_amt: float, buy_pct: float, target_pct: float, fee: float) -> dict[str, Any]:
    ref = 100.0
    buy_px = ref * (1.0 - buy_pct / 100.0)
    gross_qty = quote_amt / buy_px
    net_qty = gross_qty * (1.0 - fee)
    cost = quote_amt
    snap = estimate_net_pnl(buy_px, net_qty, cost, fee, target_pct)
    sell_px = snap.target_price
    proceeds = net_qty * sell_px * (1.0 - fee)
    pnl = proceeds - cost
    pnl_pct = (pnl / cost) * 100.0 if cost else 0.0
    return {
        "expected_pnl": pnl,
        "expected_pnl_pct": pnl_pct,
        "fee_rate_pct": fee * 100.0,
        "quote_amount": quote_amt,
        "note": f"1 ciclo ideal: compra na queda {buy_pct:g}% e vende com PnL líquido ≥ {target_pct:g}%.",
    }



def rank_strategies_on_candles(
    catalog: list[dict[str, Any]],
    candles: list[dict[str, Any]],
    *,
    inst_id: str,
    aporte_quote: float,
    days: int,
    aporte_input: float | None = None,
    aporte_ccy: str = "USDT",
    sort: str = "profit",
) -> list[dict[str, Any]]:
    """Simula cada estratégia no mesmo histórico e ordena (melhor primeiro)."""
    from . import strategies as strat_catalog

    inst = str(inst_id or "").strip().upper()
    aporte = float(aporte_quote)
    ranked: list[dict[str, Any]] = []
    for strat in catalog:
        cfg = BotConfig(
            bot_id="strategy",
            name=strat["name"],
            inst_id=inst,
            buy_pct=float(strat["buy_pct"]),
            profit_target_pct=float(strat["profit_target_pct"]),
            fee_rate_pct=float(strat["fee_rate_pct"]),
            quote_amount=aporte,
        )
        sim = simulate(cfg, candles, fee_rate=cfg.fee_rate, quote_amount=aporte, days=days)
        summary = sim.get("summary") or {}
        quality = summary.get("quality") or {}
        ranked.append(
            {
                "strategy": strat,
                "inst_id": inst,
                "params": {
                    "inst_id": inst,
                    "buy_pct": strat["buy_pct"],
                    "profit_target_pct": strat["profit_target_pct"],
                    "fee_rate_pct": strat["fee_rate_pct"],
                    "aporte": float(aporte_input if aporte_input is not None else aporte),
                    "aporte_ccy": aporte_ccy,
                    "days": days,
                },
                "summary": {
                    "cycles_closed": summary.get("cycles_closed"),
                    "capital_return_pct": summary.get("capital_return_pct"),
                    "capital_end": summary.get("capital_end"),
                    "capital_start": summary.get("capital_start"),
                    "realized_pnl": summary.get("realized_pnl"),
                    "total_pnl": summary.get("total_pnl"),
                    "wins": summary.get("wins"),
                    "losses": summary.get("losses"),
                    "assertiveness": quality.get("assertiveness"),
                    "grade": quality.get("grade"),
                    "verdict": quality.get("verdict"),
                    "pnl_validated": quality.get("pnl_validated"),
                    "profit_locked": quality.get("profit_locked"),
                    "recommend_create": quality.get("recommend_create"),
                    "note": quality.get("note") or summary.get("validation_note"),
                },
            }
        )
    ranked.sort(key=lambda r: strat_catalog.rank_key(r, sort), reverse=True)
    return ranked


def simulate(
    cfg: BotConfig,
    candles: list[dict[str, Any]],
    *,
    fee_rate: float | None = None,
    quote_amount: float | None = None,
    days: int | None = None,
) -> dict[str, Any]:
    fee = float(fee_rate if fee_rate is not None else cfg.fee_rate)
    base, quote = parse_inst(cfg.inst_id)
    quote_amt = float(quote_amount if quote_amount is not None else cfg.quote_amount)
    buy_pct = float(cfg.buy_pct)
    target_pct = float(cfg.profit_target_pct)
    ideal = _ideal_cycle(quote_amt, buy_pct, target_pct, fee)

    # caixa: começa com o aporte e recicla após cada venda (1 posição por vez)
    cash = float(quote_amt)
    start_cash = cash
    buy_size = float(quote_amt)

    state = "flat"
    ref: float | None = None
    qty = 0.0
    cost = 0.0
    entry = 0.0
    buy_ts: str | None = None
    buy_ref: float | None = None
    trades: list[dict[str, Any]] = []
    cycles: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    equity_points: list[dict[str, Any]] = []

    spent = 0.0
    received = 0.0
    realized = 0.0
    fees_paid = 0.0
    buys = 0
    sells = 0
    skips_buy = 0
    skips_sell = 0
    win = 0
    loss = 0

    rows = sorted(candles or [], key=lambda c: int(c.get("ts") or 0))

    def push_tl(**kwargs: Any) -> None:
        timeline.append(kwargs)

    if not rows:
        return {
            "ok": True,
            "persisted": False,
            "bot_id": cfg.bot_id,
            "name": cfg.name,
            "inst_id": cfg.inst_id,
            "candles": 0,
            "trades": [],
            "cycles": [],
            "timeline": [],
            "flow": [],
            "ideal_cycle": ideal,
            "summary": {
                "buys": 0,
                "sells": 0,
                "skips_buy": 0,
                "skips_sell": 0,
                "cycles_closed": 0,
                "wins": 0,
                "losses": 0,
                "win_rate_pct": 0.0,
                "avg_pnl_per_cycle": 0.0,
                "realized_pnl": 0.0,
                "unrealized_pnl": 0.0,
                "total_pnl": 0.0,
                "fees_paid": 0.0,
                "spent": 0.0,
                "received": 0.0,
                "open_state": "flat",
                "return_on_spent_pct": 0.0,
                "validated": False,
                "validation_note": "Sem candles para simular.",
                "quality": score_quality(
                    cycles=[],
                    buys=0,
                    sells=0,
                    realized=0.0,
                    capital_start=quote_amt,
                    capital_end=quote_amt,
                    capital_ret=0.0,
                    target_pct=target_pct,
                    ideal_pnl_pct=float(ideal.get("expected_pnl_pct") or 0),
                    open_pos=None,
                    days=days,
                ),
            },
            "equity": [],
        }

    for c in rows:
        ts = int(c.get("ts") or 0)
        ts_iso = _ts_iso(ts)
        high = float(c.get("high") or c.get("close") or 0)
        low = float(c.get("low") or c.get("close") or 0)
        close = float(c.get("close") or 0)
        if close <= 0:
            continue

        if state == "flat":
            if ref is None:
                ref = float(c.get("open") or close)
                push_tl(
                    ts=ts_iso,
                    action="set_ref",
                    executed=False,
                    price=ref,
                    reason=f"Referência definida em {ref:g} — ainda não compra",
                    drop_pct=0.0,
                    buy_trigger=ref * (1.0 - buy_pct / 100.0),
                    pnl_pct=None,
                    target_price=None,
                )
            else:
                trigger = ref * (1.0 - buy_pct / 100.0)
                drop_vs_ref = ((ref - low) / ref) * 100.0 if ref else 0.0
                drop_close = ((ref - close) / ref) * 100.0 if ref else 0.0
                if low <= trigger:
                    size = cash
                    if size < max(1.0, buy_size * 0.01):
                        skips_buy += 1
                        reason = (
                            f"NÃO comprou: caixa insuficiente ({size:.4f} {quote}) "
                            f"apesar da queda {drop_vs_ref:.2f}% ≥ {buy_pct:g}%"
                        )
                        push_tl(
                            ts=ts_iso,
                            action="skip_buy",
                            executed=False,
                            price=close,
                            reason=reason,
                            drop_pct=drop_vs_ref,
                            buy_trigger=trigger,
                            pnl_pct=None,
                            target_price=None,
                        )
                        continue
                    buy_px = trigger
                    gross_qty = size / buy_px
                    net_qty = gross_qty * (1.0 - fee)
                    fee_buy = size * fee
                    cost = size
                    qty = net_qty
                    entry = buy_px
                    buy_ts = ts_iso
                    buy_ref = ref
                    state = "long"
                    cash = 0.0
                    spent += size
                    fees_paid += fee_buy
                    buys += 1
                    reason = (
                        f"COMPRA efetivada: {size:g} {quote} · queda {drop_vs_ref:.2f}% ≥ {buy_pct:g}% "
                        f"(ref {ref:g} → gatilho {trigger:g})"
                    )
                    trades.append(
                        {
                            "ts": buy_ts,
                            "side": "buy",
                            "price": buy_px,
                            "qty": net_qty,
                            "quote": size,
                            "fee_est": fee_buy,
                            "pnl": None,
                            "pnl_pct": None,
                            "ref": ref,
                            "reason": reason,
                        }
                    )
                    push_tl(
                        ts=ts_iso,
                        action="buy",
                        executed=True,
                        price=buy_px,
                        reason=reason,
                        drop_pct=drop_vs_ref,
                        buy_trigger=trigger,
                        pnl_pct=None,
                        target_price=None,
                    )
                else:
                    skips_buy += 1
                    reason = (
                        f"NÃO comprou: queda máx. {drop_vs_ref:.2f}% < alvo {buy_pct:g}% "
                        f"(low {low:g} · gatilho {trigger:g} · close {close:g} · queda close {drop_close:.2f}%)"
                    )
                    push_tl(
                        ts=ts_iso,
                        action="skip_buy",
                        executed=False,
                        price=close,
                        reason=reason,
                        drop_pct=drop_vs_ref,
                        buy_trigger=trigger,
                        pnl_pct=None,
                        target_price=None,
                    )
        else:
            snap_high = estimate_net_pnl(high, qty, cost, fee, target_pct)
            snap_close = estimate_net_pnl(close, qty, cost, fee, target_pct)
            target = float(snap_high.target_price or 0)
            if high >= target and target > 0:
                sell_px = target
                fee_sell = qty * sell_px * fee
                proceeds = qty * sell_px * (1.0 - fee)
                pnl = proceeds - cost
                pnl_pct = (pnl / cost) * 100.0 if cost else 0.0
                received += proceeds
                realized += pnl
                fees_paid += fee_sell
                cash = proceeds
                sells += 1
                if pnl >= 0:
                    win += 1
                else:
                    loss += 1
                sell_ts = ts_iso
                reason = (
                    f"VENDA efetivada: PnL líquido {pnl_pct:.2f}% ≥ alvo {target_pct:g}% "
                    f"(preço {sell_px:g})"
                )
                trades.append(
                    {
                        "ts": sell_ts,
                        "side": "sell",
                        "price": sell_px,
                        "qty": qty,
                        "quote": proceeds,
                        "fee_est": fee_sell,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "ref": buy_ref,
                        "reason": reason,
                    }
                )
                cycles.append(
                    {
                        "n": len(cycles) + 1,
                        "buy_ts": buy_ts,
                        "sell_ts": sell_ts,
                        "ref": buy_ref,
                        "buy_price": entry,
                        "sell_price": sell_px,
                        "qty": qty,
                        "spent": cost,
                        "received": proceeds,
                        "fees": (cost * fee) + fee_sell,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "hit_target": pnl_pct + 1e-9 >= target_pct,
                        "ok": pnl >= 0,
                    }
                )
                push_tl(
                    ts=ts_iso,
                    action="sell",
                    executed=True,
                    price=sell_px,
                    reason=reason,
                    drop_pct=None,
                    buy_trigger=None,
                    pnl_pct=pnl_pct,
                    target_price=target,
                )
                state = "flat"
                ref = sell_px
                qty = 0.0
                cost = 0.0
                entry = 0.0
                buy_ts = None
                buy_ref = None
            else:
                skips_sell += 1
                reason = (
                    f"NÃO vendeu: PnL líquido {snap_close.pnl_pct:.2f}% < alvo {target_pct:g}% "
                    f"(close {close:g} · high {high:g} · precisa ≥ {target:g})"
                )
                push_tl(
                    ts=ts_iso,
                    action="skip_sell",
                    executed=False,
                    price=close,
                    reason=reason,
                    drop_pct=None,
                    buy_trigger=None,
                    pnl_pct=snap_close.pnl_pct,
                    target_price=target,
                )

        mtm = 0.0
        if state == "long" and qty and cost:
            mtm = estimate_net_pnl(close, qty, cost, fee, target_pct).pnl
        equity_points.append(
            {
                "ts": ts_iso,
                "close": close,
                "realized": realized,
                "unrealized": mtm,
                "equity": realized + mtm,
                "state": state,
            }
        )

    last = rows[-1]
    last_close = float(last.get("close") or 0)
    unreal = 0.0
    open_pos = None
    if state == "long" and qty and cost and last_close:
        snap = estimate_net_pnl(last_close, qty, cost, fee, target_pct)
        unreal = snap.pnl
        open_pos = {
            "qty": qty,
            "entry": entry,
            "cost": cost,
            "last": last_close,
            "pnl": unreal,
            "pnl_pct": snap.pnl_pct,
            "target_price": snap.target_price,
            "buy_ts": buy_ts,
            "ref": buy_ref,
        }

    end_cash = cash
    if state == "long" and qty and cost and last_close:
        # marca posição aberta a mercado (líquido de taxa)
        end_cash = qty * last_close * (1.0 - fee)
    capital_pnl = end_cash - start_cash
    capital_ret = (capital_pnl / start_cash * 100.0) if start_cash else 0.0

    closed = len(cycles)
    avg_pnl = (realized / closed) if closed else 0.0
    hits = sum(1 for c in cycles if c.get("hit_target"))
    quality = score_quality(
        cycles=cycles,
        buys=buys,
        sells=sells,
        realized=realized,
        capital_start=start_cash,
        capital_end=end_cash,
        capital_ret=capital_ret,
        target_pct=target_pct,
        ideal_pnl_pct=float(ideal.get("expected_pnl_pct") or 0),
        open_pos=open_pos,
        days=days,
    )
    validated = bool(quality.get("pnl_validated"))
    if closed == 0 and buys == 0:
        note = (
            f"Nenhuma compra em {len(rows)} candles: o preço não caiu ≥ {buy_pct:g}% vs referência. "
            f"Veja a coluna Motivo (NÃO comprou)."
        )
    elif closed == 0 and buys > 0:
        note = (
            f"Comprou {buys}x, mas não vendeu: PnL líquido não atingiu {target_pct:g}%. "
            f"Veja Motivo (NÃO vendeu)."
        )
    else:
        note = str(quality.get("note") or "")

    flow = [
        {"step": 1, "title": "Ref", "detail": "Define preço-base e espera queda."},
        {"step": 2, "title": "Compra", "detail": f"All-in do caixa (≥ queda {buy_pct:g}%). Aporte inicial {start_cash:g} {quote}."},
        {"step": 3, "title": "Venda", "detail": f"Só com PnL líquido ≥ {target_pct:g}% (taxas inclusas)."},
        {"step": 4, "title": "PnL", "detail": f"Recicla o caixa. Ciclo ideal ≈ {ideal['expected_pnl_pct']:.2f}%."},
    ]

    first_ts = int(rows[0].get("ts") or 0)
    last_ts = int(rows[-1].get("ts") or 0)
    return {
        "ok": True,
        "persisted": False,
        "bot_id": cfg.bot_id,
        "name": cfg.name,
        "inst_id": cfg.inst_id,
        "base": base,
        "quote": quote,
        "buy_pct": buy_pct,
        "profit_target_pct": target_pct,
        "quote_amount": quote_amt,
        "aporte": start_cash,
        "fee_rate_pct": fee * 100.0,
        "candles": len(rows),
        "from": _ts_iso(first_ts) if first_ts else None,
        "to": _ts_iso(last_ts) if last_ts else None,
        "trades": trades,
        "cycles": cycles,
        "timeline": timeline,
        "flow": flow,
        "ideal_cycle": ideal,
        "open_position": open_pos,
        "equity": equity_points[:: max(1, len(equity_points) // 120)] if equity_points else [],
        "summary": {
            "buys": buys,
            "sells": sells,
            "skips_buy": skips_buy,
            "skips_sell": skips_sell,
            "cycles_closed": closed,
            "wins": win,
            "losses": loss,
            "win_rate_pct": (win / closed * 100.0) if closed else 0.0,
            "avg_pnl_per_cycle": avg_pnl,
            "target_hits": hits,
            "realized_pnl": realized,
            "unrealized_pnl": unreal,
            "total_pnl": realized + unreal,
            "fees_paid": fees_paid,
            "spent": spent,
            "received": received,
            "open_state": state,
            "aporte": start_cash,
            "capital_start": start_cash,
            "capital_end": end_cash,
            "capital_pnl": capital_pnl,
            "capital_return_pct": capital_ret,
            "return_on_spent_pct": (realized + unreal) / spent * 100.0 if spent else 0.0,
            "validated": validated,
            "validation_note": note,
            "quality": quality,
        },
    }
