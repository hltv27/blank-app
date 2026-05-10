#!/usr/bin/env python3
"""
Claw Spot Scanner — Análise multi-timeframe para decisões de compra em spot.
Usa dados públicos da Binance (sem autenticação).

Uso:
    python3 spot_scanner.py SUI
    python3 spot_scanner.py BTC ETH SOL
    python3 spot_scanner.py --all
    python3 spot_scanner.py --top 50
    python3 spot_scanner.py --top 100
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO
# ─────────────────────────────────────────────
SPOT_URL = "https://api.binance.com"

WATCHLIST = [
    "SUIUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT",
    "LINKUSDT", "DOTUSDT", "BNBUSDT", "AVAXUSDT", "INJUSDT",
    "ARBUSDT",  "OPUSDT",  "APTUSDT", "SEIUSDT",  "TIAUSDT"
]

STABLECOINS = {
    "USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD", "USDP", "USDD",
    "FRAX", "LUSD", "GUSD", "SUSD", "USTC", "USDN", "AEUR", "EUR",
    "GBP", "BRL", "BIDR", "IDRT", "NGN", "RUB", "TRY", "VAI",
    "WBTC", "BETH", "WETH", "PAXG", "XAUT",
}

SKIP_CONTAINS = {"UP", "DOWN", "BEAR", "BULL", "3L", "3S", "2L", "2S"}


# ─────────────────────────────────────────────
#  API
# ─────────────────────────────────────────────

def get_klines(symbol: str, interval: str, limit: int = 200) -> list | None:
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
            return None
        return data
    except Exception:
        return None


def get_fear_greed() -> int:
    try:
        r = requests.get(
            "https://api.alternative.me/fng/?limit=1&format=json", timeout=8
        )
        return int(r.json()["data"][0]["value"])
    except Exception:
        return 50


def get_top_symbols(n: int = 100) -> list:
    """Top N coins por volume 24h em USDT (exclui stablecoins e tokens alavancados)."""
    try:
        r = requests.get(f"{SPOT_URL}/api/v3/ticker/24hr", timeout=15)
        tickers = r.json()
        pairs = []
        for t in tickers:
            sym = t["symbol"]
            if not sym.endswith("USDT"):
                continue
            base = sym[:-4]
            if base in STABLECOINS:
                continue
            if any(sk in base for sk in SKIP_CONTAINS):
                continue
            try:
                vol = float(t["quoteVolume"])
                pairs.append((sym, vol))
            except (ValueError, KeyError):
                continue
        pairs.sort(key=lambda x: x[1], reverse=True)
        return [sym for sym, _ in pairs[:n]]
    except Exception as e:
        print(f"  [ERRO] get_top_symbols: {e} — usando watchlist padrão")
        return WATCHLIST


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
    ath = max(closes)
    if ath == 0:
        return 0.0
    return (closes[-1] - ath) / ath * 100


def variacao_periodo(closes: list, dias: int) -> float:
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

    kl_w  = get_klines(symbol, "1w",  limit=52)
    kl_d  = get_klines(symbol, "1d",  limit=180)
    kl_4h = get_klines(symbol, "4h",  limit=120)

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
    vol_d    = volume_trend(v_d)
    dd       = drawdown_from_ath(c_d)
    var_7d   = variacao_periodo(c_d, 7)
    var_30d  = variacao_periodo(c_d, 30)
    var_90d  = variacao_periodo(c_d, 90)

    if ema9_d[-1] > ema21_d[-1] > ema50_d[-1]:
        score += 3
        sinais.append("✅ EMA stack bullish (9>21>50) diário")
    elif ema9_d[-1] < ema21_d[-1] < ema50_d[-1]:
        score -= 3
        alertas.append("🔴 EMA stack bearish (9<21<50) diário")
    else:
        sinais.append("⚠️  EMA diário misto")

    if ema200_d:
        if price > ema200_d[-1]:
            score += 2
            sinais.append(f"✅ Preço acima EMA200 diária ({ema200_d[-1]:.4g})")
        else:
            score -= 2
            alertas.append(f"🔴 Preço abaixo EMA200 diária ({ema200_d[-1]:.4g})")

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

    if adx_d >= 25:
        score += 2
        sinais.append(f"✅ ADX diário: {adx_d:.1f} — tendência forte")
    elif adx_d >= 15:
        sinais.append(f"⚠️  ADX diário: {adx_d:.1f} — tendência fraca")
    else:
        score -= 1
        alertas.append(f"🔴 ADX diário: {adx_d:.1f} — sem tendência")

    if st_d is True:
        score += 2
        sinais.append("✅ Supertrend diário: bullish")
    elif st_d is False:
        score -= 2
        alertas.append("🔴 Supertrend diário: bearish")

    sinais.append(f"   Volume diário: {vol_d}")
    if "CRESCENTE" in vol_d:
        score += 1

    sinais.append(f"   Drawdown vs ATH período: {dd:.1f}%")
    if dd < -60:
        score += 1
        sinais.append("✅ Desconto >60% do ATH — potencial acumulação")
    elif dd > -15:
        alertas.append("⚠️  Próximo do ATH do período — risco de topo")

    # ── TIMEFRAME SEMANAL ───────────────────────────────────────────────

    if kl_w and len(kl_w) >= 20:
        c_w, h_w, l_w, _ = parse(kl_w)
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
        c_4h, h_4h, l_4h, _ = parse(kl_4h)
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
        sinais.append(f"✅ Fear & Greed: {fg_val} (Extreme Fear) — bom para comprar")
    elif fg_val > 75:
        score -= 2
        alertas.append(f"⚠️  Fear & Greed: {fg_val} (Extreme Greed) — mercado eufórico")
    else:
        sinais.append(f"   Fear & Greed: {fg_val}")

    sinais.append(f"   Variação 7d:  {var_7d:+.1f}%")
    sinais.append(f"   Variação 30d: {var_30d:+.1f}%")
    sinais.append(f"   Variação 90d: {var_90d:+.1f}%")

    if score >= 10:
        recomendacao = "🟢 COMPRAR"
        resumo = "Múltiplos timeframes alinhados. Momentum e tendência positivos."
    elif score >= 5:
        recomendacao = "🟡 AGUARDAR"
        resumo = "Sinais mistos. Aguardar confirmação antes de entrar."
    elif score >= 0:
        recomendacao = "🟠 EVITAR"
        resumo = "Tendência incerta. Risco elevado de entrada errada."
    else:
        recomendacao = "🔴 NÃO COMPRAR"
        resumo = "Tendência negativa em múltiplos timeframes."

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


def imprimir_detalhes(r: dict):
    print(f"\n{'='*58}")
    print(f"  {r['symbol']}  |  {r['price']:.6g}  |  Score: {r['score']}")
    print(f"{'='*58}")
    print(f"  {r['recomendacao']}  —  {r['resumo']}")
    print(f"{'─'*58}")
    for s in r["sinais"]:
        print(f"  {s}")
    if r["alertas"]:
        print(f"{'─'*58}")
        for a in r["alertas"]:
            print(f"  {a}")
    print(f"{'─'*58}")
    print(f"  7d: {r['var_7d']:+.1f}%  |  30d: {r['var_30d']:+.1f}%  |  90d: {r['var_90d']:+.1f}%")
    print(f"  RSI diário: {r['rsi_d']:.1f}  |  ADX: {r['adx_d']:.1f}  |  DD ATH: {r['dd_ath']:.1f}%")


def imprimir_ranking(resultados: list, mostrar_detalhes_score: int = 5):
    ordenados = sorted(
        [r for r in resultados if "erro" not in r],
        key=lambda x: x["score"],
        reverse=True
    )
    erros = [r for r in resultados if "erro" in r]

    print(f"\n{'='*58}")
    print(f"  RANKING — {len(ordenados)} moedas analisadas")
    print(f"{'─'*58}")
    print(f"  {'#':>3}  {'SYMBOL':<12}  {'SCORE':>5}  {'7d':>7}  {'RSI':>5}  RECOMENDAÇÃO")
    print(f"{'─'*58}")
    for i, r in enumerate(ordenados, 1):
        print(
            f"  {i:>3}  {r['symbol']:<12}  {r['score']:>5}  "
            f"{r['var_7d']:>+6.1f}%  {r['rsi_d']:>5.1f}  {r['recomendacao']}"
        )
    if erros:
        print(f"{'─'*58}")
        print(f"  Sem dados: {', '.join(r['symbol'] for r in erros)}")
    print(f"{'='*58}")

    # Detalhes apenas para as moedas com score >= threshold
    top = [r for r in ordenados if r["score"] >= mostrar_detalhes_score]
    if top:
        print(f"\n  >>> Detalhes das moedas com score >= {mostrar_detalhes_score} <<<")
        for r in top:
            imprimir_detalhes(r)


# ─────────────────────────────────────────────
#  ENTRADA
# ─────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args:
        print("Uso: python3 spot_scanner.py SUI")
        print("     python3 spot_scanner.py BTC ETH SOL")
        print("     python3 spot_scanner.py --all")
        print("     python3 spot_scanner.py --top 50")
        print("     python3 spot_scanner.py --top 100")
        sys.exit(0)

    # Determinar lista de símbolos
    top_n = None
    if "--top" in args:
        idx = args.index("--top")
        try:
            top_n = int(args[idx + 1])
        except (IndexError, ValueError):
            top_n = 100

    print(f"\n{'='*58}")
    print(f"  CLAW SPOT SCANNER")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"{'='*58}")

    print("\n  Fetching Fear & Greed Index...")
    fg = get_fear_greed()
    print(f"  Fear & Greed: {fg}")

    if top_n is not None:
        print(f"\n  Fetching top {top_n} por volume Binance...")
        symbols = get_top_symbols(top_n)
        print(f"  {len(symbols)} símbolos encontrados.")
    elif "--all" in args:
        symbols = WATCHLIST
    else:
        symbols = [a for a in args if not a.startswith("--")]

    # Scan individual (sem --top): output detalhado imediato
    if top_n is None and "--all" not in args:
        resultados = []
        for sym in symbols:
            res = analisar(sym, fg)
            resultados.append(res)
            if "erro" in res:
                print(f"  {res['symbol']}: ERRO — {res['erro']}")
            else:
                imprimir_detalhes(res)
            time.sleep(0.3)
        if len(resultados) > 1:
            imprimir_ranking(resultados, mostrar_detalhes_score=999)
        sys.exit(0)

    # Scan em massa: paralelo com 8 workers
    workers = 8
    total   = len(symbols)
    done    = [0]
    resultados = [None] * total
    idx_map = {sym: i for i, sym in enumerate(symbols)}

    print(f"\n  Scan em paralelo ({workers} workers)...\n")

    def scan_one(sym):
        res = analisar(sym, fg)
        done[0] += 1
        status = res.get("recomendacao", "ERRO")[:10] if "erro" not in res else "ERRO"
        print(f"  [{done[0]:>3}/{total}] {sym:<14} score={res.get('score', '?'):>3}  {status}")
        return sym, res

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(scan_one, sym): sym for sym in symbols}
        for fut in as_completed(futures):
            sym, res = fut.result()
            resultados[idx_map[sym]] = res

    imprimir_ranking(resultados, mostrar_detalhes_score=7)
