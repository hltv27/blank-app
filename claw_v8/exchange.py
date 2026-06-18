"""
Claw Agent v8.0 — Binance API
Todas as chamadas HTTP à Binance e ao Telegram.
"""
import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode
from config import (
    BASE_URL, BINANCE_API_KEY, BINANCE_API_SECRET,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, SYMBOL_PRECISION, PRICE_PRECISION
)

_time_offset_ms = 0
_SAPI_URL = "https://api.binance.com"
_last_ip_alerta_ts = 0  # rate limit: só envia alerta de IP bloqueado 1x por 10min


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


def _get_retry(url: str, params: dict = None, timeout: int = 10,
               max_retries: int = 4, headers: dict = None):
    """GET com exponential backoff para 429/5xx."""
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
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=8
        )
        if not r.ok:
            print(f"[ERRO] Telegram HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[ERRO] Telegram: {e}")


def get_public_ip() -> str:
    try:
        return requests.get("https://api.ipify.org", timeout=5).text.strip()
    except Exception:
        return "desconhecido"


def get_balance() -> float | None:
    """Saldo USDC/BNFCR via /fapi/v2/account.
    Tenta marginBalance, walletBalance, crossWalletBalance, availableBalance.
    Fallback: totalMarginBalance da conta."""
    _FIELDS = ("marginBalance", "walletBalance", "crossWalletBalance", "availableBalance")
    for attempt in range(2):
        try:
            r = requests.get(
                f"{BASE_URL}/fapi/v2/account",
                params=_sign({}), headers=_headers(), timeout=10
            )
            data = r.json()
            if _is_timestamp_error(data):
                print("[AVISO] get_balance: timestamp desfasado — a resincronizar")
                sync_time()
                continue
            if isinstance(data, list):
                break
            total = 0.0
            debug = {}
            for a in data.get("assets", []):
                name = a.get("asset")
                if name in ("USDC", "BNFCR"):
                    debug[name] = {f: a.get(f) for f in _FIELDS}
                    for field in _FIELDS:
                        val = float(a.get(field) or "0")
                        if val > 0:
                            total = max(total, val)
                            break
            if total > 0:
                return round(total, 4)
            # Fallback: totalMarginBalance ao nível da conta
            tmb = float(data.get("totalMarginBalance") or "0")
            if tmb > 0:
                print(f"[AVISO] get_balance: usando totalMarginBalance={tmb:.4f}")
                return round(tmb, 4)
            print(f"[AVISO] get_balance: saldo 0 — campos USDC/BNFCR: {debug}")
        except Exception as e:
            print(f"[ERRO] get_balance: {e}")
            break
    return None


def get_klines(symbol: str, interval: str = "5m", limit: int = 220) -> list | None:
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


def get_positions() -> dict | None:
    for attempt in range(2):
        try:
            r = requests.get(
                f"{BASE_URL}/fapi/v2/positionRisk",
                params=_sign({}), headers=_headers(), timeout=10
            )
            data = r.json()
            if _is_timestamp_error(data):
                print("[AVISO] get_positions: timestamp desfasado — a resincronizar")
                sync_time()
                continue
            if isinstance(data, dict):
                msg = data.get("msg", "")
                print(f"[ERRO] get_positions: {msg}")
                if "Invalid API-key, IP" in msg:
                    global _last_ip_alerta_ts
                    if time.time() - _last_ip_alerta_ts > 600:
                        _last_ip_alerta_ts = time.time()
                        tg(f"🔒 <b>IP bloqueado</b>\nNovo IP: <code>{get_public_ip()}</code>\n<i>Adiciona este IP na Binance API → Restrições de IP</i>")
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


def get_margin_ratio_global() -> float | None:
    """Rácio de margem de TODA a conta (USDT-M + USDC-M). Usado para guard de liquidação."""
    for attempt in range(2):
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
            print(f"[ERRO] get_margin_ratio_global: {e}")
            break
    return None


def get_margin_ratio() -> float | None:
    for attempt in range(2):
        try:
            r = requests.get(
                f"{BASE_URL}/fapi/v2/account",
                params=_sign({}), headers=_headers(), timeout=10
            )
            data = r.json()
            if _is_timestamp_error(data):
                print("[AVISO] get_margin_ratio: timestamp desfasado — a resincronizar")
                sync_time()
                continue
            # Soma USDC + BNFCR — conta EU tem maintMargin em USDC mas capital em BNFCR
            total_maint   = 0.0
            total_balance = 0.0
            for asset in data.get("assets", []):
                if asset.get("asset") in ("USDC", "BNFCR"):
                    total_maint += float(asset.get("maintMargin") or "0")
                    margin = float(asset.get("marginBalance") or "0")
                    wallet = float(asset.get("walletBalance") or "0")
                    total_balance += margin or wallet
            if total_balance > 0:
                return round(total_maint / total_balance * 100, 2)
            break
        except Exception as e:
            print(f"[ERRO] get_margin_ratio: {e}")
            break
    return None


def get_price(symbol: str) -> float | None:
    try:
        r = requests.get(
            f"{BASE_URL}/fapi/v1/ticker/price",
            params={"symbol": symbol}, timeout=5
        )
        return float(r.json()["price"])
    except Exception:
        return None


def set_leverage(symbol: str):
    try:
        requests.post(
            f"{BASE_URL}/fapi/v1/marginType",
            params=_sign({"symbol": symbol, "marginType": "CROSSED"}),
            headers=_headers(), timeout=10
        )
        from config import ALAVANCAGEM
        requests.post(
            f"{BASE_URL}/fapi/v1/leverage",
            params=_sign({"symbol": symbol, "leverage": ALAVANCAGEM}),
            headers=_headers(), timeout=10
        )
    except Exception as e:
        print(f"[AVISO] set_leverage {symbol}: {e}")


def place_order(symbol: str, side: str, qty: float) -> dict | None:
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


def place_stop_market(symbol: str, side: str, stop_price: float, qty: float) -> int | None:
    """STOP_MARKET via /fapi/v1/algoOrder com closePosition=true.
    Binance BNFCR: usa algoOrder sem algoType (causa erro 'type missing')."""
    try:
        decimals = PRICE_PRECISION.get(symbol, 2)
        params = {
            "symbol":        symbol,
            "side":          side,
            "orderType":     "STOP_MARKET",
            "stopPrice":     f"{stop_price:.{decimals}f}",
            "closePosition": "true",
            "workingType":   "MARK_PRICE",
            "priceProtect":  "true",
        }
        for attempt in range(3):
            signed = _sign(params)
            r = requests.post(
                f"{BASE_URL}/fapi/v1/algoOrder",
                params=signed, headers=_headers(), timeout=10
            )
            data = r.json()
            if _is_timestamp_error(data):
                sync_time()
                continue
            if "algoId" in data:
                return data["algoId"]
            print(f"[AVISO] stop_market {symbol}: {data.get('msg', data)}")
            break
    except Exception as e:
        print(f"[ERRO] place_stop_market {symbol}: {e}")
    return None


def place_take_profit(symbol: str, side: str, tp_price: float) -> int | None:
    """TAKE_PROFIT_MARKET via /fapi/v1/algoOrder com closePosition=true.
    Binance BNFCR: endpoint regular rejeita TAKE_PROFIT_MARKET — usa algoOrder."""
    try:
        decimals = PRICE_PRECISION.get(symbol, 2)
        params = {
            "symbol":        symbol,
            "side":          side,
            "orderType":     "TAKE_PROFIT_MARKET",
            "stopPrice":     f"{tp_price:.{decimals}f}",
            "closePosition": "true",
            "workingType":   "MARK_PRICE",
            "priceProtect":  "true",
        }
        for attempt in range(2):
            r = requests.post(
                f"{BASE_URL}/fapi/v1/algoOrder",
                params=_sign(params), headers=_headers(), timeout=10
            )
            data = r.json()
            if _is_timestamp_error(data):
                sync_time()
                continue
            if "algoId" in data:
                return data["algoId"]
            print(f"[AVISO] take_profit {symbol}: {data.get('msg', data)}")
            break
    except Exception as e:
        print(f"[ERRO] place_take_profit {symbol}: {e}")
    return None


def place_trailing_stop(symbol: str, side: str, callback_rate: float,
                        activation_price: float) -> int | None:
    try:
        decimals = PRICE_PRECISION.get(symbol, 2)
        params = {
            "symbol":          symbol,
            "side":            side,
            "orderType":       "TRAILING_STOP_MARKET",
            "callbackRate":    f"{callback_rate}",
            "activationPrice": f"{activation_price:.{decimals}f}",
            "closePosition":   "true",
            "workingType":     "MARK_PRICE",
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
        # Fallback: STOP_MARKET fixo a 1.5× callback abaixo/acima da activação
        msg = data.get("msg", str(data))
        print(f"[AVISO] trailing_stop {symbol}: {msg} — fallback STOP_MARKET")
        sl_price = (activation_price * (1 - callback_rate / 100) if side == "SELL"
                    else activation_price * (1 + callback_rate / 100))
        return place_stop_market(symbol, side, sl_price, 0)
    except Exception as e:
        print(f"[ERRO] place_trailing_stop {symbol}: {e}")
    return None


def close_position(symbol: str, qty: float, side: str):
    close_side = "SELL" if side == "LONG" else "BUY"
    return place_order(symbol, close_side, abs(qty))


def get_top_futures_symbols(n: int = 20, min_days: int = 30) -> tuple:
    """
    Busca top N pares USDC-M por volume 24h.
    Retorna (lista_symbols, qty_precision_map, price_precision_map).
    Exclui: stablecoins, tokens alavancados, moedas com menos de min_days dias.
    """
    STABLES  = {"USDT","USDC","BUSD","DAI","TUSD","USDP","FDUSD","USDE","PYUSD"}
    EXCLUIR  = {"UP","DOWN","BULL","BEAR","3L","3S","HEDGE"}
    min_age_ms = min_days * 24 * 3600 * 1000
    agora_ms   = int(time.time() * 1000)

    try:
        info = requests.get(f"{BASE_URL}/fapi/v1/exchangeInfo", timeout=10).json()
        precision_map       = {}
        price_precision_map = {}
        usdc_symbols        = set()

        for s in info.get("symbols", []):
            if not (s.get("quoteAsset") == "USDC"
                    and s.get("status") == "TRADING"
                    and s.get("contractType") == "PERPETUAL"):
                continue
            sym = s["symbol"]

            # Filtro de maturidade — mínimo min_days dias listada
            onboard = s.get("onboardDate", agora_ms)
            if (agora_ms - onboard) < min_age_ms:
                print(f"[v8] {sym} excluído — listada há menos de {min_days} dias")
                continue

            usdc_symbols.add(sym)

            for f in s.get("filters", []):
                ft = f.get("filterType")
                if ft == "LOT_SIZE":
                    step = f.get("stepSize", "1")
                    decimals = len(step.rstrip("0").split(".")[1]) if "." in step else 0
                    precision_map[sym] = decimals
                elif ft == "PRICE_FILTER":
                    tick = f.get("tickSize", "0.01")
                    pdec = len(tick.rstrip("0").split(".")[1]) if "." in tick else 0
                    price_precision_map[sym] = pdec

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
        excluidas  = len(candidatos) - len(resultado)
        print(f"[v8] Top {n} USDC-M (mín. {min_days} dias): {resultado}")
        if excluidas > 0:
            print(f"[v8] {excluidas} pares com volume mas excluídos (< {min_days} dias)")
        return resultado, precision_map, price_precision_map

    except Exception as e:
        print(f"[AVISO] get_top_futures_symbols falhou: {e} — usando lista estática")
        return [], {}, {}


def cancel_order(symbol: str, order_id) -> bool:
    """Cancela uma ordem MARKET pelo orderId. Para stops/TP usar cancel_algo_order."""
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
            r = requests.delete(
                f"{BASE_URL}/fapi/v1/order",
                params=params, headers=_headers(), timeout=10
            )
            data = r.json()
        if data.get("status") == "CANCELED":
            return True
        return False
    except Exception as e:
        print(f"[AVISO] cancel_order {symbol} #{order_id}: {e}")
        return False


def get_open_algo_orders(symbol: str) -> list:
    """Lista algoIds de STOP_MARKET/TAKE_PROFIT_MARKET abertos para o símbolo.
    Usado antes do primeiro lock numa posição externa — pode já existir um stop
    colocado manualmente pelo utilizador, que tem de ser cancelado primeiro
    (a conta só permite um STOP_MARKET closePosition por símbolo)."""
    try:
        r = requests.get(
            f"{_SAPI_URL}/sapi/v1/algo/futures/openOrders",
            params=_sign({"symbol": symbol}), headers=_headers(), timeout=10
        )
        data = r.json()
        if _is_timestamp_error(data):
            sync_time()
            r = requests.get(
                f"{_SAPI_URL}/sapi/v1/algo/futures/openOrders",
                params=_sign({"symbol": symbol}), headers=_headers(), timeout=10
            )
            data = r.json()
        orders = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(orders, list):
            return [o["algoId"] for o in orders if o.get("symbol") == symbol and "algoId" in o]
    except Exception as e:
        print(f"[AVISO] get_open_algo_orders {symbol}: {e}")
    return []


def cancel_algo_order(symbol: str, algo_id) -> bool:
    """Cancela stop/TP. Tenta primeiro como algoId (trailing stops), depois como
    orderId regular (STOP_MARKET colocados via /fapi/v1/order)."""
    try:
        # Tentativa 1: algo endpoint (trailing stops / TP)
        params = _sign({"symbol": symbol, "algoId": int(algo_id)})
        r = requests.delete(
            f"{_SAPI_URL}/sapi/v1/algo/futures/order",
            params=params, headers=_headers(), timeout=10
        )
        data = r.json()
        if _is_timestamp_error(data):
            sync_time()
            params = _sign({"symbol": symbol, "algoId": int(algo_id)})
            r = requests.delete(
                f"{_SAPI_URL}/sapi/v1/algo/futures/order",
                params=params, headers=_headers(), timeout=10
            )
            data = r.json()
        if data.get("success") is True or data.get("code") == 200:
            return True
    except Exception as e:
        print(f"[AVISO] cancel_algo_order algo attempt {symbol} #{algo_id}: {e}")

    # Tentativa 2: ordem regular (STOP_MARKET via /fapi/v1/order)
    return cancel_order(symbol, algo_id)
