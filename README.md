# OKBot

Sistema simples (backend + tela web) que monitora **1 par** na OKX e opera **live**:

- **Compra** quando o preço cai `buy_pct%` vs a referência.
- **Vende só com lucro líquido**: PnL estimado já desconta taxa de compra + taxa de venda. Não vende só porque o gráfico “subiu X%”.

## Lucro líquido (não variação bruta)

Com posição aberta, a cada tick:

```
gross         = preço × qty
sell_fee_est  = gross × fee_rate
net_proceeds  = gross − sell_fee_est
pnl           = net_proceeds − custo_total   # custo já inclui fee de compra
pnl_pct       = pnl / custo_total × 100
```

Vende quando `pnl_pct >= profit_target_pct`.

O **break-even** é o preço mínimo em que, depois da fee de venda, o PnL não fica negativo.

## Setup

```bash
cd ~/Documents/projects/okx-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edite `.env` com `DATABASE_URL` (MongoDB) e, se quiser, keys OKX. As keys em **Configurações → API Keys** também vão para o Mongo (`credentials`).

```
DATABASE_URL=mongodb+srv://...
OKX_FLAG=0
```

Coleções: `bots`, `positions`, `credentials`, `trades`, `events`, `portfolio_snapshots`.

Permissões da API: **Read + Trade**. Sem withdraw.

Suba o servidor:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Abra [http://localhost:8080](http://localhost:8080).

1. Ajuste par, % queda, **% lucro líquido**, taxa taker e USDT por ordem.
2. Clique **Testar OKX** (saldo + fee da conta, se disponível).
3. **Start**. Pare antes de mudar a config.

Na tela **Ordens**: compra/venda spot (mercado, limite, post-only, IOC, FOK), cancelar uma ou todas, histórico OKX.

## Config da tela

| Campo | Significado |
|---|---|
| Par | Ex.: `BTC-USDT` |
| % queda para comprar | Dip vs referência |
| % lucro líquido para vender | Alvo **após taxas**, não % do gráfico |
| Taxa taker % | Default `0.10` (0,10% spot). Ajuste se for VIP |
| USDT por compra | Tamanho da ordem market buy |
| Intervalo poll | Segundos entre ticks |

## Riscos

- Ordens **market** têm slippage: o PnL do tick pode diferir do fill.
- Taxa errada na config distorce break-even. Confira o fee real nos trades.
- Comece com o **valor mínimo** aceito pelo par.
- Sem login na UI: use só em máquina local/confiável.
- `OKX_FLAG=1` usa o simulated trading da OKX (se a key for de demo).

## Estrutura

```
app/main.py         API FastAPI + static
app/engine.py       loop buy-dip / sell-on-net-profit
app/okx_client.py   REST assinada OKX
app/pnl.py          break-even e PnL líquido
app/db.py           SQLite (config, posição, trades, log)
static/             tela única
```
