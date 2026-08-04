"""
Claw Agent v8.0 — Indicadores técnicos
Funções puras: entrada = listas de preços, saída = valor numérico.
"""
from datetime import datetime, timezone
from config import (
    RSI_PERIOD, ATR_PERIOD, STOCH_PERIOD, BB_PERIOD, BB_STD,
    EMA_FAST, EMA_SLOW, EMA_TREND,
    SUPERTREND_PERIOD, SUPERTREND_MULT,
    CMF_PERIOD, MFI_PERIOD, ROC_PERIOD, CVD_PERIOD,
    ATR_FLOOR_PCT
)


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
    gains   = [max(d, 0)   for d in deltas[-period:]]
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
    raw = sum(trs[-period:]) / period
    floor = closes[-1] * ATR_FLOOR_PCT if closes[-1] > 0 else 0.0
    return max(raw, floor)


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
        tr   = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
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
               period: int = SUPERTREND_PERIOD, mult: float = SUPERTREND_MULT) -> bool | None:
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
    # usa volumes[-2] (última vela fechada) — volumes[-1] é a vela a formar
    avg = sum(volumes[-lookback - 2:-2]) / lookback
    return volumes[-2] > avg * 0.8


def cmf_val(closes: list, highs: list, lows: list, volumes: list,
            period: int = CMF_PERIOD) -> float:
    if len(closes) < period + 1:
        return 0.0
    mfm_sum = vol_sum = 0.0
    for i in range(-period, 0):
        hl  = highs[i] - lows[i]
        mfm = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / hl if hl > 0 else 0.0
        mfm_sum += mfm * volumes[i]
        vol_sum  += volumes[i]
    return mfm_sum / vol_sum if vol_sum > 0 else 0.0


def mfi_val(closes: list, highs: list, lows: list, volumes: list,
            period: int = MFI_PERIOD) -> float:
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


def get_daily_vwap(klines: list) -> float | None:
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
