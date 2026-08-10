"""
Claw Agent v8.0 — Geração de sinal e cálculo de SL/TP
Fase 2: score por categorias independentes, RSI trend-following.
"""
from config import (
    EMA_FAST, EMA_SLOW, EMA_TREND, RSI_PERIOD, ATR_PERIOD,
    STOCH_VETO_LONG, STOCH_VETO_SHORT,
    SCORE_ALERTA, SCORE_FORTE, ATR_MIN_PCT, RATIO_ALVO,
    RISCO_USDC, SYMBOL_PRECISION, BB_PERIOD,
    ATR_SL_MULT_MIN, ATR_SL_MULT_MAX, SL_MIN_PCT, SL_MAX_PCT,
    ADX_TREND_MIN, ADX_TREND_MIN_MAJOR, ADX_TREND_MIN_ALT, EMA_SLOPE_MIN,
    TAKER_FEE
)

_MAJOR_SYMBOLS = {"BTCUSDC", "ETHUSDC", "BNBUSDC"}
from indicators import (
    ema, rsi, atr, stoch_rsi, adx, supertrend,
    bollinger_bands, volume_ok, cmf_val, mfi_val, roc_val
)


def detect_market_mode(closes: list, atr_val: float) -> str:
    """TRENDING ou MORTO. Fase 2: thresholds subidos para filtrar mercados laterais."""
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


def signal_trending(closes: list, highs: list, lows: list, volumes: list,
                    symbol: str = ""):
    """
    Fase 2: Score por 3 categorias independentes (TREND/MOMENTUM/FLOW).
    Cada categoria tem cap máximo — evita double-counting de indicadores correlacionados.
    RSI corrigido para trend-following (momentum > 50 = LONG, não mean-reversion).
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

    adx_min = ADX_TREND_MIN_MAJOR if symbol in _MAJOR_SYMBOLS else ADX_TREND_MIN_ALT
    if adx_val < adx_min:
        return None, 0, f"VETO_ADX {adx_val:.1f}"
    if sr_val > STOCH_VETO_LONG:
        return None, 0, f"VETO_SR_LONG {sr_val:.1f}"
    if sr_val < STOCH_VETO_SHORT:
        return None, 0, f"VETO_SR_SHORT {sr_val:.1f}"
    if not volume_ok(volumes):
        return None, 0, "VETO_VOL"

    # ═══ CATEGORIA: TREND (max 3) — direcção da tendência ═══
    trend_l = trend_s = 0

    # EMA 9/21 crossover (sinal forte de mudança)
    if ema9[-1] > ema21[-1] and ema9[-2] <= ema21[-2]:
        trend_l += 2
    if ema9[-1] < ema21[-1] and ema9[-2] >= ema21[-2]:
        trend_s += 2

    # EMA 9 > 21 alignment (tendência alinhada)
    if ema9[-1] > ema21[-1]:
        trend_l += 1
    else:
        trend_s += 1

    # Supertrend (confirmação de direcção)
    st_bull = supertrend(highs, lows, closes)
    if st_bull is True:
        trend_l += 1
    elif st_bull is False:
        trend_s += 1

    trend_l = min(trend_l, 3)
    trend_s = min(trend_s, 3)

    # ═══ CATEGORIA: MOMENTUM (max 3) — força do movimento ═══
    mom_l = mom_s = 0

    # RSI trend-following: > 50 = momentum positivo = LONG
    # (Fase 2: invertido da lógica anterior que comprava fraqueza)
    if rsi_val > 50:
        mom_l += 1
    if rsi_val > 60:
        mom_l += 1
    if rsi_val < 50:
        mom_s += 1
    if rsi_val < 40:
        mom_s += 1

    # ROC (rate of change)
    roc_v = roc_val(closes)
    if roc_v > 0.3:
        mom_l += 1
    elif roc_v < -0.3:
        mom_s += 1

    mom_l = min(mom_l, 3)
    mom_s = min(mom_s, 3)

    # ═══ CATEGORIA: FLOW (max 2) — fluxo de capital ═══
    flow_l = flow_s = 0

    cmf_v = cmf_val(closes, highs, lows, volumes)
    if cmf_v > 0.05:
        flow_l += 1
    elif cmf_v < -0.05:
        flow_s += 1

    mfi_v = mfi_val(closes, highs, lows, volumes)
    if mfi_v < 45:
        flow_l += 1
    elif mfi_v > 55:
        flow_s += 1

    flow_l = min(flow_l, 2)
    flow_s = min(flow_s, 2)

    # ═══ TOTAL (max 8) — exige pelo menos 2 categorias ═══
    score_long  = trend_l + mom_l + flow_l
    score_short = trend_s + mom_s + flow_s

    cats_long  = sum(1 for c in [trend_l, mom_l, flow_l] if c > 0)
    cats_short = sum(1 for c in [trend_s, mom_s, flow_s] if c > 0)

    detail_l = f"T{trend_l}+M{mom_l}+F{flow_l}={score_long} ({cats_long}cat)"
    detail_s = f"T{trend_s}+M{mom_s}+F{flow_s}={score_short} ({cats_short}cat)"

    # Gate: preço acima/abaixo da EMA99 (confirmação de tendência)
    if score_long >= SCORE_ALERTA and cats_long >= 2 and price > ema99[-1]:
        strength = "FORTE" if score_long >= SCORE_FORTE else "ALERTA"
        return "LONG", score_long, (
            f"RSI {rsi_val:.1f} ADX {adx_val:.1f} [{strength}] {detail_l}"
        )

    if score_short >= SCORE_ALERTA and cats_short >= 2 and price < ema99[-1]:
        strength = "FORTE" if score_short >= SCORE_FORTE else "ALERTA"
        return "SHORT", score_short, (
            f"RSI {rsi_val:.1f} ADX {adx_val:.1f} [{strength}] {detail_s}"
        )

    return None, max(score_long, score_short), (
        f"SEM_SINAL RSI {rsi_val:.1f} ADX {adx_val:.1f} L:{detail_l} S:{detail_s}"
    )


def calc_sl_tp(direction: str, price: float, atr_val: float, mode: str,
               score: int = 0, adx_val: float = 0.0):
    # Multiplier dinâmico: mercado volátil → SL mais largo para evitar stop prematuro
    atr_pct = atr_val / price if price > 0 else 0.0015
    if atr_pct > 0.003:
        sl_mult = ATR_SL_MULT_MAX       # >0.3% ATR — mercado agitado
    elif atr_pct < 0.001:
        sl_mult = ATR_SL_MULT_MIN       # <0.1% ATR — mercado calmo
    else:
        sl_mult = 2.0

    # Distância: mínimo 0.5% (Binance rejeita <0.1%), máximo 3% (evita SLs demasiado largos)
    sl_dist = max(atr_val * sl_mult, price * SL_MIN_PCT)
    sl_dist = min(sl_dist, price * SL_MAX_PCT)
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
    commission_per_unit = price * TAKER_FEE * 2
    qty = round(RISCO_USDC / (sl_dist + commission_per_unit), decimals)
    return qty
