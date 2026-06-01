# Claw Agent — Documento Master do Projecto

**Período:** Início → 23 Maio 2026
**Bot:** Trading algorítmico para Binance Futures (Cross Margin, USDC-M)
**Repositório:** `blank-app` (branch `main`, auto-deploy no VPS)
**VPS:** `178.105.52.219`

---

## Índice

1. [Arquitectura e Versões](#1-arquitectura-e-versões)
2. [Módulos v8.0](#2-módulos-v80)
3. [Estratégia de Trading](#3-estratégia-de-trading)
4. [Filtros e Protecções](#4-filtros-e-protecções)
5. [Guards de Risco](#5-guards-de-risco)
6. [Lógica de Gestão de Posições](#6-lógica-de-gestão-de-posições)
7. [Posições Manuais](#7-posições-manuais)
8. [Infraestrutura e Operações](#8-infraestrutura-e-operações)
9. [Ajustes de Configuração — Histórico](#9-ajustes-de-configuração--histórico)
10. [Análises Fundamentais](#10-análises-fundamentais)
11. [Portfolio — Histórico](#11-portfolio--histórico)
12. [Comandos Úteis](#12-comandos-úteis)
13. [Sessões de Trabalho](#13-sessões-de-trabalho)
14. [Changelog Técnico](#14-changelog-técnico)
15. [Lições Aprendidas](#15-lições-aprendidas)

---

## 1. Arquitectura e Versões

| Versão | Ficheiro | Estado | Descrição |
|--------|----------|--------|-----------|
| v1–v6 | `claw_agent_v6.py` | Arquivado | Versões iniciais |
| v7.0 | `claw_agent_v7.py` | Parado | Monolítico ~1500 linhas |
| v7.1 | `claw_agent_v7.py` | Parado | +7 melhorias de pesquisa |
| **v8.0** | `claw_v8/` | **Activo no VPS** | Modular + SQLite + Filter Attribution |

### Evolução resumida

**v1–v6:** Ligação Binance, STOP_MARKET real, sync posições, Telegram, correcção bugs timestamp.

**v7.0 → v7.1:** ATR Trailing Stop, VWAP diário, OI/LSR filter, ORB, Partial TP, MTF 1H, Supertrend, TP dinâmico por score, tecto direcional, salvaguarda margem, veto por símbolo, corte emergência, saída por tempo. Depois: `_get_retry()`, HTF 4H, OBI, macro events, liquidity sweep, equity scale, correlação Pearson.

**v8.0:** Reescrita completa. Mesma estratégia v7.1, 10 módulos com responsabilidade única, SQLite substitui JSON, filter attribution, state machine.

---

## 2. Módulos v8.0

```
claw_v8/
├── main.py          # Loop principal, scan de pares, sync de posições
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
```python
def _log(symbol, direction, name, passed, price, score=0, atr_pct=0.0):
    log_filter_event(symbol, direction, name, passed, price, score, atr_pct)
    return passed
```
Permite responder: *"qual filtro está a bloquear os melhores trades?"*

---

## 3. Estratégia de Trading

### Pares activos
Top 150 USDC-M perpétuos por volume 24h — carregados dinamicamente via `get_top_futures_symbols()`. Filtro de maturidade: exclui moedas listadas há menos de 30 dias. Lista estática de fallback:
```python
SYMBOLS = ["BTCUSDC", "ETHUSDC", "BNBUSDC", "SOLUSDC",
           "XRPUSDC", "DOGEUSDC", "LINKUSDC", "SUIUSDC", "1000PEPEUSDC"]
```

### Parâmetros de risco actuais

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
| Sessão UTC | 05h–23h |

### Detecção de modo
- `TRENDING` — ATR/price > 0.08%, slope EMA99 > 0.08%
- `MORTO` — tudo o resto (sem entrada)

### Sinal TRENDING
EMA 9/21/99 + RSI + ADX + Supertrend + CMF + MFI + ROC

| Score + ADX | TP ratio |
|---|---|
| ≥ 6 + ADX > 45 | 4:1 RR |
| ≥ 6 + ADX > 35 | 3:1 RR |
| Default | 3:1 RR (RATIO_ALVO=3.0) |

### SL/TP
- **SL:** 1.2–1.8 × ATR (adaptativo por volatilidade)
- **Partial TP1:** a 2R → fecha 33% → stop para breakeven +0.2%
- **Partial TP2:** a 3R → fecha 33% → stop para +1R
- **Runner:** 34% restante com lucro garantido

---

## 4. Filtros e Protecções

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
11. `obi_ok()` — Order Book Imbalance (>0.3 veta SHORT se pressão compradora)
12. `vwap_ok()` — preço vs VWAP diário
13. `liquidity_sweep_detectado()` — confirmação (não bloqueia)
14. `equity_scale_factor()` — reduz qty se 3+ perdas seguidas
15. Correlação Pearson com posições abertas (>0.75 = skip)
16. **VETO se posição já existe** (bot ou manual) — nunca adoptar posição do utilizador

### Thresholds actuais

| Parâmetro | Valor |
|-----------|-------|
| ADX mínimo | 22.5 |
| STOCH_VETO_SHORT | 2.5 |
| STOCH_VETO_LONG | 95.0 |
| OBI veto | 0.3 |
| Correlação máx | 0.75 |
| ATR_MIN_PCT | 0.08% |
| EMA_SLOPE_MIN | 0.08% |

---

## 5. Guards de Risco

### Camada 1 — Corte de emergência (por posição)
- ROI ≤ -5.5% → fecha imediatamente

### Camada 2 — BTC crash guard
- Queda BTC > 3% → fecha todos os LONGs do bot

### Camada 3 — Drawdown 25%
- PnL total aberto (só trades bot) > -25% do saldo → fecha tudo do bot

### Camada 4 — Margem USDC/BNFCR > 35%
- Lê margem **só do activo USDC/BNFCR** (não afectado por USDT-M)
- Fecha trades do bot; nunca toca em posições manuais

### Camada 5 — Guard de liquidação global (NOVO — Mai 23)
Lê rácio de **TODA a conta** (USDT-M + USDC-M):

| Rácio global | Acção |
|---|---|
| > 40% | 🟡 Alerta Telegram (máx 1 por 5 min) |
| > 50% | 🛡 **Fecha TODAS as posições a positivo** (bot + manuais) |
| > 55% | 🟠 Alerta Telegram |
| > 70% | 🔴 Alerta crítico |

**Excepção deliberada:** único caso em que o bot fecha posições manuais — para evitar liquidação total da conta cross-margin.
Corre em todos os ciclos, mesmo sem trades do bot abertos.

### Circuit breaker
- `MAX_LOSS_DIA = 15 USDC` → cooldown 120min
- `MAX_PERDAS_SEGUIDAS = 3` → cooldown 120min
- Veto por símbolo: 3 perdas seguidas → 24h; WR < 30% em 5+ trades → 12h

---

## 6. Lógica de Gestão de Posições

### Abertura (`abrir_trade`)
1. Todos os filtros (ver secção 4)
2. **VETO se posição já existe** no símbolo
3. Escreve `pending_sync[symbol]` → coloca ordem MARKET
4. Coloca STOP_MARKET com `closePosition=true` (obrigatório conta EU/BNFCR)
5. Coloca TP como algo order
6. Se stop falhar: software SL activo a cada 10s

### Gestão (`gerir_posicoes`, ciclo 10s com posições)
- **ROI_TP_IMEDIATO:** ROI ≥ 7% → fecha imediatamente, sem aguardar tempo
- **TIME_TP:** 10min aberto + ROI ≥ 5% → fecha
- **Profit lock:** PnL > 1 USDC → move SL a cada +0.5 USDC
  - Usa nível ANTERIOR para garantir distância mínima ao mark price (Binance rejeita < ~0.1%)
  - Retry 3× com buffer crescente de 0.15%
- **TP1** (2R): fecha 33%, trailing stop para breakeven
- **TP2** (3R): fecha mais 33%, trailing stop para +1R
- **Emergency cut:** ROI ≤ -5.5% → fecha imediatamente
- **Software SL:** `price <= sl` (LONG) ou `price >= sl` (SHORT) → fecha via MARKET

### Restrição crítica EU/BNFCR
`STOP_MARKET` com `reduceOnly=true` **não é suportado**.
Usar sempre `closePosition=true`. Só pode haver **um** STOP_MARKET closePosition por símbolo de cada vez — profit lock cancela stop antigo ANTES de colocar novo.

### Endpoint de ordens condicionais
```
POST /fapi/v1/algoOrder   (não /fapi/v1/order)
Resposta devolve algoId   (não orderId)
Cancelar: DELETE /sapi/v1/algo/futures/order
```
Parâmetros enviados no **body** (não query string):
```python
r = requests.post(f"{BASE_URL}/fapi/v1/algoOrder",
                  data=signed, headers=_headers())
```

---

## 7. Posições Manuais

### Detecção
- Sem `pending_sync` → vai para `posicoes_externas`
- Nunca adicionadas a `trades_abertos`

### Monitorização
- Alertas de ROI: -5%, -3%, +3%, +5%, +10%, +15%, +20%
- Quando fecha: ROI final + duração

### Regras absolutas
- Bot **NUNCA** coloca stops em posições manuais
- Bot **NUNCA** fecha posições manuais (excepto guard liquidação global > 50% — só posições a positivo)
- P&L das manuais **NÃO** conta para circuit breaker nem drawdown guard

### Mecânica de protecção (pending_sync)
```python
# ANTES de escrever pending_sync — evita adoptar posição do utilizador
if symbol in mem.get("trades_abertos", {}) or symbol in mem.get("posicoes_externas", {}):
    print(f"[VETO] {symbol}: posição já existe — sem entrada")
    return
```
No sync loop:
```python
already_external = symbol in mem.get("posicoes_externas", {})
is_bot_orphan = (symbol in pending and
                 time.time() - pending[symbol] < 300
                 and not already_external)  # nunca adoptar externas
```

---

## 8. Infraestrutura e Operações

### Servidor
- **VPS:** `178.105.52.219`
- **OS:** Ubuntu/Debian | **Python:** 3.13
- **Repositório:** `/root/blank-app` | **Bot log:** `/root/claw.log`
- **Branch:** `main` (auto-deploy activo)
- **Auto-deploy:** `auto_deploy.sh` — detecta novos commits em `main`, reinicia bot

### Credenciais
Guardadas em `~/.bashrc` no VPS (NUNCA mostrar no chat):
```
TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, BINANCE_API_KEY, BINANCE_API_SECRET
```
Em `/etc/environment` para carregamento automático por nohup/SSH.

### Binance API
- **Tipo:** Futures USDC-M (Cross Margin)
- **Moeda de margem:** BNFCR (Europa) — o código aceita USDC e BNFCR
- **IP whitelisted:** `178.105.52.219`
- **Isolated margin:** não disponível na Binance Europa — sempre Cross Margin

### Arranque do bot
```bash
# No Termux (deploy automático via auto_deploy.sh no VPS)
cd ~/blank-app && git pull origin main
pkill -f "python.*main.py"; sleep 2
cd ~/blank-app/claw_v8 && nohup python main.py > ~/claw.log 2>&1 &
```

### Kill switch
```bash
touch /root/blank-app/claw_v8/KILL_SWITCH
# Bot cancela todas as algo orders, fecha posições do bot, encerra
```

### Reset circuit breaker (SQLite)
```bash
sqlite3 ~/blank-app/claw_v8/claw_v8.db \
  "UPDATE bot_state SET value='0' WHERE key IN ('bloqueado_ate','perdas_seguidas');
   UPDATE bot_state SET value='0.0' WHERE key='loss_dia';"
```

---

## 9. Ajustes de Configuração — Histórico

| Data | Parâmetro | Antes | Depois | Motivo |
|------|-----------|-------|--------|--------|
| Inicial | Capital máx | 50 USDC | 75 USDC | Aumentar exposição |
| v7 | Max posições | 3 | 5→4 | Controlo de risco |
| v7 | AVAXUSDC | Activo | Removido | -0.83 BNFCR, 2/3 emergências |
| v8 | recvWindow | 5s | 10s | Tolerância timestamp |
| Mai-13 | STOCH_VETO_SHORT | 5.0 | **2.5** | Apanhar SHORTs em quedas |
| Mai-13 | ADX mínimo | 25 | **22.5** | Menos falsos MORTO |
| Mai-16 | volume_ok() | volumes[-1] | **volumes[-2]** | Vela em formação = ~0 volume → VETO_VOL em tudo |
| Mai-16 | volume threshold | 1.0× | **0.8×** | Menos restritivo |
| Mai-18 | RATIO_ALVO | 2.0 | **3.0** | TP mais longe = ganhos maiores |
| Mai-18 | PARTIAL_TP_RATIO | 0.5 | **0.67** | TP1 dispara a 2R (era 1R) |
| Mai-18 | PARTIAL_TP_QTY | 50% | **33%** | Deixa mais posição no runner |
| Mai-18 | EMERGENCY_ROI_CUT | -4.0% | **-5.5%** | Mais espaço ao trade |
| Mai-18 | TP2 | não existia | **3R, fecha 33%** | Runner com lock de lucro |
| Mai-18 | Capital máx bot | 75 USDC | **300 USDC** | Escala ao saldo real |
| Mai-18 | Risco por trade | 3 USDC | **5 USDC** | Proporcional ao capital |
| Mai-18 | Alavancagem | 5× | **6×** | Mais exposição controlada |
| Mai-18 | Max trades | 4 | **5** | Proporcional ao capital |
| Mai-18 | Loss diário | 7.5 USDC | **15 USDC** | Proporcional ao capital |
| Mai-18 | MARGIN_RATIO_MAX | 50% | **35%** | Protecção mais cedo |
| Mai-18 | MAX_DRAWDOWN_PCT | n/a | **25%** | Fecha tudo se PnL aberto > -25% saldo |
| Mai-18 | TOP_N_FUTURES | 20 | **150** | Mais oportunidades |
| Mai-23 | ROI_TP_IMEDIATO | n/a | **7%** | Fecha imediatamente se ROI alto |
| Mai-23 | TIME_TP_MIN_MIN | 30 min | **10 min** | Menos tempo de espera |
| Mai-23 | Profit lock dist. | lock actual | **lock anterior** | Evitar rejeição Binance <0.1% mark |
| Mai-23 | get_margin_ratio | conta inteira | **só USDC/BNFCR** | USDT-M não afecta guards do bot |
| Mai-23 | Guard liquidação | n/a | **> 50% global** | Fecha posições a positivo |

---

## 10. Análises Fundamentais

### LAB Token — 🔴 NÃO COMPRAR
- Multi-chain trading terminal com produto real, mas:
- ZachXBT: fundador Vova Sadkov manipulou mercado em Bitget, Bybit, Binance, OKX
- Insider wallet depositou **40M LAB (~$13.6M)** em Bitget
- Apenas **7.7%** do supply em circulação; 690M tokens locked
- Pump +537% em 1 semana → crash 65% em horas

### SUI Token — 🟡 ACUMULAR EM DCA
- Layer 1 Mysten Labs, modelo objectos, processamento paralelo, linguagem Move
- TVL $2.6B (Out 2025), actualmente ~$570M | Incluído no Bitwise ETF
- Próximo unlock Jun 2026 = apenas 0.14% do supply
- **Estratégia DCA:**

| Entrada | % do capital |
|---------|-------------|
| ~$1.12 | 25% |
| ~$0.90 | 25% |
| ~$0.75 | 25% |
| Reserva | 25% |

---

## 11. Portfolio — Histórico

### Evolução do Portfolio

| Data | Tangem | Invest | Robinhood | Binance | Total aprox. | Δ |
|------|--------|--------|-----------|---------|--------------|---|
| 2026-05-03 | $3,749 | €882 + €718 crypto | — | $220 | **~€5,219** | base |
| 2026-05-10 | $4,064 | €1,303 + €569 ETF | — | €770 | **~€6,189** | +18.6% |
| 2026-05-14 | $4,290 | €1,323 | €491+€221 | — | **~€6,601** | +26.5% |
| 2026-05-16 | $4,080 | €1,299 | €695 | — | **~€6,393** | +22.5% |
| 2026-06-01 | $3,726 | €1,465 | €606 | ~$57 | **~€5,420** | +3.9% |

> Pico máximo: €6,601 a 2026-05-14. Correção de Jun explicada por BTC -8.9% ($77,960→$71,027).
> Invest subiu €166 (+12.8%) vs Mai-16 apesar da correção cripto — diversificação a funcionar.

---

### Snapshot 2026-05-03
| Carteira | Valor |
|----------|-------|
| Binance Spot | $220 |
| Tangem Wallet | $3,749 |
| Invest Stocks | €882 |
| Invest Crypto | €718 |
| **Total aprox.** | **€5,219** |

### Snapshot 2026-05-10
| Carteira | Valor |
|----------|-------|
| Tangem Wallet | $4,064 |
| Invest Stocks | €1,303 |
| Invest Crypto | €15 |
| Invest ETF USD | €569 |
| Nova Carteira Crypto | ~$95 |
| Binance EUR | €770 |
| **Total aprox.** | **€6,189** |

### Snapshot 2026-05-14
| Carteira | Valor |
|----------|-------|
| Tangem Wallet | $4,290 |
| Invest Stocks | €1,323 |
| Bux ETF/Stocks | €491 |
| Bux Crypto (PAXG) | €221 |
| **Total aprox.** | **€6,601** |

### Snapshot 2026-05-16
| Carteira | Valor | Δ |
|----------|-------|---|
| Tangem Wallet | $4,080 | -4.9% |
| Invest Stocks | €1,299 | -1.8% |
| Robinhood (ANET+ETN+PAXG) | €695 | -2.4% |
| **Total aprox.** | **€6,393** | **-3.2%** |

### Activos Tangem (2026-05-16)
| Activo | Qtd | Preço | Valor |
|--------|-----|-------|-------|
| BTC | 0.0348942 | $77,960 | $2,720 |
| ETH | 0.44191314 | $2,176 | $961 |
| SOL | 3.11745595 | $86.05 | $268 |
| XRP | 84.566087 | $1.41 | $119 |

### Bot Binance Futures (2026-05-23)
- Saldo: ~296 USDC
- PnL sessão: +23.56 USDC

---

### Snapshot 2026-06-01
| Carteira | Valor | Δ vs Mai-16 |
|----------|-------|-------------|
| Tangem Wallet | $3,726 | -8.7% |
| Invest (Trading 212) | €1,465 | +12.8% |
| Robinhood | €606 | -12.8% |
| Binance Futures (bot) | ~$57 USDC | — |
| **Total aprox.** | **~€5,420** | **-15.2%** |

> Nota: queda principal explicada pela correcção do BTC ($77,960 → $71,027, -8.9%) e das altcoins na Tangem.

#### Activos Tangem (2026-06-01)
| Activo | Qtd | Preço | Valor |
|--------|-----|-------|-------|
| BTC | 0.0348942 | $71,027 | $2,478 |
| ETH | 0.44191314 | $1,968 | $870 |
| SOL | 3.25616997 | $79.68 | $259 |
| XRP | 84.566087 | $1.29 | $109 |
| LINK | 0.96250677 | $8.93 | $9 |
| DOT | 1.00 | $1.13 | $1 |
| **Total** | | | **$3,726** |

#### Invest — Trading 212 (2026-06-01) — Total €1,465
| Activo | Qtd | Valor | P&L |
|--------|-----|-------|-----|
| VWCE (Vanguard FTSE All-World) | 3.695 | €606 | +€20 (+3.4%) |
| CEG (Constellation Energy) | 0.954 | €223 | -€15 (-6.3%) |
| RGTI (Rigetti Computing) | 9.142 | €198 | +€20 (+11.3%) |
| FTNT (Fortinet) | 0.923 | €115 | +€22 (+24.3%) |
| DXYZ (Destiny Tech100) | 3.360 | €142 | -€8 (-5.5%) |
| CMP (Compass Minerals) | 3.353 | €94 | +€9 (+10.1%) |
| LEU (Centrus Energy) | 0.552 | €87 | -€14 (-13.9%) |
| Mês passado | | +€51,42 | +3.9% |

#### Robinhood (2026-06-01) — Total €606
| Activo | Qtd |
|--------|-----|
| ANET (Arista Networks) | 2.11288 |
| SMH (VanEck Semiconductor ETF) | 0.52006 |
| ETN (Eaton Corporation) | 0.00567 |
| Buying power | €12,59 |



### Monitorização
```bash
# Log em tempo real
ssh root@178.105.52.219 "tail -f /root/claw.log"

# Últimas 30 linhas
ssh root@178.105.52.219 "tail -30 /root/claw.log"

# Analytics de performance
ssh root@178.105.52.219 "cd /root/blank-app/claw_v8 && python3 analytics.py"

# Processos activos
ssh root@178.105.52.219 "ps aux | grep python | grep -v grep"
```

### Gestão do bot
```bash
# Reiniciar após alteração de código
ssh root@178.105.52.219 "cd /root/blank-app && git pull && \
grep -E 'export.*(TELEGRAM|BINANCE)' /root/.bashrc > /tmp/ce && \
bash -c 'source /tmp/ce; kill \$(cat /root/claw.pid) 2>/dev/null; \
PYTHONUNBUFFERED=1 nohup python3 claw_v8/main.py > /root/claw.log 2>&1 & \
echo \$! > /root/claw.pid' && sleep 3 && tail -5 /root/claw.log"

# Kill switch de emergência
ssh root@178.105.52.219 "touch /root/blank-app/claw_v8/KILL_SWITCH"

# Reset circuit breaker
ssh root@178.105.52.219 "sqlite3 ~/blank-app/claw_v8/claw_v8.db \
  \"UPDATE bot_state SET value='0' WHERE key IN ('bloqueado_ate','perdas_seguidas'); \
    UPDATE bot_state SET value='0.0' WHERE key='loss_dia';\""
```

### Spot Scanner
```bash
# Análise individual
python3 claw_v8/spot_scanner.py SUI

# Top 100 pares
python3 claw_v8/spot_scanner.py --top 100

# Daemon 4h
python3 claw_v8/spot_scanner.py --daemon --top 100
```

### Git
```bash
# Push de alterações (vai para main → auto-deploy no VPS)
git add -p && git commit -m "mensagem" && git push origin main
```

---

## 13. Sessões de Trabalho

### Sessão 2026-05-13

**Tópicos:** Spot Scanner multi-timeframe, monitorização posições externas, migração Termux→VPS, ajustes estratégia.

**Desenvolvimentos:**
- `claw_v8/spot_scanner.py` criado: 1W/1D/4H, EMA/RSI/ADX/Supertrend/Volume/DDatH/Fear&Greed, score→decisão, daemon 4h, alertas Telegram, 8 workers paralelos
- Monitorização posições externas em `main.py`: detecta, regista, alerta em -5%/-3%/+3%/+5%/+10%/+15%/+20%, nunca gere
- Migração VPS: IP fixo resolve problema de bloqueios Binance (IP do Termux mudava com WiFi)
- Fix timestamp: `recvWindow` 5s→10s, `_is_timestamp_error()`, retry automático
- Credenciais em `/etc/environment` para carregamento via nohup/SSH
- **STOCH_VETO_SHORT** 5.0→2.5: apanhar SHORTs com StochRSI entre 2.5 e 5.0
- **ADX mínimo** 25→22.5: menos falsos MORTO

---

### Sessão 2026-05-16

**Tópicos:** Bug volume, resumo horário, portfolio.

**Desenvolvimentos:**
- Fix crítico `volume_ok()`: usava `volumes[-1]` (vela em formação, ~0 volume) → VETO_VOL bloqueava todos os trades. Corrigido para `volumes[-2]`
- Threshold volume 1.0×→0.8× (menos restritivo)
- Resumo horário via Telegram (posições abertas + pares TRENDING)
- Portfolio: Tangem $4,080 | Invest €1,299 | Robinhood €695 | Total ~€6,393

---

### Sessão 2026-05-18 (parte 1)

**Tópicos:** Diagnóstico de performance, overhaul dos exits.

**Diagnóstico:**
- Expectância -€0.20/trade: ganhos ~€1.75 vs perdas ~€3.00
- Benchmarking: Freqtrade, Jesse, UT Bot, r/algotrading → padrão "2R-3R-runner"

**Desenvolvimentos:**
- Fix: tabela `positions` vazia — sync não chamava `db_open_position()`. Corrigido com upsert em `close_position_db()`
- Overhaul exits: TP1 a 2R (fecha 33% → breakeven), TP2 a 3R (fecha 33% → +1R), runner 34%
- RATIO_ALVO 2→3 | PARTIAL_TP_RATIO 0.5→0.67 | EMERGENCY_ROI_CUT -4%→-5.5%
- `cancel_order()` adicionado em `exchange.py`
- Expectância esperada: -€0.20 → +€1.44 por trade

---

### Sessão 2026-05-18 (parte 2)

**Tópicos:** Escala de capital, pares dinâmicos, protecções, fix endpoint.

**Desenvolvimentos:**
- Capital 75→300 USDC | Risco 3→5 | Alavancagem 5→6 | Trades 4→5 | Loss diário 7.5→15
- `get_top_futures_symbols(n=150, min_days=30)` — top 150 USDC-M por volume
- 4 camadas de protecção: emergência -5.5%, drawdown 25%, margem >35%, BTC crash >3%
- **Fix crítico endpoint:** todas as ordens stop usavam `/fapi/v1/algoOrder` (endpoint errado) → erro "algotype". Corrigido para `/fapi/v1/order` com `type` em vez de `orderType`
- Caso ZECUSDC: stop falhou (algotype error) → TEMPO+LUCRO fechou a +€11.40
- `git pull --rebase` para resolver branches divergentes no VPS

---

### Sessão 2026-05-23

**Tópicos:** Bugs críticos, análise ZEC, guards novos.

#### Bug 1 — TIME_TP não fechava posição lucrativa
- NEAR a +5.58% ROI não fechou → virou -6.33% (-3.48 USDC)
- Causa: requeria 30min E ROI≥5% simultaneamente; NEAR atingiu +5.58% aos 23min
- Fix: `ROI_TP_IMEDIATO=7%` (fecha instantaneamente) + `TIME_TP_MIN_MIN=10` (era 30)

#### Bug 2 — Profit lock stop falhava silenciosamente
- Stop colocado a ~mark price → Binance rejeita stops a < ~0.1% do mark price
- Fix: usa nível ANTERIOR do lock (garante distância); retry 3× com buffer +0.15%

#### Bug 3 — Bot fechou posição manual ZEC SHORT (45x, +50 USDC vs potencial +145 USDC)
- Causa: `abrir_trade` escrevia `pending_sync` ANTES de verificar se posição existia → sync adoptou posição do utilizador como "órfã do bot" → TIME_TP disparou
- Fix 1 (`execution.py`): verificar `trades_abertos` e `posicoes_externas` ANTES de escrever `pending_sync`
- Fix 2 (`main.py`): `is_bot_orphan` requer `not already_external`

#### Bug 4 — Guard de margem afectado por posições USDT-M
- `get_margin_ratio()` lia `totalMaintMargin/totalMarginBalance` da CONTA INTEIRA
- TAGUSDT 30x com perdas → rácio global > 35% → guard fechou trades do bot
- Provável liquidação cruzada Binance fechou posições USDT-M ao mesmo segundo (07:43)
- Fix: `get_margin_ratio()` agora lê só activo `USDC`/`BNFCR` via `assets[]`

#### Novo — Guard de liquidação global
- `get_margin_ratio_global()`: lê conta inteira
- Alertas em escada: 🟡 40% / 🟠 55% / 🔴 70%
- Se > 50%: fecha TODAS as posições a positivo (bot + manuais) para libertar margem
- Corre sempre, mesmo sem trades do bot abertos

#### Análise trading manual ZEC
- ZEC SHORT 15x, entrada 601.34 → fechou com SL a 586 (+49 USDC bruto)
- Nova SHORT 5x, entrada 588.14
  - SL recomendado: 597 (~1.5% de margem, ~-11 USDC risco)
  - Trailing stop: activation 575, callback 1.5%
- Explicação UI Binance: "Valor da Posição" com activation = nocional ao preço de activação (não o saldo)

---

## 14. Changelog Técnico

### 🔴 Bug crítico — API Binance (endpoint de stops)
**Problema:** Binance migrou ordens condicionais de `/fapi/v1/order` para `/fapi/v1/algoOrder`. Bot usava endpoint antigo → todos os stops falhavam silenciosamente.

**Fix:** URL, campo `type`→`orderType`, `algoType: CONDITIONAL`, `algoId` em vez de `orderId`, `cancel_algo_order()` via `DELETE /sapi/v1/algo/futures/order`.

---

### 🔴 Bug — GUARDA 25% disparava com perdas mínimas
**Problema:** `get_balance()` devolve `availableBalance` (~9 USDC com posições abertas) → 25% × 9 = 2.25 USDC de limite.

**Fix:** `get_wallet_balance()` usa `totalMarginBalance`. Limite correcto: 25% × 37 USDC = ~9.25 USDC.

---

### 🔴 Bug — `place_stop_market` erro "algotype"
**Problema:** Parâmetros enviados como query string em POST `/fapi/v1/algoOrder`. Binance exige body.

**Fix:** `data=signed` (body), fallback para `params=` se erro -1102.

---

### 🔴 Bug — Lookahead bias
**Problema:** `closes[-1]` era vela ainda a formar. Sinais calculados com dados parciais.

**Fix:** Scan usa `klines[:-1]` (velas fechadas).

---

### ✅ Melhoria — tickSize / PRICE_PRECISION
`PRICE_PRECISION` separado de `SYMBOL_PRECISION`. Stops e TPs formatados com casas decimais correctas por par.

---

### ✅ Melhoria — workingType=MARK_PRICE
Adicionado a `place_stop_market` e `place_take_profit`. Protege contra wicks artificiais no last price.

---

### ✅ Melhoria — Kill switch por ficheiro
`touch ~/blank-app/claw_v8/KILL_SWITCH` → cancela algo orders, fecha posições bot, encerra.

---

### ✅ Melhoria — Pre-signal pipeline
Filtros reordenados: locais (sem API) → API leve (cached) → API pesada (HTF 4H/1H). Reduz chamadas à Binance.

---

### ✅ Expansão — USDC-M + USDT-M
`get_top_futures_symbols()` aceita USDC-M. Filtro idade: 30 dias. TOP_N_FUTURES: 150.

---

### ✅ Backtesting engine
`claw_v8/backtest.py`: descarrega klines 5m/1H/4H, aplica signal_trending + HTF alignment, simula SL/TP/partial TP/emergência, relatório completo.

---

## 15. Lições Aprendidas

1. **Conta cross-margin é partilhada.** USDT-M e USDC-M partilham o mesmo pool de margem. 30x TAGUSDT pode liquidar toda a conta incluindo trades do bot.

2. **Binance rejeita stops a < ~0.1% do mark price.** O profit lock usa nível anterior, não o actual.

3. **`pending_sync` deve ser escrito DEPOIS de verificar se já existe posição.** A ordem do código é crítica para não adoptar posições manuais.

4. **Nunca usar `reduceOnly=true` nesta conta.** Sempre `closePosition=true`. Só pode haver um STOP_MARKET closePosition por símbolo.

5. **O bot fechou ZEC manual (+50 USDC vs potencial +145 USDC).** Custo real de um bug de 2 linhas.

6. **O bot fechou SUIUSDC orphan (-8.76 USDC).** Origem: bug no pending_sync.

7. **Auto-deploy via `main`.** Todos os commits DEVEM ir para `main` para o auto-deploy actuar. Branch `claude/setup-project-structure-3xwuR` era o dev branch antigo — não é usado pelo VPS.

8. **TIME_TP com 30min mínimos era demasiado conservador.** Reduzido para 10min + ROI_TP_IMEDIATO 7% para capturas rápidas.

9. **`volumes[-1]` = vela em formação ≈ 0.** Usava dados incorrectos e bloqueava todos os trades via VETO_VOL.

10. **Trailing stop em SHORTs:** activation ABAIXO do preço actual; callback = quanto o preço sobe do mínimo para disparar. Nunca usar activation igual ao low já testado.

---

*Última actualização: 2026-05-23*
*Bot activo no VPS `178.105.52.219`, branch `main`*
