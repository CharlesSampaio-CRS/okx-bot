from dataclasses import dataclass
from typing import Optional


# Folga conservadora no preço de venda estimado (market ≠ last).
DEFAULT_SELL_SLIPPAGE_PCT = 0.08


@dataclass
class PnlSnapshot:
    price: float
    qty: float
    cost_total: float
    fee_rate: float
    gross: float
    sell_fee_est: float
    net_proceeds: float
    pnl: float
    pnl_pct: float
    break_even: float
    target_price: float
    slippage_pct: float = 0.0
    eff_price: float = 0.0


def estimate_net_pnl(
    price: float,
    qty: float,
    cost_total: float,
    fee_rate: float,
    profit_target_pct: float = 0.0,
    slippage_pct: float = DEFAULT_SELL_SLIPPAGE_PCT,
) -> PnlSnapshot:
    slip = max(0.0, float(slippage_pct or 0.0))
    if qty <= 0 or cost_total <= 0 or price <= 0:
        return PnlSnapshot(
            price=price or 0.0,
            qty=qty or 0.0,
            cost_total=cost_total or 0.0,
            fee_rate=fee_rate,
            gross=0.0,
            sell_fee_est=0.0,
            net_proceeds=0.0,
            pnl=0.0,
            pnl_pct=0.0,
            break_even=0.0,
            target_price=0.0,
            slippage_pct=slip,
            eff_price=0.0,
        )

    # Gate de venda usa preço piorado (slippage) para não vender “no last” otimista
    eff_price = float(price) * (1.0 - slip / 100.0)
    gross = eff_price * qty
    sell_fee_est = gross * fee_rate
    net_proceeds = gross - sell_fee_est
    pnl = net_proceeds - cost_total
    pnl_pct = (pnl / cost_total) * 100.0
    denom = qty * (1.0 - fee_rate)
    break_even = cost_total / denom if denom > 0 else 0.0
    # target_price no last: precisa cobrir alvo após slip + fee de venda
    target_price = (
        cost_total * (1.0 + profit_target_pct / 100.0) / denom if denom > 0 else 0.0
    )
    if slip > 0 and (1.0 - slip / 100.0) > 0:
        target_price = target_price / (1.0 - slip / 100.0)
    return PnlSnapshot(
        price=price,
        qty=qty,
        cost_total=cost_total,
        fee_rate=fee_rate,
        gross=gross,
        sell_fee_est=sell_fee_est,
        net_proceeds=net_proceeds,
        pnl=pnl,
        pnl_pct=pnl_pct,
        break_even=break_even,
        target_price=target_price,
        slippage_pct=slip,
        eff_price=eff_price,
    )


def position_cost_basis(
    *,
    okx_avg: float,
    okx_qty: float,
    local_cost: Optional[float],
    local_qty: Optional[float],
    fee_rate: float,
) -> float:
    """
    Custo em quote para gate/posição.
    Preferência: base local (inclui fee de compra) escalada; nunca abaixo do OKX;
    se não há base local, estima fee de compra no notional.
    """
    qty = float(okx_qty or 0)
    avg = float(okx_avg or 0)
    if qty <= 0 or avg <= 0:
        return float(local_cost or 0)
    okx_cost = avg * qty
    fr = max(0.0, float(fee_rate or 0))
    if local_cost and local_qty and float(local_qty) > 0:
        scaled = float(local_cost) * (qty / float(local_qty))
        return max(okx_cost, scaled)
    return okx_cost * (1.0 + fr)


def min_net_sell_pnl_pct(
    fee_rate: float, slippage_pct: float = DEFAULT_SELL_SLIPPAGE_PCT
) -> float:
    """
    Piso de PnL líquido % (já líquido de fee de venda na estimativa).
    Evita scalp que só cobre o ruído de slip.
    """
    _ = fee_rate  # reservado: fee de venda já entra em estimate_net_pnl
    slip = max(0.0, float(slippage_pct or 0))
    return max(0.05, slip + 0.05)


def fee_to_quote(
    fee: Optional[float],
    fee_ccy: Optional[str],
    price: float,
    quote_ccy: str,
    base_ccy: str,
) -> float:
    if fee is None:
        return 0.0
    abs_fee = abs(float(fee))
    if not fee_ccy:
        return abs_fee
    ccy = fee_ccy.upper()
    if ccy == quote_ccy.upper():
        return abs_fee
    if ccy == base_ccy.upper():
        return abs_fee * price
    return abs_fee


def net_base_qty(
    acc_fill_sz: float,
    fee: Optional[float],
    fee_ccy: Optional[str],
    base_ccy: str,
) -> float:
    """Qty efetiva após fee em base (compra spot costuma cobrar fee no token)."""
    qty = acc_fill_sz
    if fee is None or not fee_ccy:
        return qty
    if fee_ccy.upper() == base_ccy.upper():
        return acc_fill_sz + float(fee)  # fee OKX vem negativo
    return qty


def quote_cost(
    avg_px: float,
    acc_fill_sz: float,
    fee: Optional[float],
    fee_ccy: Optional[str],
    quote_ccy: str,
) -> float:
    """Custo em quote (USDT), incluindo fee se cobrada em quote."""
    cost = avg_px * acc_fill_sz
    if fee is None or not fee_ccy:
        return cost
    if fee_ccy.upper() == quote_ccy.upper():
        return cost - float(fee)  # fee negativo → custo sobe
    return cost


def net_sell_proceeds(
    avg_px: float,
    acc_fill_sz: float,
    fee: Optional[float],
    fee_ccy: Optional[str],
    quote_ccy: str,
    base_ccy: str,
    price_for_base_fee: float,
) -> float:
    gross = avg_px * acc_fill_sz
    if fee is None or not fee_ccy:
        return gross
    ccy = fee_ccy.upper()
    if ccy == quote_ccy.upper():
        return gross + float(fee)  # fee negativo
    if ccy == base_ccy.upper():
        return gross - abs(float(fee)) * price_for_base_fee
    return gross
