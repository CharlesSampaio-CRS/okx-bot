"""Limites globais de ordem em USD (configuráveis)."""

from __future__ import annotations

from typing import Any

from .okx_client import parse_inst

STABLE_QUOTES = frozenset({"USDT", "USDC", "USD", "DAI", "BUSD", "TUSD"})

DEFAULT_MIN_USD = 5.0
DEFAULT_MAX_USD = 100.0


def quote_to_usd(amount_quote: float, quote: str, usdt_brl: float | None = None) -> float:
    """Converte valor na moeda quote para USD aproximado."""
    if amount_quote <= 0:
        return 0.0
    q = (quote or "USDT").upper()
    if q in STABLE_QUOTES:
        return float(amount_quote)
    if q == "BRL":
        rate = float(usdt_brl or 0)
        if rate <= 0:
            raise ValueError("Taxa USDT/BRL indisponível — aguarde atualização da carteira")
        return float(amount_quote) / rate
    raise ValueError(f"Par em {q}: conversão USD não suportada — use USDT ou BRL")


def usd_to_quote(usd: float, quote: str, usdt_brl: float | None = None) -> float:
    q = (quote or "USDT").upper()
    if q in STABLE_QUOTES:
        return float(usd)
    if q == "BRL":
        rate = float(usdt_brl or 0)
        if rate <= 0:
            raise ValueError("Taxa USDT/BRL indisponível")
        return float(usd) * rate
    raise ValueError(f"Par em {q}: conversão USD não suportada")


def order_notional_quote(
    *,
    side: str,
    sz: float,
    quote: str,
    px: float,
    tgt_ccy: str | None = None,
) -> float:
    """Valor da ordem na moeda quote do par."""
    if side == "buy" and tgt_ccy == "quote_ccy":
        return float(sz)
    if px <= 0:
        raise ValueError("Preço indisponível para calcular valor da ordem")
    return float(sz) * float(px)


def validate_order_usd(
    value_usd: float,
    *,
    min_usd: float,
    max_usd: float,
    label: str = "Ordem",
) -> None:
    lo = float(min_usd)
    hi = float(max_usd)
    if lo > hi:
        raise ValueError("Limite mínimo maior que o máximo — ajuste em Configurações")
    v = float(value_usd)
    if v < lo:
        raise ValueError(f"{label} abaixo do mínimo (${lo:.2f} USD · valor ≈ ${v:.2f})")
    if v > hi:
        raise ValueError(f"{label} acima do máximo (${hi:.2f} USD · valor ≈ ${v:.2f})")


def clamp_spend_quote(
    spend_quote: float,
    quote: str,
    *,
    min_usd: float,
    max_usd: float,
    usdt_brl: float | None = None,
) -> tuple[float, str | None]:
    """Aplica teto USD; retorna (valor ajustado, aviso ou None)."""
    if spend_quote <= 0:
        return 0.0, None
    try:
        usd = quote_to_usd(spend_quote, quote, usdt_brl)
    except ValueError:
        return spend_quote, None
    hi = float(max_usd)
    if usd <= hi:
        return spend_quote, None
    capped = usd_to_quote(hi, quote, usdt_brl)
    return min(spend_quote, capped), f"limitado a ${hi:.2f} USD (≈ {capped:.4f} {quote})"


def limits_from_row(row: dict[str, Any] | None) -> dict[str, float]:
    if not row:
        return {"min_usd": DEFAULT_MIN_USD, "max_usd": DEFAULT_MAX_USD}
    return {
        "min_usd": float(row.get("min_usd") if row.get("min_usd") is not None else DEFAULT_MIN_USD),
        "max_usd": float(row.get("max_usd") if row.get("max_usd") is not None else DEFAULT_MAX_USD),
    }


def validate_inst_amount_usd(
    inst_id: str,
    amount_quote: float,
    *,
    min_usd: float,
    max_usd: float,
    usdt_brl: float | None = None,
    label: str = "Valor",
) -> None:
    _base, quote = parse_inst(inst_id)
    usd = quote_to_usd(amount_quote, quote, usdt_brl)
    validate_order_usd(usd, min_usd=min_usd, max_usd=max_usd, label=label)
