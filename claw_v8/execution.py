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
    MAX_MARGEM_TRADE, BTC_CRASH_PCT, CORR_MAX,
    BTC_SYMBOLS, ATR_VOL_SCALE_PCT, TRAILING_CB_BTC, TRAILING_CB_ALT,
    ROI_TP_IMEDIATO, SCORE_FORTE, SCORE_ALERTA, EMERGENCY_PNL_CUT,
    LIQUIDATION_GUARD_PCT, LIQUIDATION_WARN1_PCT, LIQUIDATION_WARN2_PCT, LIQUIDATION_WARN3_PCT,
    TRAILING_LOCK_USDC, PEAK_PROFIT_MIN_USDC, PEAK_DRAWDOWN_PCT,
    PROFIT_LOCK_USDC, PROFIT_LOCK_STEP, PRICE_PRECISION
)
import math
from exchange import (
    tg, get_balance, get_positions, get_margin_ratio, get_margin_ratio_global, get_price,
    get_klines,
    set_leverage, place_order, place_stop_market, place_trailing_stop,
    place_take_profit, close_position, cancel_order, cancel_algo_order,
    get_open_algo_orders
)
from indicators import atr, adx
from strategy import calc_sl_tp, calc_qty, signal_trending

# Timestamp do último check de reversão de sinal por símbolo (rate-limit 60s)
_signal_inv_ts: dict = {}
_peak_drawdown_ts: dict = {}


def _fechar_com_retry(symbol: str, qty: float, side: str, tentativas: int = 3) -> bool:
    """Tenta fechar posição na exchange. Retorna True se bem-sucedido."""
    for i in range(tentativas):
        result = close_position(symbol, qty, side)
        if result is not None:
            return True
        if i < tentativas - 1:
            time.sleep(1.5)
    return False

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

    # Reduz qty proporcionalmente quando o mercado está muito volátil (ATR > 0.3%)
    atr_pct = atr_val / price if price > 0 else 0
    if atr_pct > ATR_VOL_SCALE_PCT:
        vol_scale = round(ATR_VOL_SCALE_PCT / atr_pct, 2)
        qty_antes = qty
        qty = round(qty * vol_scale, decimals)
        if qty <= 0:
            print(f"[VOL_SCALE] {symbol}: qty zerada após escala — sem entrada")
            return
        print(f"[VOL_SCALE] {symbol}: ATR {atr_pct*100:.2f}% → qty {qty_antes} → {qty} (×{vol_scale:.2f})")

    set_leverage(symbol)
    side  = "BUY" if direction == "LONG" else "SELL"

    # Bloqueia se já existe posição neste símbolo (bot ou manual) — nunca adoptar posição do utilizador
    if symbol in mem.get("trades_abertos", {}) or symbol in mem.get("posicoes_externas", {}):
        print(f"[VETO] {symbol}: posição já existe — sem entrada")
        return

    # Marca o símbolo como "ordem em curso" — sync usa isto para distinguir bot de manual
    mem.setdefault("pending_sync", {})[symbol] = time.time()
    save_memory(mem)

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

        # STOP_MARKET inicial — closePosition=true (compatível com EU/BNFCR)
        # Se falhar, mantém a posição protegida por software SL (ciclo de 10s)
        stop_side = "SELL" if direction == "LONG" else "BUY"
        stop_id   = None
        for tentativa in range(1, STOP_RETRY_MAX + 1):
            stop_id = place_stop_market(symbol, stop_side, sl, qty)
            if stop_id:
                break
            print(f"[AVISO] {symbol}: stop falhou (tentativa {tentativa}/{STOP_RETRY_MAX})")
            time.sleep(2)
        if not stop_id:
            # Stop falhou após todas as tentativas — fechar posição e abortar trade
            print(f"[ERRO] {symbol}: stop falhou {STOP_RETRY_MAX}x — a fechar posição por segurança")
            close_position(symbol, qty, direction)
            mem.get("pending_sync", {}).pop(symbol, None)
            save_memory(mem)
            tg(
                f"🚨 <b>{symbol} — TRADE ABORTADO</b>\n"
                f"Stop na exchange falhou após {STOP_RETRY_MAX} tentativas.\n"
                f"Posição fechada por segurança."
            )
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
        stop_txt = f"🛑 SL @ {sl:.4f} (#{stop_id})" if stop_id else f"🛑 SL @ {sl:.4f} (software)"
        tp_txt   = f"TP#{tp_order_id}" if tp_order_id else "TP em memória"
        rr_icon  = f"RR {rr_actual}:1" + (" 🚀" if rr_actual >= 3 else "")
        mem.get("pending_sync", {}).pop(symbol, None)
        save_memory(mem)
        tg(
            f"📈 <b>{dir_icon}</b> — {symbol}\n"
            f"Entrada: {fill_price:.4f}\n"
            f"SL: {sl:.4f} | TP: {tp:.4f} | {rr_icon}\n"
            f"Qty: {qty:.4f} | ADX: {adx_val:.0f}\n"
            f"🔒 {stop_txt} | 🎯 {tp_txt}\n"
            f"Detalhe: {detalhe}"
        )
    else:
        mem.get("pending_sync", {}).pop(symbol, None)
        save_memory(mem)
        erro = order.get("msg", str(order)[:120]) if isinstance(order, dict) else "sem resposta"
        print(f"[ERRO] Ordem {symbol} resposta completa: {order}")
        tg(f"⚠️ <b>Ordem falhou</b> — {symbol}\nDirecção: {direction} | Erro: {erro}")


def gerir_posicoes(mem: dict):
    """Verifica posições abertas — SL/TP, partial TP, emergency cut."""

    # BTC crash guard
    btc_crash_fired = False
    posicoes_all = None
    if btc_crash_detectado():
        btc_crash_fired = True
        posicoes_all   = get_positions() or {}
        trades_bot     = mem.get("trades_abertos", {})
        fechados = []
        for sym, pos in posicoes_all.items():
            if sym not in trades_bot:
                continue  # não toca em trades manuais
            if pos["side"] == "LONG" and sym != "BTCUSDC":
                close_position(sym, pos["qty"], "LONG")
                mem.get("trades_abertos", {}).pop(sym, None)
                close_position_db(sym, "BTC_CRASH", pos["pnl"], 0)
                fechados.append(sym)
        if fechados:
            mem["btc_crash_lockout_until"] = time.time() + 3600  # LONGs bloqueados 1h
            save_memory(mem)
            log_risk_event("BTC_CRASH_GUARD", details=f"fechados={fechados}")
            tg(
                f"⚡ <b>BTC CRASH GUARD</b>\n"
                f"Longs fechados: {', '.join(fechados)}"
            )

    # ── Guarda de 25% — só conta posições do bot, nunca fecha trades manuais
    saldo_atual = get_balance()
    if saldo_atual and saldo_atual > 0:
        if posicoes_all is None:
            posicoes_all = get_positions() or {}
        posicoes_dd  = posicoes_all
        trades_bot   = mem.get("trades_abertos", {})
        pnl_total_aberto = sum(
            pos.get("pnl", 0)
            for sym, pos in posicoes_dd.items()
            if sym in trades_bot
        )
        limite_drawdown = saldo_atual * MAX_DRAWDOWN_PCT
        if pnl_total_aberto < -limite_drawdown:
            fechados_dd = []
            for sym, pos in posicoes_dd.items():
                if sym not in trades_bot:
                    continue  # nunca fechar trades manuais
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

    # Salvaguarda de margem — só fecha posições do bot
    # Usa ratio global (USDT-M + USDC-M) para evitar falsos positivos quando há
    # posições USDT-M que inflam o maintMargin do asset BNFCR
    ratio = get_margin_ratio_global()
    if ratio is not None and ratio >= MARGIN_RATIO_MAX:
        if posicoes_all is None:
            posicoes_all = get_positions() or {}
        posicoes_todas = posicoes_all
        trades_bot     = mem.get("trades_abertos", {})
        for sym, pos in posicoes_todas.items():
            if sym not in trades_bot:
                continue  # não toca em trades manuais
            close_position(sym, pos["qty"], pos["side"])
            close_position_db(sym, "MARGIN_CRITICAL", pos["pnl"], 0)
            mem.get("trades_abertos", {}).pop(sym, None)
        save_memory(mem)
        log_risk_event("MARGIN_CRITICAL", details=f"ratio={ratio:.1f}%")
        agora_mc = time.time()
        if agora_mc - mem.get("margin_critica_ts", 0) > 300:
            mem["margin_critica_ts"] = agora_mc
            save_memory(mem)
            tg(
                f"🚨 <b>MARGEM CRÍTICA — TUDO FECHADO</b>\n"
                f"Rácio: {ratio:.1f}% (limite: {MARGIN_RATIO_MAX:.0f}%)"
            )
        return

    # ── Guard de liquidação global (USDT-M + USDC-M) ─────────────────────
    # Monitora a conta inteira. Se > LIQUIDATION_GUARD_PCT, fecha tudo a positivo.
    ratio_global = get_margin_ratio_global()
    if ratio_global is not None:
        agora_ts = time.time()
        ultimo_alerta = mem.get("liq_alerta_ts", 0)
        alerta_intervalo = 300  # no máximo 1 alerta por 5 minutos

        if ratio_global >= LIQUIDATION_WARN3_PCT and agora_ts - ultimo_alerta > alerta_intervalo:
            mem["liq_alerta_ts"] = agora_ts
            save_memory(mem)
            tg(f"🔴 <b>MARGEM CRÍTICA</b> — conta global: <b>{ratio_global:.1f}%</b>\nLiquidação iminente! Reduz posições manuais imediatamente.")
        elif ratio_global >= LIQUIDATION_WARN2_PCT and agora_ts - ultimo_alerta > alerta_intervalo:
            mem["liq_alerta_ts"] = agora_ts
            save_memory(mem)
            tg(f"🟠 <b>MARGEM ELEVADA</b> — conta global: <b>{ratio_global:.1f}%</b>\nRisco de liquidação — verifica posições manuais.")
        elif ratio_global >= LIQUIDATION_WARN1_PCT and agora_ts - ultimo_alerta > alerta_intervalo:
            mem["liq_alerta_ts"] = agora_ts
            save_memory(mem)
            tg(f"🟡 <b>MARGEM EM ATENÇÃO</b> — conta global: <b>{ratio_global:.1f}%</b>")

        if ratio_global >= LIQUIDATION_GUARD_PCT:
            # Exceção: fecha TODAS as posições a positivo (bot + manuais)
            # para libertar margem e evitar liquidação total da conta
            if posicoes_all is None:
                posicoes_all = get_positions() or {}
            fechados_liq = []
            for sym, pos in posicoes_all.items():
                if pos.get("pnl", 0) > 0:
                    close_position(sym, pos["qty"], pos["side"])
                    fechados_liq.append(f"{sym} +{pos['pnl']:.2f}")
                    if sym in mem.get("trades_abertos", {}):
                        t = mem["trades_abertos"][sym]
                        _registar_fecho(sym, t.get("direction", pos["side"]),
                                        t.get("entry", pos["entry"]), t.get("sl", 0),
                                        t.get("tp", 0), abs(pos["qty"]), pos["pnl"],
                                        "LIQ_GUARD", True, mem)
                    elif sym in mem.get("posicoes_externas", {}):
                        mem.get("posicoes_externas", {}).pop(sym, None)
                        save_memory(mem)
            if fechados_liq:
                log_risk_event("LIQ_GUARD_50PCT", details=f"ratio={ratio_global:.1f}% fechados={fechados_liq}")
                tg(
                    f"🛡 <b>GUARD LIQUIDAÇÃO {ratio_global:.1f}%</b>\n"
                    f"Fechadas posições a positivo (bot + manuais):\n"
                    + "\n".join(fechados_liq)
                )
            return

    if posicoes_all is None:
        posicoes_all = get_positions()
    posicoes_binance = posicoes_all
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

        # Regista o pico de PnL já atingido — usado pela protecção de recuo
        peak_pnl = trade.get("peak_pnl", pos["pnl"])
        if pos["pnl"] > peak_pnl:
            peak_pnl = pos["pnl"]
            mem["trades_abertos"][symbol]["peak_pnl"] = peak_pnl

        entry    = trade.get("entry", 0)
        qty      = abs(pos["qty"])
        qty_base = trade.get("qty_inicial", qty)
        margin   = (qty_base * entry) / ALAVANCAGEM if entry > 0 and qty_base > 0 else 0
        roi      = (pos["pnl"] / margin * 100) if margin > 0 else 0

        opened_at = trade.get("opened_at")
        elapsed   = (time.time() - opened_at) if opened_at else 1800

        # ── Profit lock progressivo (+0.5 USDC) — NUNCA perder após lucro ──
        # A cada +0.5 USDC, move stop para o nível anterior.
        # Se stop exchange falhar, enforcement por software fecha via MARKET.
        current_lock = trade.get("profit_lock_level", 0.0)
        if qty > 0 and entry > 0 and pos["pnl"] >= PROFIT_LOCK_USDC:
            new_lock = math.floor(pos["pnl"] / PROFIT_LOCK_STEP) * PROFIT_LOCK_STEP
            if new_lock >= PROFIT_LOCK_USDC and new_lock > current_lock + 1e-9:
                lock_usdc = max(new_lock - PROFIT_LOCK_STEP, 0.0)
                price_prec = PRICE_PRECISION.get(symbol, 2)
                if side == "LONG":
                    lock_price = (round(entry + lock_usdc / qty, price_prec)
                                  if lock_usdc > 0 else round(entry * (1 + BREAKEVEN_OFFSET), price_prec))
                else:
                    lock_price = (round(entry - lock_usdc / qty, price_prec)
                                  if lock_usdc > 0 else round(entry * (1 - BREAKEVEN_OFFSET), price_prec))

                if current_lock == 0.0:
                    for old_algo_id in get_open_algo_orders(symbol):
                        cancel_algo_order(symbol, old_algo_id)
                old_stop_bot = trade.get("stop_order_id")
                if old_stop_bot:
                    cancel_algo_order(symbol, old_stop_bot)
                    mem["trades_abertos"][symbol]["stop_order_id"] = None

                lock_side = "SELL" if side == "LONG" else "BUY"
                new_lock_id = None
                for _attempt in range(3):
                    new_lock_id = place_stop_market(symbol, lock_side, lock_price, qty)
                    if new_lock_id:
                        break
                    if side == "LONG":
                        lock_price = round(lock_price * (1 - 0.0015), price_prec)
                    else:
                        lock_price = round(lock_price * (1 + 0.0015), price_prec)
                    time.sleep(0.5)

                mem["trades_abertos"][symbol]["profit_lock_level"] = new_lock
                mem["trades_abertos"][symbol]["stop_order_id"]     = new_lock_id
                mem["trades_abertos"][symbol]["sl"]                = lock_price
                save_memory(mem)
                sl = lock_price
                current_lock = new_lock
                emoji_lock = "🔒" if trade.get("profit_lock_level", 0) == 0 else "📈"
                stop_txt_lk = f"#{new_lock_id}" if new_lock_id else "SOFTWARE ⚠️"
                if not new_lock_id:
                    print(f"[AVISO] {symbol}: profit lock stop falhou após 3 tentativas")
                tg(
                    f"{emoji_lock} <b>LOCK +{new_lock:.1f} USDC</b> — {symbol}\n"
                    f"Stop → {lock_price:.6g} ({stop_txt_lk}) | PnL: +{pos['pnl']:.2f} USDC"
                )

        # Software enforcement: se lock activo + stop não na exchange → fecha via MARKET
        if current_lock > 0 and not trade.get("stop_order_id"):
            lock_floor = max(current_lock - PROFIT_LOCK_STEP, 0.0)
            if pos["pnl"] <= lock_floor:
                if _fechar_com_retry(symbol, pos["qty"], side):
                    _registar_fecho(symbol, side, entry, sl, tp, qty,
                                    pos["pnl"], "PROFIT_LOCK_SW", pos["pnl"] > 0, mem)
                    tg(
                        f"🔒🔻 <b>SOFTWARE STOP</b> — {symbol}\n"
                        f"Lock era +{current_lock:.1f} | PnL caiu para {pos['pnl']:+.2f} USDC\n"
                        f"Fechada via MARKET (stop exchange não existia)"
                    )
                else:
                    tg(
                        f"⚠️ <b>SOFTWARE STOP FALHOU</b> — {symbol}\n"
                        f"PnL: {pos['pnl']:+.2f} < lock {lock_floor:+.1f} — FECHAR MANUALMENTE!"
                    )
                continue

        # ROI alto → fecha imediatamente, sem esperar tempo
        if roi >= ROI_TP_IMEDIATO:
            if _fechar_com_retry(symbol, pos["qty"], side):
                _registar_fecho(symbol, side, entry, sl, tp, qty,
                                pos["pnl"], "ROI_TP", True, mem)
                tg(
                    f"🎯 <b>ROI TP</b> — {symbol}\n"
                    f"ROI: {roi:.1f}% | PnL: {pos['pnl']:+.2f} | {int(elapsed/60)}min"
                )
            continue

        # ── ROI ≥ 5%: fecha se mercado não confirmar, deixa correr se confirmar ──
        # Evita sair prematuramente de winners em tendência forte.
        if (roi >= 5.0
                and not trade.get("trailing_lock_done")):
            sinal_ok = False
            score5   = 0
            try:
                kl5 = get_klines(symbol)
                if kl5 and len(kl5) >= 104:
                    c5 = [float(k[4]) for k in kl5]
                    h5 = [float(k[2]) for k in kl5]
                    l5 = [float(k[3]) for k in kl5]
                    v5 = [float(k[5]) for k in kl5]
                    dir5, score5, _ = signal_trending(c5, h5, l5, v5, symbol)
                    if dir5 == side and score5 >= SCORE_ALERTA:
                        sinal_ok = True
            except Exception as _e:
                print(f"[AVISO] roi5_check {symbol}: {_e}")

            if not sinal_ok:
                if _fechar_com_retry(symbol, pos["qty"], side):
                    _registar_fecho(symbol, side, entry, sl, tp, qty,
                                    pos["pnl"], "ROI5_TP", True, mem)
                    tg(
                        f"🎯 <b>ROI 5% TP</b> — {symbol}\n"
                        f"ROI: {roi:.1f}% | PnL: {pos['pnl']:+.2f} USDC\n"
                        f"Sinal enfraqueceu — saída confirmada."
                    )
                continue
            else:
                # Mercado ainda favorável — notifica 1x por 15min e deixa correr
                if time.time() - trade.get("roi5_skip_ts", 0) > 900:
                    mem["trades_abertos"][symbol]["roi5_skip_ts"] = time.time()
                    save_memory(mem)
                    tg(
                        f"🚀 <b>ROI 5% — DEIXA CORRER</b> — {symbol}\n"
                        f"ROI: {roi:.1f}% | Score: {score5} | Mercado confirma {side}."
                    )

        # ── Saída por reversão de sinal ──────────────────────────────────
        # Se o sinal original inverteu completamente (score forte na direcção oposta),
        # fecha antes de o preço atingir o SL. Não actua se trailing já protege.
        if (elapsed > 300
                and not trade.get("trailing_lock_done")
                and not trade.get("partial_tp2_done")
                and time.time() - _signal_inv_ts.get(symbol, 0) > 60):
            _signal_inv_ts[symbol] = time.time()
            try:
                kl_inv = get_klines(symbol)
                if kl_inv and len(kl_inv) >= 104:
                    c_inv = [float(k[4]) for k in kl_inv]
                    h_inv = [float(k[2]) for k in kl_inv]
                    l_inv = [float(k[3]) for k in kl_inv]
                    v_inv = [float(k[5]) for k in kl_inv]
                    inv_dir, inv_score, inv_det = signal_trending(
                        c_inv, h_inv, l_inv, v_inv, symbol)
                    if inv_dir is not None and inv_dir != side and inv_score >= SCORE_FORTE:
                        if _fechar_com_retry(symbol, pos["qty"], side):
                            _registar_fecho(symbol, side, entry, sl, tp, qty,
                                            pos["pnl"], "SIGNAL_INV", pos["pnl"] > 0, mem)
                            tg(
                                f"🔄 <b>SINAL INVERTIDO</b> — {symbol}\n"
                                f"Era {side} | Agora: {inv_dir} (score {inv_score})\n"
                                f"PnL: {pos['pnl']:+.2f} USDC | ROI: {roi:.1f}%\n"
                                f"{inv_det}"
                            )
                        continue
            except Exception as _e:
                print(f"[AVISO] signal_inv {symbol}: {_e}")

        # ── Saída por recuo do pico de lucro ──────────────────────────────
        # Se a trade já chegou a um lucro relevante (>= PEAK_PROFIT_MIN_USDC)
        # e recuou >= PEAK_DRAWDOWN_PCT desse pico, fecha — mas só se o sinal
        # já não confirmar a direcção (evita fechar por simples ruído).
        if (peak_pnl >= PEAK_PROFIT_MIN_USDC
                and not trade.get("trailing_lock_done")
                and time.time() - _peak_drawdown_ts.get(symbol, 0) > 60):
            drawdown_pnl = peak_pnl - pos["pnl"]
            if drawdown_pnl >= peak_pnl * PEAK_DRAWDOWN_PCT:
                _peak_drawdown_ts[symbol] = time.time()
                try:
                    kl_pk = get_klines(symbol)
                    pk_dir, pk_score = None, 0
                    if kl_pk and len(kl_pk) >= 104:
                        c_pk = [float(k[4]) for k in kl_pk]
                        h_pk = [float(k[2]) for k in kl_pk]
                        l_pk = [float(k[3]) for k in kl_pk]
                        v_pk = [float(k[5]) for k in kl_pk]
                        pk_dir, pk_score, _ = signal_trending(c_pk, h_pk, l_pk, v_pk, symbol)
                    sinal_ok = pk_dir == side and pk_score >= SCORE_ALERTA
                    if not sinal_ok:
                        if _fechar_com_retry(symbol, pos["qty"], side):
                            _registar_fecho(symbol, side, entry, sl, tp, qty,
                                            pos["pnl"], "PEAK_DRAWDOWN", pos["pnl"] > 0, mem)
                            tg(
                                f"📉 <b>RECUO DE PICO</b> — {symbol}\n"
                                f"Pico: +{peak_pnl:.2f} USDC → Agora: {pos['pnl']:+.2f} USDC\n"
                                f"Sinal já não confirma {side} — saída antecipada."
                            )
                        continue
                except Exception as _e:
                    print(f"[AVISO] peak_drawdown {symbol}: {_e}")

        # ── Tempo máximo: 4 horas → fecha incondicionalmente ────────────
        tempo_min = elapsed / 60
        if tempo_min >= 240 and not trade.get("trailing_lock_done"):
            if _fechar_com_retry(symbol, pos["qty"], side):
                _registar_fecho(symbol, side, entry, sl, tp, qty,
                                pos["pnl"], "MAX_TEMPO", pos["pnl"] > 0, mem)
                tg(
                    f"⏰ <b>TEMPO MÁXIMO 4H</b> — {symbol}\n"
                    f"{tempo_min:.0f}min | PnL: {pos['pnl']:+.2f} USDC\n"
                    f"Sinal original expirado — fecho forçado."
                )
            continue

        # ── Saída por estagnação ──────────────────────────────────────────
        # 90min-180min + PnL negativo: fecha se sinal não confirmar.
        # >180min + PnL negativo: fecha incondicionalmente (não deixa sangrar).
        if (tempo_min >= 90
                and pos["pnl"] < 0
                and not trade.get("trailing_lock_done")):
            mercado_ok = False
            if tempo_min < 180:
                try:
                    kl_stag = get_klines(symbol)
                    if kl_stag and len(kl_stag) >= 104:
                        c_s = [float(k[4]) for k in kl_stag]
                        h_s = [float(k[2]) for k in kl_stag]
                        l_s = [float(k[3]) for k in kl_stag]
                        v_s = [float(k[5]) for k in kl_stag]
                        stag_dir, stag_score, _ = signal_trending(c_s, h_s, l_s, v_s, symbol)
                        if stag_dir == side and stag_score >= SCORE_ALERTA:
                            mercado_ok = True
                except Exception as _e:
                    print(f"[AVISO] stagnado_check {symbol}: {_e}")

            if mercado_ok:
                ultimo_skip = trade.get("stagnado_skip_ts", 0)
                if time.time() - ultimo_skip > 900:
                    mem["trades_abertos"][symbol]["stagnado_skip_ts"] = time.time()
                    save_memory(mem)
                    tg(
                        f"⏳ <b>STAGNADO SUSPENSO</b> — {symbol}\n"
                        f"{tempo_min:.0f}min | PnL: {pos['pnl']:+.2f} USDC\n"
                        f"Mercado ainda favorável (score {stag_score}) — a aguardar."
                    )
                continue

            if not _fechar_com_retry(symbol, pos["qty"], side):
                continue
            reason_stag = "STAGNADO_3H" if tempo_min >= 180 else "STAGNADO"
            _registar_fecho(symbol, side, entry, sl, tp, qty,
                            pos["pnl"], reason_stag, pos["pnl"] > 0, mem)
            tg(
                f"⏳ <b>{reason_stag}</b> — {symbol}\n"
                f"{tempo_min:.0f}min sem progressão | PnL: {pos['pnl']:+.2f} USDC"
            )
            continue
        # Alerta quando marginal e no-man's-land (não fecha automaticamente)
        if (25 <= tempo_min < 60 and 0.5 <= pos["pnl"] <= 2.0
                and not trade.get("partial_tp_done")
                and time.time() - trade.get("stag_alerta_ts", 0) > 1800):
            mem["trades_abertos"][symbol]["stag_alerta_ts"] = time.time()
            save_memory(mem)
            tg(
                f"⚠️ <b>TRADE ESTAGNADO</b> — {symbol}\n"
                f"{tempo_min:.0f}min | PnL: +{pos['pnl']:.2f} USDC\n"
                f"Sem progressão — avalia fecho manual."
            )

        # ── Trailing stop ao atingir TRAILING_LOCK_USDC (default 4 USDC) ──
        # Substitui o stop fixo por trailing stop — garante pelo menos 10 USDC
        if (pos["pnl"] >= TRAILING_LOCK_USDC
                and not trade.get("trailing_lock_done")
                and entry > 0 and qty > 0):
            if side == "LONG":
                activation = round(entry + TRAILING_LOCK_USDC / qty, 8)
            else:
                activation = round(entry - TRAILING_LOCK_USDC / qty, 8)
            trail_side = "SELL" if side == "LONG" else "BUY"
            cb = TRAILING_CB_BTC if symbol in BTC_SYMBOLS else TRAILING_CB_ALT
            old_stop = trade.get("stop_order_id")
            if old_stop:
                cancel_algo_order(symbol, old_stop)
                mem["trades_abertos"][symbol]["stop_order_id"] = None
            trail_id = place_trailing_stop(symbol, trail_side, cb, activation)
            mem["trades_abertos"][symbol]["trailing_lock_done"] = True
            mem["trades_abertos"][symbol]["sl"] = activation
            if trail_id:
                mem["trades_abertos"][symbol]["stop_order_id"] = trail_id
            save_memory(mem)
            stop_txt = f"#{trail_id}" if trail_id else "SOFTWARE ⚠️"
            tg(
                f"🎯 <b>TRAILING LOCK +{TRAILING_LOCK_USDC:.0f} USDC</b> — {symbol}\n"
                f"Activação: {activation:.6g} | Callback: {cb}%\n"
                f"PnL: +{pos['pnl']:.2f} USDC | {stop_txt}"
            )

        # ── Breakeven a 1R: protege lucro antes do TP1 (2R) ───────────────
        # Sem isto, uma trade que esteve em lucro mas nunca chegou a 2R
        # pode reverter e fechar no SL original (perda), apesar de ter
        # passado tempo claramente positiva.
        entry_trade0 = trade.get("entry", 0)
        sl_orig      = trade.get("sl", entry_trade0)
        sl_dist      = abs(entry_trade0 - sl_orig)
        if (sl_dist > 0 and entry_trade0 > 0
                and not trade.get("partial_tp_done")
                and not trade.get("breakeven_1r_done")
                and not trade.get("profit_lock_level", 0)):
            if side == "LONG":
                r1_level = entry_trade0 + sl_dist
                hit_r1   = price >= r1_level
                be_price1 = round(entry_trade0 * (1 + BREAKEVEN_OFFSET), 8)
            else:
                r1_level = entry_trade0 - sl_dist
                hit_r1   = price <= r1_level
                be_price1 = round(entry_trade0 * (1 - BREAKEVEN_OFFSET), 8)
            if hit_r1:
                old_stop1 = trade.get("stop_order_id")
                if old_stop1:
                    try:
                        cancel_algo_order(symbol, old_stop1)
                    except Exception:
                        pass
                be_side1     = "SELL" if side == "LONG" else "BUY"
                new_stop_id1 = place_stop_market(symbol, be_side1, be_price1, abs(pos["qty"]))
                mem["trades_abertos"][symbol]["breakeven_1r_done"] = True
                mem["trades_abertos"][symbol]["sl"]                = be_price1
                mem["trades_abertos"][symbol]["stop_order_id"]     = new_stop_id1
                save_memory(mem)
                stop_txt1 = f"#{new_stop_id1}" if new_stop_id1 else "SOFTWARE ⚠️"
                tg(
                    f"🔒 <b>BREAKEVEN 1R</b> — {symbol}\n"
                    f"Preço: {price:.4f} | Stop movido para: {be_price1:.4f}\n"
                    f"{stop_txt1}"
                )
                sl = be_price1

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
                    # Nunca downgrade o stop se profit lock já o moveu mais acima
                    if side == "LONG":
                        be_price = round(entry_trade * (1 + BREAKEVEN_OFFSET), 8)
                        be_price = max(be_price, sl)
                    else:
                        be_price = round(entry_trade * (1 - BREAKEVEN_OFFSET), 8)
                        be_price = min(be_price, sl) if sl > 0 else be_price
                    # Cancela trailing stop antigo e coloca stop de breakeven
                    old_stop = trade.get("stop_order_id")
                    if old_stop:
                        try:
                            cancel_algo_order(symbol, old_stop)
                        except Exception:
                            pass
                    be_side     = "SELL" if side == "LONG" else "BUY"
                    cb_tp1      = TRAILING_CB_BTC if symbol in BTC_SYMBOLS else TRAILING_CB_ALT
                    new_stop_id = place_trailing_stop(symbol, be_side, cb_tp1, be_price)
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
                    # Nunca downgrade o stop se profit lock já o moveu mais acima
                    sl_dist_tp2 = abs(entry_trade - trade.get("sl", entry_trade))
                    if sl_dist_tp2 == 0:
                        sl_dist_tp2 = abs(entry_trade - tp) / 3.0
                    if side == "LONG":
                        lock_price = round(entry_trade + sl_dist_tp2, 8)
                        lock_price = max(lock_price, sl)
                    else:
                        lock_price = round(entry_trade - sl_dist_tp2, 8)
                        lock_price = min(lock_price, sl) if sl > 0 else lock_price
                    old_stop2 = trade.get("stop_order_id")
                    if old_stop2:
                        try:
                            cancel_algo_order(symbol, old_stop2)
                        except Exception:
                            pass
                    be_side2     = "SELL" if side == "LONG" else "BUY"
                    cb_tp2       = TRAILING_CB_BTC if symbol in BTC_SYMBOLS else TRAILING_CB_ALT
                    new_stop2_id = place_trailing_stop(symbol, be_side2, cb_tp2, lock_price)
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

        # Corte por perda absoluta em USDC (3 USDC independente do ROI %)
        if pos["pnl"] <= -EMERGENCY_PNL_CUT:
            if _fechar_com_retry(symbol, pos["qty"], side):
                log_risk_event("EMERGENCY_PNL", symbol=symbol,
                               details=f"pnl={pos['pnl']:.2f} roi={roi:.1f}%")
                _registar_fecho(symbol, side, entry, sl, tp, qty,
                                pos["pnl"], "EMERGENCY_PNL", False, mem)
                mem["emergency_cooldown_until"] = time.time() + 1800  # 30min sem novos trades
                save_memory(mem)
                tg(
                    f"🛑 <b>CORTE -3 USDC</b> — {symbol}\n"
                    f"PnL: {pos['pnl']:+.2f} USDC | ROI: {roi:.1f}%\n"
                    f"<i>Cooldown 30min activado.</i>"
                )
            else:
                tg(f"🚨 <b>CLOSE FALHOU — PNL</b> — {symbol}\nPnL: {pos['pnl']:+.2f} — fecha MANUALMENTE")
            continue

        # Emergency ROI cut
        if roi <= EMERGENCY_ROI_CUT:
            if _fechar_com_retry(symbol, pos["qty"], side):
                log_risk_event("EMERGENCY_CUT", symbol=symbol,
                               details=f"roi={roi:.1f}% pnl={pos['pnl']:.2f}")
                _registar_fecho(symbol, side, entry, sl, tp, qty,
                                pos["pnl"], "EMERGENCY_SL", False, mem)
                mem["emergency_cooldown_until"] = time.time() + 1800  # 30min sem novos trades
                save_memory(mem)
                tg(
                    f"🛑 <b>CORTE EMERGÊNCIA</b> — {symbol}\n"
                    f"ROI: {roi:.1f}% | PnL: {pos['pnl']:+.2f}\n"
                    f"<i>Cooldown 30min activado.</i>"
                )
            else:
                tg(
                    f"🚨 <b>CLOSE FALHOU — EMERGÊNCIA</b> — {symbol}\n"
                    f"ROI: {roi:.1f}% | 3 tentativas falharam — fecha MANUALMENTE"
                )
            continue

        if sl <= 0 or tp <= 0:
            continue

        hit_sl = (side == "LONG" and price <= sl) or (side == "SHORT" and price >= sl)
        hit_tp = (side == "LONG" and price >= tp) or (side == "SHORT" and price <= tp)

        # Grace period: software SL não dispara nos primeiros 3 minutos
        # Evita que SL calculado com ATR pequeno feche imediatamente após abertura
        if hit_sl and elapsed < 180:
            print(f"[SL_GRACE] {symbol}: SL hit em {elapsed:.0f}s — aguarda 3min antes de fechar via software")
            hit_sl = False

        if hit_sl or hit_tp:
            if not _fechar_com_retry(symbol, pos["qty"], side):
                tg(f"⚠️ <b>CLOSE FALHOU</b> — {symbol}\nSL/TP hit mas close recusado — retry ciclo seguinte")
                continue
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

    mem["total_trades"] = mem.get("wins", 0) + mem.get("losses", 0)
    atualizar_stats_simbolo(symbol, won, pnl, mem)
    close_position_db(symbol, reason, pnl, 0)
    save_memory(mem)
