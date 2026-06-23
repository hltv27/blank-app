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
TOP_N_FUTURES = 50   # top 50 por volume — evita memecoins exóticos de baixo volume

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
RISCO_USDC          = 5.0
ALAVANCAGEM         = 6
RATIO_ALVO          = 3.0
MAX_LOSS_DIA        = 15.0
MAX_PERDAS_SEGUIDAS = 3
COOLDOWN_MIN        = 120
MAX_TRADES_ABERTOS  = 5
MAX_LONGS_ALT       = 3
MAX_SHORTS_ALT      = 3

# ─────────────────────────────────────────────
#  ESTRATÉGIA
# ─────────────────────────────────────────────
ADX_TREND_MIN       = 22.5   # ADX mínimo (fallback / detect_market_mode)
ADX_TREND_MIN_MAJOR = 22.5   # BTC, ETH, BNB — tendências mais limpas
ADX_TREND_MIN_ALT   = 25.0   # era 30 — alts com ADX 25+ já têm tendência suficiente
EMA_SLOPE_MIN   = 0.0005 # era 0.0008 — slope mínimo da EMA99 (0.05% em 5 velas)

RSI_OVERSOLD    = 45.0   # era 42 — dá +3 LONG com RSI < 45 (mais comum)
RSI_OVERBOUGHT  = 55.0   # era 58 — dá +3 SHORT com RSI > 55 (mais comum)
STOCH_VETO_LONG = 95.0
STOCH_VETO_SHORT= 2.5
SCORE_ALERTA    = 6
SCORE_FORTE     = 6

# Markov regime detection
MARKOV_LOOKBACK = 100   # candles for transition matrix
MARKOV_MIN_PROB = 0.55  # min P(bullish/bearish next) to generate a signal
MARKOV_SCORE    = 2     # score points added when regime confirms direction

ATR_MIN_PCT     = 0.0008
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
PARTIAL_TP_RATIO  = 0.67   # dispara a 2R (era 0.5 = 1R)
PARTIAL_TP_QTY    = 0.33   # fecha 33% (era 50%)
PARTIAL_TP2_RATIO = 1.0    # TP2 a 3R (full TP)
PARTIAL_TP2_QTY   = 0.33   # fecha mais 33%

CMF_PERIOD = 20
MFI_PERIOD = 10
ROC_PERIOD = 10
CVD_PERIOD = 20

ATR_SL_MULT_MIN     = 1.8      # era 1.2 — SL mínimo mais largo
ATR_SL_MULT_MAX     = 2.5      # era 1.8 — mercado volátil → SL ainda mais largo
SL_MIN_PCT          = 0.005    # SL nunca a menos de 0.5% da entrada (Binance rejeita <0.1%)
SL_MAX_PCT          = 0.03     # SL nunca a mais de 3% da entrada
ATR_VOL_SCALE_PCT   = 0.003    # ATR/price acima disto → reduz qty
TAKER_RATIO_MIN     = 0.52     # taker buy ratio mínimo para LONG

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
EMERGENCY_ROI_CUT   = -5.5
EMERGENCY_PNL_CUT   = 3.0    # fecha se posição perde > 3 USDC absolutos
BREAKEVEN_OFFSET    = 0.002  # +0.2% acima da entrada (cobre fees)

# Guarda de capital — nunca perder mais de 25% em aberto
MAX_DRAWDOWN_PCT    = 0.25   # 25% do saldo → fecha tudo
MARGIN_RATIO_MAX    = 35.0   # margem crítica (era 50%) → mais cedo
MAX_MARGEM_TRADE    = 0.20   # máx 20% do capital por posição (74 USDC em 370)
PROFIT_LOCK_USDC    = 0.5    # activa lock a partir deste PnL
PROFIT_LOCK_STEP    = 0.5    # a cada +0.5 USDC move o stop para esse nível
TRAILING_LOCK_USDC  = 4.0    # ao atingir 4 USDC (~0.8R), muda stop fixo → trailing stop

ROI_TP_IMEDIATO     = 7.0    # % ROI → fecha imediatamente, sem esperar tempo
TIME_TP_MIN_MIN     = 10     # minutos mínimos para TIME_TP (era 30)

# Protecção de pico de lucro: fecha se recuar muito do máximo já atingido
# E o sinal já não confirmar a direcção (evita fechar por simples ruído)
PEAK_PROFIT_MIN_USDC = 1.5    # só actua se a trade já chegou a este PnL
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
CHECK_EVERY         = 240
CHECK_POSICOES      = 30
CHECK_POSICOES_FAST = 10

# ─────────────────────────────────────────────
#  FICHEIROS / MODO
# ─────────────────────────────────────────────
DB_FILE       = "claw_v8.db"
LOG_FILE      = "claw_v8.log"
PAPER_TRADING = False

# Tabela de saídas dinâmicas: (minutos_mínimos, múltiplo_de_R, fracção_a_fechar)
# Referência para futura migração de TP1/TP2 — lógica actual já equivale a isto.
ROI_STEPS = [
    (0,    1.0, 0.0),
    (30,   1.5, 0.0),
    (60,   2.0, 0.33),
    (120,  3.0, 0.33),
    (240,  4.0, 0.0),
]
