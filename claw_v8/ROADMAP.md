# Claw Agent v8 — Roadmap de Melhorias

Baseado na auditoria exaustiva de 2026-08-06 (5 agentes independentes, 91 trades analisados).

---

## ✅ Fase 1 — Corrigir Saídas (Implementado 2026-08-06)

> **Impacto máximo, risco mínimo.** As saídas estavam a sabotar as entradas.

| Alteração | Antes | Depois | Ficheiro |
|-----------|-------|--------|----------|
| MINIMAL_ROI recalibrado | `[(0,12),(120,4),(360,1),(480,0)]` — fechava a 0% ROI | `[(0,12),(90,5),(180,2.5),(300,0.8)]` — curva suave | `config.py` |
| STAGNADO estendido | 6-8h (incondicional às 8h) | 8-10h (incondicional às 10h) | `execution.py` |
| Saída graduada adicionada | Não existia | 4-8h + perda > 2 USDC + sinal fraco → corte | `execution.py` |
| PEAK_DRAWDOWN fixado | Bug: `_lock_level==0` tornava-o impossível | Condição removida, funciona agora | `execution.py` |
| PEAK_PROFIT_MIN_USDC | 2.0 (nunca atingido) | 1.0 | `config.py` |
| PROFIT_LOCK_USDC / STEP | 0.8 / 0.5 (activava a 1.0 USDC) | 0.5 / 0.25 (activava a 0.5 USDC) | `config.py` |
| TRAILING_LOCK_USDC | 4.0 (nunca disparava) | 2.0 | `config.py` |
| TP1/TP2/BREAKEVEN_1R | Código morto (exigiam 6-18 USDC) | Removidos | `execution.py` |

---

## 📋 Fase 2 — Melhorar Qualidade de Entrada (Semana de 11-17 Ago 2026)

> **Objectivo:** Reduzir trades de baixa qualidade. Entrar menos vezes, mas com mais confiança.

### 2.1 — Reestruturar score por categorias independentes
- **Problema:** EMA cross (+3) + alignment (+1) + EMA99 (+2) + Supertrend (+2) + Markov (+2) = 10 pontos correlacionados
- **Fix:** Agrupar em 3 categorias independentes:
  - **Trend** (max 3 pts): EMA cross, EMA99 position
  - **Momentum** (max 3 pts): RSI, Stoch RSI, ROC
  - **Flow** (max 2 pts): CMF, MFI, Volume
- Exigir pelo menos **2 categorias a contribuir**, total ≥ 5
- **Ficheiro:** `strategy.py` → `signal_trending()`

### 2.2 — Corrigir RSI para trend-following
- **Problema:** RSI < 40 dá +3 para LONG (compra fraqueza) — contradiz trend-following
- **Fix:**
  - LONGs: RSI > 50 (+2), RSI > 60 (+1 extra)
  - SHORTs: RSI < 50 (+2), RSI < 40 (+1 extra)
- **Ficheiro:** `strategy.py`, `config.py` (thresholds)

### 2.3 — Remover Supertrend hard veto em `execution.py`
- **Problema:** Supertrend contado 2× (score + veto absoluto)
- **Fix:** Manter no score (+2), remover veto hard em `abrir_trade()`
- **Ficheiro:** `execution.py` linhas 93-100

### 2.4 — Subir market mode thresholds
- **Problema:** `ATR_MIN_PCT=0.0008`, `EMA_SLOPE_MIN=0.0005` passam tudo como "TRENDING"
- **Fix:** `ATR_MIN_PCT=0.003`, `EMA_SLOPE_MIN=0.003`
- **Ficheiro:** `config.py`, `strategy.py`

### 2.5 — Scan só com velas fechadas
- **Problema:** Scans a cada 15min avaliam vela incompleta (wicks → crossovers falsos)
- **Fix:** `SCAN_ALIGN_MIN=60` (scan 1×/hora) OU usar `closes[-2]` em vez de `closes[-1]`
- **Ficheiro:** `config.py`, `strategy.py`

### 2.6 — Inverter BB squeeze (bónus em vez de bloqueio)
- **Problema:** BB squeeze bloqueia entradas durante compressão — mas compressão precede breakout
- **Fix:** Detectar squeeze *release* (expansão após compressão) como bónus de score (+1)
- **Ficheiro:** `filters.py`, `strategy.py`

---

## 📋 Fase 3 — Validação e Refinamento (Semana de 18-24 Ago 2026)

> **Objectivo:** Garantir que as melhorias funcionam em dados reais, não apenas em teoria.

### 3.1 — Actualizar `backtest.py` com regras de produção
- **Problema:** Backtest não simula profit lock, MINIMAL_ROI, STAGNADO, TIME_TP, 12+ filtros
- **Fix:** Adicionar:
  - Profit lock progressivo
  - MINIMAL_ROI curve
  - STAGNADO / GRAD_EXIT
  - Saída por PEAK_DRAWDOWN
  - TIME_TP
- **Ficheiro:** `backtest.py`

### 3.2 — Walk-forward validation
- Dividir dados em 3 períodos (treino / validação / teste)
- Treinar em período A, validar em B, testar em C
- Se performance em C < B → overfitting detectado

### 3.3 — Comparar distribuição de saídas
- Gerar relatório: backtest vs produção
- Verificar que % de saídas por tipo (STAGNADO, MINIMAL_ROI, SL, etc.) é semelhante
- Discrepâncias grandes = backtest não é fiel

### 3.4 — Desactivar Kronos e Markov temporariamente
- **Justificação:** Kronos "small" em CPU com 3 amostras → bias positivo no score (+2/-1). Markov com lookback 100 em 1H = 4 dias (muito curto)
- **Fix:** `KRONOS_ENABLED = False`, `MARKOV_SCORE = 0`
- Correr 1 semana sem, comparar resultados
- Se positivo: decidir se reactivar com validação ou remover permanentemente
- **Ficheiro:** `config.py`

### 3.5 — Análise de performance Fase 1 vs baseline
- Comparar métricas 1 semana após Fase 1:
  - Win rate (alvo: >40%)
  - Win/Loss ratio (alvo: >1.5:1)
  - Expectancy (alvo: positiva)
  - Distribuição de saídas (menos STAGNADO, mais PROFIT_LOCK/MINIMAL_ROI)

---

## Métricas de Sucesso

| Métrica | Actual (pre-Fase 1) | Alvo Fase 1 | Alvo Final |
|---------|---------------------|-------------|------------|
| Win Rate | 34% | 38-42% | 40-50% |
| Win/Loss Ratio | 0.59:1 | 1.0-1.5:1 | 2.0:1+ |
| Avg Win | +0.81 USDC | +1.2-1.5 USDC | +2.0 USDC |
| Avg Loss | -1.37 USDC | -1.2 USDC | -1.0 USDC |
| Expectancy | -0.66 USDC/trade | ≥ 0.0 | +0.30 USDC/trade |
| Max DD (semana) | >25% | <15% | <10% |

---

*Documento gerado pela auditoria de 2026-08-06. Actualizar após cada fase.*
