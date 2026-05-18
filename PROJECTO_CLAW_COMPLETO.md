# Claw Agent — Histórico Completo do Projecto

**Período:** Início do projecto → 18 Maio 2026  
**Bot:** Trading algorítmico para Binance Futures (Cross Margin, USDC)  
**VPS:** `178.105.52.219`  
**Repositório:** `blank-app` (branch `claude/setup-project-structure-3xwuR`)

---

## Índice

1. [Arquitectura e Versões](#1-arquitectura-e-versões)
2. [Evolução do Bot (v1 → v8)](#2-evolução-do-bot)
3. [Módulos v8.0 — Referência](#3-módulos-v80--referência)
4. [Estratégia de Trading](#4-estratégia-de-trading)
5. [Filtros e Protecções](#5-filtros-e-protecções)
6. [Spot Scanner](#6-spot-scanner)
7. [Análises Fundamentais](#7-análises-fundamentais)
8. [Portfolio](#8-portfolio)
9. [Infraestrutura e Operações](#9-infraestrutura-e-operações)
10. [Ajustes de Configuração](#10-ajustes-de-configuração)
11. [Comandos Úteis](#11-comandos-úteis)
12. [Rotina de Sessão](#12-rotina-de-sessão)
13. [Sessões de Trabalho](#13-sessões-de-trabalho)

---

## 1. Arquitectura e Versões

| Versão | Ficheiro | Estado | Descrição |
|--------|----------|--------|-----------|
| v1–v6 | `claw_agent_v6.py` | Arquivado | Versões iniciais |
| v7.0 | `claw_agent_v7.py` | Parado | Monolítico ~1500 linhas |
| v7.1 | `claw_agent_v7.py` | Parado | +7 melhorias de pesquisa |
| **v8.0** | `claw_v8/` | **Activo no VPS** | Modular + SQLite + Filter Attribution |

---

## 2. Evolução do Bot

### Fase 1 — Fundações (v1 a v6)
- Ligação à Binance Futures
- STOP_MARKET real na abertura
- Sincronização de posições existentes
- Notificações Telegram
- Correcção de bugs de timestamp e saldo

### Fase 2 — v7.0 Features principais
Adicionadas progressivamente ao ficheiro monolítico:

- **ATR Trailing Stop** — stop dinâmico baseado em volatilidade
- **VWAP diário** — filtro de direcção (só LONG acima VWAP, SHORT abaixo)
- **OI/LSR filter** — Open Interest e Long/Short Ratio como confirmação
- **ORB — Opening Range Breakout** — modo especial para abertura NY (DST-aware)
- **Partial TP** — realização de 50% da posição no primeiro alvo
- **MTF 1H confirmation** — confirmação em timeframe 1H antes de entrar
- **Supertrend** — filtro de tendência adicional
- **TP dinâmico por força de sinal** — RR 2:1 / 3:1 / 4:1 conforme score
- **Tecto direcional** — máx 2 LONGs alt + 1 BTC simultâneos
- **Salvaguarda de margem** — fecha tudo acima de 75% margin ratio
- **Veto por símbolo** — bloqueia símbolos com performance negativa recente
- **Estorno automático** — inverte posição quando sinal reverte
- **Corte de emergência** — fecha se ROI ≤ -5% (backup ao stop)
- **Saída por tempo** — fecha após 30min se ROI ≥ 5%

### Fase 3 — v7.1 (7 melhorias de pesquisa 2025-2026)

Adicionadas após varrimento de literatura e práticas recentes:

1. **`_get_retry()`** — GET com exponential backoff para 429/5xx
2. **`htf_4h_confirmacao()`** — confirmação em 4H (fail-closed)
3. **`obi_ok()`** — Order Book Imbalance via `/fapi/v1/depth`
4. **`macro_event_proximo()`** — veto 30min antes de eventos macro (ForexFactory XML, cache 60min)
5. **`liquidity_sweep_detectado()`** — detecta wick + volume 2× + CVD positivo
6. **`equity_scale_factor()`** — reduz qty 50% após 3 perdas consecutivas
7. **`calc_correlation()`** — Pearson correlation, bloqueia pares com >0.75 correlação

### Fase 4 — v8.0 Clean Core (Reescrita Completa)

**Motivação:** ficheiro monolítico de ~2200 linhas impossível de testar e manter.

**Princípios:**
- Mesma estratégia da v7.1 — zero alterações de lógica
- 10 módulos com responsabilidade única
- SQLite substitui JSON para estado persistente
- Filter attribution — cada filtro loggado para análise futura
- State machine — transições de estado registadas

---

## 3. Módulos v8.0 — Referência

```
claw_v8/
├── main.py          # Loop principal + sync posições + posições externas
├── config.py        # Todas as constantes (editar aqui)
├── exchange.py      # Binance API + Telegram + retry + timestamp sync
├── indicators.py    # Funções puras: EMA, RSI, ATR, ADX, Supertrend, etc.
├── strategy.py      # detect_market_mode() + signal_trending() + SL/TP
├── filters.py       # Filtros com _log() automático para SQLite
├── risk.py          # em_sessao(), circuit_breaker, equity_scale_factor
├── execution.py     # abrir_trade() + gerir_posicoes()
├── storage.py       # SQLite schema + load/save memory + logging
├── analytics.py     # Relatórios de performance por filtro e símbolo
└── spot_scanner.py  # Scanner spot multi-timeframe (standalone)
```

### SQLite — Tabelas

```sql
positions          -- trades abertos e fechados
filter_events      -- cada avaliação de filtro (passed/blocked + price)
state_transitions  -- NO_POSITION → OPEN → PARTIAL_TP → CLOSED
risk_events        -- circuit breaker, margin alerts
equity_snapshots   -- saldo e margin ratio ao longo do tempo
bot_state          -- estado persistente (key/value)
```

### Filter Attribution
Cada filtro retorna via `_log()`:
```python
def _log(symbol, direction, name, passed, price, score=0, atr_pct=0.0):
    log_filter_event(symbol, direction, name, passed, price, score, atr_pct)
    return passed
```
Permite responder: *"qual filtro está a bloquear os melhores trades?"*

---

## 4. Estratégia de Trading

### Pares activos
Top 20 USDC-M perpétuos por volume 24h — carregados dinamicamente no arranque via `get_top_futures_symbols()`. Filtro de maturidade: exclui moedas listadas há menos de 30 dias (Alpha coins). Lista estática de fallback:

```python
SYMBOLS = [
    "BTCUSDC", "ETHUSDC", "BNBUSDC", "SOLUSDC",
    "XRPUSDC", "DOGEUSDC", "LINKUSDC",
    "SUIUSDC", "1000PEPEUSDC"
]
```
*(AVAXUSDC removido: 2W/2L -0.83 BNFCR, 2/3 cortes de emergência)*

### Parâmetros de risco

| Parâmetro | Valor |
|-----------|-------|
| Capital máx bot | 300 USDC |
| Risco por trade | 5 USDC |
| Alavancagem | 6× |
| Max trades abertos | 5 |
| Max LONGs alt | 3 |
| Max SHORTs alt | 3 |
| Max loss diário | 15 USDC |
| Max perdas seguidas | 3 |
| Cooldown após circuit breaker | 120 min |
| Margin ratio máximo | 35% |
| Drawdown máximo aberto | 25% do saldo |

### Detecção de modo
- `TRENDING` — ATR/price > 0.08%, slope EMA99 > 0.08%
- `MORTO` — tudo o resto (sem tendência)
- *(RANGING removido — risco de liquidação em alts)*

### Sinal TRENDING
EMA 9/21/99 + RSI + ADX + Supertrend + CMF + MFI + ROC

| Score | TP ratio |
|-------|----------|
| ≥ 6 + ADX > 45 | 4:1 RR |
| ≥ 6 + ADX > 35 | 3:1 RR |
| Default | 2:1 RR |

### SL/TP
- **SL:** 1.5 × ATR
- **TP:** dinâmico por score (ver tabela acima)
- **Partial TP:** 50% da posição no primeiro alvo
- **Trailing stop:** callback 0.5% BTC / 1.2% altcoins (a implementar)

---

## 5. Filtros e Protecções

### Ordem de execução em `abrir_trade()`

1. `macro_event_proximo()` — veto se evento macro em <30min
2. `volatility_regime_ok()` — ATR não excessivamente alto
3. `spread_ok()` — spread máximo 0.05%
4. `market_conditions_ok()` — condições gerais de mercado
5. `htf_4h_ok()` — confirmação 4H (fail-closed)
6. `htf_1h_ok()` — confirmação 1H (fail-closed)
7. `supertrend` — alinhamento de supertrend
8. `fear_greed_ok()` — Fear & Greed Index
9. `bb_squeeze_ok()` — Bollinger Band squeeze
10. `cvd_ok()` — Cumulative Volume Delta
11. `obi_ok()` — Order Book Imbalance (OBI > 0.3 veta SHORT se pressão compradora)
12. `vwap_ok()` — preço vs VWAP diário
13. `liquidity_sweep_detectado()` — info apenas
14. `equity_scale_factor()` — reduz qty 50% se 3+ perdas seguidas
15. Correlação Pearson com posições abertas (>0.75 = skip)

### Thresholds actuais (após ajustes)

| Parâmetro | Valor Original | Valor Actual |
|-----------|---------------|--------------|
| ADX mínimo | 25 | **22.5** |
| STOCH_VETO_SHORT | 5.0 | **2.5** |
| STOCH_VETO_LONG | 95.0 | 95.0 |
| OBI veto | 0.3 | 0.3 |
| Correlação máx | 0.75 | 0.75 |

### Gestão de posições abertas (`gerir_posicoes()`)
- BTC crash guard (queda > 3% em 5min)
- Margin ratio check (>50% → alerta)
- Detecção de fecho externo
- Saída por tempo + ROI
- Partial TP automático
- Corte de emergência (ROI ≤ -4%)
- SL/TP manual (backup)

---

## 6. Spot Scanner

### Ficheiro: `claw_v8/spot_scanner.py`

Ferramenta standalone para análise de compras em spot. Usa apenas APIs públicas da Binance (sem autenticação).

### Análise por timeframe

| Timeframe | Indicadores |
|-----------|------------|
| 1W (52 velas) | EMA 9/21, RSI, Supertrend |
| 1D (180 velas) | EMA 9/21/50/200, RSI, ADX, Supertrend, Volume, DD ATH |
| 4H (120 velas) | EMA 9/21, RSI |
| Global | Fear & Greed Index |

### Score → Decisão
| Score | Decisão |
|-------|---------|
| ≥ 10 | 🟢 COMPRAR |
| ≥ 5 | 🟡 AGUARDAR |
| ≥ 0 | 🟠 EVITAR |
| < 0 | 🔴 NÃO COMPRAR |

### Modos de uso
```bash
python3 claw_v8/spot_scanner.py SUI
python3 claw_v8/spot_scanner.py --top 50
python3 claw_v8/spot_scanner.py --top 100
python3 claw_v8/spot_scanner.py --daemon --top 100
```

### Modo Daemon
- Scan cada **4 horas** (alinha com vela 4H)
- **Top N dinâmico** — busca top N moedas por volume 24h Binance
- Exclui stablecoins, tokens alavancados (UP/DOWN/BULL/BEAR), wrapped tokens
- **8 workers paralelos** — 100 moedas em ~2-3 minutos
- Telegram apenas quando há mudança (sem spam)

### Alertas Telegram do scanner
| Evento | Mensagem |
|--------|----------|
| Nova moeda entra em COMPRAR | 🟢 Alerta imediato com detalhes |
| Moeda sai de COMPRAR | ⚠️ Sinal invalidado |
| Todos os dias às 8h UTC | 📊 Resumo (COMPRAR + AGUARDAR) |

---

## 7. Análises Fundamentais

### LAB Token — 🔴 NÃO COMPRAR

**O que é:** Multi-chain trading terminal (Solana, ETH, BNB), produto real com 0.5% fee.

**Razões para não comprar:**
- ZachXBT acusou fundador (Vova Sadkov) de manipulação coordenada em Bitget, Bybit, Binance, OKX
- Carteira insider depositou **40M LAB (~$13.6M)** em Bitget — dump coordenado
- Apenas **7.7%** do supply em circulação; 690M tokens locked/TBD
- Pump de **+537% em 1 semana** → crash 65% em horas
- Market cap ~$1.4B sem justificação pelos fundamentos

---

### SUI Token — 🟡 ACUMULAR EM DCA

**O que é:** Layer 1 da Mysten Labs (ex-Meta/Diem). Modelo de dados por objectos, processamento paralelo de transacções, linguagem Move.

**Pontos positivos:**
- TVL atingiu $2.6B (Out 2025), actualmente ~$570M
- Incluído no **Bitwise ETF** — validação institucional
- 200M+ contas, dezenas de biliões de transacções
- USDsui stablecoin a lançar; integração Ethereum 2026
- Próximo unlock (Jun 2026) = apenas **0.14%** do supply — irrelevante

**Riscos:**
- 60% do supply ainda por desbloquear até 2030
- Competição forte com Solana, Aptos
- TVL caiu -78% do pico

**Estratégia recomendada:** DCA em 3-4 parcelas. Não entrar tudo de uma vez.

| Entrada | % do capital |
|---------|-------------|
| Agora ~$1.12 | 25% |
| Se cair ~$0.90 | 25% |
| Se cair ~$0.75 | 25% |
| Reserva | 25% |

---

## 8. Portfolio

### Snapshot 2026-05-03
| Carteira | Valor |
|----------|-------|
| Binance Spot | $220 |
| Tangem Wallet | $3,749 |
| Invest Stocks | €882 |
| Invest Crypto | €718 |
| Invest ETF USD | €105 |
| **Total aprox.** | **€5,219** |

### Snapshot 2026-05-06
| Carteira | Valor |
|----------|-------|
| Tangem Wallet | $3,990 (+6.4%) |
| Invest Stocks | €866 |
| Invest Crypto | €271 (PAXG parcialmente vendido) |
| Invest ETF USD | €529 (MU + ANET adicionados) |
| **Total aprox.** | **€4,996** |

*Nota: queda aparente por EUR/USD subir (1.06→1.176) e PAXG vendido (-€382).*

### Snapshot 2026-05-10
| Carteira | Moeda | Valor |
|----------|-------|-------|
| Tangem Wallet | USD | $4,064 |
| Invest Stocks | EUR | €1,303 (RGTI compra significativa) |
| Invest Crypto | EUR | €15 (PAXG quase totalmente vendido) |
| Invest ETF USD | EUR | €569 (MU, ETN, ANET) |
| Nova Carteira Crypto | USD | ~$95 (BTC, LCX, SWELL, SOL staking) |
| Binance EUR | EUR | €770 (disponível) |
| **Total aprox.** | | **€6,189** |

### Activos Tangem (2026-05-10)
| Activo | Qtd | Valor USD |
|--------|-----|-----------|
| BTC | 0.03267347 | $2,642 |
| ETH | 0.44191314 | $1,029 |
| SOL | 2.75187726 | $258 (staking 5.83% APY) |
| XRP | 84.566087 | $121 |
| LINK | 0.96250677 | $10 |
| DOT | 1.00 | $1 |

### Snapshot 2026-05-14
| Carteira | Moeda | Valor |
|----------|-------|-------|
| Tangem Wallet | USD | $4,290 (+5.6% vs 10 Mai) |
| Invest Stocks | EUR | €1,323 |
| Bux (ETF/Stocks: MU, ANET, ETN) | EUR | ~€491 |
| Bux Crypto (PAXG recomprado) | EUR | ~€221 |
| Binance EUR | EUR | ~€770 (sem actualização) |
| **Total aprox.** | | **~€6,601** |

### Activos Tangem (2026-05-14)
| Activo | Qtd | Preço | Valor USD |
|--------|-----|-------|-----------|
| BTC | 0.0348942 | $81,522 | $2,845 |
| ETH | 0.44191314 | $2,304 | $1,018 |
| SOL | 3.11664982 | $92.87 | $289 (staking 5.83% APY) |
| XRP | 84.566087 | $1.49 | $126 |
| LINK | 0.96250677 | $10.64 | $10 |
| DOT | 1.00 | $1.40 | $1 |
| **Total** | | | **$4,290** |

### Invest Stocks (2026-05-14)
| Ticker | Qtd | Valor EUR | Variação |
|--------|-----|-----------|----------|
| VWCE | 1.843 | €296.79 | +4.65% |
| CEG | 0.954 | €225.44 | -5.32% |
| PLTR | 1.357 | €155.41 | -0.86% |
| RGTI | 8.442 | €140.11 | +4.54% |
| HO (Thales) | 0.644 | €143.63 | -15.17% |
| LEU | 0.552 | €89.98 | -11.11% |
| HRS | 0.334 | €88.40 | -11.60% |
| CMP | 3.353 | €87.37 | +2.32% |
| FTNT | 0.742 | €76.47 | +5.61% |
| Kongsberg | 3.694 | €19.60 | novo |
| **Total** | | **€1,323** | |

### Snapshot 2026-05-16
| Carteira | Moeda | Valor | Δ vs 14 Mai |
|----------|-------|-------|-------------|
| Tangem Wallet | USD | $4,080 | -$210 (-4.9%) |
| Invest Stocks | EUR | €1,299 | -€24 (-1.8%) |
| Robinhood (ANET+ETN+PAXG) | EUR | €695 | -€17 (-2.4%) |
| Binance EUR | EUR | ~€770 | — |
| **Total aprox.** | | **~€6,393** | **-€208 (-3.2%)** |

*Nota: queda por correção cripto generalizada hoje (-3% a -6% em todos os activos).*
*MU (Micron) vendido. ANET aumentado (1.24→2.04), ETN aumentado (0.31→0.45).*

### Activos Tangem (2026-05-16)
| Activo | Qtd | Preço | Valor USD | Δ vs 14 Mai |
|--------|-----|-------|-----------|-------------|
| BTC | 0.0348942 | $77,960 | $2,720 | -$125 |
| ETH | 0.44191314 | $2,176 | $961 | -$57 |
| SOL | 3.11745595 | $86.05 | $268 | -$21 |
| XRP | 84.566087 | $1.41 | $119 | -$7 |
| LINK | 0.96250677 | $9.64 | $9 | -$1 |
| DOT | 1.00 | $1.26 | $1 | — |
| **Total** | | | **$4,080** | **-$210** |

### Invest Stocks (2026-05-16)
| Ticker | Qtd | Valor EUR | Var hoje |
|--------|-----|-----------|----------|
| VWCE | 1.843 | €293.87 | +3.62% |
| PLTR | 1.357 | €155.29 | -0.94% |
| RGTI | 8.442 | €129.75 | -3.19% |
| HRS | 0.334 | €87.24 | -12.76% |
| CMP | 3.353 | €87.16 | +2.07% |
| FTNT | 0.742 | €78.21 | +8.01% |
| Kongsberg | 3.694 | €20.06 | novo |
| + CEG, HO, LEU | — | (scrolled) | — |
| **Total** | | **€1,299** | |

### Robinhood (2026-05-16)
| Activo | Qtd | Preço | Valor |
|--------|-----|-------|-------|
| ANET (Arista) | 2.0376 | $141.31 | ~€255 |
| ETN (Eaton) | 0.4549 | $398.80 | ~€161 |
| PAXG | 0.052037 | €3,895 | €202.68 |
| ETH | 0.00351 | €1,874 | €6.58 |
| Buying power | — | — | €75.17 |
| **Total** | | | **€695.06** |

---

## 9. Infraestrutura e Operações

### Configuração do servidor
- **VPS:** `178.105.52.219`
- **OS:** Ubuntu/Debian
- **Python:** 3.13
- **Repositório:** `/root/blank-app`
- **Bot log:** `/root/claw.log`
- **Scanner log:** `/root/spot.log`
- **Bot PID:** `/root/claw.pid`
- **Scanner PID:** `/root/spot.pid`

### Arranque dos processos
```bash
# Bot principal
grep -E 'export.*(TELEGRAM|BINANCE)' /root/.bashrc > /tmp/ce && \
bash -c 'source /tmp/ce; kill $(cat /root/claw.pid) 2>/dev/null; \
cd /root/blank-app && PYTHONUNBUFFERED=1 nohup python3 claw_v8/main.py \
> /root/claw.log 2>&1 & echo $! > /root/claw.pid'

# Spot Scanner daemon
bash -c 'source /tmp/ce; cd /root/blank-app && \
PYTHONUNBUFFERED=1 nohup python3 claw_v8/spot_scanner.py --daemon --top 100 \
> /root/spot.log 2>&1 & echo $! > /root/spot.pid'
```

### Monitorização
```bash
# Ver log do bot
ssh root@178.105.52.219 "tail -30 /root/claw.log"

# Ver log em tempo real
ssh root@178.105.52.219 "tail -f /root/claw.log"

# Ver ranking do scanner
ssh root@178.105.52.219 "grep -A 110 'RANKING' /root/spot.log | tail -110"

# Ver processos activos
ssh root@178.105.52.219 "ps aux | grep python | grep -v grep"

# Relatório de performance
ssh root@178.105.52.219 "cd /root/blank-app/claw_v8 && python3 analytics.py"
```

### Credenciais
Guardadas em `~/.bashrc` no VPS e em `/etc/environment` (carregamento automático).

```bash
export TELEGRAM_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
export BINANCE_API_KEY="..."
export BINANCE_API_SECRET="..."
```

### Binance API
- **Tipo:** Futures USDC (Cross Margin)
- **Moeda de margem:** BNFCR (Europa)
- **IP whitelisted:** `178.105.52.219`
- **Permissões:** Futures trading (sem levantamentos)

### Problema histórico de IP
O bot corria no Termux do telemóvel — o IP mudava sempre que o telemóvel mudava de WiFi/dados móveis, causando bloqueios na Binance. Resolvido ao migrar para o VPS com IP fixo.

---

## 10. Ajustes de Configuração

### Histórico de alterações ao longo do projecto

| Data | Parâmetro | Antes | Depois | Motivo |
|------|-----------|-------|--------|--------|
| Inicial | Capital máx | 50 USDC | 75 USDC | Aumentar exposição |
| Inicial | Sessão trading | Limitada | 05:00-23:00 UTC | Mais oportunidades |
| v7 | Max posições | 3 | 5 → 4 | Controlo de risco |
| v7 | AVAXUSDC | Activo | Removido | -0.83 BNFCR, 2/3 emergências |
| v8 | recvWindow | 5s | 10s | Tolerância timestamp |
| Mai-13 | STOCH_VETO_SHORT | 5.0 | **2.5** | Apanhar SHORTs em quedas |
| Mai-13 | ADX mínimo | 25 | **22.5** | Menos falsos MORTO |
| Mai-16 | volume_ok() | volumes[-1] | **volumes[-2]** | Vela a formar = ~0 volume → VETO_VOL em tudo |
| Mai-16 | volume_ok() threshold | 1.0x | **0.8x** | Menos restritivo |
| Mai-18 | RATIO_ALVO | 2.0 | **3.0** | TP mais longe = ganhos maiores |
| Mai-18 | PARTIAL_TP_RATIO | 0.5 | **0.67** | TP1 dispara a 2R (era 1R) |
| Mai-18 | PARTIAL_TP_QTY | 50% | **33%** | Deixa mais posição no runner |
| Mai-18 | EMERGENCY_ROI_CUT | -4.0% | **-5.5%** | Mais espaço ao trade |
| Mai-18 | TP2 | não existia | **3R, fecha 33%** | Runner com lock de lucro |
| Mai-18 | Breakeven stop | não existia | **entry +0.2%** | Após TP1, pior caso = zero |
| Mai-18 | Capital máx bot | 75 USDC | **300 USDC** | Escala proporcional ao saldo real |
| Mai-18 | Risco por trade | 3 USDC | **5 USDC** | Proporcional ao novo capital |
| Mai-18 | Alavancagem | 5× | **6×** | Mais exposição controlada |
| Mai-18 | Max trades abertos | 4 | **5** | Proporcional ao capital |
| Mai-18 | Max LONGs/SHORTs alt | 2 | **3** | Proporcional ao capital |
| Mai-18 | Max loss diário | 7.5 USDC | **15 USDC** | Proporcional ao capital |
| Mai-18 | MARGIN_RATIO_MAX | 50% | **35%** | Protecção mais cedo |
| Mai-18 | MAX_DRAWDOWN_PCT | não existia | **25%** | Fecha tudo se PnL aberto > -25% saldo |
| Mai-18 | Pares dinâmicos | lista estática | **top 20 por volume** | `get_top_futures_symbols()` + filtro 30 dias |
| Mai-18 | Endpoint ordens stop | `/fapi/v1/algoOrder` | **`/fapi/v1/order`** | Fix erro "algotype" — endpoint errado desde sempre |

---

## 11. Comandos Úteis

### Operações diárias
```bash
# Estado do bot
ssh root@178.105.52.219 "tail -20 /root/claw.log"

# Scan spot manual (top 100)
ssh root@178.105.52.219 "cd /root/blank-app && python3 claw_v8/spot_scanner.py --top 100"

# Scan de uma moeda específica
ssh root@178.105.52.219 "cd /root/blank-app && python3 claw_v8/spot_scanner.py SUI"

# Analytics completo
ssh root@178.105.52.219 "cd /root/blank-app/claw_v8 && python3 analytics.py"
```

### Git
```bash
# Pull no VPS
ssh root@178.105.52.219 "cd /root/blank-app && git pull"

# Push de alterações (Termux → VPS)
cd ~/blank-app && git add -p && git commit -m "mensagem" && git push
```

### Reiniciar bot após alteração de código
```bash
ssh root@178.105.52.219 "cd /root/blank-app && git pull && \
grep -E 'export.*(TELEGRAM|BINANCE)' /root/.bashrc > /tmp/ce && \
bash -c 'source /tmp/ce; kill \$(cat /root/claw.pid) 2>/dev/null; \
PYTHONUNBUFFERED=1 nohup python3 claw_v8/main.py > /root/claw.log 2>&1 & \
echo \$! > /root/claw.pid' && sleep 3 && tail -5 /root/claw.log"
```

---

## 12. Rotina de Sessão

**Combinado:** no início de cada sessão com Claude, dizer **"faz o relatório diário"**.

Claude irá automaticamente:
1. Ler este ficheiro (`PROJECTO_CLAW_COMPLETO.md`) para ter contexto completo
2. Fazer varrimento na internet (GitHub, Reddit, fóruns algotrading) para benchmarking de melhorias
3. Correr `check_results.py` no VPS para ver dados novos do bot
4. Propor melhorias baseadas nos dados reais + benchmarking

**Comando para relatório do bot:**
```bash
ssh root@178.105.52.219 "cd /root/blank-app && python3 claw_v8/check_results.py"
```

---

## 13. Sessões de Trabalho

### Sessão 2026-05-13
Ver ficheiro `SESSAO_2026-05-13.md` para detalhe completo.

**Resumo:** Spot Scanner, monitorização posições externas, migração Termux → VPS, STOCH_VETO_SHORT 5.0 → 2.5, ADX 25 → 22.5.

### Sessão 2026-05-16
- Correcção crítica `volume_ok()`: usava `volumes[-1]` (vela em formação ~0) → VETO_VOL bloqueava tudo. Corrigido para `volumes[-2]`
- Resumo horário de mercado via Telegram
- Portfolio: Tangem $4,080 | Invest €1,299 | Robinhood €695 | Total ~€6,393

### Sessão 2026-05-18 (parte 1)
- **Diagnóstico:** expectância -€0.20/trade (ganhos ~€1.75 vs perdas ~€3.00)
- **Benchmarking:** Freqtrade, Jesse, UT Bot, r/algotrading — padrão "2R-3R-runner"
- **Bug corrigido:** tabela `positions` vazia — sync block não chamava `db_open_position()`, close fazia UPDATE silencioso 0 rows. Corrigido com upsert em `close_position_db()`
- **Overhaul exits (maior mudança até hoje):**
  - TP1 a 2R → fecha 33% → stop para breakeven +0.2%
  - TP2 a 3R → fecha 33% → stop para +1R
  - Runner 34% com lucro garantido
  - RATIO_ALVO 2→3 | PARTIAL_TP_RATIO 0.5→0.67 | EMERGENCY_ROI_CUT -4%→-5.5%
- `cancel_order()` adicionado em `exchange.py`
- **Expectância esperada:** -€0.20 → **+€1.44 por trade**
- Rotina de sessão estabelecida: dizer *"faz o relatório diário"*
- Portfolio: Tangem $4,079 | Invest €1,299 | Robinhood €695 | Total ~€6,393

### Sessão 2026-05-18 (parte 2)
- **Escala de capital:** 75→300 USDC | risco 3→5 | alavancagem 5→6 | trades 4→5 | loss diário 7.5→15
- **Pares dinâmicos:** `get_top_futures_symbols(n=20, min_days=30)` — top 20 USDC-M por volume, exclui moedas com menos de 30 dias. Precisão de quantidade lida do LOT_SIZE da exchangeInfo
- **Protecção capital (4 camadas):**
  1. Corte emergência ROI ≤ -5.5%
  2. Drawdown guard: PnL aberto > -25% do saldo → fecha tudo
  3. Margin ratio > 35% → alerta Telegram
  4. BTC crash > 3% em 5min → fecha alts
- **Fix crítico endpoint ordens:** todas as funções de stop usavam `/fapi/v1/algoOrder` (requer parâmetro `algotype` — endpoint TWAP/VP) em vez de `/fapi/v1/order`. Causa: erro "Mandatory parameter 'algotype'" em todos os stops. Corrigido em `place_stop_market`, `place_take_profit`, `place_trailing_stop`. Também `algoId` → `orderId` nas respostas.
- **Caso ZECUSDC analisado:** stop falhou (algotype error) → bot ativou TEMPO+LUCRO aos 30min e fechou a +€11.40. Não foi o trailing apertado — foi o bug do endpoint. Resolvido com o fix acima.
- **Git pull --rebase:** VPS tinha branches divergentes. Solução: `git pull --rebase origin claude/setup-project-structure-3xwuR`
- **Ideia trailing adaptativo discutida mas não implementada:** callback 0.5% BTC / 1.2% altcoins. Pendente para próxima sessão.

---

## Notas Técnicas

### Porquê 4H para o spot scanner
Os indicadores mais rápidos analisados são velas de 4H. Varrer a cada 15 minutos seria analisar os mesmos dados 16 vezes sem diferença, além de ~28.000 pedidos/dia à Binance.

### Porquê SQLite em vez de JSON (v8.0)
JSON não permite queries. Com SQLite é possível responder: *"qual filtro bloqueou os trades mais rentáveis?"* — informação impossível de extrair do JSON.

### BNFCR vs USDC
A Binance Europa usa BNFCR como moeda de margem nos futuros, não USDC. O código aceita ambos em `get_balance()`.

### Isolated vs Cross Margin
Isolated margin não disponível na Binance Europa. O bot usa sempre Cross Margin.
