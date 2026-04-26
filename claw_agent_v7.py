#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║           CLAW AGENT v7 — Binance Futures USDC          ║
║  Cross Margin | 10 Pares | Trending + Ranging Mode      ║
║  Capital máx: 50 USDC | Risco: 1.0 USDC/trade          ║
╚══════════════════════════════════════════════════════════╝

ALTERAÇÕES v7 vs v6:
  - Capital limitado a 50 USDC (buffer 40 USDC na conta)
  - Cross margin explícito (obrigatório PT)
  - 10 pares por volume/liquidez Futures
  - RSI oversold 42 / overbought 58 (era 35/65)
  - StochRSI veto >95 / <5 (era >90 / <10)
  - Score mínimo ≥ 4 (era ≥ 5)
  - ATR mínimo -20% (aceita volatilidade moderada)
  - Modo RANGING: Bollinger Bands mean-reversion
  - Ciclo 4 min (era 5 min) — mais responsivo
"""

import requests
import json
import os
import time
import hmac
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlencode

# ─────────────────────────────────────────────
#  CREDENCIAIS — edita aqui ou usa variáveis de ambiente
# ─────────────────────────────────────────────
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",   "TOKEN_AQUI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "CHATID_AQUI")
BINANCE_API_KEY  = os.getenv("BINANCE_API_KEY",  "APIKEY_AQUI")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "SECRET_AQUI")

# ─────────────────────────────────────────────
#  PARES — Top 10 por liquidez Futures USDC
# ─────────────────────────────────────────────
SYMBOLS = [
    "BTCUSDC", "ETHUSDC", "BNBUSDC", "SOLUSDC",
    "XRPUSDC", "DOGEUSDC", "AVAXUSDC", "LINKUSDC",
    "SUIUSDC",  "1000PEPEUSDC"
]

# Precisão de quantidade por par (casas decimais aceites pela Binance)
SYMBOL_PRECISION = {
    "BTCUSDC": 3, "ETHUSDC": 3, "BNBUSDC": 2, "SOLUSDC": 1,
    "XRPUSDC": 1, "DOGEUSDC": 0, "AVAXUSDC": 2, "LINKUSDC": 2,
    "SUIUSDC": 1, "1000PEPEUSDC": 0,
}

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO DE RISCO
# ─────────────────────────────────────────────
CAPITAL_MAX_BOT   = 50.0    # USDC — bot nunca usa mais que isto
RISCO_USDC        = 1.0     # USDC por trade (fixo)
ALAVANCAGEM       = 10      # 10x Cross Margin
RATIO_ALVO        = 2.0     # RR mínimo 2:1
MAX_LOSS_DIA      = 3.0     # Circuit breaker diário (USDC)
MAX_PERDAS_SEGUIDAS = 4     # Circuit breaker por série negativa
COOLDOWN_MIN      = 15      # Minutos bloqueado após circuit breaker
MAX_TRADES_ABERTOS = 2      # Máximo posições simultâneas (cross = cuidado)

# ─────────────────────────────────────────────
#  PARÂMETROS DA ESTRATÉGIA — v7 CALIBRADO
# ─────────────────────────────────────────────
# Trending mode
RSI_OVERSOLD      = 42.0    # era 35 — mais sinais em ranging
RSI_OVERBOUGHT    = 58.0    # era 65
STOCH_VETO_LONG   = 95.0    # era 90 — menos vetos
STOCH_VETO_SHORT  = 5.0     # era 10
SCORE_ALERTA      = 4       # era 5 — threshold mais acessível
SCORE_FORTE       = 6       # era 7

# ATR — volatilidade mínima (-20% vs v6)
ATR_MIN_PCT       = 0.0008  # 0.08% — filtra só mercados verdadeiramente mortos

# Ranging mode (Bollinger Bands)
BB_PERIOD         = 20
BB_STD            = 2.0
RANGING_ATR_MAX   = 0.006   # Se ATR < 0.6% → modo ranging

# Indicadores base
EMA_FAST          = 9
EMA_SLOW          = 21
EMA_TREND         = 99
RSI_PERIOD        = 14
ATR_PERIOD        = 14
STOCH_PERIOD      = 14
LOOKBACK          = 220     # Velas históricas (precisa de 220 para EMA99)

# Sessões (UTC) — manhã europeia + abertura NY
SESSOES_UTC       = [(7, 20)]
CHECK_EVERY       = 240     # 4 minutos entre ciclos

# Ficheiros de estado
MEMORY_FILE = "claw_memory_v7.json"
PNL_FILE    = "claw_pnl_v7.json"
BASE_URL    = "https://fapi.binance.com"

# ─────────────────────────────────────────────
#  BINANCE — FUNÇÕES BASE
# ─────────────────────────────────────────────
def _sign(params: dict) -> dict:
    params["timestamp"] = int(time.time() * 1000)
    query = urlencode(params)
    params["signature"] = hmac.new(
        BINANCE_API_SECRET.encode(),
        query.encode(),
        hashlib.sha256
    ).hexdigest()
    return params

def _headers() -> dict:
    return {"X-MBX-APIKEY": BINANCE_API_KEY}

def get_balance() -> float | None:
    """Saldo disponível USDC na conta Futures (Cross)."""
    try:
        r = requests.get(
            f"{BASE_URL}/fapi/v2/balance",
            params=_sign({}),
            headers=_headers(),
            timeout=10
        )
        for a in r.json():
            if a["asset"] == "USDC":
                return float(a["availableBalance"])
    except Exception as e:
        print(f"[ERRO] get_balance: {e}")
    return None

def get_klines(symbol: str, interval: str = "5m", limit: int = LOOKBACK) -> list | None:
    """Velas OHLCV."""
    try:
        r = requests.get(
            f"{BASE_URL}/fapi/v1/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10
        )
        data = r.json()
        if isinstance(data, dict):
            print(f"[ERRO] Binance klines {symbol}: {data.get('msg', data)}")
            return None
        return data
    except Exception as e:
        print(f"[ERRO] get_klines {symbol}: {e}")
    return None

def get_positions() -> dict:
    """Posições abertas por símbolo."""
    try:
        r = requests.get(
            f"{BASE_URL}/fapi/v2/positionRisk",
            params=_sign({}),
            headers=_headers(),
            timeout=10
        )
        pos = {}
        for p in r.json():
            qty = float(p.get("positionAmt", 0))
            if abs(qty) > 0:
                pos[p["symbol"]] = {
                    "qty": qty,
                    "entry": float(p.get("entryPrice", 0)),
                    "pnl": float(p.get("unRealizedProfit", 0)),
                    "side": "LONG" if qty > 0 else "SHORT"
                }
        return pos
    except Exception as e:
        print(f"[ERRO] get_positions: {e}")
    return {}

def set_leverage(symbol: str):
    """Define alavancagem 10x em Cross para o par."""
    try:
        # Cross margin
        requests.post(
            f"{BASE_URL}/fapi/v1/marginType",
            params=_sign({"symbol": symbol, "marginType": "CROSSED"}),
            headers=_headers(),
            timeout=10
        )
        # Alavancagem
        requests.post(
            f"{BASE_URL}/fapi/v1/leverage",
            params=_sign({"symbol": symbol, "leverage": ALAVANCAGEM}),
            headers=_headers(),
            timeout=10
        )
    except Exception as e:
        print(f"[AVISO] set_leverage {symbol}: {e}")

def place_order(symbol: str, side: str, qty: float) -> dict | None:
    """Market order. side = BUY | SELL."""
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
            headers=_headers(),
            timeout=10
        )
        return r.json()
    except Exception as e:
        print(f"[ERRO] place_order {symbol}: {e}")
    return None

def close_position(symbol: str, qty: float, side: str):
    """Fecha posição — side da posição aberta (inverte para fechar)."""
    close_side = "SELL" if side == "LONG" else "BUY"
    return place_order(symbol, close_side, abs(qty))

# ─────────────────────────────────────────────
#  TELEGRAM
# ─────────────────────────────────────────────
def tg(msg: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=8
        )
    except Exception as e:
        print(f"[ERRO] Telegram: {e}")

# ─────────────────────────────────────────────
#  INDICADORES TÉCNICOS
# ─────────────────────────────────────────────
def ema(closes: list, period: int) -> list:
    k = 2 / (period + 1)
    result = [closes[0]]
    for c in closes[1:]:
        result.append(c * k + result[-1] * (1 - k))
    return result

def rsi(closes: list, period: int = RSI_PERIOD) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas[-period:]]
    losses = [abs(min(d, 0)) for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def atr(highs: list, lows: list, closes: list, period: int = ATR_PERIOD) -> float:
    trs = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        trs.append(tr)
    if len(trs) < period:
        return 0.0
    return sum(trs[-period:]) / period

def stoch_rsi(closes: list, period: int = STOCH_PERIOD) -> float:
    """StochRSI 0–100."""
    if len(closes) < period * 2 + 1:
        return 50.0
    rsi_vals = []
    for i in range(period, len(closes)):
        rsi_vals.append(rsi(closes[max(0, i-period*2):i+1], period))
    if len(rsi_vals) < period:
        return 50.0
    recent = rsi_vals[-period:]
    min_r, max_r = min(recent), max(recent)
    if max_r == min_r:
        return 50.0
    return (rsi_vals[-1] - min_r) / (max_r - min_r) * 100

def bollinger_bands(closes: list, period: int = BB_PERIOD, std_mult: float = BB_STD):
    """Retorna (upper, middle, lower)."""
    if len(closes) < period:
        mid = closes[-1]
        return mid, mid, mid
    window = closes[-period:]
    mid = sum(window) / period
    variance = sum((c - mid) ** 2 for c in window) / period
    std = variance ** 0.5
    return mid + std_mult * std, mid, mid - std_mult * std

def volume_ok(volumes: list, lookback: int = 20) -> bool:
    """Volume actual acima da média dos últimos N períodos."""
    if len(volumes) < lookback + 1:
        return True
    avg = sum(volumes[-lookback-1:-1]) / lookback
    return volumes[-1] > avg * 0.9  # 90% da média (era 100% — mais permissivo)

# ─────────────────────────────────────────────
#  DETECÇÃO DE MODO DE MERCADO
# ─────────────────────────────────────────────
def detect_market_mode(closes: list, atr_val: float) -> str:
    """
    TRENDING: ATR >= ATR_MIN_PCT e MA99 com inclinação clara
    RANGING:  ATR entre ATR_MIN_PCT e RANGING_ATR_MAX — usa BB
    MORTO:    ATR < ATR_MIN_PCT — sem operação
    """
    price = closes[-1]
    if atr_val == 0 or price == 0:
        return "MORTO"

    atr_pct = atr_val / price

    if atr_pct < ATR_MIN_PCT:
        return "MORTO"

    # Verifica inclinação MA99 (últimas 5 velas)
    ema_vals = ema(closes, EMA_TREND)
    slope = (ema_vals[-1] - ema_vals[-6]) / ema_vals[-6] if ema_vals[-6] != 0 else 0

    if atr_pct <= RANGING_ATR_MAX and abs(slope) < 0.0008:
        return "RANGING"

    return "TRENDING"

# ─────────────────────────────────────────────
#  GERAÇÃO DE SINAL — MODO TRENDING
# ─────────────────────────────────────────────
def signal_trending(closes: list, highs: list, lows: list, volumes: list):
    """
    Estratégia EMA 9/21/99 + RSI + ATR.
    Retorna ("LONG"|"SHORT"|None, score, detalhes)
    """
    if len(closes) < EMA_TREND + 5:
        return None, 0, "DADOS_INSUF"

    price   = closes[-1]
    ema9    = ema(closes, EMA_FAST)
    ema21   = ema(closes, EMA_SLOW)
    ema99   = ema(closes, EMA_TREND)
    rsi_val = rsi(closes)
    sr_val  = stoch_rsi(closes)
    atr_val = atr(highs, lows, closes)

    # Veto StochRSI
    if sr_val > STOCH_VETO_LONG:
        return None, 0, f"VETO_SR_LONG {sr_val:.1f}"
    if sr_val < STOCH_VETO_SHORT:
        return None, 0, f"VETO_SR_SHORT {sr_val:.1f}"

    # Veto volume
    if not volume_ok(volumes):
        return None, 0, "VETO_VOL"

    score_long  = 0
    score_short = 0

    # RSI
    if rsi_val < RSI_OVERSOLD:
        score_long  += 3
    if rsi_val > RSI_OVERBOUGHT:
        score_short += 3

    # EMA cross 9/21
    if ema9[-1] > ema21[-1] and ema9[-2] <= ema21[-2]:
        score_long  += 3  # golden cross
    if ema9[-1] < ema21[-1] and ema9[-2] >= ema21[-2]:
        score_short += 3  # death cross

    # EMA9 acima/abaixo EMA21
    if ema9[-1] > ema21[-1]:
        score_long  += 1
    else:
        score_short += 1

    # Preço vs MA99 (filtro de tendência)
    if price > ema99[-1]:
        score_long  += 2
    else:
        score_short += 2

    # ATR momentum (confirmação de força)
    if atr_val / price > ATR_MIN_PCT * 1.5:
        score_long  += 1
        score_short += 1

    # Decisão
    if score_long >= SCORE_ALERTA and price > ema99[-1]:
        strength = "FORTE" if score_long >= SCORE_FORTE else "ALERTA"
        return "LONG", score_long, f"RSI {rsi_val:.1f} SR {sr_val:.1f} Score {score_long} [{strength}]"

    if score_short >= SCORE_ALERTA and price < ema99[-1]:
        strength = "FORTE" if score_short >= SCORE_FORTE else "ALERTA"
        return "SHORT", score_short, f"RSI {rsi_val:.1f} SR {sr_val:.1f} Score {score_short} [{strength}]"

    return None, max(score_long, score_short), f"SEM_SINAL RSI {rsi_val:.1f} SR {sr_val:.1f}"

# ─────────────────────────────────────────────
#  GERAÇÃO DE SINAL — MODO RANGING (Bollinger Bands)
# ─────────────────────────────────────────────
def signal_ranging(closes: list):
    """
    Mean-reversion via Bollinger Bands.
    Compra na banda inferior, vende na superior.
    Apenas quando RSI confirma (não exaustão).
    """
    if len(closes) < BB_PERIOD + 5:
        return None, 0, "DADOS_INSUF"

    price = closes[-1]
    upper, middle, lower = bollinger_bands(closes)
    rsi_val = rsi(closes)
    sr_val  = stoch_rsi(closes)

    # LONG: preço toca banda inferior + RSI não sobrevendido extremo
    if price <= lower * 1.001 and rsi_val < 48 and sr_val < 40:
        return "LONG", 4, f"BB_LONG preço {price:.4f} lower {lower:.4f} RSI {rsi_val:.1f}"

    # SHORT: preço toca banda superior + RSI não sobrecomprado extremo
    if price >= upper * 0.999 and rsi_val > 52 and sr_val > 60:
        return "SHORT", 4, f"BB_SHORT preço {price:.4f} upper {upper:.4f} RSI {rsi_val:.1f}"

    return None, 0, f"BB_NEUTRO mid {middle:.4f} RSI {rsi_val:.1f}"

# ─────────────────────────────────────────────
#  GESTÃO DE POSIÇÃO — SL/TP DINÂMICOS
# ─────────────────────────────────────────────
def calc_sl_tp(direction: str, price: float, atr_val: float, mode: str):
    """
    Trending: SL = 1.5 * ATR, TP = SL * RATIO_ALVO
    Ranging:  SL = 1.0 * ATR (mais apertado), TP = SL * 1.5
    """
    if mode == "RANGING":
        sl_dist = atr_val * 1.0
        ratio   = 1.5
    else:
        sl_dist = atr_val * 1.5
        ratio   = RATIO_ALVO

    if direction == "LONG":
        sl = price - sl_dist
        tp = price + sl_dist * ratio
    else:
        sl = price + sl_dist
        tp = price - sl_dist * ratio

    return sl, tp

def calc_qty(price: float, sl: float, symbol: str) -> float:
    """
    Quantidade = RISCO_USDC / sl_dist
    Garante perda máxima de exatamente RISCO_USDC se o SL for atingido.
    A alavancagem afecta a margem usada, não o PnL em valor absoluto.
    """
    sl_dist = abs(price - sl)
    if sl_dist == 0:
        return 0.0
    decimals = SYMBOL_PRECISION.get(symbol, 4)
    return round(RISCO_USDC / sl_dist, decimals)

# ─────────────────────────────────────────────
#  MEMÓRIA / PNL
# ─────────────────────────────────────────────
def load_memory() -> dict:
    try:
        with open(MEMORY_FILE) as f:
            return json.load(f)
    except Exception:
        return {
            "loss_dia": 0.0,
            "perdas_seguidas": 0,
            "trades_abertos": {},
            "ultimo_reset": "",
            "bloqueado_ate": 0,
            "total_trades": 0,
            "wins": 0,
            "losses": 0
        }

def save_memory(m: dict):
    with open(MEMORY_FILE, "w") as f:
        json.dump(m, f, indent=2)

def log_trade(symbol: str, direction: str, entry: float, sl: float, tp: float,
              qty: float, pnl: float | None = None, status: str = "OPEN"):
    try:
        trades = []
        try:
            with open(PNL_FILE) as f:
                trades = json.load(f)
        except Exception:
            pass
        trades.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "direction": direction,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "qty": qty,
            "pnl": pnl,
            "status": status
        })
        with open(PNL_FILE, "w") as f:
            json.dump(trades, f, indent=2)
    except Exception as e:
        print(f"[ERRO] log_trade: {e}")

# ─────────────────────────────────────────────
#  SESSÃO ACTIVA
# ─────────────────────────────────────────────
def em_sessao() -> bool:
    hora = datetime.now(timezone.utc).hour
    return any(inicio <= hora < fim for inicio, fim in SESSOES_UTC)

# ─────────────────────────────────────────────
#  GESTÃO DE POSIÇÕES ABERTAS (SL/TP manual)
# ─────────────────────────────────────────────
def gerir_posicoes(mem: dict):
    """
    Verifica posições abertas contra SL/TP definidos.
    Cross margin — SL manual para evitar liquidação da conta toda.
    """
    posicoes_binance = get_positions()
    trades_abertos   = mem.get("trades_abertos", {})

    for symbol, trade in list(trades_abertos.items()):
        if symbol not in posicoes_binance:
            # Posição fechou externamente (liquidação ou intervenção manual)
            mem["trades_abertos"].pop(symbol, None)
            tg(f"⚠️ {symbol} fechada externamente (SL {trade.get('sl', '?'):.4f} / TP {trade.get('tp', '?'):.4f})")
            continue

        pos   = posicoes_binance[symbol]
        price = pos["entry"]  # preço actual não está aqui — busca separado
        sl    = trade.get("sl", 0)
        tp    = trade.get("tp", 0)
        side  = trade.get("direction", "LONG")

        # Preço actual
        try:
            r = requests.get(
                f"{BASE_URL}/fapi/v1/ticker/price",
                params={"symbol": symbol},
                timeout=5
            )
            price = float(r.json()["price"])
        except Exception:
            continue

        hit_sl = (side == "LONG" and price <= sl) or (side == "SHORT" and price >= sl)
        hit_tp = (side == "LONG" and price >= tp) or (side == "SHORT" and price <= tp)

        if hit_sl or hit_tp:
            close_position(symbol, pos["qty"], side)
            pnl = pos["pnl"]
            mem["trades_abertos"].pop(symbol, None)

            if hit_tp:
                mem["wins"] = mem.get("wins", 0) + 1
                mem["perdas_seguidas"] = 0
                tg(f"✅ TP {symbol}\nPnL: {pnl:+.2f} USDC")
            else:
                mem["losses"] = mem.get("losses", 0) + 1
                mem["perdas_seguidas"] = mem.get("perdas_seguidas", 0) + 1
                mem["loss_dia"] = mem.get("loss_dia", 0) + abs(pnl)
                tg(f"🔴 SL {symbol}\nPnL: {pnl:+.2f} USDC\nPerdas hoje: {mem['loss_dia']:.2f} USDC")

            log_trade(
                symbol, side,
                trade.get("entry", 0), sl, tp,
                pos["qty"], pnl,
                "TP" if hit_tp else "SL"
            )

    save_memory(mem)

# ─────────────────────────────────────────────
#  CIRCUIT BREAKER
# ─────────────────────────────────────────────
def circuit_breaker_activo(mem: dict) -> tuple[bool, str]:
    now = time.time()

    # Reset diário à meia-noite UTC
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if mem.get("ultimo_reset") != hoje:
        mem["loss_dia"] = 0.0
        mem["perdas_seguidas"] = 0
        mem["bloqueado_ate"] = 0
        mem["ultimo_reset"] = hoje
        save_memory(mem)

    if now < mem.get("bloqueado_ate", 0):
        minutos = int((mem["bloqueado_ate"] - now) / 60)
        return True, f"COOLDOWN {minutos}min"

    if mem.get("loss_dia", 0) >= MAX_LOSS_DIA:
        mem["bloqueado_ate"] = now + COOLDOWN_MIN * 60
        save_memory(mem)
        return True, f"LOSS_DIA {mem['loss_dia']:.2f} USDC"

    if mem.get("perdas_seguidas", 0) >= MAX_PERDAS_SEGUIDAS:
        mem["bloqueado_ate"] = now + COOLDOWN_MIN * 60
        mem["perdas_seguidas"] = 0
        save_memory(mem)
        return True, f"PERDAS_SEGUIDAS {MAX_PERDAS_SEGUIDAS}"

    return False, ""

# ─────────────────────────────────────────────
#  ABERTURA DE TRADE
# ─────────────────────────────────────────────
def abrir_trade(symbol: str, direction: str, closes: list, highs: list,
                lows: list, atr_val: float, mode: str, detalhe: str, mem: dict):

    saldo = get_balance()
    if saldo is None:
        return
    capital_bot = min(saldo, CAPITAL_MAX_BOT)

    if capital_bot < RISCO_USDC * 3:
        tg(f"⚠️ Saldo insuficiente: {capital_bot:.2f} USDC")
        return

    price = closes[-1]
    sl, tp = calc_sl_tp(direction, price, atr_val, mode)
    qty    = calc_qty(price, sl, symbol)

    if qty <= 0:
        return

    # Configura cross + alavancagem
    set_leverage(symbol)

    # Executa ordem
    side  = "BUY" if direction == "LONG" else "SELL"
    order = place_order(symbol, side, qty)

    if order and order.get("status") == "FILLED":
        fill_price = float(order.get("avgPrice", price))
        sl, tp = calc_sl_tp(direction, fill_price, atr_val, mode)

        mem.setdefault("trades_abertos", {})[symbol] = {
            "direction": direction,
            "entry": fill_price,
            "sl": sl,
            "tp": tp,
            "qty": qty,
            "mode": mode,
            "pnl_estimado": RISCO_USDC * RATIO_ALVO
        }
        mem["total_trades"] = mem.get("total_trades", 0) + 1
        save_memory(mem)
        log_trade(symbol, direction, fill_price, sl, tp, qty)

        modo_icon = "📊" if mode == "RANGING" else "📈"
        dir_icon  = "🟢 LONG" if direction == "LONG" else "🔴 SHORT"

        tg(
            f"{modo_icon} <b>{dir_icon}</b> — {symbol}\n"
            f"Entrada: {fill_price:.4f}\n"
            f"SL: {sl:.4f} | TP: {tp:.4f}\n"
            f"Qty: {qty:.4f} | Modo: {mode}\n"
            f"Detalhe: {detalhe}"
        )
    else:
        erro = order.get("msg", "?") if order else "sem resposta"
        print(f"[ERRO] Ordem {symbol}: {erro}")

# ─────────────────────────────────────────────
#  VALIDAÇÃO DE CREDENCIAIS
# ─────────────────────────────────────────────
def _validate_credentials():
    placeholders = {"TOKEN_AQUI", "CHATID_AQUI", "APIKEY_AQUI", "SECRET_AQUI"}
    missing = [
        name for name, val in [
            ("TELEGRAM_TOKEN",    TELEGRAM_TOKEN),
            ("TELEGRAM_CHAT_ID",  TELEGRAM_CHAT_ID),
            ("BINANCE_API_KEY",   BINANCE_API_KEY),
            ("BINANCE_API_SECRET",BINANCE_API_SECRET),
        ]
        if val in placeholders
    ]
    if missing:
        raise SystemExit(f"[ERRO] Credenciais não definidas: {', '.join(missing)}")

# ─────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────
def run():
    _validate_credentials()
    tg(
        "🤖 <b>Claw Agent v7 iniciado</b>\n"
        f"Pares: {len(SYMBOLS)} | Capital máx: {CAPITAL_MAX_BOT} USDC\n"
        f"Cross Margin | Alavancagem: {ALAVANCAGEM}x\n"
        f"Modos: TRENDING + RANGING (BB)"
    )
    print(f"[v7] Claw Agent a correr — {len(SYMBOLS)} pares")

    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            hora    = now_utc.strftime("%H:%M")
            mem     = load_memory()

            # Gerir posições abertas (SL/TP manual Cross)
            if mem.get("trades_abertos"):
                gerir_posicoes(mem)
                mem = load_memory()  # recarrega após gestão

            # Fora de sessão
            if not em_sessao():
                print(f"[{hora}] Fora sessão")
                time.sleep(CHECK_EVERY)
                continue

            # Circuit breaker
            bloqueado, motivo = circuit_breaker_activo(mem)
            if bloqueado:
                print(f"[{hora}] BLOQUEADO: {motivo}")
                time.sleep(CHECK_EVERY)
                continue

            # Máximo trades abertos (cautela Cross Margin)
            if len(mem.get("trades_abertos", {})) >= MAX_TRADES_ABERTOS:
                print(f"[{hora}] Max trades abertos atingido")
                time.sleep(CHECK_EVERY)
                continue

            # ── Scan dos 10 pares ──
            for symbol in SYMBOLS:
                # Skip se já tem posição neste par
                if symbol in mem.get("trades_abertos", {}):
                    continue

                klines = get_klines(symbol)
                if not klines or len(klines) < LOOKBACK // 2:
                    continue

                closes  = [float(k[4]) for k in klines]
                highs   = [float(k[2]) for k in klines]
                lows    = [float(k[3]) for k in klines]
                volumes = [float(k[5]) for k in klines]

                atr_val = atr(highs, lows, closes)
                mode    = detect_market_mode(closes, atr_val)

                if mode == "MORTO":
                    print(f"[{hora}] {symbol} MERCADO_MORTO ATR {atr_val/closes[-1]*100:.3f}%")
                    continue

                # Sinal conforme modo
                if mode == "TRENDING":
                    direction, score, detalhe = signal_trending(closes, highs, lows, volumes)
                else:  # RANGING
                    direction, score, detalhe = signal_ranging(closes)

                print(f"[{hora}] {symbol} {mode} {detalhe}")

                if direction:
                    abrir_trade(
                        symbol, direction, closes, highs, lows,
                        atr_val, mode, detalhe, mem
                    )
                    mem = load_memory()
                    time.sleep(2)  # pausa entre trades

        except KeyboardInterrupt:
            tg("⛔ Claw Agent v7 parado manualmente.")
            break
        except Exception as e:
            print(f"[ERRO GERAL] {e}")
            tg(f"⚠️ Claw Agent erro: {e}")

        time.sleep(CHECK_EVERY)

# ─────────────────────────────────────────────
#  ARRANQUE
# ─────────────────────────────────────────────
if __name__ == "__main__":
    run()
