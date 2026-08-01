"""
Claw Agent v8.0 — Sinal Kronos (previsão de candlesticks)
Usa o modelo Kronos para prever as próximas candles e gerar bonus de score.
"""
import sys
import os
import time
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kronos"))

import config

KRONOS_ENABLED = True
KRONOS_SCORE = 2
KRONOS_PRED_LEN = 6
KRONOS_SAMPLE_COUNT = 3
KRONOS_MODEL_NAME = "NeoQuasar/Kronos-small"
KRONOS_TOKENIZER_NAME = "NeoQuasar/Kronos-Tokenizer-base"
KRONOS_MAX_CONTEXT = 512
KRONOS_COOLDOWN = 30

_predictor = None
_last_call = {}


def init_kronos():
    """Carrega modelo e tokenizer do HuggingFace (uma vez)."""
    global _predictor
    if _predictor is not None:
        return True
    try:
        import torch
        from model import Kronos, KronosTokenizer, KronosPredictor

        print("[KRONOS] A carregar modelo...")
        t0 = time.time()
        tokenizer = KronosTokenizer.from_pretrained(KRONOS_TOKENIZER_NAME)
        model = Kronos.from_pretrained(KRONOS_MODEL_NAME)
        _predictor = KronosPredictor(model, tokenizer, device="cpu", max_context=KRONOS_MAX_CONTEXT)
        dt = time.time() - t0
        print(f"[KRONOS] Modelo carregado em {dt:.1f}s ({KRONOS_MODEL_NAME}, CPU)")
        return True
    except Exception as e:
        print(f"[KRONOS] Falha ao carregar modelo: {e}")
        _predictor = None
        return False


def kronos_score(symbol, klines, direction):
    """
    Prevê as próximas candles via Kronos e retorna bonus de score.

    Args:
        symbol: par (ex: "BTCUSDC")
        klines: lista de klines da Binance [[open_time, open, high, low, close, volume, ...], ...]
        direction: "LONG" ou "SHORT"

    Returns:
        (bonus, detalhe): bonus de score (int) e string descritiva
    """
    if not KRONOS_ENABLED or _predictor is None:
        return 0, "KRONOS_OFF"

    now = time.time()
    if symbol in _last_call and now - _last_call[symbol] < KRONOS_COOLDOWN:
        return 0, "KRONOS_COOLDOWN"

    try:
        import pandas as pd
        import numpy as np

        if len(klines) < 50:
            return 0, "KRONOS_DADOS_INSUF"

        lookback = min(len(klines), KRONOS_MAX_CONTEXT)
        klines_use = klines[-lookback:]

        timestamps = pd.to_datetime([int(k[0]) for k in klines_use], unit='ms')
        df = pd.DataFrame({
            'open':   [float(k[1]) for k in klines_use],
            'high':   [float(k[2]) for k in klines_use],
            'low':    [float(k[3]) for k in klines_use],
            'close':  [float(k[4]) for k in klines_use],
            'volume': [float(k[5]) for k in klines_use],
        })
        df['amount'] = df['volume'] * df[['open', 'high', 'low', 'close']].mean(axis=1)

        interval_ms = int(klines_use[-1][0]) - int(klines_use[-2][0])
        last_ts = pd.Timestamp(int(klines_use[-1][0]), unit='ms')
        y_timestamps = pd.DatetimeIndex([
            last_ts + pd.Timedelta(milliseconds=interval_ms * (i + 1))
            for i in range(KRONOS_PRED_LEN)
        ])

        _last_call[symbol] = now

        pred_df = _predictor.predict(
            df=df,
            x_timestamp=timestamps,
            y_timestamp=y_timestamps,
            pred_len=KRONOS_PRED_LEN,
            T=0.8,
            top_p=0.9,
            sample_count=KRONOS_SAMPLE_COUNT,
            verbose=False,
        )

        current_close = float(klines_use[-1][4])
        pred_closes = pred_df['close'].values
        pred_final = float(np.mean(pred_closes[-3:]))

        pct_change = (pred_final - current_close) / current_close * 100

        pred_direction = "LONG" if pct_change > 0.1 else ("SHORT" if pct_change < -0.1 else "NEUTRAL")

        detail = f"KRONOS {pred_direction} {pct_change:+.2f}%"

        if pred_direction == direction:
            return KRONOS_SCORE, detail
        elif pred_direction == "NEUTRAL":
            return 0, detail
        else:
            return -1, detail

    except Exception as e:
        tb_short = traceback.format_exc().strip().splitlines()[-1]
        print(f"[KRONOS] Erro {symbol}: {tb_short}")
        return 0, f"KRONOS_ERRO"
