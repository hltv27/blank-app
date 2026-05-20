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

import time
from datetime import datetime, timezone
import config
from config import (
    BTC_SYMBOLS, MAX_TRADES_ABERTOS,
    MAX_LONGS_ALT, MAX_SHORTS_ALT, LOOKBACK,
    CHECK_POSICOES_FAST, CHECK_POSICOES, CAPITAL_MAX_BOT, RISCO_USDC,
    ALAVANCAGEM, TOP_N_FUTURES
)
from exchange import tg, get_klines, get_positions, get_balance, get_price, sync_time, get_public_ip, get_top_futures_symbols
from indicators import atr, get_daily_vwap
from strategy import detect_market_mode, signal_trending
from filters import calc_correlation
from risk import em_sessao, circuit_breaker_activo, verificar_veto_simbolo
from execution import abrir_trade, gerir_posicoes
from storage import init_db, load_memory, save_memory, log_state_transition
from analytics import print_full_report


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
    dinamicos, precisoes = get_top_futures_symbols(TOP_N_FUTURES)
    if dinamicos:
        config.SYMBOLS = dinamicos
    if precisoes:
        config.SYMBOL_PRECISION.update(precisoes)
    SYMBOLS = config.SYMBOLS

    ultima_actualizacao_symbols = time.time()

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

    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            hora    = now_utc.strftime("%H:%M")
            mem     = load_memory()

            if now_utc.hour != ultima_sync_hora:
                sync_time()
                ultima_sync_hora = now_utc.hour

            # Actualiza lista de pares a cada 24h
            if time.time() - ultima_actualizacao_symbols > 86400:
                novos, precisoes_novas = get_top_futures_symbols(TOP_N_FUTURES)
                if novos:
                    config.SYMBOLS = novos
                    SYMBOLS = config.SYMBOLS
                if precisoes_novas:
                    config.SYMBOL_PRECISION.update(precisoes_novas)
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

            # ── Gestão de posições abertas ────────────────────────────────
            tem_posicoes = bool(mem.get("trades_abertos"))
            if tem_posicoes:
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
                if symbol in SYMBOLS and symbol not in mem.get("trades_abertos", {}):
                    # Posição órfã do bot — sincroniza e coloca stop com reduceOnly (nunca closePosition)
                    kl_sync = get_klines(symbol)
                    sync_stop_id = None
                    sync_sl = 0.0
                    if kl_sync and len(kl_sync) > 14:
                        from indicators import atr as calc_atr
                        from exchange import place_stop_market as _psm
                        h_s = [float(k[2]) for k in kl_sync]
                        l_s = [float(k[3]) for k in kl_sync]
                        c_s = [float(k[4]) for k in kl_sync]
                        atr_s   = calc_atr(h_s, l_s, c_s)
                        entry_s = pos["entry"] if pos["entry"] > 0 else c_s[-1]
                        qty_s   = abs(pos["qty"])
                        stop_side_s = "SELL" if pos["side"] == "LONG" else "BUY"
                        if pos["side"] == "LONG":
                            sync_sl = round(entry_s - atr_s * 1.5, 8)
                        else:
                            sync_sl = round(entry_s + atr_s * 1.5, 8)
                        # reduceOnly=true — nunca conflitua com TP orders existentes
                        sync_stop_id = _psm(symbol, stop_side_s, sync_sl, qty_s)

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
                    stop_txt = f"Stop#{sync_stop_id}" if sync_stop_id else "⚠️ stop falhou"
                    print(f"[{hora}] {symbol} sincronizado da Binance")
                    tg(
                        f"🔄 <b>{dir_icon}</b> — {symbol} (sincronizada)\n"
                        f"Entrada: {pos['entry']:.4f} | 🔒 {stop_txt}"
                    )

                elif symbol not in SYMBOLS and symbol not in mem.get("trades_abertos", {}):
                    # Posição manual fora da lista do bot — monitorizar sem gerir
                    externas = mem.setdefault("posicoes_externas", {})
                    if symbol not in externas:
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
                        print(f"[{hora}] EXTERNA detectada: {symbol} {pos['side']}")
                        tg(
                            f"👁 <b>Posição externa detectada</b>\n"
                            f"{dir_icon} <b>{symbol}</b> (fora da lista do bot)\n"
                            f"Entrada: <code>{pos['entry']:.6g}</code> | "
                            f"Qty: {abs(pos['qty']):.4g} | "
                            f"Notional: ~{notional:.1f} USDC\n"
                            f"<i>Monitorizada — não gerida pelo bot</i>"
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

                direction, score, detalhe = signal_trending(closes, highs, lows, volumes)
                print(f"[{hora}] {symbol} {mode} {detalhe}")

                if not direction:
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

        except KeyboardInterrupt:
            tg("⛔ Claw Agent v8.0 parado manualmente.")
            print("\n[v8.0] A parar...")
            print_full_report()
            break
        except Exception as e:
            print(f"[ERRO GERAL] {e}")
            tg(f"⚠️ Claw Agent v8.0 erro: {e}")

        time.sleep(CHECK_POSICOES_FAST if mem.get("trades_abertos") else CHECK_POSICOES)


if __name__ == "__main__":
    run()
