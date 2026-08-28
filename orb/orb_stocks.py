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
TARGETS = [1.0, 1.5, 2.0]              # alvo em multiplos de R
RETEST_TOL = 0.0005                               # 0.05%
ENTRY_CUTOFF_MIN_BEFORE_CLOSE = 60                # sem entradas na ultima hora
RETEST_WINDOW_MIN = 60                            # janela de reteste, em minutos = velas de 1m
LOOKBACK_DAYS = 28                                # limite do Yahoo para velas de 1m

DEFAULT_SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA",
                   "TSLA", "AMD", "META", "AMZN", "GOOGL"]

# Escaloes IBKR para accoes US. O Tiered e' o certo para ordens pequenas:
# o minimo de $0.35 contra $1.00 do Fixed decide tudo quando o nocional e' baixo.
TIERS = {
    "tiered": {"per_share": 0.0035, "min": 0.35, "max_pct": 0.005,
               "passthrough": 0.0005},   # clearing + regulatorias, aproximado
    "fixed":  {"per_share": 0.005,  "min": 1.00, "max_pct": 0.010,
               "passthrough": 0.0},      # ja' incluidas no Fixed
}
TIER = "tiered"


def commission(shares: float, notional: float) -> float:
    t = TIERS[TIER]
    base = max(t["min"], t["per_share"] * shares)
    return min(base + t["passthrough"] * shares, t["max_pct"] * notional)


def _fetch_yfinance(symbol: str) -> list:
    """Via preferida: yfinance trata do cookie/crumb que a API do Yahoo passou a exigir.

    O Yahoo so' da' velas de 1m em janelas de 7 dias e ate' ~30 dias para tras,
    por isso o pedido e' partido em pedacos.
    """
    import yfinance as yf
    from datetime import timedelta, date

    frames = []
    today = date.today()
    for wk in range(LOOKBACK_DAYS // 7 + 1):
        end = today - timedelta(days=7 * wk)
        start = end - timedelta(days=7)
        d = yf.download(symbol, start=start.isoformat(), end=end.isoformat(),
                        interval="1m", progress=False, auto_adjust=False,
                        threads=False)
        if d is not None and not d.empty:
            frames.append(d)
        time.sleep(0.25)
    if not frames:
        return []
    import pandas as pd
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="first")]
    if df.empty:
        return []
    # versoes recentes devolvem colunas MultiIndex mesmo com um so' ticker
    if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)

    out = []
    for ts, row in df.iterrows():
        try:
            o, h, l, c = (float(row["Open"]), float(row["High"]),
                          float(row["Low"]), float(row["Close"]))
        except (KeyError, TypeError, ValueError):
            continue
        if any(v != v for v in (o, h, l, c)):        # NaN
            continue
        t = ts.to_pydatetime()
        t = t.replace(tzinfo=ET) if t.tzinfo is None else t.astimezone(ET)
        out.append({"t": t, "o": o, "h": h, "l": l, "c": c})
    return out


def _fetch_raw(symbol: str) -> list:
    """Alternativa sem dependencias. Pode falhar se o Yahoo exigir crumb."""
    r = requests.get(YF.format(symbol), headers=UA, timeout=25,
                     params={"interval": "1m", "range": f"{LOOKBACK_DAYS}d"})
    ct = r.headers.get("content-type", "")
    if "json" not in ct:
        raise RuntimeError(
            f"HTTP {r.status_code}, content-type={ct or '?'}, "
            f"inicio do corpo: {r.text[:120]!r}")
    res = r.json()["chart"]["result"][0]
    ts, q = res["timestamp"], res["indicators"]["quote"][0]

    out = []
    for i, t in enumerate(ts):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        out.append({"t": datetime.fromtimestamp(t, tz=ET),
                    "o": float(o), "h": float(h), "l": float(l), "c": float(c)})
    return out


def fetch(symbol: str) -> list:
    """Velas de 5m dos ultimos 60 dias. Devolve [{t,o,h,l,c}] em ET."""
    try:
        return _fetch_yfinance(symbol)
    except ImportError:
        pass                                    # sem yfinance — tenta a via directa
    except Exception as e:
        print(f"  [{symbol}] yfinance falhou: {e}", file=sys.stderr)
    try:
        return _fetch_raw(symbol)
    except Exception as e:
        print(f"  [{symbol}] falhou: {e}", file=sys.stderr)
        return []


def sessions_for(candles: list, close_et: tuple) -> list:
    """Range agregado da vela de 5m da abertura, execucao nas velas de 1m."""
    by_day = {}
    for c in candles:
        by_day.setdefault(c["t"].date(), []).append(c)

    out = []
    for _, day in sorted(by_day.items()):
        day.sort(key=lambda x: x["t"])
        s = ob.build_session(day, OPEN_ET, close_et)
        if s:
            out.append(s)
    return out


def evaluate(candles_by_symbol: dict, mode: str, close_et: tuple,
             direction: str, notional: float, target: float = 2.0):
    ob.TARGET_R = target
    ch, cm = close_et
    cutoff_min = ch * 60 + cm - ENTRY_CUTOFF_MIN_BEFORE_CLOSE
    cutoff = (cutoff_min // 60, cutoff_min % 60)

    trades = []
    for candles in candles_by_symbol.values():
        for rng, rest in sessions_for(candles, close_et):
            t = ob.run_session(rng, rest, mode, cutoff, RETEST_TOL, "fixed",
                               retest_max=RETEST_WINDOW_MIN)
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
        "target": target,
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
    ap.add_argument("--tier", choices=["tiered", "fixed"], default="tiered",
                    help="escalao de comissoes IBKR (default tiered)")
    args = ap.parse_args()

    global TIER
    TIER = args.tier

    syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    ob.TAKER_FEE = 0.0          # comissoes tratadas aqui, nao em percentagem

    try:
        import yfinance  # noqa: F401
    except ImportError:
        print("AVISO: yfinance nao instalado — a API directa do Yahoo passou a\n"
              "       exigir cookie/crumb e costuma falhar. Instala com:\n"
              "         python3 -m venv /tmp/orbvenv && /tmp/orbvenv/bin/pip -q install yfinance\n"
              "         /tmp/orbvenv/bin/python orb_stocks.py --notional 500\n")

    print(f"ORB em accoes — range 5m + execucao 1m, {LOOKBACK_DAYS} dias, abertura 09:30 ET")
    t = TIERS[TIER]
    print(f"Nocional por posicao: ${args.notional:.0f} "
          f"| comissoes IBKR {TIER} (${t['min']:.2f} min/lado)\n")

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
    for tgt in TARGETS:
        for mode in CONFIRM_MODES:
            for close_et in SESSION_CLOSES:
                for d in DIRECTIONS:
                    r = evaluate(data, mode, close_et, d, args.notional, tgt)
                    if r:
                        results.append(r)

    if not results:
        print("Nenhuma combinacao gerou trades.")
        return 0

    # Resumo por alvo — media de TODAS as combinacoes, nao so' da melhor.
    # E' o numero robusto: se o alvo mais curto levantar a distribuicao
    # inteira, e' sinal; se so' levantar o maximo, e' ruido de seleccao.
    print("RESUMO POR ALVO (media de todas as combinacoes desse alvo)")
    print(f"  {'alvo':>6}{'combos':>8}{'exp media':>11}{'positivas':>11}"
          f"{'n medio':>9}{'%TP':>7}{'%TEMPO':>8}")
    for tgt in TARGETS:
        g = [r for r in results if r["target"] == tgt]
        if not g:
            continue
        pos = sum(1 for r in g if r["exp_r"] > 0)
        tp = sum(r["reasons"]["TP"] for r in g)
        tm = sum(r["reasons"]["TEMPO"] for r in g)
        tot = sum(r["n"] for r in g)
        print(f"  {tgt:>6.1f}{len(g):>8}{sum(r['exp_r'] for r in g)/len(g):>11.3f}"
              f"{pos:>7}/{len(g):<3}{tot//len(g):>9}"
              f"{100*tp/tot:>7.1f}{100*tm/tot:>8.1f}")

    results.sort(key=lambda r: r["exp_r"], reverse=True)
    print(f"\nTOP 12 combinacoes")
    print(f"{'alvo':<6}{'modo':<5}{'fecho':<7}{'direccao':<11}{'n':>5}{'WR%':>7}"
          f"{'avgW':>7}{'avgL':>7}{'custo':>7}{'exp(R)':>9}{'total(R)':>10}")
    print("-" * 81)
    for r in results[:12]:
        print(f"{r['target']:<6.1f}{r['mode']:<5}{r['close']:<7}{r['dir']:<11}{r['n']:>5}"
              f"{r['wr']:>7.1f}{r['avg_w']:>7.2f}{r['avg_l']:>7.2f}"
              f"{r['cost_r']:>7.2f}{r['exp_r']:>9.3f}{r['total_r']:>10.1f}")

    b = results[0]
    print(f"\nMelhor: alvo {b['target']:.1f}R, modo {b['mode']}, "
          f"fecho {b['close']} ET, {b['dir']}")
    print(f"  {b['n']} trades | WR {b['wr']:.1f}% | expectancy {b['exp_r']:+.3f}R")
    print(f"  Custo medio por trade: {b['cost_r']:.2f}R  <-- comissoes")
    print(f"  Saidas: {b['reasons']}")
    gross = b["exp_r"] + b["cost_r"]
    print(f"  Expectancia BRUTA (sem comissoes): {gross:+.3f}R")

    print(f"\n  A mesma combinacao a varios tamanhos de posicao:")
    print(f"    {'nocional':>10}{'risco medio':>13}{'custo(R)':>10}{'liquido(R)':>12}")
    risk_per_dollar = b["cost_r"] / (2 * commission(
        args.notional / 200.0, args.notional)) if b["cost_r"] > 0 else 0
    for nt in (500, 1000, 1500, 2000, 3000, 5000):
        risk = (args.notional and nt / args.notional) * (
            2 * commission(args.notional / 200.0, args.notional) / b["cost_r"]) \
            if b["cost_r"] > 0 else 0
        cost_r = (2 * commission(nt / 200.0, nt)) / risk if risk > 0 else 0
        print(f"    ${nt:>9,}{risk:>12.2f}${cost_r:>10.3f}{gross - cost_r:>12.3f}")

    if gross <= 0:
        print("\n  Sem edge nem antes de comissoes — nao ha tamanho que resolva.")
    elif b["exp_r"] <= 0:
        print("\n  Ha edge bruto, mas as comissoes comem-no a este tamanho.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
