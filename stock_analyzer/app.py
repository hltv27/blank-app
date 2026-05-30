import os

import pandas as pd
import streamlit as st

# ── Stocks extracted from user's 19 TikTok screenshots ──────────────────────
SEED_TICKERS = [
    # Morgan Stanley Top Picks 2026
    "NVDA", "ALAB", "AVGO", "MU", "TSM", "AMAT", "ADI", "NXPI",
    # TikTok picks (charlesbuildswealth, linalikesmoney, algoxaustin, kenangrace1)
    "TSEM", "DELL", "HOOD", "NBIS", "ASTS", "RKLB", "OKLO",
    "CIFR", "CRWV", "IREN",
]

st.set_page_config(
    page_title="Stock Analyzer & ETF Finder",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Analisador de Ações & ETF Finder")
st.markdown(
    "Upload screenshots de TikTok/redes sociais → extrai tickers → "
    "analisa fundamentos + momentum → encontra os melhores ETFs."
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Necessária para extrair ações automaticamente dos screenshots.",
    )

    st.markdown("---")
    st.markdown("""
### Como usar
1. Insere a API Key (Anthropic)
2. Faz upload dos teus screenshots
3. Ou ajusta a lista manualmente
4. Clica em **Analisar**
""")
    st.markdown("---")
    st.markdown("""
### Score (0–100)
| Score | Avaliação |
|-------|-----------|
| ≥ 70 | 🟢 Excelente |
| ≥ 58 | 🔵 Bom |
| ≥ 45 | 🟡 Neutro |
| ≥ 32 | 🟠 Fraco |
| < 32 | 🔴 Mau |

**Componentes do score:**
- Momentum 1A/3M → 25%
- Qualidade (ROE, margens) → 25%
- Crescimento (receita, EPS) → 20%
- Valuation (P/E, P/S) → 20%
- Saúde + Analistas → 10%
""")

# ── Input ────────────────────────────────────────────────────────────────────
col_upload, col_manual = st.columns([3, 2])

with col_upload:
    uploaded_files = st.file_uploader(
        "📸 Screenshots (podes selecionar dezenas de uma vez)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

with col_manual:
    manual_input = st.text_area(
        "Tickers pré-carregados dos teus screenshots (edita à vontade):",
        value="\n".join(SEED_TICKERS),
        height=220,
    )

# ── Analyze button ────────────────────────────────────────────────────────────
if st.button("🔍 Analisar Ações", type="primary", use_container_width=True):
    from analyzer import analyze_stocks
    from etf_finder import find_etfs_for_stocks

    all_tickers: set = set()

    # --- Extract from screenshots via Claude Vision ---
    if uploaded_files:
        if not api_key:
            st.warning("⚠️ API Key em falta — screenshots ignorados. Usa a lista manual.")
        else:
            from extractor import extract_stocks_from_images

            images = [(f.name, f.read()) for f in uploaded_files]
            with st.spinner(f"A extrair ações de {len(images)} screenshot(s)…"):
                extracted = extract_stocks_from_images(images, api_key)

            with st.expander(f"📸 Ações extraídas dos {len(images)} screenshots", expanded=False):
                for fname, tickers in extracted.items():
                    st.write(f"**{fname}**: {', '.join(tickers) if tickers else '_nenhuma_'}")
                    all_tickers.update(tickers)

    # --- Manual / seed tickers ---
    for line in manual_input.strip().splitlines():
        t = line.strip().upper().replace(" ", "")
        if t and 1 <= len(t) <= 7:
            all_tickers.add(t)

    if not all_tickers:
        st.error("Nenhuma ação encontrada.")
        st.stop()

    st.success(f"**{len(all_tickers)} ações únicas** a analisar: {', '.join(sorted(all_tickers))}")

    # ── Stock analysis ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📈 Análise Fundamental + Momentum")

    df = analyze_stocks(list(all_tickers))

    if df.empty:
        st.error("Não foi possível obter dados financeiros para nenhum ticker.")
        st.stop()

    # Colour gradient on Score column
    st.dataframe(
        df.style.background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100),
        use_container_width=True,
        height=min(700, 45 + len(df) * 38),
    )

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=True),
        "stock_analysis.csv",
        "text/csv",
    )

    # ── Category breakdown ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Distribuição por Categoria")
    cats = df["Categoria"].value_counts()
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, cat in zip(
        [c1, c2, c3, c4, c5],
        ["🟢 Excelente", "🔵 Bom", "🟡 Neutro", "🟠 Fraco", "🔴 Mau"],
    ):
        col.metric(cat, cats.get(cat, 0))

    # ── Top 5 highlight ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🏆 Top 5 para Investir")
    top5 = df.head(5)[["Ticker", "Nome", "Score", "Categoria", "Ret. 1A", "Cresc. Rev.", "Upside Analistas"]]
    st.table(top5)

    # ── ETF Finder ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🏦 ETFs que Contêm as Melhores Ações")

    top_k = min(15, len(df))
    top_tickers = df.head(top_k)["Ticker"].tolist()
    st.info(
        f"A procurar ETFs com as top **{top_k}** ações: "
        f"{', '.join(top_tickers[:6])}{'…' if top_k > 6 else ''}"
    )

    etf_df = find_etfs_for_stocks(top_tickers)

    if etf_df.empty:
        st.warning(
            "Não foi possível verificar os ETFs (dados de holdings podem estar indisponíveis). "
            "ETFs sugeridos manualmente: **SMH** (semis), **ARKK** (inovação), **QQQ** (Nasdaq-100)."
        )
    else:
        st.dataframe(etf_df, use_container_width=True)

        best = etf_df.iloc[0]
        st.success(
            f"**Melhor ETF encontrado**: **{best['ETF']}** — {best['Nome']}  \n"
            f"Contém **{best['Nº Ações']}** das tuas melhores ações: {best['Ações Top Incluídas']}  \n"
            f"Peso combinado dessas ações no ETF: **{best['Peso Combinado (%)']}%**"
        )

    st.markdown("---")
    st.caption(
        "Dados via Yahoo Finance (yfinance). Scores são indicativos — não constituem aconselhamento financeiro."
    )
