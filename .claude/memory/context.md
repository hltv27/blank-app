# Contexto Actual — CLAW Agent v8

## Estado (2026-06-15)
- **Trades totais:** 13 | **PnL:** +7.09 USDC | **WR:** 61.5%
- **Saldo real:** ~165 USDC (CAPITAL_MAX_BOT=300 — desactualizado)
- **Bot:** a correr no VPS, auto-deploy activo via cron (`* * * * *`)
- **Versão em produção:** branch `main`

## Parâmetros críticos actuais (config.py)
```
CAPITAL_MAX_BOT     = 300.0   ⚠️  real ~165 USDC
RISCO_USDC          = 5.0
ALAVANCAGEM         = 6
MAX_TRADES_ABERTOS  = 5
MAX_MARGEM_TRADE    = 0.20    (20% por trade)
SCORE_ALERTA        = 6       (sinal mínimo para entrar)
SCORE_FORTE         = 6
ADX_TREND_MIN_MAJOR = 22.5    (BTC/ETH/BNB)
ADX_TREND_MIN_ALT   = 25.0    (alts — era 30.0)
RSI_OVERSOLD        = 45.0    (era 42)
RSI_OVERBOUGHT      = 55.0    (era 58)
STOCH_VETO_LONG     = 95.0
STOCH_VETO_SHORT    = 2.5
PROFIT_LOCK_USDC    = 1.0
PROFIT_LOCK_STEP    = 0.5
TRAILING_LOCK_USDC  = 4.0
EMERGENCY_ROI_CUT   = -5.5%
EMERGENCY_PNL_CUT   = 3.0 USDC
TOP_N_FUTURES       = 50
SESSOES_UTC         = [(5, 23)]
```

## Restrições críticas da conta BNFCR
1. `STOP_MARKET reduceOnly=true` → NÃO funciona → usar `closePosition=true`
2. Só **1** STOP_MARKET closePosition por símbolo de cada vez
3. Stops e TPs usam `/fapi/v1/algoOrder` (não `/fapi/v1/order`)
4. `algoType: "CONDITIONAL"` → parâmetro inválido → **NÃO usar**
5. `place_stop_market` e `place_take_profit` usam apenas `orderType`

## Fluxo de abertura de trade
1. Filtros HTF (4H+1H), Supertrend, Fear&Greed, BB, CVD, OBI, VWAP
2. Score ≥ 6 + ADX mínimo + mercado TRENDING
3. Sizing: RISCO_USDC / (entry - SL) × entry, cap 20% capital
4. `pending_sync[symbol]` escrito ANTES da ordem
5. MARKET → STOP_MARKET (algoOrder) → TP (algoOrder)
6. Se stop falha 3x → fecha posição + alerta Telegram "TRADE ABORTADO"

## Saídas activas
| Regra | Condição |
|-------|----------|
| Profit lock | PnL > 1 USDC → move SL a cada +0.5 USDC |
| Trailing lock | PnL ≥ 4 USDC → trailing stop |
| TP1 | 2R atingido → fecha 33% |
| TP2 | 3R atingido → fecha mais 33% |
| STAGNADO | >60min, PnL entre -0.5 e +1.0 → fecha |
| EMERGENCY_PNL | perda > 3 USDC → fecha |
| EMERGENCY_ROI | ROI ≤ -5.5% → fecha |
| Software SL | price cruza SL em memória → MARKET |

## Guards de risco
- BTC crash >3% → fecha todos os LONGs do bot
- Drawdown 25% saldo → fecha tudo
- Margem >35% → fecha tudo
- Margem global >50% → fecha posições positivas (liquidation guard)
- Nunca tocam em posições manuais
