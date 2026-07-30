"""
Claw Agent v8.0 — Analytics
Relatórios de performance de filtros e trades.
Responde: qual filtro está a adicionar valor? qual está a cortar lucro?
"""
import math
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


def _max_streaks(pnls: list) -> tuple:
    """Calcula max consecutive wins e losses a partir de lista ordenada de PnLs."""
    max_w = max_l = cur_w = cur_l = 0
    for p in pnls:
        if p > 0:
            cur_w += 1
            cur_l = 0
        else:
            cur_l += 1
            cur_w = 0
        max_w = max(max_w, cur_w)
        max_l = max(max_l, cur_l)
    return max_w, max_l


def _sortino_ratio(pnls: list) -> float:
    """Sortino ratio: mean / downside deviation (per-trade PnL)."""
    if len(pnls) < 2:
        return 0.0
    mean = sum(pnls) / len(pnls)
    neg_sq = [p ** 2 for p in pnls if p < 0]
    if not neg_sq:
        return float("inf") if mean > 0 else 0.0
    downside_dev = math.sqrt(sum(neg_sq) / len(pnls))
    if downside_dev == 0:
        return 0.0
    return mean / downside_dev


def compute_expectancy(avg_win: float, avg_loss: float, win_rate: float) -> float:
    """Expectancy: avg_win * win_rate - avg_loss * (1 - win_rate). Retorna USDC esperado por trade."""
    return avg_win * win_rate - abs(avg_loss) * (1 - win_rate)


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
            AVG(CASE WHEN pnl <= 0 THEN pnl END) as avg_loss,
            SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as sum_wins,
            SUM(CASE WHEN pnl <= 0 THEN pnl ELSE 0 END) as sum_losses
        FROM positions WHERE status='CLOSED'
    """).fetchone()

    # Buscar PnLs individuais para Sortino e streaks
    pnl_rows = conn.execute(
        "SELECT pnl FROM positions WHERE status='CLOSED' ORDER BY closed_at ASC"
    ).fetchall()
    conn.close()

    if not row or row["total"] == 0:
        return "Sem trades fechados ainda."

    wr = row["wins"] / row["total"] * 100 if row["total"] > 0 else 0
    wr_frac = row["wins"] / row["total"] if row["total"] > 0 else 0

    # Métricas avançadas
    avg_win = row["avg_win"] or 0
    avg_loss = row["avg_loss"] or 0
    expectancy = compute_expectancy(avg_win, avg_loss, wr_frac)

    pnls = [r["pnl"] for r in pnl_rows if r["pnl"] is not None]
    sortino = _sortino_ratio(pnls)

    sum_wins = row["sum_wins"] or 0
    sum_losses = row["sum_losses"] or 0
    profit_factor = sum_wins / abs(sum_losses) if sum_losses != 0 else float("inf")

    max_cw, max_cl = _max_streaks(pnls)

    sortino_txt = f"{sortino:.2f}" if sortino != float("inf") else "inf"
    pf_txt = f"{profit_factor:.2f}" if profit_factor != float("inf") else "inf"

    return (
        f"\n=== TRADE SUMMARY ===\n"
        f"Total: {row['total']} | W: {row['wins']} | L: {row['losses']} | WR: {wr:.1f}%\n"
        f"PnL total: {row['total_pnl']:+.2f} USDC\n"
        f"Avg por trade: {row['avg_pnl']:+.2f} USDC\n"
        f"Avg win: {avg_win:+.2f} | Avg loss: {avg_loss:+.2f}\n"
        f"Expectancy: {expectancy:+.3f} USDC/trade\n"
        f"Sortino Ratio: {sortino_txt} | Profit Factor: {pf_txt}\n"
        f"Max streak: {max_cw}W / {max_cl}L"
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
