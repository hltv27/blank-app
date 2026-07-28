"""
Claw Agent v8.0 — Filtros de entrada
Cada filtro retorna True (passa) ou False (bloqueia).
Todos os filtros são registados no SQLite via log_filter_event().
"""
import requests
import time
from datetime import datetime, timezone, timedelta
from config import (
    BASE_URL, OBI_VETO, MACRO_CACHE_MIN, MACRO_LOOKBACK_MIN, CORR_MAX,
    ATR_REGIME_MULT, ATR_REGIME_LOOKBACK, ATR_PERIOD,
    SPREAD_MAX_PCT, BTC_CRASH_PCT, FUNDING_RATE_MAX, TAKER_RATIO_MIN
)
from indicators import ema, atr, cvd_bias
from exchange import get_klines, _get_retry
from storage import log_filter_event

_fg_cache:    dict = {"value": 50, "ts": 0.0}
_macro_cache: dict = {"ts": 0.0, "bloqueado": False}
_mkt_cache:   dict = {}
_btc_trend_cache: dict = {"bullish": None, "ts": 0.0}


def _log(symbol: str, direction: str, name: str, passed: bool,
         price: float, score: int = 0, atr_pct: float = 0.0):
    """Wrapper: regista filtro no SQLite e devolve o resultado."""
    log_filter_event(symbol, direction, name, passed, price, score, atr_pct)
    return passed


# ─────────────────────────────────────────────
#  FILTROS GLOBAIS (não dependem de preço)
# ─────────────────────────────────────────────

def macro_event_proximo(look_ahead_min: int = 60,
                         look_back_min: int = MACRO_LOOKBACK_MIN) -> bool:
    """ForexFactory XML — bloqueia 60min antes E look_back_min depois de
    FOMC/CPI/NFP (volatilidade tende a continuar após o anúncio). Fail-open."""
    global _macro_cache
    now = time.time()
    if now - _macro_cache["ts"] < MACRO_CACHE_MIN * 60:
        return _macro_cache["bloqueado"]
    try:
        import xml.etree.ElementTree as ET
        r = requests.get(
            "https://nfs.faireconomy.media/ff_calendar_thisweek.xml", timeout=10
        )
        if r.status_code != 200:
            _macro_cache = {"ts": now, "bloqueado": False}
            return False
        root      = ET.fromstring(r.text)
        now_dt    = datetime.now(timezone.utc)
        look_dt   = now_dt + timedelta(minutes=look_ahead_min)
        back_dt   = now_dt - timedelta(minutes=look_back_min)
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
                name_el = event.find("title")
                name    = name_el.text if name_el is not None else "evento"
                if now_dt <= evt_dt <= look_dt:
                    mins_away = int((evt_dt - now_dt).total_seconds() / 60)
                    print(f"[MACRO] {name} em {mins_away}min — sem entrada")
                    _macro_cache = {"ts": now, "bloqueado": True}
                    return True
                if back_dt <= evt_dt < now_dt:
                    mins_ago = int((now_dt - evt_dt).total_seconds() / 60)
                    print(f"[MACRO] {name} há {mins_ago}min — sem entrada (pós-evento)")
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


def btc_trend_bullish() -> bool:
    """BTC 4H EMA9 > EMA21 — indica tendência bullish. Cache de 15min."""
    global _btc_trend_cache
    now = time.time()
    if now - _btc_trend_cache["ts"] < 900 and _btc_trend_cache["bullish"] is not None:
        return _btc_trend_cache["bullish"]
    try:
        klines_4h = get_klines("BTCUSDC", interval="4h", limit=30)
        if not klines_4h or len(klines_4h) < 25:
            return _btc_trend_cache.get("bullish", False)
        c4h = [float(k[4]) for k in klines_4h]
        ema9  = ema(c4h, 9)
        ema21 = ema(c4h, 21)
        bullish = ema9[-1] > ema21[-1]
        _btc_trend_cache = {"bullish": bullish, "ts": now}
        print(f"[BTC_TREND] 4H EMA9={'>' if bullish else '<'}EMA21 → {'BULLISH' if bullish else 'BEARISH'}")
        return bullish
    except Exception as e:
        print(f"[BTC_TREND] Falhou: {e}")
        return _btc_trend_cache.get("bullish", False)


# ─────────────────────────────────────────────
#  FILTROS POR SÍMBOLO
# ─────────────────────────────────────────────

def volatility_regime_ok(symbol: str, closes: list, highs: list,
                          lows: list, direction: str, price: float) -> bool:
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


def spread_ok(symbol: str, direction: str, price: float) -> bool:
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


def market_conditions_ok(symbol: str, direction: str, price: float) -> bool:
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
                print(f"[FUNDING] {symbol}: rate {rate:.4%} — LONG vetado (funding caro)")
                result = _log(symbol, direction, "FUNDING_RATE", False, price)
                _mkt_cache[cache_key] = {"ts": now, "result": result}
                return result
            if direction == "SHORT" and rate < -FUNDING_RATE_MAX:
                print(f"[FUNDING] {symbol}: rate {rate:.4%} — SHORT vetado (funding caro)")
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


def htf_1h_ok(symbol: str, direction: str, price: float) -> bool:
    """EMA9/21 no 1H — fail-closed."""
    try:
        klines_1h = get_klines(symbol, interval="1h", limit=50)
        if not klines_1h or len(klines_1h) < 30:
            print(f"[HTF1H] {symbol}: dados insuficientes — fail-closed")
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


def htf_4h_ok(symbol: str, direction: str, price: float) -> bool:
    """EMA9/21 no 4H — fail-closed."""
    try:
        klines_4h = get_klines(symbol, interval="4h", limit=30)
        if not klines_4h or len(klines_4h) < 25:
            print(f"[HTF4H] {symbol}: dados insuficientes — fail-closed")
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


def obi_ok(symbol: str, direction: str, price: float) -> bool:
    """Order Book Imbalance — pressão oposta domina o livro."""
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


def fear_greed_ok(symbol: str, direction: str, price: float) -> bool:
    fg_val = get_fear_greed()
    if direction == "LONG"  and fg_val < 20:
        print(f"[F&G] {symbol}: {fg_val} — Extreme Fear, LONG vetado")
        return _log(symbol, direction, "FEAR_GREED", False, price)
    if direction == "SHORT" and fg_val > 80:
        print(f"[F&G] {symbol}: {fg_val} — Extreme Greed, SHORT vetado")
        return _log(symbol, direction, "FEAR_GREED", False, price)
    return _log(symbol, direction, "FEAR_GREED", True, price)


def cvd_ok(symbol: str, direction: str, closes: list, volumes: list,
           taker_buy_vols: list, price: float) -> bool:
    if not taker_buy_vols or not volumes:
        return _log(symbol, direction, "CVD", True, price)
    cvd_v  = cvd_bias(taker_buy_vols, volumes)
    passed = True
    if direction == "LONG"  and cvd_v < -0.15:
        print(f"[CVD] {symbol}: {cvd_v:.2f} — pressão vendedora, LONG vetado")
        passed = False
    if direction == "SHORT" and cvd_v > 0.15:
        print(f"[CVD] {symbol}: {cvd_v:.2f} — pressão compradora, SHORT vetado")
        passed = False
    return _log(symbol, direction, "CVD", passed, price)


def taker_flow_ok(symbol: str, direction: str, taker_buy_vols: list,
                  volumes: list, price: float) -> bool:
    """Confirma que o fluxo de takers está alinhado com a direcção (últimas 5 velas)."""
    if not taker_buy_vols or not volumes or len(taker_buy_vols) < 3:
        return _log(symbol, direction, "TAKER_FLOW", True, price)
    n          = min(len(taker_buy_vols), len(volumes), 5)
    total_vol  = sum(volumes[-n:])
    if total_vol <= 0:
        return _log(symbol, direction, "TAKER_FLOW", True, price)
    taker_buy  = sum(taker_buy_vols[-n:])
    ratio      = taker_buy / total_vol
    passed     = True
    if direction == "LONG"  and ratio < TAKER_RATIO_MIN:
        print(f"[TAKER] {symbol}: buy ratio {ratio:.2f} < {TAKER_RATIO_MIN} — LONG vetado")
        passed = False
    if direction == "SHORT" and ratio > (1.0 - TAKER_RATIO_MIN):
        print(f"[TAKER] {symbol}: buy ratio {ratio:.2f} > {1.0 - TAKER_RATIO_MIN:.2f} — SHORT vetado")
        passed = False
    return _log(symbol, direction, "TAKER_FLOW", passed, price)


def vwap_ok(symbol: str, direction: str, closes: list, klines: list,
            price: float) -> bool:
    from indicators import get_daily_vwap_bands
    _, _, _, upper_2, lower_2 = get_daily_vwap_bands(klines)
    passed = True
    if direction == "LONG"  and upper_2 is not None and price > upper_2:
        print(f"[VWAP] {symbol}: preço acima +2σ ({upper_2:.4f}) — sobre-estendido")
        passed = False
    if direction == "SHORT" and lower_2 is not None and price < lower_2:
        print(f"[VWAP] {symbol}: preço abaixo -2σ ({lower_2:.4f}) — sobre-estendido")
        passed = False
    return _log(symbol, direction, "VWAP_2SIGMA", passed, price)


def bb_squeeze_ok(symbol: str, direction: str, closes: list,
                  volumes: list, price: float) -> bool:
    from indicators import bb_squeeze
    if not volumes:
        return _log(symbol, direction, "BB_SQUEEZE", True, price)
    squeezed = bb_squeeze(closes)
    if squeezed:
        print(f"[BB] {symbol}: squeeze — volatilidade comprimida, aguardar breakout")
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


def liquidity_sweep_detectado(closes: list, highs: list, lows: list,
                               volumes: list, taker_buy_vols: list,
                               direction: str, lookback: int = 20) -> bool:
    """Stop hunt institucional confirmado — alto sinal de probabilidade."""
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


def calc_correlation(symbol: str, posicoes_reais: dict, lookback: int = 30) -> float:
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
