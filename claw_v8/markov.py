"""
Claw Agent v8.0 — Markov Regime Detection
First-order Markov chain over 5 market regimes. Builds a transition matrix
from the last MARKOV_LOOKBACK candles and predicts which regime is likely
next. Used as a score modifier in signal_trending().

Regimes
-------
0 BULL       — price > EMA21, EMA9 > EMA21, positive slope
1 BEAR       — price < EMA21, EMA9 < EMA21, negative slope
2 VOL_UP     — ATR spike + bullish structure
3 VOL_DOWN   — ATR spike + bearish structure
4 RANGING    — no clear structure
"""

N_STATES = 5
BULL, BEAR, VOL_UP, VOL_DOWN, RANGING = 0, 1, 2, 3, 4
_NAMES = {BULL: "BULL", BEAR: "BEAR", VOL_UP: "VOL_UP",
          VOL_DOWN: "VOL_DN", RANGING: "RANGING"}


def _classify(closes: list, highs: list, lows: list, i: int,
              atr_median: float, ema9: list, ema21: list,
              slope_min: float) -> int:
    price = closes[i]
    if price == 0 or i == 0:
        return RANGING

    tr = max(
        highs[i] - lows[i],
        abs(highs[i] - closes[i - 1]),
        abs(lows[i]  - closes[i - 1]),
    )
    vol_spike = atr_median > 0 and tr > atr_median * 2.0

    j = max(0, i - 5)
    slope = (ema21[i] - ema21[j]) / ema21[j] if ema21[j] != 0 else 0.0

    bull_struct = price > ema21[i] and ema9[i] > ema21[i]
    bear_struct = price < ema21[i] and ema9[i] < ema21[i]

    if vol_spike:
        return VOL_UP if slope >= 0 else VOL_DOWN

    if bull_struct and slope > slope_min:
        return BULL
    if bear_struct and slope < -slope_min:
        return BEAR
    return RANGING


def _ema_series(closes: list, period: int) -> list:
    k = 2 / (period + 1)
    out = [closes[0]]
    for c in closes[1:]:
        out.append(c * k + out[-1] * (1 - k))
    return out


def markov_regime_signal(closes: list, highs: list, lows: list) -> tuple:
    """
    Returns (direction_bias, score_delta, detail).
    direction_bias — 'LONG', 'SHORT', or None
    score_delta    — int added to the aligned direction score
    """
    from config import (MARKOV_LOOKBACK, MARKOV_MIN_PROB, MARKOV_SCORE,
                        EMA_FAST, EMA_SLOW, EMA_SLOPE_MIN)

    need = MARKOV_LOOKBACK + max(EMA_FAST, EMA_SLOW) + 10
    if len(closes) < need:
        return None, 0, "MKV_INSUF"

    # Work on the last (MARKOV_LOOKBACK + EMA_SLOW + 5) candles so EMA is warm
    window = MARKOV_LOOKBACK + EMA_SLOW + 5
    c = closes[-window:]
    h = highs[-window:]
    l = lows[-window:]

    ema9  = _ema_series(c, EMA_FAST)
    ema21 = _ema_series(c, EMA_SLOW)

    # Median TR as reference for vol-spike detection
    trs = [max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1]))
           for i in range(1, len(c))]
    trs_sorted = sorted(trs)
    atr_median = trs_sorted[len(trs_sorted) // 2] if trs_sorted else 0.0

    # Classify every candle into a regime
    regimes = [
        _classify(c, h, l, i, atr_median, ema9, ema21, EMA_SLOPE_MIN)
        for i in range(len(c))
    ]

    # Use only the last MARKOV_LOOKBACK regimes for the matrix
    seq = regimes[-MARKOV_LOOKBACK:]

    # Build transition matrix
    matrix = [[0] * N_STATES for _ in range(N_STATES)]
    for i in range(len(seq) - 1):
        matrix[seq[i]][seq[i + 1]] += 1

    # Normalise each row
    for row in matrix:
        total = sum(row)
        if total > 0:
            for j in range(N_STATES):
                row[j] /= total

    current   = seq[-1]
    probs     = matrix[current]
    row_sum   = sum(probs)

    # If this regime has never transitioned (no data) → neutral
    if row_sum == 0:
        return None, 0, f"MKV_{_NAMES[current]}_NODATA"

    p_bull = probs[BULL] + probs[VOL_UP]
    p_bear = probs[BEAR] + probs[VOL_DOWN]

    name = _NAMES[current]

    if p_bull >= MARKOV_MIN_PROB and p_bull > p_bear:
        return "LONG",  MARKOV_SCORE, f"MKV {name}→BULL {p_bull:.0%}"
    if p_bear >= MARKOV_MIN_PROB and p_bear > p_bull:
        return "SHORT", MARKOV_SCORE, f"MKV {name}→BEAR {p_bear:.0%}"

    return None, 0, f"MKV {name} bull={p_bull:.0%} bear={p_bear:.0%}"
