"""Compra/venda em cascata: tranches iguais ou lista personalizada de %."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import BotConfig

MAX_CASCADE_STEPS = 10


def cascade_enabled(cfg: "BotConfig") -> bool:
    return bool(getattr(cfg, "cascade_enabled", False))


def _equal_pcts(step_pct: float) -> list[float]:
    pct = max(5.0, min(100.0, float(step_pct or 33.0)))
    n = max(1, min(MAX_CASCADE_STEPS, round(100.0 / pct)))
    if n <= 1:
        return [100.0]
    steps = [pct] * (n - 1)
    steps.append(max(5.0, 100.0 - pct * (n - 1)))
    return steps


def _resolve_pcts(raw: list[float] | None, fallback_pct: float) -> list[float]:
    if raw and isinstance(raw, (list, tuple)) and len(raw) >= 1:
        out = [max(5.0, min(100.0, float(x))) for x in raw[:MAX_CASCADE_STEPS]]
        return out if out else _equal_pcts(fallback_pct)
    return _equal_pcts(fallback_pct)


def buy_pcts(cfg: "BotConfig") -> list[float]:
    if not cascade_enabled(cfg):
        return [100.0]
    raw = getattr(cfg, "cascade_buy_pcts", None)
    fb = float(getattr(cfg, "cascade_buy_pct", 33.0) or 33.0)
    return _resolve_pcts(raw, fb)


def sell_pcts(cfg: "BotConfig") -> list[float]:
    if not cascade_enabled(cfg):
        return [100.0]
    raw = getattr(cfg, "cascade_sell_pcts", None)
    fb = float(getattr(cfg, "cascade_sell_pct", 50.0) or 50.0)
    return _resolve_pcts(raw, fb)


def cascade_steps(cfg: "BotConfig") -> tuple[int, int]:
    if not cascade_enabled(cfg):
        return 1, 1
    return len(buy_pcts(cfg)), len(sell_pcts(cfg))


def buy_drop_trigger_pct(cfg: "BotConfig", step_index: int) -> float:
    """Queda % vs ref para a tranche step_index (0 = primeira compra)."""
    steps = buy_pcts(cfg)
    n = len(steps)
    if n <= 1:
        return float(cfg.buy_pct)
    return float(cfg.buy_pct) * (step_index + 1) / n


def sell_pnl_trigger_pct(cfg: "BotConfig", step_index: int) -> float:
    """PnL líquido % alvo para liberar venda.

    Cascata só fatia o *tamanho* da venda — o alvo de lucro é sempre o
    `profit_target_pct` completo. Antes, a 1ª tranche usava alvo/N (ex. 0,25%)
    e vendia com margem insuficiente vs fees/slippage.
    """
    _ = step_index
    return float(cfg.profit_target_pct)


def buy_tranche_quote(cfg: "BotConfig", total_budget: float, step_index: int) -> float:
    """Valor em quote para a tranche step_index."""
    if not cascade_enabled(cfg) or total_budget <= 0:
        return total_budget
    pcts = buy_pcts(cfg)
    if step_index >= len(pcts):
        return 0.0
    if step_index >= len(pcts) - 1:
        spent = sum(total_budget * p / 100.0 for p in pcts[:step_index])
        return max(0.0, total_budget - spent)
    return total_budget * pcts[step_index] / 100.0


def sell_tranche_qty(cfg: "BotConfig", avail_qty: float, step_index: int) -> float:
    """Quantidade base a vender na tranche step_index."""
    if avail_qty <= 0:
        return 0.0
    if not cascade_enabled(cfg):
        return avail_qty
    pcts = sell_pcts(cfg)
    if step_index >= len(pcts):
        return 0.0
    if step_index >= len(pcts) - 1:
        return avail_qty
    return avail_qty * pcts[step_index] / 100.0


def validate_cascade_pcts(pcts: list[float] | None, label: str) -> None:
    if not pcts:
        return
    if len(pcts) > MAX_CASCADE_STEPS:
        raise ValueError(f"{label}: máximo {MAX_CASCADE_STEPS} etapas")
    if any(p < 5 or p > 100 for p in pcts):
        raise ValueError(f"{label}: cada etapa entre 5% e 100%")
    if sum(pcts) > 100.01:
        raise ValueError(f"{label}: soma não pode passar de 100% (atual {sum(pcts):.0f}%)")
