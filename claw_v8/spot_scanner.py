#!/usr/bin/env python3
"""
Claw Spot Scanner — Análise multi-timeframe para decisões de compra em spot.
Usa dados públicos da Binance (sem autenticação).

Uso:
    python3 spot_scanner.py SUI
    python3 spot_scanner.py BTC ETH SOL
    python3 spot_scanner.py --all
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import time
from datetime import datetime, timezone

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO
# ─────────────────────────────────────────────
BASE_URL = "https://fapi.binance.com"
SPOT_URL = "https://api.binance.com"

WATCHLIST = [
    "SUIUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT",
    "LINKUSDT", "DOTUSDT", "BNBUSDT", "AVAXUSDT", "INJUSDT",
    "ARBUSDT",  "OPUSDT",  "APTUSDT", "SEIUSDT",  "TIAUSDT"
]

# ─────────────────────────────────────────────
#  API
# ─────────────────────────────────────────────

def get_klines(symbol: str, interval: str, limit: int = 200) -> list | None:
    """Klines spot da Binance (sem autenticação)."""
    # Tenta símbolo com USDT se não tiver sufixo
    if not symbol.endswith("USDT") and not symbol.endswith("USDC"):
        symbol = symbol + "USDT"
    try:
        r = requests.get(
            f"{SPOT_URL}/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10
        )
        data = r.json()
        if isinstance(data, dict):
            print(f"  [ERRO] {symbol} {interval}: {data.get('msg', data)}")
            return None
        return data
    except Exception as e:
        print(f"  [ERRO] klines {symbol}: {e}")
        return None


def get_fear_greed() -> int:
    try:
        r = requests.get(
            "https://api.alternative.me/fng/?limit=1&format=json", timeout=8
        )
        return int(r.json()["data"][0]["value"])
    except Exception:
        return 50


# ─────────────────────────────────────────────
#  INDICADORES
# ─────────────────────────────────────────────

def ema(closes: list, period: int) -> list:
    k = 2 / (period + 1)
    result = [closes[0]]
    for c in closes[1:]:
        result.append(c * k + result[-1] * (1 - k))
    return result


def rsi(closes: list, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas   = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains    = [max(d, 0)      for d in deltas[-period:]]
    losses   = [abs(min(d, 0)) for d in deltas[-period:]]
    avg_gain = sum(gains)  / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))


def atr(highs: list, lows: list, closes: list, period: int = 14) -> float:
    trs = [max(highs[i] - lows[i],
               abs(highs[i] - closes[i-1]),
               abs(lows[i]  - closes[i-1]))
           for i in range(1, len(closes))]
    if len(trs) < period:
        return 0.0
    return sum(trs[-period:]) / period


def adx(highs: list, lows: list, closes: list, period: int = 14) -> float:
    if len(closes) < period * 2:
        return 0.0
    tr_list, plus_dm, minus_dm = [], [], []
    for i in range(1, len(closes)):
        tr   = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        up   = highs[i] - highs[i-1]
        down = lows[i-1] - lows[i]
        tr_list.append(tr)
        plus_dm.append(up   if up > down and up > 0   else 0)
        minus_dm.append(down if down > up and down > 0 else 0)

    def smooth(data, n):
        s = [sum(data[:n])]
        for d in data[n:]:
            s.append(s[-1] - s[-1]/n + d)
        return s

    if len(tr_list) < period:
        return 0.0
    atr_s   = smooth(tr_list,  period)
    plus_s  = smooth(plus_dm,  period)
    minus_s = smooth(minus_dm, period)
    dx_list = []
    for i in range(len(atr_s)):
        if atr_s[i] == 0:
            continue
        pdi   = 100 * plus_s[i]  / atr_s[i]
        mdi   = 100 * minus_s[i] / atr_s[i]
        denom = pdi + mdi
        dx_list.append(100 * abs(pdi-mdi)/denom if denom else 0)
    if len(dx_list) < period:
        return 0.0
    return sum(dx_list[-period:]) / period


def supertrend(highs: list, lows: list, closes: list,
               period: int = 10, mult: float = 3.0) -> bool | None:
    need = period * 2 + 2
    if len(closes) < need:
        return None
    h, l, c = highs[-need:], lows[-need:], closes[-need:]
    trs = [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1, len(c))]
    direction = True
    prev_ub = prev_lb = None
    for i in range(1, len(c)):
        start   = max(0, i - period)
        atr_i   = sum(trs[start:i]) / max(i-start, 1)
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


def volume_trend(volumes: list, period: int = 20) -> str:
    """Tendência de volume: CRESCENTE / DECRESCENTE / NEUTRO."""
    if len(volumes) < period * 2:
        return "NEUTRO"
    avg_ant = sum(volumes[-period*2:-period]) / period
    avg_rec = sum(volumes[-period:])          / period
    if avg_ant == 0:
        return "NEUTRO"
    chg = (avg_rec - avg_ant) / avg_ant * 100
    if chg > 20:
        return f"CRESCENTE +{chg:.0f}%"
    if chg < -20:
        return f"DECRESCENTE {chg:.0f}%"
    return f"NEUTRO {chg:+.0f}%"


def drawdown_from_ath(closes: list) -> float:
    """Drawdown actual desde o ATH do período analisado (%)."""
    ath = max(closes)
    if ath == 0:
        return 0.0
    return (closes[-1] - ath) / ath * 100


def variacao_periodo(closes: list, dias: int) -> float:
    """Variação % nos últimos N períodos."""
    if len(closes) < dias + 1:
        return 0.0
    return (closes[-1] - closes[-dias-1]) / closes[-dias-1] * 100


# ─────────────────────────────────────────────
#  ANÁLISE PRINCIPAL
# ─────────────────────────────────────────────

def analisar(symbol: str, fg_val: int) -> dict:
    """Análise completa em 3 timeframes: semanal, diário, 4H."""
    if not symbol.upper().endswith(("USDT", "USDC")):
        symbol = symbol.upper() + "USDT"
    else:
        symbol = symbol.upper()

    print(f"\n  Fetching {symbol}...")

    # Dados
    kl_w  = get_klines(symbol, "1w",  limit=52)   # 1 ano semanal
    kl_d  = get_klines(symbol, "1d",  limit=180)  # 6 meses diário
    kl_4h = get_klines(symbol, "4h",  limit=120)  # 20 dias 4H

    if not kl_d or len(kl_d) < 50:
        return {"symbol": symbol, "erro": "dados insuficientes"}

    def parse(kl):
        c = [float(k[4]) for k in kl]
        h = [float(k[2]) for k in kl]
        l = [float(k[3]) for k in kl]
        v = [float(k[5]) for k in kl]
        return c, h, l, v

    c_d, h_d, l_d, v_d = parse(kl_d)
    price = c_d[-1]

    score   = 0
    sinais  = []
    alertas = []

    # ── TIMEFRAME DIÁRIO ────────────────────────────────────────────────

    ema9_d   = ema(c_d, 9)
    ema21_d  = ema(c_d, 21)
    ema50_d  = ema(c_d, 50)
    ema200_d = ema(c_d, 200) if len(c_d) >= 200 else None
    rsi_d    = rsi(c_d)
    adx_d    = adx(h_d, l_d, c_d)
    st_d     = supertrend(h_d, l_d, c_d)
    atr_d    = atr(h_d, l_d, c_d)
    vol_d    = volume_trend(v_d)
    dd       = drawdown_from_ath(c_d)
    var_7d   = variacao_periodo(c_d, 7)
    var_30d  = variacao_periodo(c_d, 30)
    var_90d  = variacao_periodo(c_d, 90)

    # EMA stack diário (9 > 21 > 50)
    if ema9_d[-1] > ema21_d[-1] > ema50_d[-1]:
        score += 3
        sinais.append("✅ EMA stack bullish (9>21>50) diário")
    elif ema9_d[-1] < ema21_d[-1] < ema50_d[-1]:
        score -= 3
        alertas.append("🔴 EMA stack bearish (9<21<50) diário")
    else:
        sinais.append("⚠️  EMA diário misto")

    # Preço vs EMA200 diário
    if ema200_d:
        if price > ema200_d[-1]:
            score += 2
            sinais.append(f"✅ Preço acima EMA200 diária ({ema200_d[-1]:.4f})")
        else:
            score -= 2
            alertas.append(f"🔴 Preço abaixo EMA200 diária ({ema200_d[-1]:.4f})")

    # RSI diário
    if 40 <= rsi_d <= 60:
        score += 1
        sinais.append(f"✅ RSI diário neutro/saudável: {rsi_d:.1f}")
    elif rsi_d < 35:
        score += 2
        sinais.append(f"✅ RSI diário oversold: {rsi_d:.1f} — potencial entrada")
    elif rsi_d > 70:
        score -= 1
        alertas.append(f"⚠️  RSI diário overbought: {rsi_d:.1f}")
    else:
        sinais.append(f"   RSI diário: {rsi_d:.1f}")

    # ADX diário
    if adx_d >= 25:
        score += 2
        sinais.append(f"✅ ADX diário: {adx_d:.1f} — tendência forte")
    elif adx_d >= 15:
        sinais.append(f"⚠️  ADX diário: {adx_d:.1f} — tendência fraca")
    else:
        score -= 1
        alertas.append(f"🔴 ADX diário: {adx_d:.1f} — sem tendência")

    # Supertrend diário
    if st_d is True:
        score += 2
        sinais.append("✅ Supertrend diário: bullish")
    elif st_d is False:
        score -= 2
        alertas.append("🔴 Supertrend diário: bearish")

    # Volume
    sinais.append(f"   Volume diário: {vol_d}")
    if "CRESCENTE" in vol_d:
        score += 1

    # Drawdown
    sinais.append(f"   Drawdown vs ATH período: {dd:.1f}%")
    if dd < -60:
        score += 1
        sinais.append("✅ Desconto >60% do ATH — potencial acumulação")
    elif dd > -15:
        alertas.append("⚠️  Próximo do ATH do período — risco de topo")

    # ── TIMEFRAME SEMANAL ───────────────────────────────────────────────

    if kl_w and len(kl_w) >= 20:
        c_w, h_w, l_w, v_w = parse(kl_w)
        ema9_w  = ema(c_w, 9)
        ema21_w = ema(c_w, 21)
        rsi_w   = rsi(c_w)
        st_w    = supertrend(h_w, l_w, c_w)

        if ema9_w[-1] > ema21_w[-1]:
            score += 2
            sinais.append("✅ EMA 9>21 semanal: tendência alta")
        else:
            score -= 2
            alertas.append("🔴 EMA 9<21 semanal: tendência baixa")

        if st_w is True:
            score += 2
            sinais.append("✅ Supertrend semanal: bullish")
        elif st_w is False:
            score -= 2
            alertas.append("🔴 Supertrend semanal: bearish")

        if rsi_w < 40:
            score += 2
            sinais.append(f"✅ RSI semanal oversold: {rsi_w:.1f}")
        elif rsi_w > 65:
            score -= 1
            alertas.append(f"⚠️  RSI semanal elevado: {rsi_w:.1f}")
        else:
            sinais.append(f"   RSI semanal: {rsi_w:.1f}")

    # ── TIMEFRAME 4H ────────────────────────────────────────────────────

    if kl_4h and len(kl_4h) >= 30:
        c_4h, h_4h, l_4h, v_4h = parse(kl_4h)
        ema9_4h  = ema(c_4h, 9)
        ema21_4h = ema(c_4h, 21)
        rsi_4h   = rsi(c_4h)

        if ema9_4h[-1] > ema21_4h[-1]:
            score += 1
            sinais.append("✅ EMA 9>21 no 4H: momentum positivo")
        else:
            score -= 1
            alertas.append("⚠️  EMA 9<21 no 4H: momentum negativo")

        sinais.append(f"   RSI 4H: {rsi_4h:.1f}")

    # ── FEAR & GREED ────────────────────────────────────────────────────

    if fg_val < 25:
        score += 2
        sinais.append(f"✅ Fear & Greed: {fg_val} (Extreme Fear) — historicamente bom para comprar")
    elif fg_val > 75:
        score -= 2
        alertas.append(f"⚠️  Fear & Greed: {fg_val} (Extreme Greed) — mercado eufórico")
    else:
        sinais.append(f"   Fear & Greed: {fg_val}")

    # ── VARIAÇÕES ───────────────────────────────────────────────────────

    sinais.append(f"   Variação 7d:  {var_7d:+.1f}%")
    sinais.append(f"   Variação 30d: {var_30d:+.1f}%")
    sinais.append(f"   Variação 90d: {var_90d:+.1f}%")

    # ── SCORE MÁXIMO POSSÍVEL = ~20 ─────────────────────────────────────

    # Decisão
    if score >= 10:
        recomendacao = "🟢 COMPRAR"
        resumo = "Múltiplos timeframes alinhados. Momentum e tendência positivos."
    elif score >= 5:
        recomendacao = "🟡 AGUARDAR"
        resumo = "Sinais mistos. Aguardar confirmação antes de entrar."
    elif score >= 0:
        recomendacao = "🟠 EVITAR POR AGORA"
        resumo = "Tendência incerta. Risco elevado de entrada errada."
    else:
        recomendacao = "🔴 NÃO COMPRAR"
        resumo = "Tendência negativa em múltiplos timeframes. Aguardar reversão."

    return {
        "symbol":       symbol,
        "price":        price,
        "score":        score,
        "recomendacao": recomendacao,
        "resumo":       resumo,
        "sinais":       sinais,
        "alertas":      alertas,
        "var_7d":       var_7d,
        "var_30d":      var_30d,
        "var_90d":      var_90d,
        "dd_ath":       dd,
        "rsi_d":        rsi_d,
        "adx_d":        adx_d,
    }


def imprimir(resultado: dict):
    if "erro" in resultado:
        print(f"\n{'='*55}")
        print(f"  {resultado['symbol']}: ERRO — {resultado['erro']}")
        return

    r = resultado
    print(f"\n{'='*55}")
    print(f"  {r['symbol']}  |  Preço: {r['price']:.6g}  |  Score: {r['score']}")
    print(f"{'='*55}")
    print(f"  RECOMENDAÇÃO: {r['recomendacao']}")
    print(f"  {r['resumo']}")
    print(f"{'─'*55}")
    for s in r["sinais"]:
        print(f"  {s}")
    if r["alertas"]:
        print(f"{'─'*55}")
        for a in r["alertas"]:
            print(f"  {a}")
    print(f"{'─'*55}")
    print(f"  7d: {r['var_7d']:+.1f}%  |  30d: {r['var_30d']:+.1f}%  |  90d: {r['var_90d']:+.1f}%")
    print(f"  RSI diário: {r['rsi_d']:.1f}  |  ADX: {r['adx_d']:.1f}  |  DD ATH período: {r['dd_ath']:.1f}%")


# ─────────────────────────────────────────────
#  ENTRADA
# ─────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args:
        print("Uso: python3 spot_scanner.py SUI")
        print("     python3 spot_scanner.py BTC ETH SOL")
        print("     python3 spot_scanner.py --all")
        sys.exit(0)

    if "--all" in args:
        symbols = WATCHLIST
    else:
        symbols = args

    print(f"\n{'='*55}")
    print(f"  CLAW SPOT SCANNER")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"{'='*55}")

    print("\n  Fetching Fear & Greed Index...")
    fg = get_fear_greed()
    print(f"  Fear & Greed: {fg}")

    resultados = []
    for sym in symbols:
        res = analisar(sym, fg)
        resultados.append(res)
        imprimir(res)
        time.sleep(0.5)  # evitar rate limit

    if len(resultados) > 1:
        print(f"\n{'='*55}")
        print("  RANKING (por score)")
        print(f"{'─'*55}")
        for r in sorted(resultados, key=lambda x: x.get("score", -99), reverse=True):
            if "erro" not in r:
                print(f"  {r['recomendacao']:30s}  {r['symbol']:15s}  score: {r['score']}")
        print(f"{'='*55}\n")
