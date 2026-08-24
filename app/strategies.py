"""Catálogo de estratégias de mercado (dip-buy / mean-reversion) focadas em lucro."""

from __future__ import annotations

from typing import Any

# Presets alinhados ao robô: queda % vs ref → compra; venda no PnL líquido alvo.
MARKET_STRATEGIES: list[dict[str, Any]] = [
    {
        "id": "scalp",
        "name": "Scalp rápido",
        "style": "alta frequência",
        "focus": "lucro rápido em oscilações curtas",
        "buy_pct": 0.8,
        "profit_target_pct": 0.70,
        "fee_rate_pct": 0.10,
        "risk": "médio",
        "best_for": "SOL, ETH, tokens líquidos",
        "tag": "rápido",
        "cascade_capable": False,
    },
    {
        "id": "micro_scalp",
        "name": "Micro scalp",
        "style": "ultra curta",
        "focus": "dips curtos com folga vs fee + slippage",
        "buy_pct": 0.5,
        "profit_target_pct": 0.65,
        "fee_rate_pct": 0.10,
        "risk": "alto",
        "best_for": "pares muito líquidos",
        "tag": "rápido",
        "cascade_capable": False,
    },
    {
        "id": "momentum_dip",
        "name": "Dip momentum",
        "style": "mean reversion",
        "focus": "maior número de ciclos com alvo moderado",
        "buy_pct": 1.5,
        "profit_target_pct": 1.0,
        "fee_rate_pct": 0.10,
        "risk": "médio",
        "best_for": "BTC, ETH, SOL",
        "tag": "clássica",
    },
    {
        "id": "balanced",
        "name": "Equilibrada",
        "style": "clássica",
        "focus": "balanço entre frequência e lucro por ciclo",
        "buy_pct": 2.0,
        "profit_target_pct": 1.2,
        "fee_rate_pct": 0.10,
        "risk": "baixo-médio",
        "best_for": "uso geral",
        "tag": "clássica",
    },
    {
        "id": "profit_max",
        "name": "Lucro máximo",
        "style": "agressiva",
        "focus": "prioriza PnL % por ciclo (menos trades, mais lucro)",
        "buy_pct": 2.5,
        "profit_target_pct": 2.2,
        "fee_rate_pct": 0.10,
        "risk": "alto",
        "best_for": "altcoins voláteis",
        "tag": "lucro",
    },
    {
        "id": "asymmetric",
        "name": "Assimetria",
        "style": "risk/reward",
        "focus": "queda moderada + alvo 2× a entrada (R:R ~1:2)",
        "buy_pct": 1.8,
        "profit_target_pct": 3.2,
        "fee_rate_pct": 0.10,
        "risk": "alto",
        "best_for": "tendência com pullbacks",
        "tag": "lucro",
    },
    {
        "id": "deep_dip",
        "name": "Deep dip",
        "style": "value",
        "focus": "compra em correções fortes; alvo generoso",
        "buy_pct": 5.0,
        "profit_target_pct": 3.0,
        "fee_rate_pct": 0.10,
        "risk": "alto",
        "best_for": "mercados em range",
        "tag": "value",
    },
    {
        "id": "crash_buyer",
        "name": "Crash buyer",
        "style": "capitulation",
        "focus": "só entra em dumps fortes; mira recuperação ampla",
        "buy_pct": 8.0,
        "profit_target_pct": 4.5,
        "fee_rate_pct": 0.10,
        "risk": "muito alto",
        "best_for": "altcoins / eventos",
        "tag": "value",
    },
    {
        "id": "conservative",
        "name": "Conservadora",
        "style": "defensiva",
        "focus": "queda maior + alvo seguro acima das taxas",
        "buy_pct": 3.5,
        "profit_target_pct": 1.5,
        "fee_rate_pct": 0.10,
        "risk": "baixo",
        "best_for": "BTC, capital maior",
        "tag": "segura",
    },
    {
        "id": "sniper",
        "name": "Sniper",
        "style": "seletiva",
        "focus": "poucas entradas precisas; alto hit rate esperado",
        "buy_pct": 4.0,
        "profit_target_pct": 2.0,
        "fee_rate_pct": 0.10,
        "risk": "médio",
        "best_for": "validar em 30–90d",
        "tag": "seletiva",
    },
    {
        "id": "fee_aware",
        "name": "Fee-aware",
        "style": "otimizada p/ taxas",
        "focus": "alvo cobre taker 2x com folga; evita churn",
        "buy_pct": 1.8,
        "profit_target_pct": 0.9,
        "fee_rate_pct": 0.10,
        "risk": "baixo-médio",
        "best_for": "conta com taxa ~0.1%",
        "tag": "segura",
    },
    {
        "id": "swing_range",
        "name": "Swing range",
        "style": "swing",
        "focus": "espera pullback médio e realiza no meio da banda",
        "buy_pct": 3.0,
        "profit_target_pct": 2.5,
        "fee_rate_pct": 0.10,
        "risk": "médio",
        "best_for": "BTC/ETH em lateralização",
        "tag": "swing",
    },
]


def list_strategies(include_custom: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    out = []
    for s in MARKET_STRATEGIES:
        row = dict(s)
        row.setdefault("cascade_capable", True)
        row["builtin"] = True
        row["custom"] = False
        out.append(row)
    for s in include_custom or []:
        row = dict(s)
        row.setdefault(
            "cascade_capable",
            float(row.get("buy_pct") or 0) >= 1.5 and float(row.get("profit_target_pct") or 0) >= 0.5,
        )
        row["builtin"] = False
        row["custom"] = True
        out.append(row)
    return out


def get_strategy(strategy_id: str | None, include_custom: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    sid = (strategy_id or "").strip().lower()
    if not sid:
        return None
    for s in list_strategies(include_custom):
        if str(s.get("id") or "").lower() == sid:
            return dict(s)
    return None


def rank_key(row: dict[str, Any], mode: str = "profit") -> tuple:
    """Ordenação: lucro primeiro (default) ou assertividade."""
    s = row.get("summary") or {}
    ret = float(s.get("capital_return_pct") or -999.0)
    assertiveness = float(s.get("assertiveness") or 0.0)
    locked = 1 if s.get("profit_locked") else 0
    validated = 1 if s.get("pnl_validated") else 0
    cycles = int(s.get("cycles_closed") or 0)
    # score composto: retorno ponderado pela confiança
    profit_score = ret * (0.5 + assertiveness / 200.0) + (5.0 if locked else 0.0)
    if mode == "assert":
        return (validated, locked, assertiveness, ret, cycles)
    return (profit_score, ret, locked, assertiveness, cycles)
