"""
Claw Agent v8.0 — Geração de sinal e cálculo de SL/TP
Lógica idêntica à v7.1. Zero alterações estratégicas.
"""
from config import (
    EMA_FAST, EMA_SLOW, EMA_TREND, RSI_PERIOD, ATR_PERIOD,
    RSI_OVERSOLD, RSI_OVERBOUGHT, STOCH_VETO_LONG, STOCH_VETO_SHORT,
    SCORE_ALERTA, SCORE_FORTE, ATR_MIN_PCT, RATIO_ALVO,
    RISCO_USDC, SYMBOL_PRECISION, BB_PERIOD
)
from indicators import (
    ema, rsi, atr, stoch_rsi, adx, supertrend,
    bollinger_bands, volume_ok, cmf_val, mfi_val, roc_val
)


def detect_market_mode(closes: list, atr_val: float) -> str:
    """TRENDING ou MORTO. RANGING removido (risco de liquidação em alts)."""
    price = closes[-1]
    if atr_val == 0 or price == 0:
        return "MORTO"
    if atr_val / price < ATR_MIN_PCT:
        return "MORTO"
    ema_vals = ema(closes, EMA_TREND)
    slope    = (ema_vals[-1] - ema_vals[-6]) / ema_vals[-6] if ema_vals[-6] != 0 else 0
    if abs(slope) < 0.0008:
        return "MORTO"
    return "TRENDING"


def signal_trending(closes: list, highs: list, lows: list, volumes: list):
    """
    EMA 9/21/99 + RSI + ADX + Supertrend + CMF + MFI + ROC.
    Retorna (direction, score, detalhe).
    """
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

    if adx_val < 25:
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


def calc_sl_tp(direction: str, price: float, atr_val: float, mode: str,
               score: int = 0, adx_val: float = 0.0):
    sl_dist = atr_val * 1.5
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


def calc_qty(price: float, sl: float, symbol: str) -> float:
    sl_dist  = abs(price - sl)
    if sl_dist == 0:
        return 0.0
    decimals = SYMBOL_PRECISION.get(symbol, 4)
    return round(RISCO_USDC / sl_dist, decimals)
