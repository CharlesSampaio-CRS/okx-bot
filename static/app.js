const $ = (id) => document.getElementById(id);

const TITLES = {
  overview: ["Bot", "Clique para expandir · execuções do bot"],
  config: ["Configurações", "Contas OKX · limites de ordem"],
  wallet: ["Carteira", "Saldos Spot OKX"],
  tokens: ["Tokens", "Pares Spot · ordenar e negociar"],
  orders: ["Ordens", "Spot · compra, venda e histórico"],
  lab: ["Lab", "Simule queda e alvo no histórico Spot — sem ordem real"],
  hunter: ["Caçador", "Radar Spot · top 30 · melhor estratégia por token"],
  strategies: ["Estratégias", "Catálogo de presets · valide no token · crie o bot"],
  profile: ["Perfil", "Dados da conta · nome · login"],
  docs: ["Como funciona", "Manual pesquisável · dicionário · FAQ"],
};

const STABLES = new Set(["USDT", "USDC", "BRL", "USD", "EUR", "TRY"]);

const ICO = {
  refresh: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>`,
  buy: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></svg>`,
  sell: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 5v14"/><path d="M19 12l-7 7-7-7"/></svg>`,
  swap: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M7 7h11"/><path d="M14 3l4 4-4 4"/><path d="M17 17H6"/><path d="M10 13l-4 4 4 4"/></svg>`,
  chart: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 19V5M4 19h16"/><path d="M7 14l4-4 3 3 6-7"/></svg>`,
  x: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>`,
  play: `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>`,
  pause: `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg>`,
  bot: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="5" y="10" width="14" height="10" rx="2"/><path d="M12 3v4M8 14h.01M16 14h.01M9 18h6"/><circle cx="12" cy="7" r="2"/></svg>`,
};

const STRAT_ICONS = {
  scalp: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M13 2L4 14h7l-1 8 10-14h-7l0-6z"/></svg>`,
  micro_scalp: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1"/></svg>`,
  momentum_dip: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 17c3-1 5-6 7-6s3 5 5 5 4-8 6-10"/><path d="M17 6h4v4"/></svg>`,
  balanced: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3v18"/><path d="M5 8h14"/><path d="M7 8l-3 8h6"/><path d="M17 8l3 8h-6"/></svg>`,
  profit_max: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 19V6"/><path d="M7 10l5-5 5 5"/><path d="M5 19h14"/></svg>`,
  asymmetric: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 18V8"/><path d="M10 18V4"/><path d="M16 18v-6"/><path d="M20 18v-3"/></svg>`,
  deep_dip: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 6c4 0 5 12 9 12s5-12 9-12"/><path d="M12 18v3"/></svg>`,
  crash_buyer: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 4l7 7"/><path d="M11 4v7H4"/><path d="M20 20l-7-7"/><path d="M13 20v-7h7"/></svg>`,
  conservative: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l8 4v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V7l8-4z"/></svg>`,
  sniper: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>`,
  fee_aware: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/><path d="M8 4.5A10 10 0 0 0 4.5 8"/></svg>`,
  swing_range: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 12h16"/><path d="M7 8l-3 4 3 4"/><path d="M17 8l3 4-3 4"/></svg>`,
};

function stratIcon(idOrStrat) {
  const id = typeof idOrStrat === "string" ? idOrStrat : (idOrStrat?.id || "");
  const svg = STRAT_ICONS[id] || STRAT_ICONS.balanced;
  return `<span class="strat-ico" aria-hidden="true">${svg}</span>`;
}

const CHART_RANGES = [
  { key: "1h", days: 1 / 24, bar: "1m", fallbackBar: "5m", label: "1H", limit: 80 }, // última 1h · candle 1m (fallback 5m)
  { key: "24h", days: 1, bar: "5m", label: "24h", limit: 300 },
  { key: "7d", days: 7, bar: "1H", label: "7D", limit: 400 },
  { key: "30d", days: 30, bar: "4H", label: "1M", limit: 400 },
  { key: "90d", days: 90, bar: "1D", label: "3M", limit: 400 },
  { key: "180d", days: 180, bar: "1D", label: "6M", limit: 400 },
  { key: "365d", days: 365, bar: "1D", label: "1A", limit: 400 },
];

let lastStatus = null;
const NEW_ACCT = "__new__";
let lastKeys = null;
let selectedAccountId = "";
let lastRunningCount = 0;
let lastTrades = [];
let chartRangeKey = localStorage.getItem("okx_chart_range") || "90d";
// legado: removido o range de 1 minuto
if (chartRangeKey === "1m" || chartRangeKey === "1min") chartRangeKey = "24h";
if (!CHART_RANGES.some((r) => r.key === chartRangeKey)) chartRangeKey = "90d";
try { localStorage.setItem("okx_chart_range", chartRangeKey); } catch (_) { /* ignore */ }
// compat: antigo okx_chart_days
if (!localStorage.getItem("okx_chart_range") && localStorage.getItem("okx_chart_days")) {
  const legacy = Number(localStorage.getItem("okx_chart_days"));
  const hit = CHART_RANGES.find((r) => r.days === legacy);
  if (hit) chartRangeKey = hit.key;
}
let chartDays = (CHART_RANGES.find((r) => r.key === chartRangeKey) || CHART_RANGES.find((r) => r.key === "90d") || CHART_RANGES[0]).days;
let chartInst = localStorage.getItem("okx_chart_inst") || "";
let chartForceRefresh = false;
let chartSelectedIdx = -1;
let toggling = false;
let selectedBotId = localStorage.getItem("okx_bot_id") || "";
let botDetailVisible = false;
const BOT_EXEC_OPEN_KEY = "okx_bot_exec_open"; // legado — não usado na lista/detalhe
let orderSide = "buy";
let orderContext = null;
let orderContextInst = null;
let orderLoading = false;
let orderLoadSeq = 0;
let orderLoadError = null;
let orderQuote = localStorage.getItem("okx_order_quote") || "BRL";
let orderTokenTimer = null;
const HIST_PERIODS = [
  { key: "1h", days: 1 / 24, label: "1H" },
  { key: "24h", days: 1, label: "24h" },
  { key: "7d", days: 7, label: "7D" },
  { key: "30d", days: 30, label: "1M" },
  { key: "90d", days: 90, label: "3M" },
  { key: "180d", days: 180, label: "6M" },
  { key: "365d", days: 365, label: "1A" },
];
const HIST_PERIOD_LEGACY = { "1d": "24h", "1m": "30d", "6m": "180d", "1y": "365d", day: "24h", month: "30d", year: "365d" };

let histPeriod = localStorage.getItem("okx_hist_period") || "30d";
histPeriod = HIST_PERIOD_LEGACY[histPeriod] || histPeriod;
if (!HIST_PERIODS.some((p) => p.key === histPeriod)) histPeriod = "30d";
try { localStorage.setItem("okx_hist_period", histPeriod); } catch (_) {}
let histSide = localStorage.getItem("okx_hist_side") || "all";
if (!["all", "buy", "sell"].includes(histSide)) histSide = "all";
let histStatus = localStorage.getItem("okx_hist_status") || "all";
if (!["all", "filled", "canceled"].includes(histStatus)) histStatus = "all";
let histOrigin = localStorage.getItem("okx_hist_origin") || "all";
if (!["all", "bot", "user"].includes(histOrigin)) histOrigin = "all";
let histTokenQuery = localStorage.getItem("okx_hist_token_q") || "";
let histTokenTimer = null;
/** Cache local do histórico por período (trocar lado sem refetch; persiste no navegador). */
const HIST_LS_KEY = "okx_hist_cache";
let histClientCache = { period: null, ts: 0, payload: null };
const HIST_CLIENT_TTL_MS = 5 * 60 * 1000;

function restoreHistClientCache() {
  try {
    const raw = localStorage.getItem(HIST_LS_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (!data?.payload || !data?.period || !data?.ts) return;
    if (Date.now() - data.ts > HIST_CLIENT_TTL_MS) {
      localStorage.removeItem(HIST_LS_KEY);
      return;
    }
    histClientCache = data;
  } catch (_) {
    try { localStorage.removeItem(HIST_LS_KEY); } catch (_) {}
  }
}

function persistHistClientCache() {
  try {
    if (!histClientCache?.payload || !histClientCache.period) return;
    localStorage.setItem(HIST_LS_KEY, JSON.stringify(histClientCache));
  } catch (_) {
    try { localStorage.removeItem(HIST_LS_KEY); } catch (_) {}
  }
}

function clearHistClientCache() {
  histClientCache = { period: null, ts: 0, payload: null };
  try { localStorage.removeItem(HIST_LS_KEY); } catch (_) {}
}

restoreHistClientCache();
let walletShowDust = localStorage.getItem("okx_wallet_show_dust") === "1";
const WALLET_DUST_MIN = 0.001;
let walletSort = { key: "total_bal", dir: "desc" };
let lastWallet = null;
let lastWalletTs = 0;
let usdtBrlRate = null;
let lastPnlData = null;
let pollTimer = null;
let refreshInFlight = false;
let lastTradesFetch = 0;
let pollRunningMode = null;
const POLL_ACTIVE_MS = 10_000;
const POLL_IDLE_MS = 30_000;
const TRADES_EVERY_MS = 60_000;
let orderIntent = null;
let pendingAction = null;
let pendingSecondaryAction = null;
let modalBusy = false;
let lastOpenOrders = [];
let walletOrdersOk = false;
let lastBotExecutions = [];
let lastTokens = [];
let tokensSort = { key: "vol", dir: "desc" };
let botModalQuote = localStorage.getItem("okx_order_quote") || "BRL";
let botTokenTimer = null;

function setIcon(img, src, alt) {
  if (!img) return;
  if (!src) {
    img.hidden = true;
    return;
  }
  img.hidden = false;
  img.onerror = () => {
    if (alt && img.src !== alt) {
      img.src = alt;
      return;
    }
    img.hidden = true;
  };
  img.src = src;
}

const ARROW_UP = "↑";
const ARROW_DOWN = "↓";

function signedArrow(n) {
  const v = Number(n);
  if (!Number.isFinite(v) || v === 0) return "";
  return v > 0 ? ARROW_UP : ARROW_DOWN;
}

function fmtAbs(n, digits = 4) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  const num = Math.abs(Number(n));
  if (num >= 1000) return num.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
  return num.toLocaleString("pt-BR", { maximumFractionDigits: digits });
}

function fmt(n, digits = 4) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  const num = Number(n);
  if (Math.abs(num) >= 1000) return num.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
  return num.toLocaleString("pt-BR", { maximumFractionDigits: digits });
}

/** PnL/UPL: seta ↑/↓ + valor absoluto sempre com 3 casas (ex. ↓ 0,090). */
function fmtPnl(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  const v = Number(n);
  const arrow = signedArrow(v);
  const body = Math.abs(v).toLocaleString("pt-BR", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  });
  return arrow ? `${arrow} ${body}` : body;
}

/** Variação %: seta ↑/↓ em vez de +/−. */
function fmtPct(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  const v = Number(n);
  const arrow = signedArrow(v);
  const body = `${Math.abs(v).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
  return arrow ? `${arrow} ${body}` : body;
}

function fmtVol(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  const v = Number(n);
  if (v >= 1e9) return `${(v / 1e9).toLocaleString("pt-BR", { maximumFractionDigits: 2 })}B`;
  if (v >= 1e6) return `${(v / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 2 })}M`;
  if (v >= 1e3) return `${(v / 1e3).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}K`;
  return fmt(v, 2);
}

function fmtPx(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  const num = Number(n);
  if (num === 0) return "0";
  if (Math.abs(num) >= 1) return fmt(num, 4);
  return num.toLocaleString("pt-BR", { maximumFractionDigits: 10, minimumFractionDigits: 2 });
}

function fmtQty(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  const v = Number(n);
  if (Math.abs(v) >= 1e6) return `${(v / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 2 })}M`;
  if (Math.abs(v) >= 1e3) return fmt(v, 2);
  return fmt(v, 6);
}

function quoteButtonsHtml(active) {
  const quotes = ["USDT", "BRL", "USDC", "BTC", "ETH", ...walletQuoteCcys(), "ALL"];
  return quotes.map((q) => {
    const label = q === "ALL" ? "Todos" : q;
    return `<button type="button" data-quote="${q}" class="${q === active ? "on" : ""}">${label}</button>`;
  }).join("");
}

const TZ_SP = "America/Sao_Paulo";

function parseUtcDate(ts) {
  if (ts instanceof Date) return Number.isNaN(ts.getTime()) ? null : ts;
  let s = String(ts || "").trim();
  if (!s) return null;
  if (/^\d{4}-\d{2}-\d{2} \d/.test(s)) s = s.replace(" ", "T");
  if (/^\d{4}-\d{2}-\d{2}T/.test(s) && !/[zZ]|[+-]\d{2}:?\d{2}$/.test(s)) s += "Z";
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
}

function fmtTs(ts) {
  const d = parseUtcDate(ts);
  if (!d) return "—";
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ_SP,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(d);
  const get = (t) => parts.find((p) => p.type === t)?.value || "";
  return `${get("year")}-${get("month")}-${get("day")} ${get("hour")}:${get("minute")}:${get("second")}`;
}

function fmtIntervalMin(min) {
  const m = Number(min) || 0;
  if (m >= 60 && m % 60 === 0) return `a cada ${m / 60}h`;
  if (m >= 60) return `a cada ${fmt(m / 60, 1)}h`;
  return `a cada ${fmt(m, 0)} min`;
}

function fmtRunDays(days) {
  const d = Number(days);
  if (!d) return "sem limite";
  return d === 1 ? "1 dia" : `${fmt(d, 0)} dias`;
}

const BOT_RUN_DAY_PRESETS = [7, 15, 30, 60, 90];

function normalizeBotRunDays(days) {
  const d = Number(days) || 7;
  if (BOT_RUN_DAY_PRESETS.includes(d)) return d;
  return BOT_RUN_DAY_PRESETS.reduce(
    (best, p) => (Math.abs(p - d) < Math.abs(best - d) ? p : best),
    BOT_RUN_DAY_PRESETS[0],
  );
}

function syncBotRunDaysSeg(days) {
  const d = normalizeBotRunDays(days);
  const hidden = $("bot-run-days-val");
  if (hidden) hidden.value = String(d);
  document.querySelectorAll("#bot-run-days button[data-days]").forEach((btn) => {
    btn.classList.toggle("on", Number(btn.dataset.days) === d);
  });
}

function fmtRemaining(sec) {
  if (sec == null) return null;
  const s = Math.max(0, Number(sec) || 0);
  const days = Math.floor(s / 86400);
  const hours = Math.floor((s % 86400) / 3600);
  if (days > 0) return `${days}d ${hours}h restantes`;
  const mins = Math.floor((s % 3600) / 60);
  if (hours > 0) return `${hours}h ${mins}min restantes`;
  return `${Math.max(1, mins)} min restantes`;
}

function botScheduleText(b) {
  const every = fmtIntervalMin(b.interval_min ?? (b.poll_interval ? b.poll_interval / 60 : 5));
  const dur = fmtRunDays(b.run_days);
  if (!b.running) return `${every} · ${dur}`;
  const rem = fmtRemaining(b.run_remaining_sec);
  return rem ? `${every} · ${rem}` : `${every} · ${dur}`;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 401 && !String(path).startsWith("/api/auth")) {
    showLoginGate();
    const parsed = parseApiError({ detail: "faça login com Google" }, res.statusText, "");
    throw new ApiError(parsed.message, parsed);
  }
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = { detail: text }; }
  if (!res.ok) {
    const parsed = parseApiError(data, res.statusText, text);
    throw new ApiError(parsed.message, parsed);
  }
  return data;
}

class ApiError extends Error {
  constructor(message, meta = {}) {
    super(message);
    this.name = "ApiError";
    this.summary = meta.summary || message;
    this.friendly = meta.friendly || "";
    this.technical = meta.technical || meta.full || message;
    this.full = meta.full || this.technical;
    this.code = meta.code || "";
    this.scode = meta.scode || "";
    this.cancel_gone = !!meta.cancel_gone;
  }
}

function parseApiError(data, statusText, rawText = "") {
  const d = data?.detail;
  if (d && typeof d === "object" && !Array.isArray(d)) {
    const message = (d.message || d.summary || d.friendly || d.msg || "").trim();
    const friendly = (d.friendly || "").trim();
    const technical = (d.technical || d.full || "").trim();
    const summary = friendly || message || technical;
    if (summary || technical) {
      return {
        message: summary || technical,
        summary: summary || technical,
        friendly,
        technical: technical && technical !== summary ? technical : "",
        full: technical && technical !== summary ? technical : "",
        code: d.code || "",
        scode: d.scode || "",
        cancel_gone: !!d.cancel_gone,
      };
    }
  }
  if (typeof d === "string" && d.trim()) {
    const msg = d.trim();
    return { message: msg, summary: msg, full: msg, code: "" };
  }
  if (Array.isArray(d)) {
    const parts = d.map((item) => {
      if (typeof item === "string") return item;
      const loc = Array.isArray(item.loc)
        ? item.loc.filter((x) => x !== "body").join(".")
        : "";
      const msg = item.msg || item.message || "";
      return loc && msg ? `${loc}: ${msg}` : (msg || "");
    }).filter(Boolean);
    if (parts.length) {
      const msg = parts.join(" · ");
      return { message: msg, summary: msg, full: msg, code: "" };
    }
  }
  if (typeof data?.message === "string" && data.message.trim()) {
    const msg = data.message.trim();
    return { message: msg, summary: msg, full: msg, code: "" };
  }
  if (typeof rawText === "string" && rawText.trim() && !rawText.trim().startsWith("{")) {
    const msg = rawText.trim();
    return { message: msg, summary: msg, full: msg, code: "" };
  }
  const msg = statusText || "Erro desconhecido";
  return { message: msg, summary: msg, full: msg, code: "" };
}

function showErrorModal(err, { title = "Erro", flashId } = {}) {
  const friendly = err?.friendly || err?.summary || err?.message || "Erro desconhecido";
  const technical = err?.technical || err?.full || friendly;
  const scode = err?.scode || err?.code || "";
  if (flashId) flash(flashId, friendly, false);
  openAppModal({
    title,
    hint: scode ? `Código OKX ${scode}` : "",
    errorFull: friendly,
    errorTechnical: technical !== friendly ? technical : "",
    hideConfirm: true,
    cancelLabel: "Fechar",
    action: null,
  });
}

async function withRefresh(btn, work, opts = {}) {
  const el = typeof btn === "string" ? $(btn) : btn;
  if (!el) return work();
  if (el.classList.contains("is-refreshing") || el.classList.contains("is-busy")) return;
  const status = opts.statusId ? $(opts.statusId) : null;
  const prevStatus = status ? status.textContent : "";
  const prevTitle = el.getAttribute("title") || "";
  const prevHtml = el.innerHTML;
  const busy = !!opts.busyLabel;
  el.classList.add(busy ? "is-busy" : "is-refreshing");
  el.disabled = true;
  el.setAttribute("aria-busy", "true");
  el.setAttribute("title", opts.busyLabel || "Atualizando…");
  if (busy) {
    el.innerHTML = `<span class="btn-spin" aria-hidden="true"></span><span>${escHtml(opts.busyLabel)}</span>`;
  }
  if (status) status.textContent = opts.statusText || opts.busyLabel || "Atualizando…";
  try {
    return await work();
  } finally {
    el.classList.remove("is-refreshing", "is-busy");
    el.disabled = false;
    el.removeAttribute("aria-busy");
    if (prevTitle) el.setAttribute("title", prevTitle);
    else el.removeAttribute("title");
    if (busy) el.innerHTML = prevHtml;
    if (status && (status.textContent === (opts.statusText || opts.busyLabel || "Atualizando…"))) {
      status.textContent = prevStatus;
    }
  }
}

function quoteFromInst(inst) {
  return String(inst || "").split("-")[1] || "USDT";
}

function setUsdtBrlRate(rate) {
  const n = rate == null ? null : Number(rate);
  if (n != null && !Number.isNaN(n) && n > 0) usdtBrlRate = n;
}

async function ensureFxRate() {
  if (usdtBrlRate) return usdtBrlRate;
  if (lastPnlData?.usdt_brl) setUsdtBrlRate(lastPnlData.usdt_brl);
  if (usdtBrlRate) return usdtBrlRate;
  try {
    const fx = await api("/api/fx");
    if (fx?.rate) setUsdtBrlRate(fx.rate);
  } catch {
    /* cotação opcional */
  }
  return usdtBrlRate;
}

function toBrl(amount, currency = "USD") {
  if (amount == null || Number.isNaN(Number(amount))) return null;
  const c = String(currency || "USD").toUpperCase();
  const n = Number(amount);
  if (c === "BRL") return n;
  if ((c === "USD" || c === "USDT" || c === "USDC") && usdtBrlRate) return n * usdtBrlRate;
  return null;
}

// Conversão alternativa: se quote é BRL → mostra USD; se USD/USDT → mostra BRL
function toAltCcy(amount, quoteCcy) {
  if (amount == null || Number.isNaN(Number(amount))) return null;
  const q = String(quoteCcy || "USDT").toUpperCase();
  const n = Number(amount);
  if (q === "BRL" && usdtBrlRate && usdtBrlRate > 0) {
    return { value: n / usdtBrlRate, symbol: "US$", code: "USD" };
  }
  if ((q === "USD" || q === "USDT" || q === "USDC") && usdtBrlRate) {
    return { value: n * usdtBrlRate, symbol: "R$", code: "BRL" };
  }
  return null;
}

function setKpiSub(el, amount, currency = "USD") {
  if (!el) return;
  const brl = toBrl(amount, currency);
  if (brl == null) {
    el.textContent = "";
    el.className = "kpi-sub";
    return;
  }
  const arrow = signedArrow(brl);
  el.textContent = `${arrow ? `${arrow} ` : ""}${fmtAbs(brl, 2)} BRL`;
  el.className = `kpi-sub ${brl > 0 ? "up" : brl < 0 ? "down" : ""}`;
}

function brlSubHtml(amount, currency = "USD") {
  const brl = toBrl(amount, currency);
  if (brl == null) return "";
  const tone = brl > 0 ? "up" : brl < 0 ? "down" : "";
  const arrow = signedArrow(brl);
  return `<small class="money-sub ${tone}">${arrow ? `${arrow} ` : ""}${fmtAbs(brl, 2)} BRL</small>`;
}

function setToneMoney(el, n, subEl, currency = "USD", digits = 2) {
  if (!el) return;
  if (n == null || Number.isNaN(Number(n))) {
    el.textContent = "—";
    el.className = "";
    if (subEl) setKpiSub(subEl, null);
    return;
  }
  const shown = digits >= 3 ? fmtPnl(n) : `${signedArrow(n) ? `${signedArrow(n)} ` : ""}${fmtAbs(n, digits)}`;
  el.textContent = `${shown} USD`;
  el.className = Number(n) > 0 ? "up" : Number(n) < 0 ? "down" : "";
  if (subEl) setKpiSub(subEl, n, currency);
}

function setTonePnl(el, n, subEl, currency = "USD", pct = null) {
  if (!el) return;
  if (n == null || Number.isNaN(Number(n))) {
    el.textContent = "—";
    el.className = "";
    if (subEl) setKpiSub(subEl, null);
    return;
  }
  const shown = fmtPnl(n);
  const pctTxt = pct == null || Number.isNaN(Number(pct)) ? "" : ` (${fmtPct(pct)})`;
  el.textContent = `${shown} USD${pctTxt}`;
  el.className = Number(n) > 0 ? "up" : Number(n) < 0 ? "down" : "";
  if (subEl) setKpiSub(subEl, n, currency);
}

function pnlForPeriod(data, period) {
  if (!data) return null;
  const map = {
    today: data.pnl_today ?? data.wallet_pnl_today,
    "24h": data.pnl_24h ?? data.wallet_pnl_24h,
    week: data.pnl_week ?? data.wallet_pnl_week,
    month: data.pnl_month ?? data.wallet_pnl_month,
  };
  const v = map[period];
  return v == null || Number.isNaN(Number(v)) ? null : Number(v);
}

/** Variação % do PnL vs patrimônio no início do período. */
function pnlPctOfEquity(pnl, totalEq) {
  if (pnl == null || totalEq == null) return null;
  const v = Number(pnl);
  const eq = Number(totalEq);
  if (!Number.isFinite(v) || !Number.isFinite(eq)) return null;
  const base = eq - v;
  if (base > 1e-9) return (v / base) * 100;
  if (eq > 1e-9) return (v / eq) * 100;
  return null;
}

/** Ratio OKX (0.012) ou % já em escala 100 → número para fmtPct. */
function uplRatioToPct(ratio) {
  if (ratio == null || Number.isNaN(Number(ratio))) return null;
  const r = Number(ratio);
  if (!Number.isFinite(r)) return null;
  return Math.abs(r) <= 2 ? r * 100 : r;
}

function assetUplPct(a) {
  if (!a) return null;
  const fromRatio = uplRatioToPct(a.spot_upl_ratio);
  if (fromRatio != null) return fromRatio;
  const avg = Number(a.avg_px);
  const last = Number(a.last);
  if (avg > 0 && Number.isFinite(last)) return ((last - avg) / avg) * 100;
  return null;
}

function renderPnlColumn(data) {
  const periods = [
    ["today", "Hoje"],
    ["24h", "24h"],
    ["week", "Semana"],
    ["month", "Mês"],
  ];
  const eq = data?.total_eq ?? data?.wallet_eq;
  const hasEq = eq != null;
  for (const id of ["w-pnl-col", "m-wallet-pnl-col"]) {
    const el = $(id);
    if (!el) continue;
    const tiles = el.classList.contains("pnl-col-tiles");
    if (!hasEq) {
      el.innerHTML = periods.map(([_, label]) =>
        tiles
          ? `<div class="pnl-tile"><span class="pnl-tile-k">${label}</span><strong class="pnl-tile-v">—</strong></div>`
          : `<div class="pnl-col-row"><span>${label}</span><strong>—</strong></div>`,
      ).join("");
      continue;
    }
    el.innerHTML = periods.map(([key, label]) => {
      const v = pnlForPeriod(data, key);
      const cls = v > 0 ? "up" : v < 0 ? "down" : "";
      const txt = v == null ? "—" : fmtPnl(v);
      const pct = v != null ? pnlPctOfEquity(v, eq) : null;
      const pctTxt = pct == null ? null : fmtPct(pct);
      const brl = v != null ? toBrl(v) : null;
      const brlHtml = brl != null
        ? `<small class="pnl-col-brl ${cls}">${signedArrow(brl) ? `${signedArrow(brl)} ` : ""}R$ ${fmtAbs(brl, 2)}</small>`
        : "";
      if (tiles) {
        return `<div class="pnl-tile">
          <span class="pnl-tile-k">${label}</span>
          <strong class="pnl-tile-v ${cls}">${pctTxt ?? txt}</strong>
          <span class="pnl-tile-unit">${v == null ? "" : `${txt} USD`}</span>
          ${brlHtml}
        </div>`;
      }
      const main = pctTxt != null ? `${pctTxt}` : `${txt} USD`;
      const money = pctTxt != null && v != null
        ? `<small class="pnl-col-money ${cls}">${txt} USD</small>`
        : "";
      return `<div class="pnl-col-row"><span>${label}</span><div class="pnl-col-val"><strong class="${cls}">${main}</strong>${money}${brlHtml}</div></div>`;
    }).join("");
  }
}

function repaintPnlKpis() {
  if (lastPnlData) renderPnlColumn(lastPnlData);
}

function renderPnlKpi(data) {
  if (data) {
    lastPnlData = { ...(lastPnlData || {}), ...data };
    if (data.usdt_brl != null) setUsdtBrlRate(data.usdt_brl);
  }
  renderPnlColumn(lastPnlData);
}

function flash(id, text, ok) {
  const el = $(id);
  if (!el) return;
  el.innerHTML = text ? `<span class="${ok ? "ok" : "err"}">${escHtml(text)}</span>` : "";
}

function pageId() {
  let hash = (location.hash || "#/wallet").replace("#/", "");
  if (hash === "keys") {
    if (location.hash !== "#/config") location.replace("#/config");
    return "config";
  }
  if (hash === "bot") return "overview";
  if (hash === "trades") {
    if (location.hash !== "#/orders") location.replace("#/orders");
    return "orders";
  }
  if (hash === "charts") {
    if (location.hash !== "#/wallet") location.replace("#/wallet");
    return "wallet";
  }
  return TITLES[hash] ? hash : "wallet";
}

function showPage(id) {
  document.querySelectorAll(".page").forEach((el) => el.classList.toggle("active", el.id === `page-${id}`));
  document.querySelectorAll(".nav a").forEach((a) => a.classList.toggle("active", a.dataset.page === id));
  $("page-title").textContent = TITLES[id][0];
  $("page-sub").textContent = TITLES[id][1];
  document.title = `OKBot · ${TITLES[id][0]}`;
  if ($("run-label")) $("run-label").hidden = false;
  if ($("mode-label") && lastStatus?.keys_configured) $("mode-label").hidden = false;
  if (id === "overview") refresh({ trades: true });
  if (id === "wallet") loadWallet();
  if (id === "config") loadConfig();
  if (id === "orders") loadOrders();
  if (id === "tokens") loadTokens();
  if (id === "lab") {
    renderLabControls();
    ensureLabTokens();
    if (lastLabResult) renderLabResult(lastLabResult);
  }
  if (id === "strategies") {
    renderStratControls();
    ensureStratReady();
  }
  if (id === "hunter") loadHunter();
  if (id === "profile") loadProfile();
  if (id === "docs") {
    initDocsPage();
    const jump = sessionStorage.getItem("okx_docs_jump");
    if (jump) {
      sessionStorage.removeItem("okx_docs_jump");
      setTimeout(() => {
        const el = document.getElementById(jump);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 40);
    } else {
      const main = document.querySelector(".main");
      if (main) main.scrollTop = 0;
    }
  }
}

function setRunningUI(runningCount) {
  lastRunningCount = Number(runningCount) || 0;
  applyKeysLock();
  const el = $("run-label");
  if (!el) return;
  if (!botsOn()) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  const active = runningCount > 0;
  el.textContent = active ? "Bot ativo" : "Parado";
  el.className = `pill ${active ? "on" : "off"}`;
  el.title = active
    ? "Há um bot rodando agora · só um ativo por vez"
    : "Nenhum bot em execução";
  el.setAttribute("aria-label", el.title);
}

function isLiveMode(flag) {
  return String(flag ?? "0") === "0";
}

function modeLabelHtml(live, label) {
  const kind = live ? "live" : "demo";
  const text = label || (live ? "Live" : "Demo");
  return `<span class="mode-inline"><span class="mode-dot ${kind}" aria-hidden="true"></span>${text}</span>`;
}

function setModeUI(okxFlag, configured = true) {
  const el = $("mode-label");
  if (!el) return;
  if (!configured) {
    el.hidden = true;
    el.title = "Configure as API Keys para ver o modo Live/Demo";
    return;
  }
  const live = isLiveMode(okxFlag);
  el.hidden = false;
  el.className = `pill mode-pill ${live ? "on" : "warn"}`;
  const dot = el.querySelector(".mode-dot");
  if (dot) dot.className = `mode-dot ${live ? "live" : "demo"}`;
  const text = el.querySelector(".mode-text");
  if (text) text.textContent = live ? "Live" : "Demo";
  el.title = live
    ? "Conta OKX em modo Live · ordens reais"
    : "Conta OKX em modo Demo · simulação, sem dinheiro real";
  el.setAttribute("aria-label", el.title);
}

function selectBotModalToken(instId, icon, iconAlt) {
  const form = $("app-modal-form");
  if (!form) return;
  const inst = (instId || "").toUpperCase();
  form.inst_id.value = inst;
  const base = inst.split("-")[0] || "";
  const quote = inst.split("-")[1] || "";
  if (quote) botModalQuote = quote;
  $("bot-token-label").textContent = inst || "Escolher par";
  const hint = $("bot-quote-hint");
  if (hint) hint.textContent = quote ? `(${quote})` : "";
  setIcon(
    $("bot-token-icon"),
    icon || (base ? `https://www.okx.com/cdn/oksupport/asset/currency/icon/${base.toLowerCase()}.png` : ""),
    iconAlt || (base ? `https://static.okx.com/cdn/wallet/logo/${base.toUpperCase()}.png` : ""),
  );
  renderBotQuoteSeg();
  clearBotAnalyzeResults();
}

let lastBotAnalyzeResult = null;
let botAnalyzeRunning = false;

function clearBotAnalyzeResults() {
  lastBotAnalyzeResult = null;
  const box = $("bot-analyze-results");
  if (box) {
    box.hidden = true;
    box.innerHTML = "";
  }
  const msg = $("bot-analyze-msg");
  if (msg) {
    msg.hidden = true;
    msg.textContent = "";
    msg.className = "flash";
  }
}

function botAnalyzeRowsHtml(rows) {
  if (!rows.length) return `<div class="hint">Nenhuma estratégia no ranking.</div>`;
  return rows.map((r, i) => {
    const sum = r.summary || {};
    const strat = r.strategy || {};
    const ok = !!sum.recommend_create;
    const assert = Number(sum.assertiveness);
    return `<div class="strat-rank-row ${i === 0 ? "best" : ""}">
      <div class="strat-rank-pos">${i === 0 ? "★" : i + 1}</div>
      <div class="strat-rank-main">
        <div class="strat-rank-title">
          ${stratIcon(strat)}
          <strong>${escHtml(strat.name || "—")}${i === 0 ? " · melhor" : ""}</strong>
        </div>
        <small>queda ${fmt(r.params?.buy_pct, 2)}% · alvo ${fmt(r.params?.profit_target_pct, 2)}% · ${escHtml(strat.tag || strat.style || "")}</small>
      </div>
      <div class="strat-rank-metrics">
        <div class="strat-rank-metric">
          <span>Retorno</span>
          <strong class="${Number(sum.capital_return_pct) > 0 ? "up" : Number(sum.capital_return_pct) < 0 ? "down" : ""}">${fmt(sum.capital_return_pct, 2)}%</strong>
        </div>
        <div class="strat-rank-metric">
          <span>Assert.</span>
          <strong class="${assert >= 70 ? "up" : ""}">${fmt(assert, 0)}</strong>
        </div>
        <div class="strat-rank-metric">
          <span>Ciclos</span>
          <strong>${sum.cycles_closed ?? 0}</strong>
        </div>
      </div>
      <div class="strat-rank-actions">
        <span class="pill ${ok ? "on" : sum.verdict === "revisar" ? "warn" : "bad"}">${ok ? "Aprovada" : (sum.grade || sum.verdict || "—")}</span>
        <button type="button" class="btn btn-primary" data-bot-analyze-use="${escHtml(strat.id)}">Usar</button>
      </div>
    </div>`;
  }).join("");
}

function renderBotAnalyzeResults(res) {
  lastBotAnalyzeResult = res;
  const box = $("bot-analyze-results");
  if (!box) return;
  const rows = res.results || [];
  const best = rows[0];
  const meta =
    `${res.inst_id || "—"} · ${res.days || "?"}d · ${res.candles || 0} candles · ` +
    `${res.approved_count || 0} aprovada(s) · aporte ${escHtml(res.aporte_note || String(res.aporte || ""))}`;
  box.hidden = false;
  box.innerHTML =
    `<p class="bot-analyze-meta">${meta}</p>` +
    (best
      ? `<p class="bot-analyze-meta">Melhor: <strong>${escHtml(best.strategy?.name || "—")}</strong> · ${fmt(best.summary?.capital_return_pct, 2)}% · assert. ${fmt(best.summary?.assertiveness, 0)}</p>`
      : "") +
    botAnalyzeRowsHtml(rows.slice(0, 8));
}

function applyBotAnalyzeStrategy(strategyId) {
  const form = $("app-modal-form");
  if (!form || !strategyId) return;
  const row = (lastBotAnalyzeResult?.results || []).find((r) => r.strategy?.id === strategyId);
  const sel = $("bot-strategy-select");
  if (sel) {
    const opt = [...sel.options].find((o) => o.value === strategyId);
    if (opt) sel.value = strategyId;
  }
  applyStrategyToBotForm(strategyId);
  if (row?.params) {
    if (row.params.buy_pct != null) form.buy_pct.value = row.params.buy_pct;
    if (row.params.profit_target_pct != null) form.profit_target_pct.value = row.params.profit_target_pct;
    if (row.params.fee_rate_pct != null) form.fee_rate_pct.value = row.params.fee_rate_pct;
  }
  const name = row?.strategy?.name || strategyId;
  flash("bot-analyze-msg", `Estratégia “${name}” aplicada no formulário`, true);
  const msg = $("bot-analyze-msg");
  if (msg) msg.hidden = false;
}

async function runBotModalAnalyze() {
  if (botAnalyzeRunning) return;
  const form = $("app-modal-form");
  if (!form) return;
  const inst = String(form.inst_id?.value || "").trim().toUpperCase();
  if (!inst.includes("-")) {
    flash("bot-analyze-msg", "Escolha um par Spot primeiro", false);
    const msg = $("bot-analyze-msg");
    if (msg) msg.hidden = false;
    return;
  }
  await ensureBotStrategies();
  const days = normalizeBotRunDays(Number($("bot-run-days-val")?.value || form.run_days?.value || 7));
  const aporteRaw = Number(form.quote_amount?.value);
  const aporte = Number.isFinite(aporteRaw) && aporteRaw > 0 ? aporteRaw : 50;
  botAnalyzeRunning = true;
  const msgEl = $("bot-analyze-msg");
  if (msgEl) msgEl.hidden = false;
  await withRefresh("btn-bot-analyze", async () => {
    try {
      const res = await api("/api/strategies/validate", {
        method: "POST",
        body: JSON.stringify({
          inst_id: inst,
          days,
          aporte,
          aporte_ccy: "USDT",
          sort: "profit",
        }),
      });
      renderBotAnalyzeResults(res);
      const best = (res.results || [])[0];
      flash(
        "bot-analyze-msg",
        best
          ? `Melhor: ${best.strategy?.name} · ${fmt(best.summary?.capital_return_pct, 2)}% · assert. ${fmt(best.summary?.assertiveness, 0)}`
          : "Sem resultados",
        !!best,
      );
    } catch (err) {
      clearBotAnalyzeResults();
      flash("bot-analyze-msg", err.message || "Falha na análise", false);
      if (msgEl) msgEl.hidden = false;
    }
  }, { busyLabel: "Analisando…", statusId: "bot-analyze-msg", statusText: "Validando estratégias no histórico…" });
  botAnalyzeRunning = false;
}

async function ensureBotStrategies() {
  if (stratCatalog.length) return stratCatalog;
  try {
    const res = await api("/api/strategies");
    stratCatalog = res.strategies || [];
  } catch (_) {
    stratCatalog = [];
  }
  return stratCatalog;
}

function populateBotStrategySelect(selectedId) {
  const sel = $("bot-strategy-select");
  if (!sel) return;
  const sid = String(selectedId || "").toLowerCase();
  const opts = [`<option value="">Manual (definir % abaixo)</option>`].concat(
    (stratCatalog || []).map((s) => {
      const on = String(s.id).toLowerCase() === sid ? " selected" : "";
      const tag = s.custom ? " · custom" : "";
      return `<option value="${escHtml(s.id)}"${on}>${escHtml(s.name)}${tag}</option>`;
    }),
  );
  sel.innerHTML = opts.join("");
}

function syncBotEntryModeSeg(mode) {
  const m = mode === "base" ? "base" : "quote";
  const hidden = $("bot-entry-mode-val");
  if (hidden) hidden.value = m;
  document.querySelectorAll("#bot-entry-mode button[data-entry]").forEach((btn) => {
    btn.classList.toggle("on", btn.getAttribute("data-entry") === m);
  });
}

function equalCascadeSteps(pct) {
  const p = Math.max(5, Math.min(100, Number(pct) || 20));
  const n = Math.max(1, Math.min(10, Math.round(100 / p)));
  if (n <= 1) return [100];
  const steps = Array(n - 1).fill(p);
  steps.push(Math.max(5, 100 - p * (n - 1)));
  return steps;
}

function parseCascadePctsInput(raw) {
  const s = String(raw || "").trim();
  if (!s) return null;
  const parts = s.split(/[,;\s]+/).map((x) => Number(String(x).replace("%", ""))).filter((n) => !Number.isNaN(n) && n > 0);
  return parts.length ? parts : null;
}

function resolvedCascadePcts(side) {
  const form = $("app-modal-form");
  const customOn = $(`bot-cascade-${side}-custom`)?.checked;
  if (customOn) {
    const parsed = parseCascadePctsInput(form?.[`cascade_${side}_pcts_raw`]?.value);
    if (parsed?.length) return parsed;
  }
  const pct = Number(form?.[`cascade_${side}_pct`]?.value || (side === "buy" ? 20 : 25));
  return equalCascadeSteps(pct);
}

function fmtCascadePlan(pcts) {
  if (!pcts?.length) return "";
  const sum = pcts.reduce((a, b) => a + b, 0);
  const allSame = pcts.every((p) => p === pcts[0]);
  if (allSame) return `${pcts.length} etapas de ${fmt(pcts[0], 0)}% · total ${fmt(sum, 0)}%`;
  return `${pcts.map((p) => `${fmt(p, 0)}%`).join(" + ")} = ${fmt(sum, 0)}%`;
}

function syncCascadeChipActive(side) {
  const form = $("app-modal-form");
  const pct = Number(form?.[`cascade_${side}_pct`]?.value);
  document.querySelectorAll(`#bot-cascade-${side}-chips button[data-pct]`).forEach((btn) => {
    btn.classList.toggle("on", Number(btn.dataset.pct) === pct);
  });
}

function syncBotCascadePreview() {
  for (const side of ["buy", "sell"]) {
    const planEl = $(`bot-cascade-${side}-plan`);
    const wrap = $(`bot-cascade-${side}-custom-wrap`);
    const customOn = $(`bot-cascade-${side}-custom`)?.checked;
    if (wrap) wrap.hidden = !customOn;
    if (!planEl) continue;
    const pcts = resolvedCascadePcts(side);
    const sum = pcts.reduce((a, b) => a + b, 0);
    planEl.textContent = fmtCascadePlan(pcts);
    planEl.classList.toggle("warn", sum > 100.01 || pcts.some((p) => p < 5 || p > 100) || pcts.length > 10);
    if (sum > 100.01) planEl.textContent += " · soma acima de 100%";
    else if (pcts.length > 10) planEl.textContent += " · máximo 10 etapas";
    syncCascadeChipActive(side);
  }
}

function fillBotCascadeFields(b = {}) {
  const form = $("app-modal-form");
  if (!form) return;
  if (form.cascade_buy_pct) form.cascade_buy_pct.value = b.cascade_buy_pct ?? 20;
  if (form.cascade_sell_pct) form.cascade_sell_pct.value = b.cascade_sell_pct ?? 25;
  const buyCustom = Array.isArray(b.cascade_buy_pcts) && b.cascade_buy_pcts.length > 0;
  const sellCustom = Array.isArray(b.cascade_sell_pcts) && b.cascade_sell_pcts.length > 0;
  if ($("bot-cascade-buy-custom")) $("bot-cascade-buy-custom").checked = buyCustom;
  if ($("bot-cascade-sell-custom")) $("bot-cascade-sell-custom").checked = sellCustom;
  if (form.cascade_buy_pcts_raw) {
    form.cascade_buy_pcts_raw.value = buyCustom ? b.cascade_buy_pcts.join(", ") : "";
  }
  if (form.cascade_sell_pcts_raw) {
    form.cascade_sell_pcts_raw.value = sellCustom ? b.cascade_sell_pcts.join(", ") : "";
  }
}

function readCascadePctsPayload(side) {
  if ($(`bot-cascade-${side}-custom`)?.checked) {
    return parseCascadePctsInput($("app-modal-form")?.[`cascade_${side}_pcts_raw`]?.value);
  }
  return null;
}

function cascadeSummary(b, side) {
  const pcts = Array.isArray(b[`cascade_${side}_pcts`]) && b[`cascade_${side}_pcts`].length
    ? b[`cascade_${side}_pcts`]
    : equalCascadeSteps(b[`cascade_${side}_pct`] ?? (side === "buy" ? 20 : 25));
  return fmtCascadePlan(pcts);
}

function strategyCascadeCapable(s) {
  if (!s) return false;
  if (s.cascade_capable != null) return !!s.cascade_capable;
  const id = String(s.id || "").toLowerCase();
  if (id === "scalp" || id === "micro_scalp") return false;
  return Number(s.buy_pct) >= 1.5 && Number(s.profit_target_pct) >= 0.5;
}

function cascadeEnabledFromForm() {
  const cb = $("bot-cascade-enabled");
  if (cb) return cb.checked;
  return false;
}

function syncBotCascadeSeg(on) {
  const cb = $("bot-cascade-enabled");
  if (cb) cb.checked = !!on;
}

function ensureCascadeCapableStrategy() {
  if (selectedBotStrategy()?.cascade_capable) return true;
  const pick =
    (stratCatalog || []).find((s) => s.id === "balanced" && strategyCascadeCapable(s))
    || (stratCatalog || []).find((s) => strategyCascadeCapable(s));
  const sel = $("bot-strategy-select");
  if (!pick || !sel) return false;
  sel.value = pick.id;
  applyStrategyToBotForm(pick.id);
  return true;
}

function setCascadeElVisible(el, visible, display) {
  if (!el) return;
  el.hidden = !visible;
  el.style.display = visible ? (display || "") : "none";
}

function selectedBotStrategy() {
  const sel = $("bot-strategy-select");
  const sid = (sel?.value || "").trim();
  if (!sid) {
    const form = $("app-modal-form");
    const buy = Number(form?.buy_pct?.value || 0);
    const target = Number(form?.profit_target_pct?.value || 0);
    return buy >= 1.5 && target >= 0.5 ? { id: "", cascade_capable: true, name: "Manual" } : null;
  }
  const s = (stratCatalog || []).find((x) => String(x.id) === sid);
  if (!s) return null;
  return { ...s, cascade_capable: strategyCascadeCapable(s) };
}

function syncBotCascadeUI() {
  const fields = $("bot-cascade-fields");
  const hint = $("bot-cascade-hint");
  const form = $("app-modal-form");
  if (!form) return;
  const strat = selectedBotStrategy();
  const capable = !!strat?.cascade_capable;
  const on = cascadeEnabledFromForm();
  setCascadeElVisible(fields, on && capable, "grid");
  if (!hint) return;
  if (on && capable) {
    syncBotCascadePreview();
    hint.textContent = strat?.name
      ? `Ativo · «${strat.name}» — escolha % por etapa ou personalize abaixo.`
      : "Ativo — escolha % por etapa ou personalize abaixo.";
  } else if (!capable && strat) {
    hint.textContent = `«${strat.name}» não suporta cascata. Ligue o toggle para trocar para Equilibrada.`;
  } else {
    hint.textContent = "Compras escalonadas na queda e vendas parciais no lucro.";
  }
}

function applyStrategyToBotForm(strategyId) {
  const form = $("app-modal-form");
  if (!form) return;
  const s = (stratCatalog || []).find((x) => String(x.id) === String(strategyId));
  if (!s) return;
  form.buy_pct.value = s.buy_pct ?? form.buy_pct.value;
  form.profit_target_pct.value = s.profit_target_pct ?? form.profit_target_pct.value;
  form.fee_rate_pct.value = s.fee_rate_pct ?? form.fee_rate_pct.value;
  if (!form.name.value || form.name.value === "Novo bot") {
    form.name.value = `Bot ${s.name}`;
  }
  if (!strategyCascadeCapable(s)) syncBotCascadeSeg(false);
  syncBotCascadeUI();
}

function fillBotModalForm(b = {}) {
  const form = $("app-modal-form");
  form.bot_id.value = b.bot_id || "";
  form.name.value = b.name || "Novo bot";
  const amt = b.quote_amount;
  form.quote_amount.value = amt === 0 || amt === "0" ? "" : (amt ?? "");
  form.buy_pct.value = b.buy_pct ?? 2;
  form.profit_target_pct.value = b.profit_target_pct ?? 1;
  form.fee_rate_pct.value = b.fee_rate_pct ?? 0.10;
  form.interval_min.value = b.interval_min ?? 5;
  syncBotRunDaysSeg(b.run_days ?? 7);
  form.portfolio_interval_min.value = b.portfolio_interval_min ?? 2;
  syncBotEntryModeSeg(b.entry_mode || "quote");
  populateBotStrategySelect(b.strategy_id || "");
  syncBotCascadeSeg(!!b.cascade_enabled);
  fillBotCascadeFields(b);
  selectBotModalToken(b.inst_id || orderInst() || "BTC-USDT", b.icon, b.icon_alt);
  syncBotCascadeUI();
}

function readBotFormPayload() {
  const form = $("app-modal-form");
  const entryRaw = String(form.quote_amount.value || "").trim();
  const entryMode = ($("bot-entry-mode-val")?.value || "quote");
  const strategyId = (form.strategy_id?.value || "").trim() || null;
  return {
    name: form.name.value.trim(),
    inst_id: form.inst_id.value.trim().toUpperCase(),
    strategy_id: strategyId,
    buy_pct: Number(form.buy_pct.value),
    profit_target_pct: Number(form.profit_target_pct.value),
    fee_rate_pct: Number(form.fee_rate_pct.value),
    quote_amount: entryRaw === "" ? 0 : Number(entryRaw),
    entry_mode: entryMode === "base" ? "base" : "quote",
    interval_min: Number(form.interval_min.value),
    run_days: Number(form.run_days.value),
    portfolio_interval_min: Number(form.portfolio_interval_min.value),
    cascade_enabled: cascadeEnabledFromForm(),
    cascade_buy_pct: Number(form.cascade_buy_pct?.value || 20),
    cascade_sell_pct: Number(form.cascade_sell_pct?.value || 25),
    cascade_buy_pcts: readCascadePctsPayload("buy"),
    cascade_sell_pcts: readCascadePctsPayload("sell"),
  };
}

function setBotModalLocked(locked) {
  const form = $("app-modal-form");
  for (const el of form.querySelectorAll("input, button, select")) {
    if (el.id === "bot-token-search") {
      el.disabled = !!locked;
      continue;
    }
    el.disabled = !!locked;
  }
  $("bot-token-btn").disabled = !!locked;
  $("app-modal-confirm").disabled = !!locked;
  syncBotCascadeUI();
}

function botPnlText(b) {
  const quote = quoteFromInst(b.inst_id);
  if (b.state === "long" && b.pnl != null) {
    return {
      text: `${fmtPct(b.pnl_pct)} · ${fmtPnl(b.pnl)}`,
      tone: b.pnl >= 0 ? "up" : "down",
      brlSub: quote !== "BRL" ? brlSubHtml(b.pnl, quote) : "",
    };
  }
  if (b.token_upl != null) {
    return {
      text: `${fmtPnl(b.token_upl)}`,
      tone: b.token_upl >= 0 ? "up" : "down",
      brlSub: quote !== "BRL" ? brlSubHtml(b.token_upl, quote) : "",
    };
  }
  const realized = Number(b.realized_pnl || 0);
  if (realized) {
    return {
      text: `Real. ${fmt(realized, 2)}`,
      tone: realized >= 0 ? "up" : "down",
      brlSub: quote !== "BRL" ? brlSubHtml(realized, quote) : "",
    };
  }
  return { text: "0,00", tone: "", brlSub: "" };
}

const EXEC_ACTION = {
  buy: "Comprar",
  sell: "Vender",
  wait_buy: "Aguarda queda",
  wait_sell: "Aguarda PnL",
  set_ref: "Define ref.",
};

function botExecutionsRowsHtml(rows) {
  const list = Array.isArray(rows) ? rows : [];
  lastBotExecutions = list;
  if (!list.length) {
    return `<tr><td class="empty" colspan="5">Nenhuma execução ainda.</td></tr>`;
  }
  return list.map((e, idx) => {
    const act = EXEC_ACTION[e.action] || e.action || "—";
    const cls = e.executed ? "buy" : e.would_trade ? "" : "muted";
    const decision = e.executed ? "Ordem enviada" : (e.would_trade ? "Iria operar" : "Sem ordem");
    const manual = e.manual || e.trigger === "manual" || String(e.reason || "").toLowerCase().startsWith("[manual]");
    const actLabel = manual ? `${act} · manual` : act;
    return `<tr class="exec-row" data-exec-idx="${idx}">
      <td>${fmtTs(e.ts)}</td>
      <td class="${cls}">${escHtml(actLabel)}${manual ? ` <span class="pill exec-manual-pill" title="Ciclo disparado manualmente">manual</span>` : ""}</td>
      <td title="${escHtml(e.reason || "")}">${escHtml(e.reason || decision)}</td>
      <td>${fmt(e.price, 6)}</td>
      <td>${e.poll_interval != null ? (e.poll_interval >= 60 ? `${fmt(e.poll_interval / 60, 0)} min` : `${fmt(e.poll_interval, 0)}s`) : "—"}</td>
    </tr>`;
  }).join("");
}

function openExecutionModal(exec) {
  if (!exec) return;
  const mode = exec.mode === "test" ? "Teste" : modeLabelHtml(true);
  const act = EXEC_ACTION[exec.action] || exec.action || "—";
  const decision = exec.executed ? "Executada" : (exec.would_trade ? "Iria operar" : "Não operou");
  const manual = exec.manual || exec.trigger === "manual" || String(exec.reason || "").toLowerCase().startsWith("[manual]");
  const checks = Array.isArray(exec.checks) ? exec.checks : [];
  const checkRows = checks.length
    ? checks.map((c) => [
      c?.ok ? "OK" : "Falhou",
      `${c?.label || "Regra"}${c?.detail ? ` · ${c.detail}` : ""}`,
      c?.ok ? "buy" : "sell",
    ])
    : [["Checks", "Sem checks detalhados", ""]];

  openAppModal({
    title: `Execução · ${act}${manual ? " · manual" : ""}`,
    hint: manual ? "Ciclo disparado manualmente (botão Executar agora)." : "Decisão do bot neste ciclo.",
    rich: true,
    hideConfirm: true,
    cancelLabel: "Fechar",
    kpis: [
      { label: "Decisão", value: decision, tone: exec.executed ? "up" : "" },
      { label: "Origem", value: manual ? "Manual" : "Automático" },
      { label: "Preço", value: exec.price != null ? fmt(exec.price, 6) : "—" },
    ],
    sections: [
      {
        title: "Contexto",
        rows: [
          ["Data/hora", fmtTs(exec.ts)],
          ["Modo", mode],
          ["Origem", manual ? "Manual (botão)" : "Automático (intervalo)"],
          ["Par", exec.inst_id || "—"],
          ["Estado", exec.state || "—"],
          ["Ação", act],
          ["Motivo", exec.reason || "—"],
          ["Queda", exec.drop_pct != null ? `${fmt(exec.drop_pct, 2)}%` : "—"],
          ["Alvo", exec.target_price != null ? fmt(exec.target_price, 6) : "—"],
          ["Intervalo", exec.poll_interval != null ? `${fmt(exec.poll_interval, 0)}s` : "—"],
        ],
      },
      {
        title: "Regras",
        rows: checkRows,
      },
    ],
    action: null,
  });
}

function sortBotsActiveFirst(bots) {
  return [...(bots || [])].sort((a, b) => Number(!!b.running) - Number(!!a.running));
}

function openBotPanel(id) {
  if (!id) return;
  selectedBotId = id;
  botDetailVisible = true;
  localStorage.setItem("okx_bot_id", id);
  if (lastStatus?.bots) renderBots(lastStatus.bots);
}

function closeBotPanel() {
  botDetailVisible = false;
  if (lastStatus?.bots) renderBots(lastStatus.bots);
}

function toggleBotExpand(id) {
  if (!id) return;
  if (botDetailVisible && selectedBotId === id) {
    closeBotPanel();
    return;
  }
  openBotPanel(id);
}

function renderBots(bots) {
  const list = sortBotsActiveFirst(bots);
  const box = $("bots-list");
  if (!box) return;

  if (botDetailVisible && !list.some((b) => b.bot_id === selectedBotId)) {
    botDetailVisible = false;
  }
  const expandedId = botDetailVisible ? selectedBotId : "";

  if (!list.length) {
    lastBotExecutions = [];
    box.innerHTML = `<div class="hint">Nenhum bot. Use <strong>Novo bot</strong> para criar o primeiro.</div>`;
    return;
  }

  box.innerHTML = list.map((b) => {
    const pos = b.state === "long" ? "Long" : "Aguardando";
    const run = b.running ? "Ativo" : "Parado";
    const runCls = b.running ? "on" : "off";
    const open = expandedId && b.bot_id === expandedId;
    const cascade = b.cascade_enabled ? `<span class="pill cascade-tag">cascata</span>` : "";
    const expand = open
      ? `<div class="bot-expand">
          <div class="bot-expand-actions">
            <button class="btn ${b.running ? "btn-primary stop" : "btn-primary"} btn-icon" data-act="${b.running ? "stop" : "start"}" type="button"${!b.running && b.okx_account_active === false ? " disabled title=\"Ative a conta deste bot em Configurações\"" : ""}>${b.running ? "Pause" : "Play"}</button>
            <button class="btn btn-ghost btn-icon" data-act="tick" type="button" title="${b.okx_account_active === false ? "Ative a conta deste bot em Configurações" : "Roda um ciclo agora · fica marcado como manual"}"${b.okx_account_active === false ? " disabled" : ""}>Executar agora</button>
            <button class="btn btn-ghost btn-icon" data-act="edit" type="button">Editar</button>
            <button class="btn btn-ghost btn-icon" data-act="detail" type="button">Info</button>
            <button class="btn btn-ghost btn-icon" data-act="delete" type="button"${b.running ? " disabled title=\"Pause antes de apagar\"" : ""}>Apagar</button>
          </div>
          <div class="bot-expand-exec-h">
            <strong>Execuções</strong>
            <span class="hint" style="margin:0">Clique numa linha para detalhe</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Ação</th>
                  <th>Motivo</th>
                  <th>Preço</th>
                  <th>Intervalo</th>
                </tr>
              </thead>
              <tbody>${botExecutionsRowsHtml(b.executions || [])}</tbody>
            </table>
          </div>
        </div>`
      : "";
    return `<div class="bot-item${open ? " open" : ""}" data-id="${b.bot_id}">
      <div class="bot-row" role="button" tabindex="0" aria-expanded="${open ? "true" : "false"}">
        <div class="bot-main">
          <img class="token-icon" src="${b.icon || ""}" alt="" onerror="this.onerror=null;this.src='${b.icon_alt || ""}'" />
          <div>
            <strong>${cascade}<span>${escHtml(b.name || "Bot")}</span></strong>
            <small>${escHtml(b.inst_id || "—")} · ${pos}${(lastKeys?.accounts || []).length > 1 && b.okx_account_name ? ` · ${escHtml(b.okx_account_name)}` : ""}</small>
          </div>
        </div>
        <div class="bot-actions">
          <span class="pill bot-status-pill ${runCls}">${run}</span>
          <span class="bot-row-chevron" aria-hidden="true">${open ? "▾" : "›"}</span>
        </div>
      </div>
      ${expand}
    </div>`;
  }).join("");

  if (!expandedId) lastBotExecutions = [];
}

function renderStatus(s) {
  lastStatus = s;
  applyBotsEnabled();
  setUsdtBrlRate(s.usdt_brl);
  setModeUI(s.okx_flag, s.keys_configured);
  const bots = s.bots || [];
  const runningCount = bots.filter((b) => b.running).length;
  setRunningUI(runningCount);
  renderBots(bots);
  syncPollInterval(runningCount > 0);
  if (lastWallet && pageId() === "wallet") renderWallet(lastWallet);
  if (pageId() === "lab") renderLabControls();
  if (s.wallet_error) flash("msg", s.wallet_error, false);
  else if ($("msg") && !$("msg").dataset.keep) flash("msg", "", true);
}

function originCell(row) {
  const kind = row.origin === "user" ? "user" : row.origin === "bot" ? "bot" : "";
  const label = row.origin_label || (row.origin === "user" ? "Usuário" : "—");
  return `<span class="origin ${kind}">${label}</span>`;
}

let labDays = Number(localStorage.getItem("okx_lab_days") || 30);
let labRunning = false;
let labTlFilter = "all";
let lastLabResult = null;
let labAporte = Number(localStorage.getItem("okx_lab_aporte") || 300);
let labAporteCcy = localStorage.getItem("okx_lab_aporte_ccy") || "USDT";
let labInstId = localStorage.getItem("okx_lab_inst") || "SOL-USDT";
let labBuyPct = Number(localStorage.getItem("okx_lab_buy") || 2);
let labTargetPct = Number(localStorage.getItem("okx_lab_target") || 1);
let labFeePct = Number(localStorage.getItem("okx_lab_fee") || 0.1);
let labStratSort = localStorage.getItem("okx_lab_strat_sort") || "profit";
let labTokens = [];
let labTokensLoaded = false;
let lastLabStratResult = null;

const LAB_ACTION = {
  set_ref: "Define ref.",
  buy: "Comprou",
  sell: "Vendeu",
  skip_buy: "Não comprou",
  skip_sell: "Não vendeu",
};

function syncLabInputsFromState() {
  document.querySelectorAll("#lab-days button").forEach((btn) => {
    btn.classList.toggle("on", Number(btn.dataset.days) === labDays);
  });
  const aporteInput = $("lab-aporte");
  const aporteCcy = $("lab-aporte-ccy");
  if (aporteInput && document.activeElement !== aporteInput) aporteInput.value = String(labAporte);
  if (aporteCcy) aporteCcy.value = labAporteCcy;
  const buyEl = $("lab-buy-pct");
  const tgtEl = $("lab-target-pct");
  const feeEl = $("lab-fee-pct");
  if (buyEl && document.activeElement !== buyEl) buyEl.value = String(labBuyPct);
  if (tgtEl && document.activeElement !== tgtEl) tgtEl.value = String(labTargetPct);
  if (feeEl && document.activeElement !== feeEl) feeEl.value = String(labFeePct);
  const hint = $("lab-aporte-hint");
  if (hint) {
    const q = (labInstId || "").split("-")[1] || "USDT";
    hint.textContent = labAporteCcy === "USDT"
      ? `Caixa em USDT (convertido p/ ${q} se preciso). All-in a cada compra.`
      : `Caixa direto em ${q}. All-in a cada compra.`;
  }
  const createBtn = $("btn-lab-create-bot");
  if (createBtn) createBtn.hidden = !lastLabResult;
}

function renderLabTokens() {
  const box = $("lab-tokens");
  if (!box) return;
  if (!labTokens.length) {
    box.innerHTML = `<span class="hint">Sugestões…</span>`;
    return;
  }
  const available = labTokens.filter((t) => t.available !== false);
  // Não sobrescreve par escolhido via busca (mesmo se não estiver nas sugestões)
  const selectedInList = available.some((t) => t.inst_id === labInstId);
  box.innerHTML = available.map((t) => {
    const on = t.inst_id === labInstId ? "on" : "";
    const title = t.inst_id || t.symbol || "";
    const sym = t.symbol || (t.inst_id || "").split("-")[0] || "?";
    return `<button type="button" class="lab-token ${on}" data-inst="${escHtml(t.inst_id)}" title="${escHtml(title)}">
      <img src="${t.icon || ""}" alt="" draggable="false" onerror="this.onerror=null;this.src='${t.icon_alt || ""}'" />
      <span>${escHtml(sym)}</span>
    </button>`;
  }).join("");
  const th = $("lab-token-hint");
  if (th) {
    th.textContent = selectedInList || !labInstId
      ? "Busque qualquer par Spot ou use as sugestões"
      : `Selecionado: ${labInstId}`;
  }
}

function selectLabInst(inst, meta = {}) {
  const id = String(inst || "").trim().toUpperCase();
  if (!id.includes("-")) return;
  labInstId = id;
  localStorage.setItem("okx_lab_inst", labInstId);
  const search = $("lab-token-search");
  if (search) search.value = labInstId;
  const results = $("lab-token-results");
  if (results) {
    results.hidden = true;
    results.innerHTML = "";
  }
  // Garante chip do token buscado na lista de sugestões
  if (!labTokens.some((t) => t.inst_id === labInstId)) {
    labTokens = [
      {
        inst_id: labInstId,
        symbol: labInstId.split("-")[0],
        available: true,
        icon: meta.icon || "",
        icon_alt: meta.icon_alt || "",
      },
      ...labTokens,
    ];
  }
  renderLabTokens();
  syncLabInputsFromState();
  flash("lab-msg", `Token ${labInstId}`, true);
}

let labTokenSearchTimer = null;

async function searchLabTokens(q) {
  const box = $("lab-token-results");
  if (!box) return;
  const query = String(q || "").trim();
  if (query.length < 1) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }
  box.hidden = false;
  box.innerHTML = `<div class="hint" style="margin:8px">Buscando…</div>`;
  try {
    const data = await api(`/api/instruments?quote=USDT&q=${encodeURIComponent(query)}`);
    let rows = data.instruments || [];
    // Se buscou com quote explícita (ex. BOME-BRL), amplia
    if (query.includes("-")) {
      const all = await api(`/api/instruments?quote=ALL&q=${encodeURIComponent(query)}`);
      const extra = all.instruments || [];
      const seen = new Set(rows.map((r) => r.inst_id));
      for (const r of extra) {
        if (!seen.has(r.inst_id)) {
          rows.push(r);
          seen.add(r.inst_id);
        }
      }
    }
    if (!rows.length) {
      box.innerHTML = `<div class="hint" style="margin:8px">Nenhum par encontrado</div>`;
      return;
    }
    box.innerHTML = rows.slice(0, 24).map((p) => {
      const chg = p.chg24 == null ? "" : fmtPct(p.chg24);
      const tone = p.chg24 > 0 ? "up" : p.chg24 < 0 ? "down" : "";
      return `<button type="button" class="token-item${p.inst_id === labInstId ? " on" : ""}" data-lab-pick="${escHtml(p.inst_id)}" data-icon="${escHtml(p.icon || "")}" data-alt="${escHtml(p.icon_alt || "")}">
        <img class="token-icon" src="${escHtml(p.icon || "")}" alt="" onerror="this.onerror=null;this.src='${escHtml(p.icon_alt || "")}'" />
        <span><span class="sym">${escHtml(p.base || "")}</span><div class="meta">${escHtml(p.inst_id || "")}</div></span>
        <span class="chg ${tone}">${chg}</span>
      </button>`;
    }).join("");
  } catch (err) {
    box.innerHTML = `<div class="flash"><span class="err">${escHtml(err.message)}</span></div>`;
  }
}

async function ensureLabTokens() {
  if (labTokensLoaded && labTokens.length) {
    renderLabTokens();
    return;
  }
  try {
    const res = await api("/api/lab/tokens");
    labTokens = res.tokens || [];
    labTokensLoaded = true;
    renderLabTokens();
    const search = $("lab-token-search");
    if (search && !search.value && labInstId) search.placeholder = `Atual: ${labInstId} · buscar outro…`;
  } catch (err) {
    const box = $("lab-tokens");
    if (box) box.innerHTML = `<span class="hint">${escHtml(err.message || "Falha ao listar tokens")}</span>`;
  }
}

function renderLabControls() {
  syncLabInputsFromState();
  syncLabStratSortSeg();
  renderLabTokens();
}

function readLabForm() {
  const aporteEl = $("lab-aporte");
  const ccyEl = $("lab-aporte-ccy");
  const buyEl = $("lab-buy-pct");
  const tgtEl = $("lab-target-pct");
  const feeEl = $("lab-fee-pct");
  if (aporteEl) labAporte = Math.max(1, Number(aporteEl.value) || 300);
  if (ccyEl) labAporteCcy = ccyEl.value === "quote" ? "quote" : "USDT";
  if (buyEl) labBuyPct = Math.min(50, Math.max(0.1, Number(buyEl.value) || 2));
  if (tgtEl) labTargetPct = Math.min(50, Math.max(0.1, Number(tgtEl.value) || 1));
  if (feeEl) labFeePct = Math.min(5, Math.max(0, Number(feeEl.value) || 0.1));
  localStorage.setItem("okx_lab_aporte", String(labAporte));
  localStorage.setItem("okx_lab_aporte_ccy", labAporteCcy);
  localStorage.setItem("okx_lab_buy", String(labBuyPct));
  localStorage.setItem("okx_lab_target", String(labTargetPct));
  localStorage.setItem("okx_lab_fee", String(labFeePct));
  localStorage.setItem("okx_lab_inst", labInstId);
  localStorage.setItem("okx_lab_days", String(labDays));
}

function renderLabTimeline(res) {
  const body = $("lab-timeline");
  if (!body) return;
  let rows = res.timeline || [];
  if (labTlFilter === "exec") rows = rows.filter((r) => r.executed);
  if (labTlFilter === "skip") rows = rows.filter((r) => !r.executed && (r.action === "skip_buy" || r.action === "skip_sell"));
  if (!rows.length) {
    body.innerHTML = `<tr><td class="empty" colspan="7">Nenhum evento neste filtro.</td></tr>`;
    return;
  }
  body.innerHTML = rows.map((r) => {
    const act = LAB_ACTION[r.action] || r.action || "—";
    const cls = r.executed ? (r.action === "buy" ? "buy" : r.action === "sell" ? "sell" : "") : "muted";
    const drop = r.drop_pct != null ? `${fmt(r.drop_pct, 2)}%` : "—";
    const pnl = r.pnl_pct != null ? `${fmt(r.pnl_pct, 2)}%` : "—";
    let gate = "—";
    if (r.buy_trigger != null) gate = `compra ≤ ${fmt(r.buy_trigger, 6)}`;
    if (r.target_price != null) gate = `venda ≥ ${fmt(r.target_price, 6)}`;
    return `<tr>
      <td>${fmtTs(r.ts)}</td>
      <td class="${cls}">${act}</td>
      <td>${fmt(r.price, 6)}</td>
      <td>${drop}</td>
      <td>${pnl}</td>
      <td>${gate}</td>
      <td title="${escHtml(r.reason || "")}">${escHtml(r.reason || "—")}</td>
    </tr>`;
  }).join("");
}

function syncLabStratSortSeg() {
  document.querySelectorAll("#lab-strat-sort button[data-sort]").forEach((btn) => {
    btn.classList.toggle("on", btn.dataset.sort === labStratSort);
  });
}

function setLabView(mode) {
  const compare = $("lab-strat-compare");
  const single = $("lab-single-result");
  if (compare) compare.hidden = mode !== "compare";
  if (single) single.hidden = mode !== "single";
}

function stratRankRowsHtml(rows, context = "strat") {
  if (!rows.length) {
    return `<div class="hint">Nenhuma estratégia no ranking.</div>`;
  }
  return rows.map((r, i) => {
    const sum = r.summary || {};
    const strat = r.strategy || {};
    const ok = !!sum.recommend_create;
    const assert = Number(sum.assertiveness);
    const medal = i === 0 ? " 🏆" : "";
    return `<div class="strat-rank-row ${i === 0 ? "best" : ""}">
      <div class="strat-rank-pos">${i === 0 ? "★" : i + 1}</div>
      <div class="strat-rank-main">
        <div class="strat-rank-title">
          ${stratIcon(strat)}
          <strong>${escHtml(strat.name || "—")}${medal}</strong>
        </div>
        <small>queda ${fmt(r.params?.buy_pct, 2)}% · alvo ${fmt(r.params?.profit_target_pct, 2)}% · ${escHtml(strat.tag || strat.style || "")}</small>
      </div>
      <div class="strat-rank-metrics">
        <div class="strat-rank-metric">
          <span>Retorno</span>
          <strong class="${Number(sum.capital_return_pct) > 0 ? "up" : Number(sum.capital_return_pct) < 0 ? "down" : ""}">${fmt(sum.capital_return_pct, 2)}%</strong>
        </div>
        <div class="strat-rank-metric">
          <span>PnL</span>
          <strong class="${Number(sum.total_pnl) > 0 ? "up" : Number(sum.total_pnl) < 0 ? "down" : ""}">${fmt(sum.total_pnl, 2)}</strong>
        </div>
        <div class="strat-rank-metric">
          <span>Assert.</span>
          <strong class="${assert >= 70 ? "up" : ""}">${fmt(assert, 0)}</strong>
        </div>
        <div class="strat-rank-metric">
          <span>Ciclos</span>
          <strong>${sum.cycles_closed ?? 0}</strong>
        </div>
      </div>
      <div class="strat-rank-actions">
        <span class="pill ${ok ? "on" : sum.verdict === "revisar" ? "warn" : "bad"}">${ok ? "Aprovada" : (sum.grade || sum.verdict || "—")}</span>
        <button type="button" class="btn btn-ghost" data-${context}-strat-run="${escHtml(strat.id)}">Detalhe</button>
        <button type="button" class="btn btn-primary js-bots-ui" data-${context}-strat-bot="${escHtml(strat.id)}">Criar bot</button>
      </div>
    </div>`;
  }).join("");
}

function fillWinnerBanner(prefix, row, res) {
  const st = row?.strategy || {};
  const s = row?.summary || {};
  const title = $(`${prefix}-winner-title`);
  const sub = $(`${prefix}-winner-sub`);
  const retEl = $(`${prefix}-winner-ret`);
  const pnlEl = $(`${prefix}-winner-pnl`);
  const assertEl = $(`${prefix}-winner-assert`);
  const cyclesEl = $(`${prefix}-winner-cycles`);
  const banner = prefix === "lab" ? $("lab-strat-compare") : $("strat-winner-banner");
  if (!row || !title) {
    if (banner && prefix === "strat") $("strat-winner-banner").hidden = true;
    return;
  }
  if (prefix === "strat" && $("strat-winner-banner")) $("strat-winner-banner").hidden = false;
  title.innerHTML = `${stratIcon(st)}<span>${escHtml(st.name || "—")}</span>`;
  if (sub) {
    sub.textContent =
      `${res?.inst_id || "—"} · ${res?.days || "?"}d · queda ${fmt(row.params?.buy_pct, 2)}% · alvo ${fmt(row.params?.profit_target_pct, 2)}% · ` +
      (s.recommend_create ? "recomendada para bot" : (s.verdict === "revisar" ? "revisar antes de operar" : "abaixo do ideal"));
  }
  const ret = Number(s.capital_return_pct);
  if (retEl) {
    retEl.textContent = Number.isFinite(ret) ? `${fmt(ret, 2)}%` : "—";
    retEl.className = ret > 0 ? "up" : ret < 0 ? "down" : "";
  }
  if (pnlEl) {
    pnlEl.textContent = fmt(s.total_pnl, 2);
    pnlEl.className = Number(s.total_pnl) > 0 ? "up" : Number(s.total_pnl) < 0 ? "down" : "";
  }
  const a = Number(s.assertiveness);
  if (assertEl) {
    assertEl.textContent = Number.isFinite(a) ? `${fmt(a, 0)}/100` : "—";
    assertEl.className = a >= 70 ? "up" : a >= 50 ? "" : "down";
  }
  if (cyclesEl) cyclesEl.textContent = String(s.cycles_closed ?? "—");
}

function labStratRowById(id) {
  return (lastLabStratResult?.results || []).find((r) => r.strategy?.id === id) || null;
}

function renderLabStratCompare(res) {
  lastLabStratResult = res;
  const empty = $("lab-empty");
  const results = $("lab-results");
  if (empty) empty.hidden = true;
  if (results) results.hidden = false;
  setLabView("compare");

  const rows = res.results || [];
  const best = rows[0] || null;
  fillWinnerBanner("lab", best, res);

  const meta = $("lab-rank-meta");
  if (meta) {
    meta.textContent =
      `${res.inst_id || labInstId} · ${res.days || labDays}d · ${rows.length} estratégias · ` +
      `ordenado por ${res.sort === "assert" ? "assertividade" : "lucro"} · ${res.approved_count || 0} aprovada(s)`;
  }

  const rank = $("lab-strat-rank");
  if (rank) rank.innerHTML = stratRankRowsHtml(rows, "lab");

  const runBtn = $("btn-lab-winner-run");
  const botBtn = $("btn-lab-winner-bot");
  if (runBtn) runBtn.hidden = !best;
  if (botBtn) {
    botBtn.hidden = !best;
    botBtn.textContent = best ? `Criar bot · ${best.strategy?.name || "melhor"}` : "Criar bot";
  }
}

function renderLabResult(res) {
  lastLabResult = res;
  setLabView("single");
  const s = res.summary || {};
  const q = s.quality || {};
  const quote = res.quote || "";
  const empty = $("lab-empty");
  const results = $("lab-results");
  if (empty) empty.hidden = true;
  if (results) results.hidden = false;

  const capEl = $("lab-capital");
  if (capEl) {
    capEl.textContent = `${fmt(s.capital_start ?? res.aporte ?? labAporte, 2)} → ${fmt(s.capital_end ?? 0, 2)} ${quote}`;
    capEl.title = capEl.textContent;
  }
  const retEl = $("lab-return");
  if (retEl) {
    const r = Number(s.capital_return_pct);
    retEl.textContent = Number.isFinite(r) ? `${fmt(r, 2)}%` : "—";
    retEl.className = r > 0 ? "up" : r < 0 ? "down" : "";
  }
  const assertEl = $("lab-assert");
  const assertSub = $("lab-assert-sub");
  if (assertEl) {
    const a = Number(q.assertiveness);
    assertEl.textContent = Number.isFinite(a) ? `${fmt(a, 0)}/100` : "—";
    assertEl.className = a >= 70 ? "up" : a >= 50 ? "" : "down";
  }
  if (assertSub) {
    const grade = q.grade ? `Grau ${q.grade}` : "";
    const cycles = s.cycles_closed != null ? `${s.cycles_closed} ciclos` : "";
    assertSub.textContent = [grade, cycles].filter(Boolean).join(" · ") || "—";
  }
  const totalEl = $("lab-total");
  if (totalEl) {
    totalEl.textContent = `${fmt(s.total_pnl, 4)} ${quote}`;
    totalEl.className = Number(s.total_pnl) > 0 ? "up" : Number(s.total_pnl) < 0 ? "down" : "";
    totalEl.title = totalEl.textContent;
  }

  const badge = $("lab-badge");
  if (badge) {
    const v = q.verdict || (s.validated ? "aprovado" : (s.cycles_closed ? "revisar" : "reprovado"));
    const labels = { aprovado: "PnL OK · lucro", revisar: "Revisar params", reprovado: "Sem garantia" };
    badge.textContent = labels[v] || v;
    badge.className = `pill ${v === "aprovado" ? "on" : v === "revisar" ? "warn" : "bad"}`;
  }
  $("lab-summary-title").textContent =
    `${res.inst_id || labInstId} · queda ${fmt(res.buy_pct ?? labBuyPct, 2)}% · alvo ${fmt(res.profit_target_pct ?? labTargetPct, 2)}% · ${res.days || labDays}d` +
    (res.strategy_name ? ` · ${res.strategy_name}` : "");
  $("lab-summary-text").textContent = q.note || s.validation_note || "";
  $("lab-summary-meta").textContent =
    `${res.aporte_note || `aporte ${fmt(res.aporte, 2)} ${quote}`} · ` +
    `${res.candles || 0} candles (${res.bar || "—"}) · ` +
    `não comprou ${s.skips_buy ?? 0}x · não vendeu ${s.skips_sell ?? 0}x`;

  const checksEl = $("lab-quality-checks");
  if (checksEl) {
    const checks = q.checks || [];
    if (!checks.length) {
      checksEl.hidden = true;
      checksEl.innerHTML = "";
    } else {
      checksEl.hidden = false;
      checksEl.innerHTML = checks.map((c) => {
        const ok = !!c.ok;
        return `<li class="${ok ? "ok" : "fail"}">
          <span class="mark">${ok ? "✓" : "✗"}</span>
          <span><strong>${escHtml(c.label || "")}</strong><small>${escHtml(c.detail || "")}</small></span>
        </li>`;
      }).join("");
    }
  }

  const createBtn = $("btn-lab-create-bot");
  if (createBtn) {
    createBtn.hidden = !botsOn();
    createBtn.textContent = q.recommend_create
      ? "Criar bot (aprovado)"
      : "Criar bot mesmo assim";
    createBtn.className = q.recommend_create
      ? "btn btn-primary btn-cta js-bots-ui"
      : "btn btn-ghost btn-cta js-bots-ui";
  }

  const metrics = $("lab-metrics");
  if (metrics) {
    const open = res.open_position;
    const comp = q.components || {};
    metrics.innerHTML = [
      ["Assertividade", Number.isFinite(Number(q.assertiveness)) ? `${fmt(q.assertiveness, 0)}/100 (${q.grade || "—"})` : "—"],
      ["Hit rate alvo", `${fmt(q.hit_rate_pct ?? s.win_rate_pct, 0)}%`],
      ["Lucro travado", q.profit_locked ? "Sim" : "Não"],
      ["Aporte", `${fmt(s.capital_start, 2)} ${quote}`],
      ["Caixa final", `${fmt(s.capital_end, 2)} ${quote}`],
      ["Retorno", `${fmt(s.capital_return_pct, 2)}%`],
      ["Compras / vendas", `${s.buys ?? 0} / ${s.sells ?? 0}`],
      ["Score alvo / lucro", `${fmt(comp.hit_score, 0)} / ${fmt(comp.profit_score, 0)}`],
      ["Score amostra / fim", `${fmt(comp.sample_score, 0)} / ${fmt(comp.completion_score, 0)}`],
      ["PnL realizado", `${fmt(s.realized_pnl, 4)} ${quote}`],
      ["PnL aberto", open ? `${fmt(open.pnl, 4)} ${quote}` : "—"],
      ["Não comprou / vendeu", `${s.skips_buy ?? 0} / ${s.skips_sell ?? 0}`],
    ].map(([k, v]) => `<div class="lab-metric"><span>${k}</span><strong title="${escHtml(String(v))}">${v}</strong></div>`).join("");
  }

  const cyclesBody = $("lab-cycles-body");
  const cycles = res.cycles || [];
  if (cyclesBody) {
    if (!cycles.length) {
      cyclesBody.innerHTML = `<tr><td class="empty" colspan="9">Nenhum ciclo completo. Veja gatilhos: por que não comprou/vendeu.</td></tr>`;
    } else {
      cyclesBody.innerHTML = cycles.map((c) => {
        const pnlCls = c.pnl > 0 ? "buy" : c.pnl < 0 ? "sell" : "";
        return `<tr>
          <td>${c.n}</td>
          <td>${fmtTs(c.buy_ts)}</td>
          <td>${fmtTs(c.sell_ts)}</td>
          <td>${fmt(c.buy_price, 6)} → ${fmt(c.sell_price, 6)}</td>
          <td>${fmt(c.spent, 2)}</td>
          <td>${fmt(c.received, 2)}</td>
          <td class="${pnlCls}">${fmt(c.pnl, 4)}</td>
          <td class="${pnlCls}">${fmt(c.pnl_pct, 2)}%</td>
          <td class="${c.hit_target ? "buy" : "sell"}">${c.hit_target ? "Sim" : "Não"}</td>
        </tr>`;
      }).join("");
    }
  }

  renderLabTimeline(res);

  const body = $("lab-trades");
  const trades = res.trades || [];
  if (body) {
    if (!trades.length) {
      body.innerHTML = `<tr><td class="empty" colspan="8">Nenhuma compra/venda efetivada no período.</td></tr>`;
    } else {
      body.innerHTML = trades.map((t) => {
        const cls = t.side === "buy" ? "buy" : "sell";
        const pnl = t.pnl == null ? "—" : `${fmt(t.pnl, 4)}${t.pnl_pct != null ? ` (${fmt(t.pnl_pct, 2)}%)` : ""}`;
        const pnlCls = t.pnl > 0 ? "buy" : t.pnl < 0 ? "sell" : "";
        return `<tr>
          <td>${fmtTs(t.ts)}</td>
          <td class="${cls}">${String(t.side || "").toUpperCase()}</td>
          <td>${fmt(t.price, 6)}</td>
          <td>${fmt(t.qty, 6)}</td>
          <td>${fmt(t.quote, 2)}</td>
          <td>${fmt(t.fee_est, 4)}</td>
          <td class="${pnlCls}">${pnl}</td>
          <td title="${escHtml(t.reason || "")}">${escHtml(t.reason || "—")}</td>
        </tr>`;
      }).join("");
    }
  }
}

async function openLabForBot(id, days = 30) {
  const b = botById(id);
  labDays = Number(days) || 30;
  if (b) {
    labInstId = String(b.inst_id || labInstId).toUpperCase();
    labBuyPct = Number(b.buy_pct) || labBuyPct;
    labTargetPct = Number(b.profit_target_pct) || labTargetPct;
    labFeePct = Number(b.fee_rate_pct) || labFeePct;
    if (b.quote_amount) labAporte = Number(b.quote_amount) || labAporte;
    selectedBotId = id;
    localStorage.setItem("okx_bot_id", id);
  }
  localStorage.setItem("okx_lab_days", String(labDays));
  localStorage.setItem("okx_lab_inst", labInstId);
  localStorage.setItem("okx_lab_buy", String(labBuyPct));
  localStorage.setItem("okx_lab_target", String(labTargetPct));
  localStorage.setItem("okx_lab_fee", String(labFeePct));
  if (location.hash !== "#/lab") {
    location.hash = "#/lab";
    await new Promise((r) => setTimeout(r, 40));
  }
  await ensureLabTokens();
  renderLabControls();
  await runLabSimulate();
}

async function runLabSimulate() {
  if (labRunning) return;
  readLabForm();
  if (!labInstId || !labInstId.includes("-")) {
    flash("lab-msg", "Escolha um token", false);
    return;
  }
  const tok = labTokens.find((t) => t.inst_id === labInstId);
  if (tok && !tok.available) {
    flash("lab-msg", `${tok.symbol} não tem par spot na OKX`, false);
    return;
  }
  labRunning = true;
  flash(
    "lab-msg",
    `Simulando ${labInstId} · ${labDays}d · aporte ${labAporte} · queda ${labBuyPct}% · alvo ${labTargetPct}%…`,
    true,
  );
  await withRefresh("btn-lab-run", async () => {
    try {
      const res = await api("/api/lab/simulate", {
        method: "POST",
        body: JSON.stringify({
          inst_id: labInstId,
          days: labDays,
          aporte: labAporte,
          aporte_ccy: labAporteCcy,
          buy_pct: labBuyPct,
          profit_target_pct: labTargetPct,
          fee_rate_pct: labFeePct,
        }),
      });
      renderLabResult(res);
      flash("lab-msg", `Simulação ${labDays}d · ${res.aporte_note || ""}`, true);
    } catch (err) {
      flash("lab-msg", err.message, false);
    }
  }, { busyLabel: "Simulando…", statusId: "lab-msg", statusText: "Simulando…" });
  labRunning = false;
}

async function runLabCompareStrategies() {
  if (labRunning) return;
  readLabForm();
  if (!labInstId || !labInstId.includes("-")) {
    flash("lab-msg", "Escolha um token", false);
    return;
  }
  const tok = labTokens.find((t) => t.inst_id === labInstId);
  if (tok && !tok.available) {
    flash("lab-msg", `${tok.symbol} não tem par spot na OKX`, false);
    return;
  }
  labRunning = true;
  await withRefresh("btn-lab-compare", async () => {
    try {
      const res = await api("/api/strategies/validate", {
        method: "POST",
        body: JSON.stringify({
          inst_id: labInstId,
          days: labDays,
          aporte: labAporte,
          aporte_ccy: labAporteCcy,
          sort: labStratSort,
        }),
      });
      renderLabStratCompare(res);
      const best = (res.results || [])[0];
      flash(
        "lab-msg",
        best
          ? `Melhor: ${best.strategy?.name} · retorno ${fmt(best.summary?.capital_return_pct, 2)}% · assert. ${fmt(best.summary?.assertiveness, 0)}/100`
          : "Nenhuma estratégia retornou resultado",
        !!best,
      );
    } catch (err) {
      flash("lab-msg", err.message, false);
    }
  }, { busyLabel: "Comparando…", statusId: "lab-msg", statusText: "Comparando estratégias…" });
  labRunning = false;
}

async function runLabDetailForStratRow(row) {
  if (!row) return;
  const p = row.params || {};
  labInstId = String(p.inst_id || labInstId).toUpperCase();
  labBuyPct = Number(p.buy_pct) || labBuyPct;
  labTargetPct = Number(p.profit_target_pct) || labTargetPct;
  labFeePct = Number(p.fee_rate_pct) || labFeePct;
  labAporte = Number(p.aporte || labAporte) || labAporte;
  labDays = Number(p.days || labDays) || labDays;
  renderLabControls();
  labRunning = true;
  await withRefresh("btn-lab-winner-run", async () => {
    try {
      const res = await api("/api/lab/simulate", {
        method: "POST",
        body: JSON.stringify({
          inst_id: labInstId,
          days: labDays,
          aporte: labAporte,
          aporte_ccy: labAporteCcy,
          buy_pct: labBuyPct,
          profit_target_pct: labTargetPct,
          fee_rate_pct: labFeePct,
          name: row.strategy?.name || "Lab",
        }),
      });
      res.strategy_name = row.strategy?.name || "";
      renderLabResult(res);
      flash("lab-msg", `Detalhe: ${row.strategy?.name || "—"} · ${fmt(res.summary?.capital_return_pct, 2)}%`, true);
    } catch (err) {
      flash("lab-msg", err.message, false);
    }
  }, { busyLabel: "Simulando…", statusId: "lab-msg", statusText: "Simulando estratégia…" });
  labRunning = false;
}

function openCreateBotFromLabStratRow(row) {
  if (!row) return;
  const s = row.strategy || {};
  const p = row.params || {};
  openCreateBotModal({
    strategy_id: s.id,
    name: `Bot ${s.name || (p.inst_id || labInstId || "spot").split("-")[0]}`,
    inst_id: p.inst_id || row.inst_id || labInstId,
    buy_pct: p.buy_pct ?? s.buy_pct,
    profit_target_pct: p.profit_target_pct ?? s.profit_target_pct,
    fee_rate_pct: p.fee_rate_pct ?? s.fee_rate_pct,
    quote_amount: p.aporte ?? labAporte ?? "",
    entry_mode: "quote",
    run_days: normalizeBotRunDays(p.days ?? labDays),
  });
}

function labBotPayloadFromResult(res) {
  const p = res?.params || {};
  const inst = String(p.inst_id || res?.inst_id || labInstId || "SOL-USDT").toUpperCase();
  const base = inst.split("-")[0] || "Token";
  const aporte = Number(p.aporte ?? res?.aporte_input ?? labAporte) || 300;
  return {
    name: `Bot ${base} · ${fmt(p.buy_pct ?? labBuyPct, 1)}/${fmt(p.profit_target_pct ?? labTargetPct, 1)}`,
    inst_id: inst,
    quote_amount: aporte,
    buy_pct: Number(p.buy_pct ?? labBuyPct) || 2,
    profit_target_pct: Number(p.profit_target_pct ?? labTargetPct) || 1,
    fee_rate_pct: Number(p.fee_rate_pct ?? labFeePct) || 0.1,
    interval_min: 5,
    run_days: normalizeBotRunDays(p.days ?? labDays),
    portfolio_interval_min: 2,
    icon: res?.icon,
    icon_alt: res?.icon_alt,
  };
}

function openCreateBotFromLab() {
  if (!lastLabResult) {
    flash("lab-msg", "Rode uma simulação antes de criar o bot", false);
    return;
  }
  const payload = labBotPayloadFromResult(lastLabResult);
  const q = lastLabResult?.summary?.quality || {};
  fillBotModalForm(payload);
  const assert = Number(q.assertiveness);
  const hint = q.recommend_create
    ? `Params da simulação · assertividade ${fmt(assert, 0)}/100. Confirme para gravar.`
    : `Params da simulação · assertividade ${Number.isFinite(assert) ? fmt(assert, 0) : "—"}/100. Qualidade frágil — confirme se aceitar o risco.`;
  openAppModal({
    title: "Criar bot a partir do Lab",
    hint,
    rows: [
      ["Par", payload.inst_id],
      ["Valor / compra", String(payload.quote_amount)],
      ["Queda", `${fmt(payload.buy_pct, 2)}%`],
      ["Lucro alvo", `${fmt(payload.profit_target_pct, 2)}%`],
      ["Taxa", `${fmt(payload.fee_rate_pct, 2)}%`],
    ],
    form: true,
    confirmLabel: q.recommend_create ? "Criar bot aprovado" : "Criar mesmo assim",
    confirmClass: q.recommend_create ? "btn-primary" : "btn-sell",
    confirmIco: ICO.play,
    action: { type: "bot-create", preset: payload, fromLab: true },
  });
  setBotModalLocked(false);
}

$("lab-tokens")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button.lab-token[data-inst]");
  if (!btn || btn.disabled) return;
  ev.preventDefault();
  ev.stopPropagation();
  const inst = (btn.getAttribute("data-inst") || "").toUpperCase();
  if (!inst || inst === labInstId) return;
  selectLabInst(inst, {});
  lastLabResult = null;
  lastLabStratResult = null;
  const createBtn = $("btn-lab-create-bot");
  if (createBtn) createBtn.hidden = true;
});

$("lab-token-search")?.addEventListener("input", (ev) => {
  clearTimeout(labTokenSearchTimer);
  const q = ev.target.value;
  labTokenSearchTimer = setTimeout(() => searchLabTokens(q), 200);
});

$("lab-token-search")?.addEventListener("focus", (ev) => {
  if (String(ev.target.value || "").trim()) searchLabTokens(ev.target.value);
});

$("lab-token-results")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-lab-pick]");
  if (!btn) return;
  selectLabInst(btn.getAttribute("data-lab-pick"), {
    icon: btn.getAttribute("data-icon") || "",
    icon_alt: btn.getAttribute("data-alt") || "",
  });
  lastLabResult = null;
  lastLabStratResult = null;
  const createBtn = $("btn-lab-create-bot");
  if (createBtn) createBtn.hidden = true;
});

document.addEventListener("click", (ev) => {
  if (ev.target.closest(".lab-token-search-wrap")) return;
  const results = $("lab-token-results");
  if (results) results.hidden = true;
});

$("lab-days")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-days]");
  if (!btn) return;
  labDays = Number(btn.dataset.days) || 7;
  localStorage.setItem("okx_lab_days", String(labDays));
  syncLabInputsFromState();
});

$("lab-tl-filter")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-tl]");
  if (!btn) return;
  labTlFilter = btn.dataset.tl || "all";
  document.querySelectorAll("#lab-tl-filter button").forEach((b) => {
    b.classList.toggle("on", b.dataset.tl === labTlFilter);
  });
  if (lastLabResult) renderLabTimeline(lastLabResult);
});

$("lab-aporte")?.addEventListener("change", () => {
  readLabForm();
  syncLabInputsFromState();
});

$("lab-aporte-ccy")?.addEventListener("change", () => {
  readLabForm();
  syncLabInputsFromState();
});

["lab-buy-pct", "lab-target-pct", "lab-fee-pct"].forEach((id) => {
  $(id)?.addEventListener("change", () => {
    readLabForm();
    syncLabInputsFromState();
  });
});

$("btn-lab-run")?.addEventListener("click", () => runLabSimulate());
$("btn-lab-compare")?.addEventListener("click", () => {
  // Lab = simulação manual; comparar presets fica em Estratégias
  readLabForm();
  if (labInstId && labInstId.includes("-")) {
    stratInstId = labInstId;
    localStorage.setItem("okx_strat_inst", stratInstId);
  }
  if (labDays) {
    stratDays = labDays;
    localStorage.setItem("okx_strat_days", String(stratDays));
  }
  if (labAporte) {
    stratAporte = labAporte;
    localStorage.setItem("okx_strat_aporte", String(stratAporte));
  }
  location.hash = "#/strategies";
  setTimeout(() => {
    renderStratControls();
    flash("strat-msg", "Token do Lab aplicado — clique em Validar presets", true);
  }, 60);
});
$("btn-lab-create-bot")?.addEventListener("click", () => openCreateBotFromLab());
$("btn-lab-winner-run")?.addEventListener("click", () => {
  const best = (lastLabStratResult?.results || [])[0];
  if (best) runLabDetailForStratRow(best);
});
$("btn-lab-winner-bot")?.addEventListener("click", () => {
  const best = (lastLabStratResult?.results || [])[0];
  if (best) openCreateBotFromLabStratRow(best);
});
$("lab-strat-rank")?.addEventListener("click", (ev) => {
  const runBtn = ev.target.closest("button[data-lab-strat-run]");
  const botBtn = ev.target.closest("button[data-lab-strat-bot]");
  if (runBtn) {
    runLabDetailForStratRow(labStratRowById(runBtn.getAttribute("data-lab-strat-run")));
    return;
  }
  if (botBtn) {
    openCreateBotFromLabStratRow(labStratRowById(botBtn.getAttribute("data-lab-strat-bot")));
  }
});
$("lab-strat-sort")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-sort]");
  if (!btn) return;
  labStratSort = btn.dataset.sort === "assert" ? "assert" : "profit";
  localStorage.setItem("okx_lab_strat_sort", labStratSort);
  syncLabStratSortSeg();
});

/* —— Estratégias —— */
let stratDays = Number(localStorage.getItem("okx_strat_days") || 30);
let stratInstId = localStorage.getItem("okx_strat_inst") || labInstId || "SOL-USDT";
let stratAporte = Number(localStorage.getItem("okx_strat_aporte") || labAporte || 300);
let stratSort = localStorage.getItem("okx_strat_sort") || "profit";
let stratRisk = localStorage.getItem("okx_strat_risk") || "all";
let stratCatalog = [];
let lastStratResult = null;
let stratRunning = false;

function renderStratTokens() {
  const box = $("strat-tokens");
  if (!box) return;
  const tokens = labTokens.length ? labTokens : [];
  if (!tokens.length) {
    box.innerHTML = `<span class="hint">Carregando…</span>`;
    return;
  }
  const available = tokens.filter((t) => t.available);
  if (!available.some((t) => t.inst_id === stratInstId)) {
    stratInstId = available[0]?.inst_id || "SOL-USDT";
  }
  box.innerHTML = tokens.map((t) => {
    const on = t.inst_id === stratInstId ? "on" : "";
    const dis = t.available ? "" : "disabled";
    return `<button type="button" class="lab-token ${on}" data-strat-inst="${t.inst_id}" ${dis} title="${escHtml(t.inst_id)}">
      <img src="${t.icon || ""}" alt="" draggable="false" onerror="this.onerror=null;this.src='${t.icon_alt || ""}'" />
      <span>${escHtml(t.symbol)}</span>
    </button>`;
  }).join("");
}

function stratRiskLevel(risk) {
  const r = String(risk || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{M}/gu, "");
  if (/muito\s*alto/.test(r)) return "alto";
  if (/\bbaixo\b/.test(r)) return "baixo";
  if (/\bmedio\b/.test(r)) return "medio";
  if (/\balto\b/.test(r)) return "alto";
  return "medio";
}

function stratMatchesRisk(s, filter) {
  if (!filter || filter === "all") return true;
  return stratRiskLevel(s?.risk) === filter;
}

function stratRiskLabel(filter) {
  return ({ all: "todos", baixo: "baixo", medio: "médio", alto: "alto" })[filter] || filter;
}

function filteredStratCatalog() {
  return (stratCatalog || []).filter((s) => stratMatchesRisk(s, stratRisk));
}

function renderStratControls() {
  document.querySelectorAll("#strat-days button").forEach((btn) => {
    btn.classList.toggle("on", Number(btn.dataset.days) === stratDays);
  });
  document.querySelectorAll("#strat-sort button").forEach((btn) => {
    btn.classList.toggle("on", btn.dataset.sort === stratSort);
  });
  document.querySelectorAll("#strat-risk button").forEach((btn) => {
    btn.classList.toggle("on", btn.dataset.risk === stratRisk);
  });
  const aporte = $("strat-aporte");
  if (aporte && document.activeElement !== aporte) aporte.value = String(stratAporte);
  renderStratTokens();
}

async function ensureStratReady() {
  await ensureLabTokens();
  renderStratControls();
  if (!stratCatalog.length) {
    try {
      const res = await api("/api/strategies");
      stratCatalog = res.strategies || [];
    } catch (_) {
      stratCatalog = [];
    }
  }
  renderStratCatalog();
  if (lastStratResult) renderStratResult(lastStratResult);
}

function openStrategyDetail(s) {
  if (!s) return;
  const riskTone = /alto/i.test(s.risk || "") ? "sell" : /baixo/i.test(s.risk || "") ? "buy" : "";
  openAppModal({
    title: s.name || s.id,
    hint: `${s.custom ? "Custom" : "Preset"} · ${s.id}`,
    rich: true,
    wide: true,
    kpis: [
      { label: "Queda compra", value: `${fmt(s.buy_pct, 2)}%` },
      { label: "Alvo venda", value: `${fmt(s.profit_target_pct, 2)}%` },
      { label: "Taxa", value: `${fmt(s.fee_rate_pct, 2)}%` },
    ],
    sections: [
      {
        title: "Perfil",
        rows: [
          ["Estilo", s.style || "—"],
          ["Risco", s.risk || "—", riskTone],
          ["Tag", s.tag || "—"],
          ["Foco", s.focus || "—"],
          ["Melhor para", s.best_for || "—"],
          ["Tipo", s.custom ? "Criada por você" : "Preset de mercado"],
        ],
      },
      {
        title: "Regras do bot",
        rows: [
          ["Compra", `1º ciclo sem token: compra na hora · depois só se cair ≥ ${fmt(s.buy_pct, 2)}% vs ref (máx. recente)`],
          ["Venda", `só se PnL líquido ≥ ${fmt(s.profit_target_pct, 2)}%`],
          ["Taxa assumida", `${fmt(s.fee_rate_pct, 2)}% taker`],
          ["Entrada", "opcional no bot ($/token ou saldo disponível)"],
        ],
      },
    ],
    confirmLabel: "Criar bot",
    confirmClass: "btn-buy",
    confirmIco: ICO.play,
    cancelLabel: "Usar no Lab",
    action: { type: "strat-create-bot", strategy: s },
  });
  // cancel = usar no lab: intercept via cancel button dataset
  const cancel = $("app-modal-cancel");
  if (cancel) {
    cancel.onclick = () => {
      closeModal();
      applyStrategyToLab({
        strategy: s,
        params: {
          inst_id: stratInstId,
          buy_pct: s.buy_pct,
          profit_target_pct: s.profit_target_pct,
          fee_rate_pct: s.fee_rate_pct,
          aporte: stratAporte,
          days: stratDays,
        },
      });
    };
  }
}

function openCreateStrategyModal() {
  // reuse bot form fields partially via summary form... use dedicated inline via openAppModal form false + custom? 
  // Simple: prompt-like using bot form pattern - temporary fields in modal-summary HTML
  const body = $("app-modal-summary");
  openAppModal({
    title: "Nova estratégia",
    hint: "Salva no catálogo e fica disponível ao criar bots.",
    rich: true,
    wide: true,
    rows: [],
    confirmLabel: "Salvar estratégia",
    confirmClass: "btn-primary",
    action: { type: "strat-create" },
  });
  body.hidden = false;
  body.innerHTML = `<div class="form modal-form" id="strat-create-form" style="padding:0">
    <label class="full">Nome <input name="name" required maxlength="60" placeholder="Minha scalp" /></label>
    <label>% queda compra <input name="buy_pct" type="number" step="0.01" min="0.01" value="2" required /></label>
    <label>% alvo venda <input name="profit_target_pct" type="number" step="0.01" min="0.01" value="1.2" required /></label>
    <label>Taxa % <input name="fee_rate_pct" type="number" step="0.01" min="0" value="0.10" required /></label>
    <label class="full">Estilo <input name="style" maxlength="40" value="custom" /></label>
    <label class="full">Foco <input name="focus" maxlength="200" placeholder="Descreva a tese" /></label>
    <label>Risco <input name="risk" maxlength="40" value="médio" /></label>
    <label>Tag <input name="tag" maxlength="40" value="custom" /></label>
    <label class="full">Melhor para <input name="best_for" maxlength="120" placeholder="SOL, ETH…" /></label>
  </div>`;
}

function renderStratCatalog() {
  const box = $("strat-catalog");
  if (!box) return;
  const list = filteredStratCatalog();
  if (!stratCatalog.length) {
    box.innerHTML = `<div class="hint">Catálogo indisponível.</div>`;
    return;
  }
  if (!list.length) {
    box.innerHTML = `<div class="hint">Nenhuma estratégia com risco “${escHtml(stratRiskLabel(stratRisk))}”. Tente outro filtro.</div>`;
    return;
  }
  box.innerHTML = list.map((s) => {
    const riskTone = stratRiskLevel(s.risk) === "alto" ? "sell" : stratRiskLevel(s.risk) === "baixo" ? "buy" : "";
    return `<article class="strat-card" data-strat-detail="${escHtml(s.id)}" role="button" tabindex="0">
    <header>
      <div class="strat-card-title">
        ${stratIcon(s)}
        <strong>${escHtml(s.name)}</strong>
      </div>
      <span class="pill ${riskTone || (s.custom ? "on" : "off")}">${escHtml(s.risk || s.tag || "—")}</span>
    </header>
    <p>${escHtml(s.focus || "")}</p>
    <div class="strat-params">queda ${fmt(s.buy_pct, 2)}% · alvo ${fmt(s.profit_target_pct, 2)}% · ${escHtml(s.style || "")}</div>
    <small class="hint" style="margin:0">${escHtml(s.best_for || "")}</small>
    <div class="strat-card-actions">
      <button type="button" class="btn btn-ghost" data-strat-detail-btn="${escHtml(s.id)}">Detalhe</button>
      <button type="button" class="btn btn-ghost" data-strat-apply="${escHtml(s.id)}">Lab</button>
      <button type="button" class="btn btn-primary js-bots-ui" data-strat-bot-id="${escHtml(s.id)}">Criar bot</button>
    </div>
  </article>`;
  }).join("");
}

function renderStratResult(res) {
  lastStratResult = res;
  const empty = $("strat-empty");
  const results = $("strat-results");
  if (empty) empty.hidden = true;
  if (results) results.hidden = false;

  const rows = (res.results || []).filter((r) => stratMatchesRisk(r.strategy, stratRisk));
  const best = rows[0] || null;
  const s = best?.summary || {};
  const st = best?.strategy || {};
  fillWinnerBanner("strat", best, res);
  $("strat-best-name").innerHTML = best
    ? `${stratIcon(st)}<span>${escHtml(st.name || "—")}</span>`
    : "—";
  $("strat-best-sub").textContent = best ? `${best.params?.buy_pct}% / ${best.params?.profit_target_pct}%` : "—";
  const ret = Number(s.capital_return_pct);
  const retEl = $("strat-best-ret");
  retEl.textContent = Number.isFinite(ret) ? `${fmt(ret, 2)}%` : "—";
  retEl.className = ret > 0 ? "up" : ret < 0 ? "down" : "";
  const a = Number(s.assertiveness);
  const aEl = $("strat-best-assert");
  aEl.textContent = Number.isFinite(a) ? `${fmt(a, 0)}/100` : "—";
  aEl.className = a >= 70 ? "up" : a >= 50 ? "" : "down";
  $("strat-best-cycles").textContent = String(s.cycles_closed ?? "—");
  $("strat-rank-meta").textContent =
    `${res.inst_id || "—"} · ${res.days || stratDays}d · ordenado por ${res.sort === "assert" ? "assertividade" : "lucro"} · ` +
    (stratRisk === "all" ? "todos os riscos" : `risco ${stratRiskLabel(stratRisk)}`) + " · " +
    `${res.approved_count || 0} aprovada(s) · ${rows.length} testadas`;

  const bestBotBtn = $("btn-strat-best-bot");
  if (bestBotBtn) {
    bestBotBtn.hidden = !best;
    bestBotBtn.textContent = best?.summary?.recommend_create
      ? `Criar melhor bot (${st.name || "—"})`
      : `Criar 1º do ranking (${st.name || "—"})`;
  }

  const rank = $("strat-rank");
  if (rank) {
    rank.innerHTML = rows.length
      ? stratRankRowsHtml(rows, "strat")
      : `<div class="hint">Nenhuma estratégia neste filtro de risco.</div>`;
  }
}

function stratRowById(id) {
  return (lastStratResult?.results || []).find((r) => r.strategy?.id === id) || null;
}

function applyStrategyToLab(row) {
  if (!row) return;
  const p = row.params || {};
  labInstId = String(p.inst_id || stratInstId).toUpperCase();
  labBuyPct = Number(p.buy_pct) || labBuyPct;
  labTargetPct = Number(p.profit_target_pct) || labTargetPct;
  labFeePct = Number(p.fee_rate_pct) || labFeePct;
  labAporte = Number(p.aporte || stratAporte) || labAporte;
  labDays = Number(p.days || stratDays) || labDays;
  localStorage.setItem("okx_lab_inst", labInstId);
  localStorage.setItem("okx_lab_buy", String(labBuyPct));
  localStorage.setItem("okx_lab_target", String(labTargetPct));
  localStorage.setItem("okx_lab_fee", String(labFeePct));
  localStorage.setItem("okx_lab_aporte", String(labAporte));
  localStorage.setItem("okx_lab_days", String(labDays));
  location.hash = "#/lab";
  setTimeout(() => {
    renderLabControls();
    flash("lab-msg", `Estratégia ${row.strategy?.name || ""} aplicada — rode a simulação`, true);
  }, 50);
}

function openCreateBotFromStrat(row) {
  if (!row) return;
  const s = row.strategy || {};
  const p = row.params || {};
  openCreateBotModal({
    strategy_id: s.id,
    name: `Bot ${s.name || (p.inst_id || stratInstId || "spot").split("-")[0]}`,
    inst_id: p.inst_id || row.inst_id || stratInstId || orderInst(),
    buy_pct: p.buy_pct ?? s.buy_pct,
    profit_target_pct: p.profit_target_pct ?? s.profit_target_pct,
    fee_rate_pct: p.fee_rate_pct ?? s.fee_rate_pct,
    quote_amount: p.aporte ?? "",
    entry_mode: "quote",
    run_days: normalizeBotRunDays(stratDays),
    icon: lastStratResult?.icon,
    icon_alt: lastStratResult?.icon_alt,
  });
}

async function runStratValidate() {
  if (stratRunning) return;
  const aporteEl = $("strat-aporte");
  if (aporteEl) stratAporte = Math.max(1, Number(aporteEl.value) || 300);
  localStorage.setItem("okx_strat_aporte", String(stratAporte));
  localStorage.setItem("okx_strat_inst", stratInstId);
  localStorage.setItem("okx_strat_days", String(stratDays));
  localStorage.setItem("okx_strat_sort", stratSort);
  localStorage.setItem("okx_strat_risk", stratRisk);
  if (!stratInstId.includes("-")) {
    flash("strat-msg", "Escolha um token", false);
    return;
  }
  stratRunning = true;
  const riskFiltered = filteredStratCatalog();
  if (stratRisk !== "all" && !riskFiltered.length) {
    flash("strat-msg", "Nenhuma estratégia neste nível de risco", false);
    stratRunning = false;
    return;
  }
  await withRefresh("btn-strat-run", async () => {
    try {
      const body = {
        inst_id: stratInstId,
        days: stratDays,
        aporte: stratAporte,
        aporte_ccy: "USDT",
        sort: stratSort,
      };
      if (stratRisk !== "all") body.strategy_ids = riskFiltered.map((s) => s.id);
      const res = await api("/api/strategies/validate", {
        method: "POST",
        body: JSON.stringify(body),
      });
      renderStratResult(res);
      const best = (res.results || [])[0];
      flash(
        "strat-msg",
        best
          ? `Melhor (${stratSort === "assert" ? "assert." : "lucro"}): ${best.strategy?.name} · ${fmt(best.summary?.capital_return_pct, 2)}% · assert. ${fmt(best.summary?.assertiveness, 0)}`
          : "Sem resultados",
        true,
      );
    } catch (err) {
      flash("strat-msg", err.message, false);
    }
  }, { busyLabel: "Validando…", statusId: "strat-msg", statusText: "Validando estratégias…" });
  stratRunning = false;
}

$("strat-tokens")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-strat-inst]");
  if (!btn || btn.disabled) return;
  stratInstId = btn.getAttribute("data-strat-inst");
  localStorage.setItem("okx_strat_inst", stratInstId);
  renderStratTokens();
});

$("strat-days")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-days]");
  if (!btn) return;
  stratDays = Number(btn.dataset.days) || 30;
  localStorage.setItem("okx_strat_days", String(stratDays));
  renderStratControls();
});

$("strat-sort")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-sort]");
  if (!btn) return;
  stratSort = btn.dataset.sort === "assert" ? "assert" : "profit";
  localStorage.setItem("okx_strat_sort", stratSort);
  renderStratControls();
  if (lastStratResult?.results?.length) {
    // reordena localmente sem nova chamada
    const mode = stratSort;
    const rows = [...(lastStratResult.results || [])];
    rows.sort((a, b) => {
      const sa = a.summary || {};
      const sb = b.summary || {};
      if (mode === "assert") {
        return (Number(sb.assertiveness) || 0) - (Number(sa.assertiveness) || 0)
          || (Number(sb.capital_return_pct) || 0) - (Number(sa.capital_return_pct) || 0);
      }
      const score = (s) => {
        const ret = Number(s.capital_return_pct) || -999;
        const as = Number(s.assertiveness) || 0;
        return ret * (0.5 + as / 200) + (s.profit_locked ? 5 : 0);
      };
      return score(sb) - score(sa);
    });
    lastStratResult = {
      ...lastStratResult,
      sort: stratSort,
      best_id: rows[0]?.strategy?.id,
      results: rows,
    };
    renderStratResult(lastStratResult);
  }
});

$("strat-risk")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-risk]");
  if (!btn) return;
  stratRisk = btn.dataset.risk || "all";
  localStorage.setItem("okx_strat_risk", stratRisk);
  renderStratControls();
  renderStratCatalog();
  if (lastStratResult) renderStratResult(lastStratResult);
});

$("btn-strat-run")?.addEventListener("click", () => runStratValidate());
$("btn-strat-best-bot")?.addEventListener("click", () => {
  const best = (lastStratResult?.results || [])[0];
  if (best) openCreateBotFromStrat(best);
});

$("strat-catalog")?.addEventListener("click", (ev) => {
  const applyBtn = ev.target.closest("[data-strat-apply]");
  const detailBtn = ev.target.closest("[data-strat-detail-btn]");
  const botBtn = ev.target.closest("[data-strat-bot-id]");
  const card = ev.target.closest("[data-strat-detail]");
  const id = (applyBtn || detailBtn || botBtn || card)?.getAttribute(
    applyBtn ? "data-strat-apply" : detailBtn ? "data-strat-detail-btn" : botBtn ? "data-strat-bot-id" : "data-strat-detail",
  );
  if (!id) return;
  const strat = stratCatalog.find((s) => s.id === id);
  if (!strat) return;
  if (applyBtn) {
    applyStrategyToLab({
      strategy: strat,
      params: {
        inst_id: stratInstId,
        buy_pct: strat.buy_pct,
        profit_target_pct: strat.profit_target_pct,
        fee_rate_pct: strat.fee_rate_pct,
        aporte: stratAporte,
        days: stratDays,
      },
    });
    return;
  }
  if (botBtn) {
    openCreateBotModal({
      strategy_id: strat.id,
      name: `Bot ${strat.name}`,
      buy_pct: strat.buy_pct,
      profit_target_pct: strat.profit_target_pct,
      fee_rate_pct: strat.fee_rate_pct,
      inst_id: stratInstId || orderInst(),
      run_days: normalizeBotRunDays(stratDays),
    });
    return;
  }
  // detalhe (botão ou clique no card fora dos botões)
  if (detailBtn || (card && !ev.target.closest("button"))) openStrategyDetail(strat);
});

$("btn-strat-new")?.addEventListener("click", () => openCreateStrategyModal());

$("strat-rank")?.addEventListener("click", (ev) => {
  const labBtn = ev.target.closest("button[data-strat-strat-run]");
  const botBtn = ev.target.closest("button[data-strat-strat-bot]");
  if (labBtn) applyStrategyToLab(stratRowById(labBtn.getAttribute("data-strat-strat-run")));
  if (botBtn) openCreateBotFromStrat(stratRowById(botBtn.getAttribute("data-strat-strat-bot")));
});

function tradeRows(trades) {
  if (!trades.length) {
    return `<tr><td class="empty" colspan="7">Nenhum trade ainda</td></tr>`;
  }
  return trades.map((t) => {
    const pnl = t.side === "sell" && t.pnl_realized != null ? fmtPnl(t.pnl_realized) : "—";
    const pnlCls = t.pnl_realized > 0 ? "buy" : t.pnl_realized < 0 ? "sell" : "";
    return `<tr>
      <td>${fmtTs(t.ts)}</td>
      <td>${originCell(t)}</td>
      <td>${t.inst_id || "—"}</td>
      <td class="${t.side === "buy" ? "buy" : "sell"}">${String(t.side || "").toUpperCase()}</td>
      <td>${fmt(t.qty, 8)}</td>
      <td>${fmt(t.avg_px, 6)}</td>
      <td class="${pnlCls}">${pnl}</td>
    </tr>`;
  }).join("");
}

function renderTrades(trades) {
  lastTrades = trades || [];
  const preview = $("trades-preview");
  if (preview) preview.innerHTML = tradeRows(lastTrades.slice(0, 8));
}

function instForWalletCcy(ccy) {
  ccy = String(ccy || "").toUpperCase();
  if (ccy === "BRL") return "USDT-BRL";
  // Stables: câmbio local — nunca BTC-USDT
  if (ccy === "USDT" || ccy === "USDC" || ccy === "USD") {
    return `${ccy === "USD" ? "USDT" : ccy}-BRL`;
  }
  if (ccy === preferredQuote()) return `${ccy}-USDT`;
  // Altcoins (ex. RE): muitos só existem em USDT/USDC, não em BRL
  return `${ccy}-USDT`;
}

function isStableCcy(ccy) {
  return STABLES.has(String(ccy || "").toUpperCase()) || ["USD", "DAI"].includes(String(ccy || "").toUpperCase());
}

function walletAssetByCcy(ccy) {
  const key = String(ccy || "").toUpperCase();
  return (lastWallet?.assets || []).find((a) => String(a.ccy || "").toUpperCase() === key) || null;
}

async function resolveSpotInst(base, quotePref = "") {
  const sym = String(base || "").toUpperCase();
  const q = quotePref ? `&quote=${encodeURIComponent(quotePref)}` : "";
  return api(`/api/instruments/resolve?base=${encodeURIComponent(sym)}${q}`);
}

function walletChartTokens() {
  const assets = lastWallet?.assets || [];
  return assets
    .filter((a) => a.spot !== false)
    .filter((a) => Number(a.total_bal) > 0 || Number(a.eq_usd) > 0.05)
    .map((a) => {
      const ccy = String(a.ccy || "").toUpperCase();
      const stable = a.is_stable != null ? !!a.is_stable : isStableCcy(ccy);
      let inst = a.spot_inst || null;
      if (stable) {
        if (!inst || String(inst).startsWith("BTC-")) {
          inst = instForWalletCcy(ccy);
        }
      } else {
        inst = inst || instForWalletCcy(ccy);
      }
      return {
        ccy,
        inst: inst || "",
        icon: a.icon,
        icon_alt: a.icon_alt,
        eq_usd: Number(a.eq_usd) || 0,
        bal: Number(a.total_bal) || 0,
        trading: Number(a.trading_bal) || 0,
        funding: Number(a.funding_bal) || 0,
        stable,
      };
    });
}

function chartSelectionMeta(rawInst) {
  const raw = String(rawInst || chartInst || "").toUpperCase();
  const ccy = raw.includes("-") ? raw.split("-")[0] : raw;
  const tokens = walletChartTokens();
  const fromWallet = tokens.find((t) => t.ccy === ccy) || null;
  const asset = walletAssetByCcy(ccy);
  return fromWallet || (asset ? {
    ccy,
    inst: asset.spot_inst || instForWalletCcy(ccy),
    icon: asset.icon,
    icon_alt: asset.icon_alt,
    eq_usd: Number(asset.eq_usd) || 0,
    bal: Number(asset.total_bal) || 0,
    trading: Number(asset.trading_bal) || 0,
    funding: Number(asset.funding_bal) || 0,
    stable: asset.is_stable != null ? !!asset.is_stable : isStableCcy(ccy),
  } : {
    ccy,
    inst: raw.includes("-") ? raw : instForWalletCcy(ccy),
    icon: "",
    icon_alt: "",
    eq_usd: 0,
    bal: 0,
    trading: 0,
    funding: 0,
    stable: isStableCcy(ccy),
  });
}

function chartRange() {
  return CHART_RANGES.find((r) => r.key === chartRangeKey) || CHART_RANGES.find((r) => r.key === "90d") || CHART_RANGES[0];
}

function destroyChart(ref) {
  if (ref?.chart) {
    ref.chart.destroy();
    ref.chart = null;
  }
}

function clearChartPointEl(elId) {
  const el = $(elId);
  if (el) {
    el.hidden = true;
    el.innerHTML = "";
  }
}

function renderChartPointEl(elId, metaList, idx) {
  const el = $(elId);
  if (!el) return;
  const meta = metaList[idx];
  if (!meta) {
    clearChartPointEl(elId);
    return;
  }
  chartSelectedIdx = idx;
  const cells = [`<div class="cp-title">${escHtml(meta.title || "Ponto selecionado")}</div>`];
  for (const row of meta.rows || []) {
    const tone = row.tone ? ` ${row.tone}` : "";
    cells.push(`<div><div class="cp-k">${escHtml(row.k)}</div><div class="cp-v${tone}">${escHtml(String(row.v))}</div></div>`);
  }
  el.innerHTML = cells.join("");
  el.hidden = false;
}

function fmtChartWhen(ts, bar) {
  const d = new Date(typeof ts === "number" && ts < 1e12 ? ts * 1000 : ts);
  if (Number.isNaN(d.getTime())) return "—";
  if (bar === "1D" || bar === "1W") {
    return d.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "short", year: "numeric" });
  }
  if (bar === "1m" || bar === "5m" || bar === "15m") {
    return d.toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  return d.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function dayKeyLocal(ts) {
  const d = new Date(typeof ts === "number" && ts < 1e12 ? ts * 1000 : ts);
  if (Number.isNaN(d.getTime())) return "";
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

const tokenChartState = { chart: null, meta: [] };
const walletEquityState = { chart: null, meta: [] };
let walletEquityDays = Number(localStorage.getItem("okx_wallet_equity_days") || 30);
if (![7, 30, 90, 180].includes(walletEquityDays)) walletEquityDays = 30;

function chartTheme() {
  const dark = typeof isDarkTheme === "function" ? isDarkTheme() : document.documentElement.classList.contains("theme-dark");
  if (dark) {
    return {
      line: "#7dd3fc",
      fill: "rgba(125, 211, 252, 0.14)",
      point: "#e0f2fe",
      pointBorder: "#0ea5e9",
      tick: "#a3a3a3",
      grid: "rgba(255, 255, 255, 0.08)",
      tooltipBg: "#1a1a1a",
      tooltipTitle: "#f2f2f2",
      tooltipBody: "#d4d4d4",
      tooltipBorder: "#404040",
    };
  }
  return {
    line: "#1d4ed8",
    fill: "rgba(29, 78, 216, 0.1)",
    point: "#1d4ed8",
    pointBorder: "#ffffff",
    tick: "#6b7280",
    grid: "rgba(15, 23, 42, 0.08)",
    tooltipBg: "#ffffff",
    tooltipTitle: "#111827",
    tooltipBody: "#374151",
    tooltipBorder: "#e5e7eb",
  };
}

function drawLineChartOn(canvasId, pointElId, stateRef, labels, datasets, metaList = [], opts = {}) {
  const ctx = $(canvasId);
  if (!ctx || typeof Chart === "undefined") return;
  destroyChart(stateRef);
  const meta = metaList || [];
  stateRef.meta = meta;
  clearChartPointEl(pointElId);
  const theme = chartTheme();
  const n = labels.length;
  const pointR = n <= 60 ? 3.5 : n <= 140 ? 2.5 : 0;
  const hitR = Math.max(12, pointR + 8);
  const dualY = !!opts.dualY;
  stateRef.chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: datasets.map((ds) => ({
        tension: 0.25,
        pointRadius: pointR,
        pointHoverRadius: Math.max(5, pointR + 2),
        pointHitRadius: hitR,
        pointBorderWidth: 1.5,
        pointHoverBorderWidth: 2,
        borderWidth: 2.75,
        fill: ds.fill !== false && !dualY,
        ...ds,
        borderColor: ds.borderColor || theme.line,
        backgroundColor: ds.backgroundColor || theme.fill,
        pointBackgroundColor: ds.pointBackgroundColor || theme.point,
        pointBorderColor: theme.pointBorder,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      layout: { padding: { top: 8, right: 8, bottom: 2, left: 2 } },
      onHover: (ev, els) => {
        const canvas = ev?.native?.target || ctx;
        if (canvas && canvas.style) canvas.style.cursor = els?.length ? "pointer" : "default";
      },
      onClick: (_ev, els) => {
        if (!els?.length) return;
        const idx = els[0].index;
        if (idx == null || idx < 0) return;
        renderChartPointEl(pointElId, stateRef.meta, idx);
      },
      plugins: {
        legend: {
          display: !!opts.legend,
          position: "top",
          labels: { boxWidth: 10, font: { size: 12 }, color: theme.tick },
        },
        tooltip: {
          enabled: true,
          backgroundColor: theme.tooltipBg,
          titleColor: theme.tooltipTitle,
          bodyColor: theme.tooltipBody,
          borderColor: theme.tooltipBorder,
          borderWidth: 1,
          padding: 10,
          displayColors: false,
          titleFont: { size: 12, weight: "600" },
          bodyFont: { size: 12 },
          callbacks: {
            title(items) {
              const i = items?.[0]?.dataIndex;
              const m = stateRef.meta[i];
              return m?.title || items?.[0]?.label || "";
            },
            label(item) {
              const m = stateRef.meta[item.dataIndex];
              if (m?.tooltip?.length && item.datasetIndex === 0) return m.tooltip;
              const label = item.dataset.label ? `${item.dataset.label}: ` : " ";
              return `${label}${fmt(item.parsed.y, 2)}`;
            },
          },
        },
      },
      scales: dualY ? {
        x: {
          ticks: { maxTicksLimit: 8, color: theme.tick, font: { size: 11 }, maxRotation: 0 },
          grid: { display: false },
          border: { display: false },
        },
        y: {
          type: "linear",
          position: "left",
          ticks: { color: "#059669", font: { size: 11 } },
          grid: { color: theme.grid },
          border: { display: false },
          title: { display: true, text: "USD", color: "#059669", font: { size: 11 } },
        },
        yBrl: {
          type: "linear",
          position: "right",
          ticks: { color: theme.line, font: { size: 11 } },
          grid: { drawOnChartArea: false },
          border: { display: false },
          title: { display: true, text: "BRL", color: theme.line, font: { size: 11 } },
        },
      } : {
        x: {
          ticks: { maxTicksLimit: 8, color: theme.tick, font: { size: 11 }, maxRotation: 0 },
          grid: { display: false },
          border: { display: false },
        },
        y: {
          ticks: { color: theme.tick, font: { size: 11 } },
          grid: { color: theme.grid },
          border: { display: false },
          grace: "8%",
        },
      },
    },
  });
  if (n > 0) renderChartPointEl(pointElId, stateRef.meta, n - 1);
}

function renderTokenBalancePanel(t) {
  const el = $("tc-balance");
  if (!el) return;
  if (!t) {
    el.innerHTML = "";
    return;
  }
  const usd = Number(t.eq_usd) || 0;
  const brl = toBrl(usd, "USD");
  const brlTxt = brl != null ? `R$ ${fmt(brl, 2)}` : "—";
  el.innerHTML = `
    <div class="chart-bal-card">
      <div class="chart-bal-head">
        <img src="${t.icon || ""}" alt="" onerror="this.onerror=null;this.src='${t.icon_alt || ""}'" />
        <div>
          <strong>Seu saldo · ${escHtml(t.ccy)}</strong>
          <small>${fmt(t.bal, t.bal >= 100 ? 2 : 6)} ${escHtml(t.ccy)} na Spot</small>
        </div>
      </div>
      <div class="chart-bal-grid chart-bal-grid-2">
        <div><span>Em dólar</span><strong>$${fmt(usd, 2)}</strong></div>
        <div><span>Em real</span><strong>${brlTxt}</strong></div>
      </div>
    </div>`;
}

function closeTokenChartModal() {
  const modal = $("token-chart-modal");
  if (modal) modal.hidden = true;
  destroyChart(tokenChartState);
  clearChartPointEl("tc-point");
}

function goTokenChart(inst) {
  const id = String(inst || "").toUpperCase().trim();
  if (!id) return;
  if (id.includes("-")) chartInst = id;
  else if (isStableCcy(id)) chartInst = id;
  else chartInst = `${id}-USDT`;
  chartForceRefresh = true;
  localStorage.setItem("okx_chart_inst", chartInst);
  openTokenChartModal();
}

async function openTokenChartModal() {
  if (!lastWallet) {
    try { lastWallet = await api("/api/portfolio"); } catch (_) {}
  }
  await ensureFxRate().catch(() => null);
  const t = chartSelectionMeta(chartInst);
  const modal = $("token-chart-modal");
  if (!modal) return;
  $("tc-title").textContent = t.stable ? `${t.ccy} · saldo` : `${t.inst || t.ccy} · Spot`;
  $("tc-hint").textContent = t.stable
    ? "Seu saldo em dólar e real"
    : "Saldo da posição e preço Spot";
  const icon = $("tc-icon");
  if (icon) {
    if (t.icon || t.icon_alt) {
      icon.hidden = false;
      icon.src = t.icon || t.icon_alt;
      icon.onerror = () => { icon.src = t.icon_alt || ""; };
    } else {
      icon.hidden = true;
      icon.removeAttribute("src");
    }
  }
  renderTokenBalancePanel(t);
  modal.hidden = false;
  await loadTokenChartModal();
}

async function loadTokenChartModal() {
  const t = chartSelectionMeta(chartInst);
  const range = chartRange();
  const force = chartForceRefresh;
  chartForceRefresh = false;
  const toolbar = $("tc-toolbar");
  const box = $("tc-chart-box");
  $("tc-range")?.querySelectorAll("button").forEach((b) => {
    b.classList.toggle("on", (b.dataset.key || "") === chartRangeKey);
  });

  if (t.stable) {
    if (toolbar) toolbar.hidden = true;
    if (box) box.hidden = true;
    destroyChart(tokenChartState);
    clearChartPointEl("tc-point");
    const brl = toBrl(Number(t.eq_usd) || 0, "USD");
    $("tc-msg").textContent = brl != null
      ? `Saldo Spot · $${fmt(Number(t.eq_usd) || 0, 2)} · R$ ${fmt(brl, 2)}`
      : `Saldo Spot · $${fmt(Number(t.eq_usd) || 0, 2)}`;
    return;
  }

  if (toolbar) toolbar.hidden = false;
  if (box) box.hidden = false;
  const inst = t.inst || (String(chartInst).includes("-") ? chartInst : `${t.ccy}-USDT`);
  chartInst = inst;
  $("tc-title").textContent = `${inst} · Spot · ${range.label}`;
  $("tc-msg").textContent = force ? "Atualizando candles OKX…" : "Carregando histórico OKX…";
  try {
    const lim = range.limit || 400;
    const barsToTry = [range.bar, range.fallbackBar].filter(Boolean);
    let data = null;
    let usedBar = range.bar;
    let candles = [];
    for (const bar of barsToTry) {
      data = await api(
        `/api/candles?instId=${encodeURIComponent(inst)}&bar=${encodeURIComponent(bar)}&days=${encodeURIComponent(range.days)}&limit=${lim}${force ? "&refresh=1" : ""}`,
      );
      candles = data.candles || [];
      usedBar = data.bar || bar;
      if (candles.length) break;
    }
    if (!candles.length) {
      destroyChart(tokenChartState);
      $("tc-msg").textContent = "Sem candles para este par / período";
      return;
    }
    const labels = candles.map((c) => {
      const d = new Date(c.ts);
      if (usedBar === "1D" || usedBar === "1W") {
        return d.toLocaleDateString("pt-BR");
      }
      if (range.key === "1h" || usedBar === "1m" || usedBar === "5m") {
        return d.toLocaleString("pt-BR", { hour: "2-digit", minute: "2-digit" });
      }
      return d.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
    });
    const closes = candles.map((c) => c.close);
    const meta = candles.map((c, i) => {
      const prev = i > 0 ? candles[i - 1].close : null;
      const chg = prev != null && prev > 0 ? ((c.close - prev) / prev) * 100 : null;
      const rows = [
        { k: "Abertura", v: fmtPx(c.open) },
        { k: "Máxima", v: fmtPx(c.high) },
        { k: "Mínima", v: fmtPx(c.low) },
        { k: "Fechamento", v: fmtPx(c.close) },
      ];
      if (t.bal > 0) rows.unshift({ k: "Seu saldo", v: `${fmt(t.bal, 6)} ${t.ccy}` });
      if (chg != null) {
        rows.push({
          k: "Variação",
          v: fmtPct(chg),
          tone: chg > 0 ? "up" : chg < 0 ? "down" : "",
        });
      }
      return {
        title: `${inst} · ${fmtChartWhen(c.ts, usedBar)}`,
        rows,
        tooltip: [`C ${fmtPx(c.close)}`],
      };
    });
    const cacheBit = data.cached
      ? ` · cache ${Math.round(data.cache_age_s || 0)}s`
      : (force ? " · atualizado agora" : "");
    const barBit = usedBar !== range.bar ? ` · ${usedBar} (sem ${range.bar})` : ` · ${usedBar}`;
    $("tc-msg").textContent = `${closes.length} candles · ${range.label}${barBit}${cacheBit}`;
    const theme = chartTheme();
    drawLineChartOn("token-chart-canvas", "tc-point", tokenChartState, labels, [{
      data: closes,
      borderColor: theme.line,
      backgroundColor: theme.fill,
      pointBackgroundColor: theme.point,
    }], meta);
  } catch (err) {
    destroyChart(tokenChartState);
    $("tc-msg").textContent = err.message || "Falha ao carregar gráfico";
  }
}

/** Último saldo de cada dia (histórico diário). */
function aggregateDailyEquity(points) {
  const byDay = new Map();
  for (const p of points || []) {
    const key = dayKeyLocal(p.ts);
    if (!key) continue;
    byDay.set(key, {
      ts: p.ts,
      total_eq: Number(p.total_eq) || 0,
      usdt_brl: p.usdt_brl != null ? Number(p.usdt_brl) : null,
      total_eq_brl: p.total_eq_brl != null ? Number(p.total_eq_brl) : null,
      day: key,
    });
  }
  return [...byDay.values()].sort((a, b) => String(a.day).localeCompare(String(b.day)));
}

function equityBrl(usd, pointRate) {
  const u = Number(usd) || 0;
  if (pointRate != null && Number(pointRate) > 0) return u * Number(pointRate);
  if (usdtBrlRate) return u * usdtBrlRate;
  return null;
}

let walletEquityLoadSeq = 0;

/** Histórico/gráfico da carteira desativado por enquanto. */
async function loadWalletEquityHistory() {
  return;
}

function pollIntervalMs(running) {
  return running ? POLL_ACTIVE_MS : POLL_IDLE_MS;
}

function statusQuery(page, forceTrades = false) {
  if (page !== "overview") return "";
  if (forceTrades || !lastTradesFetch || Date.now() - lastTradesFetch >= TRADES_EVERY_MS) {
    return "?include=trades";
  }
  return "";
}

function syncPollInterval(anyRunning) {
  const mode = anyRunning ? "active" : "idle";
  if (pollRunningMode === mode) return;
  pollRunningMode = mode;
  if (!document.hidden) startPolling();
}

function scheduleNextPoll() {
  if (document.hidden) return;
  const running = (lastStatus?.bots || []).some((b) => b.running);
  pollTimer = setTimeout(async () => {
    await refresh();
    scheduleNextPoll();
  }, pollIntervalMs(running));
}

function startPolling() {
  if (pollTimer) clearTimeout(pollTimer);
  pollTimer = null;
  scheduleNextPoll();
}

async function refresh(opts = {}) {
  if (document.hidden && !opts.force) return;
  if (refreshInFlight) return;
  refreshInFlight = true;
  const page = pageId();
  try {
    const q = statusQuery(page, !!opts.trades);
    const status = await api(`/api/status${q}`);
    renderStatus(status);
    if (status.trades) {
      lastTradesFetch = Date.now();
      renderTrades(status.trades);
    }
    await ensureFxRate();
    repaintPnlKpis();
    setTonePnl(
      $("m-wallet-upl"),
      status.wallet_eq != null ? (status.wallet_spot_upl ?? 0) : status.wallet_spot_upl,
      $("m-wallet-upl-brl"),
      "USD",
      status.wallet_eq != null && status.wallet_spot_upl != null
        ? pnlPctOfEquity(status.wallet_spot_upl, status.wallet_eq)
        : null,
    );
  } catch (err) {
    flash("msg", err.message, false);
  } finally {
    refreshInFlight = false;
  }
}

/** Carteira + status/bots + dados da página atual (ordens/tokens/gráfico). */
async function refreshAll() {
  const page = pageId();
  const data = await api("/api/portfolio/refresh", { method: "POST" });
  lastWallet = data;
  lastWalletTs = Date.now();
  renderWallet(data);
  await refresh({ trades: page === "overview" });
  if (page === "orders") await loadOrders();
  if (page === "tokens") await loadTokens();
  return data;
}

window.addEventListener("hashchange", () => showPage(pageId()));

/** Glossário pesquisável da tela Como funciona — atualizar junto com #page-docs. */
const DOCS_GLOSSARY = [
  { term: "Spot", aliases: ["mercado à vista", "spot trading"], def: "Compra e venda do token de verdade, sem alavancagem de contrato. O OKBot opera só Spot." },
  { term: "Par", aliases: ["inst_id", "par spot", "SOL-USDT"], def: "Combinação base-cotação, ex.: SOL-USDT. É o mercado onde o bot compra e vende." },
  { term: "Base / Quote", aliases: ["base", "quote", "cotação"], def: "No par SOL-USDT, SOL é a base (token) e USDT a quote (com o que você paga)." },
  { term: "Dip", aliases: ["queda", "pullback", "dip hunting"], def: "Queda temporária de preço. O Caçador procura dips — não pumps." },
  { term: "Pump", aliases: ["alta forte", "rally"], def: "Subida forte e rápida. Fora do radar do Caçador por desenho." },
  { term: "Spread", aliases: ["bid ask", "bid/ask", "spreads"], def: "Diferença entre o melhor preço de compra (bid) e de venda (ask). Spread largo = mais caro entrar/sair." },
  { term: "Bid / Ask", aliases: ["bid", "ask", "livro"], def: "Bid = quanto pagam para comprar de você. Ask = quanto pedem para você comprar. O meio é o mid." },
  { term: "Liquidez", aliases: ["liquidez a-d", "nota liquidez", "liq"], def: "Facilidade de negociar sem mover o preço. No app: nota A (ótima) a D (fraca), baseada em volume + spread (+ livro)." },
  { term: "Volume 24h", aliases: ["vol", "volume"], def: "Quanto foi negociado nas últimas 24h (em quote, ex. USDT). Pouco volume = risco de escorregar." },
  { term: "Slippage", aliases: ["escorregamento", "slip"], def: "Diferença entre o preço que você esperava e o da execução real. O bot reserva uma folga no alvo de lucro." },
  { term: "Taxa / Fee", aliases: ["fee", "taker", "maker", "taxa okx"], def: "Cobrança da exchange por trade. Taker costuma ser a taxa de ordem a mercado. Entra no custo do ciclo." },
  { term: "Queda %", aliases: ["buy_pct", "buy pct", "gatilho de compra"], def: "Quanto o preço precisa cair vs a referência para o bot comprar." },
  { term: "Lucro alvo %", aliases: ["profit_target", "alvo", "take profit"], def: "Quanto de lucro (após custos) o bot espera antes de vender." },
  { term: "Alvo sugerido", aliases: ["preço alvo", "target price", "venda sugerida", "take profit preço", "preço alvo"], def: "No Caçador: preço de venda se você comprar agora no last. Pega o maior entre o % da estratégia, o p60 do bounce após dips no tamanho da queda e ~40% da queda 24h; o ATR só corta se passar do teto k×ATR. Mais taxa ida+volta + spread. Não dispara ordem." },
  { term: "Var. média", aliases: ["média de variação", "oscilação média", "avg var", "variação 24h"], def: "No Caçador: média do módulo da variação em janelas de 24h no histórico do scan. Serve para comparar se o preço alvo é compatível com o que o token costuma andar." },
  { term: "Período de negociação", aliases: ["prazo", "horizonte", "dia semana mês"], def: "No Caçador: Dia, Semana ou Mês — o horizonte com melhor aptidão a completar o ciclo compra→venda." },
  { term: "Ativar bots", aliases: ["desativar bots", "bots off", "esconder bots"], def: "Interruptor em Configurações. Desligado: para todos os bots, some o menu Bot/Lab/Estratégias e não deixa criar/iniciar. Carteira e ordens manuais seguem." },
  { term: "Referência", aliases: ["ref_price", "preço de referência", "trailing"], def: "Preço-base usado para medir a queda. Pode acompanhar máximas enquanto o bot está flat (trailing)." },
  { term: "Flat", aliases: ["sem posição", "fora do mercado"], def: "Estado sem token comprado pelo bot — só esperando o gatilho de compra." },
  { term: "Ciclo", aliases: ["ciclo compra venda", "round trip"], def: "Uma volta completa: compra → venda (com ou sem lucro). O Lab conta ciclos no histórico." },
  { term: "Cascata", aliases: ["cascade", "etapas", "fatias"], def: "Dividir compra ou venda em várias etapas percentuais, em vez de tudo de uma vez." },
  { term: "Aporte", aliases: ["quote_amount", "valor da ordem"], def: "Quanto gastar por compra. 0 = usar saldo disponível na hora (ainda limitado pelo teto USD)." },
  { term: "Intervalo", aliases: ["interval_min", "poll", "a cada X min"], def: "De quanto em quanto o bot acorda para olhar o mercado. Padrão de novos bots: 30 min." },
  { term: "Execução (log)", aliases: ["execuções", "execution", "log do bot"], def: "Anotação da decisão do bot a cada ciclo. Não é a ordem na OKX. Pode ser limpa com o tempo." },
  { term: "Executar agora", aliases: ["ciclo manual", "tick manual", "manual"], def: "Botão no painel do bot que roda um ciclo imediato (mesmo parado). Compra/vende se as regras fecharem. A execução fica marcada como manual." },
  { term: "Ordem", aliases: ["order", "ordem okx", "ordem aberta", "selo ordem"], def: "Instrução real enviada à OKX (compra/venda). Aparece em Ordens. Na carteira, o selo «ordem» no token indica que esse ativo é a base de uma ordem ainda aberta; o clique abre a tela Ordens." },
  { term: "Trade", aliases: ["preenchimento", "fill"], def: "Quando a ordem é (parcial ou totalmente) executada na exchange." },
  { term: "PnL", aliases: ["lucro", "prejuízo", "pnl realizado", "upl", "hoje", "semana", "mês"], def: "Lucro ou prejuízo. Na carteira, Hoje/Semana/Mês usam o histórico de preços da OKX (vela no início do período, horário de Brasília) × o saldo atual de cada token — não o snapshot local do bot. 24h usa o open24h dos tickers da OKX. Sem vela daquele período aparece —. No Spot a OKX muitas vezes manda 0 nas vendas; o app estima com custo das compras (FIFO)." },
  { term: "FIFO", aliases: ["custo médio", "custo das compras"], def: "Método: as vendas consomem as compras mais antigas primeiro para calcular o PnL." },
  { term: "Backtest", aliases: ["simulação histórica", "lab simulate"], def: "Rodar a estratégia no passado (candles). Passado ≠ futuro." },
  { term: "Frágil", aliases: ["qualidade frágil", "recommend_create"], def: "Aviso: retorno pode até parecer bom, mas a qualidade interna (ciclos, lucro validado) ainda não passou. Revise no Lab." },
  { term: "Assertividade", aliases: ["qualidade", "grade"], def: "Nota 0–100 do Lab sobre quão “limpo” foi o histórico simulado (acertos, amostra, etc.)." },
  { term: "Aptidão / encaixe", aliases: ["sell_fitness", "aptidão", "encaixe", "fitness"], def: "Nota do Caçador (0–100): liquidez + histórico + ritmo de vendas no estilo Dia/Semana/Mês." },
  { term: "Recuperação", aliases: ["bounce", "pred bounce", "bounce_prob"], def: "Estimativa heurística de chance de o preço reagir após a queda. Não é garantia." },
  { term: "Horizonte", aliases: ["dia", "semana", "mês", "daily", "weekly", "monthly", "scalp"], def: "Estilo de ritmo: no dia (rápido), na semana ou no mês (mais lento). O Caçador compara os três." },
  { term: "Candles", aliases: ["velas", "ohlc", "gráfico"], def: "Barras de preço (abertura, máxima, mínima, fechamento) usadas no Lab e na análise." },
  { term: "Pré-voo", aliases: ["preflight", "validar bot", "checklist"], def: "Checagens antes de iniciar live: keys, par, saldo, limites, backtest rápido." },
  { term: "Edge", aliases: ["margem", "net edge", "viável", "só listar viáveis"], def: "Quanto sobra do alvo depois de taxas e spread. «Só listar viáveis» no Caçador esconde pares sem essa folga ou com livro fino demais para a ordem." },
  { term: "Funding / Trading", aliases: ["funding", "trading account", "transferir"], def: "Contas OKX. O bot gasta do trading. Dinheiro no funding precisa ser transferido antes." },
  { term: "Login Google", aliases: ["cognito", "entrar", "oauth"], def: "Entrada com a conta Google. Cada e-mail tem as próprias chaves OKX e bots." },
  { term: "API Key", aliases: ["chaves", "secret", "passphrase"], def: "Credenciais da OKX no servidor, ligadas ao seu e-mail. Prefira Read+Trade sem withdraw. O secret não é reexibido." },
  { term: "Conta OKX", aliases: ["várias contas", "outra conta", "multi conta", "subconta", "secret", "api key", "sair"], def: "Um conjunto de API Key + Secret + Passphrase. Cada login Google tem só uma. Para usar outro e-mail, clique em Sair (no computador, embaixo do menu; no celular, na faixa do topo ao lado do logo) e escolha a conta no Google. No celular botões e confirmações empilham; tabelas deslizam na horizontal." },
  { term: "Demo / Live", aliases: ["simulated", "flag", "demo trading"], def: "Demo = ambiente simulado OKX. Live = dinheiro real." },
  { term: "Limites USD", aliases: ["min_usd", "max_usd", "teto"], def: "Mínimo e máximo por ordem (manual ou bot), convertidos para USD nas Configurações." },
  { term: "Estratégia", aliases: ["preset", "scalp", "balanced"], def: "Receita pronta de queda/alvo/taxa. Pode validar no Lab/Caçador e ainda editar na mão." },
  { term: "Trailing", aliases: ["ref trailing", "máxima"], def: "Enquanto flat, a referência pode subir com o preço — evita comprar em máxima absoluta velha." },
  { term: "Listing novo", aliases: ["token novo", "age_days"], def: "Par listado há poucos dias. O Caçador aceita volume mínimo menor, mas o risco é maior." },
  { term: "Heurística", aliases: ["regra de bolso", "não é ml"], def: "Regra calculada (fórmulas + histórico), não um modelo de IA treinado. Por isso dizemos “estimativa”." },
  { term: "Copiloto", aliases: ["assistente", "chat", "llm", "ia", "linguagem natural", "chatgpt", "openai", "cursor", "plano", "giro", "troca", "pnl", "compensar"], def: "Balão no topo: converse sobre a carteira e o PnL. Ele analisa seus números, propõe caminhos (giro, corte, dip) e pergunta o que faltar. Não devolve lista de comandos. Cada passo abre o modal. Sem confirmação, nada vai à OKX." },
];

const DOCS_CHIPS = ["copiloto", "dip", "spread", "liquidez", "frágil", "cascata", "PnL", "login", "intervalo", "pump", "conta"];

let docsReady = false;

function initDocsPage() {
  renderDocsGlossary();
  renderDocsChips();
  const input = $("docs-search");
  if (input && !input.dataset.bound) {
    input.dataset.bound = "1";
    input.addEventListener("input", () => runDocsSearch(input.value));
    input.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") {
        input.value = "";
        runDocsSearch("");
        input.blur();
      }
    });
  }
  $("docs-search-clear")?.addEventListener("click", () => {
    if (input) input.value = "";
    runDocsSearch("");
    input?.focus();
  });
  docsReady = true;
  if (input?.value) runDocsSearch(input.value);
}

function renderDocsGlossary() {
  const box = $("docs-glossary-list");
  if (!box) return;
  const sorted = DOCS_GLOSSARY.slice().sort((a, b) => a.term.localeCompare(b.term, "pt"));
  box.innerHTML = sorted.map((g) => {
    const aliases = (g.aliases || []).join(" ");
    return `<div class="docs-term" data-docs-term="${escHtml(g.term)}" data-aliases="${escHtml(aliases)}">
      <dt>${escHtml(g.term)}</dt>
      <dd>${escHtml(g.def)}</dd>
      ${(g.aliases || []).length ? `<span class="docs-term-aliases">também: ${escHtml((g.aliases || []).slice(0, 4).join(" · "))}</span>` : ""}
    </div>`;
  }).join("");
}

function renderDocsChips() {
  const box = $("docs-chips");
  if (!box) return;
  box.innerHTML = DOCS_CHIPS.map((c) =>
    `<button type="button" class="docs-chip" data-docs-chip="${escHtml(c)}">${escHtml(c)}</button>`
  ).join("");
  if (!box.dataset.bound) {
    box.dataset.bound = "1";
    box.addEventListener("click", (ev) => {
      const chip = ev.target.closest("[data-docs-chip]");
      if (!chip) return;
      const q = chip.getAttribute("data-docs-chip") || "";
      const input = $("docs-search");
      if (input) {
        input.value = q;
        runDocsSearch(q);
        input.focus();
      }
    });
  }
}

function normDocsQuery(s) {
  return String(s || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function runDocsSearch(raw) {
  const q = normDocsQuery(raw);
  const clearBtn = $("docs-search-clear");
  const meta = $("docs-search-meta");
  const hitsBox = $("docs-search-hits");
  if (clearBtn) clearBtn.hidden = !q;

  document.querySelectorAll("#page-docs .docs-section").forEach((el) => {
    el.classList.remove("docs-dim", "docs-hit");
  });
  document.querySelectorAll("#page-docs .docs-term").forEach((el) => {
    el.hidden = false;
    el.classList.remove("docs-term-hit");
  });
  document.querySelectorAll("#page-docs .docs-faq-item").forEach((el) => {
    el.hidden = false;
    el.classList.remove("docs-faq-hit");
  });

  if (!q) {
    if (meta) {
      meta.hidden = true;
      meta.textContent = "";
    }
    if (hitsBox) {
      hitsBox.hidden = true;
      hitsBox.innerHTML = "";
    }
    return;
  }

  const termHits = [];
  document.querySelectorAll("#page-docs .docs-term").forEach((el) => {
    const blob = normDocsQuery(`${el.dataset.docsTerm || ""} ${el.dataset.aliases || ""} ${el.textContent || ""}`);
    const ok = blob.includes(q);
    el.hidden = !ok;
    if (ok) {
      el.classList.add("docs-term-hit");
      termHits.push({
        term: el.dataset.docsTerm || el.querySelector("dt")?.textContent || "Termo",
        def: el.querySelector("dd")?.textContent || "",
      });
    }
  });

  const sectionHits = [];
  document.querySelectorAll("#page-docs .docs-section").forEach((el) => {
    if (el.id === "docs-words") {
      el.classList.toggle("docs-hit", termHits.length > 0);
      el.classList.toggle("docs-dim", termHits.length === 0);
      return;
    }
    const blob = normDocsQuery(el.textContent || "");
    const ok = blob.includes(q);
    el.classList.toggle("docs-hit", ok);
    el.classList.toggle("docs-dim", !ok);
    if (ok) {
      const title = el.querySelector("h2")?.textContent || el.id;
      sectionHits.push({ id: el.id, title });
    }
  });

  let faqHits = 0;
  document.querySelectorAll("#page-docs .docs-faq-item").forEach((el) => {
    const blob = normDocsQuery(el.textContent || "");
    const ok = blob.includes(q);
    el.hidden = !ok;
    if (ok) {
      faqHits += 1;
      el.classList.add("docs-faq-hit");
    }
  });
  const faqSection = $("docs-faq");
  if (faqSection) {
    faqSection.classList.toggle("docs-hit", faqHits > 0);
    faqSection.classList.toggle("docs-dim", faqHits === 0 && !sectionHits.some((s) => s.id === "docs-faq"));
  }

  const total = termHits.length + sectionHits.length + faqHits;
  if (meta) {
    meta.hidden = false;
    meta.textContent = total
      ? `${termHits.length} termo(s) · ${sectionHits.length} seção(ões) · ${faqHits} FAQ`
      : `Nada encontrado para “${raw.trim()}”. Tente: spread, dip, frágil, PnL…`;
  }

  if (hitsBox) {
    if (!total) {
      hitsBox.hidden = true;
      hitsBox.innerHTML = "";
    } else {
      hitsBox.hidden = false;
      const termHtml = termHits.slice(0, 8).map((t) =>
        `<button type="button" class="docs-hit-card" data-docs-jump="docs-words" data-docs-focus-term="${escHtml(t.term)}">
          <strong>${escHtml(t.term)}</strong>
          <span>${escHtml(t.def.slice(0, 120))}${t.def.length > 120 ? "…" : ""}</span>
        </button>`
      ).join("");
      const secHtml = sectionHits.slice(0, 6).map((s) =>
        `<button type="button" class="docs-hit-card docs-hit-sec" data-docs-jump="${escHtml(s.id)}">
          <strong>Seção</strong>
          <span>${escHtml(s.title)}</span>
        </button>`
      ).join("");
      hitsBox.innerHTML = termHtml + secHtml;
    }
  }
}

document.addEventListener("click", (ev) => {
  const focusTerm = ev.target.closest("[data-docs-focus-term]");
  if (focusTerm) {
    const term = focusTerm.getAttribute("data-docs-focus-term");
    const jump = focusTerm.getAttribute("data-docs-jump") || "docs-words";
    sessionStorage.setItem("okx_docs_jump", jump);
    if (pageId() !== "docs") location.hash = "#/docs";
    else showPage("docs");
    setTimeout(() => {
      const el = [...document.querySelectorAll("#page-docs .docs-term")]
        .find((n) => (n.dataset.docsTerm || "") === term);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        el.classList.add("docs-term-flash");
        setTimeout(() => el.classList.remove("docs-term-flash"), 1600);
      }
    }, 80);
  }
});

document.addEventListener("click", (ev) => {
  if (ev.target.closest("[data-docs-focus-term]")) return;
  const jump = ev.target.closest("[data-docs-jump]");
  if (!jump) return;
  const id = jump.getAttribute("data-docs-jump");
  if (!id) return;
  ev.preventDefault();
  sessionStorage.setItem("okx_docs_jump", id);
  if (pageId() === "docs") {
    showPage("docs");
  } else {
    location.hash = "#/docs";
  }
});

$("btn-new-bot").addEventListener("click", () => openCreateBotModal());

$("bot-strategy-select")?.addEventListener("change", (ev) => {
  const id = ev.target.value;
  if (id) applyStrategyToBotForm(id);
  else syncBotCascadeUI();
});

$("bot-cascade-enabled")?.addEventListener("change", (ev) => {
  const cb = ev.target;
  if (cb.checked && !selectedBotStrategy()?.cascade_capable) {
    if (!ensureCascadeCapableStrategy()) cb.checked = false;
  }
  syncBotCascadeUI();
});
for (const side of ["buy", "sell"]) {
  $(`bot-cascade-${side}-custom`)?.addEventListener("change", () => syncBotCascadeUI());
  $("app-modal-form")?.[`cascade_${side}_pct`]?.addEventListener("input", () => syncBotCascadeUI());
  $("app-modal-form")?.[`cascade_${side}_pcts_raw`]?.addEventListener("input", () => syncBotCascadeUI());
  $(`bot-cascade-${side}-chips`)?.addEventListener("click", (ev) => {
    const btn = ev.target.closest("button[data-pct]");
    if (!btn || btn.disabled) return;
    const form = $("app-modal-form");
    if (form?.[`cascade_${side}_pct`]) form[`cascade_${side}_pct`].value = btn.dataset.pct;
    syncBotCascadeUI();
  });
}
["buy_pct", "profit_target_pct"].forEach((name) => {
  $("app-modal-form")?.querySelector(`[name="${name}"]`)?.addEventListener("input", () => syncBotCascadeUI());
});

$("bot-entry-mode")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-entry]");
  if (!btn) return;
  syncBotEntryModeSeg(btn.getAttribute("data-entry"));
});

$("bot-run-days")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-days]");
  if (!btn || btn.disabled) return;
  syncBotRunDaysSeg(Number(btn.dataset.days) || 7);
});


function botById(id) {
  return (lastStatus?.bots || []).find((b) => b.bot_id === id) || null;
}

function botForWalletCcy(ccy) {
  const key = String(ccy || "").toUpperCase();
  const matches = (lastStatus?.bots || []).filter(
    (b) => String(b.inst_id || "").split("-")[0].toUpperCase() === key,
  );
  if (!matches.length) return null;
  return matches.find((b) => b.bot_id === selectedBotId)
    || matches.find((b) => b.running)
    || matches[0];
}

function walletCanCreateBot(ccy) {
  if (!botsOn()) return false;
  const key = String(ccy || "").toUpperCase();
  if (!key || STABLES.has(key)) return false;
  return !botForWalletCcy(key);
}

async function openCreateBotFromWallet(ccy) {
  const key = String(ccy || "").toUpperCase();
  if (!key || STABLES.has(key)) {
    flash("w-msg", "Stables não usam bot Spot — escolha um token", false);
    return;
  }
  const asset = (lastWallet?.assets || []).find((a) => String(a.ccy || "").toUpperCase() === key);
  let inst = asset?.spot_inst || "";
  try {
    if (!inst) {
      const resolved = await resolveSpotInst(key, preferredQuote());
      inst = resolved.inst_id || `${key}-USDT`;
    }
  } catch (err) {
    flash("w-msg", err.message || `Sem par Spot para ${key}`, false);
    return;
  }
  await openCreateBotModal({
    name: `Bot ${key}`,
    inst_id: String(inst).toUpperCase(),
    icon: asset?.icon || "",
    icon_alt: asset?.icon_alt || "",
    quote_amount: "",
    entry_mode: "quote",
  });
}

function goToBot(botId) {
  if (!botId) return;
  location.hash = "#/bot";
  openBotPanel(botId);
}

async function handleBotAction(act, id) {
  if (!id) return;
  if (act === "select" || act === "open") {
    openBotPanel(id);
    return;
  }
  if (act === "edit") {
    selectedBotId = id;
    localStorage.setItem("okx_bot_id", id);
    openEditBotModal(id);
    return;
  }
  if (act === "detail") {
    selectedBotId = id;
    localStorage.setItem("okx_bot_id", id);
    openBotDetailModal(id);
    return;
  }
  if (act === "start") {
    openStartBotModal(id);
    return;
  }
  if (act === "test") {
    selectedBotId = id;
    localStorage.setItem("okx_bot_id", id);
    await openLabForBot(id, 30);
    return;
  }
  if (act === "stop") {
    openStopBotModal(id);
    return;
  }
  if (act === "tick") {
    openTickBotModal(id);
    return;
  }
  if (act === "delete") {
    openDeleteBotModal(id);
  }
}

$("bots-list")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-act]");
  if (btn) {
    const item = btn.closest(".bot-item");
    handleBotAction(btn.dataset.act, item?.dataset.id);
    return;
  }
  const execRow = ev.target.closest("tr[data-exec-idx]");
  if (execRow) {
    const idx = Number(execRow.dataset.execIdx);
    if (!Number.isFinite(idx) || idx < 0 || idx >= lastBotExecutions.length) return;
    openExecutionModal(lastBotExecutions[idx]);
    return;
  }
  const row = ev.target.closest(".bot-item > .bot-row");
  const item = row?.closest(".bot-item[data-id]");
  if (item?.dataset.id) toggleBotExpand(item.dataset.id);
});

$("bots-list")?.addEventListener("keydown", (ev) => {
  if (ev.key !== "Enter" && ev.key !== " ") return;
  const row = ev.target.closest(".bot-item > .bot-row");
  const item = row?.closest(".bot-item[data-id]");
  if (!item?.dataset.id) return;
  ev.preventDefault();
  toggleBotExpand(item.dataset.id);
});

function closeTokenMenu(id = "token-menu") {
  const el = $(id);
  if (el) el.hidden = true;
}

async function searchTokens(q, opts = {}) {
  const list = $(opts.listId || "order-token-list");
  if (!list) return;
  const quote = opts.quote || "USDT";
  const current = opts.current || "";
  list.innerHTML = `<div class="hint" style="margin:8px">Buscando…</div>`;
  try {
    const data = await api(`/api/instruments?quote=${encodeURIComponent(quote)}&q=${encodeURIComponent(q || "")}`);
    const rows = data.instruments || [];
    if (!rows.length) {
      list.innerHTML = `<div class="hint" style="margin:8px">Nenhum par encontrado</div>`;
      return;
    }
    list.innerHTML = rows.map((p) => {
      const chg = p.chg24 == null ? "" : fmtPct(p.chg24);
      const tone = p.chg24 > 0 ? "up" : p.chg24 < 0 ? "down" : "";
      const last = p.last == null ? "" : ` · ${fmt(p.last, 6)}`;
      return `<button type="button" class="token-item${p.inst_id === current ? " on" : ""}" data-inst="${p.inst_id}" data-icon="${p.icon}" data-alt="${p.icon_alt}">
        <img class="token-icon" src="${p.icon}" alt="" onerror="this.onerror=null;this.src='${p.icon_alt}'" />
        <span><span class="sym">${p.base}</span><div class="meta">${p.inst_id}${last}</div></span>
        <span class="chg ${tone}">${chg}</span>
      </button>`;
    }).join("");
  } catch (err) {
    list.innerHTML = `<div class="flash"><span class="err">${err.message}</span></div>`;
  }
}

async function searchBotTokens(q) {
  await searchTokens(q, {
    listId: "bot-token-list",
    quote: botModalQuote,
    current: $("app-modal-form")?.inst_id.value || "",
  });
}

function renderBotQuoteSeg() {
  const el = $("bot-quote-seg");
  if (!el) return;
  el.innerHTML = quoteButtonsHtml(botModalQuote);
}

$("bot-token-btn").addEventListener("click", async () => {
  if ($("bot-token-btn").disabled) return;
  const menu = $("bot-token-menu");
  menu.hidden = !menu.hidden;
  if (!menu.hidden) {
    renderBotQuoteSeg();
    $("bot-token-search").focus();
    await searchBotTokens($("bot-token-search").value.trim());
  }
});

$("bot-token-search").addEventListener("input", () => {
  clearTimeout(botTokenTimer);
  botTokenTimer = setTimeout(() => searchBotTokens($("bot-token-search").value.trim()), 220);
});

$("bot-quote-seg").addEventListener("click", async (ev) => {
  const btn = ev.target.closest("button[data-quote]");
  if (!btn) return;
  botModalQuote = btn.dataset.quote;
  renderBotQuoteSeg();
  await searchBotTokens($("bot-token-search").value.trim());
});

$("bot-token-list").addEventListener("click", (ev) => {
  const item = ev.target.closest(".token-item");
  if (!item) return;
  selectBotModalToken(item.dataset.inst, item.dataset.icon, item.dataset.alt);
  closeTokenMenu("bot-token-menu");
});

$("btn-bot-analyze")?.addEventListener("click", () => {
  runBotModalAnalyze();
});

$("bot-analyze-results")?.addEventListener("click", (ev) => {
  const useBtn = ev.target.closest("[data-bot-analyze-use]");
  if (!useBtn) return;
  applyBotAnalyzeStrategy(useBtn.getAttribute("data-bot-analyze-use"));
});

document.addEventListener("click", (ev) => {
  if (!ev.target.closest("#bot-token-picker")) closeTokenMenu("bot-token-menu");
  if (!ev.target.closest("#order-token-picker")) closeTokenMenu("order-token-menu");
});

function isNewAccount() {
  return selectedAccountId === NEW_ACCT || !(lastKeys?.accounts || []).length;
}

function currentAccount() {
  return (lastKeys?.accounts || []).find((a) => a.account_id === selectedAccountId) || null;
}

function isActiveSelected() {
  return !!(selectedAccountId && selectedAccountId === lastKeys?.active_account_id);
}

function applyKeysLock() {
  const form = $("keys-form");
  if (!form) return;
  const running = lastRunningCount > 0;
  const isNew = isNewAccount();
  const isActive = isActiveSelected();
  const saveBtn = $("btn-keys-save");
  if (saveBtn) saveBtn.disabled = running && (isActive || (!isNew && !lastKeys?.accounts?.length));
  const actBtn = $("btn-keys-activate");
  if (actBtn) actBtn.disabled = running;
  const testBtn = $("btn-keys-test");
  if (testBtn) {
    testBtn.hidden = isNew || !isActive;
    testBtn.disabled = isNew || !isActive;
  }
  for (const input of form.querySelectorAll("input, select")) {
    if (input.name === "account_name") {
      input.disabled = running && isActive;
    } else {
      input.disabled = running && isActive;
    }
  }
}

function fillKeysForm() {
  const form = $("keys-form");
  if (!form) return;
  const accounts = lastKeys?.accounts || [];
  const isNew = isNewAccount();
  const acct = currentAccount();
  form.account_name.value = isNew ? `Conta ${accounts.length + 1}` : (acct?.name || "");
  form.okx_flag.value = (isNew ? lastKeys?.okx_flag : acct?.okx_flag) || "0";
  form.okx_api_key.value = "";
  form.okx_secret_key.value = "";
  form.okx_passphrase.value = "";
  form.okx_api_key.placeholder = isNew
    ? "Cole a API Key"
    : (acct?.api_key_masked || lastKeys?.api_key_masked || "Cole a API Key");
  const saveBtn = $("btn-keys-save");
  if (saveBtn) saveBtn.textContent = isNew ? "Salvar e usar" : "Salvar chaves";
  const actBtn = $("btn-keys-activate");
  if (actBtn) actBtn.hidden = isNew || isActiveSelected() || !selectedAccountId;
  const delBtn = $("btn-keys-delete");
  if (delBtn) delBtn.hidden = isNew || isActiveSelected() || accounts.length < 2;
  applyKeysLock();
}

function renderAccountChips() {
  const box = $("keys-accounts");
  if (box) {
    box.innerHTML = "";
    box.hidden = true;
  }
  const actBtn = $("btn-keys-activate");
  if (actBtn) actBtn.hidden = true;
  const delBtn = $("btn-keys-delete");
  if (delBtn) delBtn.hidden = true;
}

function renderKeys(info, opts = {}) {
  lastKeys = info || {};
  const accounts = lastKeys.accounts || [];
  const keep = !!opts.keepSelection;
  if (!keep) {
    selectedAccountId = lastKeys.active_account_id || (accounts[0]?.account_id) || NEW_ACCT;
  } else if (selectedAccountId && selectedAccountId !== NEW_ACCT && !accounts.some((a) => a.account_id === selectedAccountId)) {
    selectedAccountId = lastKeys.active_account_id || NEW_ACCT;
  }
  if (!accounts.length) selectedAccountId = NEW_ACCT;
  const n = accounts.length;
  const pill = $("keys-pill");
  if (pill) {
    pill.textContent = lastKeys.configured ? "Configurado" : "Não configurado";
    pill.className = `pill ${lastKeys.configured ? "on" : "off"}`;
  }
  const parts = [];
  if (lastKeys.account_name) parts.push(escHtml(lastKeys.account_name));
  if (lastKeys.api_key_masked) parts.push(`Key ${escHtml(lastKeys.api_key_masked)}`);
  if (lastKeys.secret_set) parts.push("Secret salvo");
  if (lastKeys.passphrase_set) parts.push("Passphrase salva");
  const live = isLiveMode(lastKeys.okx_flag);
  parts.push(modeLabelHtml(live, live ? "Modo live" : "Modo demo"));
  if ($("keys-meta")) $("keys-meta").innerHTML = parts.join(" · ");
  setModeUI(lastKeys.okx_flag, lastKeys.configured);
  renderAccountChips();
  fillKeysForm();
}

async function loadKeys() {
  try {
    renderKeys(await api("/api/keys"));
  } catch (err) {
    flash("keys-msg", err.message, false);
  }
}

function renderOrderLimits(lim) {
  const form = $("order-limits-form");
  if (!form) return;
  form.min_usd.value = lim?.min_usd ?? 5;
  form.max_usd.value = lim?.max_usd ?? 100;
}

let lastBotDefaults = { default_interval_min: 30, exec_cleanup_wait_hours: 6, exec_cleanup_executed_days: 14 };

function renderBotDefaults(d) {
  lastBotDefaults = d || lastBotDefaults;
  const form = $("bot-defaults-form");
  if (!form) return;
  const en = $("cfg-bots-enabled");
  if (en) en.checked = !!d?.bots_enabled;
  form.default_interval_min.value = d?.default_interval_min ?? 30;
  form.exec_cleanup_wait_hours.value = d?.exec_cleanup_wait_hours ?? 6;
  form.exec_cleanup_executed_days.value = d?.exec_cleanup_executed_days ?? 14;
}

function botsOn() {
  return lastStatus?.bots_enabled === true;
}

function applyBotsEnabled() {
  document.body.classList.toggle("bots-off", !botsOn());
  const p = pageId();
  if (!botsOn() && (p === "overview" || p === "lab" || p === "strategies")) {
    location.hash = "#/wallet";
  }
}

function defaultBotIntervalMin() {
  return Number(lastBotDefaults?.default_interval_min) || 30;
}

async function loadConfig() {
  await loadKeys();
  try {
    renderOrderLimits(await api("/api/settings/order-limits"));
  } catch (err) {
    flash("limits-msg", err.message, false);
  }
  try {
    renderBotDefaults(await api("/api/settings/bot-defaults"));
  } catch (err) {
    flash("bot-defaults-msg", err.message, false);
  }
  // Hunter settings
  try {
    const hData = await api("/api/hunter");
    const hs = hData.settings || {};
    const hForm = $("hunter-settings-form");
    if (hForm) {
      $("cfg-hunter-enabled").checked = !!hs.enabled;
      hForm.scan_interval_min.value = hs.scan_interval_min || 10;
      hForm.quote.value = hs.quote || "USDT";
      hForm.min_drop_pct.value = hs.min_drop_pct || 1.5;
      hForm.max_drop_pct.value = hs.max_drop_pct || 35;
      hForm.min_vol_usd.value = hs.min_vol_usd || 80000;
      hForm.max_spread_pct.value = hs.max_spread_pct || 1;
      hForm.top_n.value = hs.top_n || 30;
    }
  } catch (_) {}
  // Portfolio interval (usa bot-defaults ou endpoint dedicado)
  try {
    const pForm = $("portfolio-settings-form");
    if (pForm) {
      const st = await api("/api/status");
      pForm.portfolio_interval_min.value = st.portfolio_interval_min || 2;
    }
  } catch (_) {}
  // LLM status
  try {
    const llm = await api("/api/assistant/status");
    $("cfg-llm-provider").textContent = llm.provider || "—";
    $("cfg-llm-model").textContent = llm.mode || "—";
    $("cfg-llm-status").textContent = llm.llm ? "Ativo" : "Desligado (modo local)";
    $("cfg-llm-status").style.color = llm.llm ? "var(--up)" : "var(--muted)";
  } catch (_) {}
  // Push notification status
  if ("Notification" in window) {
    const perm = Notification.permission;
    $("cfg-push-status").textContent = perm === "granted" ? "Permitido" : perm === "denied" ? "Bloqueado" : "Não configurado";
    $("cfg-push-status").style.color = perm === "granted" ? "var(--up)" : perm === "denied" ? "var(--down)" : "var(--muted)";
    $("btn-push-permission").hidden = perm === "granted";
  } else {
    $("cfg-push-status").textContent = "Não suportado";
    $("btn-push-permission").hidden = true;
  }
}

function walletAssetsFiltered(assets) {
  const list = (assets || []).filter((a) => a.spot !== false);
  if (walletShowDust) return list;
  return list.filter((a) => Number(a.total_bal) >= WALLET_DUST_MIN);
}

function syncWalletDustToggle() {
  const el = $("wallet-show-dust");
  if (el) el.checked = walletShowDust;
}

function updateWalletDustHint(allAssets, visibleAssets) {
  const el = $("w-dust-hint");
  if (!el) return;
  const hidden = (allAssets?.length || 0) - (visibleAssets?.length || 0);
  if (walletShowDust || hidden <= 0) {
    el.hidden = true;
    el.textContent = "";
    return;
  }
  el.hidden = false;
  el.textContent = `${hidden} token(s) com saldo abaixo de ${WALLET_DUST_MIN} oculto(s). Ative «Saldos < 0,001» para exibir.`;
}

function walletAssetBrl(a) {
  if (String(a?.ccy || "").toUpperCase() === "BRL") return Number(a.total_bal) || 0;
  return toBrl(Number(a?.eq_usd) || 0, "USD");
}

function lastToBrl(a) {
  const last = Number(a?.last);
  if (!Number.isFinite(last) || last <= 0) return null;
  const quote = String(a?.spot_inst || "").split("-")[1] || "USDT";
  if (quote === "BRL" || String(a?.ccy || "").toUpperCase() === "BRL") return last;
  return toBrl(last, quote === "USDC" ? "USDC" : "USD");
}

function sortWalletAssets(assets) {
  const { key, dir } = walletSort;
  return [...(assets || [])].sort((a, b) => {
    if (key === "ccy") {
      const va = String(a.ccy || "");
      const vb = String(b.ccy || "");
      return dir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
    }
    let va;
    let vb;
    va = Number(a[key]);
    vb = Number(b[key]);
    if (!Number.isFinite(va)) va = dir === "asc" ? Infinity : -Infinity;
    if (!Number.isFinite(vb)) vb = dir === "asc" ? Infinity : -Infinity;
    return dir === "asc" ? va - vb : vb - va;
  });
}

function syncWalletSortHeaders() {
  const { key, dir } = walletSort;
  document.querySelectorAll("#page-wallet th[data-sort]").forEach((th) => {
    th.classList.toggle("sort-asc", th.dataset.sort === key && dir === "asc");
    th.classList.toggle("sort-desc", th.dataset.sort === key && dir === "desc");
  });
}

function renderWallet(data) {
  lastWallet = data;
  setUsdtBrlRate(data.usdt_brl);
  const total = data.total_eq;
  $("w-total").textContent = total != null ? `$${fmt(total, 2)}` : "—";
  const brlEl = $("w-total-brl");
  if (brlEl) {
    const brl = total != null ? toBrl(total, "USD") : null;
    brlEl.textContent = brl != null ? `≈ R$ ${fmt(brl, 2)}` : "";
  }
  renderPnlKpi(data);
  $("w-updated").textContent = data.updated_at
    ? `Atualizado ${fmtTs(data.updated_at)}`
    : data.last_error || "";
  if (data.last_error) flash("w-msg", data.last_error, false);
  else flash("w-msg", "", true);

  syncWalletDustToggle();
  const allAssets = data.assets || [];
  const assets = sortWalletAssets(walletAssetsFiltered(allAssets));
  syncWalletSortHeaders();
  updateWalletDustHint(allAssets, assets);
  const body = $("wallet-body");
  if (!allAssets.length) {
    body.innerHTML = `<tr><td class="empty" colspan="8">Nenhum token com saldo. Cadastre as API Keys em Configurações e atualize.</td></tr>`;
    return;
  }
  if (!assets.length) {
    body.innerHTML = `<tr><td class="empty" colspan="8">Nenhum token com saldo ≥ ${WALLET_DUST_MIN}. Ative «Saldos &lt; 0,001» para ver posições menores.</td></tr>`;
    return;
  }
  const openMarks = openOrderMarksByBase(lastOpenOrders);
  body.innerHTML = assets.map((a) => {
    const chg = a.chg24 == null ? "—" : fmtPct(a.chg24);
    const chgCls = a.chg24 > 0 ? "buy" : a.chg24 < 0 ? "sell" : "";
    const uplPct = assetUplPct(a);
    const upl = a.spot_upl == null
      ? (uplPct == null ? "—" : fmtPct(uplPct))
      : `${fmtPnl(a.spot_upl)}${uplPct == null ? "" : ` <small class="pnl-pct">${fmtPct(uplPct)}</small>`}`;
    const uplTone = a.spot_upl != null ? Number(a.spot_upl) : uplPct;
    const uplCls = uplTone > 0 ? "buy" : uplTone < 0 ? "sell" : "";
    const brl = walletAssetBrl(a);
    const uplBrl = a.spot_upl == null ? null : toBrl(Number(a.spot_upl), "USD");
    const lastBrl = lastToBrl(a);
    const chgUsd = a.chg24 == null || a.last == null
      ? null
      : Number(a.last) * Number(a.chg24) / 100;
    const chgBrl = chgUsd == null ? null : toBrl(chgUsd, "USD");
    const extra = [];
    if (a.funding_bal > 0) extra.push(`funding ${fmt(a.funding_bal, 6)}`);
    if (a.avg_px) extra.push(`médio ${fmt(a.avg_px, 4)}`);
    const bot = botForWalletCcy(a.ccy);
    const botBtn = bot
      ? `<button class="btn btn-ico btn-ghost wallet-bot-link${bot.running ? " on" : ""}" data-bot="${bot.bot_id}" type="button" title="Ir para bot ${escHtml(bot.name || bot.inst_id)}${bot.running ? " · rodando" : ""}" aria-label="Ir para bot">${ICO.bot}</button>`
      : (walletCanCreateBot(a.ccy)
        ? `<button class="btn btn-ico btn-ghost" data-wallet-create-bot="${escHtml(a.ccy)}" type="button" title="Criar bot para ${escHtml(a.ccy)}" aria-label="Criar bot">${ICO.bot}</button>`
        : "");
    const actions = `${botBtn}<button class="btn btn-ico btn-ghost" data-order="swap" data-ccy="${a.ccy}" type="button" title="Comprar / vender" aria-label="Comprar ou vender">${ICO.swap}</button>
         <button class="btn btn-ico btn-ghost" data-chart="${a.ccy}" type="button" title="Gráfico" aria-label="Gráfico">${ICO.chart}</button>`;
    const chartTarget = (a.is_stable || isStableCcy(a.ccy))
      ? String(a.ccy || "").toUpperCase()
      : (a.spot_inst || instForWalletCcy(a.ccy) || a.ccy);
    const chartInst = escHtml(chartTarget);
    const openBadge = walletOpenOrderBadge(a.ccy, a, openMarks);
    return `<tr>
      <td>
        <div class="wallet-token-row">
          <div class="token-cell token-cell-link" data-chart-inst="${chartInst}" title="Abrir gráfico / saldo" role="link" tabindex="0">
            <img class="token-icon" src="${a.icon || ""}" alt="" onerror="this.onerror=null;this.src='${a.icon_alt || ""}'" />
            <span>${a.ccy}${extra.length ? `<small>${extra.join(" · ")}</small>` : ""}</span>
          </div>
          ${openBadge}
        </div>
      </td>
      <td class="num">${fmt(a.total_bal, 8)}</td>
      <td class="num">${fmt(a.avail, 8)}</td>
      <td class="num">${fmt(a.eq_usd, 2)}${brl != null ? `<small class="wallet-brl">R$ ${fmt(brl, 2)}</small>` : ""}</td>
      <td class="num">${fmt(a.last, 6)}${lastBrl != null ? `<small class="wallet-brl">R$ ${fmt(lastBrl, lastBrl >= 1 ? 4 : 6)}</small>` : ""}</td>
      <td class="num ${chgCls}">${chg}</td>
      <td class="num ${uplCls}">${upl}${uplBrl != null ? `<small class="wallet-brl">R$ ${fmt(uplBrl, 2)}</small>` : ""}</td>
      <td><div class="wallet-actions">${actions}</div></td>
    </tr>`;
  }).join("");
}

function openOrderMarksByBase(orders) {
  const map = {};
  for (const o of orders || []) {
    const inst = String(o.inst_id || "").toUpperCase();
    const base = inst.split("-")[0] || "";
    if (!base) continue;
    const rec = map[base] || (map[base] = { n: 0, buy: 0, sell: 0, insts: [] });
    rec.n += 1;
    if (String(o.side || "").toLowerCase() === "buy") rec.buy += 1;
    else rec.sell += 1;
    if (inst && !rec.insts.includes(inst)) rec.insts.push(inst);
  }
  return map;
}

function walletOpenOrderBadge(ccy, asset, marks) {
  const key = String(ccy || "").toUpperCase();
  const rec = marks[key];
  if (rec) {
    let cls = "mix";
    if (rec.buy && !rec.sell) cls = "buy";
    else if (rec.sell && !rec.buy) cls = "sell";
    const label = rec.n > 1 ? `${rec.n} ordens` : "ordem";
    const bits = [];
    if (rec.buy) bits.push(rec.buy === 1 ? "1 compra" : `${rec.buy} compras`);
    if (rec.sell) bits.push(rec.sell === 1 ? "1 venda" : `${rec.sell} vendas`);
    const pairs = rec.insts.length ? ` · ${rec.insts.join(", ")}` : "";
    const tip = `Ordem aberta: ${bits.join(" · ")}${pairs}. Abrir Ordens.`;
    return `<button type="button" class="wallet-open-ord ${cls}" data-goto-orders="${escHtml(key)}" title="${escHtml(tip)}">${escHtml(label)}</button>`;
  }
  if (walletOrdersOk) return "";
  const frozen = (Number(asset?.total_bal) || 0) - (Number(asset?.avail) || 0);
  if (frozen <= 1e-8) return "";
  return `<button type="button" class="wallet-open-ord mix" data-goto-orders="${escHtml(key)}" title="Saldo disponível menor que o total — pode haver ordem aberta. Abrir Ordens.">travado</button>`;
}

async function loadWallet() {
  try {
    const [portRes, openRes] = await Promise.allSettled([
      api("/api/portfolio"),
      api("/api/orders/open"),
    ]);
    if (openRes.status === "fulfilled") {
      lastOpenOrders = openRes.value?.orders || [];
      walletOrdersOk = true;
    }
    if (portRes.status !== "fulfilled") throw portRes.reason;
    const data = portRes.value;
    lastWallet = data;
    lastWalletTs = Date.now();
    setUsdtBrlRate(data.usdt_brl);
    await ensureFxRate();
    renderWallet(data);
    repaintPnlKpis();
  } catch (err) {
    flash("w-msg", err.message, false);
  }
}

function preferredQuote() {
  const assets = lastWallet?.assets || [];
  const brl = assets.find((a) => String(a.ccy).toUpperCase() === "BRL");
  const usdt = assets.find((a) => String(a.ccy).toUpperCase() === "USDT");
  if ((Number(brl?.eq_usd) || 0) >= (Number(usdt?.eq_usd) || 0) && Number(brl?.total_bal) > 0) return "BRL";
  if (Number(usdt?.total_bal) > 0) return "USDT";
  return orderQuote || "BRL";
}

function openOrderForAsset(ccy, side) {
  ccy = String(ccy || "").toUpperCase();
  void openOrderForAssetAsync(ccy, side);
}

async function openOrderForAssetAsync(ccy, side) {
  let quote;
  let inst;
  let tgt;
  try {
    if (STABLES.has(ccy)) {
      quote = ccy === "USD" ? "USDT" : ccy;
      inst = `BTC-${quote}`;
      side = "buy";
      tgt = "quote_ccy";
    } else {
      const pref = preferredQuote();
      const resolved = await resolveSpotInst(ccy, pref);
      inst = resolved.inst_id;
      quote = resolved.quote || inst.split("-")[1] || "USDT";
      if (!side || side === "swap" || side === "trade") side = "sell";
      tgt = side === "sell" ? "base_ccy" : "quote_ccy";
      if (resolved.inst_id !== `${ccy}-${pref}` && pref !== quote) {
        flash(
          "w-msg",
          `${ccy}: par ${ccy}-${pref} indisponível · usando ${inst}`,
          true,
        );
      }
    }
  } catch (err) {
    flash("w-msg", err.message || `Sem par spot para ${ccy}`, false);
    return;
  }
  orderQuote = quote;
  orderSide = side;
  localStorage.setItem("okx_order_quote", quote);
  localStorage.setItem("okx_order_inst", inst);
  orderIntent = { inst, side, quote, type: "market", tgt };
  orderContext = null;
  orderContextInst = null;
  orderLoadError = null;
  resetOrderFormForTokenSwitch();
  selectOrderToken(inst, "", "");
  setOrderFormLoading(true);
  if (pageId() === "orders") loadOrders();
  else location.hash = "#/orders";
}

$("wallet-show-dust")?.addEventListener("change", (ev) => {
  walletShowDust = !!ev.target.checked;
  localStorage.setItem("okx_wallet_show_dust", walletShowDust ? "1" : "0");
  if (lastWallet) renderWallet(lastWallet);
});

$("page-wallet")?.addEventListener("click", (ev) => {
  const th = ev.target.closest("th[data-sort]");
  if (!th) return;
  const key = th.dataset.sort;
  if (!key) return;
  if (walletSort.key === key) walletSort.dir = walletSort.dir === "asc" ? "desc" : "asc";
  else walletSort = { key, dir: key === "ccy" ? "asc" : "desc" };
  if (lastWallet) renderWallet(lastWallet);
});

$("wallet-body").addEventListener("click", (ev) => {
  const ordMark = ev.target.closest("button[data-goto-orders]");
  if (ordMark) {
    location.hash = "#/orders";
    return;
  }
  const botBtn = ev.target.closest("button[data-bot]");
  if (botBtn) {
    goToBot(botBtn.dataset.bot);
    return;
  }
  const createBtn = ev.target.closest("button[data-wallet-create-bot]");
  if (createBtn) {
    openCreateBotFromWallet(createBtn.getAttribute("data-wallet-create-bot"));
    return;
  }
  const chartBtn = ev.target.closest("button[data-chart]");
  if (chartBtn) {
    goTokenChart(chartBtn.dataset.chart);
    return;
  }
  const btn = ev.target.closest("button[data-order]");
  if (!btn) return;
  openOrderForAsset(btn.dataset.ccy, btn.dataset.order);
});

$("btn-wallet-refresh").addEventListener("click", async () => {
  await withRefresh("btn-wallet-refresh", async () => {
    try {
      await refreshAll();
      flash("w-msg", "Tudo atualizado", true);
    } catch (err) {
      flash("w-msg", err.message, false);
    }
  }, { statusId: "w-updated", statusText: "Atualizando tudo…" });
});

$("keys-form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const form = ev.currentTarget;
  const isNew = isNewAccount();
  const payload = {
    name: (form.account_name.value || "").trim() || (isNew ? `Conta ${(lastKeys?.accounts || []).length + 1}` : undefined),
    okx_flag: form.okx_flag.value,
  };
  if (form.okx_api_key.value.trim()) payload.okx_api_key = form.okx_api_key.value.trim();
  if (form.okx_secret_key.value.trim()) payload.okx_secret_key = form.okx_secret_key.value.trim();
  if (form.okx_passphrase.value.trim()) payload.okx_passphrase = form.okx_passphrase.value.trim();
  if (isNew && (!payload.okx_api_key || !payload.okx_secret_key || !payload.okx_passphrase)) {
    flash("keys-msg", "Nova conta precisa de API Key, Secret e Passphrase", false);
    return;
  }
  if (isNew) payload.activate = lastRunningCount === 0;
  const live = String(payload.okx_flag) === "0";
  openAppModal({
    title: isNew ? "Adicionar conta OKX" : "Salvar chaves",
    hint: live
      ? "As chaves vão para o servidor. Modo live: o bot e as ordens manuais operam com dinheiro real."
      : "As chaves vão para o servidor no modo demo/simulated.",
    rows: [
      ["Nome", payload.name || "—"],
      ["Modo", live ? "Live (ordens reais)" : "Demo / simulated", live ? "sell" : ""],
      ["API Key", payload.okx_api_key ? "Nova chave" : (isNew ? "—" : "Manter atual")],
      ["Secret", payload.okx_secret_key ? "Novo secret" : (isNew ? "—" : "Manter atual")],
      ["Passphrase", payload.okx_passphrase ? "Nova passphrase" : (isNew ? "—" : "Manter atual")],
      ...(isNew ? [["Ativar agora", payload.activate ? "Sim" : "Não (bots rodando)"]] : []),
    ],
    confirmLabel: isNew ? "Salvar conta" : "Salvar chaves",
    confirmClass: live ? "btn-sell" : "btn-primary",
    confirmIco: ICO.refresh,
    action: { type: "save-keys", payload, isNew, accountId: selectedAccountId },
  });
});

$("order-limits-form")?.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.currentTarget;
  const min_usd = Number(form.min_usd.value);
  const max_usd = Number(form.max_usd.value);
  if (!Number.isFinite(min_usd) || !Number.isFinite(max_usd) || min_usd <= 0 || max_usd <= 0) {
    flash("limits-msg", "Informe valores válidos", false);
    return;
  }
  if (min_usd > max_usd) {
    flash("limits-msg", "Mínimo não pode ser maior que o máximo", false);
    return;
  }
  try {
    const saved = await api("/api/settings/order-limits", {
      method: "PUT",
      body: JSON.stringify({ min_usd, max_usd }),
    });
    renderOrderLimits(saved);
    if (lastStatus) {
      lastStatus.min_usd = saved.min_usd;
      lastStatus.max_usd = saved.max_usd;
    }
    flash("limits-msg", `Salvo: $${fmt(saved.min_usd, 0)}–$${fmt(saved.max_usd, 0)} USD por ordem`, true);
  } catch (err) {
    flash("limits-msg", err.message, false);
  }
});

$("bot-defaults-form")?.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.currentTarget;
  const payload = {
    bots_enabled: !!$("cfg-bots-enabled")?.checked,
    default_interval_min: Number(form.default_interval_min.value),
    exec_cleanup_wait_hours: Number(form.exec_cleanup_wait_hours.value),
    exec_cleanup_executed_days: Number(form.exec_cleanup_executed_days.value),
  };
  if (!Number.isFinite(payload.default_interval_min) || payload.default_interval_min < 1) {
    flash("bot-defaults-msg", "Intervalo inválido", false);
    return;
  }
  try {
    const saved = await api("/api/settings/bot-defaults", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    renderBotDefaults(saved);
    if (lastStatus) lastStatus.bots_enabled = !!saved.bots_enabled;
    applyBotsEnabled();
    flash(
      "bot-defaults-msg",
      saved.bots_enabled
        ? `Bots ligados · intervalo ${fmt(saved.default_interval_min, 0)} min`
        : "Bots desligados — todos parados e ocultos no menu",
      true,
    );
  } catch (err) {
    flash("bot-defaults-msg", err.message, false);
  }
});

// Hunter settings form
$("hunter-settings-form")?.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.currentTarget;
  const payload = {
    enabled: $("cfg-hunter-enabled")?.checked || false,
    scan_interval_min: Number(form.scan_interval_min.value),
    quote: form.quote.value,
    min_drop_pct: Number(form.min_drop_pct.value),
    max_drop_pct: Number(form.max_drop_pct.value),
    min_vol_usd: Number(form.min_vol_usd.value),
    max_spread_pct: Number(form.max_spread_pct.value),
    top_n: Number(form.top_n.value),
  };
  try {
    await api("/api/hunter/settings", { method: "PUT", body: JSON.stringify(payload) });
    flash("hunter-settings-msg", "Configurações do Hunter salvas", true);
  } catch (err) {
    flash("hunter-settings-msg", err.message, false);
  }
});

// Portfolio interval form
$("portfolio-settings-form")?.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.currentTarget;
  const val = Number(form.portfolio_interval_min.value);
  if (!val || val < 1 || val > 60) {
    flash("portfolio-settings-msg", "Intervalo entre 1 e 60 min", false);
    return;
  }
  try {
    await api("/api/settings/bot-defaults", {
      method: "PUT",
      body: JSON.stringify({ portfolio_interval_min: val }),
    });
    flash("portfolio-settings-msg", `Intervalo do portfolio: ${val} min`, true);
  } catch (err) {
    flash("portfolio-settings-msg", err.message, false);
  }
});

// Push notification permission button
$("btn-push-permission")?.addEventListener("click", async () => {
  if ("Notification" in window) {
    const perm = await Notification.requestPermission();
    $("cfg-push-status").textContent = perm === "granted" ? "Permitido" : perm === "denied" ? "Bloqueado" : "Não configurado";
    $("cfg-push-status").style.color = perm === "granted" ? "var(--up)" : perm === "denied" ? "var(--down)" : "var(--muted)";
    $("btn-push-permission").hidden = perm === "granted";
  }
});

$("keys-accounts")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("[data-acct]");
  if (!btn) return;
  selectedAccountId = btn.getAttribute("data-acct") || NEW_ACCT;
  renderAccountChips();
  fillKeysForm();
});

$("btn-keys-activate")?.addEventListener("click", () => {
  const a = currentAccount();
  if (!a) return;
  const live = isLiveMode(a.okx_flag);
  openAppModal({
    title: "Usar esta conta",
    hint: "Carteira e ordens passam a esta conta. Pause os bots antes. Bots da outra conta ficam parados até você voltar nela.",
    rows: [
      ["Conta", a.name || a.account_id],
      ["Modo", live ? "Live (ordens reais)" : "Demo / simulated", live ? "sell" : ""],
    ],
    confirmLabel: "Usar esta conta",
    confirmClass: "btn-primary",
    confirmIco: ICO.swap,
    action: { type: "activate-account", id: a.account_id },
  });
});

$("btn-keys-delete")?.addEventListener("click", () => {
  const a = currentAccount();
  if (!a) return;
  openAppModal({
    title: "Apagar conta",
    hint: "Remove as chaves desta conta deste servidor. Não fecha a conta na OKX.",
    rows: [["Conta", a.name || a.account_id]],
    confirmLabel: "Apagar",
    confirmClass: "btn-sell",
    confirmIco: ICO.x,
    action: { type: "delete-account", id: a.account_id },
  });
});

$("btn-keys-test").addEventListener("click", async () => {
  if (!isActiveSelected()) {
    flash("keys-msg", "O teste usa a conta ativa. Ative esta conta primeiro.", false);
    return;
  }
  try {
    const h = await api("/api/health/okx");
    const fee = h.taker_fee_pct != null ? ` · taker ${Number(h.taker_fee_pct).toFixed(3)}%` : "";
    flash("keys-msg", `OKX ok · USDT ${fmt(h.usdt, 4)}${fee}`, true);
  } catch (err) {
    flash("keys-msg", err.message, false);
  }
});

$("tc-close")?.addEventListener("click", () => closeTokenChartModal());
$("tc-cancel")?.addEventListener("click", () => closeTokenChartModal());
$("token-chart-modal")?.addEventListener("click", (ev) => {
  if (ev.target?.dataset?.tcClose) closeTokenChartModal();
});
$("btn-tc-refresh")?.addEventListener("click", () => {
  chartForceRefresh = true;
  withRefresh("btn-tc-refresh", () => loadTokenChartModal(), {
    statusId: "tc-msg",
    statusText: "Atualizando…",
  });
});
$("tc-range")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-key], button[data-days]");
  if (!btn) return;
  const key = btn.dataset.key || "";
  const hit = CHART_RANGES.find((r) => r.key === key)
    || CHART_RANGES.find((r) => String(r.days) === String(btn.dataset.days));
  if (!hit) return;
  chartRangeKey = hit.key;
  chartDays = hit.days;
  localStorage.setItem("okx_chart_range", chartRangeKey);
  chartForceRefresh = true;
  loadTokenChartModal();
});
$("tc-trade")?.addEventListener("click", () => {
  const t = chartSelectionMeta(chartInst);
  const inst = t.stable
    ? (t.inst && String(t.inst).includes("-") ? t.inst : null)
    : (t.inst || chartInst);
  closeTokenChartModal();
  if (inst && String(inst).includes("-")) {
    goTradeToken(inst, t.icon, t.icon_alt);
  } else {
    location.hash = "#/orders";
  }
});

const ORDER_STATE = {
  live: "Aberta",
  partially_filled: "Parcial",
  filled: "Executada",
  canceled: "Cancelada",
  mmp_canceled: "Cancelada",
};

function orderInst() {
  return ($("order-form").inst_id.value || localStorage.getItem("okx_order_inst") || "BTC-USDT").trim().toUpperCase();
}

function selectOrderToken(instId, icon, iconAlt) {
  $("order-form").inst_id.value = instId || "";
  $("order-token-label").textContent = instId || "Escolher par";
  setIcon($("order-token-icon"), icon, iconAlt);
  if (instId) localStorage.setItem("okx_order_inst", instId);
}

function setOrderFormLoading(loading) {
  const form = $("order-form");
  const sk = $("order-form-skeleton");
  if (!form) return;
  form.classList.toggle("order-form--loading", !!loading);
  form.classList.toggle("order-form--error", !!orderLoadError && !loading);
  if (sk) sk.hidden = !loading;
  const lock = !!loading || !!orderLoadError;
  form.querySelectorAll("#order-form-fields input, #order-form-fields select, #order-form-fields button").forEach((el) => {
    if (el.id === "btn-order-refresh") {
      el.disabled = !!loading;
      return;
    }
    el.disabled = lock;
  });
  if ($("order-token-btn")) $("order-token-btn").disabled = !!loading;
}

function resetOrderFormForTokenSwitch() {
  const form = $("order-form");
  if (!form) return;
  form.sz.value = "";
  form.px.value = "";
  $("order-pct")?.querySelectorAll("button").forEach((b) => b.classList.remove("on"));
  const est = $("order-estimate");
  if (est) est.textContent = "";
  const meta = $("order-meta");
  if (meta) meta.innerHTML = '<span class="order-meta-sk">Carregando dados do par…</span>';
}

function orderReady(inst) {
  const id = String(inst || orderInst() || "").trim().toUpperCase();
  if (!id.includes("-")) return false;
  if (orderLoading) return false;
  if (orderLoadError) return false;
  if (!orderContext) return false;
  return String(orderContextInst || orderContext.inst_id || "").toUpperCase() === id;
}

function assertOrderReady(inst) {
  const id = String(inst || orderInst() || "").trim().toUpperCase();
  if (orderLoading) throw new Error("Aguarde o carregamento do par");
  if (orderLoadError) throw new Error(orderLoadError);
  if (!orderContext || String(orderContextInst || "").toUpperCase() !== id) {
    throw new Error("Dados do par ainda não carregaram — aguarde ou selecione o token de novo");
  }
}

async function fetchOrderContextApi(instId) {
  const id = String(instId || "").trim().toUpperCase();
  return api(`/api/orders/context?instId=${encodeURIComponent(id)}&_=${Date.now()}`);
}

async function loadOrderContextForInst(inst, opts = {}) {
  const id = String(inst || "").trim().toUpperCase();
  if (!id.includes("-")) throw new Error("Par inválido");
  const seq = ++orderLoadSeq;
  orderLoading = true;
  orderLoadError = null;
  if (!opts.preserveFields) {
    orderContext = null;
    orderContextInst = null;
    resetOrderFormForTokenSwitch();
    selectOrderToken(id, opts.icon || "", opts.iconAlt || "");
    setOrderFormLoading(true);
  } else {
    selectOrderToken(id, opts.icon || "", opts.iconAlt || "");
    if ($("btn-order-submit")) $("btn-order-submit").disabled = true;
  }
  if (!opts.silent && !opts.preserveFields) flash("order-msg", "", true);
  try {
    const ctx = await fetchOrderContextApi(id);
    if (seq !== orderLoadSeq) return null;
    renderOrderContext(ctx, { fresh: !opts.preserveFields });
    orderLoadError = null;
    if (!opts.preserveFields) setOrderFormLoading(false);
    else if ($("btn-order-submit")) $("btn-order-submit").disabled = false;
    return ctx;
  } catch (err) {
    if (seq !== orderLoadSeq) return null;
    if (!opts.preserveFields) {
      orderContext = null;
      orderContextInst = null;
    }
    orderLoadError = err?.summary || err?.message || "Erro ao carregar par";
    if (!opts.silent) {
      flash("order-msg", orderLoadError, false);
      if (err instanceof ApiError || err?.full) {
        showErrorModal(err, { title: "Erro ao carregar par" });
      }
    }
    if (!opts.preserveFields) {
      const meta = $("order-meta");
      if (meta) meta.textContent = "—";
      const est = $("order-estimate");
      if (est) est.textContent = "";
      setOrderFormLoading(false);
    } else if ($("btn-order-submit")) $("btn-order-submit").disabled = true;
    throw err;
  } finally {
    if (seq === orderLoadSeq) orderLoading = false;
  }
}

async function loadOrderHistoryOnly(opts = {}) {
  const forceHist = !!opts.forceHist;
  syncHistPeriodSeg();
  syncHistSideSeg();
  syncHistStatusSeg();
  syncHistOriginSeg();
  const histSearch = $("hist-token-search");
  if (histSearch && histSearch.value !== histTokenQuery) histSearch.value = histTokenQuery;
  const hist = await fetchOrderHistory(forceHist);
  renderHistTable(hist);
}

async function loadOrderTables(opts = {}) {
  const forceHist = !!opts.forceHist;
  syncHistPeriodSeg();
  syncHistSideSeg();
  syncHistStatusSeg();
  syncHistOriginSeg();
  const histSearch = $("hist-token-search");
  if (histSearch && histSearch.value !== histTokenQuery) histSearch.value = histTokenQuery;
  const [open, hist] = await Promise.all([
    api("/api/orders/open"),
    fetchOrderHistory(forceHist),
  ]);
  lastOpenOrders = open.orders || [];
  walletOrdersOk = true;
  if (lastWallet && pageId() === "wallet") renderWallet(lastWallet);
  renderOpenSummary(lastOpenOrders);
  $("orders-open").innerHTML = orderRows(lastOpenOrders, true);
  renderHistTable(hist);
}

function walletQuoteCcys() {
  // Só cotações Spot comuns — não usa altcoins da carteira como quote
  return [];
}

function renderOrderQuoteSeg() {
  if ($("order-quote-seg")) $("order-quote-seg").innerHTML = quoteButtonsHtml(orderQuote);
  if ($("tokens-quote")) $("tokens-quote").innerHTML = quoteButtonsHtml(orderQuote);
}

function syncOrderQuoteSeg() {
  if (!$("order-quote-seg").children.length) renderOrderQuoteSeg();
  $("order-quote-seg").querySelectorAll("button").forEach((b) => {
    b.classList.toggle("on", b.dataset.quote === orderQuote);
  });
}

function orderSizeUnit() {
  const tgt = $("order-form").tgt_ccy.value;
  const quote = orderContext?.quote || orderInst().split("-")[1] || "USDT";
  const base = orderContext?.base || (orderInst().split("-")[0] || "TOKEN");
  if (tgt === "quote_ccy") return { kind: "quote", ccy: quote };
  return { kind: "base", ccy: base };
}

function orderPrice() {
  const type = $("order-form").ord_type.value;
  if (type === "market") return Number(orderContext?.last || 0);
  const raw = String($("order-form").px.value ?? "").trim();
  if (!raw) return 0;
  const px = Number(raw);
  return Number.isFinite(px) && px > 0 ? px : 0;
}

function orderIsLimitLike(type) {
  return String(type || $("order-form")?.ord_type?.value || "limit") !== "market";
}

function updateOrderSizeHints() {
  if (orderLoading) return;
  const unit = orderSizeUnit();
  const minHint = minOrderHint();
  $("order-sz-unit").textContent = minHint ? `(${unit.ccy} · ${minHint})` : `(${unit.ccy})`;
  $("order-form").sz.placeholder = unit.kind === "quote"
    ? (minOrderQuote() ? `Mín. ${fmt(minOrderQuote(), 4)}` : "Ex. 49")
    : (minOrderBase() ? `Mín. ${fmtQty(minOrderBase())}` : "");
}

function onOrderPriceEdited() {
  updateOrderSizeHints();
  updateOrderEstimate();
}

function roundOrderBase(qty) {
  let sz = Number(qty);
  if (!Number.isFinite(sz) || sz <= 0) return 0;
  if (orderContext?.lot_sz) sz = floorToStep(sz, orderContext.lot_sz);
  return sz;
}

function floorToStep(value, step) {
  const n = Number(value);
  const s = Number(step);
  if (!Number.isFinite(n) || n <= 0) return 0;
  if (!Number.isFinite(s) || s <= 0) return n;
  return Math.floor(n / s + 1e-12) * s;
}

/** Quote (USDT/BRL): nunca arredonda para cima — evita 51008 no 100%. */
function floorQuoteAmount(value, digits = 2) {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return 0;
  const d = Math.max(0, Math.min(8, Number(digits) || 2));
  const f = 10 ** d;
  return Math.floor(n * f + 1e-12) / f;
}

function clampOrderSizeToAvail(sz, unitKind) {
  let v = Number(sz);
  if (!Number.isFinite(v) || v <= 0) return 0;
  const avail = availableForOrder();
  if (avail > 0 && v > avail) v = avail;
  if (unitKind === "quote") return floorQuoteAmount(v, 2);
  if (orderContext?.lot_sz) return floorToStep(v, orderContext.lot_sz);
  return v;
}

function orderLimitsUsd() {
  return {
    min: Number(lastStatus?.min_usd ?? 5),
    max: Number(lastStatus?.max_usd ?? 100),
  };
}

function quoteToUsd(amountQuote, quote) {
  const amt = Number(amountQuote);
  if (!Number.isFinite(amt) || amt <= 0) return null;
  const q = String(quote || "USDT").toUpperCase();
  if (["USDT", "USDC", "USD", "DAI", "BUSD", "TUSD"].includes(q)) return amt;
  if (q === "BRL") {
    const rate = Number(usdtBrlRate || lastStatus?.usdt_brl || 0);
    if (!rate) return null;
    return amt / rate;
  }
  return null;
}

function orderLimitsHintText() {
  const { min, max } = orderLimitsUsd();
  return `$${fmt(min, 0)}–$${fmt(max, 0)} USD por ordem`;
}

function orderLimitErr(quoteVal, quote) {
  if (quoteVal == null || !Number.isFinite(Number(quoteVal)) || Number(quoteVal) <= 0) return "";
  const usd = quoteToUsd(quoteVal, quote);
  if (usd == null) return "";
  const { min, max } = orderLimitsUsd();
  if (usd < min) {
    return `Abaixo do mínimo do sistema: $${fmt(min, 2)} USD (valor ≈ $${fmt(usd, 2)})`;
  }
  if (usd > max) {
    return `Acima do máximo do sistema: $${fmt(max, 2)} USD (valor ≈ $${fmt(usd, 2)})`;
  }
  return "";
}

function minOrderBase() {
  const n = Number(orderContext?.min_sz || 0);
  return n > 0 ? n : null;
}

function minOrderQuote() {
  const px = orderPrice();
  const minB = minOrderBase();
  if (!px || !minB) return null;
  // Arredonda para CIMA (centavos) — senão "mín. 1,2075 USDT" vira ~998 BOME e falha o minSz
  const raw = minB * px;
  return Math.ceil(raw * 100 - 1e-12) / 100;
}

function minOrderHint() {
  const quote = orderContext?.quote || "USDT";
  const base = orderContext?.base || "TOKEN";
  const minB = minOrderBase();
  const minQ = minOrderQuote();
  if (minB && minQ) return `mín. ${fmt(minQ, 2)} ${quote} (≥ ${fmtQty(minB)} ${base})`;
  if (minQ) return `mín. ${fmt(minQ, 2)} ${quote}`;
  if (minB) return `mín. ${fmtQty(minB)} ${base}`;
  return "";
}

function belowMinText(qtyBase, quoteValOverride) {
  const quote = orderContext?.quote || "USDT";
  const base = orderContext?.base || "TOKEN";
  const px = orderPrice();
  const quoteVal = quoteValOverride != null
    ? Number(quoteValOverride)
    : (px > 0 && qtyBase ? qtyBase * px : null);
  const sysErr = orderLimitErr(quoteVal, quote);
  if (sysErr) return sysErr;
  const minB = minOrderBase();
  if (!minB) return "";
  const minQ = minOrderQuote();
  // Compra em quote: se o USDT coberto arredondado ≥ mínimo, ok (evita falso negativo)
  if (quoteValOverride != null && minQ != null && Number(quoteValOverride) + 1e-8 >= minQ) {
    return "";
  }
  // Folga 0,1% no base — ruído de preço/lote
  if (qtyBase && qtyBase >= minB * 0.999) return "";
  if (!qtyBase || qtyBase >= minB) return "";
  const unit = orderSizeUnit();
  // Digitou valor típico de USDT no modo Token (ex.: 10 → 10 BOME em vez de 10 USDT)
  if (
    orderSide === "buy"
    && unit.kind === "base"
    && minQ != null
    && quoteValOverride == null
    && Number(qtyBase) + 1e-12 >= minQ
    && Number(qtyBase) <= Number(orderContext?.quote_avail || 0) + 1e-8
    && px > 0
    && (qtyBase / px) >= minB
  ) {
    return (
      `${fmtQty(qtyBase)} ${base} está abaixo do mínimo (${fmtQty(minB)} ${base}). `
      + `Se quis gastar ${fmt(qtyBase, 2)} ${quote}, mude “Informar em” para Valor (${quote}).`
    );
  }
  const have = qtyBase ? `sua ordem ≈ ${fmtQty(qtyBase)} ${base}` : "ordem abaixo do mínimo";
  return minQ
    ? `${have} · mínimo OKX ${fmtQty(minB)} ${base} (use ≥ ${fmt(minQ, 2)} ${quote})`
    : `${have} · mínimo OKX ${fmtQty(minB)} ${base}`;
}

function availableForOrder() {
  if (!orderContext) return 0;
  const unit = orderSizeUnit();
  const px = orderPrice();
  if (orderSide === "sell") {
    const base = Number(orderContext.base_avail || 0);
    return unit.kind === "quote" && px > 0 ? base * px : base;
  }
  const quoteAvail = Number(orderContext.quote_avail || 0);
  if (unit.kind === "quote") return quoteAvail;
  return px > 0 ? quoteAvail / px : 0;
}

function applyOrderPct(pct) {
  $("order-pct").querySelectorAll("button").forEach((b) => {
    b.classList.toggle("on", Number(b.dataset.pct) === Number(pct));
  });
  const unit = orderSizeUnit();
  let avail = availableForOrder();
  const funding = orderSide === "sell"
    ? Number(orderContext?.base_funding || 0)
    : Number(orderContext?.quote_funding || 0);
  if (avail <= 0) {
    const ccy = unit.ccy;
    flash(
      "order-msg",
      funding > 0
        ? `${fmt(funding, 4)} ${ccy} no funding. Transfira para trading.`
        : `Sem saldo de ${ccy}`,
      false,
    );
    return;
  }
  let sz = avail * (Number(pct) / 100);
  // 100%: deixa folga mínima (fee/arredondamento OKX)
  if (Number(pct) >= 100) sz = avail * 0.999;
  if (unit.kind === "quote") sz = floorQuoteAmount(sz, 2);
  else if (orderContext?.lot_sz) sz = floorToStep(sz, orderContext.lot_sz);
  sz = clampOrderSizeToAvail(sz, unit.kind);
  const px = orderPrice();
  const qtyBase = unit.kind === "quote" ? (px > 0 ? sz / px : 0) : sz;
  const digits = unit.kind === "quote" ? 2 : 8;
  $("order-form").sz.value = unit.kind === "quote"
    ? sz.toFixed(digits)
    : String(Number(sz.toFixed(digits)));
  const minErr = belowMinText(qtyBase, unit.kind === "quote" ? sz : null);
  if (minErr) flash("order-msg", minErr, false);
  else flash("order-msg", `${pct}% · ${fmt(sz, digits)} ${unit.ccy}`, true);
  updateOrderEstimate();
}

async function searchOrderTokens(q) {
  await searchTokens(q, {
    listId: "order-token-list",
    quote: orderQuote,
    current: orderInst(),
  });
}

async function loadTokens() {
  const body = $("tokens-body");
  if (!body) return;
  flash("tokens-msg", "", true);
  body.innerHTML = `<tr><td class="empty" colspan="7">Carregando…</td></tr>`;
  try {
    const q = ($("tokens-search")?.value || "").trim();
    // Com texto na busca: todos os pares (USDT, BRL, BTC…). Sem busca: filtro da cotação.
    const quote = q ? "ALL" : orderQuote;
    const data = await api(`/api/instruments?quote=${encodeURIComponent(quote)}&q=${encodeURIComponent(q)}`);
    lastTokens = (data.instruments || []).map(enrichTokenLiquidity);
    renderOrderQuoteSeg();
    const quoteSeg = $("tokens-quote");
    if (quoteSeg) quoteSeg.style.opacity = q ? "0.45" : "";
    if (q) {
      flash("tokens-msg", `${lastTokens.length} par(es) em todas as cotações · “${q}”`, true);
    }
    renderTokensTable();
  } catch (err) {
    flash("tokens-msg", err.message, false);
    body.innerHTML = `<tr><td class="empty" colspan="7">${err.message}</td></tr>`;
  }
}

function goTradeToken(inst, icon, iconAlt) {
  let pair = String(inst || "").toUpperCase();
  if (pair && !pair.includes("-")) pair = `${pair}-USDT`;
  if (!pair.includes("-")) return;
  const quote = (pair.split("-")[1] || orderQuote).toUpperCase();
  orderQuote = quote;
  orderSide = "buy";
  localStorage.setItem("okx_order_quote", quote);
  localStorage.setItem("okx_order_inst", pair);
  orderIntent = { inst: pair, side: "buy", quote, icon: icon || "", iconAlt: iconAlt || "", type: "market", tgt: "quote_ccy" };
  orderContext = null;
  orderContextInst = null;
  orderLoadError = null;
  resetOrderFormForTokenSwitch();
  selectOrderToken(pair, icon, iconAlt);
  setOrderFormLoading(true);
  const onOrders = pageId() === "orders";
  location.hash = "#/orders";
  if (onOrders) loadOrders();
}

function tokenDetailPayload(p, ctx) {
  const inst = String((ctx && ctx.inst_id) || p.inst_id || "").toUpperCase();
  const base = (ctx && ctx.base) || p.base || inst.split("-")[0] || "Token";
  const quote = (ctx && ctx.quote) || p.quote || inst.split("-")[1] || "";
  const last = ctx?.last ?? p.last;
  const chg = ctx?.chg24 ?? p.chg24;
  const chgTxt = chg == null ? "—" : fmtPct(chg);
  const chgCls = chg > 0 ? "buy" : chg < 0 ? "sell" : "";
  const vol = ctx?.vol24 ?? p.vol;
  const liq = p.liquidity || tokenLiquidityGrade(vol, ctx?.spread_pct ?? p.spread_pct);
  const upl = ctx?.token_upl;
  const uplPct = ctx?.token_upl_pct;
  const uplCls = upl > 0 ? "buy" : upl < 0 ? "sell" : "";
  const kpis = [
    { label: "Preço", value: last == null ? "—" : fmtPx(last) },
    { label: "24h", value: chgTxt, tone: chgCls },
    { label: "Vol 24h", value: vol == null ? "—" : fmtVol(vol) },
    { label: "Liquidez", value: liq },
  ];
  const marketRows = [
    ["Par", inst],
    ["Bid", ctx?.bid == null ? "—" : fmtPx(ctx.bid)],
    ["Ask", ctx?.ask == null ? "—" : fmtPx(ctx.ask)],
    ["Spread", (ctx?.spread_pct ?? p.spread_pct) == null ? "—" : `${fmt(ctx?.spread_pct ?? p.spread_pct, 3)}%`],
    ["Liquidez", `${liq} · ${(HUNTER_LIQ_TIP[liq] || "").replace(/^Liquidez [A-D] — /, "")}`],
    ["Máx 24h", ctx?.high24 == null ? "—" : fmtPx(ctx.high24)],
    ["Mín 24h", ctx?.low24 == null ? "—" : fmtPx(ctx.low24)],
    ["Abertura 24h", ctx?.open24 == null ? "—" : fmtPx(ctx.open24)],
  ];
  const balRows = ctx
    ? [
        [`${base} trading`, fmt(ctx.base_avail, 6)],
        [`${base} funding`, fmt(ctx.base_funding, 6)],
        [`${quote} trading`, fmt(ctx.quote_avail, 4)],
        [`${quote} funding`, fmt(ctx.quote_funding, 4)],
        ["Qtd posição", ctx.token_qty == null ? "—" : fmt(ctx.token_qty, 6)],
        ["Preço médio", ctx.token_avg_quote == null && ctx.token_avg == null ? "—" : fmtPx(ctx.token_avg_quote ?? ctx.token_avg)],
        ["PnL spot", upl == null ? "—" : `${fmtPnl(upl)} ${quote}${uplPct == null ? "" : ` (${fmtPct(uplPct)})`}`, uplCls],
      ]
    : [
        ["Saldos", "Conecte as API Keys para ver trading/funding"],
      ];
  const rulesRows = ctx
    ? [
        ["Mín. sz", ctx.min_sz != null ? String(ctx.min_sz) : "—"],
        ["Lot sz", ctx.lot_sz != null ? String(ctx.lot_sz) : "—"],
        ["Tick sz", ctx.tick_sz != null ? String(ctx.tick_sz) : "—"],
      ]
    : [];
  const sections = [
    {
      title: "Gráfico",
      html: `<button type="button" class="btn btn-ghost" data-chart-inst="${escHtml(inst)}" title="Abrir candles Spot OKX"><span class="btn-svg">${ICO.chart}</span> Ver gráfico Spot</button>`,
    },
    { title: "Mercado", rows: marketRows },
    { title: "Carteira", rows: balRows },
  ];
  if (rulesRows.length) sections.push({ title: "Regras do par", rows: rulesRows });
  return {
    title: `${base}`,
    hint: `${inst} · cotado em ${quote}`,
    icon: ctx?.icon || p.icon || "",
    iconAlt: ctx?.icon_alt || p.icon_alt || "",
    kpis,
    sections,
    rich: true,
    wide: true,
  };
}

async function openTokenDetail(p) {
  const inst = String(p.inst_id || "").toUpperCase();
  const base = tokenDetailPayload(p, null);
  openAppModal({
    ...base,
    confirmLabel: "Negociar",
    confirmClass: "btn-buy",
    confirmIco: ICO.swap,
    cancelLabel: "Fechar",
    action: {
      type: "token-trade",
      inst,
      icon: p.icon || "",
      iconAlt: p.icon_alt || "",
    },
  });
  try {
    const ctx = await api(`/api/orders/context?instId=${encodeURIComponent(inst)}`);
    if ($("app-modal").hidden) return;
    if (pendingAction?.type !== "token-trade" || pendingAction?.inst !== inst) return;
    const rich = tokenDetailPayload(p, ctx);
    setModalIcon(rich.icon, rich.iconAlt);
    $("app-modal-title").textContent = rich.title;
    const hintEl = $("app-modal-hint");
    if (hintEl) {
      hintEl.textContent = rich.hint;
      hintEl.hidden = !rich.hint;
    }
    fillModalBody({ kpis: rich.kpis, sections: rich.sections });
    if (ctx.icon) pendingAction.icon = ctx.icon;
    if (ctx.icon_alt) pendingAction.iconAlt = ctx.icon_alt;
  } catch (_) {
    /* sem keys — mantém dados da lista */
  }
}

function renderTokensTable() {
  const body = $("tokens-body");
  if (!body) return;
  const { key, dir } = tokensSort;
  const rows = lastTokens.slice().sort((a, b) => {
    let va = a[key];
    let vb = b[key];
    if (key === "base" || key === "inst_id") {
      va = String(va || "");
      vb = String(vb || "");
      return dir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
    }
    va = Number(va);
    vb = Number(vb);
    if (!Number.isFinite(va)) va = dir === "asc" ? Infinity : -Infinity;
    if (!Number.isFinite(vb)) vb = dir === "asc" ? Infinity : -Infinity;
    return dir === "asc" ? va - vb : vb - va;
  });
  document.querySelectorAll("#page-tokens th[data-sort]").forEach((th) => {
    th.classList.toggle("sort-asc", th.dataset.sort === key && dir === "asc");
    th.classList.toggle("sort-desc", th.dataset.sort === key && dir === "desc");
  });
  if (!rows.length) {
    body.innerHTML = `<tr><td class="empty" colspan="7">Nenhum token encontrado</td></tr>`;
    return;
  }
  body.innerHTML = rows.map((p) => {
    const chg = p.chg24 == null ? "—" : fmtPct(p.chg24);
    const tone = p.chg24 > 0 ? "buy" : p.chg24 < 0 ? "sell" : "";
    const inst = escHtml(p.inst_id || "");
    const icon = escHtml(p.icon || "");
    const alt = escHtml(p.icon_alt || "");
    const liq = String(p.liquidity || tokenLiquidityGrade(p.vol, p.spread_pct)).toUpperCase();
    const spr = p.spread_pct != null ? `spread ${fmt(p.spread_pct, 2)}%` : "spread —";
    const liqTip = escHtml(`${HUNTER_LIQ_TIP[liq] || HUNTER_LIQ_TIP.D} · ${spr}`);
    return `<tr>
      <td>
        <div class="token-cell token-cell-link" data-chart-inst="${inst}" title="Abrir gráfico Spot" role="link" tabindex="0">
          <img class="token-icon" src="${icon}" alt="" onerror="this.onerror=null;this.src='${alt}'" />
          <span>${escHtml(p.base || "—")}<small>${escHtml(p.quote || "")}</small></span>
        </div>
      </td>
      <td>${inst}</td>
      <td class="num">${fmt(p.last, 6)}</td>
      <td class="num ${tone}">${chg}</td>
      <td class="num">${fmtVol(p.vol)}</td>
      <td class="num"><span class="hunter-liq ${liq}" title="${liqTip}">${liq}</span></td>
      <td>
        <div class="token-row-actions">
          <button class="btn btn-ghost" data-token-chart="${inst}" type="button" title="Abrir gráfico Spot">Gráfico</button>
          <button class="btn btn-ghost" data-token-detail="${inst}" type="button">Detalhe</button>
          <button class="btn btn-primary" data-trade="${inst}" data-icon="${icon}" data-alt="${alt}" type="button">Negociar</button>
        </div>
      </td>
    </tr>`;
  }).join("");
}

function syncOrderForm() {
  if (orderLoading) return;
  const type = $("order-form").ord_type.value;
  const market = type === "market";
  $("order-px-wrap").style.display = market ? "none" : "";
  $("order-tgt-wrap").style.display = "";
  $("order-form").px.required = !market;
  const ctx = orderContext;
  const quote = ctx?.quote || orderInst().split("-")[1] || "USDT";
  const base = ctx?.base || (orderInst().split("-")[0] || "TOKEN");
  const tgtSelect = $("order-form").tgt_ccy;
  if (tgtSelect.options.length >= 2) {
    tgtSelect.options[0].textContent = `Valor (${quote})`;
    tgtSelect.options[1].textContent = `Token (${base})`;
    // Compra: só valor em quote (USDT) — evita "10" = 10 BOME em limite/mercado
    tgtSelect.options[1].disabled = orderSide === "buy";
  }
  if (orderSide === "buy") tgtSelect.value = "quote_ccy";
  if (orderSide === "sell") tgtSelect.value = "base_ccy";
  const unit = orderSizeUnit();
  $("order-sz-label").textContent = unit.kind === "quote" ? "Valor do par" : "Quantidade";
  updateOrderSizeHints();
  const limitLike = orderIsLimitLike(type);
  if ($("order-total-wrap")) $("order-total-wrap").hidden = !limitLike;
  $("btn-order-submit-label").textContent = orderSide === "buy" ? "Comprar" : "Vender";
  $("btn-order-submit-ico").innerHTML = orderSide === "buy" ? ICO.buy : ICO.sell;
  $("btn-order-submit").className = `btn btn-cta ${orderSide === "buy" ? "btn-buy" : "btn-sell"}`;
  syncOrderSide();
  updateOrderEstimate();
}

function orderQuoteCcy(o) {
  if (o?.quote) return String(o.quote).toUpperCase();
  const inst = String(o?.inst_id || "");
  const parts = inst.split("-");
  return (parts[1] || orderContext?.quote || "USDT").toUpperCase();
}

function moneyQuote(n, ccy, digits = 2) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `${fmt(n, digits)} ${ccy}`;
}

function updateOrderEstimate() {
  const el = $("order-estimate");
  const totalEl = $("order-total-value");
  const totalWrap = $("order-total-wrap");
  const type = $("order-form")?.ord_type?.value || "limit";
  const limitLike = orderIsLimitLike(type);
  if (totalWrap) totalWrap.hidden = !limitLike;
  if (!el && !totalEl) return;
  if (!orderReady()) {
    if (el) el.textContent = "";
    if (totalEl) totalEl.textContent = "—";
    return;
  }
  const ctx = orderContext;
  const quote = ctx?.quote || orderInst().split("-")[1] || "USDT";
  const sz = Number($("order-form").sz.value);
  if (!sz || sz <= 0) {
    if (el) el.textContent = limitLike && orderPrice() <= 0 ? "Informe o preço para calcular o valor" : "";
    if (totalEl) totalEl.textContent = "—";
    return;
  }
  const unit = orderSizeUnit();
  const px = orderPrice();
  const base = ctx?.base || orderInst().split("-")[0] || "TOKEN";
  const qtyBase = unit.kind === "quote" ? (px > 0 ? sz / px : 0) : sz;
  const totalQuote = unit.kind === "quote" ? sz : (px > 0 ? sz * px : 0);
  if (limitLike && (!px || px <= 0)) {
    if (totalEl) totalEl.textContent = "—";
    if (el) el.textContent = "Informe o preço para calcular o valor";
    return;
  }
  if (!totalQuote) {
    if (el) el.textContent = "";
    if (totalEl) totalEl.textContent = "—";
    return;
  }
  const minErr = belowMinText(qtyBase, unit.kind === "quote" ? sz : null);
  if (totalEl) totalEl.textContent = `${fmt(totalQuote, 2)} ${quote}`;
  // Conversão alternativa abaixo do campo sz
  const szBrlEl = $("order-sz-brl");
  if (szBrlEl) {
    const altSz = unit.kind === "quote" ? toAltCcy(sz, quote) : toAltCcy(totalQuote, quote);
    szBrlEl.textContent = altSz && altSz.value > 0 ? `≈ ${altSz.symbol} ${fmt(altSz.value, 2)}` : "";
  }
  if (minErr) {
    if (el) el.innerHTML = `<span class="err">${minErr}</span>`;
    return;
  }
  if (!el) return;
  // Ordem válida — limpa erro antigo no flash
  const msg = $("order-msg");
  if (msg && msg.classList.contains("err")) flash("order-msg", "", true);
  const altEst = toAltCcy(totalQuote, quote);
  const altEstTxt = altEst ? ` · ${altEst.symbol} ${fmt(altEst.value, 2)}` : "";
  el.innerHTML = `≈ ${fmtQty(qtyBase)} ${base} · ${fmt(totalQuote, 2)} ${quote}${altEstTxt}`;
}

function sumByQuote(orders, key) {
  const map = {};
  for (const o of orders || []) {
    const ccy = orderQuoteCcy(o);
    map[ccy] = (map[ccy] || 0) + (Number(o[key]) || 0);
  }
  return map;
}

function formatQuoteSums(map) {
  const entries = Object.entries(map).filter(([, v]) => Number.isFinite(v));
  if (!entries.length) return "0";
  const nonzero = entries.filter(([, v]) => Math.abs(v) > 1e-12);
  const use = nonzero.length ? nonzero : entries;
  return use.map(([ccy, v]) => moneyQuote(v, ccy)).join(" · ");
}

function renderOpenSummary(orders) {
  const el = $("open-summary");
  if (!el) return;
  const list = orders || [];
  const buys = list.filter((o) => o.side === "buy");
  const sells = list.filter((o) => o.side === "sell");
  const pnlMap = sumByQuote(list, "pnl");
  const pnlTotal = Object.values(pnlMap).reduce((acc, n) => acc + n, 0);
  const pnlCls = pnlTotal > 0 ? "up" : pnlTotal < 0 ? "down" : "";
  const pairs = [...new Set(list.map((o) => String(o.inst_id || "").toUpperCase()).filter(Boolean))];
  el.innerHTML = `
    <div><span>Compras abertas</span><strong>${formatQuoteSums(sumByQuote(buys, "value"))}</strong></div>
    <div><span>Vendas abertas</span><strong>${formatQuoteSums(sumByQuote(sells, "value"))}</strong></div>
    <div><span>PnL est.</span><strong class="${pnlCls}">${formatQuoteSums(pnlMap)}</strong></div>
    <div><span>Pares</span><strong>${pairs.length ? pairs.join(", ") : "—"}</strong></div>
  `;
}

function updateOrderMeta() {
  const ctx = orderContext;
  if (!ctx) return;
  const quote = ctx.quote || "USDT";
  const base = ctx.base || "";
  const lines = [];
  // Linha 1: Último preço
  if (ctx.last != null) lines.push(`Último ${fmtPx(ctx.last)}`);
  // Linha 2: Saldo (base ou quote dependendo do lado)
  if (orderSide === "sell") {
    const saldoTxt = `Saldo ${fmtQty(ctx.base_avail)} ${base}`;
    const saldoBrl = toBrl(ctx.base_avail * (ctx.last || 0), quote);
    lines.push(saldoBrl != null ? `${saldoTxt} (R$ ${fmt(saldoBrl, 2)})` : saldoTxt);
  } else {
    const saldoTxt = `Saldo ${fmt(ctx.quote_avail, 4)} ${quote}`;
    const saldoBrl = toBrl(ctx.quote_avail, quote);
    lines.push(saldoBrl != null ? `${saldoTxt} (R$ ${fmt(saldoBrl, 2)})` : saldoTxt);
  }
  // Linha 3: Custo médio e break-even (se venda)
  if (orderSide === "sell") {
    const avg = sellAvgInQuote(quote);
    if (avg && avg > 0) {
      const be = avg * 1.001;
      lines.push(`Custo médio ${fmt(avg, 4)} · Break-even ${fmt(be, 4)}`);
      // Linha 4: UPL estimado
      if (ctx.last != null && ctx.base_avail > 0) {
        const upl = (ctx.last - avg) * ctx.base_avail;
        const uplPct = ((ctx.last - avg) / avg) * 100;
        const uplBrl = toBrl(upl, quote);
        const uplBrlTxt = uplBrl != null ? ` (R$ ${fmt(uplBrl, 2)})` : "";
        const cls = upl >= 0 ? "up" : "down";
        lines.push(`UPL ${fmt(upl, 2)} ${quote}${uplBrlTxt} (${fmt(uplPct, 2)}%)`);
      }
    }
  }
  // Limites de ordem
  const limHint = orderLimitsHintText();
  if (limHint) lines.push(limHint);
  const el = $("order-meta");
  el.innerHTML = lines.map(l => `<span>${l}</span>`).join("<br>");
}

function setOrderSide(side) {
  orderSide = side === "sell" ? "sell" : "buy";
  $("order-pct")?.querySelectorAll("button").forEach((b) => b.classList.remove("on"));
  // Compra = valor em quote (USDT); venda = quantidade do token — evita "10" virar 10 BOME
  const tgt = $("order-form")?.tgt_ccy;
  if (tgt) tgt.value = orderSide === "buy" ? "quote_ccy" : "base_ccy";
  syncOrderSide();
  if (orderContext) updateOrderMeta();
  syncOrderForm();
}

function syncOrderSide() {
  const seg = $("order-side-seg");
  if (!seg) return;
  seg.querySelectorAll("button[data-side]").forEach((btn) => {
    const on = btn.dataset.side === orderSide;
    btn.classList.toggle("on", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
}

function renderOrderContext(ctx, { fresh = false } = {}) {
  orderContext = ctx;
  orderContextInst = String(ctx.inst_id || "").toUpperCase();
  orderLoadError = null;
  selectOrderToken(ctx.inst_id, ctx.icon, ctx.icon_alt);
  updateOrderMeta();
  const pxInput = $("order-form").px;
  if (ctx.last != null && (fresh || !pxInput.value)) pxInput.value = ctx.last;
  if (ctx.tick_sz) pxInput.step = ctx.tick_sz;
  syncOrderForm();
}

function orderFillPct(o) {
  if (o?.fill_pct != null && Number.isFinite(Number(o.fill_pct))) return Number(o.fill_pct);
  const sz = Number(o?.sz || 0);
  const fill = Number(o?.fill_sz || 0);
  if (sz <= 0) return null;
  const marketQuoteBuy = String(o?.ord_type || "") === "market"
    && String(o?.tgt_ccy || "") === "quote_ccy"
    && String(o?.side || "") === "buy";
  if (marketQuoteBuy) {
    const px = Number(o?.avg_px || o?.px || 0);
    if (px <= 0) return null;
    return Math.max(0, Math.min(100, ((fill * px) / sz) * 100));
  }
  return Math.max(0, Math.min(100, (fill / sz) * 100));
}

function realizadoCell(o) {
  const pct = orderFillPct(o);
  if (pct == null) return "—";
  const fill = Number(o.fill_sz || 0);
  const sz = Number(o.sz || 0);
  const verb = o.side === "sell" ? "Vendeu" : "Comprou";
  const cls = pct >= 100 ? "buy" : pct > 0 ? "" : "muted";
  const qty = fill > 0 && sz > 0 ? `<small>${fmt(fill, 6)} / ${fmt(sz, 6)}</small>` : "";
  return `<div class="fill-cell ${cls}"><strong>${verb} ${Math.round(pct)}%</strong>${qty}</div>`;
}

function orderTokenMeta(o) {
  const inst = String(o.inst_id || "").toUpperCase();
  const base = String(o.base || inst.split("-")[0] || "").toUpperCase();
  const lower = base.toLowerCase();
  const icon = o.icon || (lower ? `https://www.okx.com/cdn/oksupport/asset/currency/icon/${lower}.png` : "");
  const alt = o.icon_alt || (base ? `https://static.okx.com/cdn/wallet/logo/${base}.png` : "");
  return { inst, base, icon, alt };
}

function orderPairCell(o) {
  const { inst, base, icon, alt } = orderTokenMeta(o);
  if (!inst) return "—";
  const label = base && inst.includes("-") ? `<span>${escHtml(base)}<small>${escHtml(inst)}</small></span>` : `<span>${escHtml(inst)}</span>`;
  return `<div class="token-cell token-cell-link" data-chart-inst="${escHtml(inst)}" title="Abrir gráfico Spot" role="link" tabindex="0">
    <img class="token-icon" src="${escHtml(icon)}" alt="" onerror="this.onerror=null;this.src='${escHtml(alt)}';if(!this.src)this.hidden=true" />
    ${label}
  </div>`;
}

function orderPnlValue(o) {
  if (o?.pnl_realized != null && Number.isFinite(Number(o.pnl_realized))) return Number(o.pnl_realized);
  if (o?.pnl != null && Number.isFinite(Number(o.pnl))) return Number(o.pnl);
  return null;
}

function orderRows(orders, open) {
  if (!orders.length) {
    return `<tr><td class="empty" colspan="11">Nenhuma ordem</td></tr>`;
  }
  return orders.map((o) => {
    const sideCls = o.side === "buy" ? "buy" : "sell";
    const ccy = orderQuoteCcy(o);
    const pnlVal = orderPnlValue(o);
    const pnlCls = pnlVal > 0 ? "buy" : pnlVal < 0 ? "sell" : "";
    const pct = orderFillPct(o);
    const cancel = open
      ? `<td><button class="btn btn-ico btn-ghost" data-cancel="${o.ord_id}" data-inst="${o.inst_id || ""}" data-side="${o.side || ""}" data-type="${o.ord_type || ""}" data-sz="${o.sz ?? ""}" data-px="${o.px ?? ""}" data-value="${o.value ?? ""}" data-pnl="${pnlVal ?? ""}" data-quote="${ccy}" data-fill="${o.fill_sz ?? ""}" data-pct="${pct ?? ""}" type="button" title="Cancelar" aria-label="Cancelar">${ICO.x}</button></td>`
      : `<td>${ORDER_STATE[o.state] || o.state || "—"}</td>`;
    return `<tr class="order-row" data-ord-id="${o.ord_id || ""}" data-inst="${o.inst_id || ""}" style="cursor:pointer">
      <td>${fmtTs(o.created_at || o.updated_at)}</td>
      <td>${originCell(o)}</td>
      <td>${orderPairCell(o)}</td>
      <td class="${sideCls}">${String(o.side || "").toUpperCase()}</td>
      <td>${o.ord_type || "—"}</td>
      <td>${fmt(o.sz, 8)}</td>
      <td>${realizadoCell(o)}</td>
      <td>${fmt(o.px || o.avg_px, 6)}</td>
      <td>${moneyQuote(o.value, ccy)}</td>
      <td class="${pnlCls}">${pnlVal == null ? "—" : `${fmtPnl(pnlVal)} ${ccy}`}</td>
      ${cancel}
    </tr>`;
  }).join("");
}

function syncHistPeriodSeg() {
  document.querySelectorAll("#hist-period button[data-period]").forEach((btn) => {
    btn.classList.toggle("on", btn.getAttribute("data-period") === histPeriod);
  });
}

function syncHistSideSeg() {
  document.querySelectorAll("#hist-side button[data-side]").forEach((btn) => {
    btn.classList.toggle("on", btn.getAttribute("data-side") === histSide);
  });
}

function syncHistStatusSeg() {
  document.querySelectorAll("#hist-status button[data-status]").forEach((btn) => {
    btn.classList.toggle("on", btn.getAttribute("data-status") === histStatus);
  });
}

function syncHistOriginSeg() {
  document.querySelectorAll("#hist-origin button[data-origin]").forEach((btn) => {
    btn.classList.toggle("on", btn.getAttribute("data-origin") === histOrigin);
  });
}

function orderStatusGroup(state) {
  const s = String(state || "").toLowerCase();
  if (s === "filled" || s === "partially_filled") return "filled";
  if (s === "canceled" || s === "mmp_canceled" || s.includes("cancel")) return "canceled";
  return s || "other";
}

function orderOriginKind(o) {
  const origin = String(o?.origin || "").toLowerCase();
  if (origin === "bot") return "bot";
  if (origin === "user") return "user";
  if (o?.bot_id || o?.bot_name) return "bot";
  return "user";
}

function filterHistOrders(orders) {
  let list = orders || [];
  if (histOrigin === "bot" || histOrigin === "user") {
    list = list.filter((o) => orderOriginKind(o) === histOrigin);
  }
  if (histSide === "buy" || histSide === "sell") {
    list = list.filter((o) => String(o.side || "").toLowerCase() === histSide);
  }
  if (histStatus === "filled" || histStatus === "canceled") {
    list = list.filter((o) => orderStatusGroup(o.state) === histStatus);
  }
  const q = String(histTokenQuery || "").trim().toUpperCase().replace(/\s+/g, "");
  if (q) {
    list = list.filter((o) => {
      const inst = String(o.inst_id || "").toUpperCase();
      const base = String(o.base || inst.split("-")[0] || "").toUpperCase();
      const quote = String(o.quote || (inst.includes("-") ? inst.split("-")[1] : "") || "").toUpperCase();
      return inst.includes(q) || base.includes(q) || quote.includes(q) || `${base}-${quote}`.includes(q);
    });
  }
  return list;
}

function histPeriodMeta() {
  return HIST_PERIODS.find((p) => p.key === histPeriod) || HIST_PERIODS.find((p) => p.key === "30d") || HIST_PERIODS[0];
}

function setHistPeriodHint(hist, filteredCount) {
  const el = $("hist-period-hint");
  if (!el) return;
  const meta = histPeriodMeta();
  const label = hist?.period_label || meta.label;
  const sideLabel = { all: "todos os lados", buy: "compras", sell: "vendas" }[histSide] || histSide;
  const statusLabel = { all: "todos os status", filled: "executadas", canceled: "canceladas" }[histStatus] || histStatus;
  const originLabel = { all: "bot + usuário", bot: "só bot", user: "só usuário" }[histOrigin] || histOrigin;
  const total = hist?.count_total ?? filteredCount;
  const n = filteredCount;
  const qBit = histTokenQuery.trim() ? ` · busca “${escHtml(histTokenQuery.trim())}”` : "";
  const filtersActive = histSide !== "all" || histStatus !== "all" || histOrigin !== "all" || !!histTokenQuery.trim();
  const countBit = Number.isFinite(n)
    ? (filtersActive ? ` · ${n}/${total ?? "?"}${qBit}` : ` · ${n} ordem(ns)`)
    : "";
  const cacheBit = hist?.cached
    ? ` · cache ${Math.round(hist.cache_age_s || 0)}s`
    : (hist?.from_client_cache ? " · cache local" : "");
  if (hist?.note) {
    el.innerHTML = `${escHtml(hist.note)}${countBit}${cacheBit}`;
  } else {
    el.innerHTML = `<strong>${escHtml(label)}</strong> · origem <strong>${escHtml(originLabel)}</strong> · ${escHtml(sideLabel)} · ${escHtml(statusLabel)}${countBit}${cacheBit}`;
  }
}

function renderHistTable(hist) {
  const all = hist?.orders_all || hist?.orders || [];
  const filtered = filterHistOrders(all);
  $("orders-history").innerHTML = orderRows(filtered, false);
  setHistPeriodHint(
    {
      ...hist,
      count_total: all.length,
      cached: hist?.cached,
      cache_age_s: hist?.cache_age_s,
      from_client_cache: hist?.from_client_cache,
      note: hist?.note,
      period_label: hist?.period_label,
    },
    filtered.length,
  );
}

async function fetchOrderHistory(force = false) {
  const fresh =
    !force &&
    histClientCache.payload &&
    histClientCache.period === histPeriod &&
    Date.now() - histClientCache.ts < HIST_CLIENT_TTL_MS;
  if (fresh) {
    return { ...histClientCache.payload, from_client_cache: true, cached: true, cache_age_s: (Date.now() - histClientCache.ts) / 1000 };
  }
  const q = new URLSearchParams({
    period: histPeriod,
    side: "all",
  });
  if (force) q.set("refresh", "1");
  const hist = await api(`/api/orders/history?${q}`);
  // guarda lista completa (sem filtro de lado) para trocar Compra/Venda localmente
  const payload = {
    ...hist,
    orders_all: hist.orders || [],
    orders: hist.orders || [],
    count_total: hist.count_total ?? (hist.orders || []).length,
  };
  histClientCache = { period: histPeriod, ts: Date.now(), payload };
  persistHistClientCache();
  return payload;
}

async function loadOrders(opts = {}) {
  const forceHist = !!opts.forceHist;
  const preserveFields = !!opts.preserveFields;
  let targetInst = orderInst();
  const intent = orderIntent;
  if (intent?.inst) targetInst = String(intent.inst).trim().toUpperCase();
  $("order-form").inst_id.value = targetInst;
  renderOrderQuoteSeg();
  try {
    await loadOrderContextForInst(targetInst, {
      preserveFields,
      icon: intent?.icon,
      iconAlt: intent?.iconAlt,
      silent: preserveFields,
    });
    if (intent) {
      orderIntent = null;
      if (intent.side) orderSide = intent.side;
      if (intent.quote) {
        orderQuote = intent.quote;
        localStorage.setItem("okx_order_quote", orderQuote);
      }
      if (intent.type) $("order-form").ord_type.value = intent.type;
      if (intent.tgt) $("order-form").tgt_ccy.value = intent.tgt;
      syncOrderSide();
      syncOrderForm();
    }
    const needWallet = !lastWallet || Date.now() - lastWalletTs > 30000;
    if (needWallet) {
      try {
        const port = await api("/api/portfolio");
        lastWallet = port;
        lastWalletTs = Date.now();
      } catch (_) {}
    }
    await loadOrderTables({ forceHist });
    renderOrderQuoteSeg();
  } catch (err) {
    if (intent) orderIntent = intent;
    return;
  }
}

$("order-token-btn").addEventListener("click", async () => {
  const menu = $("order-token-menu");
  menu.hidden = !menu.hidden;
  if (!menu.hidden) {
    syncOrderQuoteSeg();
    $("order-token-search").focus();
    await searchOrderTokens($("order-token-search").value.trim());
  }
});

$("order-token-search").addEventListener("input", () => {
  clearTimeout(orderTokenTimer);
  orderTokenTimer = setTimeout(() => searchOrderTokens($("order-token-search").value.trim()), 220);
});

async function changeOrderQuote(quote) {
  orderQuote = quote;
  localStorage.setItem("okx_order_quote", orderQuote);
  renderOrderQuoteSeg();
  syncOrderQuoteSeg();
  const qPicker = $("order-token-search")?.value.trim() || "";
  if ($("order-token-menu") && !$("order-token-menu").hidden) await searchOrderTokens(qPicker);
  if (pageId() === "tokens") await loadTokens();
}

$("order-quote-seg").addEventListener("click", async (ev) => {
  const btn = ev.target.closest("button[data-quote]");
  if (!btn) return;
  await changeOrderQuote(btn.dataset.quote);
});

$("tokens-quote").addEventListener("click", async (ev) => {
  const btn = ev.target.closest("button[data-quote]");
  if (!btn) return;
  await changeOrderQuote(btn.dataset.quote);
});

$("tokens-search").addEventListener("input", () => {
  clearTimeout(orderTokenTimer);
  orderTokenTimer = setTimeout(() => loadTokens(), 220);
});

$("btn-tokens-refresh").addEventListener("click", () => {
  withRefresh("btn-tokens-refresh", () => loadTokens(), { statusId: "tokens-msg", statusText: "Atualizando tokens…" });
});

$("page-tokens").addEventListener("click", (ev) => {
  const th = ev.target.closest("th[data-sort]");
  if (th) {
    const key = th.dataset.sort;
    if (!key) return;
    if (tokensSort.key === key) tokensSort.dir = tokensSort.dir === "asc" ? "desc" : "asc";
    else tokensSort = { key, dir: key === "base" || key === "inst_id" ? "asc" : "desc" };
    renderTokensTable();
    return;
  }
  const detailBtn = ev.target.closest("button[data-token-detail]");
  if (detailBtn) {
    const inst = detailBtn.getAttribute("data-token-detail");
    const p = lastTokens.find((x) => String(x.inst_id || "").toUpperCase() === String(inst || "").toUpperCase());
    if (p) openTokenDetail(p);
    return;
  }
  const chartBtn = ev.target.closest("button[data-token-chart]");
  if (chartBtn) {
    goTokenChart(chartBtn.getAttribute("data-token-chart"));
    return;
  }
  const btn = ev.target.closest("button[data-trade]");
  if (!btn) return;
  goTradeToken(btn.dataset.inst || btn.dataset.trade, btn.dataset.icon, btn.dataset.alt);
});

$("order-token-list").addEventListener("click", async (ev) => {
  const item = ev.target.closest(".token-item");
  if (!item) return;
  closeTokenMenu("order-token-menu");
  try {
    await loadOrderContextForInst(item.dataset.inst, {
      icon: item.dataset.icon,
      iconAlt: item.dataset.alt,
    });
    await loadOrderTables();
  } catch (_) {}
});

$("order-side-seg")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-side]");
  if (!btn || btn.dataset.side === orderSide) return;
  setOrderSide(btn.dataset.side);
});

$("order-form").ord_type.addEventListener("change", () => {
  $("order-pct").querySelectorAll("button").forEach((b) => b.classList.remove("on"));
  syncOrderForm();
});
$("order-form").tgt_ccy.addEventListener("change", () => {
  $("order-pct").querySelectorAll("button").forEach((b) => b.classList.remove("on"));
  syncOrderForm();
});
$("order-form").sz.addEventListener("input", updateOrderEstimate);
$("order-form").px.addEventListener("input", onOrderPriceEdited);
$("order-form").px.addEventListener("change", onOrderPriceEdited);

$("order-pct").addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-pct]");
  if (!btn) return;
  applyOrderPct(btn.dataset.pct);
});

function clearOrderForm() {
  const form = $("order-form");
  form.sz.value = "";
  form.ord_type.value = "limit";
  form.tgt_ccy.value = "quote_ccy";
  orderSide = "buy";
  syncOrderSide();
  $("order-pct").querySelectorAll("button").forEach((b) => b.classList.remove("on"));
  if (orderContext?.last) form.px.value = orderContext.last;
  else form.px.value = "";
  flash("order-msg", "Formulário limpo", true);
  closeModal();
  syncOrderForm();
}

$("btn-order-clear").addEventListener("click", clearOrderForm);
$("btn-order-refresh").addEventListener("click", () => {
  withRefresh("btn-order-refresh", () => loadOrders({ preserveFields: true }), { statusId: "order-msg", statusText: "Atualizando ordens…" });
});
$("btn-open-refresh").addEventListener("click", () => {
  withRefresh("btn-open-refresh", () => loadOrders());
});
$("btn-hist-refresh").addEventListener("click", () => {
  clearHistClientCache();
  withRefresh("btn-hist-refresh", () => loadOrderHistoryOnly({ forceHist: true }));
});

$("hist-period")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-period]");
  if (!btn) return;
  const p = btn.getAttribute("data-period");
  if (!p || p === histPeriod) return;
  histPeriod = p;
  localStorage.setItem("okx_hist_period", histPeriod);
  syncHistPeriodSeg();
  withRefresh("btn-hist-refresh", () => loadOrderHistoryOnly());
});

$("hist-side")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-side]");
  if (!btn) return;
  const s = btn.getAttribute("data-side");
  if (!s || s === histSide) return;
  histSide = s;
  localStorage.setItem("okx_hist_side", histSide);
  syncHistSideSeg();
  if (histClientCache.payload && histClientCache.period === histPeriod) {
    renderHistTable({ ...histClientCache.payload, from_client_cache: true, cached: true });
    return;
  }
  withRefresh("btn-hist-refresh", () => loadOrderHistoryOnly());
});

$("hist-status")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-status]");
  if (!btn) return;
  const s = btn.getAttribute("data-status");
  if (!s || s === histStatus) return;
  histStatus = s;
  localStorage.setItem("okx_hist_status", histStatus);
  syncHistStatusSeg();
  if (histClientCache.payload && histClientCache.period === histPeriod) {
    renderHistTable({ ...histClientCache.payload, from_client_cache: true, cached: true });
    return;
  }
  withRefresh("btn-hist-refresh", () => loadOrderHistoryOnly());
});

$("hist-origin")?.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-origin]");
  if (!btn) return;
  const o = btn.getAttribute("data-origin");
  if (!o || o === histOrigin) return;
  histOrigin = o;
  localStorage.setItem("okx_hist_origin", histOrigin);
  syncHistOriginSeg();
  if (histClientCache.payload && histClientCache.period === histPeriod) {
    renderHistTable({ ...histClientCache.payload, from_client_cache: true, cached: true });
    return;
  }
  withRefresh("btn-hist-refresh", () => loadOrderHistoryOnly());
});

$("hist-token-search")?.addEventListener("input", (ev) => {
  clearTimeout(histTokenTimer);
  histTokenTimer = setTimeout(() => {
    histTokenQuery = String(ev.target.value || "");
    localStorage.setItem("okx_hist_token_q", histTokenQuery);
    if (histClientCache.payload && histClientCache.period === histPeriod) {
      renderHistTable({ ...histClientCache.payload, from_client_cache: true, cached: true });
      return;
    }
    void loadOrderHistoryOnly();
  }, 180);
});

const TYPE_LABEL = {
  market: "Mercado",
  limit: "Limite",
  post_only: "Post-only",
  ioc: "IOC",
  fok: "FOK",
};

function buildOrderPayload() {
  assertOrderReady();
  const form = $("order-form");
  const type = form.ord_type.value;
  // Compra = valor (USDT); venda = token
  if (orderSide === "buy") form.tgt_ccy.value = "quote_ccy";
  if (orderSide === "sell") form.tgt_ccy.value = "base_ccy";
  const unit = orderSizeUnit();
  const entered = Number(form.sz.value);
  if (!entered || entered <= 0) {
    throw new Error(unit.kind === "quote" ? "informe o valor do par, ex. 10" : "informe a quantidade");
  }
  const px = type === "market" ? Number(orderContext?.last || 0) : Number(form.px.value);
  if (type !== "market" && (!px || px <= 0)) throw new Error("informe o preço");
  if (unit.kind === "quote" && (!px || px <= 0) && !(type === "market" && orderSide === "buy")) {
    throw new Error("sem preço para converter o valor em token");
  }
  const quoteVal = unit.kind === "quote" ? entered : (px > 0 ? entered * px : null);
  const qtyBaseRaw = unit.kind === "quote" ? (px > 0 ? entered / px : null) : entered;
  if (orderSide === "buy") {
    const avail = Number(orderContext?.quote_avail || 0);
    const fund = Number(orderContext?.quote_funding || 0);
    const q = orderContext?.quote || "USDT";
    if (!(avail > 1e-12)) {
      throw new Error(
        fund > 1e-8
          ? `Sem saldo trading de ${q}. Há ${fmt(fund, 4)} ${q} no funding — transfira para trading antes de comprar.`
          : `Sem saldo trading de ${q}. Deposite ou transfira para a conta trading.`,
      );
    }
    if (quoteVal != null && Number.isFinite(quoteVal)) {
      const safe = floorQuoteAmount(Math.min(quoteVal, avail > 0 ? avail * 0.999 : quoteVal), 2);
      if (quoteVal > avail + 1e-8) {
        throw new Error(
          fund > 1e-8
            ? `Saldo trading ${fmt(avail, 4)} ${q} < ordem ${fmt(quoteVal, 4)}. Há ${fmt(fund, 4)} ${q} no funding — transfira para trading.`
            : `Saldo trading ${fmt(avail, 4)} ${q} insuficiente para ${fmt(quoteVal, 4)} ${q}. Máx. ≈ ${fmt(safe, 2)} ${q}.`,
        );
      }
    }
  }
  if (orderSide === "sell") {
    const avail = Number(orderContext?.base_avail || 0);
    const fund = Number(orderContext?.base_funding || 0);
    const b = orderContext?.base || "TOKEN";
    if (!(avail > 1e-12)) {
      throw new Error(
        fund > 1e-8
          ? `Sem saldo trading de ${b}. Há ${fmtQty(fund)} ${b} no funding — transfira antes de vender.`
          : `Sem saldo trading de ${b}.`,
      );
    }
    if (qtyBaseRaw != null && Number.isFinite(qtyBaseRaw) && qtyBaseRaw > avail + 1e-12) {
      throw new Error(
        fund > 1e-8
          ? `Saldo trading ${fmtQty(avail)} ${b} < ordem. Há ${fmtQty(fund)} ${b} no funding — transfira.`
          : `Saldo trading ${fmtQty(avail)} ${b} insuficiente.`,
      );
    }
  }
  const payload = {
    inst_id: orderInst(),
    side: orderSide,
    ord_type: type,
  };
  // Compra: sz sempre em quote (USDT); limite também — backend converte para base
  if (orderSide === "buy") {
    const spend = clampOrderSizeToAvail(entered, "quote");
    const qtyEst = px > 0 ? spend / px : null;
    const minErr = belowMinText(qtyEst, spend);
    if (minErr) throw new Error(minErr);
    if (!spend) throw new Error("valor inválido após arredondar para baixo");
    payload.tgt_ccy = "quote_ccy";
    payload.sz = spend;
    if (type !== "market") payload.px = Number(form.px.value);
  } else {
    const qty = roundOrderBase(qtyBaseRaw);
    if (!qty) throw new Error("quantidade inválida após arredondar o lote");
    const capped = clampOrderSizeToAvail(qty, "base");
    const minErr = belowMinText(capped, quoteVal);
    if (minErr) throw new Error(minErr);
    payload.sz = capped;
    if (type === "market") payload.tgt_ccy = "base_ccy";
    else payload.px = Number(form.px.value);
  }
  payload._quote_val = payload.tgt_ccy === "quote_ccy" ? payload.sz : (px > 0 ? payload.sz * px : quoteVal);
  payload._qty_base = payload.tgt_ccy === "quote_ccy"
    ? (px > 0 ? payload.sz / px : qtyBaseRaw)
    : payload.sz;
  payload._unit = orderSide === "buy"
    ? { kind: "quote", ccy: orderContext?.quote || "USDT" }
    : { kind: "base", ccy: orderContext?.base || "TOKEN" };
  return payload;
}

function escHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function factsHtml(rows) {
  if (!rows || !rows.length) return "";
  return `<div class="modal-facts-grid">${rows.map(([k, v, cls]) => {
    const tone = cls ? ` ${cls}` : "";
    // Suportar BRL como segunda linha (separado por \n)
    const parts = String(v).split("\n");
    const main = escHtml(parts[0]);
    const sub = parts[1] ? `<small class="modal-fact-sub">${escHtml(parts[1])}</small>` : "";
    return `<div class="modal-fact">
      <span class="modal-fact-label">${escHtml(k)}</span>
      <strong class="modal-fact-value${tone}">${main}</strong>${sub}
    </div>`;
  }).join("")}</div>`;
}

function kpisHtml(kpis) {
  if (!kpis || !kpis.length) return "";
  return kpis.map((k) => {
    const tone = k.tone ? ` ${k.tone}` : "";
    return `<div class="modal-kpi${tone}">
      <span>${escHtml(k.label || "")}</span>
      <strong>${escHtml(k.value ?? "—")}</strong>
    </div>`;
  }).join("");
}

function sectionsHtml(sections) {
  if (!sections || !sections.length) return "";
  return sections.map((sec) => {
    const title = sec.title ? `<div class="modal-section-title">${escHtml(sec.title)}</div>` : "";
    if (sec.html) return `<div class="modal-section">${title}${sec.html}</div>`;
    return `<div class="modal-section">${title}${factsHtml(sec.rows || [])}</div>`;
  }).join("");
}

function setModalIcon(icon, iconAlt) {
  const img = $("app-modal-icon");
  if (!img) return;
  if (!icon && !iconAlt) {
    img.hidden = true;
    img.removeAttribute("src");
    return;
  }
  img.hidden = false;
  img.onerror = () => {
    if (iconAlt && img.src !== iconAlt) {
      img.src = iconAlt;
      return;
    }
    img.hidden = true;
  };
  img.src = icon || iconAlt || "";
}

function fillModalBody({ kpis = [], rows = [], sections = [], errorFull = "", errorTechnical = "" } = {}) {
  const kpiBox = $("app-modal-kpis");
  if (kpiBox) {
    if (kpis.length) {
      kpiBox.hidden = false;
      kpiBox.innerHTML = kpisHtml(kpis);
    } else {
      kpiBox.hidden = true;
      kpiBox.innerHTML = "";
    }
  }
  const body = $("app-modal-summary");
  if (!body) return;
  let html = "";
  if (errorFull) {
    html += `<div class="modal-error">
      <span class="modal-error-main">${escHtml(errorFull)}</span>
      ${errorTechnical
        ? `<details class="modal-error-tech"><summary>Detalhes técnicos OKX</summary><span class="modal-error-full">${escHtml(errorTechnical)}</span></details>`
        : ""}
    </div>`;
  } else if (sections.length) {
    html += sectionsHtml(sections);
  } else if (rows.length) {
    html += factsHtml(rows);
  }
  body.innerHTML = html;
  body.hidden = !html;
}

function openAppModal({
  title,
  hint,
  icon = "",
  iconAlt = "",
  kpis = [],
  rows = [],
  sections = [],
  errorFull = "",
  errorTechnical = "",
  form = false,
  wide = false,
  rich = false,
  confirmLabel,
  cancelLabel,
  confirmClass = "btn-primary",
  confirmIco = "",
  hideConfirm = false,
  secondaryLabel = "",
  secondaryClass = "btn-ghost",
  secondaryAction = null,
  action,
} = {}) {
  pendingAction = action;
  pendingSecondaryAction = secondaryAction || null;
  modalBusy = false;
  $("app-modal-title").textContent = title || "Confirmar";
  const hintEl = $("app-modal-hint");
  if (hintEl) {
    hintEl.textContent = hint || "";
    hintEl.hidden = !hint;
  }
  setModalIcon(icon, iconAlt);
  fillModalBody({ kpis, rows, sections, errorFull, errorTechnical });
  $("app-modal-form").hidden = !form;
  const card = $("app-modal-card");
  card.classList.toggle("wide", !!form || !!wide || !!rich || !!errorFull);
  card.classList.toggle("rich", !!rich);
  card.classList.toggle("bot-form", !!form);
  $("app-modal-confirm-label").textContent = confirmLabel || "Confirmar";
  $("app-modal-confirm-ico").innerHTML = confirmIco || "";
  $("app-modal-confirm").className = `btn btn-cta ${confirmClass}`;
  $("app-modal-confirm").disabled = false;
  $("app-modal-confirm").hidden = !!hideConfirm;
  const cancelBtn = $("app-modal-cancel");
  if (cancelBtn) cancelBtn.textContent = cancelLabel || "Voltar";
  const secBtn = $("app-modal-secondary");
  if (secBtn) {
    const showSec = !!secondaryLabel;
    secBtn.hidden = !showSec;
    secBtn.disabled = false;
    secBtn.className = `btn ${secondaryClass || "btn-ghost"}`;
    const secLabel = $("app-modal-secondary-label");
    if (secLabel) secLabel.textContent = secondaryLabel || "Ajustar";
    else secBtn.textContent = secondaryLabel || "Ajustar";
  }
  flash("app-modal-msg", "", true);
  $("app-modal").hidden = false;
  if (form) {
    const nameInput = $("app-modal-form").querySelector('input[name="name"]');
    const first = nameInput || $("app-modal-form").querySelector("input:not([type=hidden]):not([type=search])");
    if (first) setTimeout(() => first.focus(), 30);
  } else {
    setBotModalLocked(false);
    closeTokenMenu("bot-token-menu");
  }
}

function closeModal() {
  $("app-modal").hidden = true;
  pendingAction = null;
  pendingSecondaryAction = null;
  modalBusy = false;
  $("app-modal-confirm").disabled = false;
  const cancel = $("app-modal-cancel");
  if (cancel) {
    cancel.onclick = null;
    cancel.textContent = "Voltar";
  }
  const sec = $("app-modal-secondary");
  if (sec) {
    sec.hidden = true;
    sec.disabled = false;
  }
  setModalIcon("", "");
  fillModalBody({});
}

function confirmModalAction() {
  if (modalBusy || !pendingAction) return;
  $("app-modal-confirm").click();
}

$("app-modal-form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  confirmModalAction();
});

$("app-modal-cancel").addEventListener("click", closeModal);
$("app-modal-close")?.addEventListener("click", closeModal);
$("app-modal-secondary")?.addEventListener("click", async () => {
  if (modalBusy || !pendingSecondaryAction) return;
  const action = pendingSecondaryAction;
  if (action.type === "bot-preflight-adjust") {
    const id = action.id;
    closeModal();
    await openEditBotModal(id);
    return;
  }
  if (action.type === "hunter-chart") {
    const inst = action.inst;
    closeModal();
    if (inst) goTokenChart(inst);
    return;
  }
  if (action.type === "bot-preflight-rerun") {
    await openStartBotModal(action.id, { force: true });
  }
});
$("app-modal").addEventListener("click", (ev) => {
  if (ev.target.dataset.close) closeModal();
  const lab = ev.target.closest("[data-preflight-lab]");
  if (lab) {
    const id = lab.getAttribute("data-preflight-lab");
    const days = Number(lab.getAttribute("data-days")) || 7;
    if (id) {
      closeModal();
      openLabForBot(id, days);
    }
    return;
  }
  const rerun = ev.target.closest("[data-preflight-rerun]");
  if (rerun) {
    const id = rerun.getAttribute("data-preflight-rerun");
    if (id) openStartBotModal(id, { force: true });
  }
});

document.addEventListener("click", (ev) => {
  const hit = ev.target.closest("[data-chart-inst]");
  if (!hit) return;
  const control = ev.target.closest("button, a, input, select, textarea, label");
  if (control && control !== hit && !control.hasAttribute("data-chart-inst")) return;
  const inst = hit.getAttribute("data-chart-inst");
  if (!inst) return;
  ev.preventDefault();
  if (!$("app-modal")?.hidden) closeModal();
  goTokenChart(inst);
});

document.addEventListener("keydown", (ev) => {
  if (ev.key !== "Enter" && ev.key !== " ") return;
  const hit = ev.target.closest("[data-chart-inst]");
  if (!hit || hit.tagName === "BUTTON" || hit.tagName === "A") return;
  if (document.activeElement !== hit) return;
  ev.preventDefault();
  goTokenChart(hit.getAttribute("data-chart-inst"));
});

document.addEventListener("keydown", (ev) => {
  if (ev.key !== "Escape") return;
  if ($("token-chart-modal") && !$("token-chart-modal").hidden) {
    closeTokenChartModal();
    return;
  }
  if (!$("app-modal").hidden) {
    closeModal();
    return;
  }
  if (copilotOpen) setCopilotOpen(false);
});

$("app-modal-confirm").addEventListener("click", async () => {
  if (!pendingAction || modalBusy) return;
  modalBusy = true;
  const action = pendingAction;
  pendingAction = null;
  $("app-modal-confirm").disabled = true;
  try {
    if (action.type === "bot-preflight-adjust") {
      const id = action.id;
      closeModal();
      await openEditBotModal(id);
      return;
    }
    if (action.type === "bot-preflight-rerun") {
      await openStartBotModal(action.id, { force: true });
      return;
    }
    if (action.type === "token-trade") {
      closeModal();
      goTradeToken(action.inst, action.icon, action.iconAlt);
      return;
    }
    if (action.type === "hunter-create-bot") {
      closeModal();
      await openHunterBotModal(action.candidate);
      return;
    }
    if (action.type === "hunter-chart") {
      const inst = action.inst;
      closeModal();
      if (inst) goTokenChart(inst);
      return;
    }
    if (action.type === "hunter-order") {
      closeModal();
      goTradeToken(action.inst, action.icon, action.iconAlt);
      return;
    }
    if (action.type === "strat-create-bot") {
      closeModal();
      const s = action.strategy || {};
      await openCreateBotModal({
        strategy_id: s.id,
        name: `Bot ${s.name || s.id}`,
        buy_pct: s.buy_pct,
        profit_target_pct: s.profit_target_pct,
        fee_rate_pct: s.fee_rate_pct,
        inst_id: stratInstId || orderInst(),
        run_days: normalizeBotRunDays(stratDays),
      });
      return;
    }
    if (action.type === "strat-create") {
      const box = $("strat-create-form");
      if (!box) throw new Error("formulário inválido");
      const get = (n) => box.querySelector(`[name="${n}"]`)?.value;
      const payload = {
        name: (get("name") || "").trim(),
        buy_pct: Number(get("buy_pct")),
        profit_target_pct: Number(get("profit_target_pct")),
        fee_rate_pct: Number(get("fee_rate_pct")),
        style: (get("style") || "custom").trim(),
        focus: (get("focus") || "").trim(),
        risk: (get("risk") || "médio").trim(),
        tag: (get("tag") || "custom").trim(),
        best_for: (get("best_for") || "").trim(),
      };
      if (!payload.name) throw new Error("informe o nome");
      const res = await api("/api/strategies", { method: "POST", body: JSON.stringify(payload) });
      stratCatalog = [];
      await ensureBotStrategies();
      renderStratCatalog();
      closeModal();
      flash("strat-msg", `Estratégia criada: ${res.strategy?.name || payload.name}`, true);
      return;
    }
    if (action.type === "bot-create" || action.type === "bot-edit") {
      if (action.locked) throw new Error("pause o bot para editar");
      const form = $("app-modal-form");
      const preset = action.preset || null;
      const name = (form.name.value.trim() || preset?.name || "").trim();
      const inst = (form.inst_id.value.trim() || preset?.inst_id || "").toUpperCase();
      if (!name) throw new Error("informe o nome");
      if (!inst.includes("-")) throw new Error("par inválido, use ex. SOL-USDT");
      const formPayload = readBotFormPayload();
      const payload = preset
        ? {
            ...formPayload,
            name,
            inst_id: String(formPayload.inst_id || preset.inst_id || inst).toUpperCase(),
            // form prevalece; preset só preenche se campo vazio
            buy_pct: formPayload.buy_pct || Number(preset.buy_pct),
            profit_target_pct: formPayload.profit_target_pct || Number(preset.profit_target_pct),
            fee_rate_pct: formPayload.fee_rate_pct ?? Number(preset.fee_rate_pct),
            quote_amount: formPayload.quote_amount,
            entry_mode: formPayload.entry_mode,
            strategy_id: formPayload.strategy_id || preset.strategy_id || null,
          }
        : formPayload;
      if (payload.quote_amount > 0 && payload.entry_mode !== "base") {
        const quote = (payload.inst_id || inst).split("-")[1] || "USDT";
        const limErr = orderLimitErr(payload.quote_amount, quote);
        if (limErr) throw new Error(limErr);
      }
      if (action.type === "bot-create") {
        const bot = await api("/api/bots", { method: "POST", body: JSON.stringify(payload) });
        closeModal();
        if (copilotPlanArmed) {
          copilotPlanArmed = false;
          setTimeout(() => advanceCopilotPlan(), 400);
        }
        flash(action.fromLab || action.fromStrat ? "lab-msg" : "msg", `Bot criado: ${bot.name || payload.name} · ${payload.inst_id}`, true);
        if (action.fromLab || action.fromStrat) {
          flash("msg", `Bot criado com params da simulação (${payload.inst_id})`, true);
          location.hash = "#/bot";
        }
        await refresh();
        openBotPanel(bot.bot_id);
      } else {
        await api(`/api/config?bot_id=${encodeURIComponent(action.id)}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        flash("msg", "Bot atualizado", true);
        closeModal();
        await refresh();
      }
    } else if (action.type === "bot-start" || action.type === "bot-stop") {
      if (toggling) return;
      toggling = true;
      if (action.type === "bot-start") {
        selectedBotId = action.id;
        localStorage.setItem("okx_bot_id", action.id);
      }
      await api(`/api/bots/${action.id}/${action.type === "bot-start" ? "start" : "stop"}`, { method: "POST" });
      closeModal();
      flash("msg", action.type === "bot-start" ? "Bot iniciado (os outros foram pausados)" : "Bot pausado", true);
      await refresh();
      toggling = false;
    } else if (action.type === "bot-tick") {
      if (toggling) return;
      toggling = true;
      selectedBotId = action.id;
      localStorage.setItem("okx_bot_id", action.id);
      try {
        await api(`/api/bots/${encodeURIComponent(action.id)}/tick`, { method: "POST" });
        closeModal();
        flash("msg", "Ciclo manual executado · veja em Execuções", true);
        botDetailVisible = true;
        await refresh({ trades: true });
        openBotPanel(action.id);
      } finally {
        toggling = false;
      }
    } else if (action.type === "bot-delete") {
      await api(`/api/bots/${encodeURIComponent(action.id)}`, { method: "DELETE" });
      if (selectedBotId === action.id) {
        selectedBotId = "";
        localStorage.removeItem("okx_bot_id");
      }
      closeModal();
      flash("msg", "Bot apagado", true);
      await refresh();
    } else if (action.type === "save-keys") {
      const before = new Set((lastKeys?.accounts || []).map((a) => a.account_id));
      let saved;
      if (action.isNew || action.accountId === NEW_ACCT) {
        saved = await api("/api/keys/accounts", { method: "POST", body: JSON.stringify(action.payload) });
      } else {
        saved = await api(`/api/keys/accounts/${encodeURIComponent(action.accountId)}`, {
          method: "PUT",
          body: JSON.stringify(action.payload),
        });
      }
      const created = (saved.accounts || []).find((a) => !before.has(a.account_id));
      if (created) selectedAccountId = created.account_id;
      else if (action.accountId && action.accountId !== NEW_ACCT) selectedAccountId = action.accountId;
      renderKeys(saved, { keepSelection: true });
      closeModal();
      flash("keys-msg", "Conta salva. Sincronizando carteira…", true);
      try { await loadWallet(); } catch (_) {}
      try { await refresh(); } catch (_) {}
      flash("keys-msg", "Conta salva", true);
    } else if (action.type === "activate-account") {
      const saved = await api(`/api/keys/accounts/${encodeURIComponent(action.id)}/activate`, { method: "POST" });
      selectedAccountId = action.id;
      renderKeys(saved);
      closeModal();
      flash("keys-msg", "Conta ativa. Sincronizando carteira…", true);
      try { await loadWallet(); } catch (_) {}
      try { await refresh(); } catch (_) {}
      flash("keys-msg", `Conta ativa: ${saved.account_name || "OKX"}`, true);
    } else if (action.type === "delete-account") {
      const saved = await api(`/api/keys/accounts/${encodeURIComponent(action.id)}`, { method: "DELETE" });
      selectedAccountId = saved.active_account_id || NEW_ACCT;
      renderKeys(saved);
      closeModal();
      flash("keys-msg", "Conta apagada", true);
    } else if (action.type === "cancel-all") {
      const res = await api("/api/orders/cancel-all", { method: "POST" });
      closeModal();
      const canceled = Number(res.canceled || 0);
      const gone = Number(res.already_gone || 0);
      const failed = Number(res.failed || 0);
      let msg;
      if (failed) {
        msg = `${canceled} cancelada(s)`
          + (gone ? `, ${gone} já resolvida(s)` : "")
          + ` · ${failed} falha(s)`;
      } else if (gone && !canceled) {
        msg = gone === 1
          ? "Ordem já executada ou cancelada"
          : `${gone} já executada(s) ou cancelada(s)`;
      } else if (gone) {
        msg = `${canceled} cancelada(s), ${gone} já resolvida(s)`;
      } else {
        msg = `${canceled} cancelada(s)`;
      }
      flash("order-msg", msg, failed === 0);
      clearHistClientCache();
      await loadOrders({ forceHist: true });
    } else if (action.type === "cancel") {
      const res = await api("/api/orders/cancel", {
        method: "POST",
        body: JSON.stringify({ inst_id: action.inst_id, ord_id: action.ord_id }),
      });
      closeModal();
      const gone = !!(res?.already_gone);
      flash(
        "order-msg",
        gone
          ? (res.message || "Ordem já executada ou cancelada")
          : "Ordem cancelada",
        true,
      );
      clearHistClientCache();
      await loadOrders({ forceHist: true });
    } else if (action.type === "order") {
      // Saldo fresco na OKX — se não cobrir, não envia a ordem
      await refreshOrderContext(action.payload.inst_id);
      const p = action.payload;
      if (p.side === "buy") {
        const need = p.tgt_ccy === "quote_ccy"
          ? Number(p.sz)
          : Number(p._quote_val != null ? p._quote_val : (Number(p.sz) * Number(orderContext?.last || p.px || 0)));
        const avail = Number(orderContext?.quote_avail || 0);
        const fund = Number(orderContext?.quote_funding || 0);
        const q = orderContext?.quote || "USDT";
        if (!(avail > 1e-12) || !(need > 0) || need > avail + 1e-8) {
          throw new Error(
            fund > 1e-8
              ? `Saldo trading ${fmt(avail, 4)} ${q} insuficiente (pedido ≈ ${fmt(need, 4)}). Há ${fmt(fund, 4)} ${q} no funding — transfira. Ordem não enviada.`
              : `Saldo trading ${fmt(avail, 4)} ${q} insuficiente para ≈ ${fmt(need, 4)} ${q}. Ordem não enviada.`,
          );
        }
      } else {
        const need = Number(p._qty_base != null ? p._qty_base : p.sz);
        const avail = Number(orderContext?.base_avail || 0);
        const fund = Number(orderContext?.base_funding || 0);
        const b = orderContext?.base || "TOKEN";
        if (!(avail > 1e-12) || !(need > 0) || need > avail + 1e-12) {
          throw new Error(
            fund > 1e-8
              ? `Saldo trading ${fmtQty(avail)} ${b} insuficiente. Há ${fmtQty(fund)} ${b} no funding — transfira. Ordem não enviada.`
              : `Saldo trading ${fmtQty(avail)} ${b} insuficiente. Ordem não enviada.`,
          );
        }
      }
      const { _quote_val, _qty_base, _unit, ...body } = p;
      await api("/api/orders", { method: "POST", body: JSON.stringify(body) });
      closeModal();
      flash("order-msg", action.payload.side === "buy" ? "Ordem de compra enviada" : "Ordem de venda enviada", true);
      if (copilotPlanArmed) {
        copilotPlanArmed = false;
        setTimeout(() => advanceCopilotPlan(), 400);
      }
      $("order-form").sz.value = "";
      clearHistClientCache();
      await loadOrders({ forceHist: true });
      try { await loadWallet(); } catch (_) {}
    }
  } catch (err) {
    const msg = err?.summary || err?.message || "Erro desconhecido";
    if (action?.type === "order" || action?.type === "cancel" || action?.type === "cancel-all") {
      // 51400 etc.: ordem já gone — mensagem amigável + atualiza lista (sem dump JSON)
      const cancelGone = !!(
        err?.cancel_gone
        || ["51400", "51401", "51402"].includes(String(err?.scode || ""))
      );
      if ((action.type === "cancel" || action.type === "cancel-all") && cancelGone) {
        closeModal();
        flash(
          "order-msg",
          err?.friendly || err?.summary || err?.message
            || "Ordem já executada ou cancelada",
          true,
        );
        clearHistClientCache();
        try { await loadOrders({ forceHist: true }); } catch (_) {}
        toggling = false;
        return;
      }
      const titles = {
        order: "Erro ao enviar ordem",
        cancel: "Erro ao cancelar ordem",
        "cancel-all": "Erro ao cancelar ordens",
      };
      showErrorModal(err, { title: titles[action.type] || "Erro", flashId: "order-msg" });
    } else {
      flash("app-modal-msg", msg, false);
    }
    toggling = false;
  } finally {
    modalBusy = false;
    if (!$("app-modal").hidden) $("app-modal-confirm").disabled = false;
  }
});

async function openCreateBotModal(seed = {}) {
  if (!botsOn()) {
    flash("msg", "Bots desativados em Configurações", false);
    return;
  }
  await ensureBotStrategies();
  const plainNew = seed.strategy_id === undefined && seed.buy_pct === undefined;
  const strategyId = seed.strategy_id ?? (plainNew ? "balanced" : "");
  fillBotModalForm({
    name: seed.name || "Novo bot",
    inst_id: seed.inst_id || orderInst() || "BTC-USDT",
    strategy_id: strategyId,
    quote_amount: seed.quote_amount ?? "",
    entry_mode: seed.entry_mode || "quote",
    buy_pct: seed.buy_pct ?? 2,
    profit_target_pct: seed.profit_target_pct ?? 1,
    fee_rate_pct: seed.fee_rate_pct ?? 0.10,
    interval_min: seed.interval_min ?? defaultBotIntervalMin(),
    run_days: normalizeBotRunDays(seed.run_days ?? 7),
    portfolio_interval_min: seed.portfolio_interval_min ?? 2,
    cascade_enabled: seed.cascade_enabled ?? false,
    cascade_buy_pct: seed.cascade_buy_pct ?? 20,
    cascade_sell_pct: seed.cascade_sell_pct ?? 25,
    cascade_buy_pcts: seed.cascade_buy_pcts ?? null,
    cascade_sell_pcts: seed.cascade_sell_pcts ?? null,
    icon: seed.icon,
    icon_alt: seed.icon_alt,
  });
  if (strategyId) applyStrategyToBotForm(strategyId);
  clearBotAnalyzeResults();
  openAppModal({
    title: "Novo bot",
    hint: "1) par · 2) analise/estratégia · 3) entrada · 4) parâmetros. Aporte vazio = saldo disponível.",
    form: true,
    wide: true,
    confirmLabel: "Criar bot",
    confirmClass: "btn-primary",
    confirmIco: ICO.play,
    action: { type: "bot-create" },
  });
  setBotModalLocked(false);
  syncBotCascadeUI();
}

async function openEditBotModal(id) {
  const b = botById(id);
  if (!b) return;
  await ensureBotStrategies();
  fillBotModalForm(b);
  clearBotAnalyzeResults();
  const locked = !!b.running;
  openAppModal({
    title: "Editar bot",
    hint: locked
      ? "Pause o bot para alterar nome, par e parâmetros."
      : "Ajuste par, estratégia ou parâmetros. Analisar compara presets no histórico do token.",
    form: true,
    confirmLabel: "Salvar",
    confirmClass: "btn-primary",
    action: { type: "bot-edit", id, locked },
  });
  setBotModalLocked(locked);
  syncBotCascadeUI();
}

function otherRunningBots(exceptId) {
  return (lastStatus?.bots || []).filter((b) => b.running && b.bot_id !== exceptId);
}

function strategyNameForBot(b) {
  const sid = String(b?.strategy_id || "").trim();
  if (!sid) return "Manual";
  const s = (stratCatalog || []).find((x) => String(x.id) === sid);
  return s?.name || sid;
}

function openBotDetailModal(id) {
  const b = botById(id);
  if (!b) return;
  const quote = quoteFromInst(b.inst_id);
  const entryLabel = (b.entry_mode || "quote") === "base" ? "Token (base)" : `$ / ${quote || "quote"}`;
  const entryVal = b.quote_amount != null && Number(b.quote_amount) > 0
    ? `${fmt(b.quote_amount, 4)} (${entryLabel})`
    : `Saldo disponível (${entryLabel})`;
  const cascadeRows = b.cascade_enabled
    ? [
      ["Cascata", "Ativa"],
      ["Compras", cascadeSummary(b, "buy")],
      ["Vendas", cascadeSummary(b, "sell")],
      ["Etapa compra", b.cascade_buy_step != null ? String(b.cascade_buy_step) : "—"],
      ["Etapa venda", b.cascade_sell_step != null ? String(b.cascade_sell_step) : "—"],
    ]
    : [["Cascata", "Desligada"]];

  openAppModal({
    title: b.name || "Detalhe do bot",
    hint: `${b.inst_id || "—"} · ${b.running ? "ativo" : "parado"} · só um bot ativo por vez`,
    icon: b.icon,
    iconAlt: b.icon_alt,
    rich: true,
    wide: true,
    hideConfirm: true,
    cancelLabel: "Fechar",
    kpis: [
      { label: "Status", value: b.running ? "Ativo" : "Parado", tone: b.running ? "up" : "" },
      { label: "Posição", value: b.state === "long" ? "Long" : "Aguardando" },
      { label: "Estratégia", value: strategyNameForBot(b) },
    ],
    sections: [
      {
        title: "Configuração",
        rows: [
          ["Par", b.inst_id || "—"],
          ["Queda p/ comprar", `${fmt(b.buy_pct, 2)}%`],
          ["Lucro líquido", `${fmt(b.profit_target_pct, 2)}%`],
          ["Entrada", entryVal],
          ["Preço", b.price != null ? fmt(b.price, 6) : "—"],
          ["Referência", b.ref_price != null ? fmt(b.ref_price, 6) : "—"],
          ["Compra se ≤", b.buy_trigger_price != null ? fmt(b.buy_trigger_price, 6) : "—"],
        ],
      },
      {
        title: "Agenda",
        rows: [
          ["Intervalo", fmtIntervalMin(b.interval_min ?? 5)],
          ["Duração", fmtRunDays(b.run_days)],
          ["Restante", fmtRemaining(b.run_remaining_sec) || "—"],
        ],
      },
      {
        title: "Cascata",
        rows: cascadeRows,
      },
      ...(b.state === "long"
        ? [{
          title: "Posição aberta",
          rows: [
            ["Qtd", b.qty != null ? fmt(b.qty, 8) : "—"],
            ["Preço médio", b.entry_price != null ? fmt(b.entry_price, 6) : "—"],
            ["Alvo venda", b.target_price != null ? fmt(b.target_price, 6) : "—"],
            ...(b.realized_pnl != null ? [["Realizado", fmt(b.realized_pnl, 4)]] : []),
          ],
        }]
        : []),
      ...(b.last_error
        ? [{ title: "Último erro", rows: [["Erro", String(b.last_error), "sell"]] }]
        : []),
    ],
    action: null,
  });
}

function preflightChecksHtml(checks) {
  if (!checks?.length) return `<div class="hint">Sem checks.</div>`;
  return `<div class="preflight-list">${checks.map((c) => {
    const tone = !c.ok ? "bad" : c.level === "warn" ? "warn" : "ok";
    const mark = !c.ok ? "✕" : c.level === "warn" ? "!" : "✓";
    const act = c.action;
    let link = "";
    if (act?.type === "open_lab" && act.bot_id) {
      const days = Number(act.days) || 7;
      link = `<button type="button" class="btn btn-ghost preflight-link" data-preflight-lab="${escHtml(act.bot_id)}" data-days="${days}">${escHtml(act.label || "Abrir no Lab")}</button>`;
    }
    return `<div class="preflight-row ${tone}">
      <span class="preflight-mark" aria-hidden="true">${mark}</span>
      <div class="preflight-main">
        <strong>${escHtml(c.label || "—")}</strong>
        <small>${escHtml(c.detail || "")}</small>
        ${link}
      </div>
    </div>`;
  }).join("")}</div>`;
}

function renderBotPreflightModal(res) {
  const b = res.bot || botById(res.bot_id) || {};
  const id = res.bot_id || b.bot_id;
  const can = !!res.can_start;
  const others = otherRunningBots(id);
  const switching = others.length > 0;
  const blockers = res.blockers || [];
  const warnings = res.warnings || [];
  let hint = can
    ? (switching
      ? "Validação ok · ao iniciar, o bot ativo será pausado"
      : "Validação ok · pode iniciar live na OKX")
    : `Bloqueado: ${blockers.join(", ") || "corrija os itens em vermelho"}`;
  if (can && warnings.length) hint += ` · avisos: ${warnings.join(", ")}`;

  openAppModal({
    title: can ? (switching ? "Pronto · trocar bot ativo" : "Pronto para iniciar") : "Ajuste necessário",
    hint,
    icon: b.icon,
    iconAlt: b.icon_alt,
    rich: true,
    wide: true,
    kpis: [
      { label: "Par", value: b.inst_id || "—" },
      { label: "Status", value: can ? "Pode iniciar" : "Bloqueado", tone: can ? "up" : "down" },
      {
        label: "Avisos",
        value: String(warnings.length || 0),
        tone: warnings.length ? "down" : "",
      },
    ],
    sections: [
      {
        title: "Checklist pré-voo",
        html: preflightChecksHtml(res.checks),
      },
      {
        title: "Ações",
        html: `<div class="preflight-actions">
          <button type="button" class="btn btn-ghost" data-preflight-lab="${escHtml(id)}" data-days="${Number(res.sim?.days) || 7}">Analisar no Lab</button>
          <button type="button" class="btn btn-ghost" data-preflight-rerun="${escHtml(id)}">Validar de novo</button>
        </div>`,
      },
    ],
    confirmLabel: can
      ? (switching ? "Pausar o outro e iniciar" : "Iniciar live")
      : "Ajustar bot",
    confirmClass: can ? (switching ? "btn-sell" : "btn-buy") : "btn-primary",
    confirmIco: can ? ICO.play : "",
    secondaryLabel: can ? "Ajustar" : "Validar de novo",
    secondaryClass: "btn-ghost",
    secondaryAction: can
      ? { type: "bot-preflight-adjust", id }
      : { type: "bot-preflight-rerun", id },
    action: can
      ? { type: "bot-start", id }
      : { type: "bot-preflight-adjust", id },
  });
}

async function openStartBotModal(id, opts = {}) {
  const b = botById(id);
  if (!b) return;
  selectedBotId = id;
  localStorage.setItem("okx_bot_id", id);

  openAppModal({
    title: "Validando bot…",
    hint: "Par, posição e avisos — saldo de compra só bloqueia na hora da ordem",
    icon: b.icon,
    iconAlt: b.icon_alt,
    rich: true,
    wide: true,
    hideConfirm: true,
    cancelLabel: "Cancelar",
    rows: [
      ["Bot", b.name || id],
      ["Par", b.inst_id || "—"],
      ["Status", "Rodando checklist…"],
    ],
    action: null,
  });

  try {
    const q = opts.backtest === false ? "backtest=0" : "backtest=1";
    const res = await api(`/api/bots/${encodeURIComponent(id)}/preflight?${q}`, { method: "POST" });
    renderBotPreflightModal(res);
  } catch (err) {
    openAppModal({
      title: "Falha na validação",
      hint: err?.summary || err?.message || "Erro ao validar",
      icon: b.icon,
      iconAlt: b.icon_alt,
      rich: true,
      confirmLabel: "Tentar de novo",
      confirmClass: "btn-primary",
      secondaryLabel: "Ajustar bot",
      secondaryAction: { type: "bot-preflight-adjust", id },
      action: { type: "bot-preflight-rerun", id },
      rows: [
        ["Bot", b.name || id],
        ["Par", b.inst_id || "—"],
        ["Erro", err?.summary || err?.message || "—", "sell"],
      ],
    });
  }
}

function openStopBotModal(id) {
  const b = botById(id);
  if (!b) return;
  openAppModal({
    title: "Pausar bot",
    hint: "O bot para de comprar/vender sozinho. Ordens abertas na OKX não são canceladas.",
    rows: [
      ["Bot", b.name || id],
      ["Par", b.inst_id || "—"],
      ["Estado", b.state === "long" ? "Long" : "Aguardando"],
      ["PnL token", botPnlText(b).text],
    ],
    confirmLabel: "Pausar",
    confirmClass: "btn-sell",
    confirmIco: ICO.pause,
    action: { type: "bot-stop", id },
  });
}

function openTickBotModal(id) {
  const b = botById(id);
  if (!b) return;
  openAppModal({
    title: "Executar ciclo agora",
    hint: "Roda uma checagem imediata com as regras atuais. Se compra/venda fechar, envia ordem real. O log fica marcado como manual.",
    rows: [
      ["Bot", b.name || id],
      ["Par", b.inst_id || "—"],
      ["Status", b.running ? "Ativo (intervalo) · este ciclo é extra" : "Parado · só este ciclo"],
      ["Estado", b.state === "long" ? "Long (pode vender)" : "Aguardando (pode comprar)"],
    ],
    confirmLabel: "Executar agora",
    confirmClass: "btn-primary",
    confirmIco: ICO.play,
    action: { type: "bot-tick", id },
  });
}

function openDeleteBotModal(id) {
  const b = botById(id);
  if (!b) return;
  if (b.running) {
    flash("msg", "Pause o bot antes de apagar", false);
    return;
  }
  openAppModal({
    title: "Apagar bot",
    hint: "Remove o bot e o histórico de execuções dele. Não cancela ordens na OKX.",
    rows: [
      ["Bot", b.name || id],
      ["Par", b.inst_id || "—"],
      ["Estado", b.state === "long" ? "Long" : "Aguardando"],
    ],
    confirmLabel: "Apagar",
    confirmClass: "btn-sell",
    confirmIco: ICO.x,
    action: { type: "bot-delete", id },
  });
}

function sellAvgInQuote(quote) {
  const q = String(quote || orderContext?.quote || "").toUpperCase();
  const avgQuote = Number(orderContext?.token_avg_quote);
  if (Number.isFinite(avgQuote) && avgQuote > 0) return avgQuote;
  const avgRaw = Number(orderContext?.token_avg);
  if (!(Number.isFinite(avgRaw) && avgRaw > 0)) return null;
  // OKX accAvgPx costuma ser USDT — só use raw se a quote for estável USD
  if (["USDT", "USD", "USDC"].includes(q)) return avgRaw;
  return null;
}

async function refreshOrderContext(inst) {
  const id = (inst || orderInst() || "").toUpperCase();
  if (!id) throw new Error("Par inválido");
  return loadOrderContextForInst(id, { preserveFields: true, silent: true });
}

function openOrderModal(payload) {
  const unit = payload._unit || orderSizeUnit();
  const quote = orderContext?.quote || unit.ccy;
  const base = orderContext?.base || (orderInst().split("-")[0] || "TOKEN");
  const px = payload.ord_type === "market" ? Number(orderContext?.last || 0) : Number(payload.px || 0);
  const total = payload._quote_val != null ? Number(payload._quote_val) : (px ? payload.sz * px : null);
  const qtyBase = payload._qty_base != null ? Number(payload._qty_base) : payload.sz;
  const fee = total != null ? total * 0.001 : null;
  const availQuote = Number(orderContext?.quote_avail || 0);
  const availBase = Number(orderContext?.base_avail || 0);
  // Conversão alternativa (par BRL → mostra USD, par USDT → mostra BRL)
  const altTotal = total != null ? toAltCcy(total, quote) : null;
  const altFee = fee != null ? toAltCcy(fee, quote) : null;
  const totalAltTxt = altTotal ? `\n≈ ${altTotal.symbol} ${fmt(altTotal.value, 2)}` : "";
  const feeAltTxt = altFee ? ` · ${altFee.symbol} ${fmt(altFee.value, 2)}` : "";
  const rows = [
    ["Lado", payload.side === "buy" ? "Compra" : "Venda", payload.side],
    ["Par", payload.inst_id],
    ["Tipo", TYPE_LABEL[payload.ord_type] || payload.ord_type],
    ["Valor", total != null ? `${fmt(total, 2)} ${quote}${totalAltTxt}` : "—"],
    ["Quantidade", `${fmt(qtyBase, 8)} ${base}`],
    ["Preço", payload.ord_type === "market" ? `Mercado ≈ ${fmt(px, 6)}` : fmt(payload.px, 6)],
    ["Taxa est.", fee != null ? `≈ ${fmt(fee, 4)} ${quote}${feeAltTxt} (0,10%)` : "—"],
    payload.side === "buy"
      ? ["Saldo trading", `${fmt(availQuote, 4)} ${quote}`, availQuote + 1e-8 >= (total || 0) ? "buy" : "sell"]
      : ["Saldo trading", `${fmtQty(availBase)} ${base}`, availBase + 1e-12 >= (qtyBase || 0) ? "buy" : "sell"],
  ];
  if (payload.side === "sell" && total != null && qtyBase) {
    const avg = sellAvgInQuote(quote);
    if (avg > 0) {
      const cost = avg * qtyBase;
      const pnl = total - (fee || 0) - cost;
      const pnlPct = cost ? (pnl / cost) * 100 : null;
      const pnlAlt = toAltCcy(pnl, quote);
      const pnlAltTxt = pnlAlt ? `\n≈ ${pnlAlt.symbol} ${fmt(pnlAlt.value, 2)}` : "";
      rows.push(["Custo méd.", `${fmt(avg, 4)} ${quote}`]);
      rows.push([
        "PnL est.",
        `${fmt(pnl, 2)} ${quote} (${pnlPct != null ? `${fmt(pnlPct, 2)}%` : "—"})${pnlAltTxt}`,
        pnl > 0 ? "buy" : pnl < 0 ? "sell" : "",
      ]);
    } else {
      rows.push(["PnL est.", "— (sem custo médio na quote do par)"]);
    }
  }
  openAppModal({
    title: payload.side === "buy" ? "Confirmar compra" : "Confirmar venda",
    hint: "Ordem live na OKX. Saldo é revalidado ao confirmar — sem saldo, a ordem não é enviada.",
    rows,
    confirmLabel: payload.side === "buy" ? "Confirmar compra" : "Confirmar venda",
    confirmClass: payload.side === "buy" ? "btn-buy" : "btn-sell",
    confirmIco: ICO.swap,
    action: { type: "order", payload },
  });
}

function openCancelModal(order) {
  const side = order.side === "sell" ? "sell" : "buy";
  const quote = order.quote || orderQuoteCcy(order);
  const val = order.value != null && order.value !== "" ? Number(order.value) : null;
  const pnl = order.pnl != null && order.pnl !== "" ? Number(order.pnl) : null;
  openAppModal({
    title: "Cancelar ordem",
    hint: "A ordem será cancelada na OKX.",
    rows: [
      ["Ação", "Cancelar", "sell"],
      ["Par", order.inst_id || "—"],
      ["Lado", side === "buy" ? "Compra" : "Venda", side],
      ["Tipo", TYPE_LABEL[order.ord_type] || order.ord_type || "—"],
      ["Quantidade", fmt(Number(order.sz), 8)],
      ["Realizado", order.pct !== "" && order.pct != null
        ? `${order.side === "sell" ? "Vendeu" : "Comprou"} ${Math.round(Number(order.pct))}%${order.fill ? ` · ${fmt(Number(order.fill), 6)}` : ""}`
        : "—"],
      ["Preço", fmt(Number(order.px), 6)],
      ["Valor", val != null && !Number.isNaN(val) ? `${fmt(val, 2)} ${quote}` : "—"],
      ["PnL est.", pnl != null && !Number.isNaN(pnl) ? `${fmtPnl(pnl)} ${quote}` : "—", pnl > 0 ? "buy" : pnl < 0 ? "sell" : ""],
      ["ID", order.ord_id || "—"],
    ],
    confirmLabel: "Cancelar ordem",
    confirmClass: "btn-sell",
    confirmIco: ICO.x,
    action: { type: "cancel", inst_id: order.inst_id, ord_id: order.ord_id },
  });
}

function openCancelAllModal() {
  const n = lastOpenOrders.length;
  const pairs = [...new Set(lastOpenOrders.map((o) => String(o.inst_id || "").toUpperCase()).filter(Boolean))];
  const pnlMap = sumByQuote(lastOpenOrders, "pnl");
  const pnlTotal = Object.values(pnlMap).reduce((acc, v) => acc + v, 0);
  openAppModal({
    title: "Cancelar todas",
    hint: "Todas as ordens abertas da conta serão canceladas na OKX.",
    rows: [
      ["Ação", "Cancelar todas", "sell"],
      ["Abertas", String(n)],
      ["Pares", pairs.length ? pairs.join(", ") : "—"],
      ["Valor", formatQuoteSums(sumByQuote(lastOpenOrders, "value"))],
      ["PnL est.", formatQuoteSums(pnlMap), pnlTotal > 0 ? "buy" : pnlTotal < 0 ? "sell" : ""],
    ],
    confirmLabel: n > 1 ? `Cancelar ${n} ordens` : "Cancelar todas",
    confirmClass: "btn-sell",
    confirmIco: ICO.x,
    action: { type: "cancel-all" },
  });
}

$("order-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  try {
    assertOrderReady();
    await refreshOrderContext(orderInst());
    assertOrderReady();
    openOrderModal(buildOrderPayload());
  } catch (err) {
    flash("order-msg", err?.summary || err.message, false);
    if (err instanceof ApiError || err?.full) {
      showErrorModal(err, { title: "Erro ao preparar ordem", flashId: null });
    }
  }
});

$("orders-open").addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-cancel]");
  if (btn) {
    openCancelModal({
      ord_id: btn.dataset.cancel,
      inst_id: btn.dataset.inst,
      side: btn.dataset.side,
      ord_type: btn.dataset.type,
      sz: btn.dataset.sz,
      px: btn.dataset.px,
      value: btn.dataset.value,
      pnl: btn.dataset.pnl,
      quote: btn.dataset.quote,
      fill: btn.dataset.fill,
      pct: btn.dataset.pct,
    });
    return;
  }
  // Click na linha para ver detalhes
  const row = ev.target.closest("tr.order-row[data-ord-id]");
  if (row && row.dataset.ordId) openOrderDetail(row.dataset.ordId, row.dataset.inst);
});

// Histórico: click na linha para detalhes
document.addEventListener("click", (ev) => {
  if (!ev.target.closest("#orders-history")) return;
  const row = ev.target.closest("tr.order-row[data-ord-id]");
  if (row && row.dataset.ordId) openOrderDetail(row.dataset.ordId, row.dataset.inst);
});

async function openOrderDetail(ordId, instId) {
  if (!ordId) return;
  try {
    const qs = instId ? `?instId=${encodeURIComponent(instId)}` : "";
    const res = await api(`/api/orders/${encodeURIComponent(ordId)}${qs}`);
    const o = res.order || {};
    const side = o.side === "buy" ? "Compra" : "Venda";
    const quote = o.quote || (o.inst_id || "").split("-")[1] || "USDT";
    const base = (o.inst_id || "").split("-")[0] || "TOKEN";
    const state = ORDER_STATE[o.state] || o.state || "—";
    const rows = [
      ["ID", o.ord_id || ordId],
      ["Par", o.inst_id || "—"],
      ["Lado", side, o.side],
      ["Tipo", TYPE_LABEL[o.ord_type] || o.ord_type || "—"],
      ["Status", state],
      ["Tamanho", `${fmt(o.sz, 8)} ${o.tgt_ccy === "quote_ccy" ? quote : base}`],
      ["Preço", o.ord_type === "market" ? "Mercado" : fmt(o.px, 6)],
      ["Preço médio", o.avg_px ? fmt(o.avg_px, 6) : "—"],
      ["Executado", o.fill_sz ? `${fmt(o.fill_sz, 8)} ${base}` : "—"],
      ["Valor", o.value != null ? `${fmt(o.value, 2)} ${quote}` : "—"],
      ["Taxa", o.fee != null ? `${fmt(Math.abs(Number(o.fee)), 6)} ${o.fee_ccy || quote}` : "—"],
      ["Criada", o.created_at || "—"],
      ["Atualizada", o.updated_at || "—"],
    ];
    if (o.pnl != null && o.pnl !== "") {
      const pnl = Number(o.pnl);
      rows.push(["PnL", `${fmt(pnl, 4)} ${quote}`, pnl > 0 ? "buy" : pnl < 0 ? "sell" : ""]);
    }
    if (o.origin_label) rows.push(["Origem", o.origin_label]);
    openAppModal({
      title: "Detalhe da ordem",
      hint: res.cached ? "Dados em cache" : "Dados atualizados da OKX",
      rows,
      hideConfirm: true,
      cancelLabel: "Fechar",
    });
  } catch (err) {
    flash("order-msg", err?.message || "Erro ao buscar detalhes", false);
  }
}

$("btn-cancel-all").addEventListener("click", () => {
  if (!lastOpenOrders.length) {
    flash("order-msg", "Nenhuma ordem aberta", false);
    return;
  }
  openCancelAllModal();
});

syncOrderForm();

/* ——— Caçador (radar Spot · sem automação) ——— */
let lastHunter = null;
let lastHunterScan = null;

const HUNTER_HORIZONS = {
  daily: { label: "Diário (scalp)", short: "Dia" },
  weekly: { label: "Semanal", short: "Semana" },
  monthly: { label: "Mensal (swing)", short: "Mês" },
};

function applyHunterSettingsToForm(s) {
  if (!s) return;
  if ($("hunter-min-drop")) $("hunter-min-drop").value = s.min_drop_pct ?? 1.5;
  if ($("hunter-max-drop")) $("hunter-max-drop").value = s.max_drop_pct ?? 35;
  if ($("hunter-min-vol")) $("hunter-min-vol").value = s.min_vol_usd ?? 80000;
  if ($("hunter-max-spread")) $("hunter-max-spread").value = s.max_spread_pct ?? 1;
  if ($("hunter-tradeable")) $("hunter-tradeable").checked = s.require_tradeable !== false;
}

function hunterSettingsFromForm() {
  return {
    quote_amount: 0,
    budget_ccy: "BRL",
    horizon: "all",
    min_drop_pct: Number($("hunter-min-drop")?.value || 1.5),
    max_drop_pct: Number($("hunter-max-drop")?.value || 35),
    min_vol_usd: Number($("hunter-min-vol")?.value || 80000),
    max_spread_pct: Number($("hunter-max-spread")?.value || 1),
    require_tradeable: !!$("hunter-tradeable")?.checked,
    validate_days: 90,
    top_n: 30,
  };
}

function renderHunterStatus(data) {
  const el = $("hunter-status");
  if (!el) return;
  const scan = data?.last_scan || lastHunterScan;
  const n = scan?.candidates?.length || 0;
  let title = "Pronto";
  let step = "Clique em Analisar agora — avalia dia, semana e mês em cada token.";
  let tone = "off";
  if (n) {
    title = `${n} oportunidade(s)`;
    step = "Cada token traz o horizonte mais propício (Dia / Semana / Mês) e a estratégia sugerida.";
    tone = "on";
  }
  if (data?.last_error) {
    tone = "wait";
    step = String(data.last_error);
  }
  el.className = `hunter-status ${tone}`;
  el.innerHTML = `<div class="hs-title">${escHtml(title)}</div>
    <div class="hs-step">${escHtml(step)}</div>
    <div class="hs-meta">Modo radar (sem automação)</div>`;

  const modePill = $("hunter-mode-pill");
  if (modePill) {
    modePill.textContent = "Radar";
    modePill.className = "pill off";
  }
}

function openCreateBotFromHunter(c) {
  return openHunterBotModal(c);
}

/** Modal único: análise (previsão/checks) + formulário de criar bot. */
async function openHunterBotModal(c) {
  if (!c) return;
  await ensureBotStrategies();
  const bs = c.best_strategy || {};
  const inst = String(c.inst_id || "").toUpperCase();
  const base = c.base || inst.split("-")[0] || "Token";
  const pred = c.prediction || {};
  const hzMeta = hunterHorizonPlain(c.best_horizon || pred.horizon);
  const checks = c.checks || [];
  const vOk = c.validation_score != null ? c.validation_score : checks.filter((x) => x.ok).length;
  const vTot = c.validation_total != null ? c.validation_total : checks.length;
  const aporte = bs.aporte != null
    ? bs.aporte
    : (Number(lastHunterScan?.order_usd) || "");
  const canCreate = !!bs.id;

  fillBotModalForm({
    name: `Bot ${base} · ${bs.name || "Spot"}`,
    inst_id: inst,
    strategy_id: bs.id || "",
    quote_amount: aporte,
    entry_mode: "quote",
    buy_pct: bs.buy_pct ?? 2,
    profit_target_pct: c.suggested_target_pct ?? bs.profit_target_pct ?? 1,
    fee_rate_pct: bs.fee_rate_pct ?? 0.10,
    interval_min: defaultBotIntervalMin(),
    run_days: normalizeBotRunDays(bs.days || 30),
    portfolio_interval_min: 2,
    cascade_enabled: false,
    icon: c.icon,
    icon_alt: c.icon_alt,
  });
  if (bs.id) applyStrategyToBotForm(bs.id);
  clearBotAnalyzeResults();

  const checksHtml = checks.length
    ? `<ul class="lab-checks">${checks.map((ch) => {
        const cls = ch.ok ? "ok" : "fail";
        return `<li class="${cls}"><span class="mark">${ch.ok ? "✓" : "✗"}</span><span><strong>${escHtml(ch.label || "")}</strong><small>${escHtml(ch.detail || "")}</small></span></li>`;
      }).join("")}</ul>`
    : `<p class="hint">Sem checklist neste scan — rode Analisar agora de novo se precisar.</p>`;

  const stratBit = bs.id
    ? `<div class="hunter-pred-strat">
        <strong>Estratégia sugerida:</strong> ${escHtml(bs.name || bs.id)}
        · compra se cair ${escHtml(fmt(bs.buy_pct, 1))}%
        · vende no lucro ${escHtml(fmt(bs.profit_target_pct, 1))}%
        · retorno hist. ${bs.capital_return_pct != null ? escHtml(fmt(bs.capital_return_pct, 1)) + "%" : "—"}
        · ${bs.recommend_create ? "qualidade ok" : "qualidade frágil — revise os campos abaixo"}
      </div>`
    : `<p class="hint">Sem estratégia automática — ajuste queda/alvo no formulário abaixo.</p>`;

  const tgt = hunterSuggestedTarget(c);
  const kpis = [
    { label: "Queda 24h", value: c.drop_pct != null ? fmtPct(-Math.abs(c.drop_pct)) : "—", tone: "sell" },
    {
      label: "Alvo sugerido",
      value: tgt ? `${fmtPx(tgt.px)}  (+${fmt(tgt.pct, 1)}%)` : "—",
      tone: tgt ? "buy" : undefined,
    },
    {
      label: "Encaixe",
      value: pred.sell_fitness != null ? `${fmt(pred.sell_fitness, 0)}/100` : "—",
      tone: Number(pred.sell_fitness) >= 62 ? "buy" : Number(pred.sell_fitness) < 45 ? "sell" : undefined,
    },
    { label: "Estilo", value: hzMeta.short },
    {
      label: "Recuperação",
      value: pred.bounce_prob_pct != null ? `${fmt(pred.bounce_prob_pct, 0)}%` : "—",
    },
    { label: "Liquidez", value: String(c.liquidity || "—") },
    { label: "Checks", value: vTot ? `${vOk}/${vTot}` : "—", tone: vOk >= Math.max(1, vTot - 2) ? "buy" : "sell" },
  ];

  openAppModal({
    title: canCreate ? `Criar bot · ${base}` : `Análise · ${base}`,
    hint: `${inst} · ${hzMeta.short} · confira a análise e ajuste o formulário se quiser`,
    icon: c.icon || "",
    iconAlt: c.icon_alt || "",
    kpis,
    sections: [
      { title: "O que isso significa", html: hunterPredictionHtml(c) + stratBit },
      { title: "Checklist", html: checksHtml },
    ],
    form: true,
    rich: true,
    wide: true,
    confirmLabel: botsOn() && canCreate ? "Criar bot" : "Fechar",
    confirmClass: botsOn() && canCreate ? "btn-primary" : "btn-ghost",
    confirmIco: botsOn() && canCreate ? ICO.play : "",
    cancelLabel: botsOn() && canCreate ? "Fechar" : "",
    secondaryLabel: "Só gráfico",
    secondaryClass: "btn-ghost",
    secondaryAction: { type: "hunter-chart", inst },
    action: botsOn() && canCreate ? { type: "bot-create" } : null,
  });
  setBotModalLocked(false);
  syncBotCascadeUI();
}

function hunterFitnessTone(fit, label) {
  const f = Number(fit);
  const lab = String(label || "").toLowerCase();
  if (lab === "alta" || f >= 62) return "ok";
  if (lab === "média" || f >= 45) return "mid";
  return "low";
}

function hunterFitnessPlain(fit, label) {
  const lab = String(label || "").toLowerCase();
  if (lab === "alta" || Number(fit) >= 62) {
    return "Boa combinação de liquidez + histórico de vendas neste estilo.";
  }
  if (lab === "média" || Number(fit) >= 45) {
    return "Aceitável, mas não é o ideal — confira estratégia e risco.";
  }
  return "Fraca evidência de vendas boas — melhor revisar ou pular.";
}

/** Alvo de venda sugerido (preço) se comprar agora no last. */
function hunterSuggestedTarget(c) {
  const last = Number(c?.suggested_entry_px ?? c?.last);
  const bs = c?.best_strategy || {};
  let pct = Number(c?.suggested_target_pct ?? bs.profit_target_pct);
  let px = Number(c?.suggested_target_px);
  const fee = Number(bs.fee_rate_pct ?? 0.1);
  const spr = Number(c?.spread_pct || 0);
  if ((!Number.isFinite(px) || px <= 0) && Number.isFinite(last) && last > 0) {
    if (!Number.isFinite(pct) || pct <= 0) pct = 3;
    const gross = pct + fee * 2 + spr;
    px = last * (1 + gross / 100);
  }
  if (!Number.isFinite(px) || px <= 0) return null;
  if (!Number.isFinite(pct) || pct <= 0) {
    pct = Number.isFinite(last) && last > 0 ? ((px / last) - 1) * 100 : null;
  }
  const gross = Number(c?.suggested_target_gross_pct);
  return {
    px,
    pct,
    last: Number.isFinite(last) && last > 0 ? last : null,
    gross: Number.isFinite(gross) ? gross : pct,
    cost: Number(c?.suggested_cost_pct),
    source: c?.suggested_target_source || null,
    sourceLabel: c?.suggested_target_source_label || null,
    atrPct: Number(c?.suggested_atr_pct),
    bouncePct: Number(c?.suggested_bounce_median_pct),
    presetPct: Number(c?.suggested_preset_pct),
  };
}

function hunterHorizonPlain(id) {
  const map = {
    daily: {
      short: "No dia",
      blurb: "Estilo rápido (scalp): compra a queda e tenta vender no mesmo dia.",
    },
    weekly: {
      short: "Na semana",
      blurb: "Estilo médio: espera alguns dias para completar o ciclo compra→venda.",
    },
    monthly: {
      short: "No mês",
      blurb: "Estilo lento: menos operações, ciclos mais longos.",
    },
  };
  return map[String(id || "").toLowerCase()] || { short: "—", blurb: "" };
}

/** Traduz ciclos/dia em linguagem humana. */
function hunterPacePlain(cpd) {
  const n = Number(cpd);
  if (!Number.isFinite(n) || n <= 0) return "Quase nenhum ciclo no histórico analisado.";
  if (n >= 1.5) return `Ritmo alto: cerca de ${fmt(n, 1)} venda(s) por dia no passado.`;
  if (n >= 0.7) return `Ritmo bom: cerca de ${fmt(n, 1)} venda por dia no passado.`;
  if (n >= 0.25) {
    const week = n * 7;
    return `Ritmo médio: cerca de ${fmt(week, 1)} venda(s) por semana no passado.`;
  }
  const month = n * 30;
  return `Ritmo baixo: cerca de ${fmt(month, 1)} venda(s) por mês no passado.`;
}

function hunterBouncePlain(pct) {
  const n = Number(pct);
  if (!Number.isFinite(n)) return null;
  if (n >= 70) return `Recuperação favorável (~${fmt(n, 0)}%): o modelo heurístico vê boa chance de o preço reagir após a queda.`;
  if (n >= 50) return `Recuperação mista (~${fmt(n, 0)}%): pode subir, mas sem certeza.`;
  return `Recuperação fraca (~${fmt(n, 0)}%): risco maior de a queda continuar.`;
}

function hunterNearLowPlain(feat) {
  const pct = feat?.near_low_pct;
  if (pct == null || !Number.isFinite(Number(pct))) return null;
  const n = Number(pct);
  if (n <= 1.5) return `Preço bem perto da mínima recente (${fmt(n, 1)}% acima) — típico de “fundo” curto.`;
  if (n <= 4) return `Ainda próximo da mínima (${fmt(n, 1)}% acima).`;
  return `Já afastado da mínima (${fmt(n, 1)}% acima) — menos “desconto” imediato.`;
}

function hunterHorizonCompareHtml(c) {
  const best = c.best_horizon || c.prediction?.horizon;
  const order = ["daily", "weekly", "monthly"];
  const cards = order.map((id) => {
    const h = c.horizons?.[id];
    if (!h || h.sell_fitness == null) return "";
    const meta = hunterHorizonPlain(id);
    const isBest = id === best;
    const tone = hunterFitnessTone(h.sell_fitness, h.fitness_label);
    const pace = hunterPacePlain(h.cycles_per_day);
    return `<div class="hunter-hz-card ${isBest ? "best" : ""} tone-${tone}">
      <div class="hunter-hz-card-h">
        <strong>${escHtml(meta.short)}</strong>
        ${isBest ? `<span class="hunter-hz-best">recomendado</span>` : ""}
      </div>
      <p class="hunter-hz-score">Nota ${escHtml(fmt(h.sell_fitness, 0))}/100 · ${escHtml(h.fitness_label || "—")}</p>
      <p class="hunter-hz-pace">${escHtml(pace)}</p>
    </div>`;
  }).filter(Boolean);
  if (!cards.length) return `<p class="hint">Sem comparação de horizontes neste scan.</p>`;
  return `<div class="hunter-hz-grid">${cards.join("")}</div>`;
}

function hunterPredictionHtml(c) {
  const pred = c.prediction || {};
  const feat = c.candle_features || pred.features || {};
  const hzId = c.best_horizon || pred.horizon;
  const hz = hunterHorizonPlain(hzId);
  const fit = pred.sell_fitness;
  const fitLab = pred.fitness_label;
  const tone = hunterFitnessTone(fit, fitLab);
  const bounce = hunterBouncePlain(pred.bounce_prob_pct ?? c.prob_up_pct);
  const near = hunterNearLowPlain(feat);
  const bounceHist = feat.bounce_rate != null
    ? `Em dips parecidos no gráfico, subiu de novo em ~${fmt(feat.bounce_rate * 100, 0)}% dos casos (${feat.bounce_sample || 0} amostras).`
    : null;

  const reasons = (pred.reasons || []).slice(0, 3).filter(Boolean);
  const reasonBits = reasons.length
    ? `<ul class="hunter-pred-why">${reasons.map((r) => `<li>${escHtml(r)}</li>`).join("")}</ul>`
    : "";

  const tgt = hunterSuggestedTarget(c);
  const tgtHtml = tgt
    ? `<p class="hunter-pred-target">Se comprar agora perto de <strong>${escHtml(fmtPx(tgt.last))}</strong>, o <strong>alvo sugerido de venda</strong> é <strong>${escHtml(fmtPx(tgt.px))}</strong> (+${escHtml(fmt(tgt.pct, 1))}% líquido${Number.isFinite(tgt.cost) && tgt.cost > 0 ? ` · ~${escHtml(fmt(tgt.gross, 1))}% bruto p/ cobrir taxa/spread` : ""})${tgt.sourceLabel ? ` · ${escHtml(tgt.sourceLabel)}` : ""}. Usa o maior entre estratégia, bounce (p60) e 40% da queda 24h; ATR só como teto — não é ordem automática.</p>`
    : "";

  return `<div class="hunter-pred">
    <p class="hunter-pred-verdict tone-${tone}">
      <strong>Em resumo:</strong>
      ${escHtml(hz.short)} parece o melhor encaixe agora.
      ${escHtml(hunterFitnessPlain(fit, fitLab))}
    </p>
    ${tgtHtml}
    <p class="hunter-pred-blurb">${escHtml(hz.blurb)}</p>
    <div class="hunter-pred-points">
      ${bounce ? `<p>${escHtml(bounce)}</p>` : ""}
      <p>${escHtml(hunterPacePlain(pred.cycles_per_day))}</p>
      ${near ? `<p>${escHtml(near)}</p>` : ""}
      ${bounceHist ? `<p>${escHtml(bounceHist)}</p>` : ""}
    </div>
    ${reasonBits}
    <div class="hunter-pred-compare">
      <div class="modal-section-title">Comparar estilos</div>
      ${hunterHorizonCompareHtml(c)}
    </div>
    <p class="hunter-pred-disclaimer">Isto é uma estimativa com base no Spot + candles + backtest — <strong>não garante lucro</strong>.</p>
  </div>`;
}

function openHunterDetail(c) {
  return openHunterBotModal(c);
}

const HUNTER_LIQ_TIP = {
  A: "Liquidez A — ótima: volume alto, spread apertado e livro profundo",
  B: "Liquidez B — boa: dá para operar com custo razoável",
  C: "Liquidez C — aceitável: liquidez mediana; cuidado com o tamanho da ordem",
  D: "Liquidez D — fraca: spread largo ou volume/livro baixos; risco de slippage",
};

/** Mesma escala A–D do Caçador (vol 24h + spread; sem livro na lista). */
function tokenLiquidityGrade(vol, spreadPct) {
  let points = 0;
  const v = Number(vol) || 0;
  if (v >= 20_000_000) points += 3;
  else if (v >= 5_000_000) points += 2;
  else if (v >= 1_000_000) points += 1;
  if (spreadPct != null && Number.isFinite(Number(spreadPct))) {
    const s = Number(spreadPct);
    if (s <= 0.08) points += 3;
    else if (s <= 0.25) points += 2;
    else if (s <= 0.6) points += 1;
  }
  if (points >= 7) return "A";
  if (points >= 5) return "B";
  if (points >= 3) return "C";
  return "D";
}

function tokenLiqRank(grade) {
  return { A: 4, B: 3, C: 2, D: 1 }[String(grade || "D").toUpperCase()] || 0;
}

function enrichTokenLiquidity(p) {
  const liq = p.liquidity || tokenLiquidityGrade(p.vol, p.spread_pct);
  return {
    ...p,
    liquidity: liq,
    liq_rank: tokenLiqRank(liq),
  };
}

function hunterLiqTip(c) {
  if (c?.liquidity_tip) return String(c.liquidity_tip);
  const liq = String(c?.liquidity || "D").toUpperCase();
  const bits = [HUNTER_LIQ_TIP[liq] || HUNTER_LIQ_TIP.D];
  if (c?.vol != null) bits.push(`vol 24h ≈ $${fmt(c.vol, 0)}`);
  if (c?.spread_pct != null) bits.push(`spread ${fmt(c.spread_pct, 2)}%`);
  if (c?.book_usd != null) bits.push(`livro ≈ $${fmt(c.book_usd, 0)}`);
  return bits.join(" · ");
}

function renderHunterCandidates(scan) {
  const body = $("hunter-body");
  const meta = $("hunter-scan-meta");
  if (!body) return;
  lastHunterScan = scan;
  const list = scan?.candidates || [];
  const funnel = scan?.funnel || {};
  if (meta) {
    const when = scan?.scanned_at ? String(scan.scanned_at).replace("T", " ").replace("+00:00", "") : "";
    const cache = scan?.cached ? ` · cache ${Math.round(scan.cache_age_s || 0)}s` : "";
    const days = scan?.validate_days ? ` · hist. até ${scan.validate_days}d` : "";
    const hz = " · Dia/Semana/Mês";
    const fun = funnel.pairs != null
      ? ` · ${funnel.pairs} pares → ${funnel.in_drop_band || 0} na queda → ${funnel.in_drop_and_vol || 0} c/ vol → ${list.length} final`
      : "";
    meta.textContent = list.length
      ? `${list.length} de até 30 · Spot${hz}${fun}${days}${when ? ` · ${when}` : ""}${cache}`
      : (scan?.empty_hint || "Nenhuma oportunidade Spot negociável na sua região com os filtros atuais");
    meta.title = "Funil + ranking por aptidão preditiva no horizonte escolhido";
  }
  if (!list.length) {
    const hint = escHtml(scan?.empty_hint || "Nada na faixa. Afrouxe volume/spread ou a queda mín./máx.");
    const funBit = funnel.pairs != null
      ? ` · funil: ${funnel.pairs} pares → ${funnel.in_drop_band || 0} na queda → ${funnel.in_drop_and_vol || 0} com vol`
      : "";
    body.innerHTML = `<tr><td class="empty" colspan="12">${hint}${escHtml(funBit)}</td></tr>`;
    return;
  }
  body.innerHTML = list.map((c, i) => {
    const instRaw = String(c.inst_id || "").toUpperCase();
    const inst = escHtml(instRaw);
    const drop = c.drop_pct != null ? fmtPct(-Math.abs(c.drop_pct)) : (c.chg24 != null ? fmtPct(c.chg24) : "—");
    const dropTip = c.drop_pct != null
      ? `Queda 24h Spot: ${fmt(Math.abs(c.drop_pct), 2)}%`
      : "Variação 24h do par Spot";
    const volTip = (() => {
      const bits = [];
      if (c.vol != null) bits.push(`Volume Spot 24h ≈ $${fmt(c.vol, 0)}`);
      if (c.vol_min_effective != null) bits.push(`mín. por idade ≈ $${fmt(c.vol_min_effective, 0)}`);
      if (c.age_days != null) bits.push(`listado há ~${fmt(c.age_days, 1)}d${c.is_new ? " (novo)" : ""}`);
      return bits.join(" · ") || "Volume Spot 24h";
    })();
    const liq = String(c.liquidity || "D");
    const liqTip = escHtml(hunterLiqTip(c));
    const bs = c.best_strategy || null;
    const tip = escHtml((c.reasons || []).slice(0, 3).join(" · ") || c.best_strategy_error || "Candidato Spot");
    let stratTip = "Sem estratégia sugerida";
    let stratCell = `<span class="hunter-bad" title="${escHtml(c.best_strategy_error || stratTip)}">—</span>`;
    if (bs) {
      stratTip = [
        `Melhor: ${bs.name || bs.id}`,
        `compra na queda ${fmt(bs.buy_pct, 1)}%`,
        `alvo ${fmt(bs.profit_target_pct, 1)}%`,
        bs.verdict ? String(bs.verdict) : "",
        bs.recommend_create ? "qualidade ok p/ criar bot" : "qualidade frágil — revise antes",
      ].filter(Boolean).join(" · ");
      stratCell = `<span title="${escHtml(stratTip)}"><strong>${escHtml(bs.name || bs.id || "—")}</strong><small style="display:block;color:var(--muted);font-weight:500">${fmt(bs.buy_pct, 1)}% ↓ · alvo ${fmt(bs.profit_target_pct, 1)}%</small></span>`;
    }
    const retTip = bs?.capital_return_pct != null
      ? `Retorno simulado do capital: ${fmt(bs.capital_return_pct, 2)}% em ${bs.days || "—"}d · ${bs.cycles_closed != null ? `${bs.cycles_closed} ciclo(s)` : ""}`
      : "Retorno % na simulação da melhor estratégia";
    const ret = bs?.capital_return_pct != null
      ? `<span class="${Number(bs.capital_return_pct) >= 0 ? "hunter-ok" : "hunter-bad"}" title="${escHtml(retTip)}">${fmtPct(bs.capital_return_pct)}</span>`
      : `<span title="${escHtml(retTip)}">—</span>`;
    const pred = c.prediction || {};
    const fit = pred.sell_fitness != null ? Number(pred.sell_fitness) : null;
    const fitCls = fit == null ? "" : fit >= 62 ? "hunter-ok" : fit < 45 ? "hunter-bad" : "";
    const cpd = pred.cycles_per_day != null ? Number(pred.cycles_per_day) : null;
    const fitTip = [
      pred.horizon_label ? `Período de negociação: ${pred.horizon_label}` : "",
      fit != null ? `Aptidão ${fmt(fit, 1)} (${pred.fitness_label || "—"})` : "",
      cpd != null ? `${fmt(cpd, 2)} ciclos/dia no hist.` : "",
      pred.bounce_prob_pct != null ? `pred. bounce ${fmt(pred.bounce_prob_pct, 0)}%` : "",
      (pred.reasons || []).slice(0, 2).join(" · "),
      pred.prediction_note || "",
    ].filter(Boolean).join(" · ") || "Aptidão preditiva a vendas";
    const fitCell = fit != null
      ? `<span class="${fitCls}" title="${escHtml(fitTip)}">${fmt(fit, 0)}</span>`
      : `<span title="${escHtml(fitTip)}">—</span>`;
    const vOk = c.validation_score;
    const vTot = c.validation_total;
    const canCreate = !!bs?.id;
    const rank = i === 0 ? `<span class="hunter-rank" title="Melhor aptidão preditiva neste scan">#1</span>` : "";
    const ageBadge = c.is_new && c.age_days != null
      ? `<span class="hunter-new" title="Listado na OKX Spot há ~${fmt(c.age_days, 1)}d${c.listed_at ? ` (${c.listed_at})` : ""} · vol mín. ajustado">novo · ${fmt(c.age_days, 0)}d</span>`
      : (c.age_days != null && c.age_days <= 60
        ? `<span class="hunter-age" title="Listado há ~${fmt(c.age_days, 1)}d${c.listed_at ? ` (${c.listed_at})` : ""}">${fmt(c.age_days, 0)}d</span>`
        : "");
    const pxTip = c.last != null
      ? `Preço atual Spot: ${fmtPx(c.last)}${c.bid != null || c.ask != null ? ` · bid ${c.bid != null ? fmtPx(c.bid) : "—"} / ask ${c.ask != null ? fmtPx(c.ask) : "—"}` : ""}`
      : "Preço atual Spot";
    const px = c.last != null ? fmtPx(c.last) : "—";
    const feat = c.candle_features || {};
    const avgVar = Number(c.avg_var_pct ?? feat.avg_var_pct);
    const avgVarMed = Number(c.avg_var_median_pct ?? feat.avg_var_median_pct);
    const avgVarN = c.avg_var_sample ?? feat.avg_var_sample;
    const avgVarOk = Number.isFinite(avgVar) && avgVar > 0;
    const tgt = hunterSuggestedTarget(c);
    const avgVarTip = avgVarOk
      ? `Média |variação| 24h no hist.: ${fmt(avgVar, 2)}%${Number.isFinite(avgVarMed) ? ` · mediana ${fmt(avgVarMed, 2)}%` : ""}${avgVarN ? ` · ${avgVarN} janelas` : ""}${c.atr_daily_pct != null || feat.atr_daily_pct != null ? ` · ATR diário ${fmt(Number(c.atr_daily_pct ?? feat.atr_daily_pct), 2)}%` : ""}`
      : "Sem histórico suficiente para média de variação 24h";
    const avgVarCell = avgVarOk
      ? `<span title="${escHtml(avgVarTip)}">±${fmt(avgVar, 1)}%</span>`
      : `<span title="${escHtml(avgVarTip)}">—</span>`;
    const tgtTip = tgt
      ? `Preço alvo de venda: ${fmtPx(tgt.px)} (+${fmt(tgt.pct, 1)}% líquido vs preço atual${Number.isFinite(tgt.cost) && tgt.cost > 0 ? ` · ~${fmt(tgt.gross, 1)}% bruto p/ taxa+spread` : ""}${tgt.sourceLabel ? ` · ${tgt.sourceLabel}` : ""}${avgVarOk ? ` · var. média 24h ±${fmt(avgVar, 1)}%` : ""}). Não é ordem.`
      : "Sem preço alvo: falta preço ou estratégia";
    const tgtCell = tgt
      ? `<span class="hunter-ok" title="${escHtml(tgtTip)}">${fmtPx(tgt.px)}<small class="hunter-target-pct">+${fmt(tgt.pct, 1)}%</small></span>`
      : `<span title="${escHtml(tgtTip)}">—</span>`;
    const hzShort = c.best_horizon_short
      || (HUNTER_HORIZONS[c.best_horizon]?.short)
      || "—";
    const hzTipBits = ["daily", "weekly", "monthly"].map((k) => {
      const h = c.horizons?.[k];
      if (!h || h.sell_fitness == null) return null;
      const mark = k === c.best_horizon ? "★ " : "";
      return `${mark}${h.short || k}: apt ${fmt(h.sell_fitness, 0)} · ${fmt(h.cycles_per_day, 2)} cyc/d`;
    }).filter(Boolean);
    const hzTip = hzTipBits.join(" · ") || "Melhor período de negociação entre dia / semana / mês";
    const hzCell = `<span class="hunter-hz" title="${escHtml(hzTip)}">${escHtml(hzShort)}</span>`;
    const checksLabel = vTot != null ? `${vOk}/${vTot}` : "—";
    const botBtnLabel = botsOn() && canCreate ? "Criar bot" : "Ver análise";
    const botBtnTip = canCreate
      ? `Análise + formulário · checks ${checksLabel}`
      : `Ver análise completa · checks ${checksLabel}`;
    return `<tr class="${i === 0 ? "hunter-row-top" : ""}">
      <td title="${tip}">
        <div class="token-cell token-cell-link" data-chart-inst="${inst}" title="Abrir gráfico Spot" role="link" tabindex="0">
          <img class="token-icon" src="${escHtml(c.icon || "")}" alt="" onerror="this.onerror=null;this.src='${escHtml(c.icon_alt || "")}'" />
          <span>${escHtml(c.base || "—")}${rank}${ageBadge}<small title="Par Spot ${inst}">${inst}</small></span>
        </div>
      </td>
      <td class="num hunter-col-drop sell" title="${escHtml(dropTip)}">${drop}</td>
      <td class="num hunter-col-px" title="${escHtml(pxTip)}">${px}</td>
      <td class="num hunter-col-var">${avgVarCell}</td>
      <td class="num hunter-col-target">${tgtCell}</td>
      <td class="hunter-col-strat">${stratCell}</td>
      <td class="hunter-col-hz">${hzCell}</td>
      <td class="num hunter-col-fit">${fitCell}</td>
      <td class="num hunter-col-ret">${ret}</td>
      <td class="hunter-col-liq"><span class="hunter-liq ${liq}" title="${liqTip}">${liq}</span></td>
      <td class="num hunter-col-vol" title="${escHtml(volTip)}">${fmtVol(c.vol)}</td>
      <td class="hunter-col-act">
        <div class="hunter-row-actions">
          <button class="btn ${botsOn() && canCreate ? "btn-primary" : "btn-ghost"}" type="button" data-hunter-bot="${inst}" title="${escHtml(botBtnTip)}">${escHtml(botBtnLabel)}${vTot != null ? ` · ${checksLabel}` : ""}</button>
          <button class="btn btn-ghost" type="button" data-hunter-order="${inst}" data-icon="${escHtml(c.icon || "")}" data-alt="${escHtml(c.icon_alt || "")}" title="Abrir Ordens Spot">Ordem</button>
        </div>
      </td>
    </tr>`;
  }).join("");
}

async function loadHunter({ forceScan = false, preserveToggle = false } = {}) {
  flash("hunter-msg", "", true);
  try {
    const data = await api("/api/hunter");
    lastHunter = data;
    applyHunterSettingsToForm(data.settings);
    // Toggle: só sincronizar na primeira carga (não em reloads)
    if (!preserveToggle && !loadHunter._toggled) {
      const toggle = $("hunter-auto-toggle");
      const label = $("hunter-auto-label");
      if (toggle) {
        toggle.checked = !!data.settings?.enabled;
        if (label) label.textContent = data.settings?.enabled ? "Auto-scan ligado" : "Auto-scan desligado";
      }
      loadHunter._toggled = true;
    }
    if (forceScan || !data.last_scan?.candidates?.length) {
      const scan = await api(`/api/hunter/scan${forceScan ? "?refresh=1" : ""}`);
      renderHunterCandidates(scan);
      renderHunterStatus({ ...data, last_scan: scan });
    } else {
      renderHunterCandidates(data.last_scan);
      renderHunterStatus(data);
    }
  } catch (err) {
    flash("hunter-msg", err.message || "Falha ao carregar caçador", false);
  }
}
loadHunter._toggled = false;

$("btn-hunter-scan")?.addEventListener("click", () => {
  withRefresh("btn-hunter-scan", async () => {
    const scan = await api("/api/hunter/scan?refresh=1");
    renderHunterCandidates(scan);
    if (lastHunter) renderHunterStatus({ ...lastHunter, last_scan: scan });
  }, {
    statusId: "hunter-msg",
    statusText: "Analisando dia, semana e mês…",
    busyLabel: "Analisando…",
  });
});

// Toggle auto-scan
$("hunter-auto-toggle")?.addEventListener("change", async (ev) => {
  const enabled = ev.target.checked;
  const label = $("hunter-auto-label");
  try {
    if (enabled) {
      await api("/api/hunter/start", { method: "POST" });
      if (label) label.textContent = "Auto-scan ligado";
      // Executar scan imediato ao ativar
      try {
        const scan = await api("/api/hunter/scan?refresh=1");
        renderHunterCandidates(scan);
      } catch (_) {}
    } else {
      await api("/api/hunter/stop", { method: "POST" });
      if (label) label.textContent = "Auto-scan desligado";
    }
  } catch (err) {
    ev.target.checked = !enabled;
    flash("hunter-msg", err?.message || "Erro ao alterar auto-scan", false);
  }
});

$("hunter-body")?.addEventListener("click", (ev) => {
  const botBtn = ev.target.closest("button[data-hunter-bot], button[data-hunter-detail], button[data-hunter-create]");
  if (botBtn) {
    const inst = botBtn.dataset.hunterBot || botBtn.dataset.hunterDetail || botBtn.dataset.hunterCreate;
    const c = (lastHunterScan?.candidates || []).find((x) => String(x.inst_id || "").toUpperCase() === String(inst || "").toUpperCase());
    if (c) openHunterBotModal(c);
    return;
  }
  const orderBtn = ev.target.closest("button[data-hunter-order]");
  if (orderBtn) {
    const inst = orderBtn.dataset.hunterOrder;
    if (!inst) return;
    goTradeToken(inst, orderBtn.dataset.icon || "", orderBtn.dataset.alt || "");
  }
});

function showLoginGate() {
  const gate = $("login-gate");
  if (gate) gate.hidden = false;
  document.body.classList.add("login-locked");
}

function hideLoginGate() {
  const gate = $("login-gate");
  if (gate) gate.hidden = true;
  document.body.classList.remove("login-locked");
}

function renderUserChip(user) {
  const chip = $("user-chip");
  if (!chip || !user?.authenticated) return;
  chip.hidden = false;
  const name = user.name || user.email || "Conta";
  if ($("user-chip-name")) $("user-chip-name").textContent = name;
  if ($("user-chip-email")) $("user-chip-email").textContent = user.email || "";
  const photo = $("user-chip-photo");
  if (photo) {
    photo.src = user.picture || "/static/img/logo-192.png";
    photo.alt = name;
  }
}

async function initAuth() {
  let cfg = { enabled: false };
  try {
    cfg = await fetch("/api/auth/config", { credentials: "same-origin" }).then((r) => r.json());
  } catch (_) {
    return true;
  }
  if (!cfg.enabled) return true;
  const meRes = await fetch("/api/auth/me", { credentials: "same-origin" });
  if (!meRes.ok) {
    showLoginGate();
    return false;
  }
  const me = await meRes.json();
  if (!me.authenticated) {
    showLoginGate();
    return false;
  }
  hideLoginGate();
  renderUserChip(me);
  return true;
}

$("btn-logout")?.addEventListener("click", () => {
  location.href = "/api/auth/logout";
});

let copilotOpen = false;
let copilotBusy = false;
const copilotHistory = [];
let copilotDraft = null;
let copilotPlanQueue = [];
let copilotPlanArmed = false;

function setCopilotOpen(on) {
  copilotOpen = !!on;
  const panel = $("copilot-panel");
  if (panel) panel.hidden = !copilotOpen;
  $("btn-copilot")?.setAttribute("aria-expanded", copilotOpen ? "true" : "false");
  if (copilotOpen) $("copilot-input")?.focus();
}

function resetCopilot() {
  copilotHistory.length = 0;
  copilotDraft = null;
  copilotPlanQueue = [];
  copilotPlanArmed = false;
  copilotBusy = false;
  const log = $("copilot-log");
  if (log) log.innerHTML = "";
  appendCopilot(
    "bot",
    "Nova conversa iniciada. Me diz o que precisa — posso listar seus tokens, criar ordens, mostrar preços, gerenciar bots, tudo por aqui.",
  );
}

function appendCopilot(role, text, actions) {
  const log = $("copilot-log");
  if (!log) return;
  const div = document.createElement("div");
  div.className = `copilot-msg ${role === "user" ? "user" : "bot"}`;
  div.textContent = text || "";
  if (actions && actions.length) {
    const box = document.createElement("div");
    box.className = "copilot-actions";
    actions.forEach((a, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = a.type === "order" && a.payload?.side === "sell" ? "btn btn-sell" : "btn btn-primary";
      btn.textContent = a.label || "Confirmar";
      btn.addEventListener("click", () => runCopilotAction(a));
      box.appendChild(btn);
    });
    div.appendChild(box);
  }
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function advanceCopilotPlan() {
  copilotPlanQueue.shift();
  if (!copilotPlanQueue.length) {
    appendCopilot("bot", "Fim dos passos do plano. Cada um só foi à OKX se você confirmou no modal.");
    return;
  }
  const nxt = copilotPlanQueue[0];
  appendCopilot("bot", `Próximo passo: ${nxt.label || "continuar"}. Confirme no modal.`);
  setTimeout(() => runCopilotAction(nxt, true), 500);
}

async function runCopilotAction(a, fromPlan = false) {
  const type = a?.type;
  if (type === "plan" && Array.isArray(a.steps) && a.steps.length) {
    copilotPlanQueue = a.steps.slice();
    appendCopilot("bot", "Vou abrir cada passo. Nada é enviado sem o seu OK no modal.");
    await runCopilotAction(copilotPlanQueue[0], true);
    return;
  }
  if (type === "navigate" && a.hash) {
    location.hash = a.hash;
    // Manter copilot aberto para continuar a conversa
    return;
  }
  if (type === "create_bot") {
    copilotPlanArmed = !!fromPlan;
    await openCreateBotModal(a.seed || {});
    return;
  }
  if (type === "start_bot" && a.bot_id) {
    await openStartBotModal(a.bot_id);
    return;
  }
  if (type === "stop_bot" && a.bot_id) {
    openStopBotModal(a.bot_id);
    return;
  }
  if (type === "order" && a.payload) {
    const p = a.payload;
    copilotPlanArmed = !!fromPlan;
    const inst = p.inst_id || "";
    const side = p.side || "buy";
    const ordType = p.ord_type || "market";
    const tgt = p.tgt_ccy || (side === "buy" ? "quote_ccy" : "base_ccy");
    // Setar orderIntent ANTES de goTradeToken para que loadOrders use os valores corretos
    const quote = (inst.split("-")[1] || "USDT").toUpperCase();
    orderIntent = { inst: inst.toUpperCase(), side, quote, icon: "", iconAlt: "", type: ordType, tgt };
    // Navegar para a página de ordens sem resetar o intent
    let pair = String(inst || "").toUpperCase();
    if (pair && !pair.includes("-")) pair = `${pair}-USDT`;
    orderQuote = quote;
    localStorage.setItem("okx_order_quote", quote);
    localStorage.setItem("okx_order_inst", pair);
    orderContext = null;
    orderContextInst = null;
    orderLoadError = null;
    location.hash = "#/orders";
    try {
      await refreshOrderContext(inst);
      setOrderFormLoading(false);
      const form = $("order-form");
      if (form) {
        form.ord_type.value = ordType;
        form.ord_type.dispatchEvent(new Event("change"));
        if (p.px != null && form.px) form.px.value = p.px;
        form.tgt_ccy.value = tgt;
        form.sz.value = p.sz;
      }
      setOrderSide(side);
      syncOrderForm();
      openOrderModal(buildOrderPayload());
    } catch (err) {
      flash("order-msg", err?.message || "não deu para montar a ordem", false);
    }
  }
}

async function sendCopilot(text) {
  const msg = String(text || "").trim();
  if (!msg || copilotBusy) return;
  copilotBusy = true;
  appendCopilot("user", msg);
  copilotHistory.push({ role: "user", content: msg });
  $("copilot-input").value = "";
  try {
    const res = await api("/api/assistant/chat", {
      method: "POST",
      body: JSON.stringify({
        message: msg,
        history: copilotHistory.slice(-16),
        draft: copilotDraft && copilotDraft.from_token ? copilotDraft : null,
      }),
    });
    const reply = res.reply || "Pronto.";
    copilotDraft = res.draft && Object.keys(res.draft).length ? res.draft : null;
    const acts = res.actions || [];
    appendCopilot("bot", reply, acts);
    copilotHistory.push({ role: "assistant", content: reply });
    const trade = acts.find((a) => a.type === "order" || a.type === "plan" || a.type === "create_bot");
    if (trade) await runCopilotAction(trade);
  } catch (err) {
    appendCopilot("bot", err?.message || "não consegui responder agora");
  } finally {
    copilotBusy = false;
  }
}

async function initCopilot() {
  try {
    const st = await api("/api/assistant/status");
    if ($("copilot-mode")) {
      $("copilot-mode").textContent = st.llm
        ? (st.provider === "cursor"
          ? "Cursor · confirma antes de enviar à OKX"
          : "IA ligada · confirma antes de enviar à OKX")
        : "modo local · frases simples · confirma antes";
    }
  } catch (_) {}
  appendCopilot(
    "bot",
    "Oi. Me pergunta o que quiser sobre a carteira e o PnL — por exemplo como compensar o prejuízo. Eu olho seus números e proponho; você confirma cada passo.",
  );
  $("btn-copilot")?.addEventListener("click", () => setCopilotOpen(!copilotOpen));
  $("copilot-close")?.addEventListener("click", () => setCopilotOpen(false));
  $("copilot-new")?.addEventListener("click", () => resetCopilot());
  $("copilot-form")?.addEventListener("submit", (ev) => {
    ev.preventDefault();
    sendCopilot($("copilot-input")?.value);
  });
}

// ===== Perfil =====

const PROFILE_AVATARS = ["\u{1F916}","\u{1F680}","\u{1F48E}","\u{1F98A}","\u{1F43A}","\u{1F981}","\u{1F43B}","\u{1F985}","\u{1F3AF}","\u{1F525}","\u{26A1}","\u{1F319}","\u{2600}\u{FE0F}","\u{1F3C6}","\u{1F47E}","\u{1F3B2}"];

async function loadProfile() {
  try {
    const me = await api("/api/auth/me");
    if (!me.authenticated) return;
    $("profile-photo").src = me.picture || "/static/img/logo-192.png";
    $("profile-name-display").textContent = me.name || "\u2014";
    $("profile-email-display").textContent = me.email || "\u2014";
    $("profile-name-input").value = me.name || "";
    $("profile-email-input").value = me.email || "";
    const grid = $("profile-avatars");
    if (grid) {
      grid.innerHTML = PROFILE_AVATARS.map(e =>
        `<button type="button" class="profile-avatar-opt" data-avatar="${e}">${e}</button>`
      ).join("");
    }
  } catch (_) {}
}

document.addEventListener("click", async (ev) => {
  if (ev.target.closest("#btn-change-photo")) {
    const picker = $("profile-avatar-picker");
    if (picker) picker.hidden = !picker.hidden;
    return;
  }
  const avatarBtn = ev.target.closest(".profile-avatar-opt[data-avatar]");
  if (avatarBtn) {
    const emoji = avatarBtn.dataset.avatar;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128"><text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" font-size="80">${emoji}</text></svg>`;
    const dataUri = `data:image/svg+xml,${encodeURIComponent(svg)}`;
    try {
      await api("/api/auth/profile", { method: "PUT", body: JSON.stringify({ picture: dataUri }) });
      $("profile-photo").src = dataUri;
      if ($("user-chip-photo")) $("user-chip-photo").src = dataUri;
      $("profile-avatar-picker").hidden = true;
      $("profile-avatars").querySelectorAll(".profile-avatar-opt").forEach(b => b.classList.remove("selected"));
      avatarBtn.classList.add("selected");
      flash("profile-msg", "Avatar atualizado", true);
    } catch (err) {
      flash("profile-msg", err?.message || "Erro", false);
    }
    return;
  }
  if (ev.target.closest("#btn-profile-logout")) {
    location.href = "/api/auth/logout";
    return;
  }
});

document.addEventListener("change", async (ev) => {
  if (ev.target.id !== "profile-upload") return;
  const file = ev.target.files?.[0];
  if (!file) return;
  if (file.size > 500000) { flash("profile-msg", "Imagem muito grande (max 500KB)", false); return; }
  const reader = new FileReader();
  reader.onload = async () => {
    try {
      await api("/api/auth/profile", { method: "PUT", body: JSON.stringify({ picture: reader.result }) });
      $("profile-photo").src = reader.result;
      if ($("user-chip-photo")) $("user-chip-photo").src = reader.result;
      $("profile-avatar-picker").hidden = true;
      flash("profile-msg", "Foto atualizada", true);
    } catch (err) { flash("profile-msg", err?.message || "Erro", false); }
  };
  reader.readAsDataURL(file);
  ev.target.value = "";
});

document.addEventListener("submit", async (ev) => {
  if (ev.target.id !== "profile-form") return;
  ev.preventDefault();
  const name = $("profile-name-input").value.trim();
  if (!name) { flash("profile-msg", "Nome vazio", false); return; }
  try {
    const res = await api("/api/auth/profile", { method: "PUT", body: JSON.stringify({ name }) });
    flash("profile-msg", "Perfil atualizado", true);
    $("profile-name-display").textContent = res.name || name;
    if ($("user-chip-name")) $("user-chip-name").textContent = res.name || name;
  } catch (err) { flash("profile-msg", err?.message || "Erro", false); }
});

// ===== Sistema de Notificações =====

let notifItems = [];
let notifUnread = 0;
let notifPanelOpen = false;
let notifSSE = null;

function showToast({ icon, title, body, tone }) {
  const container = $("toast-container");
  if (!container) return;
  const el = document.createElement("div");
  el.className = `toast ${tone || "info"}`;
  el.innerHTML = `
    <span class="toast-icon">${icon || "🔔"}</span>
    <div class="toast-body">
      <p class="toast-title">${title || ""}</p>
      <p class="toast-msg">${body || ""}</p>
    </div>
    <button class="toast-close" aria-label="Fechar">&times;</button>
  `;
  el.querySelector(".toast-close").addEventListener("click", (e) => {
    e.stopPropagation();
    removeToast(el);
  });
  el.addEventListener("click", () => {
    toggleNotifPanel(true);
    removeToast(el);
  });
  container.appendChild(el);
  // Auto-dismiss após 6s
  setTimeout(() => removeToast(el), 6000);
}

function removeToast(el) {
  if (!el || !el.parentNode) return;
  el.classList.add("removing");
  setTimeout(() => el.remove(), 300);
}

function updateNotifBadge() {
  const badge = $("notif-badge");
  if (!badge) return;
  if (notifUnread > 0) {
    badge.textContent = notifUnread > 99 ? "99+" : String(notifUnread);
    badge.hidden = false;
  } else {
    badge.hidden = true;
  }
}

function renderNotifList() {
  const list = $("notif-list");
  if (!list) return;
  if (!notifItems.length) {
    list.innerHTML = '<p class="notif-empty">Nenhuma notificação</p>';
    return;
  }
  list.innerHTML = notifItems.slice(0, 30).map(n => {
    const ago = timeAgo(n.ts);
    const unread = n.read ? "" : " unread";
    return `<div class="notif-item${unread}" data-id="${n.id}">
      <span class="notif-item-icon">${n.icon || "🔔"}</span>
      <div class="notif-item-body">
        <div class="notif-item-title">${n.title || ""}</div>
        <div class="notif-item-msg">${n.body || ""}</div>
      </div>
      <span class="notif-item-time">${ago}</span>
    </div>`;
  }).join("");
}

function timeAgo(ts) {
  if (!ts) return "";
  const diff = Math.floor(Date.now() / 1000 - ts);
  if (diff < 60) return "agora";
  if (diff < 3600) return `${Math.floor(diff / 60)}min`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

function toggleNotifPanel(forceOpen) {
  notifPanelOpen = forceOpen !== undefined ? !!forceOpen : !notifPanelOpen;
  const panel = $("notif-panel");
  if (panel) panel.hidden = !notifPanelOpen;
  if (notifPanelOpen) renderNotifList();
}

async function markAllNotifRead() {
  try {
    const res = await api("/api/notifications/read", { method: "POST", body: JSON.stringify({}) });
    notifUnread = res.unread || 0;
    notifItems.forEach(n => n.read = true);
    updateNotifBadge();
    renderNotifList();
  } catch (_) {}
}

function handleNotification(notif) {
  notifItems.unshift(notif);
  if (notifItems.length > 50) notifItems.length = 50;
  if (!notif.read) notifUnread++;
  updateNotifBadge();
  if (notifPanelOpen) renderNotifList();
  // Toast
  showToast({ icon: notif.icon, title: notif.title, body: notif.body, tone: notif.tone });
  // Browser push (se app em background)
  if (document.hidden && Notification.permission === "granted") {
    try {
      new Notification(notif.title || "OKBot", {
        body: notif.body || "",
        icon: "/static/img/logo-192.png",
        tag: notif.id,
      });
    } catch (_) {}
  }
}

function connectNotifSSE() {
  if (notifSSE) { try { notifSSE.close(); } catch (_) {} }
  notifSSE = new EventSource("/api/notifications/stream");
  notifSSE.addEventListener("notification", (ev) => {
    try {
      const notif = JSON.parse(ev.data);
      handleNotification(notif);
    } catch (_) {}
  });
  notifSSE.addEventListener("error", () => {
    // Reconectar após 10s
    setTimeout(() => {
      if (!document.hidden) connectNotifSSE();
    }, 10000);
  });
}

async function initNotifications() {
  // Carregar histórico
  try {
    const data = await api("/api/notifications");
    notifItems = data.items || [];
    notifUnread = data.unread || 0;
    updateNotifBadge();
  } catch (_) {}
  // Conectar SSE
  connectNotifSSE();
  // Event listeners
  $("btn-notifications")?.addEventListener("click", () => toggleNotifPanel());
  $("notif-read-all")?.addEventListener("click", () => markAllNotifRead());
  // Fechar painel ao clicar fora
  document.addEventListener("click", (e) => {
    if (notifPanelOpen && !e.target.closest("#notif-panel") && !e.target.closest("#btn-notifications")) {
      toggleNotifPanel(false);
    }
  });
  // Pedir permissão de browser push
  if ("Notification" in window && Notification.permission === "default") {
    // Pedir após 5s para não ser intrusivo
    setTimeout(() => {
      Notification.requestPermission();
    }, 5000);
  }
}

async function boot() {
  initTheme();
  initNavCollapse();
  applyBotsEnabled();
  const ok = await initAuth();
  if (!ok) return;
  await initCopilot();
  await initNotifications();
  await ensureFxRate();
  await refresh();
  showPage(pageId());
  startPolling();
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      if (pollTimer) clearTimeout(pollTimer);
      pollTimer = null;
      return;
    }
    refresh();
    startPolling();
  });
}

const THEME_KEY = "okx_theme";
const NAV_COLLAPSE_KEY = "okx_nav_collapsed";

function isDarkTheme() {
  return document.documentElement.classList.contains("theme-dark");
}

function syncThemeToggle() {
  const btn = $("btn-theme-toggle");
  if (!btn) return;
  const label = isDarkTheme() ? "Tema claro" : "Tema escuro";
  btn.title = label;
  btn.setAttribute("aria-label", label);
}

function setTheme(dark) {
  document.documentElement.classList.toggle("theme-dark", !!dark);
  try {
    localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
  } catch (_) {}
  syncThemeToggle();
  const modal = $("token-chart-modal");
  if (modal && !modal.hidden) loadTokenChartModal();
}

function toggleTheme() {
  setTheme(!isDarkTheme());
}

function initTheme() {
  let dark = false;
  try {
    dark = localStorage.getItem(THEME_KEY) === "dark";
  } catch (_) {}
  document.documentElement.classList.toggle("theme-dark", dark);
  syncThemeToggle();
  $("btn-theme-toggle")?.addEventListener("click", toggleTheme);
}

function setNavCollapsed(on) {
  document.body.classList.toggle("nav-collapsed", !!on);
  localStorage.setItem(NAV_COLLAPSE_KEY, on ? "1" : "0");
  const btn = $("btn-nav-toggle");
  if (btn) {
    btn.setAttribute("aria-expanded", on ? "false" : "true");
    btn.title = on ? "Expandir menu" : "Recolher menu";
    btn.setAttribute("aria-label", btn.title);
  }
}

function initNavCollapse() {
  const saved = localStorage.getItem(NAV_COLLAPSE_KEY) === "1";
  setNavCollapsed(saved);
  $("btn-nav-toggle")?.addEventListener("click", () => {
    setNavCollapsed(!document.body.classList.contains("nav-collapsed"));
  });
}

boot();
