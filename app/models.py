from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


def _coerce_cascade_pcts(v: object) -> Optional[list[float]]:
    if v is None or v == "" or v == []:
        return None
    if isinstance(v, str):
        parts = [p.strip().replace("%", "") for p in v.replace(";", ",").split(",") if p.strip()]
        v = [float(p) for p in parts]
    if isinstance(v, list):
        out = [float(x) for x in v if x is not None and str(x).strip() != ""]
        return out or None
    return None


class BotConfig(BaseModel):
    bot_id: str = "default"
    name: str = "Spot Bot"
    inst_id: str = Field(default="BTC-USDT", min_length=3)
    strategy_id: Optional[str] = None
    buy_pct: float = Field(default=2.0, gt=0, le=50)
    profit_target_pct: float = Field(default=1.0, gt=0, le=50)
    fee_rate_pct: float = Field(default=0.10, ge=0, le=5)
    # 0 = usa saldo disponível na hora da compra
    quote_amount: float = Field(default=0.0, ge=0)
    entry_mode: Literal["quote", "base"] = "quote"
    interval_min: float = Field(default=30.0, ge=1, le=1440)
    run_days: float = Field(default=7.0, ge=0, le=365)
    portfolio_interval_min: float = Field(default=2.0, ge=1, le=60)
    cascade_enabled: bool = False
    cascade_buy_pct: float = Field(default=20.0, ge=5, le=100, description="% por etapa (modo igual)")
    cascade_sell_pct: float = Field(default=25.0, ge=5, le=100, description="% por etapa (modo igual)")
    cascade_buy_pcts: Optional[list[float]] = Field(default=None, description="Etapas personalizadas de compra, ex. [20,20,20,20,20]")
    cascade_sell_pcts: Optional[list[float]] = Field(default=None, description="Etapas personalizadas de venda")

    @field_validator("cascade_buy_pcts", "cascade_sell_pcts", mode="before")
    @classmethod
    def _validate_cascade_pcts_field(cls, v: object) -> Optional[list[float]]:
        return _coerce_cascade_pcts(v)

    @property
    def fee_rate(self) -> float:
        return self.fee_rate_pct / 100.0

    @property
    def poll_interval(self) -> float:
        """Segundos entre ticks (derivado de interval_min)."""
        return max(5.0, float(self.interval_min) * 60.0)


class CredentialsUpdate(BaseModel):
    okx_api_key: Optional[str] = None
    okx_secret_key: Optional[str] = None
    okx_passphrase: Optional[str] = None
    okx_flag: Optional[str] = Field(default=None, pattern=r"^[01]$")
    name: Optional[str] = Field(default=None, max_length=60)


class AccountCreate(BaseModel):
    name: str = Field(default="Nova conta", min_length=1, max_length=60)
    okx_api_key: str = Field(min_length=4)
    okx_secret_key: str = Field(min_length=4)
    okx_passphrase: str = Field(min_length=1)
    okx_flag: str = Field(default="0", pattern=r"^[01]$")
    activate: bool = True


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=60)
    okx_api_key: Optional[str] = None
    okx_secret_key: Optional[str] = None
    okx_passphrase: Optional[str] = None
    okx_flag: Optional[str] = Field(default=None, pattern=r"^[01]$")


class BotCreate(BaseModel):
    name: str = Field(default="Novo bot", min_length=1, max_length=60)
    inst_id: str = Field(default="BTC-USDT", min_length=3)
    strategy_id: Optional[str] = None
    buy_pct: float = Field(default=2.0, gt=0, le=50)
    profit_target_pct: float = Field(default=1.0, gt=0, le=50)
    fee_rate_pct: float = Field(default=0.10, ge=0, le=5)
    quote_amount: float = Field(default=0.0, ge=0, description="0 = saldo disponível")
    entry_mode: Literal["quote", "base"] = "quote"
    interval_min: float = Field(default=30.0, ge=1, le=1440)
    run_days: float = Field(default=7.0, ge=0, le=365)
    portfolio_interval_min: float = Field(default=2.0, ge=1, le=60)
    cascade_enabled: bool = False
    cascade_buy_pct: float = Field(default=20.0, ge=5, le=100)
    cascade_sell_pct: float = Field(default=25.0, ge=5, le=100)
    cascade_buy_pcts: Optional[list[float]] = None
    cascade_sell_pcts: Optional[list[float]] = None

    @field_validator("cascade_buy_pcts", "cascade_sell_pcts", mode="before")
    @classmethod
    def _validate_cascade_pcts_field(cls, v: object) -> Optional[list[float]]:
        return _coerce_cascade_pcts(v)


class ConfigUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=60)
    inst_id: Optional[str] = Field(default=None, min_length=3)
    strategy_id: Optional[str] = None
    buy_pct: Optional[float] = Field(default=None, gt=0, le=50)
    profit_target_pct: Optional[float] = Field(default=None, gt=0, le=50)
    fee_rate_pct: Optional[float] = Field(default=None, ge=0, le=5)
    quote_amount: Optional[float] = Field(default=None, ge=0)
    entry_mode: Optional[Literal["quote", "base"]] = None
    interval_min: Optional[float] = Field(default=None, ge=1, le=1440)
    run_days: Optional[float] = Field(default=None, ge=0, le=365)
    portfolio_interval_min: Optional[float] = Field(default=None, ge=1, le=60)
    cascade_enabled: Optional[bool] = None
    cascade_buy_pct: Optional[float] = Field(default=None, ge=5, le=100)
    cascade_sell_pct: Optional[float] = Field(default=None, ge=5, le=100)
    cascade_buy_pcts: Optional[list[float]] = None
    cascade_sell_pcts: Optional[list[float]] = None

    @field_validator("cascade_buy_pcts", "cascade_sell_pcts", mode="before")
    @classmethod
    def _validate_cascade_pcts_field(cls, v: object) -> Optional[list[float]]:
        return _coerce_cascade_pcts(v)


class StrategyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    buy_pct: float = Field(gt=0, le=50)
    profit_target_pct: float = Field(gt=0, le=50)
    fee_rate_pct: float = Field(default=0.10, ge=0, le=5)
    style: str = Field(default="custom", max_length=40)
    focus: str = Field(default="", max_length=200)
    risk: str = Field(default="médio", max_length=40)
    best_for: str = Field(default="", max_length=120)
    tag: str = Field(default="custom", max_length=40)


class LabSimulate(BaseModel):
    """Simulação independente de bot: token + aporte + queda + lucro alvo."""

    inst_id: str = Field(min_length=3, description="Par OKX, ex. SOL-USDT")
    days: Literal[7, 30, 60, 90] = 30
    aporte: float = Field(default=300.0, gt=0, le=1_000_000)
    aporte_ccy: Literal["USDT", "quote"] = "USDT"
    buy_pct: float = Field(default=2.0, gt=0, le=50, description="Queda % vs ref para comprar")
    profit_target_pct: float = Field(default=1.0, gt=0, le=50, description="PnL líquido alvo %")
    fee_rate_pct: float = Field(default=0.10, ge=0, le=5)
    name: Optional[str] = Field(default=None, max_length=60)


class StrategyValidate(BaseModel):
    inst_id: str = Field(min_length=3)
    days: Literal[7, 30, 60, 90] = 30
    aporte: float = Field(default=300.0, gt=0, le=1_000_000)
    aporte_ccy: Literal["USDT", "quote"] = "USDT"
    strategy_ids: Optional[list[str]] = None
    sort: Literal["profit", "assert"] = "profit"


class Position(BaseModel):
    state: Literal["flat", "long"] = "flat"
    ref_price: Optional[float] = None
    entry_price: Optional[float] = None
    qty: Optional[float] = None
    cost_total: Optional[float] = None
    buy_fee: Optional[float] = None
    buy_fee_ccy: Optional[str] = None
    buy_fee_usdt: Optional[float] = None
    opened_at: Optional[str] = None
    cascade_buy_step: int = 0
    cascade_sell_step: int = 0
    cycle_budget: Optional[float] = None


class Trade(BaseModel):
    id: int
    ts: str
    side: str
    inst_id: str
    qty: Optional[float] = None
    avg_px: Optional[float] = None
    fee: Optional[float] = None
    fee_ccy: Optional[str] = None
    fee_usdt: Optional[float] = None
    pnl_realized: Optional[float] = None
    order_id: Optional[str] = None
    status: str = "filled"
    origin: str = "unknown"
    origin_label: str = "—"
    bot_id: Optional[str] = None
    bot_name: Optional[str] = None


class Event(BaseModel):
    id: int
    ts: str
    level: str
    message: str


class OrderCreate(BaseModel):
    inst_id: str = Field(min_length=3)
    side: Literal["buy", "sell"]
    ord_type: Literal["market", "limit", "post_only", "fok", "ioc"] = "limit"
    sz: float = Field(gt=0)
    px: Optional[float] = Field(default=None, gt=0)
    tgt_ccy: Optional[Literal["quote_ccy", "base_ccy"]] = None


class OrderCancel(BaseModel):
    inst_id: str = Field(min_length=3)
    ord_id: str = Field(min_length=1)


class OrderLimits(BaseModel):
    min_usd: float = Field(default=5.0, ge=0.01, le=50_000)
    max_usd: float = Field(default=100.0, ge=0.01, le=50_000)


class OrderLimitsUpdate(BaseModel):
    min_usd: Optional[float] = Field(default=None, ge=0.01, le=50_000)
    max_usd: Optional[float] = Field(default=None, ge=0.01, le=50_000)


class BotDefaultsUpdate(BaseModel):
    bots_enabled: Optional[bool] = None
    default_interval_min: Optional[float] = Field(default=None, ge=1, le=1440)
    exec_cleanup_wait_hours: Optional[float] = Field(default=None, ge=1, le=168)
    exec_cleanup_executed_days: Optional[float] = Field(default=None, ge=1, le=90)
    portfolio_interval_min: Optional[float] = Field(default=None, ge=1, le=60)


class HunterSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    auto_rotate: Optional[bool] = None
    bot_id: Optional[str] = None
    quote: Optional[str] = Field(default=None, max_length=12)
    min_drop_pct: Optional[float] = Field(default=None, ge=0.5, le=50)
    max_drop_pct: Optional[float] = Field(default=None, ge=1, le=80)
    min_vol_usd: Optional[float] = Field(default=None, ge=0)
    max_spread_pct: Optional[float] = Field(default=None, ge=0.05, le=5)
    require_tradeable: Optional[bool] = None
    min_liq: Optional[str] = Field(default=None, max_length=2)
    top_n: Optional[int] = Field(default=None, ge=1, le=30)
    strategy_id: Optional[str] = Field(default=None, max_length=40)
    scan_interval_min: Optional[float] = Field(default=None, ge=1, le=60)
    cooldown_min: Optional[int] = Field(default=None, ge=0, le=24 * 60)
    quote_amount: Optional[float] = Field(default=None, ge=0)
    budget_ccy: Optional[str] = Field(default=None, max_length=12)
    validate_days: Optional[int] = Field(default=None, ge=7, le=90)
    horizon: Optional[str] = Field(default=None, max_length=16)
    blacklist: Optional[list[str]] = None


class AssistantChat(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: Optional[list[dict[str, str]]] = None
    draft: Optional[dict[str, Any]] = None


class HunterApply(BaseModel):
    inst_id: str = Field(min_length=3)
    start: bool = True
    create_bot: bool = True
