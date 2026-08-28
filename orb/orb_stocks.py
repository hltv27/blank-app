#!/usr/bin/env python3
"""
ORB em accoes US — backtest.

Reutiliza a maquina de estados de orb_backtest.py (rompimento por fecho,
reteste obrigatorio, modos A/B/C) e troca o que e' especifico do mercado:

  - Dados: Yahoo Finance, velas de 5m dos ultimos 60 dias (sem chave, sem deps novas)
  - Sessao: 09:30 ET, com DST tratado por zoneinfo (nao por UTC fixo)
  - Custos: comissoes IBKR fixed tier, nao percentagem plana
  - Direccao: 'both' (IBKR, permite short) vs 'long_only' (Trading212 Invest)

O que ficou de fora, e porque:
  - Trailing: os dados de cripto mostraram que corta os vencedores (avgW
    0.50-0.70R contra 0.92-1.08R). So' saida fixa a 2R.
  - Tolerancia do reteste: 0.00/0.05/0.10% deram o mesmo. Fixada em 0.05%.
Reduzir estas duas dimensoes e' consequencia do que os dados ja' disseram,
nao pesca por um resultado bonito.

Uso:
  python3 orb_stocks.py
  python3 orb_stocks.py --notional 500
  python3 orb_stocks.py --symbols SPY,QQQ,NVDA,TSLA
"""
import argparse
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import orb_backtest as ob

ET = ZoneInfo("America/New_York")
YF = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

OPEN_ET = (9, 30)
SESSION_CLOSES = [(11, 0), (12, 0), (16, 0)]     # 90min, 2h30, sessao inteira
CONFIRM_MODES = ["A", "B", "C"]
DIRECTIONS = ["both", "long_only"]
RETEST_TOL = 0.0005                               # 0.05%
ENTRY_CUTOFF_MIN_BEFORE_CLOSE = 60                # sem entradas na ultima hora

DEFAULT_SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA",
                   "TSLA", "AMD", "META", "AMZN", "GOOGL"]

# IBKR fixed tier: $0.005/accao, minimo $1.00, maximo 1% do valor da ordem
IBKR_PER_SHARE = 0.005
IBKR_MIN = 1.00
IBKR_MAX_PCT = 0.01


def commission(shares: float, notional: float) -> float:
    return min(max(IBKR_MIN, IBKR_PER_SHARE * shares), IBKR_MAX_PCT * notional)


def fetch(symbol: str) -> list:
    """Velas de 5m dos ultimos 60 dias via Yahoo. Devolve [{t,o,h,l,c}] em ET."""
    try:
        r = requests.get(YF.format(symbol), headers=UA, timeout=25,
                         params={"interval": "5m", "range": "60d"})
        js = r.json()
        res = js["chart"]["result"][0]
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
    except Exception as e:
        print(f"  [{symbol}] falhou: {e}", file=sys.stderr)
        return []

    out = []
    for i, t in enumerate(ts):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        out.append({"t": datetime.fromtimestamp(t, tz=ET),
                    "o": float(o), "h": float(h), "l": float(l), "c": float(c)})
    return out


def sessions_for(candles: list, close_et: tuple) -> list:
    """(vela_do_range, [velas ate' ao fecho]) por dia de negociacao."""
    by_day = {}
    for c in candles:
        by_day.setdefault(c["t"].date(), []).append(c)

    out = []
    for _, day in sorted(by_day.items()):
        day.sort(key=lambda x: x["t"])
        rng = next((c for c in day
                    if (c["t"].hour, c["t"].minute) == OPEN_ET), None)
        if rng is None:
            continue
        rest = [c for c in day
                if c["t"] > rng["t"]
                and (c["t"].hour, c["t"].minute) < close_et]
        if rest:
            out.append((rng, rest))
    return out


def evaluate(candles_by_symbol: dict, mode: str, close_et: tuple,
             direction: str, notional: float):
    ch, cm = close_et
    cutoff_min = ch * 60 + cm - ENTRY_CUTOFF_MIN_BEFORE_CLOSE
    cutoff = (cutoff_min // 60, cutoff_min % 60)

    trades = []
    for candles in candles_by_symbol.values():
        for rng, rest in sessions_for(candles, close_et):
            t = ob.run_session(rng, rest, mode, cutoff, RETEST_TOL, "fixed")
            if not t:
                continue
            if direction == "long_only" and t["side"] != "LONG":
                continue
            # comissao real: dois lados, sobre o nocional escolhido
            shares = notional / t["entry"]
            cost = commission(shares, notional) * 2
            risk_usd = shares * t["R"]
            if risk_usd <= 0:
                continue
            t = dict(t, pnl_r=t["pnl_r"] - cost / risk_usd,
                     cost_r=cost / risk_usd)
            trades.append(t)

    if not trades:
        return None
    wins = [t["pnl_r"] for t in trades if t["pnl_r"] > 0]
    losses = [t["pnl_r"] for t in trades if t["pnl_r"] <= 0]
    total = sum(t["pnl_r"] for t in trades)
    return {
        "mode": mode, "close": f"{ch:02d}:{cm:02d}", "dir": direction,
        "n": len(trades),
        "wr": 100 * len(wins) / len(trades),
        "avg_w": sum(wins) / len(wins) if wins else 0.0,
        "avg_l": sum(losses) / len(losses) if losses else 0.0,
        "exp_r": total / len(trades),
        "total_r": total,
        "cost_r": sum(t["cost_r"] for t in trades) / len(trades),
        "reasons": {r: sum(1 for t in trades if t["reason"] == r)
                    for r in ("TP", "SL", "TEMPO")},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    ap.add_argument("--notional", type=float, default=500.0,
                    help="valor por posicao em USD (default 500)")
    args = ap.parse_args()

    syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    ob.TAKER_FEE = 0.0          # comissoes tratadas aqui, nao em percentagem

    print(f"ORB em accoes — velas de 5m, 60 dias, abertura 09:30 ET")
    print(f"Nocional por posicao: ${args.notional:.0f} "
          f"| comissoes IBKR fixed (${IBKR_MIN:.2f} min/lado)\n")

    data, total_days = {}, 0
    for s in syms:
        cs = fetch(s)
        if not cs:
            print(f"  {s}: sem dados")
            continue
        data[s] = cs
        d = len({c['t'].date() for c in cs})
        total_days += d
        print(f"  {s}: {len(cs)} velas, {d} dias")
        time.sleep(0.3)

    if not data:
        print("\nSem dados. Aborta.")
        return 1
    print(f"\nTotal: {total_days} dias-simbolo\n")

    results = []
    for mode in CONFIRM_MODES:
        for close_et in SESSION_CLOSES:
            for d in DIRECTIONS:
                r = evaluate(data, mode, close_et, d, args.notional)
                if r:
                    results.append(r)

    if not results:
        print("Nenhuma combinacao gerou trades.")
        return 0

    results.sort(key=lambda r: r["exp_r"], reverse=True)
    print(f"{'modo':<5}{'fecho':<7}{'direccao':<11}{'n':>5}{'WR%':>7}"
          f"{'avgW':>7}{'avgL':>7}{'custo':>7}{'exp(R)':>9}{'total(R)':>10}")
    print("-" * 75)
    for r in results:
        print(f"{r['mode']:<5}{r['close']:<7}{r['dir']:<11}{r['n']:>5}"
              f"{r['wr']:>7.1f}{r['avg_w']:>7.2f}{r['avg_l']:>7.2f}"
              f"{r['cost_r']:>7.2f}{r['exp_r']:>9.3f}{r['total_r']:>10.1f}")

    b = results[0]
    print(f"\nMelhor: modo {b['mode']}, fecho {b['close']} ET, {b['dir']}")
    print(f"  {b['n']} trades | WR {b['wr']:.1f}% | expectancy {b['exp_r']:+.3f}R")
    print(f"  Custo medio por trade: {b['cost_r']:.2f}R  <-- comissoes")
    print(f"  Saidas: {b['reasons']}")
    if b["exp_r"] <= 0:
        print("\n  Nenhuma combinacao tem expectativa positiva.")
    else:
        print(f"\n  Sem comissoes seria {b['exp_r'] + b['cost_r']:+.3f}R "
              f"— a diferenca mede quanto a corretora leva.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
