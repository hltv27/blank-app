import time
from typing import Dict, List

import pandas as pd
import streamlit as st
import yfinance as yf

# Curated list of ETFs that may hold the screened stocks
ETFS = {
    # Broad Market
    'SPY':  'SPDR S&P 500',
    'QQQ':  'Invesco Nasdaq-100',
    'VTI':  'Vanguard Total Market',
    'IVV':  'iShares S&P 500',
    'VOO':  'Vanguard S&P 500',
    'VUG':  'Vanguard Growth',
    # Technology
    'XLK':  'Technology Select SPDR',
    'VGT':  'Vanguard IT',
    'SMH':  'VanEck Semiconductors',
    'SOXX': 'iShares Semiconductors',
    'IGV':  'iShares Expanded Tech-Software',
    # Other sectors
    'XLF':  'Financial Select SPDR',
    'XLV':  'Health Care Select SPDR',
    'XLY':  'Consumer Discretionary SPDR',
    'XLC':  'Communication Services SPDR',
    'XLE':  'Energy Select SPDR',
    # Innovation / Growth
    'ARKK': 'ARK Innovation',
    'ARKG': 'ARK Genomic Revolution',
    'ARKQ': 'ARK Autonomous Tech',
    'ARKW': 'ARK Next Gen Internet',
    # Thematic
    'BOTZ': 'Global X Robotics & AI',
    'AIQ':  'Global X AI & Big Data',
    'ROBO': 'Robo Global Robotics',
    'FINX': 'Global X FinTech',
    'ICLN': 'iShares Clean Energy',
    'IBB':  'iShares Biotech',
    # Memory / Semiconductors (specific)
    'DRAM': 'Defiance Next Gen Connectivity',
}


@st.cache_data(ttl=3600, show_spinner=False)
def _get_holdings(symbol: str) -> Dict[str, float]:
    """Returns {TICKER: weight_%}. Tries multiple yfinance approaches."""
    try:
        t = yf.Ticker(symbol)

        # Approach 1: info['holdings'] (works for many ETFs)
        info = t.info or {}
        raw = info.get('holdings', [])
        if raw:
            return {
                h['symbol'].upper(): h.get('holdingPercent', 0) * 100
                for h in raw if 'symbol' in h
            }

        # Approach 2: funds_data.top_holdings (newer yfinance)
        try:
            fd = t.funds_data
            th = fd.top_holdings if fd else None
            if th is not None and not th.empty:
                result = {}
                for idx, row in th.iterrows():
                    col = next((c for c in ['Holding Percent', 'holdingPercent', 'weight']
                                if c in th.columns), None)
                    if col:
                        result[str(idx).upper()] = float(row[col]) * 100
                if result:
                    return result
        except Exception:
            pass
    except Exception:
        pass
    return {}


def find_etfs_for_stocks(top_stocks: List[str], top_n: int = 10) -> pd.DataFrame:
    rows = []
    progress = st.progress(0)
    status = st.empty()

    etf_list = list(ETFS.items())
    for i, (sym, name) in enumerate(etf_list):
        status.text(f"A verificar {sym}… ({i + 1}/{len(etf_list)})")
        progress.progress((i + 1) / len(etf_list))

        holdings = _get_holdings(sym)
        if not holdings:
            time.sleep(0.1)
            continue

        matched, total_weight = [], 0.0
        for stock in top_stocks:
            for key in [stock, stock.replace('.', '-'), stock.replace('-', '.')]:
                if key in holdings:
                    matched.append(stock)
                    total_weight += holdings[key]
                    break

        if matched:
            rows.append({
                'ETF': sym,
                'Nome': name,
                'Ações Top Incluídas': ', '.join(matched),
                'Nº Ações': len(matched),
                'Peso Combinado (%)': round(total_weight, 2),
            })

        time.sleep(0.08)

    status.empty()
    progress.empty()

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(
            ['Nº Ações', 'Peso Combinado (%)'],
            ascending=[False, False]
        ).reset_index(drop=True)
        df.index += 1
    return df.head(top_n)
