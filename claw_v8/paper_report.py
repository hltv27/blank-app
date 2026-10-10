"""
Resumo do modo papel — corre manualmente no VPS:
    cd /root/blank-app/claw_v8 && python3 paper_report.py
Lê paper_trades.jsonl (escrito por paper.py) e mostra bruto, comissões e
líquido, por motivo de saída e por símbolo, mais o veredicto (t-stat > 2 aos 1000 trades ou a 2026-12-31).
"""
from collections import defaultdict

from paper import ler_trades, resumo


def _agrupar(trades, chave):
    g = defaultdict(lambda: [0, 0.0])
    for t in trades:
        g[t[chave]][0] += 1
        g[t[chave]][1] += t["liquido"]
    return sorted(g.items(), key=lambda kv: kv[1][1])


def main():
    trades = ler_trades()
    r = resumo()
    print(f"Trades: {r['trades']} | WR líquido {r['wr_pct']}%")
    print(f"Bruto {r['bruto']:+.2f} | Fees {r['fees']:.2f} | Líquido {r['liquido']:+.2f} "
          f"({r['liquido_por_trade']:+.3f}/trade, desvio {r['desvio_por_trade']:.3f}, t={r['t_stat']:+.2f})")
    print(f"Veredicto: {r['veredicto']}")
    if not trades:
        return
    print("\nPor motivo de saída:")
    for k, (n, liq) in _agrupar(trades, "motivo"):
        print(f"  {k:<8} {n:>4} trades  {liq:+8.2f}")
    print("\nPor símbolo (piores primeiro):")
    for k, (n, liq) in _agrupar(trades, "symbol")[:10]:
        print(f"  {k:<12} {n:>4} trades  {liq:+8.2f}")


if __name__ == "__main__":
    main()
