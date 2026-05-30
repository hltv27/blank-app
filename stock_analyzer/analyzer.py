import time
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(ticker: str) -> Dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        # Require at least a price to consider the ticker valid
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not price:
            return {'ticker': ticker, 'error': 'no price data'}

        hist = t.history(period="1y", auto_adjust=True)
        ret_1y = ret_3m = None
        if len(hist) > 5:
            ret_1y = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
            if len(hist) >= 63:
                ret_3m = (hist['Close'].iloc[-1] / hist['Close'].iloc[-63] - 1) * 100

        return {
            'ticker': ticker,
            'name': (info.get('longName') or info.get('shortName') or ticker)[:35],
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'market_cap': info.get('marketCap'),
            'price': price,
            'target_price': info.get('targetMeanPrice'),
            'forward_pe': info.get('forwardPE'),
            'pb': info.get('priceToBook'),
            'ps': info.get('priceToSalesTrailing12Months'),
            'roe': info.get('returnOnEquity'),
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'debt_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'rec_mean': info.get('recommendationMean'),
            'rec_key': info.get('recommendationKey', ''),
            'num_analysts': info.get('numberOfAnalystOpinions', 0) or 0,
            'ret_1y': ret_1y,
            'ret_3m': ret_3m,
        }
    except Exception as e:
        return {'ticker': ticker, 'error': str(e)}


def _norm(value: Optional[float], lo: float, hi: float) -> Optional[float]:
    if value is None or hi == lo:
        return None
    return float(max(0.0, min(100.0, (value - lo) / (hi - lo) * 100)))


def score_stock(d: Dict) -> float:
    parts: List[tuple] = []  # (score, weight)

    # Momentum (25%)
    if d.get('ret_1y') is not None:
        parts.append((_norm(d['ret_1y'], -50, 80), 0.15))
    if d.get('ret_3m') is not None:
        parts.append((_norm(d['ret_3m'], -25, 40), 0.10))

    # Valuation — lower P/E / P/S = better (20%)
    fpe = d.get('forward_pe')
    if fpe and 0 < fpe < 200:
        parts.append((_norm(-fpe, -60, -5), 0.12))
    ps = d.get('ps')
    if ps and ps > 0:
        parts.append((_norm(-ps, -20, -0.5), 0.08))

    # Quality (25%)
    if d.get('roe') is not None:
        parts.append((_norm(d['roe'], -0.05, 0.35), 0.15))
    if d.get('profit_margin') is not None:
        parts.append((_norm(d['profit_margin'], -0.1, 0.30), 0.10))

    # Growth (20%)
    if d.get('revenue_growth') is not None:
        parts.append((_norm(d['revenue_growth'], -0.1, 0.40), 0.10))
    if d.get('earnings_growth') is not None:
        parts.append((_norm(d['earnings_growth'], -0.2, 0.50), 0.10))

    # Analyst sentiment (10%)
    if d.get('rec_mean') and (d.get('num_analysts') or 0) >= 3:
        parts.append((_norm(-d['rec_mean'], -5, -1), 0.07))
        price, target = d.get('price'), d.get('target_price')
        if price and target and price > 0:
            upside = (target / price - 1) * 100
            parts.append((_norm(upside, -20, 50), 0.03))

    # Financial health (10%)
    de = d.get('debt_equity')
    if de is not None and de >= 0:
        parts.append((_norm(-min(de, 300), -300, 0), 0.05))
    if d.get('current_ratio') is not None:
        parts.append((_norm(min(d['current_ratio'], 4), 0.5, 3.5), 0.05))

    valid = [(s, w) for s, w in parts if s is not None]
    if not valid:
        return 0.0
    total_w = sum(w for _, w in valid)
    return round(sum(s * w for s, w in valid) / total_w, 1)


def _category(score: float) -> str:
    if score >= 70: return '🟢 Excelente'
    if score >= 58: return '🔵 Bom'
    if score >= 45: return '🟡 Neutro'
    if score >= 32: return '🟠 Fraco'
    return '🔴 Mau'


def _pct(v) -> str:
    if v is None: return 'N/A'
    return f"{round(v * 100, 1)}%"


def _fmt(v, decimals=1) -> str:
    if v is None: return 'N/A'
    return str(round(v, decimals))


def analyze_stocks(tickers: List[str]) -> pd.DataFrame:
    rows = []
    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.text(f"A analisar {ticker}… ({i + 1}/{len(tickers)})")
        progress.progress((i + 1) / len(tickers))

        d = fetch_stock_data(ticker)
        if 'error' in d:
            continue

        score = score_stock(d)
        price = d.get('price')
        target = d.get('target_price')
        upside = round((target / price - 1) * 100, 1) if price and target and price > 0 else None

        rows.append({
            'Ticker': d['ticker'],
            'Nome': d.get('name', ticker),
            'Sector': d.get('sector') or 'N/A',
            'Score': score,
            'Categoria': _category(score),
            'P/E Fwd': _fmt(d.get('forward_pe')),
            'ROE': _pct(d.get('roe')),
            'Margem Liq.': _pct(d.get('profit_margin')),
            'Cresc. Rev.': _pct(d.get('revenue_growth')),
            'Cresc. EPS': _pct(d.get('earnings_growth')),
            'Ret. 1A': f"{round(d['ret_1y'], 1)}%" if d.get('ret_1y') is not None else 'N/A',
            'Ret. 3M': f"{round(d['ret_3m'], 1)}%" if d.get('ret_3m') is not None else 'N/A',
            'Upside Analistas': f"{upside}%" if upside is not None else 'N/A',
            'Recomendação': d.get('rec_key', 'N/A'),
        })

        time.sleep(0.05)

    status.empty()
    progress.empty()

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values('Score', ascending=False).reset_index(drop=True)
        df.index += 1
    return df
