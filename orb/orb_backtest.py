#!/usr/bin/env python3
"""
ORB (Opening Range Breakout) com reteste — backtest e varrimento de parametros.

Standalone: nao importa nada de claw_v8 e nao toca em nenhum ficheiro dele.
Usa apenas endpoints publicos da Binance (sem chaves de API).

Regra base (ancorada na abertura de NY, 13:30 UTC = 14:30 Lisboa):
  1. A vela de 5m das 13:30-13:35 define o range: H (maximo) e L (minimo)
  2. Rompimento: uma vela FECHA acima do H (long) ou abaixo do L (short).
     Mechas sozinhas nao contam.
  3. Reteste: o preco volta e toca no nivel rompido, ate' RETEST_MAX velas depois
  4. Confirmacao: modo A, B ou C (ver CONFIRM_MODES)
  5. Stop no lado oposto do range; alvo 2R fixo ou trailing apos 1R
  6. Fecho por tempo as 15:00 UTC (90 min apos a abertura)
  7. Um trade por sessao — o primeiro lado a completar a sequencia fecha a porta ao outro

Uso:
  python3 orb_backtest.py --days 90
  python3 orb_backtest.py --days 90 --symbols BTCUSDC,ETHUSDC
  python3 orb_backtest.py --days 90 --single A 14:30 0.0 fixed
"""
import argparse
import sys
import time
from datetime import datetime, timezone

import requests

BASE_URL = "https://fapi.binance.com"
INTERVAL = "1m"          # range agregado de 5m, execucao em 1m
CANDLE_MS = 60 * 1000

# ── Sessao ────────────────────────────────────────────────────────────
OPEN_H, OPEN_M = 13, 30      # 13:30 UTC = 14:30 Lisboa (abertura NY)
CLOSE_H, CLOSE_M = 15, 0     # 90 minutos depois

# ── Custos ────────────────────────────────────────────────────────────
TAKER_FEE = 0.0005           # 0.05% por lado, igual ao claw_v8
RISCO_USDC = 6.0             # so' para converter R em USDC no relatorio

# ── Grelha do varrimento ──────────────────────────────────────────────
CONFIRM_MODES = ["A", "B", "C"]
NO_ENTRY_AFTER = ["14:15", "14:30", "14:45"]
RETEST_TOL = [0.0, 0.0005, 0.0010]     # 0%, 0.05%, 0.10%
EXIT_MODES = ["fixed", "trail"]

DEFAULT_SYMBOLS = ["BTCUSDC", "ETHUSDC", "SOLUSDC", "XRPUSDC", "BNBUSDC"]

REJECTION_WICK_RATIO = 0.5   # mecha >= 50% do corpo para contar como rejeicao
TARGET_R = 2.0


# ══════════════════════════════════════════════════════════════════════
#  Dados
# ══════════════════════════════════════════════════════════════════════
def fetch_klines(symbol: str, days: int) -> list:
    """Puxa velas de 5m dos ultimos N dias, paginando (limite 1500/pedido)."""
    end = int(time.time() * 1000)
    start = end - days * 24 * 60 * 60 * 1000
    out, cursor = [], start
    while cursor < end:
        try:
            r = requests.get(
                f"{BASE_URL}/fapi/v1/klines",
                params={"symbol": symbol, "interval": INTERVAL,
                        "startTime": cursor, "limit": 1500},
                timeout=20,
            )
            batch = r.json()
        except Exception as e:
            print(f"  [{symbol}] erro de rede: {e}", file=sys.stderr)
            break
        if not isinstance(batch, list) or not batch:
            break
        out.extend(batch)
        nxt = int(batch[-1][0]) + CANDLE_MS
        if nxt <= cursor:
            break
        cursor = nxt
        time.sleep(0.12)          # cortesia com o rate limit
    return out


def to_candles(raw: list) -> list:
    """[{t, o, h, l, c}] com t em datetime UTC."""
    cs = []
    for k in raw:
        cs.append({
            "t": datetime.fromtimestamp(int(k[0]) / 1000, tz=timezone.utc),
            "o": float(k[1]), "h": float(k[2]),
            "l": float(k[3]), "c": float(k[4]),
        })
    return cs


def split_sessions(candles: list) -> list:
    """Agrupa por dia UTC e constroi cada sessao (range 5m + execucao 1m)."""
    by_day = {}
    for c in candles:
        by_day.setdefault(c["t"].date(), []).append(c)

    sessions = []
    for _, day_candles in sorted(by_day.items()):
        day_candles.sort(key=lambda x: x["t"])
        s = build_session(day_candles, (OPEN_H, OPEN_M), (CLOSE_H, CLOSE_M))
        if s:
            sessions.append(s)
    return sessions


def build_session(candles_1m: list, open_hm: tuple, close_hm: tuple):
    """
    Range da primeira vela de 5m, execucao nas velas de 1m seguintes.

    A vela do range e' agregada a partir das cinco velas de 1m que comecam
    na abertura — e' a mesma vela de 5m do grafico, mas assim a execucao
    continua com resolucao de 1 minuto, que e' como a estrategia e' operada.
    """
    oh, om = open_hm
    head = [c for c in candles_1m
            if (c["t"].hour, c["t"].minute) >= (oh, om)
            and (c["t"].hour * 60 + c["t"].minute) < (oh * 60 + om + 5)]
    if len(head) < 5:
        return None
    rng = {"t": head[0]["t"], "o": head[0]["o"], "c": head[-1]["c"],
           "h": max(x["h"] for x in head), "l": min(x["l"] for x in head)}
    start = oh * 60 + om + 5
    end = close_hm[0] * 60 + close_hm[1]
    rest = [c for c in candles_1m
            if start <= (c["t"].hour * 60 + c["t"].minute) < end]
    return (rng, rest) if rest else None


# ══════════════════════════════════════════════════════════════════════
#  Confirmacao
# ══════════════════════════════════════════════════════════════════════
def is_rejection(c: dict, level: float, side: str) -> bool:
    """Vela de rejeicao: mecha atravessa o nivel, corpo fecha do lado certo."""
    body = abs(c["c"] - c["o"]) or 1e-9
    if side == "LONG":
        if c["c"] <= level:
            return False
        wick = min(c["o"], c["c"]) - c["l"]
        return c["l"] <= level and wick >= body * REJECTION_WICK_RATIO
    else:
        if c["c"] >= level:
            return False
        wick = c["h"] - max(c["o"], c["c"])
        return c["h"] >= level and wick >= body * REJECTION_WICK_RATIO


def confirm(mode: str, c: dict, level: float, side: str, pending_rej: dict):
    """
    Devolve (entrou, preco_entrada, nova_vela_de_rejeicao_pendente).

    A — vela verde/vermelha a fechar alem do nivel
    B — vela de rejeicao a fechar alem do nivel; entra no fecho dela
    C — identifica a vela de rejeicao mas NAO entra nela; entra quando uma
        vela seguinte passa o maximo (long) / minimo (short) dessa vela
    """
    if mode == "A":
        if side == "LONG" and c["c"] > c["o"] and c["c"] > level:
            return True, c["c"], None
        if side == "SHORT" and c["c"] < c["o"] and c["c"] < level:
            return True, c["c"], None
        return False, None, None

    if mode == "B":
        if is_rejection(c, level, side):
            return True, c["c"], None
        return False, None, None

    # modo C
    if pending_rej is not None:
        if side == "LONG" and c["h"] > pending_rej["h"]:
            return True, pending_rej["h"], pending_rej
        if side == "SHORT" and c["l"] < pending_rej["l"]:
            return True, pending_rej["l"], pending_rej
        return False, None, pending_rej          # continua a espera
    if is_rejection(c, level, side):
        return False, None, c                    # arma a vela de rejeicao
    return False, None, None


# ══════════════════════════════════════════════════════════════════════
#  Simulacao de uma sessao
# ══════════════════════════════════════════════════════════════════════
def run_session(rng: dict, rest: list, mode: str, cutoff: tuple,
                tol: float, exit_mode: str, retest_max: int = 12):
    """Devolve o trade da sessao (dict) ou None.

    retest_max e' contado em velas de `rest`. A regra e' de 60 minutos, por
    isso vale 12 em velas de 5m e 60 em velas de 1m — quem chama e' que sabe
    a resolucao com que esta' a trabalhar.
    """
    H, L = rng["h"], rng["l"]
    if H <= L:
        return None

    side = None          # lado do rompimento
    level = None
    broke_i = None
    retested = False
    pending_rej = None

    for i, c in enumerate(rest):
        # ── 1. rompimento por FECHO ──
        if side is None:
            if c["c"] > H:
                side, level, broke_i = "LONG", H, i
            elif c["c"] < L:
                side, level, broke_i = "SHORT", L, i
            continue

        # janela de reteste esgotada
        if not retested and (i - broke_i) > retest_max:
            return None

        # ── 2. reteste: o preco volta e toca no nivel ──
        if not retested:
            if side == "LONG" and c["l"] <= level * (1 + tol):
                retested = True
            elif side == "SHORT" and c["h"] >= level * (1 - tol):
                retested = True
            else:
                continue
            # a propria vela do reteste ja' pode confirmar

        # ── 3. confirmacao ──
        if (c["t"].hour, c["t"].minute) >= cutoff:
            return None                          # tarde demais para entrar

        ok, entry, pending_rej = confirm(mode, c, level, side, pending_rej)
        if not ok:
            continue

        # ── 4. gestao da posicao ──
        sl = L if side == "LONG" else H
        R = abs(entry - sl)
        if R <= 0:
            return None
        tp = entry + TARGET_R * R if side == "LONG" else entry - TARGET_R * R
        peak = entry

        for c2 in rest[i + 1:]:
            if side == "LONG":
                peak = max(peak, c2["h"])
                if exit_mode == "trail" and peak >= entry + R:
                    sl = max(sl, entry, peak - R)
                if c2["l"] <= sl:                # pessimista: SL primeiro
                    return _trade(side, entry, sl, R, "SL", c2["t"])
                if exit_mode == "fixed" and c2["h"] >= tp:
                    return _trade(side, entry, tp, R, "TP", c2["t"])
            else:
                peak = min(peak, c2["l"])
                if exit_mode == "trail" and peak <= entry - R:
                    sl = min(sl, entry, peak + R)
                if c2["h"] >= sl:
                    return _trade(side, entry, sl, R, "SL", c2["t"])
                if exit_mode == "fixed" and c2["l"] <= tp:
                    return _trade(side, entry, tp, R, "TP", c2["t"])

        return _trade(side, entry, rest[-1]["c"], R, "TEMPO", rest[-1]["t"])

    return None


def _trade(side, entry, exit_px, R, reason, t):
    gross = (exit_px - entry) if side == "LONG" else (entry - exit_px)
    fees = (entry + exit_px) * TAKER_FEE
    return {"side": side, "entry": entry, "exit": exit_px, "R": R,
            "reason": reason, "t": t, "pnl_r": (gross - fees) / R}


# ══════════════════════════════════════════════════════════════════════
#  Avaliacao
# ══════════════════════════════════════════════════════════════════════
def evaluate(sessions_by_symbol: dict, mode, cutoff_s, tol, exit_mode):
    h, m = map(int, cutoff_s.split(":"))
    trades = []
    for sessions in sessions_by_symbol.values():
        for rng, rest in sessions:
            t = run_session(rng, rest, mode, (h, m), tol, exit_mode, retest_max=60)
            if t:
                trades.append(t)
    if not trades:
        return None

    wins = [t["pnl_r"] for t in trades if t["pnl_r"] > 0]
    losses = [t["pnl_r"] for t in trades if t["pnl_r"] <= 0]
    total_r = sum(t["pnl_r"] for t in trades)
    return {
        "mode": mode, "cutoff": cutoff_s, "tol": tol, "exit": exit_mode,
        "n": len(trades),
        "wr": 100 * len(wins) / len(trades),
        "avg_w": sum(wins) / len(wins) if wins else 0.0,
        "avg_l": sum(losses) / len(losses) if losses else 0.0,
        "exp_r": total_r / len(trades),
        "total_r": total_r,
        "total_usdc": total_r * RISCO_USDC,
        "reasons": {r: sum(1 for t in trades if t["reason"] == r)
                    for r in ("TP", "SL", "TEMPO")},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    ap.add_argument("--single", nargs=4, metavar=("MODE", "CUTOFF", "TOL", "EXIT"),
                    help="corre uma so' combinacao, ex: A 14:30 0.0 fixed")
    args = ap.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    print(f"ORB backtest — {args.days} dias, velas de {INTERVAL}")
    print(f"Abertura {OPEN_H:02d}:{OPEN_M:02d} UTC | fecho {CLOSE_H:02d}:{CLOSE_M:02d} UTC")
    print(f"Simbolos: {', '.join(symbols)}\n")

    sessions_by_symbol, total_sessions = {}, 0
    for sym in symbols:
        raw = fetch_klines(sym, args.days)
        if not raw:
            print(f"  {sym}: sem dados — ignorado")
            continue
        sess = split_sessions(to_candles(raw))
        sessions_by_symbol[sym] = sess
        total_sessions += len(sess)
        print(f"  {sym}: {len(raw)} velas, {len(sess)} sessoes")

    if not sessions_by_symbol:
        print("\nSem dados. Aborta.")
        return 1
    print(f"\nTotal: {total_sessions} sessoes\n")

    if args.single:
        mode, cutoff, tol, ex = args.single
        r = evaluate(sessions_by_symbol, mode, cutoff, float(tol), ex)
        print(r if r else "Zero trades nesta combinacao.")
        return 0

    results = []
    for mode in CONFIRM_MODES:
        for cutoff in NO_ENTRY_AFTER:
            for tol in RETEST_TOL:
                for ex in EXIT_MODES:
                    r = evaluate(sessions_by_symbol, mode, cutoff, tol, ex)
                    if r:
                        results.append(r)

    if not results:
        print("Nenhuma combinacao gerou trades.")
        return 0

    results.sort(key=lambda r: r["exp_r"], reverse=True)
    print(f"{'modo':<5}{'cutoff':<8}{'tol%':>6}{'saida':>7}"
          f"{'n':>5}{'WR%':>7}{'avgW':>7}{'avgL':>7}"
          f"{'exp(R)':>8}{'total(R)':>10}{'USDC':>9}")
    print("-" * 86)
    for r in results:
        print(f"{r['mode']:<5}{r['cutoff']:<8}{r['tol']*100:>6.2f}{r['exit']:>7}"
              f"{r['n']:>5}{r['wr']:>7.1f}{r['avg_w']:>7.2f}{r['avg_l']:>7.2f}"
              f"{r['exp_r']:>8.3f}{r['total_r']:>10.1f}{r['total_usdc']:>9.1f}")

    best = results[0]
    print(f"\nMelhor: modo {best['mode']}, cutoff {best['cutoff']}, "
          f"tol {best['tol']*100:.2f}%, saida {best['exit']}")
    print(f"  {best['n']} trades | WR {best['wr']:.1f}% | "
          f"expectancy {best['exp_r']:+.3f}R ({best['exp_r']*RISCO_USDC:+.2f} USDC/trade)")
    print(f"  Saidas: {best['reasons']}")
    if best["exp_r"] <= 0:
        print("\n  ATENCAO: nenhuma combinacao tem expectativa positiva.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
