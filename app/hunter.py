"""Radar de tokens em baixa + score de liquidez / rentabilidade (heurística)."""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Any

STABLES = {"USDT", "USDC", "BRL", "USD", "EUR", "TRY", "DAI", "BUSD", "TUSD", "FDUSD"}
BLUE_CHIPS = {"BTC", "ETH"}

# Token novo: volume menor é esperado — piso ~60k (não 100k+)
NEW_TOKEN_DAYS = 14.0
NEW_TOKEN_MIN_VOL = 60_000.0
VERY_NEW_DAYS = 3.0
VERY_NEW_MIN_VOL = 25_000.0


def _f(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def listing_age_days(list_time_ms: Any) -> float | None:
    """Idade do par Spot em dias a partir do listTime OKX (ms). None se desconhecido."""
    ms = _f(list_time_ms)
    if ms is None or ms <= 0:
        return None
    now_ms = time.time() * 1000.0
    if ms > now_ms:
        return 0.0  # pré-list / recém liberado
    return max(0.0, (now_ms - ms) / 86_400_000.0)


def listing_iso(list_time_ms: Any) -> str | None:
    ms = _f(list_time_ms)
    if ms is None or ms <= 0:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def effective_min_vol(min_vol: float, age_days: float | None) -> float:
    """
    Ajusta volume mínimo pela idade do token.
    Novo (<14d): aceita até ~60k; muito novo (<3d): até ~25k.
    """
    base = max(0.0, float(min_vol or 0))
    if age_days is None:
        return base
    age = float(age_days)
    if age <= VERY_NEW_DAYS:
        return min(base, VERY_NEW_MIN_VOL)
    if age <= NEW_TOKEN_DAYS:
        # interpola 25k → 60k → min_vol conforme envelhece
        t = (age - VERY_NEW_DAYS) / max(NEW_TOKEN_DAYS - VERY_NEW_DAYS, 1e-9)
        soft = NEW_TOKEN_MIN_VOL + t * max(0.0, base - NEW_TOKEN_MIN_VOL)
        return min(base, max(VERY_NEW_MIN_VOL, soft))
    return base


def is_new_listing(age_days: float | None, *, days: float = NEW_TOKEN_DAYS) -> bool:
    return age_days is not None and float(age_days) <= float(days)


def spread_pct(bid: float | None, ask: float | None, last: float | None = None) -> float | None:
    b, a = _f(bid), _f(ask)
    if not b or not a or b <= 0 or a <= 0 or a < b:
        return None
    mid = (a + b) / 2.0
    if mid <= 0:
        mid = _f(last) or 0
    if mid <= 0:
        return None
    return ((a - b) / mid) * 100.0


def liquidity_label(vol: float, spread: float | None, book_usd: float | None = None) -> str:
    """A=ótima · B=boa · C=aceitável · D=fraca."""
    points = 0
    if vol >= 20_000_000:
        points += 3
    elif vol >= 5_000_000:
        points += 2
    elif vol >= 1_000_000:
        points += 1
    if spread is not None:
        if spread <= 0.08:
            points += 3
        elif spread <= 0.25:
            points += 2
        elif spread <= 0.6:
            points += 1
    if book_usd is not None:
        if book_usd >= 50_000:
            points += 2
        elif book_usd >= 15_000:
            points += 1
    if points >= 7:
        return "A"
    if points >= 5:
        return "B"
    if points >= 3:
        return "C"
    return "D"


_LIQ_MEANING = {
    "A": "Ótima — volume alto, spread apertado e livro profundo",
    "B": "Boa — dá para operar com custo razoável",
    "C": "Aceitável — liquidez mediana; cuidado com o tamanho da ordem",
    "D": "Fraca — spread largo ou volume/livro baixos; risco de slippage",
}


def liquidity_tip(
    label: str,
    *,
    vol: float | None = None,
    spread: float | None = None,
    book_usd: float | None = None,
) -> str:
    base = _LIQ_MEANING.get(str(label or "D").upper(), _LIQ_MEANING["D"])
    bits = [f"Liquidez {label}: {base}"]
    if vol is not None:
        bits.append(f"vol 24h ≈ ${float(vol):,.0f}")
    if spread is not None:
        bits.append(f"spread {float(spread):.2f}%")
    if book_usd is not None:
        bits.append(f"livro ≈ ${float(book_usd):,.0f}")
    bits.append("Nota = volume + spread + profundidade do livro Spot")
    return " · ".join(bits)


def rentability_check(
    *,
    profit_target_pct: float,
    fee_rate_pct: float,
    spread_pct_val: float | None,
    order_usd: float,
    vol_24h: float,
    book_usd: float | None = None,
) -> dict[str, Any]:
    """
    Viabilidade grosseira do ciclo compra→venda:
    - taxa ida+volta + spread consome quanto do alvo
    - ordem cabe no volume/livro
    """
    issues: list[str] = []
    fee_rt = float(fee_rate_pct or 0) * 2  # compra + venda
    spr = float(spread_pct_val or 0)
    cost_pct = fee_rt + spr
    target = float(profit_target_pct or 0)
    net_edge = target - cost_pct
    # Viável = o alvo ainda cobre taxa ida+volta + spread (não exige “folga de 25%”).
    edge_ok = net_edge >= 0.0 if target > 0 else True
    if not edge_ok:
        issues.append(
            f"alvo {target:.2f}% não cobre o custo ≈ {cost_pct:.2f}% (taxa {fee_rt:.2f}% + spread {spr:.2f}%)"
        )

    vol = float(vol_24h or 0)
    vol_share = (order_usd / vol * 100.0) if vol > 0 and order_usd > 0 else 0.0
    vol_ok = vol_share <= 2.0 if order_usd > 0 and vol > 0 else True
    if order_usd > 0 and vol > 0 and not vol_ok:
        issues.append(f"ordem ${order_usd:.0f} = {vol_share:.2f}% do vol 24h (alto impacto)")

    book_ok = True
    # livro 0 / ausente = não medido — não zera a lista inteira
    if book_usd is not None and float(book_usd) > 0 and order_usd > 0:
        book_ok = float(book_usd) >= order_usd
        if not book_ok:
            issues.append(f"livro ≈ ${float(book_usd):,.0f} fino vs ordem ${order_usd:.0f}")

    tradeable = edge_ok and vol_ok and book_ok

    return {
        "tradeable": tradeable,
        "cost_pct": round(cost_pct, 3),
        "net_edge_pct": round(net_edge, 3),
        "vol_share_pct": round(vol_share, 3),
        "issues": issues,
    }


def score_candidate(
    *,
    chg24: float | None,
    vol: float | None,
    min_drop_pct: float,
    max_drop_pct: float,
    min_vol: float,
    base: str = "",
    bid: float | None = None,
    ask: float | None = None,
    last: float | None = None,
    max_spread_pct: float = 0.8,
    profit_target_pct: float = 3.0,
    fee_rate_pct: float = 0.10,
    order_usd: float = 50.0,
    book_usd: float | None = None,
    age_days: float | None = None,
) -> dict[str, Any]:
    """Score 0–100 + liquidez + viabilidade de rentabilidade."""
    reasons: list[str] = []
    chg = float(chg24) if chg24 is not None else 0.0
    volume = float(vol or 0)
    drop = -chg
    spr = spread_pct(bid, ask, last)
    vol_need = effective_min_vol(min_vol, age_days)
    newish = is_new_listing(age_days)

    empty = {
        "score": 0.0,
        "prob_up_pct": 0.0,
        "reasons": [],
        "eligible": False,
        "spread_pct": spr,
        "liquidity": "D",
        "tradeable": False,
        "rentability": None,
        "vol_min_effective": vol_need,
        "is_new": newish,
        "age_days": round(age_days, 2) if age_days is not None else None,
    }

    if chg >= 0:
        return {**empty, "reasons": ["sem queda 24h"]}
    if drop < min_drop_pct:
        return {**empty, "reasons": [f"queda {drop:.1f}% < mínimo {min_drop_pct:g}%"]}
    if drop > max_drop_pct:
        return {**empty, "reasons": [f"queda {drop:.1f}% > máximo {max_drop_pct:g}% (risco alto)"]}
    if volume < vol_need:
        age_bit = (
            f" (token ~{age_days:.0f}d · mín. ajustado ${vol_need:,.0f})"
            if age_days is not None
            else ""
        )
        return {
            **empty,
            "reasons": [f"volume ${volume:,.0f} < mínimo ${vol_need:,.0f}{age_bit}"],
        }
    if spr is not None and spr > max_spread_pct:
        return {
            **empty,
            "spread_pct": spr,
            "reasons": [f"spread {spr:.2f}% > máx {max_spread_pct:g}% (liquidez ruim)"],
        }

    mid = (min_drop_pct + max_drop_pct) / 2.0
    span = max(max_drop_pct - min_drop_pct, 1.0)
    dip_fit = 1.0 - abs(drop - mid) / span
    dip_score = 28.0 + 22.0 * max(0.0, dip_fit)
    reasons.append(f"queda 24h {drop:.1f}%")
    if newish and age_days is not None:
        reasons.append(f"listagem nova (~{age_days:.1f}d) · vol mín. ${vol_need:,.0f}")

    if volume >= 50_000_000:
        vol_score = 28.0
        reasons.append("volume muito alto")
    elif volume >= 10_000_000:
        vol_score = 24.0
        reasons.append("volume alto")
    elif volume >= 2_000_000:
        vol_score = 20.0
        reasons.append("volume bom")
    elif volume >= 500_000:
        vol_score = 14.0
        reasons.append("volume ok")
    else:
        vol_score = 8.0
        reasons.append("volume baixo")

    # Spread / livro
    spr_score = 12.0
    if spr is None:
        spr_score = 6.0
        reasons.append("sem bid/ask")
    elif spr <= 0.08:
        spr_score = 16.0
        reasons.append(f"spread apertado {spr:.2f}%")
    elif spr <= 0.25:
        spr_score = 13.0
        reasons.append(f"spread bom {spr:.2f}%")
    elif spr <= 0.6:
        spr_score = 9.0
        reasons.append(f"spread ok {spr:.2f}%")
    else:
        spr_score = 4.0
        reasons.append(f"spread largo {spr:.2f}%")

    book_score = 0.0
    if book_usd is not None:
        if book_usd >= 50_000:
            book_score = 8.0
            reasons.append(f"livro ${book_usd:,.0f}")
        elif book_usd >= 15_000:
            book_score = 5.0
            reasons.append(f"livro ${book_usd:,.0f}")
        elif book_usd >= 5_000:
            book_score = 2.0
            reasons.append(f"livro fino ${book_usd:,.0f}")
        else:
            book_score = -4.0
            reasons.append(f"livro muito fino ${book_usd:,.0f}")

    base_u = (base or "").upper()
    base_score = 8.0
    if base_u in BLUE_CHIPS:
        base_score = 6.0
        reasons.append("blue chip")
    elif base_u in STABLES:
        return {**empty, "reasons": ["stablecoin"]}
    else:
        reasons.append("altcoin")

    depth_pen = 0.0
    if drop > mid:
        depth_pen = 8.0 * ((drop - mid) / (max_drop_pct - mid + 1e-9))
        if depth_pen > 2:
            reasons.append("dip profundo — cautela")

    rent = rentability_check(
        profit_target_pct=profit_target_pct,
        fee_rate_pct=fee_rate_pct,
        spread_pct_val=spr,
        order_usd=order_usd,
        vol_24h=volume,
        book_usd=book_usd,
    )
    rent_score = 10.0 if rent["tradeable"] else -6.0
    if rent["tradeable"]:
        reasons.append(f"edge líquido ≈ {rent['net_edge_pct']:.2f}%")
    else:
        reasons.extend(rent["issues"][:1])

    liq = liquidity_label(volume, spr, book_usd)
    raw = dip_score + vol_score + spr_score + book_score + base_score + rent_score - depth_pen
    score = max(0.0, min(100.0, raw))
    # Prob. ilustrativa — baixa se não tradeable
    prob = 30.0 + (score / 100.0) * 40.0
    if not rent["tradeable"]:
        prob = min(prob, 42.0)
        score = min(score, 55.0)

    return {
        "score": round(score, 1),
        "prob_up_pct": round(prob, 1),
        "reasons": reasons,
        "eligible": True,
        "spread_pct": round(spr, 3) if spr is not None else None,
        "liquidity": liq,
        "liquidity_tip": liquidity_tip(liq, vol=volume, spread=spr, book_usd=book_usd),
        "tradeable": bool(rent["tradeable"]),
        "rentability": rent,
        "vol_min_effective": vol_need,
        "is_new": newish,
        "age_days": round(age_days, 2) if age_days is not None else None,
    }


def scan_dips(
    pairs: list[dict[str, Any]],
    *,
    min_drop_pct: float = 5.0,
    max_drop_pct: float = 28.0,
    min_vol: float = 500_000.0,
    max_spread_pct: float = 0.8,
    profit_target_pct: float = 3.0,
    fee_rate_pct: float = 0.10,
    order_usd: float = 50.0,
    blacklist: list[str] | None = None,
    exclude_inst: set[str] | None = None,
    top_n: int = 25,
    require_tradeable: bool = False,
) -> list[dict[str, Any]]:
    blocked = {str(x).upper() for x in (blacklist or [])}
    exclude = {str(x).upper() for x in (exclude_inst or set())}
    out: list[dict[str, Any]] = []
    for p in pairs or []:
        inst = str(p.get("inst_id") or "").upper()
        base = str(p.get("base") or "").upper()
        if not inst or base in STABLES:
            continue
        if inst in blocked or base in blocked or inst in exclude:
            continue
        age_days = p.get("age_days")
        if age_days is None and p.get("list_time"):
            age_days = listing_age_days(p.get("list_time"))
        scored = score_candidate(
            chg24=p.get("chg24"),
            vol=p.get("vol"),
            min_drop_pct=min_drop_pct,
            max_drop_pct=max_drop_pct,
            min_vol=min_vol,
            base=base,
            bid=p.get("bid"),
            ask=p.get("ask"),
            last=p.get("last"),
            max_spread_pct=max_spread_pct,
            profit_target_pct=profit_target_pct,
            fee_rate_pct=fee_rate_pct,
            order_usd=order_usd,
            book_usd=p.get("book_usd"),
            age_days=age_days,
        )
        if not scored.get("eligible"):
            continue
        if require_tradeable and not scored.get("tradeable"):
            continue
        drop = -float(p.get("chg24") or 0)
        out.append(
            {
                "inst_id": inst,
                "base": base,
                "quote": str(p.get("quote") or "").upper(),
                "icon": p.get("icon"),
                "icon_alt": p.get("icon_alt"),
                "last": p.get("last"),
                "bid": p.get("bid"),
                "ask": p.get("ask"),
                "chg24": p.get("chg24"),
                "drop_pct": round(drop, 2),
                "vol": p.get("vol"),
                "spread_pct": scored.get("spread_pct"),
                "liquidity": scored.get("liquidity"),
                "liquidity_tip": scored.get("liquidity_tip"),
                "tradeable": scored.get("tradeable"),
                "rentability": scored.get("rentability"),
                "book_usd": p.get("book_usd"),
                "score": scored["score"],
                "prob_up_pct": scored["prob_up_pct"],
                "reasons": scored["reasons"],
                "list_time": p.get("list_time"),
                "listed_at": p.get("listed_at") or listing_iso(p.get("list_time")),
                "age_days": scored.get("age_days"),
                "is_new": scored.get("is_new"),
                "vol_min_effective": scored.get("vol_min_effective"),
            }
        )
    out.sort(
        key=lambda x: (
            -int(bool(x.get("tradeable"))),
            -float(x.get("score") or 0),
            -float(x.get("drop_pct") or 0),
        )
    )
    return out[: max(1, min(int(top_n), 100))]


# ── Horizontes de venda + análise / previsão leve ──────────────────────────

HORIZONS: dict[str, dict[str, Any]] = {
    "daily": {
        "label": "Diário (scalp)",
        "hint": "Oscilações curtas · muitos ciclos · dips leves",
        "validate_days": 7,
        "min_drop_pct": 1.5,
        "max_drop_pct": 12.0,
        "min_vol_usd": 200_000.0,
        "max_spread_pct": 0.50,
        "cycles_weight": 1.45,
        "return_weight": 0.75,
        "near_low_bars": 24,  # ~1d em 1H
    },
    "weekly": {
        "label": "Semanal",
        "hint": "Mean-reversion em dias · equilíbrio ciclos × retorno",
        "validate_days": 30,
        "min_drop_pct": 3.0,
        "max_drop_pct": 20.0,
        "min_vol_usd": 100_000.0,
        "max_spread_pct": 0.80,
        "cycles_weight": 1.0,
        "return_weight": 1.0,
        "near_low_bars": 48,
    },
    "monthly": {
        "label": "Mensal (swing)",
        "hint": "Swings maiores · prioriza retorno e dips profundos",
        "validate_days": 90,
        "min_drop_pct": 5.0,
        "max_drop_pct": 35.0,
        "min_vol_usd": 80_000.0,
        "max_spread_pct": 1.0,
        "cycles_weight": 0.65,
        "return_weight": 1.35,
        "near_low_bars": 60,
    },
}


def normalize_horizon(raw: Any) -> str:
    h = str(raw or "weekly").strip().lower()
    return h if h in HORIZONS else "weekly"


def horizon_preset(horizon: str) -> dict[str, Any]:
    return dict(HORIZONS[normalize_horizon(horizon)])


def apply_horizon_to_settings(cfg: dict[str, Any], *, override_filters: bool = False) -> dict[str, Any]:
    """Aplica validate_days do horizonte; filtros só se override_filters=True."""
    out = dict(cfg or {})
    h = normalize_horizon(out.get("horizon"))
    out["horizon"] = h
    preset = HORIZONS[h]
    out["validate_days"] = int(preset["validate_days"])
    if override_filters:
        out["min_drop_pct"] = float(preset["min_drop_pct"])
        out["max_drop_pct"] = float(preset["max_drop_pct"])
        out["min_vol_usd"] = float(preset["min_vol_usd"])
        out["max_spread_pct"] = float(preset["max_spread_pct"])
    return out


def _std(xs: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean = sum(xs) / n
    return (sum((x - mean) ** 2 for x in xs) / (n - 1)) ** 0.5


def _sma(values: list[float], period: int) -> float | None:
    """Simple Moving Average dos últimos N valores."""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _calc_rsi(closes: list[float], period: int = 14) -> float | None:
    """RSI (Relative Strength Index) clássico."""
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(0, diff))
        losses.append(max(0, -diff))
    if len(gains) < period:
        return None
    # Média exponencial (Wilder's smoothing)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _find_support(lows: list[float], current_price: float) -> float | None:
    """Encontra nível de suporte: cluster de mínimas próximas abaixo do preço."""
    if len(lows) < 5:
        return None
    # Buscar mínimas abaixo do preço atual
    below = sorted([l for l in lows if l < current_price * 0.995])
    if not below:
        return min(lows) if lows else None
    # Cluster: agrupar mínimas dentro de 1% umas das outras
    clusters: list[list[float]] = []
    for val in below:
        placed = False
        for cluster in clusters:
            if abs(val - cluster[0]) / cluster[0] < 0.01:
                cluster.append(val)
                placed = True
                break
        if not placed:
            clusters.append([val])
    # Suporte mais forte = cluster com mais toques, mais próximo do preço
    if not clusters:
        return below[-1]
    clusters.sort(key=lambda c: (-len(c), -max(c)))
    return sum(clusters[0]) / len(clusters[0])


def _detect_higher_lows(lows: list[float]) -> bool:
    """Detecta se os últimos fundos locais são ascendentes (tendência de alta)."""
    if len(lows) < 20:
        return False
    # Encontrar fundos locais (mínimo de janela de 5)
    local_mins: list[float] = []
    for i in range(2, len(lows) - 2):
        if lows[i] <= lows[i-1] and lows[i] <= lows[i-2] and lows[i] <= lows[i+1] and lows[i] <= lows[i+2]:
            local_mins.append(lows[i])
    if len(local_mins) < 3:
        return False
    # Verificar se os últimos 3+ fundos são crescentes
    recent = local_mins[-4:]
    ascending = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])
    return ascending >= len(recent) - 1


def analyze_candles(candles: list[dict[str, Any]], *, horizon: str = "weekly") -> dict[str, Any]:
    """
    Features leves (sem ML): tendência, vol realizada, proximidade da mínima,
    taxa de bounce após dips — base para o score preditivo.
    """
    preset = horizon_preset(horizon)
    rows = sorted(
        [c for c in (candles or []) if (c.get("c") or c.get("close")) is not None],
        key=lambda c: int(c.get("ts") or 0),
    )
    if len(rows) < 12:
        return {"ok": False, "bars": len(rows)}

    closes = [float(c.get("c") or c.get("close")) for c in rows]
    highs = [float(c.get("h") or c.get("high") or c.get("c") or c.get("close")) for c in rows]
    lows = [float(c.get("l") or c.get("low") or c.get("c") or c.get("close")) for c in rows]
    last = closes[-1]
    first = closes[0]
    chg_period_pct = ((last / first) - 1.0) * 100.0 if first > 0 else 0.0

    rets = [(closes[i] / closes[i - 1] - 1.0) for i in range(1, len(closes)) if closes[i - 1] > 0]
    rv = _std(rets) * 100.0  # % por barra
    # Vol “moderada” boa p/ mean-reversion: nem morta nem explosiva
    if 0.15 <= rv <= 1.8:
        vol_fit = 1.0
    elif rv < 0.15:
        vol_fit = max(0.2, rv / 0.15)
    else:
        vol_fit = max(0.15, 1.8 / rv)

    look = min(int(preset.get("near_low_bars") or 48), len(lows))
    window_lows = lows[-look:]
    window_highs = highs[-look:]
    period_low = min(window_lows) if window_lows else last
    period_high = max(window_highs) if window_highs else last
    near_low_pct = ((last - period_low) / period_low * 100.0) if period_low > 0 else 99.0
    # 0% = na mínima → score 1; longe → 0
    near_low_score = max(0.0, min(1.0, 1.0 - near_low_pct / 8.0))

    # Bounce rate: após barra com queda ≥ 1%, as próximas 3 sobem vs o close do dip?
    dips = 0
    bounces = 0
    for i in range(1, len(closes) - 3):
        if closes[i - 1] <= 0:
            continue
        bar_chg = (closes[i] / closes[i - 1] - 1.0) * 100.0
        if bar_chg > -1.0:
            continue
        dips += 1
        if max(closes[i + 1 : i + 4]) >= closes[i] * 1.005:
            bounces += 1
    bounce_rate = (bounces / dips) if dips >= 3 else None

    range_pct = ((period_high - period_low) / period_low * 100.0) if period_low > 0 else 0.0

    # ── Indicadores técnicos avançados ──

    # RSI(14)
    rsi_14 = _calc_rsi(closes, 14)

    # Médias móveis (SMA)
    sma_20 = _sma(closes, 20)
    sma_50 = _sma(closes, 50)

    # Posição relativa às médias
    above_sma20 = (last > sma_20) if sma_20 else None
    above_sma50 = (last > sma_50) if sma_50 else None

    # Tendência: preço acima das médias = uptrend, dip é pullback (bom)
    trend_score = 0.0
    if above_sma20:
        trend_score += 0.4
    if above_sma50:
        trend_score += 0.6
    # Se SMA20 > SMA50 = golden cross zone
    if sma_20 and sma_50 and sma_20 > sma_50:
        trend_score += 0.2
    trend_score = min(1.0, trend_score)

    # ATH distance — usando todos os highs disponíveis
    ath = max(highs) if highs else last
    ath_distance_pct = ((ath - last) / ath * 100.0) if ath > 0 else 0.0
    # Score: mais perto do ATH = token forte; muito longe = pode ser morto
    # <20% do ATH = ótimo (0.9-1.0), 20-50% = ok, >80% = ruim
    if ath_distance_pct <= 10:
        ath_score = 1.0
    elif ath_distance_pct <= 30:
        ath_score = 0.7
    elif ath_distance_pct <= 50:
        ath_score = 0.5
    elif ath_distance_pct <= 70:
        ath_score = 0.3
    else:
        ath_score = 0.1

    # Volume trend: média volume últimas 5 barras vs média 20 barras
    vols = [float(c.get("vol") or 0) for c in rows if c.get("vol")]
    vol_trend = 1.0
    if len(vols) >= 20:
        vol_recent = sum(vols[-5:]) / 5.0
        vol_avg = sum(vols[-20:]) / 20.0
        vol_trend = (vol_recent / vol_avg) if vol_avg > 0 else 1.0
    # Volume crescendo no dip = capitulação (bom sinal de fundo)
    vol_trend_score = min(1.0, max(0.0, (vol_trend - 0.5) / 1.5))

    # Suporte: detectar cluster de lows (preços mínimos próximos)
    support_level = _find_support(lows[-look:], last)

    # Higher lows (fundos ascendentes) — últimos 4 fundos locais
    higher_lows = _detect_higher_lows(lows)

    # RSI score: <30 = sobrevendido (ótimo para compra), 30-50 = bom, >70 = sobrecomprado
    rsi_score = 0.5
    if rsi_14 is not None:
        if rsi_14 <= 25:
            rsi_score = 1.0
        elif rsi_14 <= 35:
            rsi_score = 0.85
        elif rsi_14 <= 50:
            rsi_score = 0.6
        elif rsi_14 <= 70:
            rsi_score = 0.35
        else:
            rsi_score = 0.1

    return {
        "ok": True,
        "bars": len(rows),
        "chg_period_pct": round(chg_period_pct, 2),
        "realized_vol_bar_pct": round(rv, 3),
        "vol_fit": round(vol_fit, 3),
        "near_low_pct": round(near_low_pct, 2),
        "near_low_score": round(near_low_score, 3),
        "bounce_rate": round(bounce_rate, 3) if bounce_rate is not None else None,
        "bounce_sample": dips,
        "range_pct": round(range_pct, 2),
        "period_low": period_low,
        "period_high": period_high,
        # Novos indicadores
        "rsi_14": round(rsi_14, 1) if rsi_14 is not None else None,
        "rsi_score": round(rsi_score, 3),
        "sma_20": round(sma_20, 6) if sma_20 else None,
        "sma_50": round(sma_50, 6) if sma_50 else None,
        "above_sma20": above_sma20,
        "above_sma50": above_sma50,
        "trend_score": round(trend_score, 3),
        "ath": ath,
        "ath_distance_pct": round(ath_distance_pct, 2),
        "ath_score": round(ath_score, 3),
        "vol_trend": round(vol_trend, 3),
        "vol_trend_score": round(vol_trend_score, 3),
        "support_level": round(support_level, 6) if support_level else None,
        "higher_lows": higher_lows,
    }


def _sigmoid(x: float) -> float:
    if x < -20:
        return 0.0
    if x > 20:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def predict_sell_fitness(
    *,
    horizon: str,
    spot_score: float,
    tradeable: bool,
    features: dict[str, Any] | None,
    best_strategy: dict[str, Any] | None,
    validate_days: int,
) -> dict[str, Any]:
    """
    Score preditivo heurístico (não ML): aptidão a vendas no horizonte.
    Combina liquidez Spot + features de candle + backtest da melhor estratégia.
    """
    preset = horizon_preset(horizon)
    days = max(1, int(validate_days or preset["validate_days"]))
    feat = features if features and features.get("ok") else {}
    bs = best_strategy or {}

    cycles = float(bs.get("cycles_closed") or 0)
    cycles_per_day = cycles / days
    ret = float(bs.get("capital_return_pct") or 0)
    assertiveness = float(bs.get("assertiveness") or 0) / 100.0
    recommend = 1.0 if bs.get("recommend_create") else 0.35

    # Normalizações 0–1
    spot_n = max(0.0, min(1.0, float(spot_score or 0) / 100.0))
    # daily quer ~≥0.5 ciclo/dia; weekly ~0.15; monthly ~0.05
    target_cpd = {"daily": 0.55, "weekly": 0.18, "monthly": 0.06}.get(
        normalize_horizon(horizon), 0.18
    )
    cyc_n = max(0.0, min(1.0, cycles_per_day / max(target_cpd, 1e-6)))
    ret_n = max(0.0, min(1.0, (ret + 5.0) / 25.0))  # -5%→0 · +20%→1
    near = float(feat.get("near_low_score") or 0.4)
    vol_fit = float(feat.get("vol_fit") or 0.5)
    bounce = feat.get("bounce_rate")
    bounce_n = float(bounce) if bounce is not None else 0.45

    cw = float(preset["cycles_weight"])
    rw = float(preset["return_weight"])
    # Novos indicadores do analyze_candles
    trend_n = float(feat.get("trend_score") or 0.3)
    rsi_n = float(feat.get("rsi_score") or 0.5)
    ath_n = float(feat.get("ath_score") or 0.3)
    vol_trend_n = float(feat.get("vol_trend_score") or 0.5)
    higher_lows_n = 1.0 if feat.get("higher_lows") else 0.3

    w_sum = 0.16 + 0.12 + 0.12 * cw + 0.12 * rw + 0.10 + 0.08 + 0.06 + 0.08 + 0.06 + 0.05 + 0.05
    z = (
        0.16 * spot_n          # Score base do spot (liquidez/spread/vol)
        + 0.12 * assertiveness  # Assertividade do backtest
        + 0.12 * cw * cyc_n    # Ciclos por dia
        + 0.12 * rw * ret_n    # Retorno de capital
        + 0.10 * near           # Proximidade da mínima
        + 0.08 * bounce_n       # Taxa de bounce
        + 0.06 * vol_fit        # Fitness de volatilidade
        + 0.08 * trend_n        # Tendência (MAs, higher lows)
        + 0.06 * rsi_n          # RSI (sobrevendido = bom)
        + 0.05 * ath_n          # Distância do ATH
        + 0.05 * vol_trend_n    # Volume crescendo
    ) / w_sum
    z *= 0.55 + 0.45 * recommend
    if not tradeable:
        z *= 0.72

    # Prob. calibrada (sigmoid) — explícita como heurística, não modelo treinado
    bounce_prob = 100.0 * _sigmoid(5.0 * (z - 0.48))
    sell_fitness = max(0.0, min(100.0, z * 100.0))

    label = "alta"
    if sell_fitness < 45:
        label = "baixa"
    elif sell_fitness < 62:
        label = "média"

    reasons = []
    if cycles_per_day > 0:
        reasons.append(f"{cycles_per_day:.2f} ciclos/d no hist.")
    if feat.get("near_low_pct") is not None:
        reasons.append(f"perto da mínima ({feat['near_low_pct']:.1f}%)")
    if bounce is not None:
        reasons.append(f"bounce hist. {bounce * 100:.0f}%")
    if ret:
        reasons.append(f"retorno sim. {ret:.1f}%")
    # Novos indicadores
    if feat.get("rsi_14") is not None:
        rsi_v = feat["rsi_14"]
        if rsi_v <= 30:
            reasons.append(f"RSI {rsi_v:.0f} (sobrevendido)")
        elif rsi_v >= 70:
            reasons.append(f"RSI {rsi_v:.0f} (sobrecomprado)")
        else:
            reasons.append(f"RSI {rsi_v:.0f}")
    if feat.get("trend_score") is not None and feat["trend_score"] >= 0.6:
        reasons.append("tendência de alta (acima das MAs)")
    elif feat.get("trend_score") is not None and feat["trend_score"] < 0.3:
        reasons.append("tendência de baixa")
    if feat.get("ath_distance_pct") is not None:
        reasons.append(f"ATH -{feat['ath_distance_pct']:.0f}%")
    if feat.get("higher_lows"):
        reasons.append("fundos ascendentes")
    if feat.get("vol_trend") is not None and feat["vol_trend"] > 1.5:
        reasons.append(f"volume crescendo {feat['vol_trend']:.1f}x")

    return {
        "sell_fitness": round(sell_fitness, 1),
        "bounce_prob_pct": round(bounce_prob, 1),
        "fitness_label": label,
        "cycles_per_day": round(cycles_per_day, 3),
        "horizon": normalize_horizon(horizon),
        "horizon_label": preset["label"],
        "prediction_note": (
            "Heurística Spot + candles + backtest — não é garantia nem modelo treinado"
        ),
        "reasons": reasons[:4],
        "features": feat,
    }


def pick_best_horizon_bundle(
    *,
    spot_score: float,
    tradeable: bool,
    candles: list[dict[str, Any]],
    strategies_by_horizon: dict[str, dict[str, Any] | None],
) -> dict[str, Any]:
    """
    Avalia daily/weekly/monthly e devolve o melhor horizonte + resumo dos três.
    strategies_by_horizon[hz] = payload best_strategy (ou None).
    """
    SHORT = {"daily": "Dia", "weekly": "Semana", "monthly": "Mês"}
    horizons: dict[str, Any] = {}
    for hz in ("daily", "weekly", "monthly"):
        preset = HORIZONS[hz]
        days = int(preset["validate_days"])
        feats = analyze_candles(candles, horizon=hz)
        bs = strategies_by_horizon.get(hz)
        pred = predict_sell_fitness(
            horizon=hz,
            spot_score=spot_score,
            tradeable=tradeable,
            features=feats,
            best_strategy=bs,
            validate_days=days,
        )
        horizons[hz] = {
            "id": hz,
            "short": SHORT[hz],
            "label": preset["label"],
            "validate_days": days,
            "sell_fitness": pred.get("sell_fitness"),
            "bounce_prob_pct": pred.get("bounce_prob_pct"),
            "cycles_per_day": pred.get("cycles_per_day"),
            "fitness_label": pred.get("fitness_label"),
            "prediction": pred,
            "candle_features": feats,
            "best_strategy": bs,
        }

    best_hz = max(
        horizons.keys(),
        key=lambda h: float(horizons[h].get("sell_fitness") or 0),
    )
    best = horizons[best_hz]
    return {
        "best_horizon": best_hz,
        "best_horizon_short": best["short"],
        "best_horizon_label": best["label"],
        "horizons": horizons,
        "prediction": best["prediction"],
        "candle_features": best["candle_features"],
        "best_strategy": best["best_strategy"],
    }


def union_horizon_filters(user_cfg: dict[str, Any] | None = None) -> dict[str, float]:
    """Faixa que cobre diário+semanal+mensal (união dos presets), respeitando afrouxar do user."""
    cfg = user_cfg or {}
    mins = [float(h["min_drop_pct"]) for h in HORIZONS.values()]
    maxs = [float(h["max_drop_pct"]) for h in HORIZONS.values()]
    vols = [float(h["min_vol_usd"]) for h in HORIZONS.values()]
    sprs = [float(h["max_spread_pct"]) for h in HORIZONS.values()]
    # união: queda mais larga, vol mais permissivo, spread mais tolerante
    out = {
        "min_drop_pct": min(mins),
        "max_drop_pct": max(maxs),
        "min_vol_usd": min(vols),
        "max_spread_pct": max(sprs),
    }
    # se o user pediu faixa ainda mais aberta nos filtros avançados, respeita
    if cfg.get("min_drop_pct") is not None:
        out["min_drop_pct"] = min(out["min_drop_pct"], float(cfg["min_drop_pct"]))
    if cfg.get("max_drop_pct") is not None:
        out["max_drop_pct"] = max(out["max_drop_pct"], float(cfg["max_drop_pct"]))
    if cfg.get("min_vol_usd") is not None:
        out["min_vol_usd"] = min(out["min_vol_usd"], float(cfg["min_vol_usd"]))
    if cfg.get("max_spread_pct") is not None:
        out["max_spread_pct"] = max(out["max_spread_pct"], float(cfg["max_spread_pct"]))
    return out


def rank_by_sell_fitness(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reordena: tradeable → sell_fitness → score Spot."""
    return sorted(
        candidates,
        key=lambda x: (
            -int(bool(x.get("tradeable"))),
            -float((x.get("prediction") or {}).get("sell_fitness") or 0),
            -float(x.get("score") or 0),
            -float(x.get("drop_pct") or 0),
        ),
    )
