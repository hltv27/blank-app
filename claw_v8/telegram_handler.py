"""
Claw Agent v8 — Telegram command handler
Comandos: /status /fechar /pause /resume /pairs /help
Chamado pelo loop principal a cada ciclo; rate-limitado internamente.
"""
import time
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from storage import save_memory

_last_update_id = 0
_last_poll_ts   = 0
_POLL_INTERVAL  = 15  # segundos entre polls


def process_commands(mem: dict):
    """Processa comandos pendentes do Telegram. Modifica mem se /pause, /resume."""
    global _last_update_id, _last_poll_ts
    if time.time() - _last_poll_ts < _POLL_INTERVAL:
        return
    _last_poll_ts = time.time()
    for upd in _get_updates():
        msg = upd.get("message") or upd.get("edited_message") or {}
        if not msg:
            continue
        chat_id = str(msg.get("chat", {}).get("id", ""))
        if chat_id != str(TELEGRAM_CHAT_ID):
            continue
        text = msg.get("text", "").strip()
        if not text.startswith("/"):
            continue
        _handle(text.lower(), mem)


def _get_updates() -> list:
    global _last_update_id
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
            params={"timeout": 1, "offset": _last_update_id + 1, "limit": 20},
            timeout=5,
        )
        data = r.json()
        if not data.get("ok"):
            return []
        updates = data.get("result", [])
        if updates:
            _last_update_id = updates[-1]["update_id"]
        return updates
    except Exception:
        return []


def _tg(msg: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=8,
        )
    except Exception:
        pass


def _handle(text: str, mem: dict):
    if text in ("/status", "/s"):
        _cmd_status(mem)
    elif text.startswith("/fechar "):
        sym = text.split(" ", 1)[1].upper().strip()
        _cmd_fechar(sym, mem)
    elif text == "/pause":
        mem["paused"] = True
        save_memory(mem)
        _tg("⏸ <b>Bot pausado.</b> Sem novos trades — posições existentes continuam a ser geridas.")
    elif text == "/resume":
        mem["paused"] = False
        save_memory(mem)
        _tg("▶️ <b>Bot retomado.</b> Scan ativo.")
    elif text == "/pairs":
        _cmd_pairs()
    elif text in ("/help", "/start"):
        _tg(
            "📋 <b>Comandos disponíveis:</b>\n"
            "/status — posições e saldo actual\n"
            "/fechar SYMBOL — fecha posição do bot\n"
            "/pause — suspende novos trades\n"
            "/resume — retoma scan\n"
            "/pairs — lista pares activos\n"
            "/help — esta mensagem"
        )


def _cmd_status(mem: dict):
    from exchange import get_balance, get_price
    trades    = mem.get("trades_abertos", {})
    saldo     = get_balance()
    saldo_txt = f"{saldo:.2f} USDC" if saldo else "n/d"
    linhas    = []
    for sym, t in trades.items():
        p = get_price(sym)
        d = t.get("direction", "?")
        e = t.get("entry", 0)
        if p and e > 0:
            roi  = ((p - e) / e * 100) if d == "LONG" else ((e - p) / e * 100)
            icon = "🟢" if d == "LONG" else "🔴"
            lock = " 🔒" if t.get("profit_lock_level", 0) >= 1.0 else ""
            linhas.append(f"  {icon} {sym}: {roi:+.1f}%{lock}")
    pos_txt = "\n".join(linhas) if linhas else "  Nenhuma"
    flags   = []
    if mem.get("paused"):
        flags.append("⏸ PAUSADO")
    if time.time() < mem.get("btc_crash_lockout_until", 0):
        mins = int((mem["btc_crash_lockout_until"] - time.time()) / 60)
        flags.append(f"⚡ BTC_LOCK {mins}min")
    if time.time() < mem.get("emergency_cooldown_until", 0):
        mins = int((mem["emergency_cooldown_until"] - time.time()) / 60)
        flags.append(f"🛑 EMG_COOL {mins}min")
    flag_txt = " | " + " | ".join(flags) if flags else ""
    _tg(
        f"📊 <b>Status{flag_txt}</b>\n"
        f"Saldo: <b>{saldo_txt}</b> | Trades: {len(trades)}\n"
        f"Perdas hoje: {mem.get('loss_dia', 0):.2f} USDC | "
        f"Perdas seguidas: {mem.get('perdas_seguidas', 0)}\n"
        f"\n<b>Posições:</b>\n{pos_txt}"
    )


def _cmd_fechar(symbol: str, mem: dict):
    from exchange import get_positions, close_position
    if symbol not in mem.get("trades_abertos", {}):
        _tg(f"⚠️ <b>{symbol}</b> não está nos trades do bot.")
        return
    posicoes = get_positions()
    if not posicoes or symbol not in posicoes:
        _tg(f"⚠️ <b>{symbol}</b> não tem posição activa na exchange.")
        return
    pos  = posicoes[symbol]
    side = mem["trades_abertos"][symbol].get("direction", pos["side"])
    result = close_position(symbol, pos["qty"], side)
    if result:
        _tg(f"✅ <b>{symbol}</b> fechado via comando.\n<i>Bot regista fecho no próximo ciclo.</i>")
    else:
        _tg(f"❌ Falhou fechar <b>{symbol}</b> — tenta manualmente na app.")


def _cmd_pairs():
    import config
    syms = config.SYMBOLS
    n    = len(syms)
    txt  = ", ".join(syms[:15]) + (f" … +{n - 15}" if n > 15 else "")
    _tg(f"📋 <b>Pares activos ({n}):</b>\n{txt}")
