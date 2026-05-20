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
TOP_N_FUTURES = 20   # número de pares a negociar (20 ou 50)

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

BTC_SYMBOLS = {"BTCUSDC"}

# ─────────────────────────────────────────────
#  RISCO
# ─────────────────────────────────────────────
CAPITAL_MAX_BOT     = 300.0
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
ADX_TREND_MIN   = 22.5   # ADX mínimo para modo TRENDING
EMA_SLOPE_MIN   = 0.0008 # slope mínimo da EMA99 para confirmar tendência

RSI_OVERSOLD    = 42.0
RSI_OVERBOUGHT  = 58.0
STOCH_VETO_LONG = 95.0
STOCH_VETO_SHORT= 2.5
SCORE_ALERTA    = 4
SCORE_FORTE     = 6

ATR_MIN_PCT     = 0.0008
BB_PERIOD       = 20
BB_STD          = 2.0

EMA_FAST        = 9
EMA_SLOW        = 21
EMA_TREND       = 99
RSI_PERIOD      = 14
ATR_PERIOD      = 14
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

ATR_SL_MULT_MIN     = 1.2      # mercado calmo → SL mais apertado
ATR_SL_MULT_MAX     = 1.8      # mercado volátil → SL mais largo
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
BREAKEVEN_OFFSET    = 0.002  # +0.2% acima da entrada (cobre fees)

# Guarda de capital — nunca perder mais de 25% em aberto
MAX_DRAWDOWN_PCT    = 0.25   # 25% do saldo → fecha tudo
MARGIN_RATIO_MAX    = 35.0   # margem crítica (era 50%) → mais cedo
MAX_MARGEM_TRADE    = 0.20   # máx 20% do capital por posição (60 USDC em 300)
PROFIT_LOCK_USDC    = 1.0    # activa lock a partir deste PnL
PROFIT_LOCK_STEP    = 0.5    # a cada +0.5 USDC move o stop para esse nível

OBI_VETO        = 0.3
EQUITY_EMA_N    = 20
CORR_MAX        = 0.75
MACRO_CACHE_MIN = 60

# ─────────────────────────────────────────────
#  SESSÃO / TIMING
# ─────────────────────────────────────────────
SESSOES_UTC         = [(5, 23)]
CHECK_EVERY         = 240
CHECK_POSICOES      = 30
CHECK_POSICOES_FAST = 10

# ─────────────────────────────────────────────
#  FICHEIROS
# ─────────────────────────────────────────────
DB_FILE = "claw_v8.db"
