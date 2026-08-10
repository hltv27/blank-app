#!/usr/bin/env python3
"""
Claw v8 — Backtesting Engine (actualizado Fase 2)
Testa a estratégia em dados históricos da Binance (sem autenticação).
Timeframe: 1H (alinhado com SIGNAL_INTERVAL actual).

Simula:
  - Entradas via signal_trending() + HTF alignment + filtros
  - SL baseado em ATR (2-2.5×)
  - Profit lock progressivo (+2 USDC trigger, +1 USDC step)
  - PEAK_DRAWDOWN (recuo ≥40% do pico após +1 USDC)
  - ROI_TP_IMEDIATO (12%)
  - STAGNADO (8-10h)
  - EMERGENCY_ROI_CUT (-25%)
  - Slippage e fees

Uso:
    python backtest.py                        # todos os símbolos, 90 dias
    python backtest.py --symbol BTCUSDC       # só BTC
    python backtest.py --days 180             # 6 meses
    python backtest.py --symbol SOLUSDC --days 120
"""

import os, sys, json, time, argparse, math
from datetime import datetime, timezone, timedelta
from pathlib import Path

_here = Path(__file__).parent
sys.path.insert(0, str(_here))

import requests
from config import (
    BASE_URL, SYMBOLS, SYMBOL_PRECISION,
    EMA_FAST, EMA_SLOW, EMA_TREND,
    STOCH_VETO_LONG, STOCH_VETO_SHORT,
    SCORE_ALERTA, SCORE_FORTE, SCORE_LONG_MIN, SCORE_SHORT_MIN,
    ATR_SL_MULT_MIN, ATR_SL_MULT_MAX, RATIO_ALVO,
    RISCO_USDC, ALAVANCAGEM,
    EMERGENCY_ROI_CUT, SUPERTREND_PERIOD, SUPERTREND_MULT,
    ATR_MIN_PCT, EMA_SLOPE_MIN,
    PROFIT_LOCK_USDC, PROFIT_LOCK_STEP,
    PEAK_PROFIT_MIN_USDC, PEAK_DRAWDOWN_PCT,
    ROI_TP_IMEDIATO, SL_MIN_PCT, SL_MAX_PCT,
    TAKER_FEE,
)
from indicators import (
    ema, rsi, atr, stoch_rsi, adx, supertrend,
    volume_ok, cmf_val, mfi_val, roc_val, cvd_bias, bb_squeeze,
)
from strategy import detect_market_mode, signal_trending, calc_sl_tp, calc_qty

# ─────────────────────────────────────────────
CACHE_DIR   = _here.parent / "backtest_cache"
MAX_BARS    = 48       # máx candles 1H por trade (48 × 1h = 48h = 2 dias)
LOOKBACK    = 220      # janela de indicadores

# ── Slippage & fee simulation ────────────────
SLIPPAGE_ENTRY = 0.0003  # 0.03% slippage on market entry
SLIPPAGE_SL    = 0.0005  # 0.05% slippage on stop loss (wider — adverse conditions)
SLIPPAGE_TP    = 0.0002  # 0.02% slippage on take profit
FEE_RATE       = 0.0005  # 0.05% taker fee per side (entry + exit) — Binance Futures
# ─────────────────────────────────────────────

CACHE_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════
#  DOWNLOAD E CACHE
# ═══════════════════════════════════════════════════════

def _download_klines(symbol: str, interval: str, start_ms: int, end_ms: int) -> list:
    """Faz download paginado de klines da Binance (sem auth)."""
    result = []
    limit  = 1000
    cur    = start_ms
    while cur < end_ms:
        try:
            r = requests.get(
                f"{BASE_URL}/fapi/v1/klines",
                params={"symbol": symbol, "interval": interval,
                        "startTime": cur, "endTime": end_ms, "limit": limit},
                timeout=15
            )
            data = r.json()
            if not isinstance(data, list) or not data:
                break
            result.extend(data)
            cur = int(data[-1][0]) + 1
            if len(data) < limit:
                break
            time.sleep(0.12)   # respeita rate limit
        except Exception as e:
            print(f"  [DOWNLOAD ERR] {symbol} {interval}: {e}")
            break
    return result


def load_klines(symbol: str, interval: str, days: int) -> list:
    """Carrega klines do cache ou descarrega. Cache válido durante 1h."""
    cache_file = CACHE_DIR / f"{symbol}_{interval}_{days}d.json"
    now = time.time()

    if cache_file.exists() and now - cache_file.stat().st_mtime < 3600:
        with open(cache_file) as f:
            return json.load(f)

    end_ms   = int(now * 1000)
    start_ms = end_ms - days * 24 * 3600 * 1000
    print(f"  Descarregando {symbol} {interval} ({days}d)...")
    data = _download_klines(symbol, interval, start_ms, end_ms)
    if data:
        with open(cache_file, "w") as f:
            json.dump(data, f)
    return data


# ═══════════════════════════════════════════════════════
#  HTF ALIGNMENT (4H sobre 1H)
# ═══════════════════════════════════════════════════════

def _build_htf_index(klines_htf: list) -> list:
    """Retorna lista de (open_time_ms, ema9, ema21) para cada vela HTF."""
    closes = [float(k[4]) for k in klines_htf]
    if len(closes) < 25:
        return []
    e9  = ema(closes, 9)
    e21 = ema(closes, 21)
    return [(int(klines_htf[i][0]), e9[i], e21[i]) for i in range(len(klines_htf))]


def htf_bias(htf_index: list, ts_ms: int) -> str:
    """
    Dado um timestamp 1H, devolve 'LONG', 'SHORT' ou 'NEUTRAL'
    consoante EMA9 vs EMA21 na última vela HTF fechada antes de ts_ms.
    """
    if not htf_index:
        return "NEUTRAL"
    result = None
    for (open_ts, e9, e21) in htf_index:
        if open_ts <= ts_ms:
            result = (e9, e21)
        else:
            break
    if result is None:
        return "NEUTRAL"
    return "LONG" if result[0] > result[1] else "SHORT"


# ═══════════════════════════════════════════════════════
#  SIMULAÇÃO DE TRADE (com profit lock + PEAK_DRAWDOWN)
# ═══════════════════════════════════════════════════════

def simulate_trade(direction: str, entry: float, sl: float, tp: float,
                   future_candles: list, qty: float, score: int = 0) -> dict | None:
    """
    Simula o trade nos candles 1H seguintes ao sinal.

    Mecanismos de saída simulados:
    1. SL baseado em ATR (exchange stop)
    2. Profit lock progressivo (+2 USDC trigger, +1 USDC step)
    3. PEAK_DRAWDOWN (recuo ≥40% após pico ≥1 USDC)
    4. ROI_TP_IMEDIATO (12% ROI)
    5. STAGNADO (8h com PnL < 0.5, 10h incondicional)
    6. EMERGENCY_ROI (-25%)
    7. TIMEOUT (48h)
    """
    if not future_candles or qty <= 0 or sl <= 0:
        return None

    # Preços de execução com slippage
    if direction == "LONG":
        sl_exec = sl * (1 - SLIPPAGE_SL)
    else:
        sl_exec = sl * (1 + SLIPPAGE_SL)

    margin = entry * qty / ALAVANCAGEM if ALAVANCAGEM > 0 else entry * qty

    # Estado do profit lock
    peak_pnl = 0.0
    lock_level = 0       # nível actual do profit lock (em steps de PROFIT_LOCK_STEP)
    current_sl = sl      # SL actual (pode ser movido pelo profit lock)

    for i, candle in enumerate(future_candles[:MAX_BARS]):
        high  = float(candle[2])
        low   = float(candle[3])
        close = float(candle[4])
        hours = i + 1  # horas desde entrada (candles 1H)

        # ── PnL actual (no close) ──────────────────────────────────
        if direction == "LONG":
            open_pnl = (close - entry) * qty
        else:
            open_pnl = (entry - close) * qty

        fee = entry * qty * FEE_RATE * 2
        net_pnl = open_pnl - fee

        # Actualizar pico
        if net_pnl > peak_pnl:
            peak_pnl = net_pnl

        roi = open_pnl / margin * 100 if margin > 0 else 0

        # ── 1. SL check (intra-candle via high/low) ────────────────
        if direction == "LONG":
            hit_sl = low <= current_sl
        else:
            hit_sl = high >= current_sl

        if hit_sl:
            if direction == "LONG":
                exit_price = current_sl * (1 - SLIPPAGE_SL)
                loss = (entry - exit_price) * qty
            else:
                exit_price = current_sl * (1 + SLIPPAGE_SL)
                loss = (exit_price - entry) * qty
            realized = -loss - fee
            # Se profit lock moveu o SL acima do entry, pode ser positivo
            exit_reason = "PROFIT_LOCK_SL" if lock_level > 0 else "SL"
            return {
                "won": realized > 0,
                "pnl": round(realized, 4),
                "exit_reason": exit_reason,
                "bars": hours,
            }

        # ── 2. ROI_TP_IMEDIATO (12%) ───────────────────────────────
        if roi >= ROI_TP_IMEDIATO:
            realized = open_pnl - fee
            return {
                "won": True,
                "pnl": round(realized, 4),
                "exit_reason": "ROI_TP",
                "bars": hours,
            }

        # ── 3. Profit lock progressivo ─────────────────────────────
        if net_pnl >= PROFIT_LOCK_USDC:
            new_level = int(net_pnl / PROFIT_LOCK_STEP)
            if new_level > lock_level:
                lock_level = new_level
                # Move SL para entry + (lock_level - 1) * step em termos de preço
                # Na prática: protege (lock_level - 1) * PROFIT_LOCK_STEP de lucro
                protected_pnl = (lock_level - 1) * PROFIT_LOCK_STEP
                if protected_pnl > 0:
                    sl_move = protected_pnl / qty
                    if direction == "LONG":
                        current_sl = max(current_sl, entry + sl_move)
                    else:
                        current_sl = min(current_sl, entry - sl_move)

        # ── 4. PEAK_DRAWDOWN ───────────────────────────────────────
        if peak_pnl >= PEAK_PROFIT_MIN_USDC and net_pnl > 0:
            drawdown_from_peak = (peak_pnl - net_pnl) / peak_pnl if peak_pnl > 0 else 0
            if drawdown_from_peak >= PEAK_DRAWDOWN_PCT:
                realized = net_pnl
                return {
                    "won": realized > 0,
                    "pnl": round(realized, 4),
                    "exit_reason": "PEAK_DD",
                    "bars": hours,
                }

        # ── 5. EMERGENCY_ROI ───────────────────────────────────────
        if roi <= EMERGENCY_ROI_CUT:
            realized = open_pnl - fee
            return {
                "won": False,
                "pnl": round(realized, 4),
                "exit_reason": "EMERGENCY",
                "bars": hours,
            }

        # ── 6. STAGNADO ────────────────────────────────────────────
        if hours >= 10:
            # 10h+ incondicional
            realized = open_pnl - fee
            return {
                "won": realized > 0,
                "pnl": round(realized, 4),
                "exit_reason": "STAGNADO",
                "bars": hours,
            }
        if hours >= 8 and net_pnl < 0.5:
            # 8h+ com PnL baixo
            realized = open_pnl - fee
            return {
                "won": realized > 0,
                "pnl": round(realized, 4),
                "exit_reason": "STAGNADO",
                "bars": hours,
            }

    # ── TIMEOUT: fecha no último candle ────────────────────────────
    if future_candles:
        last_close = float(future_candles[min(MAX_BARS - 1, len(future_candles) - 1)][4])
        if direction == "LONG":
            open_pnl = (last_close - entry) * qty
        else:
            open_pnl = (entry - last_close) * qty
        fee = entry * qty * FEE_RATE * 2
        realized = open_pnl - fee

    return {
        "won": realized > 0,
        "pnl": round(realized, 4),
        "exit_reason": "TIMEOUT",
        "bars": MAX_BARS,
    }


# ═══════════════════════════════════════════════════════
#  BACKTEST POR SÍMBOLO (1H)
# ═══════════════════════════════════════════════════════

def run_symbol(symbol: str, klines_1h: list, klines_4h: list) -> list:
    """
    Corre o backtest para um símbolo usando candles 1H.
    Retorna lista de trades simulados.
    """
    if len(klines_1h) < LOOKBACK + MAX_BARS + 10:
        print(f"  {symbol}: dados insuficientes ({len(klines_1h)} candles 1H)")
        return []

    htf4h = _build_htf_index(klines_4h)
    trades = []
    in_trade = False

    for i in range(LOOKBACK, len(klines_1h) - MAX_BARS - 1):
        if in_trade:
            last = trades[-1]
            if i >= last["entry_idx"] + last["bars"]:
                in_trade = False
            else:
                continue

        window = klines_1h[max(0, i - LOOKBACK + 1): i + 1]
        closes  = [float(k[4]) for k in window]
        highs   = [float(k[2]) for k in window]
        lows    = [float(k[3]) for k in window]
        volumes = [float(k[5]) for k in window]
        taker_buy = [float(k[9]) for k in window]

        atr_val = atr(highs, lows, closes)
        mode    = detect_market_mode(closes, atr_val)
        if mode != "TRENDING":
            continue

        direction, score, detalhe = signal_trending(closes, highs, lows, volumes, symbol)
        if not direction:
            continue

        # ── Score mínimo por direcção ──────────────────────────────
        if direction == "LONG" and score < SCORE_LONG_MIN:
            continue
        if direction == "SHORT" and score < SCORE_SHORT_MIN:
            continue

        # ── HTF alignment (4H) ─────────────────────────────────────
        ts_ms   = int(klines_1h[i][0])
        bias_4h = htf_bias(htf4h, ts_ms)

        if bias_4h != "NEUTRAL" and bias_4h != direction:
            continue

        # ── CVD ────────────────────────────────────────────────────
        cvd_v = cvd_bias(taker_buy, volumes)
        if direction == "LONG"  and cvd_v < -0.15:
            continue
        if direction == "SHORT" and cvd_v > 0.15:
            continue

        # ── BB squeeze ─────────────────────────────────────────────
        if bb_squeeze(closes):
            continue

        # ── Entrada e dimensionamento ──────────────────────────────
        price = closes[-1]
        adx_v = adx(highs, lows, closes)
        sl, tp = calc_sl_tp(direction, price, atr_val, mode, score, adx_v)
        qty    = calc_qty(price, sl, symbol)
        if qty <= 0:
            continue

        # ── Entry slippage ─────────────────────────────────────────
        if direction == "LONG":
            price_exec = price * (1 + SLIPPAGE_ENTRY)
        else:
            price_exec = price * (1 - SLIPPAGE_ENTRY)

        # ── Simulação do trade ─────────────────────────────────────
        future = klines_1h[i + 1: i + 1 + MAX_BARS]
        result = simulate_trade(direction, price_exec, sl, tp, future, qty, score)
        if result is None:
            continue

        ts_dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        trades.append({
            "symbol":    symbol,
            "direction": direction,
            "entry":     price_exec,
            "sl":        round(sl, 6),
            "tp":        round(tp, 6),
            "qty":       qty,
            "score":     score,
            "adx":       round(adx_v, 1),
            "ts":        ts_dt.strftime("%Y-%m-%d %H:%M"),
            "month":     ts_dt.strftime("%Y-%m"),
            "entry_idx": i,
            **result,
        })
        in_trade = True

    return trades


# ═══════════════════════════════════════════════════════
#  RELATÓRIO
# ═══════════════════════════════════════════════════════

def _pf(gross_wins, gross_losses):
    if gross_losses == 0:
        return float("inf") if gross_wins > 0 else 0.0
    return round(gross_wins / gross_losses, 2)


def print_report(all_trades: list, symbols_tested: list, days: int):
    if not all_trades:
        print("\nNenhum trade gerado.")
        return

    sep = "─" * 70

    # ── Por símbolo ────────────────────────────────────────────────
    print(f"\n{'═'*70}")
    print(f"  CLAW v8 — BACKTEST 1H ({days} dias) — {len(symbols_tested)} símbolos")
    print(f"{'═'*70}")

    print(f"\n{'SYM':<14} {'N':>4} {'WR%':>6} {'PnL':>8} {'PF':>5} {'AvgW':>7} {'AvgL':>7}")
    print(sep)

    for sym in symbols_tested:
        ts = [t for t in all_trades if t["symbol"] == sym]
        if not ts:
            continue
        wins   = [t for t in ts if t["won"]]
        losses = [t for t in ts if not t["won"]]
        gw     = sum(t["pnl"] for t in wins)
        gl     = abs(sum(t["pnl"] for t in losses))
        pnl    = sum(t["pnl"] for t in ts)
        wr     = len(wins) / len(ts) * 100
        avg_w  = gw / len(wins) if wins else 0
        avg_l  = gl / len(losses) if losses else 0
        print(f"{sym:<14} {len(ts):>4} {wr:>5.1f}% {pnl:>+8.2f} {_pf(gw, gl):>5} "
              f"{avg_w:>+7.2f} {-avg_l:>+7.2f}")

    # ── Totais ─────────────────────────────────────────────────────
    print(sep)
    wins_all   = [t for t in all_trades if t["won"]]
    losses_all = [t for t in all_trades if not t["won"]]
    gw_all     = sum(t["pnl"] for t in wins_all)
    gl_all     = abs(sum(t["pnl"] for t in losses_all))
    pnl_all    = sum(t["pnl"] for t in all_trades)
    wr_all     = len(wins_all) / len(all_trades) * 100
    avg_w_all  = gw_all / len(wins_all) if wins_all else 0
    avg_l_all  = gl_all / len(losses_all) if losses_all else 0
    expectancy = pnl_all / len(all_trades)

    print(f"{'TOTAL':<14} {len(all_trades):>4} {wr_all:>5.1f}% {pnl_all:>+8.2f} "
          f"{_pf(gw_all, gl_all):>5} {avg_w_all:>+7.2f} {-avg_l_all:>+7.2f}")

    # ── Exit reasons ───────────────────────────────────────────────
    reasons = {}
    for t in all_trades:
        r = t["exit_reason"]
        reasons[r] = reasons.get(r, 0) + 1
    print(f"\nMotivos de saída:")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        pct = v / len(all_trades) * 100
        pnl_r = sum(t["pnl"] for t in all_trades if t["exit_reason"] == k)
        print(f"  {k:<16} {v:>4} ({pct:>5.1f}%)  PnL {pnl_r:>+8.2f}")

    # ── Drawdown ───────────────────────────────────────────────────
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in sorted(all_trades, key=lambda x: x["ts"]):
        cum  += t["pnl"]
        peak  = max(peak, cum)
        dd    = peak - cum
        max_dd = max(max_dd, dd)

    # ── LONG vs SHORT ──────────────────────────────────────────────
    longs  = [t for t in all_trades if t["direction"] == "LONG"]
    shorts = [t for t in all_trades if t["direction"] == "SHORT"]
    l_wr   = len([t for t in longs  if t["won"]]) / len(longs)  * 100 if longs  else 0
    s_wr   = len([t for t in shorts if t["won"]]) / len(shorts) * 100 if shorts else 0
    l_pnl  = sum(t["pnl"] for t in longs)
    s_pnl  = sum(t["pnl"] for t in shorts)

    print(f"\nLONG:  {len(longs):>3} trades | WR {l_wr:.1f}% | PnL {l_pnl:+.2f} USDC")
    print(f"SHORT: {len(shorts):>3} trades | WR {s_wr:.1f}% | PnL {s_pnl:+.2f} USDC")

    # ── Por mês ────────────────────────────────────────────────────
    months = {}
    for t in all_trades:
        m = t["month"]
        months.setdefault(m, []).append(t["pnl"])
    print(f"\n{'Mês':<10} {'Trades':>6} {'PnL':>8} {'PnL/dia':>8}")
    print("─" * 38)
    for m in sorted(months):
        ts_m = months[m]
        pnl_m = sum(ts_m)
        # Estimar dias no mês
        days_in_month = 30
        pnl_per_day = pnl_m / days_in_month
        print(f"{m:<10} {len(ts_m):>6} {pnl_m:>+8.2f} {pnl_per_day:>+8.2f}")

    # ── Resumo final ───────────────────────────────────────────────
    avg_bars = sum(t["bars"] for t in all_trades) / len(all_trades)
    print(f"\n{'═'*70}")
    print(f"  Total trades   : {len(all_trades)}")
    print(f"  Win rate       : {wr_all:.1f}%")
    print(f"  Avg win        : {avg_w_all:+.2f} USDC")
    print(f"  Avg loss       : {-avg_l_all:+.2f} USDC")
    print(f"  Win/Loss ratio : {avg_w_all/avg_l_all:.2f}:1" if avg_l_all > 0 else "  Win/Loss ratio : N/A")
    print(f"  Expectancy     : {expectancy:+.2f} USDC/trade")
    print(f"  PnL total      : {pnl_all:+.2f} USDC  (risco {RISCO_USDC} USDC/trade)")
    print(f"  Profit factor  : {_pf(gw_all, gl_all)}")
    print(f"  Max drawdown   : -{max_dd:.2f} USDC")
    print(f"  Avg duração    : {avg_bars:.1f}h ({avg_bars:.0f} candles 1H)")
    total_notional = sum(abs(t["entry"]) * t["qty"] for t in all_trades)
    total_fees     = total_notional * FEE_RATE * 2
    print(f"  Fees est.      : -{total_fees:.2f} USDC  ({FEE_RATE*100:.3f}% x2 lados)")
    print(f"  Slippage       : entry {SLIPPAGE_ENTRY*100:.2f}%  SL {SLIPPAGE_SL*100:.2f}%  TP {SLIPPAGE_TP*100:.2f}%")
    pnl_per_day = pnl_all / days if days > 0 else 0
    print(f"  PnL/dia médio  : {pnl_per_day:+.2f} USDC")
    print(f"{'═'*70}")

    # ── Walk-Forward Validation ────────────────────────────────────
    sorted_trades = sorted(all_trades, key=lambda x: x["ts"])
    split_idx = int(len(sorted_trades) * 0.7)
    if split_idx > 0 and split_idx < len(sorted_trades):
        train_trades = sorted_trades[:split_idx]
        test_trades  = sorted_trades[split_idx:]

        def _wf_metrics(trades_wf):
            if not trades_wf:
                return 0, 0.0, 0.0, 0.0
            w = [t for t in trades_wf if t["won"]]
            gw = sum(t["pnl"] for t in w)
            gl = abs(sum(t["pnl"] for t in trades_wf if not t["won"]))
            return len(trades_wf), sum(t["pnl"] for t in trades_wf), \
                   len(w) / len(trades_wf) * 100, _pf(gw, gl)

        tr_n, tr_pnl, tr_wr, tr_pf = _wf_metrics(train_trades)
        te_n, te_pnl, te_wr, te_pf = _wf_metrics(test_trades)

        print(f"\n{'═'*70}")
        print(f"  === Walk-Forward Validation ===")
        print(f"  Training (70%): {tr_n} trades, {tr_pnl:+.2f} USDC, "
              f"{tr_wr:.1f}% win rate, PF {tr_pf}")
        print(f"  Testing  (30%): {te_n} trades, {te_pnl:+.2f} USDC, "
              f"{te_wr:.1f}% win rate, PF {te_pf}")
        tr_start = train_trades[0]["ts"][:10]
        tr_end   = train_trades[-1]["ts"][:10]
        te_start = test_trades[0]["ts"][:10]
        te_end   = test_trades[-1]["ts"][:10]
        print(f"  Periodo treino: {tr_start} a {tr_end}")
        print(f"  Periodo teste : {te_start} a {te_end}")
        print(f"{'═'*70}")
    else:
        print(f"\n  (Walk-forward: trades insuficientes para split 70/30)")
    print()


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Claw v8 Backtesting Engine (1H)")
    parser.add_argument("--symbol", type=str, default=None,
                        help="Símbolo específico (ex: BTCUSDC). Default: todos.")
    parser.add_argument("--days", type=int, default=90,
                        help="Número de dias históricos (default: 90)")
    args = parser.parse_args()

    symbols = [args.symbol] if args.symbol else SYMBOLS
    days    = args.days

    print(f"\n Claw v8 Backtest 1H — {days} dias — {len(symbols)} símbolo(s)")
    print(f" Config: PROFIT_LOCK={PROFIT_LOCK_USDC} STEP={PROFIT_LOCK_STEP} "
          f"PEAK_DD={PEAK_DRAWDOWN_PCT*100:.0f}% ROI_TP={ROI_TP_IMEDIATO}%")
    print(f" Score: ALERTA={SCORE_ALERTA} LONG_MIN={SCORE_LONG_MIN} "
          f"SHORT_MIN={SCORE_SHORT_MIN} FORTE={SCORE_FORTE}")
    print(f" Cache: {CACHE_DIR}\n")

    all_trades = []
    tested     = []

    for sym in symbols:
        print(f"[{sym}]")
        k1h = load_klines(sym, "1h",  days + 10)
        k4h = load_klines(sym, "4h",  days + 10)

        if not k1h or len(k1h) < LOOKBACK + MAX_BARS + 10:
            print(f"  {sym}: dados insuficientes — ignorado\n")
            continue

        trades = run_symbol(sym, k1h, k4h)
        print(f"  {len(trades)} trades simulados")
        all_trades.extend(trades)
        tested.append(sym)

    print_report(all_trades, tested, days)


if __name__ == "__main__":
    main()
