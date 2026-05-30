import time
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
import yfinance as yf

# ── Sector classification ─────────────────────────────────────────────────────
# (ticker → (sector_pt, emoji, brief_description))
SECTOR_MAP: Dict[str, tuple] = {
    # IA & Semiconductors
    "NVDA":  ("IA & Semicondutores",       "🤖", "GPUs dominantes em IA; data centers e inferência"),
    "ALAB":  ("IA & Semicondutores",       "🤖", "Chips de conectividade para clusters de IA em hiperescala"),
    "AVGO":  ("IA & Semicondutores",       "🤖", "ASICs, networking e switch para data centers IA"),
    "MU":    ("IA & Semicondutores",       "🤖", "Memória HBM — o 'novo bottleneck' de IA (Morgan Stanley)"),
    "TSM":   ("IA & Semicondutores",       "🤖", "Maior foundry mundial; fabrica chips NVDA, AAPL, AMD"),
    "AMAT":  ("IA & Semicondutores",       "🤖", "Equipamento de fabricação de semicondutores (semicap)"),
    "ADI":   ("IA & Semicondutores",       "🤖", "Chips analógicos/mistos; recuperação automóvel+industrial"),
    "NXPI":  ("IA & Semicondutores",       "🤖", "Semicondutores automotive e IoT; recuperação cíclica"),
    "TSEM":  ("IA & Semicondutores",       "🤖", "Foundry especializada; nicho defence/medical/RF"),
    "SIVEF": ("IA & Semicondutores",       "🤖", "Sivers — chips RF e fotónica para 5G e defesa"),
    # AI Cloud & Infrastructure
    "NBIS":  ("IA Cloud & Infraestrutura", "☁️", "Nebius — cloud GPU nativa para treino de modelos IA"),
    "CRWV":  ("IA Cloud & Infraestrutura", "☁️", "CoreWeave — maior cloud GPU dedicada (ex-Nvidia partner)"),
    "DELL":  ("IA Cloud & Infraestrutura", "☁️", "Servidores AI PowerEdge; infrastructure play em IA"),
    # Space & Aerospace
    "ASTS":  ("Espaço & Comunicações",     "🚀", "Rede celular via satélite — internet direta ao telemóvel"),
    "RKLB":  ("Espaço & Comunicações",     "🚀", "Rocket Lab — lançamentos small-sat + produção de satélites"),
    # Nuclear Energy
    "OKLO":  ("Energia Nuclear",           "⚛️", "Micro-reatores modulares (SMR) — energia limpa para IA"),
    # Crypto Mining & HPC Energy
    "CIFR":  ("Cripto Mining",             "₿",  "Bitcoin mining — exposição pura a BTC sem deter BTC"),
    "IREN":  ("Cripto Mining",             "₿",  "Iris Energy — mining BTC + HPC/IA data centers verdes"),
    # Finance / Fintech
    "HOOD":  ("Fintech",                   "💰", "Robinhood — corretagem retail + cripto; crescimento rápido"),
    # Crypto / Digital Assets
    "GLXY":  ("Cripto & Activos Digitais", "🪙", "Galaxy Digital — banco cripto institucional (TSX)"),
}

# Sector descriptions (for section headers)
SECTOR_DESC: Dict[str, str] = {
    "IA & Semicondutores":       "O sector mais quente de 2024-2026. A corrida à capacidade de IA puxou chips, memória e equipamento. Risco: ciclo semis e concentração em TSMC.",
    "IA Cloud & Infraestrutura": "Cloud especializada em GPU rental e servidores IA. Crescimento explosivo mas margens comprimidas por CAPEX. Alta especulação.",
    "Espaço & Comunicações":     "Space 2.0 — lançamentos privados e internet via satélite. Alto risco, potencial disruptivo a 3-5 anos.",
    "Energia Nuclear":           "SMRs como solução energética para data centers IA. Longo prazo (5-10 anos até receitas relevantes). Muito especulativo.",
    "Cripto Mining":             "Proxy de Bitcoin — alta correlação com BTC, alta volatilidade. Mais fácil de comprar num broker que BTC direto.",
    "Fintech":                   "Plataformas financeiras digitais. HOOD beneficia do boom de retail trading e cripto.",
    "Cripto & Activos Digitais": "Exposição institucional a cripto. Fora do NYSE/NASDAQ — bolsa de Toronto (TSX).",
}

# ETF recommendations per sector
SECTOR_ETFS: Dict[str, List[str]] = {
    "IA & Semicondutores":       ["SMH", "SOXX", "XLK", "VGT", "QQQ"],
    "IA Cloud & Infraestrutura": ["SKYY", "CLOU", "WCLD", "QQQ", "ARKW"],
    "Espaço & Comunicações":     ["UFO", "ARKX", "XLC"],
    "Energia Nuclear":           ["NLR", "URA", "URNM"],
    "Cripto Mining":             ["WGMI", "BITQ", "BITO"],
    "Fintech":                   ["FINX", "ARKF", "KOIN"],
    "Cripto & Activos Digitais": ["BITQ", "BITO", "IBIT"],
}

# Fallback: map yfinance English sector → Portuguese sector name
YF_SECTOR_FALLBACK: Dict[str, str] = {
    "Technology":              "Tecnologia",
    "Communication Services":  "Comunicações",
    "Consumer Cyclical":       "Consumo Cíclico",
    "Consumer Defensive":      "Consumo Defensivo",
    "Healthcare":              "Saúde",
    "Financial Services":      "Financeiro",
    "Industrials":             "Industrial",
    "Basic Materials":         "Materiais",
    "Energy":                  "Energia",
    "Utilities":               "Utilities",
    "Real Estate":             "Imobiliário",
    "Defense":                 "Defesa",
}


def _sector_for(ticker: str, yf_sector: str) -> tuple:
    """Return (sector_pt, emoji, desc) — manual map takes priority."""
    if ticker in SECTOR_MAP:
        return SECTOR_MAP[ticker]
    pt = YF_SECTOR_FALLBACK.get(yf_sector, yf_sector or "Outro")
    return (pt, "📌", "")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(ticker: str) -> Dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

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
            'yf_sector': info.get('sector', ''),
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
    except Exception:
        return {'ticker': ticker, 'error': 'fetch failed'}


def _norm(value: Optional[float], lo: float, hi: float) -> Optional[float]:
    if value is None or hi == lo:
        return None
    return float(max(0.0, min(100.0, (value - lo) / (hi - lo) * 100)))


def score_stock(d: Dict) -> float:
    parts: List[tuple] = []

    if d.get('ret_1y') is not None:
        parts.append((_norm(d['ret_1y'], -50, 80), 0.15))
    if d.get('ret_3m') is not None:
        parts.append((_norm(d['ret_3m'], -25, 40), 0.10))

    fpe = d.get('forward_pe')
    if fpe and 0 < fpe < 200:
        parts.append((_norm(-fpe, -60, -5), 0.12))
    ps = d.get('ps')
    if ps and ps > 0:
        parts.append((_norm(-ps, -20, -0.5), 0.08))

    if d.get('roe') is not None:
        parts.append((_norm(d['roe'], -0.05, 0.35), 0.15))
    if d.get('profit_margin') is not None:
        parts.append((_norm(d['profit_margin'], -0.1, 0.30), 0.10))

    if d.get('revenue_growth') is not None:
        parts.append((_norm(d['revenue_growth'], -0.1, 0.40), 0.10))
    if d.get('earnings_growth') is not None:
        parts.append((_norm(d['earnings_growth'], -0.2, 0.50), 0.10))

    if d.get('rec_mean') and (d.get('num_analysts') or 0) >= 3:
        parts.append((_norm(-d['rec_mean'], -5, -1), 0.07))
        price, target = d.get('price'), d.get('target_price')
        if price and target and price > 0:
            upside = (target / price - 1) * 100
            parts.append((_norm(upside, -20, 50), 0.03))

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


def _verdict(score: float) -> str:
    if score >= 70: return '🟢 Forte Compra'
    if score >= 58: return '🔵 Compra'
    if score >= 45: return '🟡 Neutro'
    if score >= 32: return '🟠 Evitar'
    return '🔴 Vender/Ignorar'


def _pct(v) -> str:
    if v is None: return '—'
    return f"{round(v * 100, 1)}%"


def _fmt(v, d=1) -> str:
    if v is None: return '—'
    return str(round(v, d))


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
        sector_pt, emoji, note = _sector_for(ticker, d.get('yf_sector', ''))

        price = d.get('price')
        target = d.get('target_price')
        upside = round((target / price - 1) * 100, 1) if price and target and price > 0 else None

        rows.append({
            'Ticker':        d['ticker'],
            'Nome':          d.get('name', ticker),
            'Sector':        f"{emoji} {sector_pt}",
            '_sector_key':   sector_pt,   # clean key for grouping
            '_note':         note,
            'Score':         score,
            'Veredicto':     _verdict(score),
            'Preço':         f"${_fmt(price)}",
            'P/E Fwd':       _fmt(d.get('forward_pe')),
            'ROE':           _pct(d.get('roe')),
            'Margem Liq.':   _pct(d.get('profit_margin')),
            'Cresc. Receita':_pct(d.get('revenue_growth')),
            'Cresc. EPS':    _pct(d.get('earnings_growth')),
            'Ret. 1 Ano':    f"{round(d['ret_1y'], 1)}%" if d.get('ret_1y') is not None else '—',
            'Ret. 3 Meses':  f"{round(d['ret_3m'], 1)}%" if d.get('ret_3m') is not None else '—',
            'Upside Analysts':f"{upside}%" if upside is not None else '—',
            'Recomendação':  d.get('rec_key', '—'),
        })
        time.sleep(0.05)

    status.empty()
    progress.empty()

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values('Score', ascending=False).reset_index(drop=True)
        df.index += 1
    return df
