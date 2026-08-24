"""Copiloto: linguagem natural → proposta de ação (nunca executa sozinho)."""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import tempfile
from typing import Any, Optional

import httpx

from .config import settings

_ALIASES = {
    "btc": "BTC",
    "bitcoin": "BTC",
    "eth": "ETH",
    "ethereum": "ETH",
    "sol": "SOL",
    "solana": "SOL",
    "xrp": "XRP",
    "ripple": "XRP",
    "doge": "DOGE",
    "pepe": "PEPE",
    "bnb": "BNB",
    "ada": "ADA",
    "avax": "AVAX",
    "link": "LINK",
    "sui": "SUI",
    "ton": "TON",
    "dot": "DOT",
    "matic": "POL",
    "pol": "POL",
    "shib": "SHIB",
    "ltc": "LTC",
    "bch": "BCH",
    "uni": "UNI",
    "near": "NEAR",
    "atom": "ATOM",
    "apt": "APT",
    "trx": "TRX",
    "fil": "FIL",
}

_QUOTES = ("USDT", "USDC", "USD", "BRL")


_STOP_WORDS = {
    "usdt", "usdc", "usd", "brl", "bot", "bots", "tudo", "todo", "todos", "mercado",
    "plano", "planos", "depois", "depois", "comprar", "compra", "compre", "vender",
    "venda", "vende", "troca", "trocar", "por", "para", "pra", "com", "meu", "minha",
    "o", "a", "os", "as", "de", "do", "da", "em", "no", "na", "um", "uma", "e", "ou",
    "ordem", "limite", "limit", "valor", "alto", "alta", "grande", "pnl", "preco", "preço",
}


def _llm_system(ctx: str = "", draft: dict[str, Any] | None = None) -> str:
    draft_txt = json.dumps(draft, ensure_ascii=False) if draft else "{}"
    return (
        "Você é o Copiloto do OKBot — um assistente Spot OKX completo. "
        "Você TEM AUTONOMIA para executar todas as funções do app via conversa: "
        "listar tokens, mostrar saldos, cotações, bots, ordens abertas, histórico, PnL. "
        "Quando o usuário perguntar algo, RESPONDA COM OS DADOS no reply (não diga 'vá na página X'). "
        "Use os números do contexto da conta abaixo. Nunca invente dados.\n\n"
        "REGRAS DE COMPORTAMENTO:\n"
        "1. Se o usuário pedir 'meus tokens' ou 'minha carteira', LISTE TODOS os tokens com saldo, "
        "quantidade e valor em USD no reply. Adicione action navigate para quem quiser ver mais.\n"
        "2. Se o usuário pedir cotação, responda com o preço.\n"
        "3. Se o usuário pedir para criar ordem mas faltar dados (token ou valor), "
        "LISTE os tokens da carteira dele e PERGUNTE qual usar e quanto.\n"
        "4. Se o usuário pedir ordens abertas ou histórico, use intent=list_orders ou intent=order_history.\n"
        "5. Se o usuário pedir bots, liste os bots ativos com status.\n"
        "6. Seja PROATIVO: sugira ações baseado nos dados da carteira.\n"
        "7. Nunca execute ordem sozinho — proponha e o usuário confirma.\n\n"
        "Responda SOMENTE JSON válido, sem markdown:\n"
        '{"reply":"texto rico em português com dados concretos (saldos, preços, listas)","intent":"advise|plan|buy|sell|create_bot|wallet|price|'
        'list_bots|start_bot|stop_bot|open_hunter|list_orders|order_history|help|unknown","token":"SOL","quote":"USDT",'
        '"amount":50,"amount_kind":"quote|base|all|pct","pct":null,"ord_type":"limit|market",'
        '"px":null,"buy_pct":3,'
        '"profit_target_pct":1,"draft":{"from_token":"PEPE","from_kind":"all","from_pct":100,'
        '"to":[{"token":"SOL","pct":60},{"token":"ETH","pct":40}],"quote":"USDT",'
        '"also_bots":false,"buy_pct":3,"profit_target_pct":1},"steps":[]}\n\n'
        "INTENTS:\n"
        "- wallet = listar tokens/saldos. INCLUA A LISTA COMPLETA no reply.\n"
        "- price = cotação de um token.\n"
        "- buy/sell = montar ordem. Se faltar token, liste as opções da carteira no reply e pergunte.\n"
        "- plan = giro multi-step (vender A, comprar B e C).\n"
        "- create_bot = criar bot DCA.\n"
        "- start_bot/stop_bot = iniciar/pausar bot.\n"
        "- list_bots = listar bots ativos.\n"
        "- list_orders = mostrar ordens abertas.\n"
        "- order_history = histórico de ordens.\n"
        "- open_hunter = abrir radar de dips.\n"
        "- advise = análise/sugestão sem ação.\n"
        "- help = ajuda geral.\n\n"
        "QUANDO O USUÁRIO PEDIR ORDEM SEM ESPECIFICAR TOKEN:\n"
        "No reply, liste os tokens disponíveis na carteira dele com saldos e pergunte qual usar. "
        "NÃO diga apenas 'Qual token?'. Mostre as opções reais.\n\n"
        "QUANDO O USUÁRIO PERGUNTAR 'QUAIS MEUS TOKENS' OU 'MINHA CARTEIRA':\n"
        "intent=wallet. No reply inclua a lista formatada com: Token | Quantidade | Valor USD.\n\n"
        "QUANDO O USUÁRIO PEDIR PARA 'COMPENSAR PERDA' OU 'ZERAR PNL' OU 'VENDER PARA RECUPERAR':\n"
        "IMPORTANTE: isso é intent=sell, NÃO advise! O usuário quer uma ORDEM.\n"
        "1. Identifique o token no prejuízo (UPL negativo) usando os dados do contexto.\n"
        "2. Calcule o preço de break-even: break_even = custo_medio * (1 + taxa_venda).\n"
        "   Taxa de venda OKX spot ≈ 0.1% (0.001). Então: break_even = custo_medio * 1.001.\n"
        "3. Se o UPL% é -10%, para zerar: preço_venda = custo_medio * 1.001.\n"
        "   Para COMPENSAR 100% da perda vendendo TUDO: preço = custo_medio * 1.001.\n"
        "   Para compensar vendendo PARCIAL: preço precisa ser MAIOR (break_even / fração_vendida).\n"
        "4. SEMPRE use intent=sell, ord_type=limit, px=break_even calculado, amount_kind=all (ou base), amount=qty total do token.\n"
        "5. No reply, explique: custo médio, preço break-even, e que a ordem limite só executa se o preço subir.\n"
        "6. Se o preço atual está ABAIXO do break-even, avise que a ordem ficará pendente até o preço subir.\n"
        "7. Pergunte se quer vender tudo ou uma parte (e ajuste o preço se parcial).\n\n"
        "REGRA CRÍTICA: Se o usuário menciona 'ordem', 'compensar', 'recuperar', 'zerar' junto com um token,\n"
        "NUNCA use intent=advise. Use intent=sell com ord_type=limit e px=break_even.\n"
        "Se o usuário responde apenas o nome do token (ex: 'de XRP', 'XRP', 'do xrp') após pedir ordem/compensar,\n"
        "MANTENHA o intent=sell da conversa anterior e use o token informado.\n\n"
        f"Contexto da conta (USE ESSES DADOS NAS RESPOSTAS):\n{ctx or 'indisponível'}\n\n"
        f"Rascunho atual do plano:\n{draft_txt}"
    )


def _cursor_key() -> str:
    key = (settings.cursor_api_key or os.environ.get("CURSOR_API_KEY") or "").strip()
    if key:
        return key
    alt = (settings.llm_api_key or "").strip()
    if alt.startswith(("github_pat_", "ghp_", "gho_", "github_pat_")):
        return ""
    if alt.startswith(("key_", "crsr_", "cursor_")):
        return alt
    return ""


def llm_provider() -> str:
    return (settings.llm_provider or "cursor").strip().lower()


def llm_enabled() -> bool:
    if llm_provider() == "openai":
        return bool((settings.llm_api_key or "").strip())
    return bool(_cursor_key() and shutil.which(settings.cursor_bin or "cursor"))


def _num(raw: str | None) -> Optional[float]:
    if raw is None:
        return None
    s = str(raw).strip().replace(" ", "").replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    return v if v > 0 else None


def _norm(text: str) -> str:
    t = (text or "").strip().lower()
    t = t.replace("r$", " brl ").replace("$", " usd ")
    t = re.sub(r"[!?]+", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _guess_quote(text: str) -> str:
    t = _norm(text)
    if re.search(r"\b(brl|reais?|real)\b", t):
        return "BRL"
    if re.search(r"\b(usdc)\b", t):
        return "USDC"
    return "USDT"


def _guess_token(text: str) -> Optional[str]:
    t = _norm(text)
    m = re.search(r"\b([a-z0-9]{2,12})-(usdt|usdc|usd|brl)\b", t)
    if m:
        return m.group(1).upper()
    for key, ccy in _ALIASES.items():
        if re.search(rf"\b{re.escape(key)}\b", t):
            return ccy
    m = re.search(
        r"\b(?:de|do|da|em|o|a)\s+([a-z]{2,10})\b",
        t,
    )
    if m:
        raw = m.group(1)
        if raw not in _STOP_WORDS:
            return _ALIASES.get(raw, raw.upper())
    return None


def _tokens_in(text: str) -> list[str]:
    t = _norm(text)
    found: list[str] = []
    for key, ccy in sorted(_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(key)}\b", t) and ccy not in found:
            found.append(ccy)
    for m in re.finditer(r"\b([a-z]{2,10})\b", t):
        raw = m.group(1)
        if raw in _STOP_WORDS:
            continue
        ccy = _ALIASES.get(raw, raw.upper())
        if ccy in found or len(ccy) > 10:
            continue
        if raw in _ALIASES or re.fullmatch(r"[a-z]{2,6}", raw):
            found.append(ccy)
    return found


def _looks_like_plan(t: str) -> bool:
    sell = bool(re.search(r"\b(vender?|venda|troc(?:a|ar)|gir(?:a|ar)|sair|desfazer|sair)\b", t))
    buy = bool(re.search(r"\b(compr(?:e|ar)|compra|por|entrar|aportar|giro)\b", t))
    if re.search(r"\btroc(?:a|ar)\b.+\b(por|em|pra|para)\b", t):
        return len(_tokens_in(t)) >= 2
    if re.search(r"\b(plano|roteiro|roteiro)\b.+\b(vender|compra|troca|gira)\b", t):
        return True
    return sell and buy and len(_tokens_in(t)) >= 2


def _looks_like_advise(t: str) -> bool:
    if _looks_like_plan(t):
        return False
    if re.search(r"\b(criar|cria|crie)\b.*\bbot\b", t):
        return False
    if re.search(r"\b(ordem|limite|limit)\b", t) and not re.search(r"\bqual\b", t):
        return False
    # "compensar perda" + token específico = ação, não conselho
    if re.search(r"\b(compens\w*|recuper\w*|zerar)\b", t) and _guess_token(t):
        return False
    # "abrir/criar ordem" = ação
    if re.search(r"\b(abrir|abra|crie|cria|criar|monte|quero)\b.*\bordem\b", t):
        return False
    return bool(
        re.search(
            r"\b(pnl|p&l|preju[ií]zo|compens|recuper|sugest|analis|o que (fazer|comprar|vender|eu)|"
            r"qual (seria|ordem|token)|deveria|como (voltar|recuperar|compens)|"
            r"melhor (ordem|par|token)|unrealized|upl)\b",
            t,
        )
        or re.search(r"\b(o que (você|voce) (faria|sugere|montaria))\b", t)
    )


def _confirm_utterance(t: str) -> bool:
    return bool(re.search(r"\b(sim|ok|pode|monta|monta|fecha|confirma|isso|vamos|fechou|bora|quero)\b", t))


def _draft_from_text(text: str) -> dict[str, Any]:
    t = _norm(text)
    toks = _tokens_in(t)
    frm = None
    dest: list[str] = []
    m = re.search(
        r"(?:vend(?:e|a|er)|troc(?:a|ar)|gir(?:a|ar)|sair(?:\s+de)?)\s+"
        r"(?:todo[s]?|tudo(?:\s+d[eo])?)?\s*(?:meu\s+)?"
        r"(?P<frm>[a-z0-9]{2,12}).{0,100}?"
        r"(?:compr(?:e|ar|a)|por|pra|para|em|entrar(?:\s+em)?)\s+(?P<to>.+)$",
        t,
    )
    if m:
        frm = _ALIASES.get(m.group("frm"), m.group("frm").upper())
        dest = _tokens_in(m.group("to"))
        dest = [x for x in dest if x != frm]
    if not frm and toks:
        frm = toks[0]
        dest = toks[1:]
    kind = "all"
    pct = None
    m_pct = re.search(r"(\d+(?:[.,]\d+)?)\s*%", t)
    if m_pct and not re.search(r"qued[ae]|lucro|alvo", t):
        kind = "pct"
        pct = _num(m_pct.group(1))
    if re.search(r"\b(tudo|todo[s]?|100\s*%)\b", t):
        kind = "all"
        pct = 100
    n = len(dest) or 1
    to = [{"token": x, "pct": round(100.0 / n, 2)} for x in dest]
    return {
        "from_token": frm,
        "from_kind": kind,
        "from_pct": pct if kind == "pct" else (100 if kind == "all" else None),
        "to": to,
        "quote": _guess_quote(text),
        "also_bots": bool(re.search(r"\bbots?\b", t)),
        "buy_pct": None,
        "profit_target_pct": None,
    }


def _merge_draft(prev: dict[str, Any] | None, incoming: dict[str, Any] | None, text: str) -> dict[str, Any]:
    out = dict(prev or {})
    nxt = incoming or {}
    for k in ("from_token", "from_kind", "from_pct", "quote", "also_bots", "buy_pct", "profit_target_pct"):
        if nxt.get(k) not in (None, "", [], "null"):
            out[k] = nxt[k]
    if nxt.get("to"):
        out["to"] = nxt["to"]
    t = _norm(text)
    toks = _tokens_in(t)
    if not out.get("from_token") and toks:
        out["from_token"] = toks[0]
    if (not out.get("to")) and toks:
        rest = [x for x in toks if x != out.get("from_token")]
        if rest:
            n = len(rest)
            out["to"] = [{"token": x, "pct": round(100.0 / n, 2)} for x in rest]
    # "70 sol 30 eth"
    pairs = re.findall(r"(\d+(?:[.,]\d+)?)\s*%?\s*(?:em|no|na|de)?\s*([a-z]{2,10})", t)
    assigned = []
    for num, raw in pairs:
        if raw in _STOP_WORDS:
            continue
        tok = _ALIASES.get(raw, raw.upper())
        assigned.append({"token": tok, "pct": _num(num)})
    if assigned and sum(float(x.get("pct") or 0) for x in assigned) > 0:
        out["to"] = assigned
        if not out.get("from_token"):
            leftover = [x for x in toks if x not in {a["token"] for a in assigned}]
            if leftover:
                out["from_token"] = leftover[0]
    if re.search(r"\b(50/?50|meio a meio|igual|partes iguais)\b", t) and out.get("to"):
        n = len(out["to"])
        out["to"] = [{"token": x["token"], "pct": round(100.0 / n, 2)} for x in out["to"]]
    return out


def _draft_complete(d: dict[str, Any] | None) -> bool:
    if not d or not d.get("from_token"):
        return False
    to = d.get("to") or []
    return bool(to) and all(x.get("token") for x in to)


def _draft_missing(d: dict[str, Any] | None) -> str:
    if not d or not d.get("from_token"):
        return "Qual token você quer vender (ou de qual sair)?"
    to = d.get("to") or []
    if not to:
        return f"Com o valor de {d['from_token']}, o que você quer comprar? Pode ser mais de um, ex.: «60% SOL e 40% ETH»."
    return ""


def parse_local(text: str) -> dict[str, Any]:
    t = _norm(text)
    intent = "unknown"
    if _looks_like_plan(t):
        intent = "plan"
    elif re.search(r"\b(criar|cria|monte|montar|plano|bot)\b", t) and re.search(
        r"\b(bot|plano|queda|cair|lucro|vender?|comprar?)\b", t
    ):
        if re.search(r"\b(criar|cria|monte|montar|plano)\b", t) and not _looks_like_plan(t):
            intent = "create_bot"
    if intent == "unknown":
        if _looks_like_plan(t):
            intent = "plan"
        elif re.search(r"\b(vender?|venda|sell|desfazer)\b", t):
            intent = "sell"
        elif re.search(r"\b(compr(?:e|ar)|compra|buy|aportar)\b", t):
            intent = "buy"
        elif re.search(r"\b(ordem|limite|limit)\b.*\b(compens\w*|recuper\w*|zerar|perda|preju[ií]zo)\b", t):
            intent = "sell"
        elif re.search(r"\b(compens\w*|recuper\w*|zerar)\b.*\b(perda|preju[ií]zo|pnl|upl)\b", t) and _guess_token(text):
            intent = "sell"
        elif re.search(
            r"\b(ordem|limite|limit)\b|\b(abrir|abra|crie|cria|criar|monte)\b.{0,20}\bordem\b",
            t,
        ) and _guess_token(text) and _guess_token(text) not in {"ORDEM", "LIMITE", "VALOR"}:
            intent = "sell" if re.search(r"\b(vender?|venda|sell)\b", t) else "buy"
        elif re.search(r"\b(iniciar|ligar|start|play)\b.*\bbot\b|\bbot\b.*\b(iniciar|ligar)\b", t):
            intent = "start_bot"
        elif re.search(r"\b(pausar|parar|pause|stop)\b.*\bbot\b", t):
            intent = "stop_bot"
        elif re.search(r"\b(meus bots|listar? (os )?bots|quais bots)\b", t):
            intent = "list_bots"
        elif re.search(r"\b(saldo|carteira|quanto tenho|quanto eu tenho|wallet|meus tokens|tokens dispon[ií]veis)\b", t):
            intent = "wallet"
        elif re.search(r"\b(ordens? aberta|pending|ordens? pendente)\b", t):
            intent = "list_orders"
        elif re.search(r"\b(hist[oó]rico|[uú]ltimas? ordens?|ordens? (feita|executada|passada))\b", t):
            intent = "order_history"
        elif re.search(r"\b(preço|preco|cotação|cotacao|quanto (está|esta|tá|ta))\b", t):
            intent = "price"
        elif re.search(r"\b(caçador|cacador|hunter|radar|dip)\b", t):
            intent = "open_hunter"
        elif _looks_like_advise(t):
            intent = "advise"
        elif re.search(r"\b(ajuda|help)\b", t):
            intent = "help"

    amount_kind = "quote"
    amount = None
    pct = None
    if re.search(r"\b(tudo|todo[s]?|inteiro|100\s*%|todo o saldo)\b", t):
        amount_kind = "all"
    else:
        m_pct = re.search(r"(\d+(?:[.,]\d+)?)\s*%", t)
        if m_pct and intent in {"sell", "buy"}:
            amount_kind = "pct"
            pct = _num(m_pct.group(1))
        else:
            m_amt = re.search(
                r"(\d+(?:[.,]\d+)?)\s*(usdt|usdc|usd|brl|reais?|d[oó]lares?)?(?!\s*%)",
                t,
            )
            if m_amt:
                amount = _num(m_amt.group(1))
                unit = (m_amt.group(2) or "").lower()
                if intent == "sell" and unit not in {"usdt", "usdc", "usd", "brl", "reais", "real", "dolares", "dólares"}:
                    # "vender 0.5 sol" → base
                    if unit in {"", None} and intent == "sell":
                        after = t[m_amt.end() :].strip()
                        if re.match(r"^(de\s+)?[a-z]{2,10}\b", after) or True:
                            # if next word is a token, it's base qty
                            nxt = re.match(r"(?:de\s+)?([a-z]{2,10})\b", after)
                            if nxt and nxt.group(1) not in {"usdt", "usdc", "usd", "brl", "reais", "real"}:
                                amount_kind = "base"
                if unit in {"usdt", "usdc", "usd", "brl", "reais", "real", "dolares", "dólares"}:
                    amount_kind = "quote"

    buy_pct = None
    m_buy = re.search(r"qued[ae]\s*(?:de\s*)?(\d+(?:[.,]\d+)?)\s*%", t)
    if m_buy:
        buy_pct = _num(m_buy.group(1))
        if intent == "unknown":
            intent = "create_bot"
    profit = None
    m_p = re.search(r"(?:lucro|alvo|vender?\s+com)\s*(?:de\s*)?(\d+(?:[.,]\d+)?)\s*%", t)
    if m_p:
        profit = _num(m_p.group(1))
        if intent == "unknown":
            intent = "create_bot"

    ord_type = "market"
    if re.search(r"\b(mercado|market)\b", t):
        ord_type = "market"
    elif re.search(r"\b(limite|limit|post.?only|ioc|fok)\b", t) or re.search(r"\bordem\b", t):
        ord_type = "post_only" if re.search(r"\bpost.?only\b", t) else "limit"
    m_px = re.search(r"(?:pre[cç]o|px|a)\s+(\d+(?:[.,]\d+)?)", t)
    px = _num(m_px.group(1)) if m_px else None
    high = bool(re.search(r"\b(alto|alta|grande|pesad|m[aá]xim|bastante|valor alto|alto valor)\b", t))
    if intent in {"buy", "sell"} and amount is None and re.search(r"\bordem\b", t):
        high = True

    draft = _draft_from_text(text) if intent == "plan" else None
    return {
        "intent": intent,
        "token": _guess_token(text),
        "quote": _guess_quote(text),
        "amount": amount,
        "amount_kind": amount_kind,
        "pct": pct,
        "buy_pct": buy_pct,
        "profit_target_pct": profit,
        "ord_type": ord_type,
        "px": px,
        "high_size": high,
        "reply": "",
        "draft": draft,
        "steps": [],
    }


def _extract_json_obj(raw: str) -> Optional[dict[str, Any]]:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _history_block(history: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for row in (history or [])[-6:]:
        role = "assistente" if row.get("role") == "assistant" else "usuário"
        content = str(row.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content[:800]}")
    return "\n".join(lines)


async def _cursor_parse(
    text: str,
    history: list[dict[str, str]],
    *,
    ctx: str = "",
    draft: dict[str, Any] | None = None,
) -> Optional[dict[str, Any]]:
    key = _cursor_key()
    bin_path = shutil.which(settings.cursor_bin or "cursor")
    if not key or not bin_path:
        return None
    prompt = _llm_system(ctx, draft)
    hist = _history_block(history)
    if hist:
        prompt += "\n\nConversa recente:\n" + hist
    prompt += f"\n\nPedido do usuário:\n{text.strip()[:1600]}"
    env = os.environ.copy()
    env["CURSOR_API_KEY"] = key
    env["NO_OPEN_BROWSER"] = "1"
    work = tempfile.mkdtemp(prefix="okbot-cursor-")
    cmd = [
        bin_path,
        "agent",
        "--mode",
        "ask",
        "--print",
        "--output-format",
        "text",
        "--trust",
        "--sandbox",
        "enabled",
        "--workspace",
        work,
    ]
    model = (settings.cursor_model or "").strip()
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=work,
        )
        try:
            stdout, _stderr = await asyncio.wait_for(proc.communicate(), timeout=70.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return None
        if proc.returncode not in (0, None):
            return None
        return _extract_json_obj(stdout.decode("utf-8", errors="replace"))
    except Exception:
        return None
    finally:
        shutil.rmtree(work, ignore_errors=True)


async def _llm_parse(
    text: str,
    history: list[dict[str, str]],
    *,
    ctx: str = "",
    draft: dict[str, Any] | None = None,
) -> Optional[dict[str, Any]]:
    if not llm_enabled():
        return None
    if llm_provider() != "openai":
        return await _cursor_parse(text, history, ctx=ctx, draft=draft)
    messages: list[dict[str, str]] = [{"role": "system", "content": _llm_system(ctx, draft)}]
    for row in (history or [])[-6:]:
        role = "assistant" if row.get("role") == "assistant" else "user"
        content = str(row.get("content") or "").strip()
        if content:
            messages.append({"role": role, "content": content[:800]})
    messages.append({"role": "user", "content": text.strip()[:1200]})
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.llm_model or "gpt-4o-mini",
        "temperature": 0.35,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key.strip()}",
        "Content-Type": "application/json",
    }
    import logging
    _log = logging.getLogger("okbot.assistant")
    _log.info(f"[LLM] calling {url} model={payload.get('model')}")
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.post(url, headers=headers, json=payload)
        _log.info(f"[LLM] status={res.status_code}")
        if res.status_code >= 400:
            _log.warning(f"[LLM] first attempt failed: {res.status_code} {res.text[:300]}")
            # alguns modelos não aceitam response_format
            payload.pop("response_format", None)
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(url, headers=headers, json=payload)
            _log.info(f"[LLM] retry status={res.status_code}")
        if res.status_code >= 400:
            _log.error(f"[LLM] final failure: {res.status_code} {res.text[:500]}")
            return None
        body = res.json()
        content = (
            ((body.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        )
        _log.info(f"[LLM] raw content: {content[:300]}")
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I)
        data = json.loads(content)
        if not isinstance(data, dict):
            _log.warning(f"[LLM] parsed but not dict: {type(data)}")
            return None
        return data
    except Exception as exc:
        _log.exception(f"[LLM] exception: {exc}")
        return None


def _merge(local: dict[str, Any], llm: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(local)
    if not llm:
        return out
    for key in (
        "intent",
        "token",
        "quote",
        "amount",
        "amount_kind",
        "pct",
        "buy_pct",
        "profit_target_pct",
        "ord_type",
        "px",
        "high_size",
        "reply",
        "draft",
        "steps",
    ):
        val = llm.get(key)
        if val in (None, "", "null"):
            continue
        if key == "intent" and str(val) in {"unknown", "advise"} and out.get("intent") in {"buy", "sell", "plan"}:
            continue
        if key == "intent" and str(val) == "unknown" and out.get("intent") != "unknown":
            continue
        if key == "high_size":
            out["high_size"] = bool(val)
            continue
        if key in {"amount", "pct", "buy_pct", "profit_target_pct", "px"}:
            num = _num(val) if not isinstance(val, (int, float)) else float(val)
            if num:
                out[key] = num
            continue
        if key == "token":
            tok = str(val).upper().replace("USDT", "").split("-")[0]
            out["token"] = _ALIASES.get(tok.lower(), tok)
            continue
        if key == "quote":
            out["quote"] = str(val).upper()
            continue
        out[key] = val
    if llm.get("intent") == "plan":
        out["intent"] = "plan"
    if isinstance(llm.get("draft"), dict):
        out["draft"] = _merge_draft(out.get("draft") if isinstance(out.get("draft"), dict) else None, llm.get("draft"), "")
    if isinstance(llm.get("steps"), list) and llm.get("steps"):
        out["steps"] = llm["steps"]
    return out


async def _resolve_inst(okx, token: str | None, quote: str) -> Optional[str]:
    if not token:
        return None
    tok = str(token).upper().replace("/", "-")
    quote = (quote or "USDT").upper()
    if "-" in tok:
        inst = tok
    else:
        inst = f"{tok}-{quote}"
    if not okx:
        return inst
    try:
        pairs = await okx.list_spot_pairs(quote=quote if quote != "USD" else "USDT")
    except Exception:
        return inst
    ids = {str(p.get("inst_id") or "").upper() for p in pairs}
    if inst in ids:
        return inst
    # tenta USDT se a quote pedida não existir
    alt = f"{tok.split('-')[0]}-USDT"
    if alt in ids:
        return alt
    return inst


async def _wallet_bits(okx, ccy: str | None = None) -> dict[str, Any]:
    acct = await okx.get_trading_account()
    details = []
    for row in acct.get("details") or []:
        code = str(row.get("ccy") or "").upper()
        qty = okx._f(row.get("availBal")) or 0.0
        eq = okx._f(row.get("eqUsd")) or 0.0
        if qty <= 0 and eq < 0.05:
            continue
        details.append({"ccy": code, "avail": qty, "eq_usd": eq})
    details.sort(key=lambda x: -float(x.get("eq_usd") or 0))
    hit = None
    if ccy:
        want = ccy.upper()
        hit = next((d for d in details if d["ccy"] == want), None)
    return {
        "total_eq": okx._f(acct.get("totalEq")),
        "assets": details[:12],
        "asset": hit,
    }


_STABLES = {"USDT", "USDC", "USD", "BRL", "DAI", "FDUSD"}


def _fmt_usd(v: Any) -> str:
    if v is None:
        return "—"
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(n) < 0.005:
        return "US$0,00"
    sign = "+" if n > 0 else "−"
    return f"{sign}US${abs(n):.2f}".replace(".", ",")


def _pnl_horizon(text: str) -> str:
    t = _norm(text)
    if re.search(r"\b(m[eê]s|mensal)\b", t):
        return "month"
    if re.search(r"\b(semana|semanal)\b", t):
        return "week"
    if re.search(r"\b(24h|24 h)\b", t):
        return "24h"
    if re.search(r"\b(hoje|hoje)\b", t):
        return "today"
    return "today"


def _advise_reply(text: str, snap: dict[str, Any]) -> str:
    port = snap.get("portfolio") or {}
    assets = list(snap.get("assets") or [])
    if not assets:
        return (
            "Ainda não vejo a sua carteira trading nesta sessão. "
            "Se as chaves OKX já estão ligadas, atualize a Carteira e me diga de novo. "
            "O PnL que você quer compensar é de hoje, da semana ou de um token específico?"
        )
    horizon = _pnl_horizon(text)
    pnl_map = {
        "today": port.get("pnl_today"),
        "24h": port.get("pnl_24h"),
        "week": port.get("pnl_week"),
        "month": port.get("pnl_month"),
    }
    labels = {"today": "hoje", "24h": "24h", "week": "na semana", "month": "no mês"}
    pnl = pnl_map.get(horizon)
    upl = port.get("spot_upl")
    total = port.get("total_eq")
    coins = [a for a in assets if str(a.get("ccy") or "").upper() not in _STABLES]
    stables = [a for a in assets if str(a.get("ccy") or "").upper() in _STABLES]
    cash = sum(float(a.get("eq_usd") or a.get("eq_usd") or 0) for a in stables)
    losers = sorted(
        [a for a in coins if float(a.get("spot_upl") or 0) < -0.2],
        key=lambda a: float(a.get("spot_upl") or 0),
    )
    winners = sorted(
        [a for a in coins if float(a.get("spot_upl") or 0) > 0.2],
        key=lambda a: -float(a.get("spot_upl") or 0),
    )
    parts: list[str] = []
    parts.append(
        f"Patrimônio Spot ≈ {_fmt_usd(total)}. "
        f"PnL {labels[horizon]}: {_fmt_usd(pnl)}. UPL aberto: {_fmt_usd(upl)}."
    )
    if losers:
        bits = ", ".join(
            f"{a.get('ccy')} {_fmt_usd(a.get('spot_upl'))}" for a in losers[:3]
        )
        parts.append(f"No vermelho: {bits}.")
    if winners:
        bits = ", ".join(
            f"{a.get('ccy')} {_fmt_usd(a.get('spot_upl'))}" for a in winners[:3]
        )
        parts.append(f"No verde: {bits}.")
    if cash > 0.5:
        parts.append(f"Estável livre ≈ {_fmt_usd(cash)}.")
    gap = abs(float(pnl)) if pnl is not None and float(pnl) < 0 else None
    if gap:
        parts.append(
            f"Para zerar esse PnL {labels[horizon]} você precisaria de cerca de {_fmt_usd(gap)} a favor. "
            "Nenhuma ordem garante isso."
        )
        if losers:
            top = str(losers[0].get("ccy") or "")
            parts.append(
                f"Vender {top} só realiza o prejuízo — não ‘compensa’. "
                "Caminhos: cortar o token no vermelho, girar só o estável, ou caçar um dip. Qual você quer?"
            )
        elif cash > 0.5:
            parts.append(
                "Com estável livre dá para montar uma compra pequena. "
                "Você prefere BTC/ETH (mais líquido) ou um alt que já está na carteira?"
            )
        else:
            parts.append("Sem estável livre, compensar implica vender alguém. Qual token você aceita girar?")
    else:
        parts.append(
            "Não há rombo nesse recorte, ou o número ainda não chegou. "
            "Quer que eu foque no UPL aberto, na semana, ou em um token?"
        )
    return " ".join(parts)


async def _account_context(okx, port: dict[str, Any] | None = None) -> dict[str, Any]:
    port = dict(port or {})
    assets: list[dict[str, Any]] = []
    for a in port.get("assets") or []:
        ccy = str(a.get("ccy") or "").upper()
        if not ccy:
            continue
        eq = a.get("eq_usd")
        if eq is None:
            eq = a.get("eq_usd")
        upl = a.get("spot_upl")
        if upl is None:
            upl = a.get("spot_upl")
        assets.append(
            {
                "ccy": ccy,
                "avail": a.get("avail") if a.get("avail") is not None else a.get("total_bal"),
                "eq_usd": eq,
                "spot_upl": upl,
                "spot_upl_ratio": a.get("spot_upl_ratio"),
                "avg_px": a.get("avg_px"),
                "chg24": a.get("chg24"),
            }
        )
    wallet: dict[str, Any] = {}
    if not assets and okx:
        try:
            wallet = await _wallet_bits(okx)
            for a in wallet.get("assets") or []:
                assets.append(
                    {
                        "ccy": a.get("ccy"),
                        "avail": a.get("avail"),
                        "eq_usd": a.get("eq_usd"),
                        "spot_upl": None,
                        "chg24": None,
                    }
                )
        except Exception:
            pass
    bots: list[str] = []
    try:
        from . import db

        bots = [f"{b.get('name')} ({b.get('inst_id')})" for b in (db.list_bots() or [])[:8]]
    except Exception:
        pass
    # Lista detalhada para o LLM poder responder perguntas sobre a carteira
    lines = []
    for a in assets[:20]:
        ccy = a.get("ccy", "?")
        avail = float(a.get("avail") or 0)
        eq = float(a.get("eq_usd") or 0)
        upl = a.get("spot_upl")
        chg = a.get("chg24")
        avg_px = a.get("avg_px")
        upl_ratio = a.get("spot_upl_ratio")
        line = f"{ccy}: qty={avail:g}, valor≈US${eq:.2f}"
        if avg_px is not None:
            line += f", custo_medio={float(avg_px):g}"
        if upl is not None:
            line += f", UPL={_fmt_usd(upl)}"
        if upl_ratio is not None:
            line += f", UPL%={float(upl_ratio)*100:.2f}%"
        if chg is not None:
            line += f", 24h={float(chg):+.1f}%"
        lines.append(line)
    # Ordens abertas (resumo)
    open_orders_text = ""
    if okx:
        try:
            pending = await okx.list_pending()
            if pending:
                oo_lines = []
                for o in pending[:5]:
                    oo_lines.append(f"{o.get('side','?')} {o.get('instId','?')} sz={o.get('sz','?')} px={o.get('px','?')}")
                open_orders_text = f"\nOrdens abertas ({len(pending)}): " + "; ".join(oo_lines)
        except Exception:
            pass
    text = (
        f"Patrimônio total ≈ US${float(port.get('total_eq') or 0):.2f}.\n"
        f"PnL hoje {_fmt_usd(port.get('pnl_today'))}, 24h {_fmt_usd(port.get('pnl_24h'))}, "
        f"semana {_fmt_usd(port.get('pnl_week'))}, mês {_fmt_usd(port.get('pnl_month'))}, "
        f"UPL spot {_fmt_usd(port.get('spot_upl'))}.\n"
        "Tokens na carteira:\n" + ("\n".join(lines) or "vazia ou sem chave OKX") + "\n"
        "Bots: " + (", ".join(bots) or "nenhum") +
        open_orders_text
    )
    return {"text": text, "wallet": wallet, "assets": assets, "portfolio": port}


def _steps_from_draft(draft: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not _draft_complete(draft):
        return []
    assert draft is not None
    frm = str(draft["from_token"]).upper()
    kind = str(draft.get("from_kind") or "all")
    steps: list[dict[str, Any]] = [
        {
            "type": "order",
            "side": "sell",
            "token": frm,
            "amount_kind": kind,
            "pct": draft.get("from_pct"),
        }
    ]
    for dest in draft.get("to") or []:
        tok = str(dest.get("token") or "").upper()
        if not tok:
            continue
        steps.append(
            {
                "type": "order",
                "side": "buy",
                "token": tok,
                "amount_kind": "quote",
                "pct": dest.get("pct"),
            }
        )
        if draft.get("also_bots"):
            steps.append(
                {
                    "type": "create_bot",
                    "token": tok,
                    "buy_pct": draft.get("buy_pct") or 2,
                    "profit_target_pct": draft.get("profit_target_pct") or 1,
                }
            )
    return steps


async def _actions_from_steps(okx, steps: list[dict[str, Any]], quote: str, snap: dict[str, Any]) -> list[dict[str, Any]]:
    assets = {str(a.get("ccy") or "").upper(): a for a in (snap.get("assets") or [])}
    sell_usd = 0.0
    out: list[dict[str, Any]] = []
    for st in steps or []:
        typ = str(st.get("type") or "order")
        tok = str(st.get("token") or "").upper()
        if not tok:
            continue
        if typ == "create_bot":
            inst = await _resolve_inst(okx, tok, quote)
            if not inst:
                continue
            out.append(
                {
                    "type": "create_bot",
                    "label": f"Criar bot {tok}",
                    "seed": {
                        "name": f"Bot {tok}",
                        "inst_id": inst,
                        "buy_pct": float(st.get("buy_pct") or 2),
                        "profit_target_pct": float(st.get("profit_target_pct") or 1),
                        "quote_amount": "",
                    },
                }
            )
            continue
        side = str(st.get("side") or "buy")
        inst = await _resolve_inst(okx, tok, quote)
        if not inst:
            continue
        kind = str(st.get("amount_kind") or ("all" if side == "sell" else "quote"))
        amount = st.get("amount")
        pct = st.get("pct")
        asset = assets.get(tok) or {}
        if side == "sell":
            avail = float(asset.get("avail") or 0)
            if kind == "pct" and pct:
                amount = avail * float(pct) / 100.0
            elif kind in {"all", "base"} and not amount:
                amount = avail or None
            if amount:
                sell_usd += float(asset.get("eq_usd") or 0) * (
                    (float(pct) / 100.0) if (kind == "pct" and pct) else 1.0
                )
                out.append(
                    {
                        "type": "order",
                        "label": f"Vender {tok}",
                        "payload": {
                            "inst_id": inst,
                            "side": "sell",
                            "ord_type": "market",
                            "sz": float(amount),
                            "tgt_ccy": "base_ccy",
                        },
                    }
                )
            continue
        usd = None
        if amount and kind == "quote":
            usd = float(amount)
        elif pct and sell_usd:
            usd = sell_usd * float(pct) / 100.0
        elif sell_usd:
            usd = sell_usd
        if usd and usd > 0:
            out.append(
                {
                    "type": "order",
                    "label": f"Comprar {tok} ≈ US${usd:.2f}",
                    "payload": {
                        "inst_id": inst,
                        "side": "buy",
                        "ord_type": "market",
                        "sz": round(usd, 4),
                        "tgt_ccy": "quote_ccy",
                    },
                }
            )
    return out


async def handle(
    message: str,
    *,
    history: list[dict[str, str]] | None = None,
    draft: dict[str, Any] | None = None,
    okx: Any = None,
    portfolio: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = (message or "").strip()
    if not text:
        return {
            "reply": "Pode falar à vontade. Eu olho seu PnL e a carteira e sugiro o próximo passo — ou pergunto o que faltar. Nada vai à OKX sem você confirmar.",
            "mode": "local" if not llm_enabled() else "llm",
            "actions": [],
            "draft": draft,
        }
    snap = await _account_context(okx, portfolio)
    incoming_draft = draft if isinstance(draft, dict) else None
    local = parse_local(text)
    llm = await _llm_parse(text, history or [], ctx=snap.get("text") or "", draft=incoming_draft)
    parsed = _merge(local, llm)
    merged_draft = _merge_draft(incoming_draft, parsed.get("draft") if isinstance(parsed.get("draft"), dict) else None, text)
    parsed["draft"] = merged_draft
    tnorm = _norm(text)

    # Verificar histórico: se conversa anterior pediu ação e agora user diz só o token
    _hist_context = ""
    for h in (history or [])[-4:]:
        _hist_context += " " + _norm(str(h.get("content") or ""))
    _hist_wants_action = bool(re.search(
        r"\b(compens\w*|recuper\w*|zerar|ordem|vender?|venda|comprar?|compra)\b", _hist_context
    ))

    loc_intent = str(local.get("intent") or "unknown")
    if loc_intent in {"buy", "sell", "plan", "create_bot"}:
        parsed["intent"] = loc_intent
        if local.get("token"):
            parsed["token"] = local["token"]
        parsed["ord_type"] = local.get("ord_type") or parsed.get("ord_type")
        parsed["high_size"] = local.get("high_size") or parsed.get("high_size")
        if local.get("px"):
            parsed["px"] = local["px"]
    if incoming_draft and parsed.get("intent") in {"unknown", "help"}:
        if _confirm_utterance(tnorm) or _draft_complete(merged_draft):
            parsed["intent"] = "plan"
    if parsed.get("intent") in {"unknown", "help", "advise"} and re.search(
        r"\b(ordem|limite|limit)\b", tnorm
    ) and parsed.get("token"):
        parsed["intent"] = "sell" if re.search(r"\b(vender?|venda|sell)\b", tnorm) else "buy"
    # "compensar perda" + token = sell (não advise)
    if parsed.get("intent") in {"advise", "unknown"} and parsed.get("token") and re.search(
        r"\b(compens\w*|recuper\w*|zerar|perda|ordem)\b", tnorm
    ):
        parsed["intent"] = "sell"
    # Se o histórico pedia ação e o user agora diz só um token → manter intent do histórico
    if parsed.get("intent") in {"advise", "unknown", "help"} and parsed.get("token") and _hist_wants_action:
        if re.search(r"\b(compens\w*|recuper\w*|zerar|perda|vender?|venda)\b", _hist_context):
            parsed["intent"] = "sell"
        elif re.search(r"\b(comprar?|compra|buy)\b", _hist_context):
            parsed["intent"] = "buy"
    intent = str(parsed.get("intent") or "unknown")
    if not llm:
        mode = "local"
    elif llm_provider() == "openai":
        mode = "llm"
    else:
        mode = "cursor"
    actions: list[dict[str, Any]] = []
    reply = str(parsed.get("reply") or "").strip()

    token = parsed.get("token")
    quote = str(parsed.get("quote") or "USDT").upper()
    inst = await _resolve_inst(okx, token, quote) if token else None

    if intent in {"help", "unknown", "advise"}:
        if not reply:
            reply = _advise_reply(text, snap)
        # Adicionar ações de navegação relevantes baseado no contexto
        actions: list[dict[str, Any]] = []
        if snap.get("assets"):
            actions.append({"type": "navigate", "hash": "#/wallet", "label": "Ver carteira"})
        actions.append({"type": "navigate", "hash": "#/orders", "label": "Ver ordens"})
        return {
            "reply": reply,
            "mode": mode,
            "actions": actions,
            "draft": None,
        }

    if intent == "plan":
        missing = _draft_missing(merged_draft)
        steps = parsed.get("steps") or _steps_from_draft(merged_draft)
        if missing and not steps:
            reply = reply or missing
            return {"reply": reply, "mode": mode, "actions": [], "draft": merged_draft}
        built = await _actions_from_steps(okx, steps if isinstance(steps, list) else [], quote, snap)
        if not built:
            reply = reply or (
                missing
                or "Entendi o giro, mas falta tamanho (saldo/preço). Diga se vende tudo ou um % e o que comprar."
            )
            return {"reply": reply, "mode": mode, "actions": [], "draft": merged_draft}
        from_tok = (merged_draft or {}).get("from_token") or "?"
        dest = ", ".join(
            f"{x.get('token')} {float(x.get('pct') or 0):g}%" for x in (merged_draft.get("to") or []) if isinstance(x, dict)
        ) or "os tokens combinados"
        reply = reply or (
            f"Plano: vender {from_tok} e com o valor comprar {dest}. "
            "Vou abrir cada passo para você confirmar. Nada vai sozinho à OKX."
        )
        return {
            "reply": reply,
            "mode": mode,
            "actions": [
                {"type": "plan", "label": "Seguir o plano passo a passo", "steps": built},
                *built,
            ],
            "draft": merged_draft,
        }

    if intent == "open_hunter":
        return {
            "reply": reply or "Abrindo o Caçador — radar de dips Spot.",
            "mode": mode,
            "actions": [{"type": "navigate", "hash": "#/hunter", "label": "Abrir Caçador"}],
        }

    if intent == "wallet":
        wallet = await _wallet_bits(okx, token) if okx else {}
        if parsed.get("token") and wallet.get("asset"):
            a = wallet["asset"]
            reply = reply or (
                f"📊 **{a['ccy']}**\n"
                f"• Disponível: {a['avail']:g}\n"
                f"• Valor: ≈ US${float(a.get('eq_usd') or 0):.2f}"
            )
        else:
            tot = wallet.get("total_eq")
            assets_list = wallet.get("assets") or []
            if assets_list:
                lines = []
                for x in assets_list[:15]:
                    ccy = x.get("ccy", "?")
                    avail = float(x.get("avail") or 0)
                    eq = float(x.get("eq_usd") or 0)
                    if avail > 0 or eq > 0.01:
                        lines.append(f"• {ccy}: {avail:g} (≈ US${eq:.2f})")
                tokens_text = "\n".join(lines) if lines else "nenhum token com saldo"
                reply = reply or (
                    f"💰 Patrimônio total ≈ US${float(tot or 0):.2f}\n\n"
                    f"Seus tokens:\n{tokens_text}\n\n"
                    "Quer operar algum deles? Me diz o token e a ação (comprar, vender, criar bot)."
                )
            else:
                reply = reply or f"Patrimônio trading ≈ US${float(tot or 0):.2f}. Não encontrei tokens com saldo."
        return {
            "reply": reply,
            "mode": mode,
            "actions": [{"type": "navigate", "hash": "#/wallet", "label": "Ver carteira completa"}],
            "wallet": wallet,
        }

    if intent == "price":
        if not inst or not okx:
            # Sem token especificado, listar preços dos tokens da carteira
            wallet = await _wallet_bits(okx) if okx else {}
            assets_list = wallet.get("assets") or []
            if assets_list and okx:
                price_lines = []
                for a in assets_list[:8]:
                    ccy = a.get("ccy", "")
                    if ccy in _STABLES:
                        continue
                    try:
                        t = await okx.get_ticker(f"{ccy}-USDT")
                        p = okx._f(t.get("last"))
                        if p:
                            price_lines.append(f"• {ccy}: US${p:g}")
                    except Exception:
                        continue
                if price_lines:
                    reply = reply or ("Cotações dos seus tokens:\n" + "\n".join(price_lines) + "\n\nQual te interessa?")
                    return {"reply": reply, "mode": mode, "actions": [{"type": "navigate", "hash": "#/tokens", "label": "Ver todos"}]}
            return {"reply": reply or "Qual token? Ex.: «preço do SOL».", "mode": mode, "actions": []}
        try:
            ticker = await okx.get_ticker(inst)
            last = okx._f(ticker.get("last"))
        except Exception:
            last = None
        reply = reply or (f"{inst} ≈ US${last:g}." if last else f"Não achei cotação de {inst}.")
        return {
            "reply": reply,
            "mode": mode,
            "actions": [{"type": "navigate", "hash": "#/tokens", "label": f"Ver gráfico {inst}"}],
        }

    if intent in {"list_orders", "order_history"}:
        from . import db as _db
        if okx:
            try:
                if intent == "list_orders":
                    pending = await okx.list_pending()
                    if pending:
                        lines = []
                        for o in pending[:10]:
                            side = o.get("side", "?")
                            inst_o = o.get("instId", "?")
                            sz = o.get("sz", "?")
                            px_o = o.get("px", "mercado")
                            state = o.get("state", "?")
                            lines.append(f"• {side.upper()} {inst_o} | qty: {sz} | px: {px_o} | {state}")
                        reply = reply or (f"Ordens abertas ({len(pending)}):\n" + "\n".join(lines))
                    else:
                        reply = reply or "Nenhuma ordem aberta no momento."
                else:
                    history = await okx.list_history(limit=10)
                    if history:
                        lines = []
                        for o in history[:10]:
                            side = o.get("side", "?")
                            inst_o = o.get("instId", "?")
                            sz = o.get("fillSz") or o.get("sz", "?")
                            px_o = o.get("avgPx") or o.get("px", "?")
                            state = o.get("state", "?")
                            lines.append(f"• {side.upper()} {inst_o} | qty: {sz} | px: {px_o} | {state}")
                        reply = reply or (f"Últimas ordens:\n" + "\n".join(lines))
                    else:
                        reply = reply or "Sem histórico de ordens recente."
            except Exception:
                reply = reply or "Não consegui buscar as ordens agora. Tente novamente."
        else:
            reply = reply or "Sem conexão OKX para buscar ordens."
        return {
            "reply": reply,
            "mode": mode,
            "actions": [{"type": "navigate", "hash": "#/orders", "label": "Ver ordens"}],
        }

    if intent in {"start_bot", "stop_bot", "list_bots"}:
        from . import db

        bots = db.list_bots()
        if intent == "list_bots":
            if bots:
                lines = []
                for b in bots[:10]:
                    name = b.get("name", "?")
                    inst_b = b.get("inst_id", "?")
                    status = "▶️ ativo" if b.get("running") else "⏸️ parado"
                    lines.append(f"• {name} ({inst_b}) — {status}")
                reply = reply or ("Seus bots:\n" + "\n".join(lines) + "\n\nQuer iniciar, pausar ou criar um novo?")
            else:
                reply = reply or "Nenhum bot criado ainda. Quer criar um? Me diz o token, ex.: «cria bot de SOL, queda 3%, lucro 1%»."
            return {
                "reply": reply,
                "mode": mode,
                "actions": [{"type": "navigate", "hash": "#/bot", "label": "Gerenciar bots"}],
            }
        want = (token or "").upper()
        chosen = None
        for b in bots:
            inst_b = str(b.get("inst_id") or "").upper()
            name = str(b.get("name") or "").upper()
            if want and (want in inst_b.split("-")[0] or want in name):
                chosen = b
                break
        if not chosen and len(bots) == 1:
            chosen = bots[0]
        if not chosen:
            return {
                "reply": reply or "Qual bot? Diga o token, ex.: «pausar bot de SOL».",
                "mode": mode,
                "actions": [{"type": "navigate", "hash": "#/bot", "label": "Ver bots"}],
            }
        kind = "start_bot" if intent == "start_bot" else "stop_bot"
        verb = "Iniciar" if intent == "start_bot" else "Pausar"
        return {
            "reply": reply or f"{verb} «{chosen.get('name')}» ({chosen.get('inst_id')})? Confirme no modal.",
            "mode": mode,
            "actions": [
                {
                    "type": kind,
                    "bot_id": chosen.get("bot_id"),
                    "label": f"{verb} {chosen.get('name')}",
                }
            ],
        }

    if intent == "create_bot":
        if not inst:
            return {
                "reply": reply or "De qual token é o plano? Ex.: «crie um bot de SOL, queda 3%, lucro 1%».",
                "mode": mode,
                "actions": [],
            }
        buy_pct = float(parsed.get("buy_pct") or 2)
        profit = float(parsed.get("profit_target_pct") or 1)
        quote_amt = 0.0
        if parsed.get("amount_kind") == "quote" and parsed.get("amount"):
            quote_amt = float(parsed["amount"])
        name = f"Bot {inst.split('-')[0]}"
        return {
            "reply": reply
            or (
                f"Vou montar um bot de {inst}: compra se cair {buy_pct:g}% e vende com {profit:g}% de lucro"
                + (f", aporte {quote_amt:g} {quote}." if quote_amt else ".")
                + " Confirme no formulário — nada inicia sozinho."
            ),
            "mode": mode,
            "actions": [
                {
                    "type": "create_bot",
                    "label": f"Criar bot {inst.split('-')[0]}",
                    "seed": {
                        "name": name,
                        "inst_id": inst,
                        "buy_pct": buy_pct,
                        "profit_target_pct": profit,
                        "quote_amount": quote_amt or "",
                    },
                }
            ],
        }

    if intent in {"buy", "sell"}:
        if not inst:
            # Listar tokens disponíveis para que o usuário escolha
            wallet = await _wallet_bits(okx) if okx else {}
            assets_list = wallet.get("assets") or []
            side_label = "comprar" if intent == "buy" else "vender"
            if assets_list:
                if intent == "sell":
                    # Mostrar apenas tokens não-stables que o user pode vender
                    sellable = [a for a in assets_list if str(a.get("ccy", "")).upper() not in _STABLES and float(a.get("avail") or 0) > 0]
                    if sellable:
                        lines = [f"• {a['ccy']}: {float(a['avail']):g} (≈ US${float(a.get('eq_usd') or 0):.2f})" for a in sellable[:10]]
                        reply = reply or (
                            f"Tokens disponíveis para venda:\n" + "\n".join(lines) + "\n\n"
                            "Qual quer vender e quanto? (ex.: «vende tudo de XRP» ou «vende 50% de SOL»)"
                        )
                    else:
                        reply = reply or "Você não tem tokens (não-estáveis) com saldo para vender."
                else:
                    # Compra: mostrar saldo USDT disponível e sugerir tokens
                    stable_avail = sum(float(a.get("avail") or 0) for a in assets_list if str(a.get("ccy", "")).upper() in _STABLES)
                    reply = reply or (
                        f"Saldo disponível para compra: ≈ US${stable_avail:.2f}\n\n"
                        "Qual token quer comprar e quanto? (ex.: «compre 30 USDT de SOL» ou «compre ETH com tudo»)"
                    )
            else:
                reply = reply or f"Qual token quer {side_label}? Ex.: «compre 20 USDT de SOL»."
            return {
                "reply": reply,
                "mode": mode,
                "actions": [{"type": "navigate", "hash": "#/orders", "label": "Abrir Ordens"}],
            }
        side = "buy" if intent == "buy" else "sell"
        kind = str(parsed.get("amount_kind") or ("quote" if side == "buy" else "base"))
        amount = parsed.get("amount")
        pct = parsed.get("pct")
        last = None
        avail_base = 0.0
        avail_quote = 0.0
        base = inst.split("-")[0]
        if okx:
            try:
                ticker = await okx.get_ticker(inst)
                last = okx._f(ticker.get("last"))
            except Exception:
                last = None
            wallet = await _wallet_bits(okx, base)
            if wallet.get("asset"):
                avail_base = float(wallet["asset"].get("avail") or 0)
            try:
                acct = await okx.get_trading_account()
                for row in acct.get("details") or []:
                    if str(row.get("ccy") or "").upper() == quote:
                        avail_quote = okx._f(row.get("availBal")) or 0.0
            except Exception:
                pass
        if kind == "all" and side == "sell":
            amount = avail_base
            kind = "base"
        elif kind == "pct":
            p = (float(pct or 0) / 100.0)
            if side == "sell":
                amount = avail_base * p
                kind = "base"
            else:
                amount = avail_quote * p
                kind = "quote"
        if parsed.get("high_size") and not amount:
            if side == "buy":
                amount = avail_quote * 0.9 if avail_quote > 0 else None
                kind = "quote"
            else:
                amount = avail_base * 0.9 if avail_base > 0 else None
                kind = "base"
        ord_type = str(parsed.get("ord_type") or "market").lower()
        if ord_type not in {"market", "limit", "post_only", "ioc", "fok"}:
            ord_type = "limit" if parsed.get("ord_type") else "market"
        px = parsed.get("px")

        # Break-even: se é venda e tem custo médio, calcular preço de compensação
        avg_px_entry = None
        if side == "sell" and base:
            for a in (snap.get("assets") or []):
                if str(a.get("ccy") or "").upper() == base:
                    if a.get("avg_px"):
                        avg_px_entry = float(a["avg_px"])
                    # Fallback: usar avail do snap se OKX não retornou
                    if avail_base <= 0 and float(a.get("avail") or 0) > 0:
                        avail_base = float(a["avail"])
                    break
        # Se LLM sugeriu preço = break-even ou se é uma venda sem preço com custo médio disponível
        if side == "sell" and avg_px_entry and not px:
            # Calcular break-even: custo_medio * (1 + fee_rate)
            fee_rate = 0.001  # 0.1% taker fee OKX
            break_even = avg_px_entry * (1 + fee_rate)
            px = break_even
            ord_type = "limit"  # Forçar limite para break-even
            if not amount and avail_base > 0:
                amount = avail_base
                kind = "base"

        if ord_type != "market" and not px and last:
            px = last * (0.999 if side == "buy" else 1.001)
        if not amount:
            # Informar break-even se disponível
            be_info = ""
            if avg_px_entry:
                be_info = f" Custo médio: {avg_px_entry:g}. Break-even (c/ taxa): {avg_px_entry * 1.001:.4f}."
            ask = "quanto em USDT" if side == "buy" else "quantos tokens (ou «tudo»)"
            return {
                "reply": reply or f"Entendi {side} de {inst}. Falta o tamanho: {ask}. Tenho {avail_quote:g} {quote} e {avail_base:g} {base}.{be_info}",
                "mode": mode,
                "actions": [{"type": "navigate", "hash": "#/orders", "label": "Abrir Ordens"}],
            }
        tgt = "quote_ccy" if kind == "quote" else "base_ccy"
        verb = "Compra" if side == "buy" else "Venda"
        unit = quote if kind == "quote" else base
        tipo = "a mercado" if ord_type == "market" else f"limite @ {float(px):g}" if px else "limite"
        # Reply mais informativo para vendas de compensação
        if not reply and side == "sell" and avg_px_entry and px:
            diff_pct = ((float(px) - (last or 0)) / (last or 1)) * 100 if last else 0
            if last and float(px) > last:
                reply = (
                    f"{verb} {tipo} de {float(amount):g} {unit} em {inst}.\n"
                    f"Custo médio: {avg_px_entry:g} | Break-even: {float(px):.4f} (c/ taxa 0.1%)\n"
                    f"Preço atual: {last:g} — a ordem fica pendente até XRP subir {diff_pct:.1f}%.\n"
                    "Confirme no modal — só executa quando o preço atingir o limite."
                )
            else:
                reply = (
                    f"{verb} {tipo} de {float(amount):g} {unit} em {inst}.\n"
                    f"Custo médio: {avg_px_entry:g} | Preço de venda: {float(px):.4f}\n"
                    "Confirme no modal."
                )
        reply = reply or (
            f"{verb} {tipo} de {float(amount):g} {unit} em {inst}. "
            "Confirme no modal — eu não envio a ordem sozinho."
        )
        payload = {
            "inst_id": inst,
            "side": side,
            "ord_type": ord_type,
            "sz": float(amount),
            "tgt_ccy": tgt,
        }
        if ord_type != "market" and px:
            payload["px"] = float(px)
        return {
            "reply": reply,
            "mode": mode,
            "actions": [
                {
                    "type": "order",
                    "label": f"{verb} {inst}" + (" limite" if ord_type != "market" else ""),
                    "payload": payload,
                }
            ],
        }

    return {
        "reply": reply or "Não consegui transformar isso em uma ação. Tente de novo com o token e o valor.",
        "mode": mode,
        "actions": [],
    }
