from contextlib import asynccontextmanager
import asyncio
import math
import time
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import auth, credentials, db
from .context import current_user_id
from . import cache as api_cache
from .cascade import validate_cascade_pcts
from .config import STATIC_DIR
from .engine import TradingEngine
from .models import AccountCreate, AccountUpdate, AssistantChat, BotConfig, BotCreate, BotDefaultsUpdate, ConfigUpdate, CredentialsUpdate, HunterApply, HunterSettingsUpdate, LabSimulate, OrderCancel, OrderCreate, OrderLimits, OrderLimitsUpdate, StrategyCreate, StrategyValidate
from .okx_client import OkxClient, OkxError, icon_urls, parse_inst
from .order_limits import order_notional_quote, quote_to_usd, validate_inst_amount_usd, validate_order_usd
from .portfolio import PortfolioWatcher
from .hunter_watcher import HunterWatcher
from . import lab as lab_sim
from . import strategies as strat_catalog
from .strategies import get_strategy

# Histórico OKX muda pouco — cache TTL ~5 min (RAM + Mongo api_cache). refresh=1 ou nova ordem invalida.
_HIST_CACHE: dict[str, dict[str, Any]] = {}
_HIST_CACHE_KIND = "orders_history"
_HIST_TTL_S = 300.0
_CANDLES_CACHE_KIND = "candles"
_CANDLES_TTL_S = 86400.0  # 1 dia — refresh=1 força atualização
_EQ_HIST_CACHE_KIND = "equity_history"
_EQ_HIST_TTL_S = 86400.0  # 1 dia



def _hist_cache_get(key: str) -> Optional[dict[str, Any]]:
    hit = _HIST_CACHE.get(key)
    if hit:
        if time.time() - float(hit.get("ts") or 0) <= _HIST_TTL_S:
            return hit
        _HIST_CACHE.pop(key, None)
    stored = db.get_api_cache(key, _HIST_TTL_S)
    if not stored:
        return None
    hit = {"ts": stored["ts"], "payload": stored["payload"]}
    _HIST_CACHE[key] = hit
    return hit


def _hist_cache_set(key: str, payload: dict[str, Any]) -> None:
    ts = time.time()
    _HIST_CACHE[key] = {"ts": ts, "payload": payload}
    db.set_api_cache(key, payload, kind=_HIST_CACHE_KIND)


def _hist_cache_clear() -> None:
    _HIST_CACHE.clear()
    db.clear_api_cache(kind=_HIST_CACHE_KIND)
    db.clear_api_cache(kind="order_detail")


def _raise_okx(exc: OkxError, status: int = 400) -> None:
    raise HTTPException(status, detail=exc.as_detail()) from exc


class EngineHub:
    def __init__(self) -> None:
        self.okx = OkxClient()
        self._engines: dict[str, TradingEngine] = {}

    def get(self, bot_id: str) -> TradingEngine:
        if bot_id not in self._engines:
            self._engines[bot_id] = TradingEngine(bot_id, self.okx)
        return self._engines[bot_id]

    def drop(self, bot_id: str) -> None:
        self._engines.pop(bot_id, None)

    def any_running(self) -> bool:
        uid = current_user_id.get() or ""
        for bid, eng in self._engines.items():
            if not eng.running:
                continue
            if uid:
                owner = db.peek_bot_user(bid)
                if owner != uid:
                    continue
            return True
        return False

    async def start_only(self, bot_id: str) -> None:
        uid = current_user_id.get() or ""
        for bid, eng in list(self._engines.items()):
            if bid == bot_id or not eng.running:
                continue
            if uid:
                owner = db.peek_bot_user(bid)
                if owner != uid:
                    continue
            await eng.stop()
        await self.get(bot_id).start()

    async def close(self) -> None:
        for eng in self._engines.values():
            await eng.stop()
        await self.okx.aclose()

    async def card(self, bot_id: str, *, refresh: bool = True) -> dict[str, Any]:
        eng = self.get(bot_id)
        if refresh and credentials.configured() and not eng.running:
            try:
                await asyncio.wait_for(eng.refresh_token_view(), timeout=3.0)
            except (asyncio.TimeoutError, OkxError, Exception):
                pass
        snap = eng.snapshot()
        if refresh and snap.get("price") is None and snap.get("inst_id"):
            try:
                eng.last_price = await asyncio.wait_for(
                    self.okx.get_last_price(snap["inst_id"]),
                    timeout=2.0,
                )
                snap = eng.snapshot()
            except (asyncio.TimeoutError, OkxError, Exception):
                pass
        try:
            base, _quote = parse_inst(str(snap.get("inst_id") or ""))
            icon, alt = icon_urls(base)
        except Exception:
            icon, alt = None, None
        snap["icon"] = icon
        snap["icon_alt"] = alt
        try:
            row = db.get_bot_doc(bot_id)
        except KeyError:
            row = {}
        aid = str(row.get("okx_account_id") or "")
        active = credentials.active_id()
        snap["okx_account_id"] = aid
        snap["okx_account_name"] = (
            credentials.account_name(aid) if aid else credentials.account_name(active)
        )
        snap["okx_account_active"] = (not aid) or (not active) or (aid == active)
        return snap


hub = EngineHub()
portfolio = PortfolioWatcher(hub.okx)
hunter = HunterWatcher(hub.okx, hub)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    if not auth.enabled():
        credentials.load()
        aid = credentials.active_id()
        if aid:
            db.stamp_existing_okx_account_id(aid)
        if credentials.configured():
            await portfolio.start()
    await hunter.start()
    cleanup_task = asyncio.create_task(_executions_cleanup_loop(), name="executions-cleanup")
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    await hunter.stop()
    await portfolio.stop()
    await hub.close()


async def _executions_cleanup_loop() -> None:
    """Job horário: limpa log de decisões antigas (não apaga trades/ordens)."""
    while True:
        try:
            await asyncio.sleep(3600)
            defaults = db.get_bot_defaults()
            stats = db.cleanup_executions(
                wait_max_age_hours=float(defaults.get("exec_cleanup_wait_hours") or 6),
                executed_max_age_days=float(defaults.get("exec_cleanup_executed_days") or 14),
            )
            if stats.get("deleted_waits") or stats.get("deleted_executed"):
                db.add_event(
                    f"limpeza execuções: waits={stats.get('deleted_waits', 0)} · "
                    f"executadas={stats.get('deleted_executed', 0)}"
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            # não derruba o app por falha de limpeza
            await asyncio.sleep(60)


app = FastAPI(title="OKBot", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.middleware("http")
async def auth_gate(request: Request, call_next):
    path = request.url.path
    token = None
    if auth.enabled() and not path.startswith("/api/auth"):
        user = auth.user_from_request(request)
        if path.startswith("/api/") and not user:
            return auth.unauthorized()
        if user:
            token = auth.bind_user(user)
            credentials.hydrate_user(str(user.get("user_id") or ""))
            await portfolio.ensure_started()
    try:
        return await call_next(request)
    finally:
        if token is not None:
            current_user_id.reset(token)


@app.get("/api/auth/config")
async def auth_config() -> dict[str, Any]:
    return {"enabled": auth.enabled()}


@app.get("/api/auth/login")
async def auth_login(request: Request):
    if not auth.enabled():
        raise HTTPException(400, "login Google não configurado")
    url = await auth.login_url(request)
    resp = RedirectResponse(url, status_code=302)
    auth.set_state_cookie(resp, getattr(request.state, "oauth_state", ""))
    return resp


@app.get("/api/auth/callback")
async def auth_callback(request: Request, code: str = "", state: str = ""):
    saved = request.cookies.get(auth.STATE_COOKIE) or ""
    if not code or not state or state != saved:
        raise HTTPException(400, "login inválido ou expirado — tente de novo")
    claims = await auth.exchange_code(request, code)
    user = auth.upsert_user(claims)
    sid = auth.create_session(str(user["user_id"]))
    resp = RedirectResponse("/", status_code=302)
    auth.set_session_cookie(resp, sid)
    resp.delete_cookie(auth.STATE_COOKIE, path="/")
    return resp


@app.get("/api/auth/me")
async def auth_me(request: Request) -> dict[str, Any]:
    user = auth.user_from_request(request)
    if auth.enabled() and not user:
        return auth.unauthorized()
    return auth.public_user(user)


@app.api_route("/api/auth/logout", methods=["GET", "POST"])
async def auth_logout(request: Request):
    auth.drop_session(request.cookies.get(auth.COOKIE))
    if auth.enabled():
        resp = RedirectResponse(auth.logout_url(request), status_code=302)
    else:
        resp = RedirectResponse("/", status_code=302)
    auth.clear_session_cookie(resp)
    return resp


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(STATIC_DIR / "favicon.ico")


@app.get("/api/status")
async def status(include: str = "") -> dict[str, Any]:
    """Painel rápido: só cache local. Sem OKX — evita travar o poll da UI."""
    bots = []
    for row in db.list_bots():
        bots.append(await hub.card(row["bot_id"], refresh=False))
    bots.sort(key=lambda b: (not bool(b.get("running")), str(b.get("updated_at") or ""), str(b.get("bot_id") or "")))
    port = portfolio.snapshot()
    # Não chama portfolio.refresh_now() aqui — o PortfolioWatcher já atualiza em background.
    running = hub.any_running()
    data: dict[str, Any] = {
        "running": running,
        "keys_configured": credentials.configured(),
        "bots": bots,
        "wallet_eq": port.get("total_eq"),
        "wallet_pnl_today": port.get("pnl_today"),
        "wallet_pnl_24h": port.get("pnl_24h"),
        "wallet_pnl_week": port.get("pnl_week"),
        "wallet_pnl_month": port.get("pnl_month"),
        "wallet_spot_upl": port.get("spot_upl"),
        "wallet_updated_at": port.get("updated_at"),
        "wallet_error": port.get("last_error"),
        "usdt_brl": port.get("usdt_brl"),
        "okx_flag": credentials.get("okx_flag"),
        "portfolio_interval_min": db.portfolio_interval_min(),
        "cache": api_cache.cache_status(),
        **db.get_order_limits(),
    }
    if "trades" in {p.strip() for p in include.split(",") if p.strip()}:
        data["trades"] = [t.model_dump() for t in db.list_trades(80)]
    return data


@app.get("/api/bots")
async def list_bots() -> dict[str, Any]:
    bots = [await hub.card(row["bot_id"]) for row in db.list_bots()]
    bots.sort(key=lambda b: (not bool(b.get("running")), str(b.get("updated_at") or ""), str(b.get("bot_id") or "")))
    return {"bots": bots}


@app.post("/api/bots")
async def create_bot(body: BotCreate) -> dict[str, Any]:
    _ensure_cascade_ok(body.model_dump())
    _ensure_bot_quote_ok(body.model_dump())
    await _ensure_inst_ok(body.inst_id)
    dup = db.find_duplicate_bot(
        inst_id=body.inst_id,
        buy_pct=body.buy_pct,
        profit_target_pct=body.profit_target_pct,
        fee_rate_pct=body.fee_rate_pct,
        quote_amount=body.quote_amount,
    )
    if dup:
        raise HTTPException(
            409,
            f"já existe o bot «{dup.get('name') or dup.get('bot_id')}» com os mesmos params "
            f"({dup.get('inst_id')} · queda {dup.get('buy_pct')}% · alvo {dup.get('profit_target_pct')}% · "
            f"valor {dup.get('quote_amount')}). Edite ou apague o existente — dois iguais competem entre si.",
        )
    created = db.create_bot(
        name=body.name,
        inst_id=body.inst_id,
        strategy_id=body.strategy_id,
        buy_pct=body.buy_pct,
        profit_target_pct=body.profit_target_pct,
        fee_rate_pct=body.fee_rate_pct,
        quote_amount=body.quote_amount,
        entry_mode=body.entry_mode,
        interval_min=body.interval_min or float(db.get_bot_defaults().get("default_interval_min") or 30),
        run_days=body.run_days,
        portfolio_interval_min=body.portfolio_interval_min,
        cascade_enabled=body.cascade_enabled,
        cascade_buy_pct=body.cascade_buy_pct,
        cascade_sell_pct=body.cascade_sell_pct,
        cascade_buy_pcts=body.cascade_buy_pcts,
        cascade_sell_pcts=body.cascade_sell_pcts,
        okx_account_id=credentials.active_id() or None,
    )
    db.add_event(f"bot criado: {created['name']}", bot_id=created["bot_id"])
    return await hub.card(created["bot_id"])


@app.delete("/api/bots/{bot_id}")
async def delete_bot(bot_id: str) -> dict[str, Any]:
    eng = hub.get(bot_id)
    if eng.running:
        raise HTTPException(400, "pare o bot antes de apagar")
    try:
        db.delete_bot(bot_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    hub.drop(bot_id)
    return {"ok": True}


@app.get("/api/config")
async def get_config(bot_id: str) -> dict[str, Any]:
    try:
        return db.get_config(bot_id).model_dump()
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.put("/api/config")
async def put_config(update: ConfigUpdate, bot_id: str) -> dict[str, Any]:
    if hub.get(bot_id).running:
        raise HTTPException(400, "pare o bot antes de alterar a configuração")
    try:
        current = db.get_config(bot_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    data = current.model_dump()
    patch = update.model_dump(exclude_unset=True)
    if "inst_id" in patch and patch["inst_id"]:
        patch["inst_id"] = patch["inst_id"].strip().upper()
    data.update(patch)
    data["bot_id"] = bot_id
    _ensure_cascade_ok(data)
    _ensure_bot_quote_ok(data)
    if patch.get("inst_id"):
        await _ensure_inst_ok(str(patch["inst_id"]))
    try:
        saved = db.save_config(BotConfig(**data), bot_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    db.add_event("configuração salva", bot_id=bot_id)
    return saved.model_dump()


def _need_idle(msg: str) -> None:
    if hub.any_running():
        raise HTTPException(400, msg)


async def _reload_okx_session() -> None:
    hub.okx.invalidate_private()
    if credentials.configured():
        await portfolio.start()
        try:
            await portfolio.refresh_now()
        except OkxError:
            pass


def _ensure_bot_account(bot_id: str) -> None:
    try:
        row = db.get_bot_doc(bot_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    aid = str(row.get("okx_account_id") or "")
    active = credentials.active_id()
    if not aid:
        if active:
            db.set_bot_account(bot_id, active)
        return
    if active and aid != active:
        label = credentials.account_name(aid) or "outra conta"
        raise HTTPException(
            400,
            f"este bot pertence à conta «{label}». Ative essa conta em Configurações",
        )


@app.get("/api/keys")
async def get_keys() -> dict[str, Any]:
    return credentials.status()


@app.put("/api/keys")
async def put_keys(update: CredentialsUpdate) -> dict[str, Any]:
    _need_idle("pause os bots antes de alterar as chaves da conta ativa")
    try:
        saved = credentials.save(
            api_key=update.okx_api_key,
            secret=update.okx_secret_key,
            passphrase=update.okx_passphrase,
            flag=update.okx_flag,
            name=update.name,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.add_event("credenciais OKX atualizadas")
    await _reload_okx_session()
    return saved


@app.post("/api/keys/accounts")
async def create_okx_account(body: AccountCreate) -> dict[str, Any]:
    if body.activate:
        _need_idle("pause os bots antes de ativar a nova conta")
    before = credentials.active_id()
    try:
        saved = credentials.add_account(
            name=body.name,
            api_key=body.okx_api_key,
            secret=body.okx_secret_key,
            passphrase=body.okx_passphrase,
            flag=body.okx_flag,
            activate=body.activate,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.add_event(f"conta OKX adicionada: {body.name}")
    if credentials.active_id() != before:
        await _reload_okx_session()
    return saved


@app.put("/api/keys/accounts/{account_id}")
async def update_okx_account(account_id: str, body: AccountUpdate) -> dict[str, Any]:
    keys_changed = bool(
        body.okx_api_key or body.okx_secret_key or body.okx_passphrase or body.okx_flag is not None
    )
    if account_id == credentials.active_id() and keys_changed:
        _need_idle("pause os bots antes de alterar as chaves da conta ativa")
    try:
        saved = credentials.update_account(
            account_id,
            name=body.name,
            api_key=body.okx_api_key,
            secret=body.okx_secret_key,
            passphrase=body.okx_passphrase,
            flag=body.okx_flag,
        )
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.add_event("conta OKX atualizada")
    if account_id == credentials.active_id() and keys_changed:
        await _reload_okx_session()
    return saved


@app.post("/api/keys/accounts/{account_id}/activate")
async def activate_okx_account(account_id: str) -> dict[str, Any]:
    _need_idle("pause os bots antes de trocar de conta OKX")
    try:
        saved = credentials.activate(account_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.add_event(f"conta OKX ativa: {saved.get('account_name') or account_id}")
    await _reload_okx_session()
    return saved


@app.delete("/api/keys/accounts/{account_id}")
async def delete_okx_account(account_id: str) -> dict[str, Any]:
    try:
        saved = credentials.delete_account(account_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.add_event("conta OKX apagada")
    return saved


@app.post("/api/bots/{bot_id}/start")
async def start_engine(bot_id: str) -> dict[str, Any]:
    if not credentials.configured():
        raise HTTPException(400, "cadastre API Key, Secret e Passphrase em Configurações")
    try:
        cfg = db.get_config(bot_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    _ensure_bot_account(bot_id)
    await _ensure_inst_ok(cfg.inst_id)
    await hub.start_only(bot_id)
    return await hub.card(bot_id)


@app.post("/api/bots/{bot_id}/preflight")
async def bot_preflight(bot_id: str, backtest: int = 1) -> dict[str, Any]:
    """Valida saldo, par, limites e (opcional) backtest rápido antes de iniciar live."""
    checks: list[dict[str, Any]] = []

    def add(
        ok: bool,
        label: str,
        detail: str,
        *,
        level: str = "block",
        action: dict[str, Any] | None = None,
    ) -> None:
        row: dict[str, Any] = {"ok": bool(ok), "label": label, "detail": detail, "level": level}
        if action:
            row["action"] = action
        checks.append(row)

    if not credentials.configured():
        add(False, "API Keys", "Cadastre Key, Secret e Passphrase em Configurações")
        return {
            "ok": False,
            "can_start": False,
            "checks": checks,
            "blockers": [c["label"] for c in checks if not c["ok"] and c["level"] == "block"],
            "warnings": [],
            "bot_id": bot_id,
        }

    try:
        cfg = db.get_config(bot_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc

    try:
        row = db.get_bot_doc(bot_id)
    except KeyError:
        row = {}
    aid = str(row.get("okx_account_id") or "")
    active = credentials.active_id()
    if aid and active and aid != active:
        add(
            False,
            "Conta OKX",
            f"Este bot é da conta «{credentials.account_name(aid)}». Ative essa conta em Configurações.",
        )
    elif active:
        add(True, "Conta OKX", credentials.account_name(active) or "conta ativa")

    base, quote = parse_inst(cfg.inst_id)
    card = await hub.card(bot_id)
    eng = hub.get(bot_id)

    # Par Spot / compliance
    try:
        await _ensure_inst_ok(cfg.inst_id)
        add(True, "Par Spot", f"{cfg.inst_id} negociável na sua conta")
    except HTTPException as exc:
        add(False, "Par Spot", str(exc.detail))

    # Preço
    price = float(card.get("price") or 0)
    if price <= 0:
        try:
            price = float(await hub.okx.get_last_price(cfg.inst_id) or 0)
        except OkxError as exc:
            add(False, "Preço", f"indisponível: {exc}")
            price = 0.0
    if price > 0:
        add(True, "Preço", f"{price:g} {quote}")

    # Posição / saldo: quote só avisa no start — a compra real já valida na hora da ordem.
    # Se já tem token (long), o bot pode rodar só para vender.
    hub.okx.invalidate_private()
    state = str(card.get("state") or "flat")
    qty = float(card.get("qty") or 0)
    has_token = state == "long" and qty > 1e-12
    quote_avail = 0.0
    base_avail = 0.0
    try:
        quote_avail = float(await hub.okx.get_balance(quote))
        base_avail = float(await hub.okx.get_balance(base))
    except OkxError as exc:
        add(True, "Saldos", f"não foi possível ler agora ({exc}) — a ordem valida na hora", level="warn")
    else:
        if has_token or base_avail > 1e-12:
            held = qty if has_token else base_avail
            add(
                True,
                f"Posição {base}",
                f"≈ {held:g} {base} em trading · bot pode iniciar e aguardar venda/PnL",
            )
            if quote_avail <= 1e-12:
                add(
                    True,
                    f"Saldo {quote}",
                    f"0 disponível — ok se não for comprar agora; a próxima compra só roda com saldo",
                    level="warn",
                )
            else:
                add(True, f"Saldo {quote}", f"{quote_avail:g} disponível para compras futuras")
        else:
            planned, plan_detail = eng._planned_spend(cfg, price or 1.0, quote_avail)
            spend, limit_note, limit_err = await eng._apply_order_limits(planned, quote)
            if limit_err:
                # Limite do sistema: aviso, não barra o start (ordem também valida)
                add(True, "Limite USD", limit_err, level="warn")
            if spend <= 0 or quote_avail <= 1e-12:
                fund = 0.0
                try:
                    fund = float(await hub.okx.get_funding_avail(quote))
                except Exception:
                    fund = 0.0
                tip = (
                    f" Há ≈ {fund:g} {quote} no funding — transfira antes da 1ª compra."
                    if fund > 1e-8
                    else " Sem saldo trading para comprar agora — o bot inicia e espera; a ordem só sai com saldo."
                )
                add(
                    True,
                    f"Saldo {quote}",
                    f"disponível {quote_avail:g} · {tip}",
                    level="warn",
                )
            elif spend > quote_avail + 1e-8:
                add(
                    True,
                    f"Saldo {quote}",
                    f"disponível {quote_avail:g} < aporte ≈ {spend:g} — bot inicia; compra só com saldo suficiente",
                    level="warn",
                )
            else:
                note = f"{plan_detail} · 1ª compra ≈ {spend:g} {quote}"
                if limit_note:
                    note = f"{note} · {limit_note}"
                add(True, f"Saldo {quote}", f"{quote_avail:g} disponível · {note}")

            # minSz só como aviso (bloqueio real na ordem)
            if price > 0 and spend > 0 and quote_avail + 1e-12 >= spend:
                try:
                    inst = await hub.okx.get_instrument(cfg.inst_id)
                    min_sz = float(inst.get("minSz") or 0)
                    est_base = spend / price
                    if min_sz > 0 and est_base + 1e-15 < min_sz:
                        add(
                            True,
                            "Tamanho mínimo",
                            f"≈{est_base:g} {base} < min {min_sz:g} — ajuste o aporte antes da compra",
                            level="warn",
                        )
                    else:
                        add(
                            True,
                            "Tamanho mínimo",
                            f"≈{est_base:g} {base}" + (f" ≥ {min_sz:g}" if min_sz else ""),
                        )
                except OkxError as exc:
                    add(True, "Tamanho mínimo", str(exc), level="warn")

    # Outro bot ativo
    others = [
        await hub.card(row["bot_id"])
        for row in db.list_bots()
        if row.get("bot_id") != bot_id
    ]
    running_others = [o for o in others if o.get("running")]
    if running_others:
        names = ", ".join(o.get("name") or o.get("bot_id") for o in running_others)
        add(
            True,
            "Bot ativo",
            f"Ao iniciar, pausará: {names}",
            level="warn",
        )
    else:
        add(True, "Bot ativo", "Nenhum outro bot rodando")

    # Params básicos
    buy_pct = float(cfg.buy_pct or 0)
    target = float(cfg.profit_target_pct or 0)
    if buy_pct <= 0 or target <= 0:
        add(False, "Parâmetros", "queda e alvo de lucro devem ser > 0")
    else:
        add(
            True,
            "Parâmetros",
            f"queda {buy_pct:g}% · lucro {target:g}% · taxa {float(cfg.fee_rate_pct or 0):g}%",
        )

    # Backtest rápido (opcional)
    sim = None
    sim_days = None
    if int(backtest or 0) and price > 0:
        sim_days = int(getattr(cfg, "run_days", None) or 7)
        sim_days = max(7, min(sim_days, 30))
        bar = lab_sim.bar_for_days(sim_days)
        aporte = float(getattr(cfg, "quote_amount", 0) or 0)
        if aporte <= 0:
            aporte = min(max(quote_avail * 0.5, 10.0), 100.0) if quote_avail > 0 else 50.0
        try:
            candles = await hub.okx.get_candles(cfg.inst_id, bar=bar, days=sim_days, limit=800)
            sim = lab_sim.simulate(
                cfg,
                candles,
                fee_rate=cfg.fee_rate,
                quote_amount=aporte,
                days=sim_days,
            )
            summary = sim.get("summary") or {}
            quality = summary.get("quality") or {}
            ret = summary.get("capital_return_pct")
            assertiv = quality.get("assertiveness")
            rec = bool(quality.get("recommend_create"))
            note = str(quality.get("note") or "").strip()
            detail = (
                f"{sim_days}d · retorno {float(ret or 0):.2f}% · assert. {float(assertiv or 0):.0f} "
                f"· ciclos {summary.get('cycles_closed', 0)}"
            )
            lab_action = {
                "type": "open_lab",
                "bot_id": bot_id,
                "days": int(sim_days),
                "label": "Abrir no Lab",
            }
            if rec:
                add(
                    True,
                    "Backtest",
                    f"{detail} · ok para operar",
                    level="ok",
                    action=lab_action,
                )
            else:
                tip = f" {note}" if note else " Ajuste queda/alvo ou abra no Lab."
                add(
                    True,
                    "Backtest",
                    f"{detail} · frágil — revise ou ajuste antes.{tip}",
                    level="warn",
                    action=lab_action,
                )
        except Exception as exc:
            add(True, "Backtest", f"não rodou ({exc})", level="warn")

    blockers = [c["label"] for c in checks if not c["ok"] and c.get("level") == "block"]
    warnings = [
        c["label"]
        for c in checks
        if c.get("level") == "warn"
        and (
            "frágil" in str(c.get("detail") or "").lower()
            or "pausará" in str(c.get("detail") or "")
            or not c["ok"]
        )
    ]

    return {
        "ok": not blockers,
        "can_start": not blockers,
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "bot_id": bot_id,
        "bot": card,
        "quote": quote,
        "base": base,
        "price": price or None,
        "sim": {
            "days": sim_days,
            "summary": (sim or {}).get("summary"),
        } if sim else None,
    }


@app.post("/api/bots/{bot_id}/stop")
async def stop_engine(bot_id: str) -> dict[str, Any]:
    await hub.get(bot_id).stop()
    return await hub.card(bot_id)


@app.post("/api/bots/{bot_id}/tick")
async def tick_engine(bot_id: str) -> dict[str, Any]:
    """Executa um ciclo agora (manual). Pode comprar/vender se as regras fecharem."""
    if not credentials.configured():
        raise HTTPException(400, "cadastre API Key, Secret e Passphrase em Configurações")
    try:
        db.get_config(bot_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    _ensure_bot_account(bot_id)
    eng = hub.get(bot_id)
    try:
        await eng.tick_once(manual=True)
    except OkxError as exc:
        eng.last_error = str(exc)
        _raise_okx(exc)
    except Exception as exc:
        eng.last_error = str(exc)
        raise HTTPException(400, str(exc)) from exc
    return await hub.card(bot_id)


@app.get("/api/lab/tokens")
async def lab_tokens() -> dict[str, Any]:
    """Presets do Lab com disponibilidade na OKX spot (e se a região permite negociar)."""
    try:
        tickers = await hub.okx.get_ticker_map()
        tokens = lab_sim.lab_token_catalog(tickers.keys())
        tradable = await hub.okx.get_account_tradable_spot_ids()
        if tradable is not None:
            for t in tokens:
                inst = str(t.get("inst_id") or "").upper()
                if t.get("available") and inst not in tradable:
                    t["available"] = False
                    t["note"] = "Indisponível na sua região (compliance OKX)"
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"tokens": tokens}


def _all_strategies() -> list[dict[str, Any]]:
    return strat_catalog.list_strategies(db.list_custom_strategies())


def _ensure_cascade_ok(data: dict[str, Any]) -> None:
    if not data.get("cascade_enabled"):
        return
    sid = (data.get("strategy_id") or "").strip().lower() or None
    if sid:
        strat = next((s for s in _all_strategies() if s["id"] == sid), None)
        if strat and not strat.get("cascade_capable"):
            raise HTTPException(
                400,
                f"A estratégia «{strat.get('name') or sid}» não suporta cascata (use swing, deep dip, etc.).",
            )
    elif float(data.get("buy_pct") or 0) < 1.5 or float(data.get("profit_target_pct") or 0) < 0.5:
        raise HTTPException(400, "Cascata no modo manual exige queda ≥ 1,5% e alvo ≥ 0,5%.")
    try:
        validate_cascade_pcts(data.get("cascade_buy_pcts"), "Compras em cascata")
        validate_cascade_pcts(data.get("cascade_sell_pcts"), "Vendas em cascata")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def _usdt_brl_now() -> float | None:
    rate = portfolio.snapshot().get("usdt_brl")
    try:
        return float(rate) if rate is not None else None
    except (TypeError, ValueError):
        return None


def _ensure_bot_quote_ok(data: dict[str, Any]) -> None:
    raw = float(data.get("quote_amount") or 0)
    if raw <= 0:
        return
    inst = (data.get("inst_id") or "").strip().upper()
    if not inst or "-" not in inst:
        return
    mode = str(data.get("entry_mode") or "quote").lower()
    if mode == "base":
        return
    limits = db.get_order_limits()
    try:
        validate_inst_amount_usd(
            inst,
            raw,
            min_usd=limits["min_usd"],
            max_usd=limits["max_usd"],
            usdt_brl=_usdt_brl_now(),
            label="Valor de entrada",
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


async def _validate_manual_order(body: OrderCreate) -> None:
    inst = body.inst_id.strip().upper()
    _base, quote = parse_inst(inst)
    sz = float(body.sz or 0)
    if not math.isfinite(sz) or sz <= 0:
        raise HTTPException(400, "Quantidade/valor da ordem inválido")
    px = float(body.px or 0)
    if body.ord_type != "market" and px <= 0:
        raise HTTPException(400, "Preço obrigatório para ordem limite")
    if body.ord_type == "market" and px <= 0:
        try:
            px = float(await hub.okx.get_last_price(inst) or 0)
        except OkxError as exc:
            raise HTTPException(502, f"Preço indisponível: {exc}") from exc
    if px <= 0:
        raise HTTPException(400, "Preço indisponível para validar valor da ordem")

    tgt = (body.tgt_ccy or "").lower().strip()
    if body.ord_type == "market" and not tgt:
        tgt = "quote_ccy" if body.side == "buy" else "base_ccy"

    # Instrumento live + compliance
    try:
        instrument = await hub.okx.get_instrument(inst)
        if str(instrument.get("state") or "").lower() not in {"", "live"}:
            raise HTTPException(400, f"Par {inst} não está negociável agora (state={instrument.get('state')})")
        min_sz = float(instrument.get("minSz") or 0)
    except HTTPException:
        raise
    except OkxError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception:
        min_sz = 0.0

    quote_ccy_buy = (
        body.side == "buy"
        and (tgt == "quote_ccy" or (body.ord_type == "market" and tgt != "base_ccy"))
    )
    if min_sz > 0 and px > 0:
        base_eq = (sz / px) if quote_ccy_buy else sz
        if base_eq + 1e-15 < min_sz:
            min_quote = min_sz * px
            # "10" enviado como BOME mas parece USDT (mín. ~1.2 USDT / 1000 BOME)
            if (
                body.side == "buy"
                and not quote_ccy_buy
                and sz + 1e-12 >= min_quote
                and (sz / px) >= min_sz
            ):
                if body.ord_type == "market":
                    body.tgt_ccy = "quote_ccy"
                    quote_ccy_buy = True
                    base_eq = sz / px
                else:
                    # Limite: sz na OKX é sempre base — converte USDT → token
                    body.sz = float(sz) / float(px)
                    sz = body.sz
                    base_eq = sz
            if base_eq + 1e-15 < min_sz:
                raise HTTPException(
                    400,
                    (
                        f"Abaixo do mínimo OKX deste par: {min_sz:g} {_base} "
                        f"(≈ {min_quote:.4f} {quote}). Você enviou ≈ {base_eq:g} {_base}. "
                        f"Para gastar {quote}, use Mercado + valor do par "
                        f"(mín. ≈ {min_quote:.2f} {quote})."
                    ),
                )

    # Compra limite com valor em quote (USDT): mantém tgt_ccy=quote_ccy;
    # place_order converte USDT → base antes do POST (OKX exige base no limite).
    if body.side == "buy" and body.ord_type != "market" and quote_ccy_buy:
        body.tgt_ccy = "quote_ccy"

    notional = order_notional_quote(
        side=body.side,
        sz=sz,
        quote=quote,
        px=px,
        tgt_ccy=body.tgt_ccy,
    )
    if notional <= 0:
        raise HTTPException(400, "Valor nocional da ordem inválido")

    # Saldo trading fresco — falha fechada (não engole erro)
    try:
        if body.side == "buy":
            if quote_ccy_buy:
                await hub.okx.precheck_spot_buy(inst, sz, price=px, fresh_balance=True)
            else:
                # compra em base_ccy: precisa de quote ≈ sz * px
                need_quote = float(sz) * float(px)
                await hub.okx.precheck_spot_buy(inst, need_quote, price=px, fresh_balance=True)
        else:
            sell_qty = float(sz) if tgt != "quote_ccy" else (float(sz) / px if px > 0 else 0.0)
            await hub.okx.precheck_spot_sell(inst, sell_qty, fresh_balance=True)
    except OkxError as exc:
        raise HTTPException(400, str(exc)) from exc

    limits = db.get_order_limits()
    try:
        usd = quote_to_usd(notional, quote, _usdt_brl_now())
        validate_order_usd(
            usd,
            min_usd=limits["min_usd"],
            max_usd=limits["max_usd"],
            label="Ordem",
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/settings/order-limits")
async def get_order_limits_api() -> dict[str, float]:
    return db.get_order_limits()


@app.put("/api/settings/order-limits")
async def put_order_limits(body: OrderLimitsUpdate) -> dict[str, float]:
    cur = db.get_order_limits()
    lo = float(body.min_usd if body.min_usd is not None else cur["min_usd"])
    hi = float(body.max_usd if body.max_usd is not None else cur["max_usd"])
    try:
        saved = db.save_order_limits(lo, hi)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    db.add_event(f"limites de ordem: ${saved['min_usd']:.0f}–${saved['max_usd']:.0f} USD")
    return saved


@app.get("/api/settings/bot-defaults")
async def get_bot_defaults_api() -> dict[str, Any]:
    return db.get_bot_defaults()


@app.put("/api/settings/bot-defaults")
async def put_bot_defaults(body: BotDefaultsUpdate) -> dict[str, Any]:
    saved = db.save_bot_defaults(body.model_dump(exclude_none=True))
    db.add_event(
        f"padrão bots: intervalo {saved['default_interval_min']:g} min · "
        f"limpeza waits {saved['exec_cleanup_wait_hours']:g}h"
    )
    return saved


@app.get("/api/strategies")
async def list_strategies() -> dict[str, Any]:
    return {"strategies": _all_strategies()}


@app.post("/api/strategies")
async def create_strategy(body: StrategyCreate) -> dict[str, Any]:
    created = db.create_custom_strategy(body.model_dump())
    db.add_event(f"estratégia criada: {created['name']}")
    return {"strategy": created}


@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str) -> dict[str, Any]:
    if not db.delete_custom_strategy(strategy_id):
        raise HTTPException(400, "só é possível apagar estratégias customizadas")
    db.add_event(f"estratégia apagada: {strategy_id}")
    return {"ok": True}


@app.post("/api/strategies/validate")
async def validate_strategies(body: StrategyValidate) -> dict[str, Any]:
    """Roda todas (ou subset) das estratégias no mesmo histórico e ranqueia por lucro/assertividade."""
    inst_id = body.inst_id.strip().upper()
    days = int(body.days)
    bar = lab_sim.bar_for_days(days)
    try:
        base, quote = parse_inst(inst_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    catalog = _all_strategies()
    if body.strategy_ids:
        wanted = {s.strip().lower() for s in body.strategy_ids}
        catalog = [s for s in catalog if s["id"] in wanted]
    if not catalog:
        raise HTTPException(400, "nenhuma estratégia selecionada")

    aporte_quote = float(body.aporte)
    aporte_note = f"{aporte_quote:g} {quote}"
    try:
        candles = await hub.okx.get_candles(inst_id, bar=bar, days=days, limit=800)
        if body.aporte_ccy == "USDT" and quote not in {"USDT", "USD", "USDC"}:
            tickers = await hub.okx.get_ticker_map()
            fx = hub.okx.avg_cost_in_quote(1.0, quote, tickers)
            if not fx or fx <= 0:
                raise OkxError(f"não foi possível converter USDT → {quote}")
            aporte_quote = float(body.aporte) * fx
            aporte_note = f"{body.aporte:g} USDT ≈ {aporte_quote:.2f} {quote}"
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc

    ranked = lab_sim.rank_strategies_on_candles(
        catalog,
        candles,
        inst_id=inst_id,
        aporte_quote=aporte_quote,
        days=days,
        aporte_input=body.aporte,
        aporte_ccy=body.aporte_ccy,
        sort=body.sort,
    )
    best = ranked[0] if ranked else None
    approved = [r for r in ranked if (r.get("summary") or {}).get("recommend_create")]
    try:
        icon, alt = icon_urls(base)
    except Exception:
        icon, alt = None, None
    return {
        "ok": True,
        "inst_id": inst_id,
        "base": base,
        "quote": quote,
        "days": days,
        "bar": bar,
        "candles": len(candles),
        "aporte": body.aporte,
        "aporte_ccy": body.aporte_ccy,
        "aporte_note": aporte_note,
        "sort": body.sort,
        "icon": icon,
        "icon_alt": alt,
        "best_id": (best or {}).get("strategy", {}).get("id"),
        "approved_count": len(approved),
        "results": ranked,
    }


@app.post("/api/lab/simulate")
async def lab_simulate(body: LabSimulate) -> dict[str, Any]:
    """Backtest independente de bot. Só simulação — não persiste."""
    days = int(body.days)
    bar = lab_sim.bar_for_days(days)
    inst_id = body.inst_id.strip().upper()
    try:
        base, quote = parse_inst(inst_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    name = (body.name or f"Lab {base}").strip() or f"Lab {base}"
    cfg = BotConfig(
        bot_id="lab",
        name=name,
        inst_id=inst_id,
        buy_pct=body.buy_pct,
        profit_target_pct=body.profit_target_pct,
        fee_rate_pct=body.fee_rate_pct,
        quote_amount=body.aporte,
    )

    aporte_quote = float(body.aporte)
    aporte_note = f"{aporte_quote:g} {quote}"
    try:
        candles = await hub.okx.get_candles(inst_id, bar=bar, days=days, limit=800)
        if body.aporte_ccy == "USDT" and quote not in {"USDT", "USD", "USDC"}:
            tickers = await hub.okx.get_ticker_map()
            fx = hub.okx.avg_cost_in_quote(1.0, quote, tickers)
            if not fx or fx <= 0:
                raise OkxError(f"não foi possível converter USDT → {quote}")
            aporte_quote = float(body.aporte) * fx
            aporte_note = f"{body.aporte:g} USDT ≈ {aporte_quote:.2f} {quote}"
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc

    result = lab_sim.simulate(cfg, candles, fee_rate=cfg.fee_rate, quote_amount=aporte_quote, days=days)
    result["days"] = days
    result["bar"] = bar
    result["aporte_input"] = body.aporte
    result["aporte_ccy"] = body.aporte_ccy
    result["aporte_note"] = aporte_note
    result["inst_id"] = inst_id
    result["params"] = {
        "inst_id": inst_id,
        "buy_pct": body.buy_pct,
        "profit_target_pct": body.profit_target_pct,
        "fee_rate_pct": body.fee_rate_pct,
        "aporte": body.aporte,
        "aporte_ccy": body.aporte_ccy,
        "days": days,
    }
    try:
        icon, alt = icon_urls(base)
    except Exception:
        icon, alt = None, None
    result["icon"] = icon
    result["icon_alt"] = alt
    return result


@app.get("/api/portfolio")
async def get_portfolio() -> dict[str, Any]:
    if not credentials.configured():
        raise HTTPException(400, "cadastre as API Keys primeiro")
    data = portfolio.snapshot()
    if data.get("total_eq") is None and not data.get("last_error"):
        try:
            data = await portfolio.refresh_now()
        except OkxError as exc:
            raise HTTPException(502, str(exc)) from exc
    return data


@app.get("/api/fx")
async def get_fx(pair: str = "USDT-BRL") -> dict[str, Any]:
    """Cotação pública (sem credenciais) para exibir PnL em BRL."""
    wanted = (pair or "USDT-BRL").upper()
    try:
        tickers = await hub.okx.get_ticker_map()
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc
    rate = None
    if wanted == "USDT-BRL":
        rate = PortfolioWatcher._usdt_brl_rate(tickers)
    return {"pair": wanted, "rate": rate}


@app.post("/api/portfolio/refresh")
async def refresh_portfolio() -> dict[str, Any]:
    if not credentials.configured():
        raise HTTPException(400, "cadastre as API Keys primeiro")
    try:
        data = await portfolio.refresh_now()
        for row in db.list_bots():
            try:
                await hub.get(row["bot_id"]).refresh_token_view(force=True)
            except OkxError:
                pass
        return data
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.get("/api/portfolio/history")
async def portfolio_history(
    limit: int = 500,
    days: int = 45,
    daily: bool = True,
    refresh: int = 0,
) -> dict[str, Any]:
    """Histórico de saldo gravado pelo bot (cache 1 dia).

    A OKX não expõe na API o gráfico de patrimônio — só o saldo atual.
    """
    if not credentials.configured():
        raise HTTPException(400, "cadastre as API Keys primeiro")
    days_n = max(1, min(int(days), 180))
    grain = "hour" if days_n <= 7 else "day"
    cache_key = f"eq_hist|{grain}|{days_n}"
    if not refresh:
        hit = db.get_api_cache(cache_key, _EQ_HIST_TTL_S)
        if hit:
            payload = dict(hit["payload"])
            payload["cached"] = True
            payload["cache_age_s"] = round(time.time() - float(hit["ts"]), 1)
            return payload
    if daily:
        points = db.list_portfolio_series(days=days_n, grain=grain)
    else:
        points = db.list_portfolio_history(limit)
    payload = {
        "points": points,
        "daily": bool(daily),
        "grain": grain if daily else "raw",
        "days": days_n,
        "source": "local_snapshots",
        "okx_has_balance_history": False,
        "cached": False,
        "cache_age_s": 0,
        "note": "A OKX não entrega gráfico de patrimônio na API; o gráfico usa snapshots locais. O PnL Hoje/Semana/Mês/24h usa histórico de preços da OKX.",
    }
    if daily:
        db.set_api_cache(cache_key, payload, kind=_EQ_HIST_CACHE_KIND)
    return payload


def _require_keys() -> None:
    if not credentials.configured():
        raise HTTPException(400, "cadastre as API Keys primeiro")


async def _ensure_inst_ok(inst_id: str) -> None:
    inst = (inst_id or "").strip().upper()
    try:
        parse_inst(inst)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    try:
        await hub.okx.ensure_spot_instrument(inst)
        if not await hub.okx.is_spot_tradable_for_account(inst):
            raise HTTPException(
                400,
                "Este par ou cripto não pode ser negociado na sua região por restrições de compliance local da OKX.",
            )
    except OkxError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/orders/context")
async def order_context(instId: str = "BTC-USDT") -> dict[str, Any]:
    _require_keys()
    inst = instId.strip().upper()
    try:
        base, quote = parse_inst(inst)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    try:
        ticker = await hub.okx.get_ticker(inst)
        instrument = await hub.okx.ensure_spot_instrument(inst)
        account = await hub.okx.get_trading_account()
        funding = await hub.okx.get_funding_balances()
        tickers = await hub.okx.get_ticker_map()
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc

    def _fund(ccy: str) -> float:
        for item in funding or []:
            if str(item.get("ccy") or "").upper() == ccy.upper():
                return hub.okx._f(item.get("availBal") or item.get("bal")) or 0.0
        return 0.0

    details = {str(i.get("ccy") or "").upper(): i for i in (account.get("details") or [])}
    base_row = details.get(base) or {}
    quote_row = details.get(quote) or {}
    detail = hub.okx._ccy_from_item(base, base_row) if base_row else hub.okx._empty_ccy(base)
    icon, alt = icon_urls(base)
    avg_raw = detail.get("avg_px")
    avg_quote = hub.okx.avg_cost_in_quote(avg_raw, quote, tickers)
    return {
        "inst_id": inst,
        "base": base,
        "quote": quote,
        "icon": icon,
        "icon_alt": alt,
        "last": hub.okx._f(ticker.get("last")),
        "bid": hub.okx._f(ticker.get("bidPx")),
        "ask": hub.okx._f(ticker.get("askPx")),
        "min_sz": instrument.get("minSz"),
        "lot_sz": instrument.get("lotSz"),
        "tick_sz": instrument.get("tickSz"),
        "base_avail": hub.okx._f(base_row.get("availBal")) or 0.0,
        "quote_avail": hub.okx._f(quote_row.get("availBal")) or 0.0,
        "base_funding": _fund(base),
        "quote_funding": _fund(quote),
        "token_avg": avg_raw,
        "token_avg_quote": avg_quote,
        "token_qty": detail.get("qty"),
        "token_upl": detail.get("upl"),
        "token_upl_pct": (float(detail["upl_ratio"]) * 100.0) if detail.get("upl_ratio") is not None else None,
        "high24": hub.okx._f(ticker.get("high24h")),
        "low24": hub.okx._f(ticker.get("low24h")),
        "open24": hub.okx._f(ticker.get("open24h")),
        "vol24": hub.okx._f(ticker.get("volCcy24h")),
        "chg24": (
            ((hub.okx._f(ticker.get("last")) - hub.okx._f(ticker.get("open24h"))) / hub.okx._f(ticker.get("open24h")))
            * 100.0
            if hub.okx._f(ticker.get("last")) and hub.okx._f(ticker.get("open24h"))
            else None
        ),
    }


@app.get("/api/orders/open")
async def open_orders(instId: Optional[str] = None) -> dict[str, Any]:
    _require_keys()
    try:
        orders = await hub.okx.list_pending(instId.strip().upper() if instId else None)
        return {"orders": db.attach_origins(await hub.okx.enrich_orders(orders))}
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.get("/api/orders/history")
async def order_history(
    instId: Optional[str] = None,
    limit: int = 1000,
    period: str = "30d",
    side: str = "all",
    status: str = "all",
    refresh: int = 0,
) -> dict[str, Any]:
    """Histórico: período (1h…1A) · lado · status · cache ~5 min."""
    _require_keys()
    period_map = {
        "1h": (1 / 24, "1H"),
        "24h": (1, "24h"),
        "7d": (7, "7D"),
        "30d": (30, "1M"),
        "90d": (90, "3M"),
        "180d": (180, "6M"),
        "365d": (365, "1A"),
        # legado
        "1d": (1, "24h"),
        "day": (1, "24h"),
        "1m": (30, "1M"),
        "month": (30, "1M"),
        "6m": (180, "6M"),
        "1y": (365, "1A"),
        "year": (365, "1A"),
    }
    key = (period or "30d").strip().lower()
    if key not in period_map:
        raise HTTPException(400, "period inválido — use 1h, 24h, 7d, 30d, 90d, 180d ou 365d")
    side_key = (side or "all").strip().lower()
    if side_key not in {"all", "buy", "sell"}:
        raise HTTPException(400, "side inválido — use all, buy ou sell")
    status_key = (status or "all").strip().lower()
    if status_key not in {"all", "filled", "canceled"}:
        raise HTTPException(400, "status inválido — use all, filled ou canceled")
    days, label = period_map[key]
    period_out = key if key in {"1h", "24h", "7d", "30d", "90d", "180d", "365d"} else (
        "24h" if days <= 1 else "30d" if days <= 30 else "90d" if days <= 90 else "180d" if days <= 180 else "365d"
    )
    okx_max_days = 90
    capped = days > okx_max_days
    fetch_days = min(days, okx_max_days)
    cap = max(1, min(int(limit), 3000))
    inst = instId.strip().upper() if instId else None
    cache_key = f"{period_out}|{inst or '*'}|{fetch_days}|{cap}"
    force = int(refresh or 0) == 1

    try:
        hit = None if force else _hist_cache_get(cache_key)
        if hit:
            base = dict(hit["payload"])
            orders = list(base.get("orders") or [])
            cached = True
            age_s = round(time.time() - float(hit["ts"]), 1)
        else:
            raw = await hub.okx.list_history(inst, limit=cap, days=fetch_days)
            orders = db.attach_origins(await hub.okx.enrich_orders(raw))
            note = None
            if capped:
                note = (
                    f"Pedido: {label}. A OKX só expõe ~3 meses de ordens — "
                    f"mostrando os últimos {fetch_days} dias disponíveis."
                )
            base = {
                "orders": orders,
                "period": period_out,
                "period_label": label,
                "days": days,
                "fetch_days": fetch_days,
                "capped": capped,
                "note": note,
                "limit": cap,
            }
            _hist_cache_set(cache_key, base)
            cached = False
            age_s = 0.0

        def status_group(state: Any) -> str:
            s = str(state or "").lower()
            if s in {"filled", "partially_filled"}:
                return "filled"
            if "cancel" in s:
                return "canceled"
            return s or "other"

        filtered = orders
        if side_key in {"buy", "sell"}:
            filtered = [o for o in filtered if str(o.get("side") or "").lower() == side_key]
        if status_key in {"filled", "canceled"}:
            filtered = [o for o in filtered if status_group(o.get("state")) == status_key]
        side_label = {"all": "todas", "buy": "compras", "sell": "vendas"}[side_key]
        status_label = {"all": "todos", "filled": "executadas", "canceled": "canceladas"}[status_key]
        return {
            **{k: v for k, v in base.items() if k != "orders"},
            "orders": filtered,
            "side": side_key,
            "side_label": side_label,
            "status": status_key,
            "status_label": status_label,
            "count": len(filtered),
            "count_total": len(orders),
            "cached": cached,
            "cache_ttl_s": int(_HIST_TTL_S),
            "cache_age_s": age_s,
        }
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.post("/api/orders")
async def create_order(body: OrderCreate) -> dict[str, Any]:
    _require_keys()
    inst = body.inst_id.strip().upper()
    try:
        await _ensure_inst_ok(inst)
        await _validate_manual_order(body)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    cl_ord_id = db.make_cl_ord_id("user")
    try:
        order = await hub.okx.place_order(
            inst,
            body.side,
            body.ord_type,
            body.sz,
            px=body.px,
            tgt_ccy=body.tgt_ccy,
            cl_ord_id=cl_ord_id,
        )
    except OkxError as exc:
        _raise_okx(exc)
    ord_id = str(order.get("ord_id") or order.get("ordId") or "")
    db.remember_order_origin(ord_id or None, origin="user", cl_ord_id=cl_ord_id)
    state = str(order.get("state") or "")
    if state in {"filled", "partially_filled"} or order.get("avg_px"):
        db.add_trade(
            side=body.side,
            inst_id=inst,
            qty=order.get("fill_sz") or order.get("sz"),
            avg_px=order.get("avg_px") or order.get("px"),
            fee=order.get("fee"),
            fee_ccy=order.get("fee_ccy"),
            fee_usdt=None,
            pnl_realized=None,
            order_id=ord_id or None,
            status=state or "filled",
            origin="user",
            cl_ord_id=cl_ord_id,
        )
    db.add_event(f"ordem {body.side} {body.ord_type} {inst} sz={body.sz} · usuário")
    order["origin"] = "user"
    order["origin_label"] = "Usuário"
    _hist_cache_clear()
    # Notificação de ordem criada/preenchida
    from .notifications import notify_order_filled
    notify_order_filled(
        current_user_id.get() or "_global",
        inst, body.side,
        float(order.get("fill_sz") or order.get("sz") or body.sz),
        float(order.get("avg_px") or order.get("px") or 0),
        quote=inst.split("-")[1] if "-" in inst else "USDT",
    )
    return order


@app.post("/api/orders/cancel")
async def cancel_order(body: OrderCancel) -> dict[str, Any]:
    _require_keys()
    try:
        result = await hub.okx.cancel_order(body.inst_id.strip().upper(), body.ord_id.strip())
    except OkxError as exc:
        _raise_okx(exc)
    if result.get("already_gone"):
        db.add_event(f"ordem {body.ord_id} já executada/cancelada")
    else:
        db.add_event(f"ordem cancelada {body.ord_id}")
    _hist_cache_clear()
    # Notificação de cancelamento
    from .notifications import notify_order_cancelled
    notify_order_cancelled(
        current_user_id.get() or "_global",
        body.inst_id.strip().upper(),
        "",
        reason="já executada" if result.get("already_gone") else "cancelada pelo usuário",
    )
    return result


@app.post("/api/orders/cancel-all")
async def cancel_all_orders(instId: Optional[str] = None) -> dict[str, Any]:
    _require_keys()
    try:
        result = await hub.okx.cancel_all_pending(instId.strip().upper() if instId else None)
    except OkxError as exc:
        _raise_okx(exc)
    gone = int(result.get("already_gone") or 0)
    canceled = int(result.get("canceled") or 0)
    failed = int(result.get("failed") or 0)
    if gone and not canceled and not failed:
        db.add_event(f"{gone} ordem(ns) já executada(s)/cancelada(s)")
    else:
        db.add_event(
            f"ordens: {canceled} cancelada(s)"
            + (f", {gone} já resolvida(s)" if gone else "")
            + (f", {failed} falha(s)" if failed else "")
        )
    _hist_cache_clear()
    return result


@app.get("/api/orders/{ord_id}")
async def get_order_detail(ord_id: str, instId: str = "") -> dict[str, Any]:
    """Busca detalhes de uma ordem na OKX (com cache até invalidar)."""
    _require_keys()
    oid = ord_id.strip()
    inst = instId.strip().upper() if instId else ""
    cache_key = f"order_detail|{oid}"
    hit = db.get_api_cache(cache_key, ttl_s=3600)
    if hit:
        return {"order": hit["payload"], "cached": True}
    try:
        from .okx_client import normalize_order
        # Se não temos instId, tentar achar nas pending/history recentes
        if not inst:
            try:
                pending = await hub.okx.list_pending()
                for o in pending:
                    if str(o.get("ordId") or "") == oid:
                        inst = str(o.get("instId") or "")
                        break
            except Exception:
                pass
        if not inst:
            # Tenta buscar do histórico 7d
            try:
                hist = await hub.okx.list_history(limit=100, days=7)
                for o in hist:
                    if str(o.get("ordId") or o.get("ord_id") or "") == oid:
                        inst = str(o.get("instId") or o.get("inst_id") or "")
                        break
            except Exception:
                pass
        if not inst:
            raise HTTPException(400, "instId necessário para buscar ordem na OKX")
        raw = await hub.okx.get_order(inst, oid)
        if raw:
            normalized = normalize_order(raw)
            enriched = await hub.okx.enrich_orders([normalized])
            result = db.attach_origins(enriched)[0] if enriched else normalized
            db.set_api_cache(cache_key, result, kind="order_detail")
            return {"order": result, "cached": False}
        raise HTTPException(404, "Ordem não encontrada")
    except OkxError as exc:
        _raise_okx(exc)


@app.get("/api/instruments/check")
async def check_instrument(instId: str) -> dict[str, Any]:
    inst = (instId or "").strip().upper()
    try:
        row = await hub.okx.ensure_spot_instrument(inst)
    except OkxError as exc:
        raise HTTPException(400, str(exc)) from exc
    base, quote = parse_inst(inst)
    return {"ok": True, "inst_id": inst, "base": base, "quote": quote, "min_sz": row.get("minSz")}


@app.get("/api/instruments/resolve")
async def resolve_instrument(base: str, quote: str = "") -> dict[str, Any]:
    """Encontra par spot válido para um token (ex. RE → RE-USDT se RE-BRL não existir)."""
    sym = (base or "").strip().upper()
    if not sym:
        raise HTTPException(400, "base obrigatório")
    if sym == "BRL":
        return {"inst_id": "USDT-BRL", "base": "USDT", "quote": "BRL"}
    if sym in {"USDT", "USDC", "USD", "DAI"}:
        q = (quote or "USDT").upper()
        inst = f"BTC-{q}" if q != sym else "BTC-USDT"
        await _ensure_inst_ok(inst)
        b, qq = parse_inst(inst)
        return {"inst_id": inst, "base": b, "quote": qq}
    candidates: list[str] = []
    pref = (quote or "").strip().upper()
    if pref:
        candidates.append(f"{sym}-{pref}")
    for q in ("USDT", "USDC", "BRL"):
        cand = f"{sym}-{q}"
        if cand not in candidates:
            candidates.append(cand)
    last_err: str | None = None
    for inst in candidates:
        try:
            row = await hub.okx.ensure_spot_instrument(inst)
            b, qq = parse_inst(inst)
            return {
                "inst_id": inst,
                "base": b,
                "quote": qq,
                "min_sz": row.get("minSz"),
                "candidates_tried": candidates,
            }
        except OkxError as exc:
            last_err = str(exc)
            continue
    raise HTTPException(
        400,
        last_err or f"Nenhum par spot para {sym} (tentou: {', '.join(candidates)}). Use RE-USDT na OKX.",
    )


@app.get("/api/instruments")
async def instruments(q: str = "", quote: str = "USDT") -> dict[str, Any]:
    try:
        pairs = await hub.okx.list_spot_pairs(quote=quote, query=q)
        q_clean = (q or "").strip()
        quote_u = (quote or "ALL").upper()
        if q_clean or quote_u in {"ALL", "*", ""}:
            limit = 300
        else:
            limit = 80
        return {
            "quote": quote_u,
            "q": q_clean,
            "count": len(pairs),
            "instruments": pairs[:limit],
            "market": "spot",
            "inst_type": "SPOT",
        }
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.get("/api/candles")
async def candles(
    instId: str,
    bar: str = "1D",
    days: float = 365,
    limit: int = 400,
    refresh: int = 0,
) -> dict[str, Any]:
    inst = (instId or "").strip().upper()
    if not inst:
        raise HTTPException(400, "instId obrigatório")
    days_f = max(1 / 96, min(float(days), 365.0))  # mín. ~15 min
    limit = max(20, min(int(limit), 800))
    # Case-sensitive na OKX: 1m = minuto, 1M = mês
    bar = (bar or "1D").strip()
    if bar == "1M":
        bar = "1D"
    cache_key = f"candles|{inst}|{bar}|{days_f}|{limit}"
    # 1m/5m/15m mudam rápido — cache curto
    ttl = 60.0 if bar in {"1m", "5m", "15m"} else _CANDLES_TTL_S
    if not refresh:
        hit = db.get_api_cache(cache_key, ttl)
        if hit:
            payload = dict(hit["payload"])
            payload["cached"] = True
            payload["cache_age_s"] = round(time.time() - float(hit["ts"]), 1)
            return payload
    try:
        rows = await hub.okx.get_candles(inst, bar=bar, days=days_f, limit=limit)
        # Sem candles de 1m → tenta 15m
        used_bar = bar
        if not rows and bar == "1m":
            used_bar = "15m"
            rows = await hub.okx.get_candles(inst, bar=used_bar, days=days_f, limit=limit)
            cache_key = f"candles|{inst}|{used_bar}|{days_f}|{limit}"
        payload = {
            "inst_id": inst,
            "bar": used_bar,
            "days": days_f,
            "candles": rows,
            "cached": False,
            "cache_age_s": 0,
        }
        db.set_api_cache(cache_key, payload, kind=_CANDLES_CACHE_KIND)
        return payload
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.get("/api/hunter")
async def hunter_status() -> dict[str, Any]:
    cfg = db.get_hunter_settings()
    return {
        "settings": cfg,
        "watching": False,
        "last_error": hunter.last_error,
        "last_scan": hunter.last_scan,
        "bot": None,
        "rotations": [],
        "mode": "radar",
    }


@app.put("/api/hunter/settings")
async def hunter_settings_put(body: HunterSettingsUpdate) -> dict[str, Any]:
    patch = body.model_dump(exclude_none=True)
    # Força radar: sem automação
    patch["enabled"] = False
    patch["auto_rotate"] = False
    saved = db.save_hunter_settings(patch)
    db.clear_api_cache(kind="hunter_scan")
    return {"settings": saved}


@app.get("/api/hunter/scan")
async def hunter_scan(refresh: int = 0) -> dict[str, Any]:
    try:
        data = await hunter.scan_now(force=int(refresh or 0) == 1)
        return data
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.post("/api/hunter/apply")
async def hunter_apply(body: HunterApply) -> dict[str, Any]:
    raise HTTPException(
        410,
        "Automação do Caçador removida. Use «Criar bot» com a melhor estratégia sugerida.",
    )


@app.post("/api/hunter/start")
async def hunter_start_auto() -> dict[str, Any]:
    cfg = db.save_hunter_settings({"enabled": True})
    return {"ok": True, "settings": cfg, "mode": "radar"}


@app.post("/api/hunter/stop")
async def hunter_stop_auto() -> dict[str, Any]:
    cfg = db.save_hunter_settings({"enabled": False})
    return {"ok": True, "settings": cfg, "mode": "radar"}


@app.get("/api/assistant/status")
async def assistant_status() -> dict[str, Any]:
    from . import assistant as copilot

    provider = copilot.llm_provider() if copilot.llm_enabled() else "local"
    if not copilot.llm_enabled():
        provider = "local"
    elif copilot.llm_provider() != "openai":
        provider = "cursor"
    else:
        provider = "openai"
    return {
        "ok": True,
        "llm": copilot.llm_enabled(),
        "provider": provider,
        "mode": "llm" if copilot.llm_enabled() else "local",
    }


@app.post("/api/assistant/chat")
async def assistant_chat(body: AssistantChat) -> dict[str, Any]:
    from . import assistant as copilot

    try:
        return await copilot.handle(
            body.message,
            history=body.history or [],
            draft=body.draft,
            okx=hub.okx if credentials.configured() else None,
            portfolio=portfolio.snapshot(),
        )
    except Exception as exc:
        raise HTTPException(400, str(exc) or "não entendi o pedido") from exc


@app.get("/api/health/okx")
async def health_okx() -> dict[str, Any]:
    try:
        info = await hub.okx.health()
        # Taxa spot de referência (não depende de bot fantasma)
        fee = await hub.okx.get_trade_fee("BTC-USDT")
        if fee is not None:
            info["taker_fee_pct"] = fee * 100.0
        return info
    except OkxError as exc:
        raise HTTPException(502, str(exc)) from exc


# ---------------------------------------------------------------------------
# Notificações em tempo real (SSE)
# ---------------------------------------------------------------------------

from starlette.responses import StreamingResponse
from .notifications import hub as notif_hub


@app.get("/api/notifications/stream")
async def notifications_stream(request: Request):
    """SSE stream de notificações para o usuário autenticado."""
    user_id = current_user_id.get() or "_global"
    queue = notif_hub.subscribe(user_id)

    async def event_generator():
        try:
            # Heartbeat inicial
            yield "event: connected\ndata: {}\n\n"
            while True:
                # Esperar notificação ou timeout (heartbeat a cada 30s)
                try:
                    notif = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield notif.to_sse()
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                # Checar se o cliente desconectou
                if await request.is_disconnected():
                    break
        finally:
            notif_hub.unsubscribe(user_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/notifications")
async def notifications_list(limit: int = 30) -> dict[str, Any]:
    """Histórico de notificações recentes."""
    user_id = current_user_id.get() or "_global"
    items = notif_hub.history(user_id, limit=limit)
    unread = notif_hub.unread_count(user_id)
    return {"items": items, "unread": unread}


@app.post("/api/notifications/read")
async def notifications_mark_read(body: dict[str, Any] = {}) -> dict[str, Any]:
    """Marcar notificações como lidas."""
    user_id = current_user_id.get() or "_global"
    notif_id = body.get("id")  # None = marcar todas
    notif_hub.mark_read(user_id, notif_id)
    return {"ok": True, "unread": notif_hub.unread_count(user_id)}
