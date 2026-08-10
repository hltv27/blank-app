"""
Claw Agent v8.0 — Configuração central
Todas as constantes num só lugar. Edita aqui.
"""
import os

# ─────────────────────────────────────────────
#  CREDENCIAIS
# ─────────────────────────────────────────────
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN",    "TOKEN_AQUI")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID",  "CHATID_AQUI")
BINANCE_API_KEY   = os.getenv("BINANCE_API_KEY",   "APIKEY_AQUI")
BINANCE_API_SECRET= os.getenv("BINANCE_API_SECRET","SECRET_AQUI")

BASE_URL = "https://fapi.binance.com"

# ─────────────────────────────────────────────
#  PARES
# ─────────────────────────────────────────────
TOP_N_FUTURES = 40   # top 40 por volume — mais diversidade sem memecoins ilíquidos

# Pares sempre scaneados, independentemente de estarem no top N por volume
FORCE_INCLUDE_SYMBOLS = ["ZECUSDC"]

# Lista base de fallback (usada se a fetch dinâmica falhar)
SYMBOLS = [
    "BTCUSDC", "ETHUSDC", "BNBUSDC", "SOLUSDC",
    "XRPUSDC", "DOGEUSDC", "LINKUSDC",
    "SUIUSDC",  "1000PEPEUSDC"
]

SYMBOL_PRECISION = {
    "BTCUSDC": 3, "ETHUSDC": 3, "BNBUSDC": 2, "SOLUSDC": 1,
    "XRPUSDC": 1, "DOGEUSDC": 0, "AVAXUSDC": 2, "LINKUSDC": 2,
    "SUIUSDC": 1, "1000PEPEUSDC": 0,
}

# Casas decimais para preços (tickSize) — actualizado dinamicamente via exchangeInfo
PRICE_PRECISION = {
    "BTCUSDC": 1, "ETHUSDC": 2, "BNBUSDC": 2, "SOLUSDC": 3,
    "XRPUSDC": 4, "DOGEUSDC": 5, "AVAXUSDC": 3, "LINKUSDC": 3,
    "SUIUSDC": 4, "1000PEPEUSDC": 6,
}

BTC_SYMBOLS = {"BTCUSDC"}

# ─────────────────────────────────────────────
#  RISCO
# ─────────────────────────────────────────────
CAPITAL_MAX_BOT     = 370.0
RISCO_USDC          = 6.0
ALAVANCAGEM         = 6
RATIO_ALVO          = 3.0
MAX_LOSS_DIA        = 10.0
REDUCING_LOSS_PCT   = 0.5     # entra em REDUCING a 50% do MAX_LOSS_DIA (5 USDC)
REDUCING_STREAK     = 2       # entra em REDUCING após 2 perdas seguidas
MAX_PERDAS_SEGUIDAS = 3
COOLDOWN_MIN        = 120
MAX_TRADES_ABERTOS  = 5
MAX_LONGS_ALT       = 3
MAX_SHORTS_ALT      = 3

# ─────────────────────────────────────────────
#  ESTRATÉGIA
# ─────────────────────────────────────────────
SIGNAL_INTERVAL     = "1h"   # timeframe do sinal (era "5m")
SCAN_ALIGN_MIN      = 60     # Fase 2: scan 1×/hora com vela fechada (era 15 — lia wicks)

ADX_TREND_MIN       = 22.5   # ADX mínimo (fallback / detect_market_mode)
ADX_TREND_MIN_MAJOR = 22.5   # BTC, ETH, BNB — tendências mais limpas
ADX_TREND_MIN_ALT   = 25.0   # alts com ADX 25+ já têm tendência suficiente
EMA_SLOPE_MIN   = 0.003  # slope mínimo da EMA99 (Fase 2: era 0.0005 — passava tudo)
STOCH_VETO_LONG = 95.0
STOCH_VETO_SHORT= 2.5
SCORE_ALERTA    = 5       # Fase 2: score por categorias (max 8), era 6 com max ~18
SCORE_FORTE     = 7       # sinais "fortes" (Fase 2: era 8)
SCORE_LONG_MIN  = 5       # LONGs: score mínimo (Fase 2: era 6)
SCORE_SHORT_MIN = 6       # SHORTs: score mínimo (Fase 2: era 8 — demasiado restritivo)

# Markov regime detection
MARKOV_LOOKBACK = 100   # candles for transition matrix
MARKOV_MIN_PROB = 0.55  # min P(bullish/bearish next) to generate a signal
MARKOV_SCORE    = 0     # Fase 2: desactivado temporariamente (adicionava ruído ao score)

ATR_MIN_PCT     = 0.003   # Fase 2: era 0.0008 — passava tudo como TRENDING
ATR_FLOOR_PCT   = 0.0003  # ATR mínimo: 0.03% do preço (evita qty degenerada em volatilidade ultra-baixa)
BB_PERIOD       = 20
BB_STD          = 2.0

EMA_FAST        = 9
EMA_SLOW        = 21
EMA_TREND       = 99
RSI_PERIOD      = 14
ATR_PERIOD      = 8
STOCH_PERIOD    = 14
LOOKBACK        = 220

SUPERTREND_PERIOD = 10
SUPERTREND_MULT   = 3.0
# TP1/TP2 parciais removidos (Fase 1 auditoria — código morto, nunca disparavam)
# PARTIAL_TP_RATIO  = 0.67
# PARTIAL_TP_QTY    = 0.33
# PARTIAL_TP2_RATIO = 1.0
# PARTIAL_TP2_QTY   = 0.33

CMF_PERIOD = 20
MFI_PERIOD = 10
ROC_PERIOD = 10
CVD_PERIOD = 20

ATR_SL_MULT_MIN     = 2.0      # SL mínimo (1H ATR — mais largo que 5m)
ATR_SL_MULT_MAX     = 2.5      # mercado volátil → SL ainda mais largo
SL_MIN_PCT          = 0.008    # SL nunca a menos de 0.8% (1H precisa de mais espaço)
SL_MAX_PCT          = 0.04     # SL máximo 4% (era 3% — 1H pode precisar de mais)
ATR_VOL_SCALE_PCT   = 0.006    # ATR/price acima disto → reduz qty (era 0.3%, agora 0.6% para 1H)
TAKER_RATIO_MIN     = 0.52     # taker buy ratio mínimo para LONG
TAKER_FEE           = 0.0005   # Binance Futures taker fee (0.05%) — usado no position sizing

TRAILING_CB_BTC     = 0.5      # callback trailing BTC/ETH/BNB (%)
TRAILING_CB_ALT     = 1.2      # callback trailing alts (%)

# ─────────────────────────────────────────────
#  PROTECÇÕES
# ─────────────────────────────────────────────
FUNDING_RATE_MAX    = 0.0005   # 0.05% — longs pagam demasiado acima disto
SPREAD_MAX_PCT      = 0.05
ATR_REGIME_MULT     = 3.0
ATR_REGIME_LOOKBACK = 50
BTC_CRASH_PCT       = 3.0
STOP_RETRY_MAX      = 3
EMERGENCY_ROI_CUT   = -25.0   # nunca dispara antes do SL baseado em ATR (era -7 → cortava prematuramente)
EMERGENCY_PNL_CUT   = 6.5    # max RISCO_USDC + margem (era 7.0 → deixava perder mais que 1R)
BREAKEVEN_OFFSET    = 0.002  # +0.2% acima da entrada (cobre fees)

# Guarda de capital — nunca perder mais de 25% em aberto
MAX_DRAWDOWN_PCT    = 0.25   # 25% do saldo → fecha tudo
MARGIN_RATIO_MAX    = 35.0   # margem crítica (era 50%) → mais cedo
MAX_MARGEM_TRADE    = 0.30   # máx 30% do capital por posição
PROFIT_LOCK_USDC    = 2.0    # só toca no stop a +2 USDC de lucro REAL (era 0.5 — matava wins)
PROFIT_LOCK_STEP    = 1.0    # move stop a cada +1 USDC (era 0.25 — stop demasiado perto, noise matava)
TRAILING_LOCK_USDC  = 2.0    # trailing stop activa junto com profit lock a +2 USDC

ROI_TP_IMEDIATO     = 12.0   # % ROI → fecha imediatamente (era 7% — dava pouco espaço)
TIME_TP_MIN_MIN     = 10     # minutos mínimos para TIME_TP (era 30)

# Tabela minimal_roi: (minutos, ROI% mínimo para fechar)
# Substitui TIME_TP + STAGNADO por um único mecanismo decrescente
# MINIMAL_ROI desactivado — era o assassino de winners.
# Cortava lucros a +0.8 USDC enquanto o SL permitia perdas de -3 a -6 USDC.
# Saídas agora geridas por: profit lock (+0.25 step), trailing lock (2 USDC),
# PEAK_DRAWDOWN (recuo 40% do pico), ROI_TP_IMEDIATO (12%).
MINIMAL_ROI = []

# Trailing por % do pico (substitui steps fixos de USDC após activação)
TRAILING_LOCK_PCT   = 0.30   # fecha se recuar 30% do pico de PnL

# Protecção de pico de lucro: fecha se recuar muito do máximo já atingido
# E o sinal já não confirmar a direcção (evita fechar por simples ruído)
PEAK_PROFIT_MIN_USDC = 1.0    # só actua se a trade já chegou a +1 USDC (era 2.0 — nunca atingido com avg win 0.81)
PEAK_DRAWDOWN_PCT     = 0.40  # fecha se recuar >=40% do pico desde então

OBI_VETO        = 0.3
EQUITY_EMA_N    = 20
CORR_MAX        = 0.75
MACRO_CACHE_MIN = 60
MACRO_LOOKBACK_MIN = 30  # bloqueia também N min DEPOIS de evento de alto impacto

# Guard de liquidação global (conta inteira USDT+USDC)
LIQUIDATION_GUARD_PCT = 50.0  # > 50% → fecha todas as posições a positivo
LIQUIDATION_WARN1_PCT = 40.0  # aviso 🟡
LIQUIDATION_WARN2_PCT = 55.0  # aviso 🟠
LIQUIDATION_WARN3_PCT = 70.0  # aviso 🔴 crítico

# ─────────────────────────────────────────────
#  SESSÃO / TIMING
# ─────────────────────────────────────────────
SESSOES_UTC         = [(5, 23)]
CHECK_EVERY         = 900    # scan a cada 15 min (era 4 min — 1H não precisa de mais)
CHECK_POSICOES      = 30
CHECK_POSICOES_FAST = 15     # gestão de posições a cada 15s (era 10)

# ─────────────────────────────────────────────
#  FICHEIROS / MODO
# ─────────────────────────────────────────────
DB_FILE       = "claw_v8.db"
LOG_FILE      = "claw_v8.log"
PAPER_TRADING = False
MONITOR_EXTERNAS = False  # True = monitoriza posições manuais e aplica profit lock
KRONOS_ENABLED   = True   # True = usa modelo Kronos para bonus/penalidade de score

# Tabela de saídas dinâmicas: (minutos_mínimos, múltiplo_de_R, fracção_a_fechar)
# Referência para futura migração de TP1/TP2 — lógica actual já equivale a isto.
ROI_STEPS = [
    (0,    1.0, 0.0),
    (120,  1.5, 0.0),
    (360,  2.0, 0.33),
    (720,  3.0, 0.33),
    (1440, 4.0, 0.0),
]
