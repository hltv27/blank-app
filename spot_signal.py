#!/usr/bin/env python3
"""
Spot Signal Bot — Binance Spot
Analisa top 100 pares USDT no mercado spot e envia sinais de compra via Telegram.
Não executa ordens — apenas notificações.

Arrancar: nohup python -u spot_signal.py > ~/spot_signal.log 2>&1 &
"""
import os
import time
import requests
from datetime import datetime, timezone

# ── Configuração ─────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",   "TOKEN_AQUI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "CHATID_AQUI")

SPOT_BASE_URL   = "https://api.binance.com"
VALOR_POR_SINAL = 25.0        # USDC a gastar por sinal
TOP_N_SPOT      = 100         # top N pares por volume 24h
MIN_VOLUME_USDT = 5_000_000   # volume mínimo 24h (5M USDT)
SCORE_MIN       = 5           # score mínimo para emitir sinal
ADX_MIN         = 22.5
SIGNAL_COOLDOWN = 4 * 3600    # não re-envia mesmo par durante 4h

EMA_FAST    = 9
EMA_SLOW    = 21
EMA_TREND   = 99
ATR_SL_MULT = 1.5
TP_RATIO    = 3.0

# ── Estado em memória ────────────────────────────────────────────────────────
_sinais_enviados: dict = {}  # symbol → timestamp do último sinal

# ── Telegram ─────────────────────────────────────────────────────────────────
def tg(msg: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=8
        )
    except Exception as e:
        print(f"[ERRO] Telegram: {e}")


# ── Indicadores (standalone) ─────────────────────────────────────────────────
def _ema(closes: list, period: int) -> list:
    if len(closes) < period:
        return closes[:]
    k = 2 / (period + 1)
    val = sum(closes[:period]) / period
    result = [val]
    for p in closes[period:]:
        val = p * k + val * (1 - k)
        result.append(val)
    return [result[0]] * (period - 1) + result


def _atr(highs, lows, closes, period=14) -> float:
    trs = [max(highs[i] - lows[i],
               abs(highs[i] - closes[i-1]),
               abs(lows[i]  - closes[i-1]))
           for i in range(1, len(closes))]
    if not trs:
        return 0.0
    if len(trs) < period:
        return sum(trs) / len(trs)
    val = sum(trs[:period]) / period
    for tr in trs[period:]:
        val = (val * (period - 1) + tr) / period
    return val


def _rsi(closes, period=14) -> float:
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        if d > 0: gains  += d
        else:     losses -= d
    ag = gains  / period
    al = losses / period
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        ag = (ag * (period - 1) + (d if d > 0 else 0)) / period
        al = (al * (period - 1) + (-d if d < 0 else 0)) / period
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def _adx(highs, lows, closes, period=14) -> float:
    if len(closes) < period * 2:
        return 0.0
    pdm, mdm, trs = [], [], []
    for i in range(1, len(closes)):
        up   = highs[i]  - highs[i-1]
        down = lows[i-1] - lows[i]
        pdm.append(up   if up > down and up > 0   else 0)
        mdm.append(down if down > up and down > 0 else 0)
        trs.append(max(highs[i] - lows[i],
                       abs(highs[i] - closes[i-1]),
                       abs(lows[i]  - closes[i-1])))

    def smooth(lst):
        s = sum(lst[:period])
        r = [s]
        for v in lst[period:]:
            s = s - s / period + v
            r.append(s)
        return r

    st = smooth(trs)
    sp = smooth(pdm)
    sm = smooth(mdm)
    dx = []
    for i in range(len(st)):
        if st[i] == 0:
            continue
        p = 100 * sp[i] / st[i]
        m = 100 * sm[i] / st[i]
        dx.append(100 * abs(p - m) / (p + m) if (p + m) > 0 else 0)
    return sum(dx[-period:]) / min(len(dx), period) if dx else 0.0


def _supertrend(highs, lows, closes, period=10, mult=3.0) -> bool | None:
    if len(closes) < period + 1:
        return None
    atr_v = _atr(highs, lows, closes, period)
    mid   = (highs[-1] + lows[-1]) / 2
    lower = mid - mult * atr_v
    return closes[-1] > lower


# ── Binance Spot API ──────────────────────────────────────────────────────────
def _get_klines(symbol: str, interval="5m", limit=220):
    try:
        r = requests.get(
            f"{SPOT_BASE_URL}/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10
        )
        data = r.json()
        return None if isinstance(data, dict) else data
    except Exception as e:
        print(f"[ERRO] klines {symbol}: {e}")
        return None


def get_top_spot_symbols(n=TOP_N_SPOT) -> list:
    STABLES = {"USDT","USDC","BUSD","DAI","TUSD","USDP","FDUSD","USDE"}
    EXCLUIR = {"UP","DOWN","BULL","BEAR","3L","3S","HEDGE"}
    try:
        tickers = requests.get(
            f"{SPOT_BASE_URL}/api/v3/ticker/24hr", timeout=15
        ).json()
        candidatos = []
        for t in tickers:
            sym = t.get("symbol", "")
            if not sym.endswith("USDT"):
                continue
            base = sym.replace("USDT", "").replace("1000", "")
            if base in STABLES or any(ex in base for ex in EXCLUIR):
                continue
            try:
                vol = float(t.get("quoteVolume", 0))
                if vol >= MIN_VOLUME_USDT:
                    candidatos.append((sym, vol))
            except Exception:
                continue
        candidatos.sort(key=lambda x: x[1], reverse=True)
        resultado = [s for s, _ in candidatos[:n]]
        print(f"[Spot] {len(resultado)} pares carregados (mín. vol {MIN_VOLUME_USDT/1e6:.0f}M USDT)")
        return resultado
    except Exception as e:
        print(f"[ERRO] get_top_spot_symbols: {e}")
        return []


# ── Análise de um par ─────────────────────────────────────────────────────────
def analisar(symbol: str) -> dict | None:
    klines = _get_klines(symbol)
    if not klines or len(klines) < 110:
        return None

    closed  = klines[:-1]  # exclui vela a formar
    closes  = [float(k[4]) for k in closed]
    highs   = [float(k[2]) for k in closed]
    lows    = [float(k[3]) for k in closed]

    price = closes[-1]
    if price <= 0:
        return None

    atr_v = _atr(highs, lows, closes)
    adx_v = _adx(highs, lows, closes)
    rsi_v = _rsi(closes)
    ema9  = _ema(closes, EMA_FAST)
    ema21 = _ema(closes, EMA_SLOW)
    ema99 = _ema(closes, EMA_TREND)

    # Filtros de entrada
    if adx_v < ADX_MIN:
        return None
    if atr_v / price < 0.0008:
        return None  # mercado morto
    if price < ema99[-1]:
        return None  # só compras em tendência ascendente
    if rsi_v > 75:
        return None  # sobrecomprado — não é boa entrada

    score = 0
    if ema9[-1] > ema21[-1] and ema9[-2] <= ema21[-2]:
        score += 3  # crossover bullish
    if ema9[-1] > ema21[-1]:
        score += 1
    if price > ema99[-1]:
        score += 2
    if rsi_v < 50:
        score += 1
    if rsi_v < 40:
        score += 1
    if _supertrend(highs, lows, closes) is True:
        score += 2
    if adx_v > 30:
        score += 1

    if score < SCORE_MIN:
        return None

    sl     = price - atr_v * ATR_SL_MULT
    tp     = price + atr_v * ATR_SL_MULT * TP_RATIO
    sl_pct = (price - sl) / price * 100
    tp_pct = (tp - price) / price * 100

    # Casas decimais do preço para formatação
    price_str = f"{price:.10f}".rstrip("0")
    dec = len(price_str.split(".")[-1]) if "." in price_str else 0
    dec = min(max(dec, 2), 8)

    qty = round(VALOR_POR_SINAL / price, dec)

    return {
        "price": price, "sl": sl, "tp": tp,
        "sl_pct": sl_pct, "tp_pct": tp_pct,
        "qty": qty, "score": score, "adx": adx_v, "rsi": rsi_v,
        "dec": dec,
    }


# ── Loop principal ────────────────────────────────────────────────────────────
def run():
    print("[Spot Signal] A arrancar...")
    tg(
        "📡 <b>Spot Signal Bot iniciado</b>\n"
        f"Top {TOP_N_SPOT} pares USDT | 25 USDC por sinal\n"
        "<i>Não executa ordens — só notificações</i>"
    )

    symbols         = get_top_spot_symbols()
    ultimo_minuto   = -1
    ultima_symbols  = time.time()
    ultimo_resumo   = -1

    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            minuto  = now_utc.minute
            hora    = now_utc.strftime("%H:%M")

            # Actualiza lista de pares a cada 24h
            if time.time() - ultima_symbols > 86400:
                symbols        = get_top_spot_symbols()
                ultima_symbols = time.time()

            # Resumo horário
            if now_utc.hour != ultimo_resumo:
                ultimo_resumo = now_utc.hour
                n_cooldown = sum(
                    1 for sym, ts in _sinais_enviados.items()
                    if time.time() - ts < SIGNAL_COOLDOWN
                )
                tg(
                    f"📊 <b>Spot Signal — {hora} UTC</b>\n"
                    f"Pares monitorizados: {len(symbols)}\n"
                    f"Sinais recentes (4h): {n_cooldown}"
                )

            # Scan alinhado com velas de 5 min
            if minuto % 5 != 0 or minuto == ultimo_minuto:
                time.sleep(10)
                continue

            ultimo_minuto = minuto
            print(f"[{hora}] Scan de {len(symbols)} pares...")

            encontrados = 0
            for symbol in symbols:
                # Cooldown por par
                if time.time() - _sinais_enviados.get(symbol, 0) < SIGNAL_COOLDOWN:
                    continue

                resultado = analisar(symbol)
                if not resultado:
                    continue

                encontrados += 1
                _sinais_enviados[symbol] = time.time()

                r    = resultado
                coin = symbol.replace("USDT", "")
                fmt  = f".{r['dec']}f"

                msg = (
                    f"📡 <b>SINAL SPOT — COMPRA</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🪙 <b>{coin}</b>\n"
                    f"💰 Entrada: <code>{r['price']:{fmt}}</code> USDT\n"
                    f"🛑 Stop Loss: <code>{r['sl']:{fmt}}</code>  (-{r['sl_pct']:.1f}%)\n"
                    f"🎯 Take Profit: <code>{r['tp']:{fmt}}</code>  (+{r['tp_pct']:.1f}%)\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💵 Gastar: <b>25 USDC</b>\n"
                    f"📦 Qty: <b>{r['qty']} {coin}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 Score: {r['score']} | ADX: {r['adx']:.0f} | RSI: {r['rsi']:.0f}\n"
                    f"<i>Execução manual — bot não coloca ordem</i>"
                )
                tg(msg)
                print(f"[{hora}] SINAL: {symbol} | Score {r['score']} | {r['price']:{fmt}}")
                time.sleep(1)

            if encontrados == 0:
                print(f"[{hora}] Sem sinais")

        except KeyboardInterrupt:
            tg("⛔ Spot Signal Bot parado.")
            print("[Spot Signal] Parado.")
            break
        except Exception as e:
            print(f"[ERRO GERAL] {e}")

        time.sleep(10)


if __name__ == "__main__":
    run()
