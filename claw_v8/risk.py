"""
Claw Agent v8.0 — Gestão de risco
Circuit breakers, position sizing, sessão, vetos por símbolo.
"""
import time
from datetime import datetime, timezone, timedelta
from config import (
    MAX_LOSS_DIA, MAX_PERDAS_SEGUIDAS, COOLDOWN_MIN,
    SESSOES_UTC, ALAVANCAGEM, CAPITAL_MAX_BOT, RISCO_USDC
)
from storage import save_memory, log_risk_event
from exchange import tg


# ─────────────────────────────────────────────
#  SESSÃO
# ─────────────────────────────────────────────

def em_sessao() -> bool:
    hora = datetime.now(timezone.utc).hour
    return any(inicio <= hora < fim for inicio, fim in SESSOES_UTC)


def ny_open_utc() -> tuple[int, int]:
    now  = datetime.now(timezone.utc)
    year = now.year
    mar1 = datetime(year, 3, 1, tzinfo=timezone.utc)
    dst_start = mar1 + timedelta(days=(6 - mar1.weekday()) % 7 + 7, hours=7)
    nov1 = datetime(year, 11, 1, tzinfo=timezone.utc)
    dst_end = nov1 + timedelta(days=(6 - nov1.weekday()) % 7, hours=6)
    if dst_start <= now < dst_end:
        return 13, 30
    return 14, 30


# ─────────────────────────────────────────────
#  CIRCUIT BREAKER
# ─────────────────────────────────────────────

def circuit_breaker_activo(mem: dict) -> tuple[bool, str]:
    now  = time.time()
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if mem.get("ultimo_reset") != hoje:
        mem["loss_dia"]        = 0.0
        mem["perdas_seguidas"] = 0
        mem["bloqueado_ate"]   = 0
        mem["ultimo_reset"]    = hoje
        save_memory(mem)

    if now < mem.get("bloqueado_ate", 0):
        minutos = int((mem["bloqueado_ate"] - now) / 60)
        return True, f"COOLDOWN {minutos}min"

    if mem.get("loss_dia", 0) >= MAX_LOSS_DIA:
        mem["bloqueado_ate"] = now + COOLDOWN_MIN * 60
        save_memory(mem)
        log_risk_event("CIRCUIT_BREAKER_DAILY", details=f"loss_dia={mem['loss_dia']:.2f}")
        return True, f"LOSS_DIA {mem['loss_dia']:.2f} USDC"

    if mem.get("perdas_seguidas", 0) >= MAX_PERDAS_SEGUIDAS:
        mem["bloqueado_ate"]   = now + COOLDOWN_MIN * 60
        mem["perdas_seguidas"] = 0
        save_memory(mem)
        log_risk_event("CIRCUIT_BREAKER_STREAK", details=f"perdas={MAX_PERDAS_SEGUIDAS}")
        return True, f"PERDAS_SEGUIDAS {MAX_PERDAS_SEGUIDAS}"

    return False, ""


# ─────────────────────────────────────────────
#  EQUITY CURVE FEEDBACK
# ─────────────────────────────────────────────

def equity_scale_factor(mem: dict) -> float:
    perdas = mem.get("perdas_seguidas", 0)
    if perdas >= 3:
        print(f"[EQUITY] {perdas} perdas seguidas — tamanho reduzido 50%")
        return 0.5
    return 1.0


# ─────────────────────────────────────────────
#  VETO POR SÍMBOLO
# ─────────────────────────────────────────────

def verificar_veto_simbolo(symbol: str, mem: dict) -> tuple[bool, str]:
    stats = mem.get("simbolos_stats", {}).get(symbol)
    if not stats:
        return False, ""
    vetado_ate = stats.get("vetado_ate", 0)
    if vetado_ate <= 0:
        return False, ""
    if time.time() < vetado_ate:
        mins = int((vetado_ate - time.time()) / 60)
        return True, f"vetado ainda {mins}min"
    stats["perdas_seguidas"] = 0
    stats["vetado_ate"]      = 0
    total = stats.get("wins", 0) + stats.get("losses", 0)
    wr    = stats.get("wins", 0) / total * 100 if total > 0 else 0
    tg(
        f"\U0001f513 <b>VETO EXPIRADO — {symbol}</b>\n"
        f"Stats: {stats.get('wins',0)}W / {stats.get('losses',0)}L | "
        f"WR: {wr:.0f}% | PnL: {stats.get('pnl_total',0):+.2f}\n"
        f"<i>Perdas seguidas reiniciadas.</i>"
    )
    save_memory(mem)
    return False, ""


def atualizar_stats_simbolo(symbol: str, won: bool, pnl: float, mem: dict):
    stats = mem.setdefault("simbolos_stats", {}).setdefault(symbol, {
        "wins": 0, "losses": 0, "perdas_seguidas": 0,
        "pnl_total": 0.0, "vetado_ate": 0
    })
    stats["pnl_total"]    = round(stats.get("pnl_total", 0) + pnl, 4)
    stats["ultima_trade"] = datetime.now(timezone.utc).isoformat()

    if won:
        stats["wins"]             = stats.get("wins", 0) + 1
        stats["perdas_seguidas"]  = 0
    else:
        stats["losses"]           = stats.get("losses", 0) + 1
        stats["perdas_seguidas"]  = stats.get("perdas_seguidas", 0) + 1

    total  = stats["wins"] + stats["losses"]
    wr     = stats["wins"] / total * 100 if total > 0 else 100
    ps     = stats["perdas_seguidas"]
    motivo = None

    if ps >= 3:
        motivo = f"3 perdas seguidas ({ps}x)"
        stats["vetado_ate"] = time.time() + 24 * 3600
    elif total >= 5 and wr < 30:
        motivo = f"win rate crítico {wr:.0f}% em {total} trades"
        stats["vetado_ate"] = time.time() + 72 * 3600  # 3 dias (era 12h)

    if motivo:
        h_veto = 24 if ps >= 3 else 72
        tg(
            f"\U0001f6ab <b>VETO — {symbol}</b>\nMotivo: {motivo}\n"
            f"Stats: {stats['wins']}W / {stats['losses']}L | "
            f"WR: {wr:.0f}% | PnL: {stats['pnl_total']:+.2f}\n"
            f"Bot não abre {symbol} durante {h_veto}h."
        )
        log_risk_event("VETO_SIMBOLO", symbol=symbol, details=motivo)
