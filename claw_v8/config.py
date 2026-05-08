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
CAPITAL_MAX_BOT     = 75.0
RISCO_USDC          = 3.0
ALAVANCAGEM         = 5
RATIO_ALVO          = 2.0
MAX_LOSS_DIA        = 7.5
MAX_PERDAS_SEGUIDAS = 3
COOLDOWN_MIN        = 120
MARGIN_RATIO_MAX    = 50.0
MAX_TRADES_ABERTOS  = 4
MAX_LONGS_ALT       = 2
MAX_SHORTS_ALT      = 2

# ─────────────────────────────────────────────
#  ESTRATÉGIA
# ─────────────────────────────────────────────
RSI_OVERSOLD    = 42.0
RSI_OVERBOUGHT  = 58.0
STOCH_VETO_LONG = 95.0
STOCH_VETO_SHORT= 5.0
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
PARTIAL_TP_RATIO  = 0.5

CMF_PERIOD = 20
MFI_PERIOD = 10
ROC_PERIOD = 10
CVD_PERIOD = 20

# ─────────────────────────────────────────────
#  PROTECÇÕES
# ─────────────────────────────────────────────
SPREAD_MAX_PCT      = 0.05
ATR_REGIME_MULT     = 3.0
ATR_REGIME_LOOKBACK = 50
BTC_CRASH_PCT       = 3.0
STOP_RETRY_MAX      = 3
EMERGENCY_ROI_CUT   = -4.0

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
