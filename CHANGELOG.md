# Claw Agent v8.0 — Changelog

## Sessão de Maio 2026

---

### 🔴 Bug crítico — API Binance (raiz de todos os stops falhados)

**Problema**: Em Dezembro 2025 a Binance migrou ordens condicionais
(`STOP_MARKET`, `TAKE_PROFIT_MARKET`, `TRAILING_STOP_MARKET`) do endpoint
`/fapi/v1/order` para `/fapi/v1/algoOrder`. O bot continuava a usar o endpoint
antigo → todos os stops falhavam silenciosamente há 5 meses.

**Fix** (`exchange.py`):
- URL: `/fapi/v1/order` → `/fapi/v1/algoOrder`
- Campo `type` → `orderType`
- Adicionado `algoType: CONDITIONAL`
- Resposta devolve `algoId` (não `orderId`)
- Nova função `cancel_algo_order()` via `DELETE /sapi/v1/algo/futures/order`
- Actualizado `execution.py` para usar `cancel_algo_order` em profit lock, TP1 e TP2

---

### 🔴 Bug — Posição WLDUSDC tratada como externa

**Problema**: Bot abria posição, mas na próxima scan já a considerava "manual".
- Janela `pending_sync` expirava em 5 min (tempo insuficiente)
- Verificação `symbol in SYMBOLS` falhava se lista dinâmica mudasse

**Fix** (`main.py`):
- Janela `pending_sync`: 300s → 900s (15 min)
- Removida verificação `symbol in SYMBOLS` no sync de órfão

---

### 🔴 Bug — GUARDA 25% disparava com perdas mínimas

**Problema**: `get_balance()` devolve `availableBalance` (margem livre ~9 USDC
com posições abertas). O guarda calculava 25% × 9 = 2.25 USDC de limite,
fechando tudo com qualquer perda > 2 USDC numa conta de 37 USDC.

**Fix** (`exchange.py`, `execution.py`):
- Nova função `get_wallet_balance()` devolve `totalMarginBalance`
- Guarda de drawdown usa `get_wallet_balance()` em vez de `get_balance()`
- Limite correcto: 25% × 37 USDC = ~9.25 USDC

---

### 🟡 Fix — Auto-deploy VPS nunca actualizava

**Problema**: Todo o desenvolvimento estava no branch
`claude/setup-project-structure-3xwuR`. O VPS faz `git reset --hard origin/main`
— nunca via as alterações.

**Fix**: Todos os commits passaram a ir directamente para `main`.

---

### ✅ Melhoria — Lookahead bias

**Problema**: `closes[-1]` era a vela ainda a formar, não uma vela fechada.
Sinais calculados com dados parciais → falsos positivos.

**Fix** (`main.py`):
- Scan: usa `klines[:-1]` (velas fechadas) para calcular indicadores
- Resumo horário: idem
- Sync de órfão: idem

---

### ✅ Melhoria — tickSize / PRICE_PRECISION

**Problema**: `SYMBOL_PRECISION` guardava casas decimais de **quantidade**
(stepSize), mas era usado também para formatar **preços** de stops e TPs.
BTCUSDC tem qty precision=3 mas price precision=1 → preços enviados com
decimais errados → ordens rejeitadas.

**Fix** (`config.py`, `exchange.py`):
- Novo dict `PRICE_PRECISION` com valores por defeito
- `get_top_futures_symbols()` extrai `PRICE_FILTER tickSize` do exchangeInfo
- `place_stop_market`, `place_take_profit`, `place_trailing_stop` usam
  `PRICE_PRECISION` para formatar preços

---

### ✅ Melhoria — workingType=MARK_PRICE

**Fix** (`exchange.py`):
- Adicionado `"workingType": "MARK_PRICE"` a `place_stop_market` e
  `place_take_profit`
- Protege contra wicks artificiais no last price que disparariam stops
  prematuramente

---

### ✅ Melhoria — Kill switch por ficheiro

**Fix** (`main.py`):
- No início de cada ciclo verifica se existe ficheiro `KILL_SWITCH`
- Se existir: cancela todas as algo orders, fecha posições do bot, encerra
- Uso: `touch ~/blank-app/claw_v8/KILL_SWITCH`

---

### ✅ Melhoria — Pre-signal pipeline

**Problema**: Filtros caros (HTF 4H/1H — buscam 200 velas remotas) corriam
para todos os pares mesmo quando os indicadores locais já vetavam.

**Fix** (`execution.py`) — nova ordem dos filtros em `abrir_trade`:
1. Locais (sem API): `volatility_regime`, `supertrend`, `bb_squeeze`, `cvd`, `vwap`
2. API leve (cached): `fear_greed`, `spread`, `market_conditions`, `obi`
3. API pesada: `htf_4h`, `htf_1h` — só correm se tudo o resto passou

---

### ✅ Expansão de mercado — USDC-M + USDT-M

**Antes**: Bot apenas scaneava USDC-M (≈38 pares disponíveis).

**Fix** (`exchange.py`, `config.py`):
- `get_top_futures_symbols()` aceita agora `quoteAsset` USDC e USDT
- USDC-M tem prioridade; USDT-M entra apenas para coins sem equivalente USDC
  (ex: LUNC, PUMP, DOGS, NEIRO, etc.)
- Filtro de idade: 30 dias → 7 dias
- `TOP_N_FUTURES`: 20 → 150 (top 150 por volume 24h)

---

### ✅ Ficheiro único `claw_v8_single.py`

Criado ficheiro com todo o código do bot num único ficheiro Python
para distribuição e backup.

---

### ✅ Backtesting engine `claw_v8/backtest.py`

Motor de backtesting criado de raiz:
- Descarrega klines 5m/1H/4H da Binance com cache em disco (1h TTL)
- Aplica `signal_trending` + `detect_market_mode` + alinhamento HTF
- Simula trades com SL/TP via high/low das velas, partial TP 33% a 2R,
  corte de emergência, timeout 8h, comissão 0.04% por lado
- Relatório: WR, PnL, profit factor, drawdown, LONG vs SHORT,
  breakdown mensal, por símbolo
- Uso: `python backtest.py --days 90` ou `--symbol BTCUSDC --days 180`

---

## Estado actual

| Parâmetro | Valor |
|---|---|
| Capital máximo | 300 USDC |
| Risco por trade | 5 USDC |
| Alavancagem | 6x |
| Margem | Cross |
| Pares scaneados | Top 150 (USDC-M + USDT-M) |
| Scan interval | 5 min (alinhado com velas) |
| Gestão de posições | 10s (com posições abertas) |
| Max trades abertos | 5 |
| Circuit breaker diário | 15 USDC |
| Drawdown guard | 25% do saldo total (`get_wallet_balance`) |
| Sessão UTC | 05h–23h |

---

## Pendente / Próximos passos

### Alta prioridade
- [ ] **Analisar primeiros trades reais** com os 150 pares — ver `analytics.py`
  após 20-30 trades para perceber quais filtros estão a cortar lucro vs. proteger
- [ ] **Verificar MITOUSDT** nos logs — apareceu no GUARDA 25% a ser fechado,
  sendo par USDT não deveria estar em `trades_abertos`; investigar origem

### Médio prazo
- [ ] **ML Filtering** — Random Forest para filtrar sinais maus com base no
  histórico SQLite. Só faz sentido após 200+ trades limpos
- [ ] **Backtesting com dados reais** — correr `python backtest.py --days 90`
  no VPS para validar parâmetros actuais (RSI, ADX, score thresholds)
- [ ] **Actualizar `claw_v8_single.py`** — reflectir todas as alterações desta
  sessão (actualmente desactualizado)

### Notas de contexto para próxima sessão
- Bot corre no **VPS** via `auto_deploy.sh` (cron 5min, branch `main`)
- Log VPS: `tail -f /root/claw.log`
- Kill switch: `touch /root/blank-app/claw_v8/KILL_SWITCH`
- Reset cooldown: `sqlite3 ~/blank-app/claw_v8/claw_v8.db "UPDATE bot_state SET value='0' WHERE key IN ('bloqueado_ate','perdas_seguidas'); UPDATE bot_state SET value='0.0' WHERE key='loss_dia';"`
- Credenciais em `~/.bashrc` — **nunca mostrar no chat**
- Conta EU BNFCR: `closePosition=true` obrigatório, `reduceOnly=true` não suportado
