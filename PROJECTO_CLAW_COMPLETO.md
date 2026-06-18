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
| **v8.0** | `claw_v8/` | **Activo no Termux** | Modular + SQLite + Filter Attribution |

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
|-----------| ------|
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
|-----------|---------------|---------------|
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
|-----------|-----------|
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
|--------| ---------|
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

### LEU (Centrus Energy) — 🟢 MANTER — TESE DE LONGO PRAZO

**O que é:** Única empresa norte-americana com capacidade activa de enriquecimento de urânio, incluindo HALEU (High-Assay Low-Enriched Uranium) — combustível crítico para os reactores nucleares de próxima geração (SMR, reactores avançados).

**Pontos positivos:**
- Monopólio de facto nos EUA para HALEU — sem concorrência doméstica no curto prazo
- Contratos directos com o Departamento de Energia (DOE) para produção de HALEU — receita garantida pelo governo
- A lei de proibição de urânio russo (2024) obrigou as utilities americanas a procurar alternativas domésticas — Centrus beneficia directamente
- Renascimento nuclear global: SMR da NuScale, TerraPower, Oklo — todos precisam de HALEU
- A IA está a aumentar o consumo energético nos data centers → energia nuclear volta a ser prioritária nos EUA (Microsoft, Google já assinaram contratos com centrais nucleares)

**Riscos:**
- Small cap (~$400M market cap) — muito sensível a notícias e contratos
- Receita concentrada em contratos governamentais — atrasos em renovações afectam o preço
- Ciclo nuclear é longo: os SMR mais avançados não estarão operacionais antes de 2030-2032
- Posição pequena (€8.13) — mesmo com upside de 3-5x, o impacto no portfólio é limitado

**Estratégia recomendada:** Manter. A tese é sólida mas de horizonte longo (3-5 anos). Considerar reforçar para €20-30 se o DOE anunciar extensão ou expansão dos contratos HALEU. Não é para trading — é para deixar quieto.

---

### FTNT (Fortinet) — 🟢 MANTER + ACUMULAR EM DIPS

**O que é:** Líder mundial em firewalls e segurança de rede (FortiGate). Caminha para plataforma SASE/zero-trust completa — um único vendor para firewall, SD-WAN, endpoint e cloud security.

**Pontos positivos:**
- Billings a recuperar após abrandamento 2023-2024: crescimento voltou a acelerar em 2025
- Receita recorrente (subscriptions + suporte) já >50% do total — modelo previsível
- Free cash flow margin ~25-30% — empresa extremamente eficiente
- Setor em crescimento estrutural: IA a criar novas superfícies de ataque, ransomware em alta, zero-trust a tornar-se mandatório nas empresas
- No teu portfólio desde ~Abr-2026: +14.35% já registado; AutoInvest de €1/dia activo

**Riscos:**
- Competição da Palo Alto Networks (PANW) que está mais agressiva em bundling e a oferecer produto gratuito para ganhar quota
- Valuation não barato: ~7-8x revenue — exige execução consistente
- Ciclo de renovação de firewalls físicos pode ser mais lento nos próximos 2 anos

**Estratégia recomendada:** Manter e continuar AutoInvest diário. Em correções de -10 a -15% adicionar parcela extra. É a tua melhor posição individual em termos de risco/retorno no médio prazo (2-3 anos).

---

### VWCE (Vanguard FTSE All-World) — 🟢 CORE — AUMENTAR SEMPRE

**O que é:** ETF UCITS que replica o FTSE All-World Index — ~3,700 empresas de 50 países. ~63% EUA, ~6% Japão, ~4% UK, resto do mundo. TER: 0.22%.

**Pontos positivos:**
- Diversificação máxima num único instrumento — elimina risco idiossincrático
- Retorno histórico ajustado ~7-10% a.a. no longo prazo
- Acumula automaticamente dividendos (acc) — eficiente fiscalmente
- Já é a tua maior posição (€867) e é assim que deve ser

**Pontos a considerar:**
- Concentração elevada em mega-caps US tech (Nvidia, Apple, Microsoft, Amazon, Google = ~18% do índice) — que é um risco mas também o que está a puxar os retornos
- Em correções de mercado cai com tudo (2022: -18%) — mas é o melhor ativo para DCA nesses momentos

**Estratégia recomendada:** Esta é a âncora do portfólio. Devias ter AutoInvest em VWCE pelo menos igual ao de FTNT — idealmente mais. Em qualquer mês em que não saibas onde investir, vai para VWCE. Meta: crescer esta posição até representar 50%+ do portfólio de stocks (actualmente ~65% do T212, já bem posicionado).

---

### IONQ (IonQ) — 🟡 MANTER PEQUENO — NÃO AUMENTAR JÁ

**O que é:** Empresa de computação quântica pura (pure play), NYSE. Usa arquitectura de iões aprisionados (trapped-ion) — tecnologia diferenciada vs qubits supercondutores da IBM/Google.

**Pontos positivos:**
- Crescimento de receita ~100% em 2025 (base pequena, mas momentum real)
- Contratos com US Air Force, US Army, governo federal — validação de performance
- Parceria com AWS, Azure, Google Cloud — os 3 grandes hiperescalers
- Arquitectura trapped-ion tem vantagem em fidelidade de qubits vs concorrentes

**Riscos:**
- Pré-lucro: continuam a queimar cash (~$50-70M/ano)
- Computação quântica com impacto comercial real: estimado 2028-2032 no mínimo
- Volatilidade extrema: o stock já fez -60% e +200% em períodos de 6 meses
- Competição de IBM, Google, Microsoft com muito mais recursos
- A tua posição actual (€3.08) é micro — o upside em euros é insignificante mesmo que o stock duplique

**Estratégia recomendada:** Manter como "lottery ticket" — a posição de €3 está bem. Considerar aumentar para €20-30 se e quando reportarem receita >$100M com path credível para breakeven (provavelmente 2027). Não adicionar agora só por especulação.

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
|---------| -------------|
| Agora ~$1.12 | 25% |
| Se cair ~$0.90 | 25% |
| Se cair ~$0.75 | 25% |
| Reserva | 25% |

---

## 8. Portfolio

### Snapshot 2026-05-03
| Carteira | Valor |
|----------| ------|
| Binance Spot | $220 |
| Tangem Wallet | $3,749 |
| Invest Stocks | €882 |
| Invest Crypto | €718 |
| Invest ETF USD | €105 |
| **Total aprox.** | **€5,219** |

### Snapshot 2026-05-06
| Carteira | Valor |
|----------| ------|
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
|--------|-----|----------|
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
|--------|-----|-------|----------|
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

### Snapshot 2026-06-01
| Carteira | Moeda | Valor | Δ vs 16 Mai |
|----------|-------|-------|-------------|
| Tangem Wallet | USD | $3,726 | -$354 (-8.7%) |
| Invest (Trading 212) | EUR | €1,465 | +€166 (+12.8%) |
| Robinhood | EUR | €606 | -€89 (-12.8%) |
| Binance Futures (bot) | USD | ~$57 USDC | — |
| **Total aprox.** | | **~€5,420** | — |

*Nota: BTC corrigiu de $77,960 → $71,027 (-8.9%), arrastando toda a Tangem. Invest subiu €166 graças a VWCE e RGTI — diversificação a amortecer a correção cripto. PAXG e ETN quase totalmente vendidos no Robinhood; SMH adicionado.*

### Activos Tangem (2026-06-01)
| Activo | Qtd | Preço | Valor USD | Δ vs 16 Mai |
|--------|-----|-------|-----------|-------------|
| BTC | 0.0348942 | $71,027 | $2,478 | -$242 |
| ETH | 0.44191314 | $1,968 | $870 | -$91 |
| SOL | 3.25616997 | $79.68 | $259 | -$9 |
| XRP | 84.566087 | $1.29 | $109 | -$10 |
| LINK | 0.96250677 | $8.93 | $9 | — |
| DOT | 1.00 | $1.13 | $1 | — |
| **Total** | | | **$3,726** | **-$354** |

### Invest — Trading 212 (2026-06-01)
| Ticker | Qtd | Valor EUR | Var |
|--------|-----|-----------|-----|
| VWCE (Vanguard FTSE All-World) | 3.695 | €605.66 | +3.35% |
| CEG (Constellation Energy) | 0.954 | €223.10 | -6.30% |
| RGTI (Rigetti Computing) | 9.142 | €198.37 | +11.32% |
| FTNT (Fortinet) | 0.923 | €114.79 | +24.26% |
| DXYZ (Destiny Tech100) | 3.360 | €141.56 | -5.48% |
| CMP (Compass Minerals) | 3.353 | €93.97 | +10.05% |
| LEU (Centrus Energy) | 0.552 | €87.17 | -13.89% |
| **Total** | | **€1,464.62** | **+€51 mês passado (+3.9%)** |

*Vendidos vs Mai-16: PLTR, HRS, HO (Thales), Kongsberg. Adicionados: DXYZ, mais VWCE (+1.85 unid.), mais RGTI (+0.7 unid.), mais FTNT (+0.18 unid.).*

### Robinhood (2026-06-01)
| Activo | Qtd | Preço | Valor aprox. |
|--------|-----|-------|-------------|
| ANET (Arista Networks) | 2.11288 | $169.62 | ~€317 |
| SMH (VanEck Semiconductor ETF) | 0.52006 | $608.28 | ~€281 |
| ETN (Eaton) | 0.00567 | $400.92 | ~€2 |
| Buying power | — | — | €12.59 |
| **Total** | | | **€605.97** |

*Principais mudanças vs Mai-16: PAXG liquidado, ETN quase totalmente vendido (0.45→0.006), SMH adicionado como nova posição principal.*

---

### Snapshot 2026-06-03
| Carteira | Moeda | Valor | Δ vs 01 Jun |
|----------|-------|-------|-------------|
| Tangem Wallet | USD | $3,415 | -$311 (-8.3%) |
| Invest (Trading 212) | EUR | €1,473 | +€8 (+0.6%) |
| Robinhood (ANET) | EUR | €335 | +€18 (+5.7%) |
| Binance Futures (bot) | USD | ~$154 USDC | — |
| **Total aprox.** | | **~€5,088** | — |

*Nota: BTC caiu de $71,027 → $65,244 (-8.1%), ETH -8.5%, SOL -10.1%. Tangem sofreu nova corrida descendente. Trading 212 estável graças a FTNT (+14.98%) e VWCE (+2.29%). Portfólio Trading 212 reorganizado: DXYZ, CMP, LEU removidos; VWCE reforçado (3.695→5.327), SMH migrado do Robinhood, RGTI reduzido (9.142→4.271).*

### Activos Tangem (2026-06-03)
| Activo | Qtd | Preço | Valor USD | Δ vs 01 Jun |
|--------|-----|-------|-----------|-------------|
| BTC | 0.0348942 | $65,244 | $2,277 | -$201 |
| ETH | 0.44191314 | $1,798 | $795 | -$75 |
| SOL | 3.25711846 | $71.72 | $234 (APY 5.74%) | -$25 |
| XRP | 84.566087 | $1.20 | $102 | -$7 |
| LINK | 0.96250677 | $8.19 | $8 | -$1 |
| DOT | 1.00 | $1.09 | $1 | — |
| **Total** | | | **$3,415** | **-$311** |

### Invest — Trading 212 (2026-06-03)
| Ticker | Qtd | Valor EUR | Var dia |
|--------|-----|-----------|---------|
| VWCE (Vanguard FTSE All-World) | 5.32660687 | €874.31 | +2.29% |
| CEG (Constellation Energy) | 0.95436341 | €220.07 | -7.58% |
| FTNT (Fortinet) | 1.45056673 | €183.19 | +14.98% |
| SMH (VanEck Semiconductor ETF) | 1.05989092 | €107.84 | +0.89% |
| RGTI (Rigetti Computing) | 4.27129751 | €87.98 | +5.67% |
| **Total** | | **€1,473.39** | |

*Mudanças vs Jun-01: DXYZ, CMP, LEU vendidos. VWCE reforçado (+1.63 unid.), FTNT reforçado (+0.53 unid.), SMH migrado do Robinhood (+0.54 unid.), RGTI reduzido (-4.87 unid.).*

### Robinhood (2026-06-03)
| Activo | Qtd | Preço | Valor EUR | Retorno Total |
|--------|-----|-------|-----------|---------------|
| ANET (Arista Networks) | 2.23166 | $173.85 | €334.61 | +€54.20 (+19.33%) |

*Custo médio ANET: €125.65/acção. SMH migrado para Trading 212.*

---

### Snapshot 2026-06-12
| Carteira | Moeda | Valor | Δ vs 03 Jun |
|----------|-------|-------|-------------|
| Tangem Wallet | USD | $3,313 | -$102 (-3.0%) |
| Invest (Trading 212) | EUR | €1,328 | -€145 (-9.8%) |
| Robinhood | EUR | €678 | +€343 (+102%) |
| Binance Futures (bot) | USD | ~$150 USDC | — |
| **Total aprox.** | | **~€5,231** | **+€143 (+2.8%)** |

*Nota: Tangem em queda ligeira (BTC $65,244→$63,832, ETH -6.6%). Trading 212 perdeu €145 com RGTI e SMH removidos e CEG a cair -13.7%. Robinhood duplicou com SMH de volta + QQQ e VTI adicionados. Portfolio altamente diversificado: 13 posições em Trading 212, 5 no Robinhood.*

### Activos Tangem (2026-06-12)
| Activo | Qtd | Preço | Valor USD | Δ vs 03 Jun |
|--------|-----|-------|-----------|-------------|
| BTC | 0.0348942 | $63,832 | $2,227 | -$50 |
| ETH | 0.44191314 | $1,680 | $743 | -$52 |
| SOL | 3.26187746 | $67.72 | $221 (APY 5.77%) | -$13 |
| XRP | 84.566087 | $1.15 | $97 | -$5 |
| Base ETH | 0.009798 | $1,680 | $16 | novo |
| LINK | 0.96250677 | $7.93 | $8 | — |
| DOT | 1.00 | $0.97 | $1 | — |
| **Total** | | | **$3,313** | **-$102** |

*Novo: Base ETH (0.009798 ETH na rede Base).*

### Invest — Trading 212 (2026-06-12)
| Ticker | Qtd | Valor EUR | Var |
|--------|-----|-----------|-----|
| VWCE (Vanguard FTSE All-World) | 5.34529036 | €866.74 | +1.04% |
| CEG (Constellation Energy) | 0.95436341 | €205.46 | -13.71% |
| FTNT (Fortinet) | 1.45056673 | €182.19 | +14.35% |
| ALOY (REalloys) | 2.25364349 | €31.43 | +12.41% |
| ASTS (AST SpaceMobile) | 0.09750445 | €7.32 | -8.39% |
| LEU (Centrus Energy) | 0.05773685 | €8.13 | +1.75% |
| MRVL (Marvell Technology) | 0.03434547 | €8.48 | +6.13% |
| CRWV (CoreWeave) | 0.03606306 | €3.22 | +7.33% |
| SOLS (Solstice Advanced Materials) | 0.04329377 | €3.10 | +3.33% |
| IONQ (IonQ) | 0.0601098 | €3.08 | +2.67% |
| AMTM (Amentum Holdings) | 0.15404932 | €3.04 | +1.33% |
| S (SentinelOne) | 0.23462755 | €2.98 | -0.67% |
| FB2A (Meta Platforms) | 0.00600559 | €2.95 | -1.67% |
| **Total** | | **~€1,328** | |

*Removidos vs Jun-03: RGTI, SMH europeia. Adicionados: ALOY, ASTS, MRVL, CRWV, SOLS, IONQ, AMTM, S, FB2A.*

### Robinhood (2026-06-12) — €678.19 total
| Activo | Qtd | Preço |
|--------|-----|-------|
| ANET (Arista Networks) | 2.3034 | $163.04 |
| SMH (VanEck Semiconductor ETF) | 0.56218 | $618.76 |
| QQQ (Invesco Nasdaq-100 ETF) | 0.06418 | $720.05 |
| VTI (Vanguard Total Market ETF) | 0.00319 | $366.51 |
| ETN (Eaton) | 0.00273 | $394.15 |

*SMH americana mantida/aumentada no Robinhood (versão diferente da SMH europeia que saiu do T212). Adicionados QQQ e VTI (ETFs de índice amplo).*

---

### Snapshot 2026-06-15
| Carteira | Moeda | Valor | Δ vs 12 Jun |
|----------|-------|-------|-------------|
| Tangem Wallet | USD | $3,542 | +$229 (+6.9%) |
| Invest (Trading 212) | EUR | €1,466 | +€138 (+10.4%) |
| Robinhood | EUR | €698 | +€20 (+3.0%) |
| Binance Futures (bot) | USD | ~$165 USDC | +$15 |
| **Total aprox.** | | **~€5,574** | **+€343 (+6.2%)** |

*Nota: Mercado cripto em recuperação forte — BTC +4.8% ($63,832→$67,192), ETH +10.5%, SOL +11.9%, XRP +13.2%. Tangem recuperou $229. T212 cresceu €138 com posições significativamente reforçadas (ALOY, MRVL, IONQ, CRWV, FB2A, LEU). AutoInvest expandido para €274/mês.*

### Activos Tangem (2026-06-15)
| Activo | Qtd | Preço | Valor USD | Δ vs 12 Jun |
|--------|-----|-------|-----------|-------------|
| BTC | 0.0348942 | $67,192 | $2,345 | +$118 |
| ETH | 0.44191314 | $1,842 | $814 | +$71 |
| SOL | 3.2628276 | $75.74 | $247 (APY 5.75%) | +$26 |
| XRP | 84.566087 | $1.29 | $109 | +$12 |
| Base ETH | 0.009798 | $1,842 | $18 | — |
| LINK | 0.96250677 | $8.55 | $8 | — |
| **Total** | | | **$3,542** | **+$229** |

*DOT já não aparece na carteira (vendido ou valor negligenciável).*

### Invest — Trading 212 (2026-06-15)
| Ticker | Qtd | Valor EUR | Var | Δ qtd vs Jun-12 |
|--------|-----|-----------|-----|-----------------|
| VWCE (Vanguard FTSE All-World) | 5.40631806 | €889.88 | +2.55% | +0.06 |
| CEG (Constellation Energy) | 0.95436341 | €216.45 | -9.10% | — |
| FTNT (Fortinet) | 1.45846945 | €186.89 | +16.57% | +0.008 |
| ALOY (REalloys) | 4.06864039 | €57.82 | +5.30% | **+1.82** |
| MRVL (Marvell Technology) | 0.2011094 | €51.92 | +5.19% | **+0.167** |
| LEU (Centrus Energy) | 0.13281743 | €20.23 | +8.07% | +0.075 |
| IONQ (IonQ) | 0.24858356 | €13.48 | +3.85% | **+0.188** |
| CRWV (CoreWeave) | 0.13168071 | €12.29 | +4.06% | **+0.096** |
| DRON (Drone Acc) | 1.68690958 | €10.05 | +0.50% | novo |
| FB2A (Meta Platforms) | 0.01201983 | €6.19 | +3.17% | +0.006 |
| EBS (Emergent BioSolutions) | 0.13682567 | €0.98 | -2.00% | novo |
| **Total** | | **€1,466** | | |

*Removidos vs Jun-12: ASTS, SOLS, AMTM, S. Adicionados: DRON, EBS. AutoInvest expandido para €274/mês (novos: MRVL, META, LEU, IONQ, ALOY, EBS, CEG a €1/dia cada).*

### Robinhood (2026-06-15) — €698.42 total
| Activo | Qtd | Preço | Δ qtd vs Jun-12 |
|--------|-----|-------|-----------------|
| ANET (Arista Networks) | 2.59102 | $166.57 | +0.288 |
| SMH (VanEck Semiconductor ETF) | 0.56218 | $646.94 | — |
| QQQ, VTI, ETN | — | — | mantidos |

---

### Activos Tangem (2026-06-18)
| Activo | Qtd | Preço | Valor USD | Δ vs 15 Jun |
|--------|-----|-------|-----------|-------------|
| BTC | 0.0348942 | $63,618.57 | $2,219.92 | -$125 |
| ETH | 0.44191314 | $1,733.97 | $766.27 | -$48 |
| SOL | 3.26472832 | $70.74 | $230.93 (APY 5.75%) | -$16 |
| XRP | 84.566087 | $1.16 | $97.92 | -$11 |
| Base ETH | 0.009798 | $1,733.97 | $16.99 | -$1 |
| LINK | 0.96250677 | $7.99 | $7.69 | — |
| **Total** | | | **$3,341** | **-$201** |

### Invest — Trading 212 (2026-06-18) — €1,545.62 total
| Ticker | Qtd | Valor EUR | Var hoje |
|--------|-----|-----------|----------|
| VWCE (Vanguard FTSE All-World) | 5.67667402 | €940.68 | +3.08% |
| CEG (Constellation Energy) | 0.95877895 | €231.77 | -3.07% |
| FTNT (Fortinet) | 1.04051011 | €131.44 | +10.23% |
| MRVL (Marvell Technology) | 0.3779996 | €107.27 | +8.05% |
| LEU (Centrus Energy) | 0.44170761 | €72.88 | +4.65% |
| CRWV (CoreWeave) | 0.59074987 | €61.58 | +5.03% |

*IONQ e EBS já não aparecem — vendidos, conforme decidido. Conta total +€26.17 (+1.9%) hoje.*

### Robinhood (2026-06-18) — €709.35 total
| Activo | Qtd | Preço |
|--------|-----|-------|
| ANET (Arista Networks) | 2.95008 | $168.91 |
| SMH (VanEck Semiconductor ETF) | 0.45925 | $658.12 |

*+€13.45 (+1.93%) hoje.*

---

### Evolução do Portfólio Total
| Data | Tangem | T212 | Robinhood | Outros | **Total €** | Δ |
|------|--------|------|-----------|--------|-------------|---|
| Mai-03 | $3,749 | €1,705 | — | $220 Spot | **~€5,219** | base |
| Mai-06 | $3,990 | €1,666 | — | — | **~€4,996** | -€223 |
| Mai-10 | $4,064 | €1,887 | — | €770 Binance | **~€6,189** | +€1,193 |
| **Mai-14** | **$4,290** | **€1,323** | **€695** | **€770** | **~€6,601** | **+€412 ← PICO** |
| Mai-16 | $4,080 | €1,299 | €695 | €770 | **~€6,393** | -€208 |
| Jun-01 | $3,726 | €1,465 | €606 | $57 bot | **~€5,420** | -€973 |
| Jun-03 | $3,415 | €1,473 | €335 | $154 bot | **~€5,088** | -€332 |
| Jun-12 | $3,313 | €1,328 | €678 | $150 bot | **~€5,231** | +€143 |
| Jun-15 | $3,542 | €1,466 | €698 | $165 bot + $290 ZEC | **~€5,842** | +€611 |
| Jun-18 | $3,341 | €1,546 | €709 | $165 bot + $290 ZEC (sem actualização) | **~€5,770** | -€72 |

*Taxa EUR/USD ~1.08 usada para conversões. ZEC Spot Binance: 0.5424 ZEC ≈ $290 (ganho via Earn, custo $0). Pico histórico: €6,601 em Mai-14 (BTC $81,522). Distância ao pico: -€831 (-12.6%). Recuperação desde mínimo Jun-03: +€682 (+13.4%).*

---

## 9. Infraestrutura e Operações

### Configuração actual — Termux (Android)
- **Dispositivo:** Android (Termux), utilizador `u0_a1208`
- **Python:** unbuffered obrigatório (`python -u`)
- **Repositório:** `~/blank-app`
- **Bot log:** `~/claw.log`
- **Ficheiros bot:** `~/blank-app/claw_v8/`

> **Nota:** Bot migrado para Termux após período no VPS. Sem cron disponível no Termux — bot arrancado manualmente.

### Arranque do bot (Termux)
```bash
pkill -f "python.*main.py"; sleep 2
cd ~/blank-app && git pull origin main
cd claw_v8 && python -u main.py > ~/claw.log 2>&1 &
sleep 3 && tail -20 ~/claw.log
```

### Monitorização
```bash
# Ver log do bot
tail -30 ~/claw.log

# Ver log em tempo real
tail -f ~/claw.log

# Ver processos activos
ps aux | grep python | grep -v grep

# Relatório de performance
cd ~/blank-app && python3 claw_v8/check_results.py
```

### Credenciais
Guardadas em `~/.bashrc` como variáveis de ambiente. **Nunca mostrar no chat.**

```bash
export TELEGRAM_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
export BINANCE_API_KEY="..."
export BINANCE_API_SECRET="..."
```

### Binance API
- **Tipo:** Futures USDC-M (Cross Margin)
- **Moeda de margem:** BNFCR (conta europeia — Binance France Crypto Receipt)
- **Permissões:** Futures trading (sem levantamentos)
- **Restrição crítica:** `STOP_MARKET reduceOnly=true` NÃO suportado → usar `closePosition=true`

### Histórico de infraestrutura
O bot correu inicialmente no Termux → migrado para VPS `178.105.52.219` por causa de IP instável (WiFi/dados móveis) → retornou ao Termux. A conta BNFCR tem restrições de API não existentes noutras contas Binance.

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
| Mai-23 | ROI_TP_IMEDIATO | não existia | **7.0%** | Fecha imediatamente se ROI alto, sem esperar tempo |
| Mai-23 | TIME_TP_MIN_MIN | 30 min | **10 min** | Era demasiado conservador — NEAR perdeu +5.58% |
| Mai-23 | get_margin_ratio() | conta inteira | **só USDC/BNFCR** | USDT-M contaminava o rácio e activava guard errado |
| Mai-23 | LIQUIDATION_GUARD_PCT | não existia | **50%** | Fecha posições a positivo se conta global > 50% |
| Mai-23 | Profit lock price | nível actual | **nível anterior** | Binance rejeita stops a < 0.1% do mark price |
| Mai-28 | SCORE_ALERTA | 4 | **6** | Entradas com score 4 tinham taxa de sucesso baixa |
| Mai-28 | PRICE_PRECISION | SYMBOL_PRECISION | **PRICE_FILTER tickSize** | Stops rejeitados por Binance por casas decimais erradas |
| Mai-28 | STAGNADO condição | pnl < 0.5 | **-0.5 ≤ pnl < 1.0** | Fechava posições perdedoras — bug crítico |
| Mai-28 | get_balance / margin | primeira correspondência | **soma USDC+BNFCR** | Conta BNFCR reportava 0.17 USDC — bug BNFCR (1ª parte) |
| Mai-30 | get_balance / margin | retornava primeiro match | **soma total USDC+BNFCR** | Fix definitivo BNFCR — elimina margem falsa 526% |
| Mai-30 | ATR_PERIOD | 14 | **8** | ATR(8) óptimo para scalping 5m — menos lag no SL sizing |
| Mai-30 | total_trades | só incrementado na abertura | **recalculado no fecho** | Ficava a 0 após restart da DB |

---

## 11. Comandos Úteis

### Operações diárias
```bash
# Estado do bot
tail -20 ~/claw.log

# Scan spot manual (top 100)
cd ~/blank-app && python3 claw_v8/spot_scanner.py --top 100

# Scan de uma moeda específica
cd ~/blank-app && python3 claw_v8/spot_scanner.py SUI

# Relatório de performance
cd ~/blank-app && python3 claw_v8/check_results.py
```

### Git
```bash
# Pull e restart (Termux)
pkill -f "python.*main.py"; sleep 2
cd ~/blank-app && git pull origin main
cd claw_v8 && python -u main.py > ~/claw.log 2>&1 &
sleep 3 && tail -20 ~/claw.log
```

---

## 12. Rotina de Sessão

**Combinado:** no início de cada sessão com Claude, dizer **"faz o relatório diário"**.

Claude irá automaticamente:
1. Ler este ficheiro (`PROJECTO_CLAW_COMPLETO.md`) para ter contexto completo
2. Fazer varrimento na internet (GitHub, Reddit, fóruns algotrading) para benchmarking de melhorias
3. Correr `check_results.py` no Termux para ver dados novos do bot
4. Propor melhorias baseadas nos dados reais + benchmarking

**Comando para relatório do bot:**
```bash
cd ~/blank-app && python3 claw_v8/check_results.py
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

### Sessão 2026-05-23
Ver ficheiro `SESSAO_2026-05-23.md` para detalhe completo.

**Resumo:** 5 bugs corrigidos + 2 guards novos. Sessão de debugging intensivo após incidente com posição manual ZEC.

- **TIME_TP reformulado:** `ROI_TP_IMEDIATO=7%` (fecha imediatamente) + `TIME_TP_MIN_MIN=10` (era 30). NEAR perdeu saída a +5.58% porque ainda não tinha 30 min.
- **Profit lock fix:** stop colocado no nível *anterior* ao actual — Binance rejeita stops a < 0.1% do mark price.
- **Bug ZEC crítico:** bot adoptou posição manual do utilizador como órfã e fechou a -50 USDC de oportunidade. Fix: veto em `abrir_trade()` se símbolo já existe em `posicoes_externas`.
- **get_margin_ratio() isolado:** guard de margem afectado por posições USDT-M do utilizador. Corrigido para ler só USDC/BNFCR.
- **Guard de liquidação global:** `LIQUIDATION_GUARD_PCT=50%` → fecha TODAS as posições a positivo (bot + manuais) para evitar liquidação total da conta.
- **Commits:** `6b06533`, `446a978`

### Sessões 2026-05-28/29
**Resumo:** Merge do core v8 com melhorias de infra da v8.5 + 3 bug fixes críticos.

- **PRICE_PRECISION fix (bug #9):** `place_stop_market`, `place_take_profit`, `place_trailing_stop` usavam `SYMBOL_PRECISION` (casas decimais da quantidade) para formatar preços → stops rejeitados pela Binance. Corrigido para `PRICE_PRECISION` (tickSize do `PRICE_FILTER`). `get_top_futures_symbols()` actualiza dinamicamente ao arrancar e a cada 24h. — SHA `de19dff`
- **SCORE_ALERTA 4→6 (bug #10):** score mínimo de entrada 4 era demasiado baixo. Exige agora sinal forte. — SHA `e0003ea`
- **STAGNADO fix (bug #8):** condição antiga `pnl < 0.5` fechava posições perdedoras (ex: -2 USDC após 68min). Nova condição: `-0.5 ≤ pnl < 1.0`. — SHA `92e1a97`
- **get_balance() + get_margin_ratio() fix (bug BNFCR — 1ª parte):** passa a ler USDC e BNFCR em vez de só USDC. — SHA `d691f48`

### Sessão 2026-05-30
Ver ficheiro `SESSAO_2026-05-30.md` para detalhe completo.

**Resumo:** Relatório diário + fix definitivo BNFCR + ATR length + total_trades.

- **Bug BNFCR definitivo:** `get_balance()` e `get_margin_ratio()` reportavam 0.17 USDC e 526% de margem. Causa: conta EU/BNFCR tem capital em BNFCR, dust USDC vinha primeiro na resposta API. Fix: soma total USDC + BNFCR em vez de retornar na primeira correspondência. Spam de 4 alertas "MARGEM CRÍTICA" com rácios de 526%/532%/917%/341% eliminado com cooldown de 300s. — SHA `50eedee`
- **ATR_PERIOD 14→8:** benchmark confirma ATR(8) óptimo para scalping 5m. Menos lag no sizing de SL/TP.
- **total_trades fix:** era incrementado só na abertura, não no fecho. Após reset da DB ficava a 0 enquanto wins/losses mostravam valores reais. Fix: recalcular em `_registar_fecho()`. — SHA `5fdb018`
- **Varrimento internet:** funding rate (0.05%) confirmado correcto; ATR params, score, HTF, risco por trade todos alinhados com benchmarks 2025-2026. Open Interest identificado como próxima melhoria.

---

## Notas Técnicas

### Porquê 4H para o spot scanner
Os indicadores mais rápidos analisados são velas de 4H. Varrer a cada 15 minutos seria analisar os mesmos dados 16 vezes sem diferença, além de ~28.000 pedidos/dia à Binance.

### Porquê SQLite em vez de JSON (v8.0)
JSON não permite queries. Com SQLite é possível responder: *"qual filtro bloqueou os trades mais rentáveis?"* — informação impossível de extrair do JSON.

### BNFCR vs USDC
A Binance Europa usa BNFCR como moeda de margem nos futuros, não USDC. O capital fica em BNFCR mas os `maintMargin` das posições USDC-M aparecem na linha USDC da API. `get_balance()` e `get_margin_ratio()` somam ambos os activos para obter valores correctos.

### Isolated vs Cross Margin
Isolated margin não disponível na Binance Europa. O bot usa sempre Cross Margin.
