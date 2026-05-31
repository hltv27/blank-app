"""
Claw Agent v8.0 — Analytics
Relatórios de performance de filtros e trades.
Responde: qual filtro está a adicionar valor? qual está a cortar lucro?
"""
import sqlite3
from storage import get_conn, DB_FILE


def filter_performance_report() -> str:
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            filter_name,
            passed,
            COUNT(*) as total,
            AVG(CASE WHEN future_price_30m IS NOT NULL AND price_at_signal > 0
                THEN (future_price_30m - price_at_signal) / price_at_signal * 100
                ELSE NULL END) as avg_return_30m
        FROM filter_events
        GROUP BY filter_name, passed
        ORDER BY filter_name, passed DESC
    """).fetchall()
    conn.close()

    if not rows:
        return "Sem dados de filtros ainda."

    lines = ["", "=== FILTER PERFORMANCE ==="]
    current_filter = None
    for row in rows:
        if row["filter_name"] != current_filter:
            current_filter = row["filter_name"]
            lines.append(f"\n{current_filter}:")
        label = "PASSOU" if row["passed"] else "BLOQUEOU"
        avg_r = f"{row['avg_return_30m']:.2f}%" if row["avg_return_30m"] is not None else "N/A"
        lines.append(f"  {label}: {row['total']}x | return_30m médio: {avg_r}")

    return "\n".join(lines)


def trade_summary() -> str:
    conn = get_conn()
    row  = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
            SUM(pnl) as total_pnl,
            AVG(pnl) as avg_pnl,
            AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
            AVG(CASE WHEN pnl <= 0 THEN pnl END) as avg_loss
        FROM positions WHERE status='CLOSED'
    """).fetchone()
    conn.close()

    if not row or row["total"] == 0:
        return "Sem trades fechados ainda."

    wr = row["wins"] / row["total"] * 100 if row["total"] > 0 else 0
    return (
        f"\n=== TRADE SUMMARY ===\n"
        f"Total: {row['total']} | W: {row['wins']} | L: {row['losses']} | WR: {wr:.1f}%\n"
        f"PnL total: {row['total_pnl']:+.2f} USDC\n"
        f"Avg por trade: {row['avg_pnl']:+.2f} USDC\n"
        f"Avg win: {row['avg_win']:+.2f} | Avg loss: {row['avg_loss']:+.2f}"
    )


def symbol_performance() -> str:
    conn = get_conn()
    rows = conn.execute("""
        SELECT symbol,
            COUNT(*) as total,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(pnl) as total_pnl
        FROM positions WHERE status='CLOSED'
        GROUP BY symbol ORDER BY total_pnl DESC
    """).fetchall()
    conn.close()

    if not rows:
        return "Sem dados por símbolo ainda."

    lines = ["\n=== POR SÍMBOLO ==="]
    for row in rows:
        wr = row["wins"] / row["total"] * 100 if row["total"] > 0 else 0
        lines.append(
            f"{row['symbol']}: {row['total']} trades | "
            f"WR {wr:.0f}% | PnL {row['total_pnl']:+.2f}"
        )
    return "\n".join(lines)


def print_full_report():
    print(trade_summary())
    print(symbol_performance())
    print(filter_performance_report())


if __name__ == "__main__":
    print_full_report()
