"""
Claw Agent v8.0 — Modo papel (paper trading)
Simula a conta de futuros com os preços reais da Binance, sem enviar ordens.
Substitui as funções de conta/ordens de exchange.py quando PAPER_TRADING=True
(ver o fim de exchange.py). Estratégia, filtros e gestão de posições correm
exactamente iguais — só a execução é simulada.

Simulação:
  - Fill MARKET ao último preço ± PAPER_SLIPPAGE (sempre contra nós)
  - Comissão taker (TAKER_FEE) em cada fill, entrada e saída
  - STOP_MARKET / TRAILING / TP verificados a cada get_positions() (≈15s)
    e executados ao preço actual (não ao trigger — conservador)
  - Funding não simulado
Cada trade fechado fica em paper_trades.jsonl com bruto, comissões e líquido.
"""
import json
import os
import threading
import time

from config import PAPER_SALDO_INICIAL, TAKER_FEE

PAPER_SLIPPAGE = 0.0002  # 0.02% contra nós em cada fill MARKET
_MAINT_RATE    = 0.004   # aproximação da margem de manutenção (0.4% do nocional)

_DIR         = os.path.dirname(os.path.abspath(__file__))
_STATE_FILE  = os.path.join(_DIR, "paper_state.json")
TRADES_FILE  = os.path.join(_DIR, "paper_trades.jsonl")

_lock  = threading.RLock()
_get_price = None  # injectado por exchange.py (preço real, endpoint público)
_state: dict = {}


def init(get_price_fn):
    global _get_price, _state
    _get_price = get_price_fn
    try:
        with open(_STATE_FILE, encoding="utf-8") as f:
            _state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _state = {"saldo": PAPER_SALDO_INICIAL, "posicoes": {}, "stops": {},
                  "next_id": 1, "fees_total": 0.0, "inicio_ts": int(time.time())}
        _save()
    print(f"[PAPEL] Modo papel activo — saldo simulado {_state['saldo']:.2f} USDC, "
          f"{len(_state['posicoes'])} posições abertas")


def _save():
    tmp = _STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_state, f, indent=1)
    os.replace(tmp, _STATE_FILE)


def _novo_id() -> int:
    i = _state["next_id"]
    _state["next_id"] = i + 1
    return i


def _executar(symbol: str, side: str, qty: float, motivo: str) -> dict | None:
    """Fill MARKET simulado. side BUY/SELL, qty positiva."""
    price = _get_price(symbol)
    if not price or qty <= 0:
        return None
    fill  = price * (1 + PAPER_SLIPPAGE) if side == "BUY" else price * (1 - PAPER_SLIPPAGE)
    fee   = qty * fill * TAKER_FEE
    delta = qty if side == "BUY" else -qty
    _state["saldo"]      -= fee
    _state["fees_total"] += fee

    pos = _state["posicoes"].get(symbol)
    if pos is None or (pos["qty"] > 0) == (delta > 0):
        # Abre ou aumenta posição — preço médio ponderado
        if pos is None:
            pos = {"qty": 0.0, "entry": 0.0, "fees": 0.0, "aberta_ts": int(time.time())}
        novo_qty     = pos["qty"] + delta
        pos["entry"] = (abs(pos["qty"]) * pos["entry"] + qty * fill) / abs(novo_qty)
        pos["qty"]   = novo_qty
        pos["fees"] += fee
        _state["posicoes"][symbol] = pos
    else:
        # Reduz / fecha
        fechado   = min(qty, abs(pos["qty"]))
        sinal     = 1 if pos["qty"] > 0 else -1
        bruto     = (fill - pos["entry"]) * fechado * sinal
        frac      = fechado / abs(pos["qty"])
        fee_ent   = pos["fees"] * frac
        _state["saldo"] += bruto
        pos["fees"] -= fee_ent
        pos["qty"]  += delta if fechado == qty else -pos["qty"]
        _registar_trade(symbol, "LONG" if sinal > 0 else "SHORT", pos["entry"], fill,
                        fechado, bruto, fee_ent + fee, pos["aberta_ts"], motivo)
        if abs(pos["qty"]) < 1e-12:
            del _state["posicoes"][symbol]
            for sid in [k for k, s in _state["stops"].items() if s["symbol"] == symbol]:
                del _state["stops"][sid]
        resto = qty - fechado
        if resto > 1e-12:
            # Inverteu a posição — o excedente abre no sentido contrário
            _state["saldo"] += fee * resto / qty  # evita cobrar a fee duas vezes
            _state["fees_total"] -= fee * resto / qty
            return _executar(symbol, side, resto, motivo)
    _save()
    return {"orderId": _novo_id(), "avgPrice": f"{fill}", "status": "FILLED",
            "executedQty": f"{qty}"}


def _registar_trade(symbol, lado, entry, saida, qty, bruto, fees, aberta_ts, motivo):
    rec = {
        "symbol": symbol, "lado": lado, "entry": round(entry, 8), "saida": round(saida, 8),
        "qty": qty, "bruto": round(bruto, 4), "fees": round(fees, 4),
        "liquido": round(bruto - fees, 4), "aberta_ts": aberta_ts,
        "fechada_ts": int(time.time()), "motivo": motivo,
    }
    with open(TRADES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"[PAPEL] Fechado {symbol} {lado} ({motivo}): bruto {bruto:+.2f} "
          f"fees {fees:.2f} líquido {bruto - fees:+.2f} USDC")


def _verificar_stops():
    """Dispara stops/trailing/TP simulados cujo preço foi atingido."""
    for sid, s in list(_state["stops"].items()):
        sym = s["symbol"]
        pos = _state["posicoes"].get(sym)
        if pos is None:
            del _state["stops"][sid]
            continue
        price = _get_price(sym)
        if not price:
            continue
        vende = s["side"] == "SELL"  # SELL fecha LONG, BUY fecha SHORT
        disparou = False
        if s["tipo"] == "STOP":
            disparou = price <= s["trigger"] if vende else price >= s["trigger"]
        elif s["tipo"] == "TP":
            disparou = price >= s["trigger"] if vende else price <= s["trigger"]
        elif s["tipo"] == "TRAIL":
            if not s.get("activo"):
                s["activo"] = price >= s["activation"] if vende else price <= s["activation"]
                s["melhor"] = price
            if s.get("activo"):
                s["melhor"] = max(s["melhor"], price) if vende else min(s["melhor"], price)
                cb = s["callback"] / 100
                disparou = (price <= s["melhor"] * (1 - cb) if vende
                            else price >= s["melhor"] * (1 + cb))
        if disparou and sid in _state["stops"]:
            _executar(sym, s["side"], abs(pos["qty"]), s["tipo"])
    _save()


# ─────────────────────────────────────────────
#  API simulada — mesmas assinaturas que exchange.py
# ─────────────────────────────────────────────

def get_positions() -> dict | None:
    with _lock:
        _verificar_stops()
        out = {}
        for sym, p in _state["posicoes"].items():
            price = _get_price(sym) or p["entry"]
            out[sym] = {
                "qty":   p["qty"],
                "entry": p["entry"],
                "pnl":   (price - p["entry"]) * p["qty"],  # bruto, como unRealizedProfit
                "side":  "LONG" if p["qty"] > 0 else "SHORT",
            }
        return out


def _nao_realizado() -> tuple[float, float]:
    """(pnl não realizado, nocional) das posições simuladas."""
    pnl = nocional = 0.0
    for sym, p in _state["posicoes"].items():
        price = _get_price(sym) or p["entry"]
        pnl      += (price - p["entry"]) * p["qty"]
        nocional += abs(p["qty"]) * price
    return pnl, nocional


def get_balance() -> float | None:
    with _lock:
        pnl, _ = _nao_realizado()
        return round(_state["saldo"] + pnl, 4)


def get_margin_ratio_global() -> float | None:
    with _lock:
        pnl, nocional = _nao_realizado()
        equity = _state["saldo"] + pnl
        if equity <= 0:
            return 100.0
        return round(nocional * _MAINT_RATE / equity * 100, 2)


get_margin_ratio = get_margin_ratio_global


def set_leverage(symbol: str):
    pass


def place_order(symbol: str, side: str, qty: float) -> dict | None:
    with _lock:
        return _executar(symbol, side, qty, "ORDEM")


def close_position(symbol: str, qty: float, side: str):
    close_side = "SELL" if side == "LONG" else "BUY"
    return place_order(symbol, close_side, abs(qty))


def _novo_stop(symbol: str, side: str, tipo: str, **campos) -> int:
    with _lock:
        sid = _novo_id()
        _state["stops"][str(sid)] = {"symbol": symbol, "side": side, "tipo": tipo, **campos}
        _save()
        print(f"[PAPEL] {tipo} {symbol} {side} #{sid} {campos}")
        return sid


def place_stop_market(symbol: str, side: str, stop_price: float, qty: float) -> int | None:
    return _novo_stop(symbol, side, "STOP", trigger=stop_price)


def place_take_profit(symbol: str, side: str, tp_price: float) -> int | None:
    return _novo_stop(symbol, side, "TP", trigger=tp_price)


def place_trailing_stop(symbol: str, side: str, callback_rate: float,
                        activation_price: float) -> int | None:
    return _novo_stop(symbol, side, "TRAIL", callback=callback_rate,
                      activation=activation_price)


def cancel_algo_order(symbol: str, algo_id) -> bool:
    with _lock:
        existia = _state["stops"].pop(str(algo_id), None) is not None
        _save()
        return existia


cancel_order = cancel_algo_order


def get_open_algo_orders(symbol: str) -> list:
    with _lock:
        return [int(k) for k, s in _state["stops"].items() if s["symbol"] == symbol]


# ─────────────────────────────────────────────
#  Resumo
# ─────────────────────────────────────────────

def ler_trades() -> list[dict]:
    try:
        with open(TRADES_FILE, encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]
    except FileNotFoundError:
        return []


# Critério para voltar ao dinheiro real. Com 100 trades e "líquido > 0" uma
# estratégia sem edge passava ~50% das vezes; exige-se t-stat do líquido por
# trade (média / (desvio / √n)) acima de 2. A recolha termina aos 1000 trades
# ou no fim do prazo (o que vier primeiro); no prazo, com menos de
# MIN_TRADES_PRAZO trades a amostra não chega para decidir.
MIN_TRADES_VEREDICTO = 1000
MIN_TRADES_PRAZO     = 30
PRAZO_VEREDICTO      = "2026-12-31"   # UTC, inclusive
T_STAT_MIN           = 2.0


def resumo() -> dict:
    trades = ler_trades()
    n      = len(trades)
    wins   = sum(1 for t in trades if t["liquido"] > 0)
    bruto  = sum(t["bruto"] for t in trades)
    fees   = sum(t["fees"] for t in trades)
    liq    = bruto - fees
    media  = liq / n if n else 0.0
    if n >= 2:
        desvio = (sum((t["liquido"] - media) ** 2 for t in trades) / (n - 1)) ** 0.5
        t_stat = media / (desvio / n ** 0.5) if desvio > 0 else 0.0
    else:
        desvio, t_stat = 0.0, 0.0
    prazo_fim = time.strftime("%Y-%m-%d", time.gmtime()) > PRAZO_VEREDICTO
    if n < MIN_TRADES_VEREDICTO and not prazo_fim:
        veredicto = (f"A RECOLHER ({n}/{MIN_TRADES_VEREDICTO} trades até "
                     f"{PRAZO_VEREDICTO}, t={t_stat:+.2f})")
    elif n < MIN_TRADES_PRAZO:
        veredicto = f"INCONCLUSIVO (prazo terminou com {n} trades, t={t_stat:+.2f})"
    elif t_stat > T_STAT_MIN:
        veredicto = f"APROVADO (t={t_stat:+.2f})"
    elif t_stat < 0:
        veredicto = f"REPROVADO (t={t_stat:+.2f})"
    else:
        veredicto = f"INCONCLUSIVO (t={t_stat:+.2f}, precisa > {T_STAT_MIN:g})"
    return {
        "trades": n, "wins": wins, "wr_pct": round(wins / n * 100, 1) if n else 0.0,
        "bruto": round(bruto, 2), "fees": round(fees, 2), "liquido": round(liq, 2),
        "liquido_por_trade": round(media, 3),
        "desvio_por_trade": round(desvio, 3), "t_stat": round(t_stat, 2),
        "veredicto": veredicto,
    }
