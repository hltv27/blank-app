#!/usr/bin/env python3
"""
Claw Agent v8.0 — Ficheiro único
Todos os módulos combinados: config, storage, indicators, exchange,
filters, strategy, risk, execution, analytics, main.
"""
import os, sys, time, math, sqlite3, json, hmac, hashlib, requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

# ═══════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN",    "TOKEN_AQUI")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID",  "CHATID_AQUI")
BINANCE_API_KEY   = os.getenv("BINANCE_API_KEY",   "APIKEY_AQUI")
BINANCE_API_SECRET= os.getenv("BINANCE_API_SECRET","SECRET_AQUI")

BASE_URL  = "https://fapi.binance.com"
_SAPI_URL = "https://api.binance.com"

TOP_N_FUTURES = 20

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

ADX_TREND_MIN   = 22.5
EMA_SLOPE_MIN   = 0.0008

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
PARTIAL_TP_RATIO  = 0.67
PARTIAL_TP_QTY    = 0.33
PARTIAL_TP2_RATIO = 1.0
PARTIAL_TP2_QTY   = 0.33

CMF_PERIOD = 20
MFI_PERIOD = 10
ROC_PERIOD = 10
CVD_PERIOD = 20

ATR_SL_MULT_MIN     = 1.2
ATR_SL_MULT_MAX     = 1.8
ATR_VOL_SCALE_PCT   = 0.003
TAKER_RATIO_MIN     = 0.52

TRAILING_CB_BTC     = 0.5
TRAILING_CB_ALT     = 1.2

FUNDING_RATE_MAX    = 0.0005
SPREAD_MAX_PCT      = 0.05
ATR_REGIME_MULT     = 3.0
ATR_REGIME_LOOKBACK = 50
BTC_CRASH_PCT       = 3.0
STOP_RETRY_MAX      = 3
EMERGENCY_ROI_CUT   = -5.5
BREAKEVEN_OFFSET    = 0.002

MAX_DRAWDOWN_PCT    = 0.25
MARGIN_RATIO_MAX    = 35.0
MAX_MARGEM_TRADE    = 0.20
PROFIT_LOCK_USDC    = 1.0
PROFIT_LOCK_STEP    = 0.5

OBI_VETO        = 0.3
EQUITY_EMA_N    = 20
CORR_MAX        = 0.75
MACRO_CACHE_MIN = 60

SESSOES_UTC         = [(5, 23)]
CHECK_EVERY         = 240
CHECK_POSICOES      = 30
CHECK_POSICOES_FAST = 10

DB_FILE = "claw_v8.db"

# ═══════════════════════════════════════════════════════════════
#  STORAGE
# ═══════════════════════════════════════════════════════════════

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.cursor().executescript("""
    CREATE TABLE IF NOT EXISTS positions (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol        TEXT    NOT NULL,
        direction     TEXT    NOT NULL,
        entry_price   REAL,
        sl            REAL,
        tp            REAL,
        qty           REAL,
        qty_inicial   REAL,
        mode          TEXT,
        opened_at     REAL,
        closed_at     REAL,
        close_reason  TEXT,
        pnl           REAL,
        roi           REAL,
        stop_order_id TEXT,
        tp_order_id   TEXT,
        partial_tp_done INTEGER DEFAULT 0,
        status        TEXT    DEFAULT 'OPEN'
    );
    CREATE TABLE IF NOT EXISTS filter_events (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        ts             REAL    NOT NULL,
        symbol         TEXT    NOT NULL,
        direction      TEXT    NOT NULL,
        filter_name    TEXT    NOT NULL,
        passed         INTEGER NOT NULL,
        price_at_signal REAL,
        score          INTEGER,
        atr_pct        REAL,
        future_price_15m REAL,
        future_price_30m REAL,
        future_price_60m REAL
    );
    CREATE TABLE IF NOT EXISTS state_transitions (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        ts         REAL    NOT NULL,
        symbol     TEXT    NOT NULL,
        from_state TEXT,
        to_state   TEXT    NOT NULL,
        trigger    TEXT,
        details    TEXT
    );
    CREATE TABLE IF NOT EXISTS risk_events (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        ts         REAL    NOT NULL,
        event_type TEXT    NOT NULL,
        symbol     TEXT,
        details    TEXT
    );
    CREATE TABLE IF NOT EXISTS equity_snapshots (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        ts              REAL    NOT NULL,
        balance         REAL,
        margin_ratio    REAL,
        open_positions  INTEGER,
        daily_pnl       REAL
    );
    CREATE TABLE IF NOT EXISTS bot_state (
        key        TEXT PRIMARY KEY,
        value      TEXT,
        updated_at REAL
    );
    """)
    conn.commit()
    conn.close()
    print("[v8] SQLite inicializado")


def state_get(key: str, default=None):
    conn = get_conn()
    row  = conn.execute("SELECT value FROM bot_state WHERE key=?", (key,)).fetchone()
    conn.close()
    if row is None:
        return default
    try:
        return json.loads(row["value"])
    except Exception:
        return row["value"]


def state_set(key: str, value):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO bot_state(key, value, updated_at) VALUES(?,?,?)",
        (key, json.dumps(value), time.time())
    )
    conn.commit()
    conn.close()


def load_memory() -> dict:
    return {
        "loss_dia":         state_get("loss_dia",         0.0),
        "perdas_seguidas":  state_get("perdas_seguidas",  0),
        "trades_abertos":   state_get("trades_abertos",   {}),
        "ultimo_reset":     state_get("ultimo_reset",     ""),
        "bloqueado_ate":    state_get("bloqueado_ate",    0),
        "total_trades":     state_get("total_trades",     0),
        "wins":             state_get("wins",             0),
        "losses":           state_get("losses",           0),
        "simbolos_stats":   state_get("simbolos_stats",   {}),
    }


def save_memory(mem: dict):
    for key, value in mem.items():
        state_set(key, value)


def open_position(symbol, direction, entry_price, sl, tp, qty, mode,
                  stop_order_id, tp_order_id) -> int:
    conn = get_conn()
    c    = conn.cursor()
    c.execute("""
        INSERT INTO positions
        (symbol, direction, entry_price, sl, tp, qty, qty_inicial, mode,
         opened_at, stop_order_id, tp_order_id, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,'OPEN')
    """, (symbol, direction, entry_price, sl, tp, qty, qty,
          mode, time.time(), str(stop_order_id), str(tp_order_id)))
    pos_id = c.lastrowid
    conn.commit()
    conn.close()
    log_state_transition(symbol, None, "OPEN", "ORDER_FILLED",
                         f"entry={entry_price} sl={sl} tp={tp}")
    return pos_id


def close_position_db(symbol, close_reason, pnl, roi):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE positions
        SET status='CLOSED', closed_at=?, close_reason=?, pnl=?, roi=?
        WHERE symbol=? AND status='OPEN'
    """, (time.time(), close_reason, pnl, roi, symbol))
    if c.rowcount == 0:
        c.execute("""
            INSERT INTO positions
            (symbol, direction, entry_price, pnl, roi, close_reason,
             opened_at, closed_at, status, mode)
            VALUES (?, 'UNKNOWN', 0, ?, ?, ?, ?, ?, 'CLOSED', 'LEGACY')
        """, (symbol, pnl, roi, close_reason, time.time() - 3600, time.time()))
    conn.commit()
    conn.close()
    log_state_transition(symbol, "OPEN", "CLOSED", close_reason,
                         f"pnl={pnl:.2f} roi={roi:.1f}%")


def update_position_partial_tp(symbol, qty_restante):
    conn = get_conn()
    conn.execute("""
        UPDATE positions SET qty=?, partial_tp_done=1
        WHERE symbol=? AND status='OPEN'
    """, (qty_restante, symbol))
    conn.commit()
    conn.close()


def log_filter_event(symbol, direction, filter_name, passed, price,
                     score=0, atr_pct=0.0):
    conn = get_conn()
    conn.execute("""
        INSERT INTO filter_events
        (ts, symbol, direction, filter_name, passed, price_at_signal, score, atr_pct)
        VALUES (?,?,?,?,?,?,?,?)
    """, (time.time(), symbol, direction, filter_name,
          1 if passed else 0, price, score, atr_pct))
    conn.commit()
    conn.close()


def log_state_transition(symbol, from_state, to_state, trigger, details=""):
    conn = get_conn()
    conn.execute("""
        INSERT INTO state_transitions (ts, symbol, from_state, to_state, trigger, details)
        VALUES (?,?,?,?,?,?)
    """, (time.time(), symbol, from_state, to_state, trigger, details))
    conn.commit()
    conn.close()


def log_risk_event(event_type, symbol=None, details=""):
    conn = get_conn()
    conn.execute("""
        INSERT INTO risk_events (ts, event_type, symbol, details)
        VALUES (?,?,?,?)
    """, (time.time(), event_type, symbol, details))
    conn.commit()
    conn.close()


def log_equity_snapshot(balance, margin_ratio, open_positions, daily_pnl):
    conn = get_conn()
    conn.execute("""
        INSERT INTO equity_snapshots (ts, balance, margin_ratio, open_positions, daily_pnl)
        VALUES (?,?,?,?,?)
    """, (time.time(), balance, margin_ratio, open_positions, daily_pnl))
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════════
#  INDICATORS
# ═══════════════════════════════════════════════════════════════

def ema(closes: list, period: int) -> list:
    k = 2 / (period + 1)
    result = [closes[0]]
    for c in closes[1:]:
        result.append(c * k + result[-1] * (1 - k))
    return result


def rsi(closes: list, period: int = RSI_PERIOD) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas  = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains   = [max(d, 0)      for d in deltas[-period:]]
    losses  = [abs(min(d, 0)) for d in deltas[-period:]]
    avg_gain = sum(gains)  / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))


def atr(highs: list, lows: list, closes: list, period: int = ATR_PERIOD) -> float:
    trs = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i]  - closes[i-1])
        )
        trs.append(tr)
    if len(trs) < period:
        return 0.0
    return sum(trs[-period:]) / period


def stoch_rsi(closes: list, period: int = STOCH_PERIOD) -> float:
    if len(closes) < period * 2 + 1:
        return 50.0
    rsi_vals = [rsi(closes[max(0, i - period * 2):i + 1], period)
                for i in range(period, len(closes))]
    if len(rsi_vals) < period:
        return 50.0
    recent = rsi_vals[-period:]
    min_r, max_r = min(recent), max(recent)
    if max_r == min_r:
        return 50.0
    return (rsi_vals[-1] - min_r) / (max_r - min_r) * 100


def adx(highs: list, lows: list, closes: list, period: int = 14) -> float:
    if len(closes) < period * 2:
        return 25.0
    tr_list, plus_dm, minus_dm = [], [], []
    for i in range(1, len(closes)):
        tr   = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        up   = highs[i] - highs[i-1]
        down = lows[i-1] - lows[i]
        tr_list.append(tr)
        plus_dm.append(up   if up > down and up > 0   else 0)
        minus_dm.append(down if down > up and down > 0 else 0)

    def _smooth(data, n):
        s = [sum(data[:n])]
        for d in data[n:]:
            s.append(s[-1] - s[-1] / n + d)
        return s

    if len(tr_list) < period:
        return 25.0
    atr_s   = _smooth(tr_list,  period)
    plus_s  = _smooth(plus_dm,  period)
    minus_s = _smooth(minus_dm, period)
    dx_list = []
    for i in range(len(atr_s)):
        if atr_s[i] == 0:
            continue
        pdi   = 100 * plus_s[i]  / atr_s[i]
        mdi   = 100 * minus_s[i] / atr_s[i]
        denom = pdi + mdi
        dx_list.append(100 * abs(pdi - mdi) / denom if denom else 0)
    if len(dx_list) < period:
        return 25.0
    return sum(dx_list[-period:]) / period


def supertrend(highs: list, lows: list, closes: list,
               period: int = SUPERTREND_PERIOD, mult: float = SUPERTREND_MULT):
    need = period * 2 + 2
    if len(closes) < need:
        return None
    h, l, c = highs[-need:], lows[-need:], closes[-need:]
    trs = [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1, len(c))]
    direction = True
    prev_ub = prev_lb = None
    for i in range(1, len(c)):
        start   = max(0, i - period)
        atr_i   = sum(trs[start:i]) / max(i - start, 1)
        hl2     = (h[i] + l[i]) / 2
        basic_ub = hl2 + mult * atr_i
        basic_lb = hl2 - mult * atr_i
        if prev_ub is None:
            prev_ub, prev_lb = basic_ub, basic_lb
            continue
        final_ub = basic_ub if basic_ub < prev_ub or c[i-1] > prev_ub else prev_ub
        final_lb = basic_lb if basic_lb > prev_lb or c[i-1] < prev_lb else prev_lb
        if c[i] > prev_ub:
            direction = True
        elif c[i] < prev_lb:
            direction = False
        prev_ub, prev_lb = final_ub, final_lb
    return direction


def bollinger_bands(closes: list, period: int = BB_PERIOD, std_mult: float = BB_STD):
    if len(closes) < period:
        mid = closes[-1]
        return mid, mid, mid
    window   = closes[-period:]
    mid      = sum(window) / period
    variance = sum((c - mid) ** 2 for c in window) / period
    std      = variance ** 0.5
    return mid + std_mult * std, mid, mid - std_mult * std


def volume_ok(volumes: list, lookback: int = 20) -> bool:
    if len(volumes) < lookback + 2:
        return True
    avg = sum(volumes[-lookback - 2:-2]) / lookback
    return volumes[-2] > avg * 0.8


def cmf_val(closes, highs, lows, volumes, period: int = CMF_PERIOD) -> float:
    if len(closes) < period + 1:
        return 0.0
    mfm_sum = vol_sum = 0.0
    for i in range(-period, 0):
        hl  = highs[i] - lows[i]
        mfm = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / hl if hl > 0 else 0.0
        mfm_sum += mfm * volumes[i]
        vol_sum  += volumes[i]
    return mfm_sum / vol_sum if vol_sum > 0 else 0.0


def mfi_val(closes, highs, lows, volumes, period: int = MFI_PERIOD) -> float:
    if len(closes) < period + 2:
        return 50.0
    tp  = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(len(closes))]
    mf  = [tp[i] * volumes[i] for i in range(len(tp))]
    pos = neg = 0.0
    for i in range(-period, 0):
        if tp[i] > tp[i - 1]:
            pos += mf[i]
        else:
            neg += mf[i]
    if neg == 0:
        return 100.0
    return 100 - (100 / (1 + pos / neg))


def roc_val(closes: list, period: int = ROC_PERIOD) -> float:
    if len(closes) < period + 1:
        return 0.0
    prev = closes[-period - 1]
    return (closes[-1] - prev) / prev * 100 if prev != 0 else 0.0


def bb_squeeze(closes: list, period: int = BB_PERIOD, lookback: int = 50) -> bool:
    if len(closes) < period + lookback:
        return False
    upper, mid, lower = bollinger_bands(closes, period)
    if mid == 0:
        return False
    current_width = (upper - lower) / mid
    widths = []
    for i in range(1, lookback + 1):
        sub = closes[:len(closes) - i]
        if len(sub) < period:
            break
        u, m, l = bollinger_bands(sub, period)
        if m > 0:
            widths.append((u - l) / m)
    if not widths:
        return False
    rank = sum(1 for w in widths if current_width > w) / len(widths)
    return rank < 0.2


def cvd_bias(taker_buy_vols: list, volumes: list, period: int = CVD_PERIOD) -> float:
    if len(taker_buy_vols) < period or len(volumes) < period:
        return 0.0
    buy   = sum(taker_buy_vols[-period:])
    total = sum(volumes[-period:])
    return (buy / total - 0.5) if total > 0 else 0.0


def get_daily_vwap(klines: list):
    midnight    = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_ms = int(midnight.timestamp() * 1000)
    today   = [k for k in klines if int(k[0]) >= midnight_ms]
    if len(today) < 5:
        return None
    cum_pv  = sum((float(k[2]) + float(k[3]) + float(k[4])) / 3 * float(k[5]) for k in today)
    cum_vol = sum(float(k[5]) for k in today)
    return cum_pv / cum_vol if cum_vol > 0 else None


def get_daily_vwap_bands(klines: list) -> tuple:
    midnight    = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_ms = int(midnight.timestamp() * 1000)
    today = [k for k in klines if int(k[0]) >= midnight_ms]
    if len(today) < 5:
        return None, None, None, None, None
    tps     = [(float(k[2]) + float(k[3]) + float(k[4])) / 3 for k in today]
    vols    = [float(k[5]) for k in today]
    cum_vol = sum(vols)
    if cum_vol == 0:
        return None, None, None, None, None
    vwap     = sum(tp * v for tp, v in zip(tps, vols)) / cum_vol
    variance = sum((tp - vwap) ** 2 * v for tp, v in zip(tps, vols)) / cum_vol
    std      = variance ** 0.5
    return vwap, vwap + std, vwap - std, vwap + 2 * std, vwap - 2 * std

# ═══════════════════════════════════════════════════════════════
#  EXCHANGE
# ═══════════════════════════════════════════════════════════════

_time_offset_ms = 0


def sync_time():
    global _time_offset_ms
    try:
        r = requests.get(f"{BASE_URL}/fapi/v1/time", timeout=5)
        _time_offset_ms = r.json()["serverTime"] - int(time.time() * 1000)
        print(f"[v8] Time offset Binance: {_time_offset_ms:+d}ms")
    except Exception as e:
        print(f"[AVISO] sync_time: {e}")


def _is_timestamp_error(data) -> bool:
    return isinstance(data, dict) and data.get("code") in (-1021, -1022)


def _sign(params: dict) -> dict:
    params["timestamp"]  = int(time.time() * 1000) + _time_offset_ms
    params["recvWindow"] = 10000
    query = urlencode(params)
    params["signature"] = hmac.new(
        BINANCE_API_SECRET.encode(), query.encode(), hashlib.sha256
    ).hexdigest()
    return params


def _headers() -> dict:
    return {"X-MBX-APIKEY": BINANCE_API_KEY}


def _get_retry(url, params=None, timeout=10, max_retries=4, headers=None):
    delay = 2
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                print(f"[RETRY] HTTP {r.status_code} (tentativa {attempt+1}/{max_retries}) — {delay}s")
                time.sleep(delay)
                delay *= 2
                continue
            return r
        except requests.exceptions.ConnectionError as e:
            print(f"[RETRY] Ligação falhou ({e}) — {delay}s")
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            print(f"[RETRY] Erro: {e}")
            break
    return None


def tg(msg: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=8
        )
    except Exception as e:
        print(f"[ERRO] Telegram: {e}")


def get_public_ip() -> str:
    try:
        return requests.get("https://api.ipify.org", timeout=5).text.strip()
    except Exception:
        return "desconhecido"


def get_balance():
    for _ in range(2):
        try:
            r = requests.get(
                f"{BASE_URL}/fapi/v2/balance",
                params=_sign({}), headers=_headers(), timeout=10
            )
            data = r.json()
            if _is_timestamp_error(data):
                sync_time()
                continue
            if isinstance(data, dict):
                msg = data.get("msg", "")
                print(f"[ERRO] get_balance: {msg}")
                if "Invalid API-key, IP" in msg:
                    tg(f"🔒 <b>IP bloqueado</b>\nNovo IP: <code>{get_public_ip()}</code>")
                return None
            for a in data:
                if a["asset"] in ("USDC", "BNFCR"):
                    return float(a["availableBalance"])
        except Exception as e:
            print(f"[ERRO] get_balance: {e}")
            break
    return None


def get_klines(symbol, interval="5m", limit=220):
    try:
        r = _get_retry(
            f"{BASE_URL}/fapi/v1/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit}
        )
        if r is None:
            return None
        data = r.json()
        if isinstance(data, dict):
            print(f"[ERRO] klines {symbol}: {data.get('msg', data)}")
            return None
        return data
    except Exception as e:
        print(f"[ERRO] get_klines {symbol}: {e}")
    return None


def get_positions():
    for _ in range(2):
        try:
            r = requests.get(
                f"{BASE_URL}/fapi/v2/positionRisk",
                params=_sign({}), headers=_headers(), timeout=10
            )
            data = r.json()
            if _is_timestamp_error(data):
                sync_time()
                continue
            if isinstance(data, dict):
                msg = data.get("msg", "")
                print(f"[ERRO] get_positions: {msg}")
                if "Invalid API-key, IP" in msg:
                    tg(f"🔒 <b>IP bloqueado</b>\nNovo IP: <code>{get_public_ip()}</code>")
                return None
            pos = {}
            for p in data:
                qty = float(p.get("positionAmt", 0))
                if abs(qty) > 0:
                    pos[p["symbol"]] = {
                        "qty":   qty,
                        "entry": float(p.get("entryPrice", 0)),
                        "pnl":   float(p.get("unRealizedProfit", 0)),
                        "side":  "LONG" if qty > 0 else "SHORT"
                    }
            return pos
        except Exception as e:
            print(f"[ERRO] get_positions: {e}")
            break
    return None


def get_margin_ratio():
    for _ in range(2):
        try:
            r = requests.get(
                f"{BASE_URL}/fapi/v2/account",
                params=_sign({}), headers=_headers(), timeout=10
            )
            data = r.json()
            if _is_timestamp_error(data):
                sync_time()
                continue
            maint   = float(data.get("totalMaintMargin",  0))
            balance = float(data.get("totalMarginBalance", 0))
            if balance > 0:
                return round(maint / balance * 100, 2)
            break
        except Exception as e:
            print(f"[ERRO] get_margin_ratio: {e}")
            break
    return None


def get_price(symbol):
    try:
        r = requests.get(
            f"{BASE_URL}/fapi/v1/ticker/price",
            params={"symbol": symbol}, timeout=5
        )
        return float(r.json()["price"])
    except Exception:
        return None


def set_leverage(symbol):
    try:
        requests.post(
            f"{BASE_URL}/fapi/v1/marginType",
            params=_sign({"symbol": symbol, "marginType": "CROSSED"}),
            headers=_headers(), timeout=10
        )
        requests.post(
            f"{BASE_URL}/fapi/v1/leverage",
            params=_sign({"symbol": symbol, "leverage": ALAVANCAGEM}),
            headers=_headers(), timeout=10
        )
    except Exception as e:
        print(f"[AVISO] set_leverage {symbol}: {e}")


def place_order(symbol, side, qty):
    try:
        decimals = SYMBOL_PRECISION.get(symbol, 4)
        r = requests.post(
            f"{BASE_URL}/fapi/v1/order",
            params=_sign({
                "symbol":   symbol,
                "side":     side,
                "type":     "MARKET",
                "quantity": f"{qty:.{decimals}f}",
            }),
            headers=_headers(), timeout=10
        )
        return r.json()
    except Exception as e:
        print(f"[ERRO] place_order {symbol}: {e}")
    return None


def place_stop_market(symbol, side, stop_price, qty):
    try:
        decimals = SYMBOL_PRECISION.get(symbol, 4)
        params = {
            "symbol":        symbol,
            "side":          side,
            "orderType":     "STOP_MARKET",
            "algoType":      "CONDITIONAL",
            "stopPrice":     f"{stop_price:.{decimals}f}",
            "closePosition": "true",
        }
        r = requests.post(
            f"{BASE_URL}/fapi/v1/algoOrder",
            params=_sign(params), headers=_headers(), timeout=10
        )
        data = r.json()
        if _is_timestamp_error(data):
            sync_time()
            r = requests.post(f"{BASE_URL}/fapi/v1/algoOrder",
                              params=_sign(params), headers=_headers(), timeout=10)
            data = r.json()
        if "algoId" in data:
            return data["algoId"]
        print(f"[AVISO] stop_market {symbol}: {data.get('msg', data)}")
    except Exception as e:
        print(f"[ERRO] place_stop_market {symbol}: {e}")
    return None


def place_take_profit(symbol, side, tp_price):
    try:
        decimals = SYMBOL_PRECISION.get(symbol, 4)
        params = {
            "symbol":        symbol,
            "side":          side,
            "orderType":     "TAKE_PROFIT_MARKET",
            "algoType":      "CONDITIONAL",
            "stopPrice":     f"{tp_price:.{decimals}f}",
            "closePosition": "true",
        }
        r = requests.post(
            f"{BASE_URL}/fapi/v1/algoOrder",
            params=_sign(params), headers=_headers(), timeout=10
        )
        data = r.json()
        if _is_timestamp_error(data):
            sync_time()
            r = requests.post(f"{BASE_URL}/fapi/v1/algoOrder",
                              params=_sign(params), headers=_headers(), timeout=10)
            data = r.json()
        if "algoId" in data:
            return data["algoId"]
        print(f"[AVISO] take_profit {symbol}: {data.get('msg', data)}")
    except Exception as e:
        print(f"[ERRO] place_take_profit {symbol}: {e}")
    return None


def place_trailing_stop(symbol, side, callback_rate, activation_price):
    try:
        decimals = SYMBOL_PRECISION.get(symbol, 4)
        params = {
            "symbol":          symbol,
            "side":            side,
            "orderType":       "TRAILING_STOP_MARKET",
            "algoType":        "CONDITIONAL",
            "callbackRate":    f"{callback_rate}",
            "activationPrice": f"{activation_price:.{decimals}f}",
            "closePosition":   "true",
        }
        r    = requests.post(f"{BASE_URL}/fapi/v1/algoOrder",
                             params=_sign(params), headers=_headers(), timeout=10)
        data = r.json()
        if _is_timestamp_error(data):
            sync_time()
            r    = requests.post(f"{BASE_URL}/fapi/v1/algoOrder",
                                 params=_sign(params), headers=_headers(), timeout=10)
            data = r.json()
        if "algoId" in data:
            print(f"[OK] Trailing stop {symbol}: callback {callback_rate}%")
            return data["algoId"]
        msg = data.get("msg", str(data))
        print(f"[AVISO] trailing_stop {symbol}: {msg} — fallback STOP_MARKET")
        sl_price = (activation_price * (1 - callback_rate / 100) if side == "SELL"
                    else activation_price * (1 + callback_rate / 100))
        return place_stop_market(symbol, side, sl_price, 0)
    except Exception as e:
        print(f"[ERRO] place_trailing_stop {symbol}: {e}")
    return None


def close_position(symbol, qty, side):
    close_side = "SELL" if side == "LONG" else "BUY"
    return place_order(symbol, close_side, abs(qty))


def cancel_order(symbol, order_id) -> bool:
    try:
        params = _sign({"symbol": symbol, "orderId": int(order_id)})
        r = requests.delete(
            f"{BASE_URL}/fapi/v1/order",
            params=params, headers=_headers(), timeout=10
        )
        data = r.json()
        if _is_timestamp_error(data):
            sync_time()
            params = _sign({"symbol": symbol, "orderId": int(order_id)})
            r = requests.delete(f"{BASE_URL}/fapi/v1/order",
                                params=params, headers=_headers(), timeout=10)
            data = r.json()
        return data.get("status") == "CANCELED"
    except Exception as e:
        print(f"[AVISO] cancel_order {symbol} #{order_id}: {e}")
        return False


def cancel_algo_order(symbol, algo_id) -> bool:
    try:
        params = _sign({"symbol": symbol, "algoId": int(algo_id)})
        r = requests.delete(
            f"{_SAPI_URL}/sapi/v1/algo/futures/order",
            params=params, headers=_headers(), timeout=10
        )
        data = r.json()
        if _is_timestamp_error(data):
            sync_time()
            params = _sign({"symbol": symbol, "algoId": int(algo_id)})
            r = requests.delete(f"{_SAPI_URL}/sapi/v1/algo/futures/order",
                                params=params, headers=_headers(), timeout=10)
            data = r.json()
        if data.get("success") is True or data.get("code") == 200:
            return True
        print(f"[AVISO] cancel_algo_order {symbol} #{algo_id}: {data.get('msg', data)}")
        return False
    except Exception as e:
        print(f"[AVISO] cancel_algo_order {symbol} #{algo_id}: {e}")
        return False


def get_top_futures_symbols(n=20, min_days=30):
    STABLES = {"USDT","USDC","BUSD","DAI","TUSD","USDP","FDUSD","USDE","PYUSD"}
    EXCLUIR = {"UP","DOWN","BULL","BEAR","3L","3S","HEDGE"}
    min_age_ms = min_days * 24 * 3600 * 1000
    agora_ms   = int(time.time() * 1000)
    try:
        info = requests.get(f"{BASE_URL}/fapi/v1/exchangeInfo", timeout=10).json()
        precision_map = {}
        usdc_symbols  = set()
        for s in info.get("symbols", []):
            if not (s.get("quoteAsset") == "USDC"
                    and s.get("status") == "TRADING"
                    and s.get("contractType") == "PERPETUAL"):
                continue
            sym = s["symbol"]
            onboard = s.get("onboardDate", agora_ms)
            if (agora_ms - onboard) < min_age_ms:
                print(f"[v8] {sym} excluído — listada há menos de {min_days} dias")
                continue
            usdc_symbols.add(sym)
            for f in s.get("filters", []):
                if f.get("filterType") == "LOT_SIZE":
                    step = f.get("stepSize", "1")
                    decimals = len(step.rstrip("0").split(".")[1]) if "." in step else 0
                    precision_map[sym] = decimals
                    break
        tickers = requests.get(f"{BASE_URL}/fapi/v1/ticker/24hr", timeout=10).json()
        candidatos = []
        for t in tickers:
            sym  = t.get("symbol", "")
            if sym not in usdc_symbols:
                continue
            base = sym.replace("USDC", "").replace("1000", "")
            if base in STABLES or any(ex in base for ex in EXCLUIR):
                continue
            try:
                candidatos.append((sym, float(t.get("quoteVolume", 0))))
            except Exception:
                continue
        candidatos.sort(key=lambda x: x[1], reverse=True)
        resultado = [s for s, _ in candidatos[:n]]
        print(f"[v8] Top {n} USDC-M (mín. {min_days} dias): {resultado}")
        return resultado, precision_map
    except Exception as e:
        print(f"[AVISO] get_top_futures_symbols falhou: {e} — usando lista estática")
        return [], {}

# ═══════════════════════════════════════════════════════════════
#  FILTERS
# ═══════════════════════════════════════════════════════════════

_fg_cache:    dict = {"value": 50, "ts": 0.0}
_macro_cache: dict = {"ts": 0.0, "bloqueado": False}
_mkt_cache:   dict = {}


def _log(symbol, direction, name, passed, price, score=0, atr_pct=0.0):
    log_filter_event(symbol, direction, name, passed, price, score, atr_pct)
    return passed


def macro_event_proximo(look_ahead_min=60) -> bool:
    global _macro_cache
    now = time.time()
    if now - _macro_cache["ts"] < MACRO_CACHE_MIN * 60:
        return _macro_cache["bloqueado"]
    try:
        r = requests.get(
            "https://nfs.faireconomy.media/ff_calendar_thisweek.xml", timeout=10
        )
        if r.status_code != 200:
            _macro_cache = {"ts": now, "bloqueado": False}
            return False
        root    = ET.fromstring(r.text)
        now_dt  = datetime.now(timezone.utc)
        look_dt = now_dt + timedelta(minutes=look_ahead_min)
        for event in root.findall(".//event"):
            impact = event.find("impact")
            if impact is None or (impact.text or "").strip().lower() != "high":
                continue
            date_el = event.find("date")
            time_el = event.find("time")
            if date_el is None or time_el is None:
                continue
            try:
                evt_dt = datetime.strptime(
                    f"{date_el.text} {time_el.text}", "%b %d, %Y %I:%M%p"
                ).replace(tzinfo=timezone.utc)
                if now_dt <= evt_dt <= look_dt:
                    name_el   = event.find("title")
                    name      = name_el.text if name_el is not None else "evento"
                    mins_away = int((evt_dt - now_dt).total_seconds() / 60)
                    print(f"[MACRO] {name} em {mins_away}min — sem entrada")
                    _macro_cache = {"ts": now, "bloqueado": True}
                    return True
            except ValueError:
                continue
        _macro_cache = {"ts": now, "bloqueado": False}
        return False
    except Exception as e:
        print(f"[MACRO] Calendário indisponível: {e} — filtro ignorado")
        _macro_cache = {"ts": now, "bloqueado": False}
        return False


def get_fear_greed() -> int:
    global _fg_cache
    if time.time() - _fg_cache["ts"] < 3600:
        return _fg_cache["value"]
    try:
        r = requests.get(
            "https://api.alternative.me/fng/?limit=1&format=json", timeout=8
        )
        val = int(r.json()["data"][0]["value"])
        _fg_cache = {"value": val, "ts": time.time()}
        print(f"[F&G] Fear & Greed: {val}")
        return val
    except Exception:
        return _fg_cache["value"]


def volatility_regime_ok(symbol, closes, highs, lows, direction, price) -> bool:
    if len(closes) < ATR_REGIME_LOOKBACK + ATR_PERIOD + 1:
        return _log(symbol, direction, "VOLATILITY_REGIME", True, price)
    atr_atual = atr(highs, lows, closes)
    atrs = []
    for i in range(1, ATR_REGIME_LOOKBACK + 1):
        sc, sh, sl_ = closes[:-i], highs[:-i], lows[:-i]
        if len(sc) > ATR_PERIOD:
            atrs.append(atr(sh, sl_, sc))
    if not atrs:
        return _log(symbol, direction, "VOLATILITY_REGIME", True, price)
    atr_medio = sum(atrs) / len(atrs)
    passed = not (atr_medio > 0 and atr_atual > atr_medio * ATR_REGIME_MULT)
    if not passed:
        print(f"[REGIME] {symbol}: ATR {atr_atual:.6f} > {ATR_REGIME_MULT}× média — regime violento")
    return _log(symbol, direction, "VOLATILITY_REGIME", passed, price)


def spread_ok(symbol, direction, price) -> bool:
    try:
        r = requests.get(
            f"{BASE_URL}/fapi/v1/ticker/bookTicker",
            params={"symbol": symbol}, timeout=5
        )
        data = r.json()
        bid  = float(data["bidPrice"])
        ask  = float(data["askPrice"])
        if bid <= 0:
            return _log(symbol, direction, "SPREAD", True, price)
        spread_pct = (ask - bid) / bid * 100
        passed = spread_pct <= SPREAD_MAX_PCT
        if not passed:
            print(f"[SPREAD] {symbol}: {spread_pct:.3f}% > {SPREAD_MAX_PCT}%")
        return _log(symbol, direction, "SPREAD", passed, price)
    except Exception:
        return _log(symbol, direction, "SPREAD", True, price)


def market_conditions_ok(symbol, direction, price) -> bool:
    cache_key = f"{symbol}_{direction}"
    now = time.time()
    if cache_key in _mkt_cache and now - _mkt_cache[cache_key]["ts"] < 300:
        return _mkt_cache[cache_key]["result"]
    try:
        r = requests.get(f"{BASE_URL}/fapi/v1/fundingRate",
                         params={"symbol": symbol, "limit": 1}, timeout=5)
        fr_data = r.json()
        if fr_data:
            rate = float(fr_data[-1]["fundingRate"])
            if direction == "LONG"  and rate >  FUNDING_RATE_MAX:
                result = _log(symbol, direction, "FUNDING_RATE", False, price)
                _mkt_cache[cache_key] = {"ts": now, "result": result}
                return result
            if direction == "SHORT" and rate < -FUNDING_RATE_MAX:
                result = _log(symbol, direction, "FUNDING_RATE", False, price)
                _mkt_cache[cache_key] = {"ts": now, "result": result}
                return result
        r = requests.get(f"{BASE_URL}/futures/data/openInterestHist",
                         params={"symbol": symbol, "period": "1h", "limit": 5}, timeout=5)
        oi_data = r.json()
        if isinstance(oi_data, list) and len(oi_data) >= 5:
            oi_now = float(oi_data[-1]["sumOpenInterest"])
            oi_4h  = float(oi_data[0]["sumOpenInterest"])
            oi_chg = (oi_now / oi_4h - 1) * 100 if oi_4h > 0 else 0
            if oi_chg < -5:
                result = _log(symbol, direction, "OPEN_INTEREST", False, price)
                _mkt_cache[cache_key] = {"ts": now, "result": result}
                return result
        r = requests.get(f"{BASE_URL}/futures/data/globalLongShortAccountRatio",
                         params={"symbol": symbol, "period": "1h", "limit": 1}, timeout=5)
        lsr_data = r.json()
        if isinstance(lsr_data, list) and lsr_data:
            lsr = float(lsr_data[-1]["longShortRatio"])
            if direction == "LONG"  and lsr > 2.5:
                result = _log(symbol, direction, "LONG_SHORT_RATIO", False, price)
                _mkt_cache[cache_key] = {"ts": now, "result": result}
                return result
            if direction == "SHORT" and lsr < 0.4:
                result = _log(symbol, direction, "LONG_SHORT_RATIO", False, price)
                _mkt_cache[cache_key] = {"ts": now, "result": result}
                return result
    except Exception:
        pass
    result = _log(symbol, direction, "MARKET_CONDITIONS", True, price)
    _mkt_cache[cache_key] = {"ts": now, "result": result}
    return result


def htf_1h_ok(symbol, direction, price) -> bool:
    try:
        klines_1h = get_klines(symbol, interval="1h", limit=50)
        if not klines_1h or len(klines_1h) < 30:
            return _log(symbol, direction, "HTF_1H", False, price)
        c1h      = [float(k[4]) for k in klines_1h]
        ema9_1h  = ema(c1h, 9)
        ema21_1h = ema(c1h, 21)
        passed = ema9_1h[-1] > ema21_1h[-1] if direction == "LONG" else ema9_1h[-1] < ema21_1h[-1]
        if not passed:
            print(f"[HTF1H] {symbol}: 1H bias contra {direction}")
        return _log(symbol, direction, "HTF_1H", passed, price)
    except Exception as e:
        print(f"[HTF1H] {symbol}: API falhou ({e}) — fail-closed")
        return _log(symbol, direction, "HTF_1H", False, price)


def htf_4h_ok(symbol, direction, price) -> bool:
    try:
        klines_4h = get_klines(symbol, interval="4h", limit=30)
        if not klines_4h or len(klines_4h) < 25:
            return _log(symbol, direction, "HTF_4H", False, price)
        c4h      = [float(k[4]) for k in klines_4h]
        ema9_4h  = ema(c4h, 9)
        ema21_4h = ema(c4h, 21)
        passed = ema9_4h[-1] > ema21_4h[-1] if direction == "LONG" else ema9_4h[-1] < ema21_4h[-1]
        if not passed:
            print(f"[HTF4H] {symbol}: 4H bias contra {direction}")
        return _log(symbol, direction, "HTF_4H", passed, price)
    except Exception as e:
        print(f"[HTF4H] {symbol}: API falhou ({e}) — fail-closed")
        return _log(symbol, direction, "HTF_4H", False, price)


def obi_ok(symbol, direction, price) -> bool:
    try:
        r = requests.get(
            f"{BASE_URL}/fapi/v1/depth",
            params={"symbol": symbol, "limit": 20}, timeout=5
        )
        data    = r.json()
        bids    = data.get("bids", [])
        asks    = data.get("asks", [])
        if not bids or not asks:
            return _log(symbol, direction, "OBI", True, price)
        bid_vol = sum(float(b[1]) for b in bids)
        ask_vol = sum(float(a[1]) for a in asks)
        total   = bid_vol + ask_vol
        if total == 0:
            return _log(symbol, direction, "OBI", True, price)
        obi    = (bid_vol - ask_vol) / total
        passed = True
        if direction == "LONG"  and obi < -OBI_VETO:
            print(f"[OBI] {symbol}: OBI {obi:.2f} — pressão vendedora, LONG vetado")
            passed = False
        if direction == "SHORT" and obi > OBI_VETO:
            print(f"[OBI] {symbol}: OBI {obi:.2f} — pressão compradora, SHORT vetado")
            passed = False
        return _log(symbol, direction, "OBI", passed, price)
    except Exception:
        return _log(symbol, direction, "OBI", True, price)


def fear_greed_ok(symbol, direction, price) -> bool:
    fg_val = get_fear_greed()
    if direction == "LONG"  and fg_val < 20:
        return _log(symbol, direction, "FEAR_GREED", False, price)
    if direction == "SHORT" and fg_val > 80:
        return _log(symbol, direction, "FEAR_GREED", False, price)
    return _log(symbol, direction, "FEAR_GREED", True, price)


def cvd_ok(symbol, direction, closes, volumes, taker_buy_vols, price) -> bool:
    if not taker_buy_vols or not volumes:
        return _log(symbol, direction, "CVD", True, price)
    cvd_v  = cvd_bias(taker_buy_vols, volumes)
    passed = True
    if direction == "LONG"  and cvd_v < -0.15:
        passed = False
    if direction == "SHORT" and cvd_v > 0.15:
        passed = False
    return _log(symbol, direction, "CVD", passed, price)


def vwap_ok(symbol, direction, closes, klines, price) -> bool:
    _, _, _, upper_2, lower_2 = get_daily_vwap_bands(klines)
    passed = True
    if direction == "LONG"  and upper_2 is not None and price > upper_2:
        passed = False
    if direction == "SHORT" and lower_2 is not None and price < lower_2:
        passed = False
    return _log(symbol, direction, "VWAP_2SIGMA", passed, price)


def bb_squeeze_ok(symbol, direction, closes, volumes, price) -> bool:
    if not volumes:
        return _log(symbol, direction, "BB_SQUEEZE", True, price)
    squeezed = bb_squeeze(closes)
    return _log(symbol, direction, "BB_SQUEEZE", not squeezed, price)


def btc_crash_detectado() -> bool:
    try:
        klines_btc = get_klines("BTCUSDC", interval="5m", limit=3)
        if not klines_btc or len(klines_btc) < 2:
            return False
        open_price  = float(klines_btc[-2][1])
        close_price = float(klines_btc[-2][4])
        if open_price <= 0:
            return False
        variacao = (close_price - open_price) / open_price * 100
        if variacao <= -BTC_CRASH_PCT:
            print(f"[CRASH] BTC dump {variacao:.2f}% — a fechar longs")
            return True
    except Exception:
        pass
    return False


def liquidity_sweep_detectado(closes, highs, lows, volumes, taker_buy_vols,
                               direction, lookback=20) -> bool:
    if len(closes) < lookback + 2 or len(volumes) < lookback + 2:
        return False
    last_close = closes[-2]
    last_low   = lows[-2]
    last_high  = highs[-2]
    last_vol   = volumes[-2]
    swing_low  = min(lows[-lookback - 2:-2])
    swing_high = max(highs[-lookback - 2:-2])
    avg_vol    = sum(volumes[-lookback - 2:-2]) / max(lookback, 1)
    vol_spike  = last_vol > avg_vol * 2.0 if avg_vol > 0 else False
    cvd_v      = cvd_bias(taker_buy_vols, volumes) if taker_buy_vols else 0.0
    if direction == "LONG":
        return last_low < swing_low and last_close > swing_low and vol_spike and cvd_v > 0
    else:
        return last_high > swing_high and last_close < swing_high and vol_spike and cvd_v < 0


def calc_correlation(symbol, posicoes_reais, lookback=30) -> float:
    if not posicoes_reais:
        return 0.0
    try:
        kl_novo = get_klines(symbol, limit=lookback + 1)
        if not kl_novo or len(kl_novo) < lookback:
            return 0.0
        c_novo   = [float(k[4]) for k in kl_novo]
        ret_novo = [(c_novo[i] - c_novo[i-1]) / c_novo[i-1]
                    for i in range(1, len(c_novo)) if c_novo[i-1] != 0]
        max_corr = 0.0
        for sym_open in posicoes_reais:
            if sym_open == symbol:
                continue
            kl_open = get_klines(sym_open, limit=lookback + 1)
            if not kl_open or len(kl_open) < lookback:
                continue
            c_open   = [float(k[4]) for k in kl_open]
            ret_open = [(c_open[i] - c_open[i-1]) / c_open[i-1]
                        for i in range(1, len(c_open)) if c_open[i-1] != 0]
            n = min(len(ret_novo), len(ret_open))
            if n < 10:
                continue
            r_n    = ret_novo[-n:]
            r_o    = ret_open[-n:]
            mean_n = sum(r_n) / n
            mean_o = sum(r_o) / n
            cov    = sum((a - mean_n) * (b - mean_o) for a, b in zip(r_n, r_o)) / n
            std_n  = (sum((a - mean_n) ** 2 for a in r_n) / n) ** 0.5
            std_o  = (sum((b - mean_o) ** 2 for b in r_o) / n) ** 0.5
            if std_n > 0 and std_o > 0:
                corr     = abs(cov / (std_n * std_o))
                max_corr = max(max_corr, corr)
        return max_corr
    except Exception as e:
        print(f"[CORR] {symbol}: {e}")
        return 0.0

# ═══════════════════════════════════════════════════════════════
#  STRATEGY
# ═══════════════════════════════════════════════════════════════

def detect_market_mode(closes, atr_val) -> str:
    price = closes[-1]
    if atr_val == 0 or price == 0:
        return "MORTO"
    if atr_val / price < ATR_MIN_PCT:
        return "MORTO"
    ema_vals = ema(closes, EMA_TREND)
    slope    = (ema_vals[-1] - ema_vals[-6]) / ema_vals[-6] if ema_vals[-6] != 0 else 0
    if abs(slope) < EMA_SLOPE_MIN:
        return "MORTO"
    return "TRENDING"


def signal_trending(closes, highs, lows, volumes):
    if len(closes) < EMA_TREND + 5:
        return None, 0, "DADOS_INSUF"

    price    = closes[-1]
    ema9     = ema(closes, EMA_FAST)
    ema21    = ema(closes, EMA_SLOW)
    ema99    = ema(closes, EMA_TREND)
    rsi_val  = rsi(closes)
    sr_val   = stoch_rsi(closes)
    atr_val  = atr(highs, lows, closes)
    adx_val  = adx(highs, lows, closes)

    if adx_val < ADX_TREND_MIN:
        return None, 0, f"VETO_ADX {adx_val:.1f}"
    if sr_val > STOCH_VETO_LONG:
        return None, 0, f"VETO_SR_LONG {sr_val:.1f}"
    if sr_val < STOCH_VETO_SHORT:
        return None, 0, f"VETO_SR_SHORT {sr_val:.1f}"
    if not volume_ok(volumes):
        return None, 0, "VETO_VOL"

    score_long = score_short = 0

    if rsi_val < RSI_OVERSOLD:
        score_long  += 3
    if rsi_val > RSI_OVERBOUGHT:
        score_short += 3

    if ema9[-1] > ema21[-1] and ema9[-2] <= ema21[-2]:
        score_long  += 3
    if ema9[-1] < ema21[-1] and ema9[-2] >= ema21[-2]:
        score_short += 3

    if ema9[-1] > ema21[-1]:
        score_long  += 1
    else:
        score_short += 1

    if price > ema99[-1]:
        score_long  += 2
    else:
        score_short += 2

    if atr_val / price > ATR_MIN_PCT * 1.5:
        score_long  += 1
        score_short += 1

    st_bull = supertrend(highs, lows, closes)
    if st_bull is True:
        score_long  += 2
    elif st_bull is False:
        score_short += 2

    if sr_val < 30:
        score_long  += 1
    elif sr_val > 70:
        score_short += 1

    cmf_v = cmf_val(closes, highs, lows, volumes)
    if cmf_v > 0.05:
        score_long  += 1
    elif cmf_v < -0.05:
        score_short += 1

    mfi_v = mfi_val(closes, highs, lows, volumes)
    if mfi_v < 45:
        score_long  += 1
    elif mfi_v > 55:
        score_short += 1

    roc_v = roc_val(closes)
    if roc_v > 0.3:
        score_long  += 1
    elif roc_v < -0.3:
        score_short += 1

    if score_long >= SCORE_ALERTA and price > ema99[-1]:
        strength = "FORTE" if score_long >= SCORE_FORTE else "ALERTA"
        return "LONG", score_long, f"RSI {rsi_val:.1f} SR {sr_val:.1f} Score {score_long} [{strength}]"

    if score_short >= SCORE_ALERTA and price < ema99[-1]:
        strength = "FORTE" if score_short >= SCORE_FORTE else "ALERTA"
        return "SHORT", score_short, f"RSI {rsi_val:.1f} SR {sr_val:.1f} Score {score_short} [{strength}]"

    return None, max(score_long, score_short), f"SEM_SINAL RSI {rsi_val:.1f} SR {sr_val:.1f}"


def calc_sl_tp(direction, price, atr_val, mode, score=0, adx_val=0.0):
    atr_pct = atr_val / price if price > 0 else 0.0015
    if atr_pct > 0.003:
        sl_mult = ATR_SL_MULT_MAX
    elif atr_pct < 0.001:
        sl_mult = ATR_SL_MULT_MIN
    else:
        sl_mult = 1.5

    sl_dist = atr_val * sl_mult
    if score >= SCORE_FORTE and adx_val > 45:
        ratio = 4.0
    elif score >= SCORE_FORTE and adx_val > 35:
        ratio = 3.0
    else:
        ratio = RATIO_ALVO

    if direction == "LONG":
        return price - sl_dist, price + sl_dist * ratio
    else:
        return price + sl_dist, price - sl_dist * ratio


def calc_qty(price, sl, symbol) -> float:
    sl_dist  = abs(price - sl)
    if sl_dist == 0:
        return 0.0
    decimals = SYMBOL_PRECISION.get(symbol, 4)
    return round(RISCO_USDC / sl_dist, decimals)

# ═══════════════════════════════════════════════════════════════
#  RISK
# ═══════════════════════════════════════════════════════════════

def em_sessao() -> bool:
    hora = datetime.now(timezone.utc).hour
    return any(inicio <= hora < fim for inicio, fim in SESSOES_UTC)


def circuit_breaker_activo(mem) -> tuple:
    now  = time.time()
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if mem.get("ultimo_reset") != hoje:
        mem["loss_dia"]        = 0.0
        mem["perdas_seguidas"] = 0
        mem["bloqueado_ate"]   = 0
        mem["ultimo_reset"]    = hoje
        save_memory(mem)

    if now < mem.get("bloqueado_ate", 0):
        minutos = int((mem["bloqueado_ate"] - now) / 60)
        return True, f"COOLDOWN {minutos}min"

    if mem.get("loss_dia", 0) >= MAX_LOSS_DIA:
        mem["bloqueado_ate"] = now + COOLDOWN_MIN * 60
        save_memory(mem)
        log_risk_event("CIRCUIT_BREAKER_DAILY", details=f"loss_dia={mem['loss_dia']:.2f}")
        return True, f"LOSS_DIA {mem['loss_dia']:.2f} USDC"

    if mem.get("perdas_seguidas", 0) >= MAX_PERDAS_SEGUIDAS:
        mem["bloqueado_ate"]   = now + COOLDOWN_MIN * 60
        mem["perdas_seguidas"] = 0
        save_memory(mem)
        log_risk_event("CIRCUIT_BREAKER_STREAK", details=f"perdas={MAX_PERDAS_SEGUIDAS}")
        return True, f"PERDAS_SEGUIDAS {MAX_PERDAS_SEGUIDAS}"

    return False, ""


def equity_scale_factor(mem) -> float:
    perdas = mem.get("perdas_seguidas", 0)
    if perdas >= 3:
        print(f"[EQUITY] {perdas} perdas seguidas — tamanho reduzido 50%")
        return 0.5
    return 1.0


def verificar_veto_simbolo(symbol, mem) -> tuple:
    stats = mem.get("simbolos_stats", {}).get(symbol)
    if not stats:
        return False, ""
    vetado_ate = stats.get("vetado_ate", 0)
    if vetado_ate <= 0:
        return False, ""
    if time.time() < vetado_ate:
        mins = int((vetado_ate - time.time()) / 60)
        return True, f"vetado ainda {mins}min"
    stats["perdas_seguidas"] = 0
    stats["vetado_ate"]      = 0
    total = stats.get("wins", 0) + stats.get("losses", 0)
    wr    = stats.get("wins", 0) / total * 100 if total > 0 else 0
    tg(
        f"🔓 <b>VETO EXPIRADO — {symbol}</b>\n"
        f"Stats: {stats.get('wins',0)}W / {stats.get('losses',0)}L | "
        f"WR: {wr:.0f}% | PnL: {stats.get('pnl_total',0):+.2f}\n"
        f"<i>Perdas seguidas reiniciadas.</i>"
    )
    save_memory(mem)
    return False, ""


def atualizar_stats_simbolo(symbol, won, pnl, mem):
    stats = mem.setdefault("simbolos_stats", {}).setdefault(symbol, {
        "wins": 0, "losses": 0, "perdas_seguidas": 0,
        "pnl_total": 0.0, "vetado_ate": 0
    })
    stats["pnl_total"]    = round(stats.get("pnl_total", 0) + pnl, 4)
    stats["ultima_trade"] = datetime.now(timezone.utc).isoformat()

    if won:
        stats["wins"]             = stats.get("wins", 0) + 1
        stats["perdas_seguidas"]  = 0
    else:
        stats["losses"]           = stats.get("losses", 0) + 1
        stats["perdas_seguidas"]  = stats.get("perdas_seguidas", 0) + 1

    total  = stats["wins"] + stats["losses"]
    wr     = stats["wins"] / total * 100 if total > 0 else 100
    ps     = stats["perdas_seguidas"]
    motivo = None

    if ps >= 3:
        motivo = f"3 perdas seguidas ({ps}x)"
        stats["vetado_ate"] = time.time() + 24 * 3600
    elif total >= 5 and wr < 30:
        motivo = f"win rate crítico {wr:.0f}% em {total} trades"
        stats["vetado_ate"] = time.time() + 12 * 3600

    if motivo:
        h_veto = 24 if ps >= 3 else 12
        tg(
            f"🚫 <b>VETO — {symbol}</b>\nMotivo: {motivo}\n"
            f"Stats: {stats['wins']}W / {stats['losses']}L | "
            f"WR: {wr:.0f}% | PnL: {stats['pnl_total']:+.2f}\n"
            f"Bot não abre {symbol} durante {h_veto}h."
        )
        log_risk_event("VETO_SIMBOLO", symbol=symbol, details=motivo)

# ═══════════════════════════════════════════════════════════════
#  EXECUTION
# ═══════════════════════════════════════════════════════════════

def abrir_trade(symbol, direction, closes, highs, lows, atr_val, mode,
                detalhe, mem, score=0, volumes=None, taker_buy_vols=None, klines=None):

    price = closes[-1]

    if macro_event_proximo():
        print(f"[AVISO] {symbol}: evento macro próximo — sem entrada")
        return
    if not volatility_regime_ok(symbol, closes, highs, lows, direction, price):
        tg(f"⚡ <b>REGIME VIOLENTO</b> — {symbol}\nATR extremo. Sem entrada.")
        return
    if not spread_ok(symbol, direction, price):
        return
    if not market_conditions_ok(symbol, direction, price):
        print(f"[AVISO] {symbol}: condições de mercado desfavoráveis para {direction}")
        return
    if not htf_4h_ok(symbol, direction, price):
        return
    if not htf_1h_ok(symbol, direction, price):
        print(f"[AVISO] {symbol}: HTF 1H contra {direction} — veto")
        return

    st_bull = supertrend(highs, lows, closes)
    if direction == "LONG"  and st_bull is False:
        print(f"[AVISO] {symbol}: Supertrend bearish — LONG vetado")
        return
    if direction == "SHORT" and st_bull is True:
        print(f"[AVISO] {symbol}: Supertrend bullish — SHORT vetado")
        return

    if not fear_greed_ok(symbol, direction, price):
        return
    if not bb_squeeze_ok(symbol, direction, closes, volumes, price):
        return
    if not cvd_ok(symbol, direction, closes, volumes, taker_buy_vols, price):
        return
    if not obi_ok(symbol, direction, price):
        return
    if klines and not vwap_ok(symbol, direction, closes, klines, price):
        return

    if volumes and taker_buy_vols:
        if liquidity_sweep_detectado(closes, highs, lows, volumes, taker_buy_vols, direction):
            detalhe += " | LIQ_SWEEP✓"

    saldo = get_balance()
    if saldo is None:
        return
    capital_bot = min(saldo, CAPITAL_MAX_BOT)
    if capital_bot < RISCO_USDC * 3:
        return

    adx_val = adx(highs, lows, closes)
    sl, tp  = calc_sl_tp(direction, price, atr_val, mode, score, adx_val)
    qty     = calc_qty(price, sl, symbol)
    if qty <= 0:
        return

    decimals = SYMBOL_PRECISION.get(symbol, 4)

    scale = equity_scale_factor(mem)
    if scale < 1.0:
        qty = round(qty * scale, decimals)
        if qty <= 0:
            return

    max_qty = round((capital_bot * ALAVANCAGEM * 0.8) / price, decimals)
    if max_qty <= 0:
        return
    if qty > max_qty:
        qty = max_qty

    max_qty_margem = round((capital_bot * MAX_MARGEM_TRADE * ALAVANCAGEM) / price, decimals)
    if max_qty_margem <= 0:
        return
    if qty > max_qty_margem:
        qty = max_qty_margem

    atr_pct = atr_val / price if price > 0 else 0
    if atr_pct > ATR_VOL_SCALE_PCT:
        vol_scale = round(ATR_VOL_SCALE_PCT / atr_pct, 2)
        qty = round(qty * vol_scale, decimals)
        if qty <= 0:
            return

    set_leverage(symbol)
    side = "BUY" if direction == "LONG" else "SELL"

    mem.setdefault("pending_sync", {})[symbol] = time.time()
    save_memory(mem)

    order = place_order(symbol, side, qty)

    if order and "orderId" in order:
        fill_price = float(order.get("avgPrice") or 0) or price
        sl, tp     = calc_sl_tp(direction, fill_price, atr_val, mode, score, adx_val)
        sl_dist    = abs(fill_price - sl)
        tp_dist    = abs(tp - fill_price)
        rr_actual  = round(tp_dist / sl_dist, 1) if sl_dist > 0 else 2.0

        time.sleep(1)
        pos_verif = get_positions()
        if pos_verif is not None and symbol not in pos_verif:
            time.sleep(3)
            pos_verif = get_positions()
            if pos_verif is not None and symbol not in pos_verif:
                print(f"[ERRO] {symbol}: posição não confirmada após retry")
                return

        stop_side = "SELL" if direction == "LONG" else "BUY"
        stop_id   = None
        for tentativa in range(1, STOP_RETRY_MAX + 1):
            stop_id = place_stop_market(symbol, stop_side, sl, qty)
            if stop_id:
                break
            print(f"[AVISO] {symbol}: stop falhou (tentativa {tentativa}/{STOP_RETRY_MAX})")
            time.sleep(2)
        if not stop_id:
            print(f"[AVISO] {symbol}: stop na exchange falhou — software SL activo em {sl:.4f}")
            tg(f"⚠️ <b>{symbol}</b> aberto | SL @ {sl:.4f} (software)\nStop na exchange falhou — bot vigia preço a cada 10s.")

        tp_side     = "SELL" if direction == "LONG" else "BUY"
        tp_order_id = place_take_profit(symbol, tp_side, tp)

        try:
            open_position(symbol, direction, fill_price, sl, tp, qty,
                          mode, stop_id, tp_order_id)
        except Exception as _db_e:
            print(f"[AVISO] db_open_position falhou: {_db_e}")

        mem.setdefault("trades_abertos", {})[symbol] = {
            "direction":     direction,
            "entry":         fill_price,
            "sl":            sl,
            "tp":            tp,
            "qty":           qty,
            "qty_inicial":   qty,
            "mode":          mode,
            "opened_at":     time.time(),
            "stop_order_id": stop_id,
            "tp_order_id":   tp_order_id,
        }
        mem["total_trades"] = mem.get("total_trades", 0) + 1
        save_memory(mem)

        dir_icon = "🟢 LONG" if direction == "LONG" else "🔴 SHORT"
        stop_txt = f"🛑 SL @ {sl:.4f} (#{stop_id})" if stop_id else f"🛑 SL @ {sl:.4f} (software)"
        tp_txt   = f"TP#{tp_order_id}" if tp_order_id else "TP em memória"
        rr_icon  = f"RR {rr_actual}:1" + (" 🚀" if rr_actual >= 3 else "")
        mem.get("pending_sync", {}).pop(symbol, None)
        save_memory(mem)
        tg(
            f"📈 <b>{dir_icon}</b> — {symbol}\n"
            f"Entrada: {fill_price:.4f}\n"
            f"SL: {sl:.4f} | TP: {tp:.4f} | {rr_icon}\n"
            f"Qty: {qty:.4f} | ADX: {adx_val:.0f}\n"
            f"🔒 {stop_txt} | 🎯 {tp_txt}\n"
            f"Detalhe: {detalhe}"
        )
    else:
        mem.get("pending_sync", {}).pop(symbol, None)
        save_memory(mem)
        erro = order.get("msg", str(order)[:120]) if isinstance(order, dict) else "sem resposta"
        tg(f"⚠️ <b>Ordem falhou</b> — {symbol}\nDirecção: {direction} | Erro: {erro}")


def gerir_posicoes(mem):
    btc_crash_fired = False
    posicoes_all = None

    if btc_crash_detectado():
        btc_crash_fired = True
        posicoes_all    = get_positions() or {}
        trades_bot      = mem.get("trades_abertos", {})
        fechados = []
        for sym, pos in posicoes_all.items():
            if sym not in trades_bot:
                continue
            if pos["side"] == "LONG" and sym != "BTCUSDC":
                close_position(sym, pos["qty"], "LONG")
                mem.get("trades_abertos", {}).pop(sym, None)
                close_position_db(sym, "BTC_CRASH", pos["pnl"], 0)
                fechados.append(sym)
        if fechados:
            save_memory(mem)
            log_risk_event("BTC_CRASH_GUARD", details=f"fechados={fechados}")
            tg(f"⚡ <b>BTC CRASH GUARD</b>\nLongs fechados: {', '.join(fechados)}")

    saldo_atual = get_balance()
    if saldo_atual and saldo_atual > 0:
        if posicoes_all is None:
            posicoes_all = get_positions() or {}
        trades_bot = mem.get("trades_abertos", {})
        pnl_total_aberto = sum(
            pos.get("pnl", 0) for sym, pos in posicoes_all.items() if sym in trades_bot
        )
        limite_drawdown = saldo_atual * MAX_DRAWDOWN_PCT
        if pnl_total_aberto < -limite_drawdown:
            fechados_dd = []
            for sym, pos in posicoes_all.items():
                if sym not in trades_bot:
                    continue
                close_position(sym, pos["qty"], pos["side"])
                close_position_db(sym, "DRAWDOWN_25PCT", pos["pnl"], 0)
                mem.get("trades_abertos", {}).pop(sym, None)
                fechados_dd.append(sym)
            if fechados_dd:
                save_memory(mem)
                log_risk_event("DRAWDOWN_25PCT",
                               details=f"pnl={pnl_total_aberto:.2f} limite={-limite_drawdown:.2f}")
                tg(
                    f"🛡 <b>GUARDA 25% ACTIVADO</b>\n"
                    f"Perdas abertas: {pnl_total_aberto:.2f} USDC\n"
                    f"Fechados: {', '.join(fechados_dd)}"
                )
            return

    ratio = get_margin_ratio()
    if ratio is not None and ratio >= MARGIN_RATIO_MAX:
        if posicoes_all is None:
            posicoes_all = get_positions() or {}
        trades_bot = mem.get("trades_abertos", {})
        for sym, pos in posicoes_all.items():
            if sym not in trades_bot:
                continue
            close_position(sym, pos["qty"], pos["side"])
            close_position_db(sym, "MARGIN_CRITICAL", pos["pnl"], 0)
            mem.get("trades_abertos", {}).pop(sym, None)
        save_memory(mem)
        log_risk_event("MARGIN_CRITICAL", details=f"ratio={ratio:.1f}%")
        tg(f"🚨 <b>MARGEM CRÍTICA — TUDO FECHADO</b>\nRácio: {ratio:.1f}% (limite: {MARGIN_RATIO_MAX:.0f}%)")
        return

    if posicoes_all is None:
        posicoes_all = get_positions()
    posicoes_binance = posicoes_all
    if posicoes_binance is None:
        print("[AVISO] gerir_posicoes: API falhou")
        return
    trades_abertos = mem.get("trades_abertos", {})

    for symbol, trade in list(trades_abertos.items()):
        if symbol not in posicoes_binance:
            pnl_ext   = trade.get("pnl_ultimo", None)
            side_ext  = trade.get("direction", "LONG")
            entry_ext = trade.get("entry", 0)
            sl_ext    = trade.get("sl", 0)
            qty_ext   = abs(trade.get("qty", 0))
            if pnl_ext is None:
                pnl_ext = -abs(entry_ext - sl_ext) * qty_ext if sl_ext > 0 else 0.0
            won = pnl_ext > 0
            _registar_fecho(symbol, side_ext, entry_ext, sl_ext,
                            trade.get("tp", 0), qty_ext, pnl_ext, "ALGO_STOP", won, mem)
            continue

        pos   = posicoes_binance[symbol]
        sl    = trade.get("sl", 0)
        tp    = trade.get("tp", 0)
        side  = trade.get("direction", "LONG")
        price = get_price(symbol)
        if price is None:
            continue

        mem["trades_abertos"][symbol]["pnl_ultimo"] = pos["pnl"]

        entry    = trade.get("entry", 0)
        qty      = abs(pos["qty"])
        qty_base = trade.get("qty_inicial", qty)
        margin   = (qty_base * entry) / ALAVANCAGEM if entry > 0 and qty_base > 0 else 0
        roi      = (pos["pnl"] / margin * 100) if margin > 0 else 0

        opened_at = trade.get("opened_at")
        elapsed   = (time.time() - opened_at) if opened_at else 1800

        if elapsed >= 30 * 60 and roi >= 5.0:
            close_position(symbol, pos["qty"], side)
            _registar_fecho(symbol, side, entry, sl, tp, qty, pos["pnl"], "TIME_TP", True, mem)
            tg(f"⏱️ <b>TEMPO+LUCRO</b> — {symbol}\nROI: {roi:.1f}% | PnL: {pos['pnl']:+.2f} | {int(elapsed/60)}min")
            continue

        lock_side = "SELL" if side == "LONG" else "BUY"
        if (not trade.get("partial_tp_done") and entry > 0 and qty > 0
                and pos["pnl"] >= PROFIT_LOCK_USDC):
            current_lock = trade.get("profit_lock_level", 0.0)
            new_lock = math.floor(pos["pnl"] / PROFIT_LOCK_STEP) * PROFIT_LOCK_STEP
            if new_lock >= PROFIT_LOCK_USDC and new_lock > current_lock + 1e-9:
                if side == "LONG":
                    lock_price = round(entry + new_lock / qty, 8)
                else:
                    lock_price = round(entry - new_lock / qty, 8)

                old_stop_lock = trade.get("stop_order_id")
                if old_stop_lock:
                    cancel_algo_order(symbol, old_stop_lock)
                    mem["trades_abertos"][symbol]["stop_order_id"] = None

                new_lock_id = place_stop_market(symbol, lock_side, lock_price, qty)

                mem["trades_abertos"][symbol]["profit_lock_level"] = new_lock
                mem["trades_abertos"][symbol]["sl"]                = lock_price
                if new_lock_id:
                    mem["trades_abertos"][symbol]["stop_order_id"] = new_lock_id
                else:
                    print(f"[AVISO] {symbol}: lock stop {lock_price:.4f} falhou — software SL activo")
                save_memory(mem)
                emoji = "🔒" if current_lock == 0.0 else "📈"
                stop_info = f"#{new_lock_id}" if new_lock_id else "software"
                tg(f"{emoji} <b>LOCK +{new_lock:.1f} USDC</b> — {symbol}\nStop → {lock_price:.4f} ({stop_info}) | PnL: +{pos['pnl']:.2f} USDC")

        entry_trade = trade.get("entry", 0)
        if sl > 0 and tp > 0 and not trade.get("partial_tp_done") and entry_trade > 0:
            if side == "LONG":
                tp1_level = entry_trade + (tp - entry_trade) * PARTIAL_TP_RATIO
                hit_tp1   = price >= tp1_level
            else:
                tp1_level = entry_trade - (entry_trade - tp) * PARTIAL_TP_RATIO
                hit_tp1   = price <= tp1_level
            if hit_tp1:
                decimals_p  = SYMBOL_PRECISION.get(symbol, 4)
                qty_total   = abs(pos["qty"])
                qty_tp1     = round(qty_total * PARTIAL_TP_QTY, decimals_p)
                if qty_tp1 > 0:
                    close_position(symbol, qty_tp1, side)
                    qty_restante = round(qty_total - qty_tp1, decimals_p)
                    if side == "LONG":
                        be_price = round(entry_trade * (1 + BREAKEVEN_OFFSET), 8)
                    else:
                        be_price = round(entry_trade * (1 - BREAKEVEN_OFFSET), 8)
                    old_stop = trade.get("stop_order_id")
                    if old_stop:
                        try:
                            cancel_algo_order(symbol, old_stop)
                        except Exception:
                            pass
                    be_side     = "SELL" if side == "LONG" else "BUY"
                    cb_tp1      = TRAILING_CB_BTC if symbol in BTC_SYMBOLS else TRAILING_CB_ALT
                    new_stop_id = place_trailing_stop(symbol, be_side, cb_tp1, be_price)
                    mem["trades_abertos"][symbol]["partial_tp_done"] = True
                    mem["trades_abertos"][symbol]["qty"]             = qty_restante
                    mem["trades_abertos"][symbol]["sl"]              = be_price
                    mem["trades_abertos"][symbol]["stop_order_id"]   = new_stop_id
                    update_position_partial_tp(symbol, qty_restante)
                    pnl_tp1 = round(abs(tp1_level - entry_trade) * qty_tp1, 2)
                    log_state_transition(symbol, "OPEN", "TP1", "PRICE_HIT",
                                        f"qty={qty_tp1} pnl={pnl_tp1:.2f} be={be_price:.4f}")
                    tg(
                        f"📊 <b>TP1 — 33% fechado</b> — {symbol}\n"
                        f"Preço: {price:.4f} | +{pnl_tp1:.2f} USDC\n"
                        f"🔒 Stop movido para breakeven: {be_price:.4f}"
                    )
                    save_memory(mem)

        if sl > 0 and tp > 0 and trade.get("partial_tp_done") and \
                not trade.get("partial_tp2_done") and entry_trade > 0:
            if side == "LONG":
                tp2_level = entry_trade + (tp - entry_trade) * PARTIAL_TP2_RATIO
                hit_tp2   = price >= tp2_level
            else:
                tp2_level = entry_trade - (entry_trade - tp) * PARTIAL_TP2_RATIO
                hit_tp2   = price <= tp2_level
            if hit_tp2:
                decimals_p   = SYMBOL_PRECISION.get(symbol, 4)
                qty_total    = abs(pos["qty"])
                qty_inicial  = trade.get("qty_inicial", qty_total)
                qty_tp2      = round(qty_inicial * PARTIAL_TP2_QTY, decimals_p)
                qty_tp2      = min(qty_tp2, qty_total)
                if qty_tp2 > 0:
                    close_position(symbol, qty_tp2, side)
                    qty_restante = round(qty_total - qty_tp2, decimals_p)
                    sl_dist = abs(entry_trade - trade.get("sl", entry_trade))
                    if sl_dist == 0:
                        sl_dist = abs(entry_trade - tp) / 3.0
                    if side == "LONG":
                        lock_price = round(entry_trade + sl_dist, 8)
                    else:
                        lock_price = round(entry_trade - sl_dist, 8)
                    old_stop2 = trade.get("stop_order_id")
                    if old_stop2:
                        try:
                            cancel_algo_order(symbol, old_stop2)
                        except Exception:
                            pass
                    be_side2     = "SELL" if side == "LONG" else "BUY"
                    cb_tp2       = TRAILING_CB_BTC if symbol in BTC_SYMBOLS else TRAILING_CB_ALT
                    new_stop2_id = place_trailing_stop(symbol, be_side2, cb_tp2, lock_price)
                    mem["trades_abertos"][symbol]["partial_tp2_done"] = True
                    mem["trades_abertos"][symbol]["qty"]              = qty_restante
                    mem["trades_abertos"][symbol]["sl"]               = lock_price
                    mem["trades_abertos"][symbol]["stop_order_id"]    = new_stop2_id
                    update_position_partial_tp(symbol, qty_restante)
                    pnl_tp2 = round(abs(tp2_level - entry_trade) * qty_tp2, 2)
                    log_state_transition(symbol, "OPEN", "TP2", "PRICE_HIT",
                                        f"qty={qty_tp2} pnl={pnl_tp2:.2f} lock={lock_price:.4f}")
                    tg(
                        f"🎯 <b>TP2 — 33% fechado</b> — {symbol}\n"
                        f"Preço: {price:.4f} | +{pnl_tp2:.2f} USDC\n"
                        f"🔒 Stop em +1R: {lock_price:.4f} | Runner livre"
                    )
                    save_memory(mem)

        if roi <= EMERGENCY_ROI_CUT:
            close_position(symbol, pos["qty"], side)
            log_risk_event("EMERGENCY_CUT", symbol=symbol,
                           details=f"roi={roi:.1f}% pnl={pos['pnl']:.2f}")
            _registar_fecho(symbol, side, entry, sl, tp, qty, pos["pnl"], "EMERGENCY_SL", False, mem)
            tg(f"🛑 <b>CORTE EMERGÊNCIA</b> — {symbol}\nROI: {roi:.1f}% | PnL: {pos['pnl']:+.2f}")
            continue

        if sl <= 0 or tp <= 0:
            continue

        hit_sl = (side == "LONG" and price <= sl) or (side == "SHORT" and price >= sl)
        hit_tp = (side == "LONG" and price >= tp) or (side == "SHORT" and price <= tp)

        if hit_sl or hit_tp:
            close_position(symbol, pos["qty"], side)
            reason = "TP" if hit_tp else "SL"
            _registar_fecho(symbol, side, entry, sl, tp, qty, pos["pnl"], reason, hit_tp, mem)
            if hit_tp:
                tg(f"✅ <b>TP ATINGIDO</b> — {symbol}\nDirecção: {side} | Entrada: {entry:.4f}\nPnL: {pos['pnl']:+.2f} USDC")
            else:
                tg(f"🔴 <b>SL ATINGIDO</b> — {symbol}\nDirecção: {side} | Entrada: {entry:.4f}\nPnL: {pos['pnl']:+.2f} USDC\nPerdas hoje: {mem.get('loss_dia', 0):.2f} USDC")

    save_memory(mem)

    try:
        bal   = get_balance()
        ratio = get_margin_ratio()
        if bal is not None:
            daily_pnl = sum(t.get("pnl_ultimo", 0) for t in mem.get("trades_abertos", {}).values())
            log_equity_snapshot(bal, ratio or 0, len(posicoes_binance), daily_pnl)
    except Exception:
        pass


def _registar_fecho(symbol, side, entry, sl, tp, qty, pnl, reason, won, mem):
    mem["trades_abertos"].pop(symbol, None)
    if won:
        mem["wins"]            = mem.get("wins", 0) + 1
        mem["perdas_seguidas"] = 0
    else:
        mem["losses"]          = mem.get("losses", 0) + 1
        mem["perdas_seguidas"] = mem.get("perdas_seguidas", 0) + 1
        mem["loss_dia"]        = mem.get("loss_dia", 0) + abs(pnl)
    atualizar_stats_simbolo(symbol, won, pnl, mem)
    close_position_db(symbol, reason, pnl, 0)
    save_memory(mem)

# ═══════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════

def trade_summary() -> str:
    conn = get_conn()
    row  = conn.execute("""
        SELECT COUNT(*) as total,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
            SUM(pnl) as total_pnl,
            AVG(pnl) as avg_pnl,
            AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
            AVG(CASE WHEN pnl <= 0 THEN pnl END) as avg_loss
        FROM positions WHERE status='CLOSED'
    """).fetchone()
    conn.close()
    if not row or row["total"] == 0:
        return "Sem trades fechados ainda."
    wr = row["wins"] / row["total"] * 100 if row["total"] > 0 else 0
    return (
        f"\n=== TRADE SUMMARY ===\n"
        f"Total: {row['total']} | W: {row['wins']} | L: {row['losses']} | WR: {wr:.1f}%\n"
        f"PnL total: {row['total_pnl']:+.2f} USDC\n"
        f"Avg win: {row['avg_win']:+.2f} | Avg loss: {row['avg_loss']:+.2f}"
    )


def print_full_report():
    conn = get_conn()
    rows = conn.execute("""
        SELECT symbol, COUNT(*) as total,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(pnl) as total_pnl
        FROM positions WHERE status='CLOSED'
        GROUP BY symbol ORDER BY total_pnl DESC
    """).fetchall()
    conn.close()
    print(trade_summary())
    for row in rows:
        wr = row["wins"] / row["total"] * 100 if row["total"] > 0 else 0
        print(f"{row['symbol']}: {row['total']} trades | WR {wr:.0f}% | PnL {row['total_pnl']:+.2f}")

# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def _validate_credentials():
    placeholders = {"TOKEN_AQUI", "CHATID_AQUI", "APIKEY_AQUI", "SECRET_AQUI"}
    missing = [
        name for name, val in [
            ("TELEGRAM_TOKEN",     TELEGRAM_TOKEN),
            ("TELEGRAM_CHAT_ID",   TELEGRAM_CHAT_ID),
            ("BINANCE_API_KEY",    BINANCE_API_KEY),
            ("BINANCE_API_SECRET", BINANCE_API_SECRET),
        ]
        if val in placeholders
    ]
    if missing:
        raise SystemExit(f"[ERRO] Credenciais não definidas: {', '.join(missing)}")


def run():
    global SYMBOLS, SYMBOL_PRECISION

    _validate_credentials()
    init_db()
    sync_time()

    dinamicos, precisoes = get_top_futures_symbols(TOP_N_FUTURES)
    if dinamicos:
        SYMBOLS = dinamicos
    if precisoes:
        SYMBOL_PRECISION.update(precisoes)

    ultima_actualizacao_symbols = time.time()

    ip_atual = get_public_ip()
    tg(
        "🤖 <b>Claw Agent v8.0 iniciado</b>\n"
        f"Pares: {len(SYMBOLS)} (top {TOP_N_FUTURES} USDC-M) | Capital: {CAPITAL_MAX_BOT} USDC\n"
        f"Cross Margin | Alavancagem: {ALAVANCAGEM}x\n"
        f"Modo: TRENDING | SQLite: ativo\n"
        f"IP: <code>{ip_atual}</code>"
    )
    print(f"[v8.0] Claw Agent a correr — {len(SYMBOLS)} pares")

    ultimo_minuto_scan = -1
    ultima_sync_hora   = -1
    ultimo_resumo_hora = -1

    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            hora    = now_utc.strftime("%H:%M")
            mem     = load_memory()

            if now_utc.hour != ultima_sync_hora:
                sync_time()
                ultima_sync_hora = now_utc.hour

            if time.time() - ultima_actualizacao_symbols > 86400:
                novos, precisoes_novas = get_top_futures_symbols(TOP_N_FUTURES)
                if novos:
                    SYMBOLS = novos
                if precisoes_novas:
                    SYMBOL_PRECISION.update(precisoes_novas)
                print(f"[{hora}] Pares actualizados: {len(SYMBOLS)}")
                ultima_actualizacao_symbols = time.time()

            if now_utc.hour != ultimo_resumo_hora:
                ultimo_resumo_hora = now_utc.hour
                try:
                    trades_abertos = mem.get("trades_abertos", {})
                    n_abertos = len(trades_abertos)
                    linhas_pos = []
                    for sym, t in trades_abertos.items():
                        preco_a = get_price(sym)
                        if preco_a and t.get("entry", 0) > 0:
                            if t["direction"] == "LONG":
                                roi = (preco_a - t["entry"]) / t["entry"] * 100
                            else:
                                roi = (t["entry"] - preco_a) / t["entry"] * 100
                            icone = "🟢" if t["direction"] == "LONG" else "🔴"
                            linhas_pos.append(f"  {icone} {sym}: {roi:+.1f}% (entry {t['entry']:.4g})")

                    sample = list(BTC_SYMBOLS) + [s for s in SYMBOLS if s not in BTC_SYMBOLS][:8]
                    trending_list = []
                    for sym in sample:
                        kl = get_klines(sym)
                        if not kl or len(kl) < 30:
                            continue
                        h_r = [float(k[2]) for k in kl]
                        l_r = [float(k[3]) for k in kl]
                        c_r = [float(k[4]) for k in kl]
                        atr_r  = atr(h_r, l_r, c_r)
                        modo_r = detect_market_mode(c_r, atr_r)
                        if modo_r == "TRENDING":
                            trending_list.append(sym.replace("USDC", ""))

                    saldo = get_balance()
                    saldo_txt = f"{saldo:.2f} USDC" if saldo else "n/d"
                    pos_txt   = "\n".join(linhas_pos) if linhas_pos else "  Nenhuma"
                    trend_txt = ", ".join(trending_list) if trending_list else "nenhum"
                    tg(
                        f"📊 <b>Status {hora} UTC</b>\n"
                        f"Saldo: <b>{saldo_txt}</b> | Trades: {n_abertos}/{MAX_TRADES_ABERTOS}\n"
                        f"\n<b>Posições abertas:</b>\n{pos_txt}\n"
                        f"\n<b>TRENDING</b> ({len(trending_list)}/{len(sample)}): {trend_txt}"
                    )
                except Exception as _e:
                    print(f"[{hora}] Resumo horário falhou: {_e}")

            tem_posicoes = bool(mem.get("trades_abertos"))
            if tem_posicoes:
                gerir_posicoes(mem)
                mem = load_memory()

            minuto         = now_utc.minute
            sleep_interval = CHECK_POSICOES_FAST if tem_posicoes else CHECK_POSICOES
            if minuto % 5 != 0 or minuto == ultimo_minuto_scan:
                time.sleep(sleep_interval)
                continue

            ultimo_minuto_scan = minuto

            if not em_sessao():
                print(f"[{hora}] Fora sessão")
                continue

            bloqueado, motivo = circuit_breaker_activo(mem)
            if bloqueado:
                print(f"[{hora}] BLOQUEADO: {motivo}")
                continue

            posicoes_reais = get_positions()
            if posicoes_reais is None:
                print(f"[{hora}] get_positions falhou — scan ignorado")
                continue

            for symbol, pos in posicoes_reais.items():
                if symbol not in mem.get("trades_abertos", {}):
                    pending = mem.get("pending_sync", {})
                    is_bot_orphan = (symbol in pending and time.time() - pending[symbol] < 300)

                    if is_bot_orphan and symbol in SYMBOLS:
                        mem.get("pending_sync", {}).pop(symbol, None)
                        kl_sync = get_klines(symbol)
                        sync_stop_id = None
                        sync_sl = 0.0
                        if kl_sync and len(kl_sync) > 14:
                            h_s = [float(k[2]) for k in kl_sync]
                            l_s = [float(k[3]) for k in kl_sync]
                            c_s = [float(k[4]) for k in kl_sync]
                            atr_s   = atr(h_s, l_s, c_s)
                            entry_s = pos["entry"] if pos["entry"] > 0 else c_s[-1]
                            stop_side_s = "SELL" if pos["side"] == "LONG" else "BUY"
                            sync_sl = round(entry_s - atr_s * 1.5, 8) if pos["side"] == "LONG" else round(entry_s + atr_s * 1.5, 8)
                            sync_stop_id = place_stop_market(symbol, stop_side_s, sync_sl, 0)

                        mem.setdefault("trades_abertos", {})[symbol] = {
                            "direction":     pos["side"],
                            "entry":         pos["entry"],
                            "sl":            sync_sl,
                            "tp":            0,
                            "qty":           pos["qty"],
                            "qty_inicial":   abs(pos["qty"]),
                            "mode":          "SYNC",
                            "opened_at":     time.time(),
                            "stop_order_id": sync_stop_id,
                        }
                        save_memory(mem)
                        log_state_transition(symbol, None, "OPEN", "SYNC",
                                             f"entry={pos['entry']} side={pos['side']}")
                        try:
                            open_position(symbol, pos["side"], pos["entry"],
                                          0, 0, abs(pos["qty"]), "SYNC", sync_stop_id, None)
                        except Exception:
                            pass
                        dir_icon = "🟢 LONG" if pos["side"] == "LONG" else "🔴 SHORT"
                        stop_txt = f"Stop#{sync_stop_id}" if sync_stop_id else "SL em memória"
                        tg(f"🔄 <b>{dir_icon}</b> — {symbol} (órfão recuperado)\nEntrada: {pos['entry']:.4f} | 🔒 {stop_txt}")

                    elif symbol not in mem.get("posicoes_externas", {}):
                        externas = mem.setdefault("posicoes_externas", {})
                        externas[symbol] = {
                            "direction": pos["side"],
                            "entry":     pos["entry"],
                            "qty":       pos["qty"],
                            "opened_at": time.time(),
                            "alertas":   [],
                        }
                        save_memory(mem)
                        dir_icon  = "🟢 LONG" if pos["side"] == "LONG" else "🔴 SHORT"
                        notional  = abs(pos["qty"]) * pos["entry"] if pos["entry"] > 0 else 0
                        na_lista  = " (par do bot)" if symbol in SYMBOLS else ""
                        tg(
                            f"👁 <b>Posição manual detectada</b>\n"
                            f"{dir_icon} <b>{symbol}</b>{na_lista}\n"
                            f"Entrada: <code>{pos['entry']:.6g}</code> | "
                            f"Qty: {abs(pos['qty']):.4g} | ~{notional:.1f} USDC\n"
                            f"<i>Bot não gere nem coloca stops. P&amp;L não conta para os limites.</i>"
                        )

            externas = mem.get("posicoes_externas", {})
            fechadas_ext = []
            for symbol, ext in externas.items():
                if symbol in posicoes_reais:
                    preco_atual = get_price(symbol)
                    if preco_atual and ext["entry"] > 0:
                        roi = ((preco_atual - ext["entry"]) / ext["entry"] * 100
                               if ext["direction"] == "LONG"
                               else (ext["entry"] - preco_atual) / ext["entry"] * 100)
                        for nivel in [-5, -3, 3, 5, 10, 15, 20]:
                            tag = f"alerta_{nivel}"
                            if tag not in ext["alertas"]:
                                if (nivel < 0 and roi <= nivel) or (nivel > 0 and roi >= nivel):
                                    ext["alertas"].append(tag)
                                    save_memory(mem)
                                    icone = "🚨" if nivel < 0 else "💰"
                                    tg(f"{icone} <b>{symbol}</b> (externa) — ROI: <b>{roi:+.1f}%</b>\nEntrada: {ext['entry']:.6g} | Actual: {preco_atual:.6g}")
                else:
                    fechadas_ext.append(symbol)
                    preco_fecho = get_price(symbol)
                    if preco_fecho and ext["entry"] > 0:
                        roi = ((preco_fecho - ext["entry"]) / ext["entry"] * 100
                               if ext["direction"] == "LONG"
                               else (ext["entry"] - preco_fecho) / ext["entry"] * 100)
                        icone = "✅" if roi > 0 else "❌"
                        duracao_h = (time.time() - ext["opened_at"]) / 3600
                        tg(f"{icone} <b>{symbol}</b> (externa) — fechada\nROI: <b>{roi:+.1f}%</b> | Duração: {duracao_h:.1f}h")
            for symbol in fechadas_ext:
                del mem["posicoes_externas"][symbol]
            if fechadas_ext:
                save_memory(mem)

            if len(posicoes_reais) >= MAX_TRADES_ABERTOS:
                continue

            saldo_pre = get_balance()
            if saldo_pre is None or min(saldo_pre, CAPITAL_MAX_BOT) < RISCO_USDC * 3:
                continue

            agora = time.time()
            for sym in list(mem.get("pending_sync", {}).keys()):
                if agora - mem["pending_sync"][sym] > 600:
                    mem["pending_sync"].pop(sym)
                    save_memory(mem)

            for symbol in SYMBOLS:
                if symbol in posicoes_reais:
                    continue

                klines = get_klines(symbol)
                if not klines or len(klines) < LOOKBACK // 2:
                    continue

                closes         = [float(k[4]) for k in klines]
                highs          = [float(k[2]) for k in klines]
                lows           = [float(k[3]) for k in klines]
                volumes        = [float(k[5]) for k in klines]
                taker_buy_vols = [float(k[9]) for k in klines]

                atr_val = atr(highs, lows, closes)
                vwap    = get_daily_vwap(klines)
                mode    = detect_market_mode(closes, atr_val)

                if mode != "TRENDING":
                    print(f"[{hora}] {symbol} {mode}")
                    continue

                direction, score, detalhe = signal_trending(closes, highs, lows, volumes)
                print(f"[{hora}] {symbol} {mode} {detalhe}")

                if not direction:
                    continue

                vetado, motivo_veto = verificar_veto_simbolo(symbol, mem)
                if vetado:
                    print(f"[{hora}] {symbol} VETO_SIMBOLO {motivo_veto}")
                    continue

                if vwap is not None:
                    price_now = closes[-1]
                    if direction == "LONG"  and price_now < vwap:
                        continue
                    if direction == "SHORT" and price_now > vwap:
                        continue

                longs_reais  = [s for s, p in posicoes_reais.items() if p["side"] == "LONG"]
                shorts_reais = [s for s, p in posicoes_reais.items() if p["side"] == "SHORT"]
                longs_alt    = [s for s in longs_reais  if s not in BTC_SYMBOLS]
                shorts_alt   = [s for s in shorts_reais if s not in BTC_SYMBOLS]

                if direction == "LONG":
                    if symbol in BTC_SYMBOLS and any(s in BTC_SYMBOLS for s in longs_reais):
                        continue
                    if symbol not in BTC_SYMBOLS and len(longs_alt) >= MAX_LONGS_ALT:
                        continue
                if direction == "SHORT":
                    if symbol in BTC_SYMBOLS and any(s in BTC_SYMBOLS for s in shorts_reais):
                        continue
                    if symbol not in BTC_SYMBOLS and len(shorts_alt) >= MAX_SHORTS_ALT:
                        continue

                if posicoes_reais:
                    corr = calc_correlation(symbol, posicoes_reais)
                    if corr > CORR_MAX:
                        print(f"[{hora}] {symbol} CORR {corr:.2f} — skip")
                        continue

                abrir_trade(
                    symbol, direction, closes, highs, lows,
                    atr_val, mode, detalhe, mem, score,
                    volumes=volumes, taker_buy_vols=taker_buy_vols, klines=klines
                )
                mem = load_memory()
                time.sleep(2)
                if len(mem.get("trades_abertos", {})) >= MAX_TRADES_ABERTOS:
                    break

        except KeyboardInterrupt:
            tg("⛔ Claw Agent v8.0 parado manualmente.")
            print("\n[v8.0] A parar...")
            print_full_report()
            break
        except Exception as e:
            print(f"[ERRO GERAL] {e}")
            tg(f"⚠️ Claw Agent v8.0 erro: {e}")

        time.sleep(CHECK_POSICOES_FAST if mem.get("trades_abertos") else CHECK_POSICOES)


if __name__ == "__main__":
    run()
