#!/usr/bin/env python3
"""Consulta rápida aos resultados do bot — corre no VPS."""
import sqlite3, os, json

db_path = os.path.join(os.path.dirname(__file__), "..", "claw_v8.db")
db_path = os.path.abspath(db_path)

if not os.path.exists(db_path):
    print(f"Base de dados não encontrada: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 50)
print("WIN / LOSS")
print("=" * 50)
cur.execute("SELECT COUNT(*) FROM positions WHERE status='CLOSED' AND pnl>0")
wins = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM positions WHERE status='CLOSED' AND pnl<=0")
losses = cur.fetchone()[0]
total = wins + losses
wr = (wins / total * 100) if total > 0 else 0
print(f"Trades totais : {total}")
print(f"Wins          : {wins}  ({wr:.1f}%)")
print(f"Losses        : {losses}  ({100-wr:.1f}%)")

cur.execute("SELECT ROUND(AVG(pnl),3) FROM positions WHERE status='CLOSED' AND pnl>0")
avg_win = cur.fetchone()[0] or 0
cur.execute("SELECT ROUND(AVG(pnl),3) FROM positions WHERE status='CLOSED' AND pnl<=0")
avg_loss = cur.fetchone()[0] or 0
cur.execute("SELECT ROUND(SUM(pnl),2) FROM positions WHERE status='CLOSED'")
total_pnl = cur.fetchone()[0] or 0

print(f"PnL médio ganho : +{avg_win:.3f} USDC")
print(f"PnL médio perda : {avg_loss:.3f} USDC")
rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0
print(f"R:R real        : {rr:.2f}:1")
print(f"PnL total       : {total_pnl:+.2f} USDC")

print()
print("=" * 50)
print("POR RAZÃO DE FECHO")
print("=" * 50)
cur.execute("""
    SELECT close_reason, COUNT(*) as n,
           ROUND(SUM(pnl),2) as total,
           ROUND(AVG(pnl),3) as media
    FROM positions WHERE status='CLOSED'
    GROUP BY close_reason ORDER BY n DESC
""")
for r in cur.fetchall():
    print(f"  {r[0]:<20} {r[1]:>3}x  total={r[2]:>7.2f}  média={r[3]:>7.3f}")

print()
print("=" * 50)
print("ÚLTIMOS 20 TRADES")
print("=" * 50)
cur.execute("""
    SELECT symbol, direction,
           ROUND(entry_price,4) as entry,
           ROUND(pnl,3) as pnl,
           close_reason,
           datetime(closed_at, 'unixepoch') as dt
    FROM positions WHERE status='CLOSED'
    ORDER BY closed_at DESC LIMIT 20
""")
for r in cur.fetchall():
    sinal = "✓" if r["pnl"] > 0 else "✗"
    print(f"  {sinal} {r['symbol']:<15} {r['direction']:<5} entry={r['entry']}  pnl={r['pnl']:>7.3f}  [{r['close_reason']}]  {r['dt']}")

print()
print("=" * 50)
print("BOT STATE")
print("=" * 50)
cur.execute("SELECT key, value FROM bot_state WHERE key IN ('wins','losses','total_trades','loss_dia','perdas_seguidas')")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
