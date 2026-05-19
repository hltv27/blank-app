"""
Claw Agent v8.0 — Execução de trades e gestão de posições
Mesma lógica da v7.1 + logging SQLite completo.
"""
import time
import requests
from config import (
    BASE_URL, CAPITAL_MAX_BOT, RISCO_USDC, ALAVANCAGEM,
    SYMBOL_PRECISION, STOP_RETRY_MAX, EMERGENCY_ROI_CUT,
    PARTIAL_TP_RATIO, PARTIAL_TP_QTY, PARTIAL_TP2_RATIO, PARTIAL_TP2_QTY,
    BREAKEVEN_OFFSET, MARGIN_RATIO_MAX, MAX_DRAWDOWN_PCT,
    MAX_MARGEM_TRADE, BTC_CRASH_PCT, CORR_MAX
)
from exchange import (
    tg, get_balance, get_positions, get_margin_ratio, get_price,
    set_leverage, place_order, place_stop_market, place_trailing_stop,
    place_take_profit, close_position, cancel_order
)
from indicators import atr, adx
from strategy import calc_sl_tp, calc_qty
from filters import (
    macro_event_proximo, volatility_regime_ok, spread_ok,
    market_conditions_ok, htf_4h_ok, htf_1h_ok, fear_greed_ok,
    bb_squeeze_ok, cvd_ok, obi_ok, vwap_ok,
    liquidity_sweep_detectado, btc_crash_detectado, calc_correlation
)
from risk import equity_scale_factor, atualizar_stats_simbolo
from storage import (
    save_memory, load_memory,
    open_position as db_open_position,
    close_position_db, update_position_partial_tp,
    log_state_transition, log_risk_event, log_equity_snapshot
)


def abrir_trade(symbol: str, direction: str, closes: list, highs: list,
                lows: list, atr_val: float, mode: str, detalhe: str,
                mem: dict, score: int = 0, volumes: list = None,
                taker_buy_vols: list = None, klines: list = None):

    price = closes[-1]

    # ── Filtros globais ──────────────────────────────────────────────────
    if macro_event_proximo():
        print(f"[AVISO] {symbol}: evento macro próximo — sem entrada")
        return

    if not volatility_regime_ok(symbol, closes, highs, lows, direction, price):
        tg(f"⚡ <b>REGIME VIOLENTO</b> — {symbol}\nATR extremo. Sem entrada.")
        return

    if not spread_ok(symbol, direction, price):
        return

    if not market_conditions_ok(symbol, direction, price):
        print(f"[AVISO] {symbol}: condições de mercado desfavoráveis para {direction}")
        return

    # ── HTF multi-timeframe (4H → 1H → 5min) ───────────────────────────
    if not htf_4h_ok(symbol, direction, price):
        return

    if not htf_1h_ok(symbol, direction, price):
        print(f"[AVISO] {symbol}: HTF 1H contra {direction} — veto")
        return

    # ── Supertrend ───────────────────────────────────────────────────────
    from indicators import supertrend
    st_bull = supertrend(highs, lows, closes)
    if direction == "LONG"  and st_bull is False:
        print(f"[AVISO] {symbol}: Supertrend bearish — LONG vetado")
        return
    if direction == "SHORT" and st_bull is True:
        print(f"[AVISO] {symbol}: Supertrend bullish — SHORT vetado")
        return

    # ── Fear & Greed ─────────────────────────────────────────────────────
    if not fear_greed_ok(symbol, direction, price):
        return

    # ── BB Squeeze ───────────────────────────────────────────────────────
    if not bb_squeeze_ok(symbol, direction, closes, volumes, price):
        return

    # ── CVD ──────────────────────────────────────────────────────────────
    if not cvd_ok(symbol, direction, closes, volumes, taker_buy_vols, price):
        return

    # ── OBI ──────────────────────────────────────────────────────────────
    if not obi_ok(symbol, direction, price):
        return

    # ── VWAP ±2σ ─────────────────────────────────────────────────────────
    if klines and not vwap_ok(symbol, direction, closes, klines, price):
        return

    # ── Liquidity Sweep (confirmação — não bloqueia) ─────────────────────
    if volumes and taker_buy_vols:
        if liquidity_sweep_detectado(closes, highs, lows, volumes, taker_buy_vols, direction):
            detalhe += " | LIQ_SWEEP✓"
            print(f"[LSweep] {symbol}: liquidity sweep confirmado")

    # ── Saldo e capital ──────────────────────────────────────────────────
    saldo = get_balance()
    if saldo is None:
        return
    capital_bot = min(saldo, CAPITAL_MAX_BOT)
    if capital_bot < RISCO_USDC * 3:
        return

    adx_val = adx(highs, lows, closes)
    sl, tp  = calc_sl_tp(direction, price, atr_val, mode, score, adx_val)
    qty     = calc_qty(price, sl, symbol)
    if qty <= 0:
        return

    decimals = SYMBOL_PRECISION.get(symbol, 4)

    # ── Equity Curve Feedback ────────────────────────────────────────────
    scale = equity_scale_factor(mem)
    if scale < 1.0:
        qty = round(qty * scale, decimals)
        if qty <= 0:
            return

    max_qty = round((capital_bot * ALAVANCAGEM * 0.8) / price, decimals)
    if max_qty <= 0:
        print(f"[AVISO] {symbol}: capital insuficiente")
        return
    if qty > max_qty:
        print(f"[AVISO] {symbol}: qty {qty} → {max_qty} (capital limitado)")
        qty = max_qty

    # Cap de margem: máx MAX_MARGEM_TRADE do capital por posição
    max_qty_margem = round((capital_bot * MAX_MARGEM_TRADE * ALAVANCAGEM) / price, decimals)
    if max_qty_margem <= 0:
        print(f"[AVISO] {symbol}: capital insuficiente para margem mínima")
        return
    if qty > max_qty_margem:
        margem_orig = round(qty * price / ALAVANCAGEM, 2)
        print(f"[AVISO] {symbol}: margem {margem_orig} USDC → cap {round(capital_bot * MAX_MARGEM_TRADE, 1)} USDC ({MAX_MARGEM_TRADE*100:.0f}%)")
        qty = max_qty_margem

    set_leverage(symbol)
    side  = "BUY" if direction == "LONG" else "SELL"
    order = place_order(symbol, side, qty)

    if order and "orderId" in order:
        fill_price = float(order.get("avgPrice") or 0) or price
        sl, tp     = calc_sl_tp(direction, fill_price, atr_val, mode, score, adx_val)
        sl_dist    = abs(fill_price - sl)
        tp_dist    = abs(tp - fill_price)
        rr_actual  = round(tp_dist / sl_dist, 1) if sl_dist > 0 else 2.0

        # Confirma posição na Binance
        time.sleep(1)
        pos_verif = get_positions()
        if pos_verif is not None and symbol not in pos_verif:
            time.sleep(3)
            pos_verif = get_positions()
            if pos_verif is not None and symbol not in pos_verif:
                print(f"[ERRO] {symbol}: posição não confirmada após retry")
                return

        # STOP_MARKET fixo na SL — dispara instantaneamente na exchange
        # (trailing stop entra apenas após TP1, quando já estamos em lucro)
        stop_side = "SELL" if direction == "LONG" else "BUY"
        stop_id   = None
        for tentativa in range(1, STOP_RETRY_MAX + 1):
            stop_id = place_stop_market(symbol, stop_side, sl, qty)
            if stop_id:
                break
            print(f"[AVISO] {symbol}: stop falhou (tentativa {tentativa}/{STOP_RETRY_MAX})")
            time.sleep(2)
        if not stop_id:
            tg(f"🚨 <b>STOP NÃO COLOCADO</b> — {symbol}\nFechando posição por segurança.")
            close_position(symbol, qty, direction)
            return

        # TP como ordem real
        tp_side      = "SELL" if direction == "LONG" else "BUY"
        tp_order_id  = place_take_profit(symbol, tp_side, tp)

        # Regista no SQLite
        try:
            db_open_position(symbol, direction, fill_price, sl, tp, qty,
                             mode, stop_id, tp_order_id)
        except Exception as _db_e:
            print(f"[AVISO] db_open_position falhou: {_db_e}")

        # Regista na memória
        mem.setdefault("trades_abertos", {})[symbol] = {
            "direction":     direction,
            "entry":         fill_price,
            "sl":            sl,
            "tp":            tp,
            "qty":           qty,
            "qty_inicial":   qty,
            "mode":          mode,
            "opened_at":     time.time(),
            "stop_order_id": stop_id,
            "tp_order_id":   tp_order_id,
        }
        mem["total_trades"] = mem.get("total_trades", 0) + 1
        save_memory(mem)

        dir_icon = "🟢 LONG" if direction == "LONG" else "🔴 SHORT"
        stop_txt = f"🛑 SL fixo @ {sl:.4f} (#{stop_id})"
        tp_txt   = f"TP#{tp_order_id}" if tp_order_id else "TP em memória"
        rr_icon  = f"RR {rr_actual}:1" + (" 🚀" if rr_actual >= 3 else "")
        tg(
            f"📈 <b>{dir_icon}</b> — {symbol}\n"
            f"Entrada: {fill_price:.4f}\n"
            f"SL: {sl:.4f} | TP: {tp:.4f} | {rr_icon}\n"
            f"Qty: {qty:.4f} | ADX: {adx_val:.0f}\n"
            f"🔒 {stop_txt} | 🎯 {tp_txt}\n"
            f"Detalhe: {detalhe}"
        )
    else:
        erro = order.get("msg", str(order)[:120]) if isinstance(order, dict) else "sem resposta"
        print(f"[ERRO] Ordem {symbol} resposta completa: {order}")
        tg(f"⚠️ <b>Ordem falhou</b> — {symbol}\nDirecção: {direction} | Erro: {erro}")


def gerir_posicoes(mem: dict):
    """Verifica posições abertas — SL/TP, partial TP, emergency cut."""

    # BTC crash guard
    if btc_crash_detectado():
        posicoes_crash = get_positions() or {}
        fechados = []
        for sym, pos in posicoes_crash.items():
            if pos["side"] == "LONG" and sym != "BTCUSDC":
                close_position(sym, pos["qty"], "LONG")
                mem.get("trades_abertos", {}).pop(sym, None)
                close_position_db(sym, "BTC_CRASH", pos["pnl"], 0)
                fechados.append(sym)
        if fechados:
            save_memory(mem)
            log_risk_event("BTC_CRASH_GUARD", details=f"fechados={fechados}")
            tg(
                f"⚡ <b>BTC CRASH GUARD</b>\n"
                f"Longs fechados: {', '.join(fechados)}"
            )

    # ── Guarda de 25% — fecha tudo se perdas abertas > 25% do saldo ────
    saldo_atual = get_balance()
    if saldo_atual and saldo_atual > 0:
        posicoes_dd = get_positions() or {}
        pnl_total_aberto = sum(pos.get("pnl", 0) for pos in posicoes_dd.values())
        limite_drawdown = saldo_atual * MAX_DRAWDOWN_PCT
        if pnl_total_aberto < -limite_drawdown:
            fechados_dd = []
            for sym, pos in posicoes_dd.items():
                close_position(sym, pos["qty"], pos["side"])
                close_position_db(sym, "DRAWDOWN_25PCT", pos["pnl"], 0)
                mem.get("trades_abertos", {}).pop(sym, None)
                fechados_dd.append(sym)
            if fechados_dd:
                save_memory(mem)
                log_risk_event("DRAWDOWN_25PCT",
                               details=f"pnl={pnl_total_aberto:.2f} limite={-limite_drawdown:.2f}")
                tg(
                    f"🛡 <b>GUARDA 25% ACTIVADO</b>\n"
                    f"Perdas abertas: {pnl_total_aberto:.2f} USDC\n"
                    f"Limite: -{limite_drawdown:.0f} USDC ({MAX_DRAWDOWN_PCT*100:.0f}% de {saldo_atual:.0f})\n"
                    f"Fechados: {', '.join(fechados_dd)}"
                )
            return

    # Salvaguarda de margem
    ratio = get_margin_ratio()
    if ratio is not None and ratio >= MARGIN_RATIO_MAX:
        posicoes_todas = get_positions() or {}
        for sym, pos in posicoes_todas.items():
            close_position(sym, pos["qty"], pos["side"])
            close_position_db(sym, "MARGIN_CRITICAL", pos["pnl"], 0)
            mem.get("trades_abertos", {}).pop(sym, None)
        save_memory(mem)
        log_risk_event("MARGIN_CRITICAL", details=f"ratio={ratio:.1f}%")
        tg(
            f"🚨 <b>MARGEM CRÍTICA — TUDO FECHADO</b>\n"
            f"Rácio: {ratio:.1f}% (limite: {MARGIN_RATIO_MAX:.0f}%)"
        )
        return

    posicoes_binance = get_positions()
    if posicoes_binance is None:
        print("[AVISO] gerir_posicoes: API falhou")
        return
    trades_abertos = mem.get("trades_abertos", {})

    for symbol, trade in list(trades_abertos.items()):
        if symbol not in posicoes_binance:
            # Posição fechou externamente (trailing stop Binance)
            pnl_ext   = trade.get("pnl_ultimo", None)
            side_ext  = trade.get("direction", "LONG")
            entry_ext = trade.get("entry", 0)
            sl_ext    = trade.get("sl", 0)
            qty_ext   = abs(trade.get("qty", 0))
            if pnl_ext is None:
                pnl_ext = -abs(entry_ext - sl_ext) * qty_ext if sl_ext > 0 else 0.0
            won = pnl_ext > 0
            _registar_fecho(symbol, side_ext, entry_ext, sl_ext,
                            trade.get("tp", 0), qty_ext, pnl_ext,
                            "ALGO_STOP", won, mem)
            continue

        pos   = posicoes_binance[symbol]
        sl    = trade.get("sl", 0)
        tp    = trade.get("tp", 0)
        side  = trade.get("direction", "LONG")
        price = get_price(symbol)
        if price is None:
            continue

        mem["trades_abertos"][symbol]["pnl_ultimo"] = pos["pnl"]

        entry    = trade.get("entry", 0)
        qty      = abs(pos["qty"])
        qty_base = trade.get("qty_inicial", qty)
        margin   = (qty_base * entry) / ALAVANCAGEM if entry > 0 and qty_base > 0 else 0
        roi      = (pos["pnl"] / margin * 100) if margin > 0 else 0

        opened_at = trade.get("opened_at")
        elapsed   = (time.time() - opened_at) if opened_at else 1800

        # Saída por tempo + ROI ≥ 5%
        if elapsed >= 30 * 60 and roi >= 5.0:
            close_position(symbol, pos["qty"], side)
            _registar_fecho(symbol, side, entry, sl, tp, qty,
                            pos["pnl"], "TIME_TP", True, mem)
            tg(
                f"⏱️ <b>TEMPO+LUCRO</b> — {symbol}\n"
                f"ROI: {roi:.1f}% | PnL: {pos['pnl']:+.2f} | {int(elapsed/60)}min"
            )
            continue

        # ── TP1: fecha 33% a 2R, move stop para breakeven ────────────────
        entry_trade = trade.get("entry", 0)
        if sl > 0 and tp > 0 and not trade.get("partial_tp_done") and entry_trade > 0:
            if side == "LONG":
                tp1_level   = entry_trade + (tp - entry_trade) * PARTIAL_TP_RATIO
                hit_tp1     = price >= tp1_level
            else:
                tp1_level   = entry_trade - (entry_trade - tp) * PARTIAL_TP_RATIO
                hit_tp1     = price <= tp1_level
            if hit_tp1:
                decimals_p  = SYMBOL_PRECISION.get(symbol, 4)
                qty_total   = abs(pos["qty"])
                qty_tp1     = round(qty_total * PARTIAL_TP_QTY, decimals_p)
                if qty_tp1 > 0:
                    close_position(symbol, qty_tp1, side)
                    qty_restante = round(qty_total - qty_tp1, decimals_p)
                    # Breakeven stop: entrada + 0.2% (cobre fees)
                    if side == "LONG":
                        be_price = round(entry_trade * (1 + BREAKEVEN_OFFSET), 8)
                    else:
                        be_price = round(entry_trade * (1 - BREAKEVEN_OFFSET), 8)
                    # Cancela trailing stop antigo e coloca stop de breakeven
                    old_stop = trade.get("stop_order_id")
                    if old_stop:
                        try:
                            cancel_order(symbol, old_stop)
                        except Exception:
                            pass
                    be_side     = "SELL" if side == "LONG" else "BUY"
                    new_stop_id = place_trailing_stop(symbol, be_side, 0.5, be_price)
                    mem["trades_abertos"][symbol]["partial_tp_done"] = True
                    mem["trades_abertos"][symbol]["qty"]             = qty_restante
                    mem["trades_abertos"][symbol]["sl"]              = be_price
                    mem["trades_abertos"][symbol]["stop_order_id"]   = new_stop_id
                    update_position_partial_tp(symbol, qty_restante)
                    pnl_tp1 = round(abs(tp1_level - entry_trade) * qty_tp1, 2)
                    log_state_transition(symbol, "OPEN", "TP1", "PRICE_HIT",
                                        f"qty={qty_tp1} pnl={pnl_tp1:.2f} be={be_price:.4f}")
                    tg(
                        f"📊 <b>TP1 — 33% fechado</b> — {symbol}\n"
                        f"Preço: {price:.4f} | +{pnl_tp1:.2f} USDC\n"
                        f"🔒 Stop movido para breakeven: {be_price:.4f}"
                    )
                    save_memory(mem)

        # ── TP2: fecha mais 33% a 3R, move stop para +1R ─────────────────
        if sl > 0 and tp > 0 and trade.get("partial_tp_done") and \
                not trade.get("partial_tp2_done") and entry_trade > 0:
            if side == "LONG":
                tp2_level = entry_trade + (tp - entry_trade) * PARTIAL_TP2_RATIO
                hit_tp2   = price >= tp2_level
            else:
                tp2_level = entry_trade - (entry_trade - tp) * PARTIAL_TP2_RATIO
                hit_tp2   = price <= tp2_level
            if hit_tp2:
                decimals_p   = SYMBOL_PRECISION.get(symbol, 4)
                qty_total    = abs(pos["qty"])
                qty_inicial  = trade.get("qty_inicial", qty_total)
                qty_tp2      = round(qty_inicial * PARTIAL_TP2_QTY, decimals_p)
                qty_tp2      = min(qty_tp2, qty_total)
                if qty_tp2 > 0:
                    close_position(symbol, qty_tp2, side)
                    qty_restante = round(qty_total - qty_tp2, decimals_p)
                    # Stop para +1R (lock de lucro no runner)
                    sl_dist = abs(entry_trade - trade.get("sl", entry_trade))
                    if sl_dist == 0:
                        sl_dist = abs(entry_trade - tp) / 3.0
                    if side == "LONG":
                        lock_price = round(entry_trade + sl_dist, 8)
                    else:
                        lock_price = round(entry_trade - sl_dist, 8)
                    old_stop2 = trade.get("stop_order_id")
                    if old_stop2:
                        try:
                            cancel_order(symbol, old_stop2)
                        except Exception:
                            pass
                    be_side2     = "SELL" if side == "LONG" else "BUY"
                    new_stop2_id = place_trailing_stop(symbol, be_side2, 0.5, lock_price)
                    mem["trades_abertos"][symbol]["partial_tp2_done"] = True
                    mem["trades_abertos"][symbol]["qty"]              = qty_restante
                    mem["trades_abertos"][symbol]["sl"]               = lock_price
                    mem["trades_abertos"][symbol]["stop_order_id"]    = new_stop2_id
                    update_position_partial_tp(symbol, qty_restante)
                    pnl_tp2 = round(abs(tp2_level - entry_trade) * qty_tp2, 2)
                    log_state_transition(symbol, "OPEN", "TP2", "PRICE_HIT",
                                        f"qty={qty_tp2} pnl={pnl_tp2:.2f} lock={lock_price:.4f}")
                    tg(
                        f"🎯 <b>TP2 — 33% fechado</b> — {symbol}\n"
                        f"Preço: {price:.4f} | +{pnl_tp2:.2f} USDC\n"
                        f"🔒 Stop em +1R: {lock_price:.4f} | Runner livre"
                    )
                    save_memory(mem)

        # Emergency ROI cut
        if roi <= EMERGENCY_ROI_CUT:
            close_position(symbol, pos["qty"], side)
            log_risk_event("EMERGENCY_CUT", symbol=symbol,
                           details=f"roi={roi:.1f}% pnl={pos['pnl']:.2f}")
            _registar_fecho(symbol, side, entry, sl, tp, qty,
                            pos["pnl"], "EMERGENCY_SL", False, mem)
            tg(
                f"🛑 <b>CORTE EMERGÊNCIA</b> — {symbol}\n"
                f"ROI: {roi:.1f}% | PnL: {pos['pnl']:+.2f}"
            )
            continue

        if sl <= 0 or tp <= 0:
            continue

        hit_sl = (side == "LONG" and price <= sl) or (side == "SHORT" and price >= sl)
        hit_tp = (side == "LONG" and price >= tp) or (side == "SHORT" and price <= tp)

        if hit_sl or hit_tp:
            close_position(symbol, pos["qty"], side)
            reason = "TP" if hit_tp else "SL"
            _registar_fecho(symbol, side, entry, sl, tp, qty,
                            pos["pnl"], reason, hit_tp, mem)
            if hit_tp:
                tg(
                    f"✅ <b>TP ATINGIDO</b> — {symbol}\n"
                    f"Direcção: {side} | Entrada: {entry:.4f}\n"
                    f"PnL: {pos['pnl']:+.2f} USDC"
                )
            else:
                tg(
                    f"🔴 <b>SL ATINGIDO</b> — {symbol}\n"
                    f"Direcção: {side} | Entrada: {entry:.4f}\n"
                    f"PnL: {pos['pnl']:+.2f} USDC\n"
                    f"Perdas hoje: {mem.get('loss_dia', 0):.2f} USDC"
                )

    save_memory(mem)

    # Snapshot de equity a cada ciclo com posições abertas
    try:
        bal   = get_balance()
        ratio = get_margin_ratio()
        if bal is not None:
            daily_pnl = sum(
                t.get("pnl_ultimo", 0)
                for t in mem.get("trades_abertos", {}).values()
            )
            log_equity_snapshot(bal, ratio or 0, len(posicoes_binance), daily_pnl)
    except Exception:
        pass


def _registar_fecho(symbol: str, side: str, entry: float, sl: float,
                    tp: float, qty: float, pnl: float, reason: str,
                    won: bool, mem: dict):
    """Centraliza o registo de fecho de posição."""
    from risk import atualizar_stats_simbolo
    mem["trades_abertos"].pop(symbol, None)
    if won:
        mem["wins"]            = mem.get("wins", 0) + 1
        mem["perdas_seguidas"] = 0
    else:
        mem["losses"]          = mem.get("losses", 0) + 1
        mem["perdas_seguidas"] = mem.get("perdas_seguidas", 0) + 1
        mem["loss_dia"]        = mem.get("loss_dia", 0) + abs(pnl)

    atualizar_stats_simbolo(symbol, won, pnl, mem)
    close_position_db(symbol, reason, pnl, 0)
    save_memory(mem)
