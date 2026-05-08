"""
Claw Agent v8.0 — SQLite Storage
Substitui JSON. Regista tudo: trades, filtros, estado, eventos de risco.
"""
import sqlite3
import json
import time
from datetime import datetime, timezone
from config import DB_FILE


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria todas as tabelas se não existirem."""
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS positions (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol        TEXT    NOT NULL,
        direction     TEXT    NOT NULL,
        entry_price   REAL,
        sl            REAL,
        tp            REAL,
        qty           REAL,
        qty_inicial   REAL,
        mode          TEXT,
        opened_at     REAL,
        closed_at     REAL,
        close_reason  TEXT,
        pnl           REAL,
        roi           REAL,
        stop_order_id TEXT,
        tp_order_id   TEXT,
        partial_tp_done INTEGER DEFAULT 0,
        status        TEXT    DEFAULT 'OPEN'
    );

    CREATE TABLE IF NOT EXISTS filter_events (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        ts             REAL    NOT NULL,
        symbol         TEXT    NOT NULL,
        direction      TEXT    NOT NULL,
        filter_name    TEXT    NOT NULL,
        passed         INTEGER NOT NULL,
        price_at_signal REAL,
        score          INTEGER,
        atr_pct        REAL,
        future_price_15m REAL,
        future_price_30m REAL,
        future_price_60m REAL
    );

    CREATE TABLE IF NOT EXISTS state_transitions (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        ts         REAL    NOT NULL,
        symbol     TEXT    NOT NULL,
        from_state TEXT,
        to_state   TEXT    NOT NULL,
        trigger    TEXT,
        details    TEXT
    );

    CREATE TABLE IF NOT EXISTS risk_events (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        ts         REAL    NOT NULL,
        event_type TEXT    NOT NULL,
        symbol     TEXT,
        details    TEXT
    );

    CREATE TABLE IF NOT EXISTS equity_snapshots (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        ts              REAL    NOT NULL,
        balance         REAL,
        margin_ratio    REAL,
        open_positions  INTEGER,
        daily_pnl       REAL
    );

    CREATE TABLE IF NOT EXISTS bot_state (
        key        TEXT PRIMARY KEY,
        value      TEXT,
        updated_at REAL
    );
    """)

    conn.commit()
    conn.close()
    print("[v8] SQLite inicializado")


# ─────────────────────────────────────────────
#  BOT STATE (substitui claw_memory_v7.json)
# ─────────────────────────────────────────────

def state_get(key: str, default=None):
    conn = get_conn()
    row  = conn.execute("SELECT value FROM bot_state WHERE key=?", (key,)).fetchone()
    conn.close()
    if row is None:
        return default
    try:
        return json.loads(row["value"])
    except Exception:
        return row["value"]


def state_set(key: str, value):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO bot_state(key, value, updated_at) VALUES(?,?,?)",
        (key, json.dumps(value), time.time())
    )
    conn.commit()
    conn.close()


def load_memory() -> dict:
    """Carrega estado completo do bot (equivalente ao JSON anterior)."""
    return {
        "loss_dia":         state_get("loss_dia",         0.0),
        "perdas_seguidas":  state_get("perdas_seguidas",  0),
        "trades_abertos":   state_get("trades_abertos",   {}),
        "ultimo_reset":     state_get("ultimo_reset",     ""),
        "bloqueado_ate":    state_get("bloqueado_ate",    0),
        "total_trades":     state_get("total_trades",     0),
        "wins":             state_get("wins",             0),
        "losses":           state_get("losses",           0),
        "simbolos_stats":   state_get("simbolos_stats",   {}),
    }


def save_memory(mem: dict):
    """Persiste estado completo do bot no SQLite."""
    for key, value in mem.items():
        state_set(key, value)


# ─────────────────────────────────────────────
#  POSITIONS
# ─────────────────────────────────────────────

def open_position(symbol: str, direction: str, entry_price: float, sl: float,
                  tp: float, qty: float, mode: str, stop_order_id,
                  tp_order_id) -> int:
    conn = get_conn()
    c    = conn.cursor()
    c.execute("""
        INSERT INTO positions
        (symbol, direction, entry_price, sl, tp, qty, qty_inicial, mode,
         opened_at, stop_order_id, tp_order_id, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,'OPEN')
    """, (symbol, direction, entry_price, sl, tp, qty, qty,
          mode, time.time(), str(stop_order_id), str(tp_order_id)))
    pos_id = c.lastrowid
    conn.commit()
    conn.close()
    log_state_transition(symbol, None, "OPEN", "ORDER_FILLED",
                         f"entry={entry_price} sl={sl} tp={tp}")
    return pos_id


def close_position_db(symbol: str, close_reason: str, pnl: float, roi: float):
    conn = get_conn()
    conn.execute("""
        UPDATE positions
        SET status='CLOSED', closed_at=?, close_reason=?, pnl=?, roi=?
        WHERE symbol=? AND status='OPEN'
    """, (time.time(), close_reason, pnl, roi, symbol))
    conn.commit()
    conn.close()
    log_state_transition(symbol, "OPEN", "CLOSED", close_reason,
                         f"pnl={pnl:.2f} roi={roi:.1f}%")


def update_position_partial_tp(symbol: str, qty_restante: float):
    conn = get_conn()
    conn.execute("""
        UPDATE positions SET qty=?, partial_tp_done=1
        WHERE symbol=? AND status='OPEN'
    """, (qty_restante, symbol))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  FILTER EVENTS (attribution)
# ─────────────────────────────────────────────

def log_filter_event(symbol: str, direction: str, filter_name: str,
                     passed: bool, price: float, score: int = 0, atr_pct: float = 0.0):
    """
    Regista cada filtro avaliado — passou ou bloqueou.
    Os future_price_* são preenchidos mais tarde pelo analytics.
    """
    conn = get_conn()
    conn.execute("""
        INSERT INTO filter_events
        (ts, symbol, direction, filter_name, passed, price_at_signal, score, atr_pct)
        VALUES (?,?,?,?,?,?,?,?)
    """, (time.time(), symbol, direction, filter_name,
          1 if passed else 0, price, score, atr_pct))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  STATE TRANSITIONS
# ─────────────────────────────────────────────

def log_state_transition(symbol: str, from_state, to_state: str,
                          trigger: str, details: str = ""):
    conn = get_conn()
    conn.execute("""
        INSERT INTO state_transitions (ts, symbol, from_state, to_state, trigger, details)
        VALUES (?,?,?,?,?,?)
    """, (time.time(), symbol, from_state, to_state, trigger, details))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  RISK EVENTS
# ─────────────────────────────────────────────

def log_risk_event(event_type: str, symbol: str = None, details: str = ""):
    conn = get_conn()
    conn.execute("""
        INSERT INTO risk_events (ts, event_type, symbol, details)
        VALUES (?,?,?,?)
    """, (time.time(), event_type, symbol, details))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  EQUITY SNAPSHOTS
# ─────────────────────────────────────────────

def log_equity_snapshot(balance: float, margin_ratio: float,
                         open_positions: int, daily_pnl: float):
    conn = get_conn()
    conn.execute("""
        INSERT INTO equity_snapshots (ts, balance, margin_ratio, open_positions, daily_pnl)
        VALUES (?,?,?,?,?)
    """, (time.time(), balance, margin_ratio, open_positions, daily_pnl))
    conn.commit()
    conn.close()
