#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║              CLAW AGENT v8.0 — Clean Core               ║
║  Estrutura modular | SQLite | Filter Attribution         ║
║  Mesma estratégia da v7.1 — zero alterações de lógica   ║
╚══════════════════════════════════════════════════════════╝
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import subprocess
import time
import traceback
import threading
from datetime import datetime, timezone, timedelta
import config
from config import (
    BTC_SYMBOLS, MAX_TRADES_ABERTOS,
    MAX_LONGS_ALT, MAX_SHORTS_ALT, LOOKBACK,
    CHECK_POSICOES_FAST, CHECK_POSICOES, CAPITAL_MAX_BOT, RISCO_USDC,
    ALAVANCAGEM, TOP_N_FUTURES, FORCE_INCLUDE_SYMBOLS,
    PROFIT_LOCK_USDC, PROFIT_LOCK_STEP, SCORE_LONG_MIN
)
import math
from exchange import (
    tg, get_klines, get_positions, get_balance, get_price, sync_time, get_public_ip,
    get_top_futures_symbols, place_stop_market, cancel_algo_order, get_open_algo_orders,
    close_position
)
from indicators import atr, get_daily_vwap
from strategy import detect_market_mode, signal_trending
from filters import calc_correlation
from risk import em_sessao, circuit_breaker_activo, verificar_veto_simbolo
from execution import abrir_trade, gerir_posicoes
from storage import init_db, load_memory, save_memory, log_state_transition
from analytics import print_full_report
from telegram_handler import process_commands


def _relatorio_diario(mem: dict):
    """Relatório diário às 23:00 UTC → Telegram + status.json + git push."""
    try:
        from storage import get_conn
        data_hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Stats do dia via SQLite
        conn = get_conn()
        rows = conn.execute(
            "SELECT pnl, direction FROM positions WHERE status='CLOSED' AND date(closed_at,'unixepoch') = ?",
            (data_hoje,)
        ).fetchall()
        conn.close()

        pnl_dia   = round(sum(r["pnl"] for r in rows if r["pnl"] is not None), 2)
        wins_dia  = sum(1 for r in rows if (r["pnl"] or 0) > 0)
        losses_dia = sum(1 for r in rows if (r["pnl"] or 0) <= 0)
        total_dia  = len(rows)
        wr_dia     = round(wins_dia / total_dia * 100, 1) if total_dia > 0 else 0.0
        melhor     = max(rows, key=lambda r: r["pnl"] or 0, default=None)
        pior       = min(rows, key=lambda r: r["pnl"] or 0, default=None)

        saldo = get_balance() or 0

        # Posições abertas com ROI actual
        abertos = []
        for sym, t in mem.get("trades_abertos", {}).items():
            preco = get_price(sym)
            roi = 0.0
            if preco and t.get("entry", 0) > 0:
                roi = ((preco - t["entry"]) / t["entry"] * 100
                       if t["direction"] == "LONG"
                       else (t["entry"] - preco) / t["entry"] * 100)
            abertos.append({"symbol": sym, "side": t["direction"],
                            "entry": t.get("entry", 0), "roi_pct": round(roi, 2)})

        cb_activo, cb_motivo = circuit_breaker_activo(mem)
        status = {
            "data":    data_hoje,
            "ts":      int(time.time()),
            "saldo":   round(saldo, 2),
            "pnl_dia": pnl_dia,
            "trades":  {"total": total_dia, "wins": wins_dia,
                        "losses": losses_dia, "wr_pct": wr_dia},
            "abertos": abertos,
            "melhor":  {"symbol": melhor["symbol"] if hasattr(melhor, '__getitem__') else "", "pnl": round(melhor["pnl"] or 0, 2)} if melhor else None,
            "pior":    {"symbol": pior["symbol"] if hasattr(pior, '__getitem__') else "", "pnl": round(pior["pnl"] or 0, 2)} if pior else None,
            "circuit_breaker": cb_activo,
            "cb_motivo": cb_motivo if cb_activo else "",
            "wins_total":   mem.get("wins", 0),
            "losses_total": mem.get("losses", 0),
            "versao": "v8.0",
        }

        # Escreve status.json (último dia — para Claude ler rapidamente)
        base_path = os.path.dirname(__file__)
        status_path = os.path.join(base_path, "status.json")
        with open(status_path, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)

        # Append status_history.jsonl (histórico completo, nunca sobrescreve)
        history_path = os.path.join(base_path, "status_history.jsonl")
        with open(history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(status, ensure_ascii=False) + "\n")

        # Git pull + push (evita conflitos se houve outro commit entretanto)
        repo_path = os.path.abspath(os.path.join(base_path, ".."))
        subprocess.run(["git", "-C", repo_path, "pull", "--rebase", "origin", "main"],
                       capture_output=True, timeout=60)
        subprocess.run(["git", "-C", repo_path, "add",
                        "claw_v8/status.json", "claw_v8/status_history.jsonl"],
                       capture_output=True, timeout=30)
        subprocess.run(["git", "-C", repo_path, "commit", "-m", f"status: {data_hoje}"],
                       capture_output=True, timeout=30)
        r = subprocess.run(["git", "-C", repo_path, "push", "origin", "main"],
                           capture_output=True, timeout=60)
        push_ok = r.returncode == 0

        # Telegram
        pos_txt    = ", ".join(f"{p['symbol'].replace('USDC','')} {p['roi_pct']:+.1f}%" for p in abertos) or "Nenhuma"
        melhor_txt = f"{melhor['symbol'].replace('USDC','')} +{melhor['pnl']:.2f}" if melhor else "n/a"
        pior_txt   = f"{pior['symbol'].replace('USDC','')} {pior['pnl']:.2f}" if pior else "n/a"
        cb_txt     = f" | ⛔ CB: {cb_motivo}" if cb_activo else ""
        push_txt   = "📁 GitHub ✅" if push_ok else "📁 push ⚠️"

        tg(
            f"📊 <b>Relatório {data_hoje}</b>\n"
            f"💰 Saldo: <b>{saldo:.2f} USDC</b> | P&amp;L dia: <b>{pnl_dia:+.2f} USDC</b>\n"
            f"📈 Trades: {total_dia} ({wins_dia}W/{losses_dia}L) WR {wr_dia:.0f}%\n"
            f"🔓 Abertos: {pos_txt}\n"
            f"⭐ {melhor_txt}  💀 {pior_txt}{cb_txt}\n"
            f"{push_txt}"
        )
        print(f"[v8] Relatório diário {data_hoje} — push {'OK' if push_ok else 'FALHOU'}")

    except Exception as e:
        print(f"[ERRO] relatorio_diario: {e}")
        tg(f"⚠️ Relatório diário falhou: {e}")


def _validate_credentials():
    from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, BINANCE_API_KEY, BINANCE_API_SECRET
    placeholders = {"TOKEN_AQUI", "CHATID_AQUI", "APIKEY_AQUI", "SECRET_AQUI"}
    missing = [
        name for name, val in [
            ("TELEGRAM_TOKEN",     TELEGRAM_TOKEN),
            ("TELEGRAM_CHAT_ID",   TELEGRAM_CHAT_ID),
            ("BINANCE_API_KEY",    BINANCE_API_KEY),
            ("BINANCE_API_SECRET", BINANCE_API_SECRET),
        ]
        if val in placeholders
    ]
    if missing:
        raise SystemExit(f"[ERRO] Credenciais não definidas: {', '.join(missing)}")


def run():
    _validate_credentials()
    init_db()
    sync_time()

    # Fetch dinâmico dos top N pares USDC-M por volume + precisão
    dinamicos, precisoes, price_precisoes = get_top_futures_symbols(TOP_N_FUTURES)
    if dinamicos:
        # Merge: top N + FORCE_INCLUDE_SYMBOLS (sem duplicados, força-include no fim)
        extras = [s for s in FORCE_INCLUDE_SYMBOLS if s not in dinamicos]
        config.SYMBOLS = dinamicos + extras
    if precisoes:
        config.SYMBOL_PRECISION.update(precisoes)
    if price_precisoes:
        config.PRICE_PRECISION.update(price_precisoes)
    SYMBOLS = config.SYMBOLS

    ultima_actualizacao_symbols = time.time()

    # ── Watchdog thread: alerta se loop principal parar > 5min ──────────
    _heartbeat = [time.time()]

    def _watchdog():
        while True:
            time.sleep(120)
            if time.time() - _heartbeat[0] > 300:
                tg("🚨 <b>WATCHDOG</b> — loop principal inativo há 5min. A reiniciar processo...")
                print("[WATCHDOG] loop principal parado há 5min — a forçar saída para reinício automático")
                os._exit(1)

    threading.Thread(target=_watchdog, daemon=True).start()

    ip_atual = get_public_ip()
    tg(
        "🤖 <b>Claw Agent v8.0 iniciado</b>\n"
        f"Pares: {len(SYMBOLS)} (top {TOP_N_FUTURES} USDC-M) | Capital: {CAPITAL_MAX_BOT} USDC\n"
        f"Cross Margin | Alavancagem: {ALAVANCAGEM}x\n"
        f"Modo: TRENDING | SQLite: ativo\n"
        f"IP: <code>{ip_atual}</code>"
    )
    print(f"[v8.0] Claw Agent a correr — {len(SYMBOLS)} pares")

    ultimo_minuto_scan  = -1
    ultima_sync_hora    = -1
    ultimo_resumo_hora  = -1
    # Carrega do SQLite — sobrevive a restarts (não perde dias)
    from storage import state_get, state_set
    ultimo_relatorio_dia = state_get("ultimo_relatorio_dia", -1)

    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            hora    = now_utc.strftime("%H:%M")
            mem     = load_memory()
            _heartbeat[0] = time.time()
            process_commands(mem)

            if now_utc.hour != ultima_sync_hora:
                sync_time()
                ultima_sync_hora = now_utc.hour

            # Relatório diário: 23:00 UTC normalmente, catch-up imediato se houve dia(s) sem relatório
            if now_utc.day != ultimo_relatorio_dia:
                yesterday = (now_utc - timedelta(days=1)).day
                missed_day = (ultimo_relatorio_dia != yesterday and ultimo_relatorio_dia != -1)
                if now_utc.hour == 23 or missed_day:
                    ultimo_relatorio_dia = now_utc.day
                    state_set("ultimo_relatorio_dia", ultimo_relatorio_dia)
                    _relatorio_diario(mem)

            # Actualiza lista de pares a cada 24h
            if time.time() - ultima_actualizacao_symbols > 86400:
                novos, precisoes_novas, price_precisoes_novas = get_top_futures_symbols(TOP_N_FUTURES)
                if novos:
                    extras_novos = [s for s in FORCE_INCLUDE_SYMBOLS if s not in novos]
                    config.SYMBOLS = novos + extras_novos
                    SYMBOLS = config.SYMBOLS
                if precisoes_novas:
                    config.SYMBOL_PRECISION.update(precisoes_novas)
                if price_precisoes_novas:
                    config.PRICE_PRECISION.update(price_precisoes_novas)
                print(f"[{hora}] Pares actualizados: {len(SYMBOLS)}")
                ultima_actualizacao_symbols = time.time()

            # ── Resumo horário de mercado ─────────────────────────────────
            if now_utc.hour != ultimo_resumo_hora:
                ultimo_resumo_hora = now_utc.hour
                try:
                    trades_abertos = mem.get("trades_abertos", {})
                    n_abertos = len(trades_abertos)
                    linhas_pos = []
                    for sym, t in trades_abertos.items():
                        preco_a = get_price(sym)
                        if preco_a and t.get("entry", 0) > 0:
                            if t["direction"] == "LONG":
                                roi = (preco_a - t["entry"]) / t["entry"] * 100
                            else:
                                roi = (t["entry"] - preco_a) / t["entry"] * 100
                            icone = "🟢" if t["direction"] == "LONG" else "🔴"
                            linhas_pos.append(
                                f"  {icone} {sym}: {roi:+.1f}% (entry {t['entry']:.4g})"
                            )

                    # Scan rápido de modo de mercado (BTC_SYMBOLS primeiro)
                    sample = list(BTC_SYMBOLS) + [s for s in SYMBOLS if s not in BTC_SYMBOLS][:8]
                    trending_list, morto_list = [], []
                    for sym in sample:
                        kl = get_klines(sym)
                        if not kl or len(kl) < 30:
                            continue
                        h_r = [float(k[2]) for k in kl]
                        l_r = [float(k[3]) for k in kl]
                        c_r = [float(k[4]) for k in kl]
                        from indicators import atr as _atr
                        from strategy import detect_market_mode as _dmm
                        atr_r = _atr(h_r, l_r, c_r)
                        modo_r = _dmm(c_r, atr_r)
                        if modo_r == "TRENDING":
                            trending_list.append(sym.replace("USDC", ""))
                        else:
                            morto_list.append(sym.replace("USDC", ""))

                    saldo = get_balance()
                    saldo_txt = f"{saldo:.2f} USDC" if saldo else "n/d"

                    pos_txt = "\n".join(linhas_pos) if linhas_pos else "  Nenhuma"
                    trend_txt = ", ".join(trending_list) if trending_list else "nenhum"
                    msg = (
                        f"📊 <b>Status {hora} UTC</b>\n"
                        f"Saldo: <b>{saldo_txt}</b> | Trades: {n_abertos}/{MAX_TRADES_ABERTOS}\n"
                        f"\n<b>Posições abertas:</b>\n{pos_txt}\n"
                        f"\n<b>TRENDING</b> ({len(trending_list)}/{len(sample)}): {trend_txt}"
                    )
                    tg(msg)
                    print(f"[{hora}] Resumo horário enviado")
                except Exception as _e:
                    print(f"[{hora}] Resumo horário falhou: {_e}")

            # ── Gestão de posições abertas + guard de liquidação global ──
            tem_posicoes = bool(mem.get("trades_abertos"))
            # gerir_posicoes corre sempre: inclui guard de liquidação global
            # que protege a conta mesmo sem trades do bot abertos
            gerir_posicoes(mem)
            mem = load_memory()

            # ── Scan alinhado com velas de 5 min ──────────────────────────
            minuto         = now_utc.minute
            sleep_interval = CHECK_POSICOES_FAST if tem_posicoes else CHECK_POSICOES
            if minuto % 5 != 0 or minuto == ultimo_minuto_scan:
                time.sleep(sleep_interval)
                continue

            ultimo_minuto_scan = minuto

            if not em_sessao():
                print(f"[{hora}] Fora sessão")
                continue

            bloqueado, motivo = circuit_breaker_activo(mem)
            if bloqueado:
                print(f"[{hora}] BLOQUEADO: {motivo}")
                continue

            # Sincroniza memória com posições reais
            posicoes_reais = get_positions()
            if posicoes_reais is None:
                print(f"[{hora}] get_positions falhou — scan ignorado")
                continue

            for symbol, pos in posicoes_reais.items():
                if symbol not in mem.get("trades_abertos", {}):
                    # Verifica se o bot iniciou esta ordem (marcador pending_sync)
                    pending = mem.get("pending_sync", {})
                    already_external = symbol in mem.get("posicoes_externas", {})
                    is_bot_orphan = (symbol in pending and
                                     time.time() - pending[symbol] < 300  # < 5 min
                                     and not already_external)

                    if is_bot_orphan and symbol in SYMBOLS:
                        # Posição órfã do bot (ordem enviada mas memória não guardada)
                        mem.get("pending_sync", {}).pop(symbol, None)
                        kl_sync = get_klines(symbol)
                        sync_stop_id = None
                        sync_sl = 0.0
                        if kl_sync and len(kl_sync) > 14:
                            from indicators import atr as calc_atr
                            h_s = [float(k[2]) for k in kl_sync]
                            l_s = [float(k[3]) for k in kl_sync]
                            c_s = [float(k[4]) for k in kl_sync]
                            atr_s   = calc_atr(h_s, l_s, c_s)
                            entry_s = pos["entry"] if pos["entry"] > 0 else c_s[-1]
                            stop_side_s = "SELL" if pos["side"] == "LONG" else "BUY"
                            if pos["side"] == "LONG":
                                sync_sl = round(entry_s - atr_s * 1.5, 8)
                            else:
                                sync_sl = round(entry_s + atr_s * 1.5, 8)
                            sync_stop_id = place_stop_market(symbol, stop_side_s, sync_sl, 0)

                        mem.setdefault("trades_abertos", {})[symbol] = {
                            "direction":     pos["side"],
                            "entry":         pos["entry"],
                            "sl":            sync_sl,
                            "tp":            0,
                            "qty":           pos["qty"],
                            "qty_inicial":   abs(pos["qty"]),
                            "mode":          "SYNC",
                            "opened_at":     time.time(),
                            "stop_order_id": sync_stop_id,
                        }
                        save_memory(mem)
                        log_state_transition(symbol, None, "OPEN", "SYNC",
                                             f"entry={pos['entry']} side={pos['side']}")
                        try:
                            from storage import open_position as db_open_pos
                            db_open_pos(symbol, pos["side"], pos["entry"],
                                        0, 0, abs(pos["qty"]), "SYNC",
                                        sync_stop_id, None)
                        except Exception as _db_e:
                            print(f"[AVISO] db_open_pos sync falhou: {_db_e}")
                        dir_icon = "🟢 LONG" if pos["side"] == "LONG" else "🔴 SHORT"
                        stop_txt = f"Stop#{sync_stop_id}" if sync_stop_id else "SL em memória"
                        print(f"[{hora}] {symbol} sincronizado (órfão do bot)")
                        tg(
                            f"🔄 <b>{dir_icon}</b> — {symbol} (órfão recuperado)\n"
                            f"Entrada: {pos['entry']:.4f} | 🔒 {stop_txt}"
                        )

                    elif symbol not in mem.get("posicoes_externas", {}):
                        # Posição manual (sem marcador pending_sync) — monitorizar sem gerir
                        externas = mem.setdefault("posicoes_externas", {})
                        externas[symbol] = {
                            "direction":  pos["side"],
                            "entry":      pos["entry"],
                            "qty":        pos["qty"],
                            "opened_at":  time.time(),
                            "alertas":    [],
                        }
                        save_memory(mem)
                        dir_icon = "🟢 LONG" if pos["side"] == "LONG" else "🔴 SHORT"
                        notional = abs(pos["qty"]) * pos["entry"] if pos["entry"] > 0 else 0
                        na_lista = " (par do bot)" if symbol in SYMBOLS else ""
                        print(f"[{hora}] EXTERNA detectada: {symbol} {pos['side']}{na_lista}")
                        tg(
                            f"👁 <b>Posição manual detectada</b>\n"
                            f"{dir_icon} <b>{symbol}</b>{na_lista}\n"
                            f"Entrada: <code>{pos['entry']:.6g}</code> | "
                            f"Qty: {abs(pos['qty']):.4g} | ~{notional:.1f} USDC\n"
                            f"<i>Bot não fecha nem conta para os limites. A partir de +{PROFIT_LOCK_USDC:.1f} USDC, bloqueia lucro a cada {PROFIT_LOCK_STEP:.1f} USDC.</i>"
                        )


            # ── Monitorização de posições externas ───────────────────────
            externas = mem.get("posicoes_externas", {})
            fechadas_ext = []
            for symbol, ext in externas.items():
                if symbol in posicoes_reais:
                    # Ainda aberta — verifica P&L
                    preco_atual = get_price(symbol)
                    if preco_atual and ext["entry"] > 0:
                        if ext["direction"] == "LONG":
                            roi = (preco_atual - ext["entry"]) / ext["entry"] * 100
                        else:
                            roi = (ext["entry"] - preco_atual) / ext["entry"] * 100
                        niveis = [-5, -3, 3, 5, 10, 15, 20]
                        for nivel in niveis:
                            tag = f"alerta_{nivel}"
                            if tag not in ext["alertas"]:
                                if (nivel < 0 and roi <= nivel) or (nivel > 0 and roi >= nivel):
                                    ext["alertas"].append(tag)
                                    save_memory(mem)
                                    icone = "🚨" if nivel < 0 else "💰"
                                    print(f"[{hora}] EXTERNA {symbol} ROI {roi:+.1f}%")
                                    tg(
                                        f"{icone} <b>{symbol}</b> (externa) — "
                                        f"ROI: <b>{roi:+.1f}%</b>\n"
                                        f"Entrada: {ext['entry']:.6g} | "
                                        f"Actual: {preco_atual:.6g}"
                                    )

                    # ── Lock de lucro progressivo (mesma lógica do bot) ──────
                    pos_real = posicoes_reais[symbol]
                    pnl_ext  = pos_real["pnl"]
                    qty_ext  = abs(pos_real["qty"])
                    side_ext = ext["direction"]
                    current_lock_ext = ext.get("profit_lock_level", 0.0)
                    if qty_ext > 0 and ext["entry"] > 0 and pnl_ext >= PROFIT_LOCK_USDC:
                        new_lock_ext = math.floor(pnl_ext / PROFIT_LOCK_STEP) * PROFIT_LOCK_STEP
                        if new_lock_ext >= PROFIT_LOCK_USDC and new_lock_ext > current_lock_ext + 1e-9:
                            lock_usdc_ext = max(new_lock_ext - PROFIT_LOCK_STEP, 0.0)
                            if side_ext == "LONG":
                                lock_price_ext = (round(ext["entry"] + lock_usdc_ext / qty_ext, 8)
                                                   if lock_usdc_ext > 0 else round(ext["entry"] * 1.0005, 8))
                            else:
                                lock_price_ext = (round(ext["entry"] - lock_usdc_ext / qty_ext, 8)
                                                   if lock_usdc_ext > 0 else round(ext["entry"] * 0.9995, 8))

                            # Primeira activação: pode já existir stop colocado manualmente
                            # pelo utilizador — cancela TUDO antes (só pode haver 1 closePosition stop)
                            if current_lock_ext == 0.0:
                                for old_algo_id in get_open_algo_orders(symbol):
                                    cancel_algo_order(symbol, old_algo_id)
                            old_stop_ext = ext.get("stop_order_id")
                            if old_stop_ext:
                                cancel_algo_order(symbol, old_stop_ext)
                                ext["stop_order_id"] = None

                            lock_side_ext = "SELL" if side_ext == "LONG" else "BUY"
                            new_lock_id_ext = None
                            for attempt in range(3):
                                new_lock_id_ext = place_stop_market(symbol, lock_side_ext, lock_price_ext, qty_ext)
                                if new_lock_id_ext:
                                    break
                                if side_ext == "LONG":
                                    lock_price_ext = round(lock_price_ext * (1 - 0.0015), 8)
                                else:
                                    lock_price_ext = round(lock_price_ext * (1 + 0.0015), 8)
                                time.sleep(0.5)

                            ext["profit_lock_level"] = new_lock_ext
                            ext["stop_order_id"]     = new_lock_id_ext
                            save_memory(mem)
                            emoji_ext = "🔒" if current_lock_ext == 0.0 else "📈"
                            stop_info_ext = f"#{new_lock_id_ext}" if new_lock_id_ext else "SOFTWARE ⚠️"
                            if not new_lock_id_ext:
                                print(f"[AVISO] {symbol} (externa): lock stop falhou após 3 tentativas")
                            tg(
                                f"{emoji_ext} <b>LOCK +{new_lock_ext:.1f} USDC</b> — {symbol} (externa)\n"
                                f"Stop → {lock_price_ext:.6g} ({stop_info_ext}) | PnL: +{pnl_ext:.2f} USDC"
                            )

                    # ── Software stop enforcement (externa) ─────────────────
                    # Se lock activo + stop não colocado na exchange → fecha via MARKET
                    # quando PnL cai abaixo do nível protegido
                    current_lock_ext = ext.get("profit_lock_level", 0.0)
                    if current_lock_ext > 0 and not ext.get("stop_order_id"):
                        lock_floor = max(current_lock_ext - PROFIT_LOCK_STEP, 0.0)
                        if pnl_ext <= lock_floor:
                            close_side_ext = "SELL" if ext["direction"] == "LONG" else "BUY"
                            close_result = close_position(symbol, qty_ext, ext["direction"])
                            if close_result:
                                fechadas_ext.append(symbol)
                                tg(
                                    f"🔒🔻 <b>SOFTWARE STOP</b> — {symbol} (externa)\n"
                                    f"Lock era +{current_lock_ext:.1f} | PnL caiu para {pnl_ext:+.2f} USDC\n"
                                    f"Fechada via MARKET (stop exchange não existia)"
                                )
                            else:
                                tg(
                                    f"⚠️ <b>SOFTWARE STOP FALHOU</b> — {symbol}\n"
                                    f"PnL: {pnl_ext:+.2f} < lock {lock_floor:+.1f} — FECHAR MANUALMENTE!"
                                )

                else:
                    # Fechada — calcula P&L final
                    fechadas_ext.append(symbol)
                    preco_fecho = get_price(symbol)
                    if preco_fecho and ext["entry"] > 0:
                        if ext["direction"] == "LONG":
                            roi = (preco_fecho - ext["entry"]) / ext["entry"] * 100
                        else:
                            roi = (ext["entry"] - preco_fecho) / ext["entry"] * 100
                        icone = "✅" if roi > 0 else "❌"
                        duracao_h = (time.time() - ext["opened_at"]) / 3600
                        print(f"[{hora}] EXTERNA {symbol} fechada ROI {roi:+.1f}%")
                        tg(
                            f"{icone} <b>{symbol}</b> (externa) — fechada\n"
                            f"ROI: <b>{roi:+.1f}%</b> | "
                            f"Duração: {duracao_h:.1f}h\n"
                            f"Entrada: {ext['entry']:.6g} | "
                            f"Fecho: ~{preco_fecho:.6g}"
                        )
            for symbol in fechadas_ext:
                del mem["posicoes_externas"][symbol]
            if fechadas_ext:
                save_memory(mem)

            if len(posicoes_reais) >= MAX_TRADES_ABERTOS:
                print(f"[{hora}] Max trades abertos ({len(posicoes_reais)})")
                continue

            saldo_pre = get_balance()
            if saldo_pre is None or min(saldo_pre, CAPITAL_MAX_BOT) < RISCO_USDC * 3:
                print(f"[{hora}] Saldo insuficiente: {saldo_pre}")
                continue

            # ── Limpa pending_sync antigos (>10 min) ─────────────────────
            agora = time.time()
            for sym in list(mem.get("pending_sync", {}).keys()):
                if agora - mem["pending_sync"][sym] > 600:
                    mem["pending_sync"].pop(sym)
                    save_memory(mem)

            # ── Scan dos pares ────────────────────────────────────────────
            for symbol in SYMBOLS:
                if symbol in posicoes_reais:
                    continue

                klines = get_klines(symbol)
                if not klines or len(klines) < LOOKBACK // 2:
                    continue

                closes         = [float(k[4]) for k in klines]
                highs          = [float(k[2]) for k in klines]
                lows           = [float(k[3]) for k in klines]
                volumes        = [float(k[5]) for k in klines]
                taker_buy_vols = [float(k[9]) for k in klines]

                atr_val = atr(highs, lows, closes)
                vwap    = get_daily_vwap(klines)
                mode    = detect_market_mode(closes, atr_val)

                if mode != "TRENDING":
                    print(f"[{hora}] {symbol} {mode}")
                    continue

                direction, score, detalhe = signal_trending(closes, highs, lows, volumes, symbol)
                print(f"[{hora}] {symbol} {mode} {detalhe}")

                if not direction:
                    continue

                if direction == "LONG" and score < SCORE_LONG_MIN:
                    print(f"[{hora}] {symbol} LONG score {score} < {SCORE_LONG_MIN} — skip")
                    continue

                # BTC crash lockout: não abre LONGs durante 1h após crash
                if direction == "LONG" and time.time() < mem.get("btc_crash_lockout_until", 0):
                    mins_lock = int((mem["btc_crash_lockout_until"] - time.time()) / 60)
                    print(f"[{hora}] {symbol} BTC_CRASH_LOCKOUT — LONG bloqueado {mins_lock}min")
                    continue

                # Veto por símbolo
                vetado, motivo_veto = verificar_veto_simbolo(symbol, mem)
                if vetado:
                    print(f"[{hora}] {symbol} VETO_SIMBOLO {motivo_veto}")
                    continue

                # Filtro VWAP diário
                if vwap is not None:
                    price_now = closes[-1]
                    if direction == "LONG"  and price_now < vwap:
                        print(f"[{hora}] {symbol} VETO_VWAP LONG abaixo {vwap:.4f}")
                        continue
                    if direction == "SHORT" and price_now > vwap:
                        print(f"[{hora}] {symbol} VETO_VWAP SHORT acima {vwap:.4f}")
                        continue

                # Tecto direcional
                longs_reais  = [s for s, p in posicoes_reais.items() if p["side"] == "LONG"]
                shorts_reais = [s for s, p in posicoes_reais.items() if p["side"] == "SHORT"]
                longs_alt    = [s for s in longs_reais  if s not in BTC_SYMBOLS]
                shorts_alt   = [s for s in shorts_reais if s not in BTC_SYMBOLS]

                if direction == "LONG":
                    if symbol in BTC_SYMBOLS and any(s in BTC_SYMBOLS for s in longs_reais):
                        print(f"[{hora}] {symbol} TECTO_DIR BTC LONG")
                        continue
                    if symbol not in BTC_SYMBOLS and len(longs_alt) >= MAX_LONGS_ALT:
                        print(f"[{hora}] {symbol} TECTO_DIR {len(longs_alt)}/{MAX_LONGS_ALT} LONGs")
                        continue
                if direction == "SHORT":
                    if symbol in BTC_SYMBOLS and any(s in BTC_SYMBOLS for s in shorts_reais):
                        print(f"[{hora}] {symbol} TECTO_DIR BTC SHORT")
                        continue
                    if symbol not in BTC_SYMBOLS and len(shorts_alt) >= MAX_SHORTS_ALT:
                        print(f"[{hora}] {symbol} TECTO_DIR {len(shorts_alt)}/{MAX_SHORTS_ALT} SHORTs")
                        continue

                # Correlação com posições abertas
                if posicoes_reais:
                    corr = calc_correlation(symbol, posicoes_reais)
                    if corr > 0.75:
                        print(f"[{hora}] {symbol} CORR {corr:.2f} — skip")
                        continue

                abrir_trade(
                    symbol, direction, closes, highs, lows,
                    atr_val, mode, detalhe, mem, score,
                    volumes=volumes,
                    taker_buy_vols=taker_buy_vols,
                    klines=klines
                )
                mem = load_memory()
                time.sleep(2)
                if len(mem.get("trades_abertos", {})) >= MAX_TRADES_ABERTOS:
                    print(f"[{hora}] Limite {MAX_TRADES_ABERTOS} trades — scan parado")
                    break
                # Máx 1 nova posição por ciclo de scan — evita abrir 5 posições correlacionadas ao mesmo tempo
                if len(mem.get("trades_abertos", {})) > len(posicoes_reais):
                    print(f"[{hora}] 1 trade aberto neste ciclo — próximo scan em 5min")
                    break

        except KeyboardInterrupt:
            tg("⛔ Claw Agent v8.0 parado manualmente.")
            print("\n[v8.0] A parar...")
            print_full_report()
            break
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[ERRO GERAL] {e}\n{tb}")
            tb_short = "\n".join(tb.strip().splitlines()[-6:])
            tg(f"⚠️ Claw Agent v8.0 erro: {e}\n<pre>{tb_short}</pre>")

        time.sleep(CHECK_POSICOES_FAST if mem.get("trades_abertos") else CHECK_POSICOES)


if __name__ == "__main__":
    run()
