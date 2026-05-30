import os

import pandas as pd
import streamlit as st

# ── Stocks extracted from user's 19 TikTok/Instagram screenshots ─────────────
SEED_TICKERS = [
    # Morgan Stanley Top Picks 2026 — semicondutores
    "NVDA", "ALAB", "AVGO", "MU", "TSM", "AMAT", "ADI", "NXPI",
    # TikTok picks
    "TSEM",   # linalikesmoney — Tower Semiconductor
    "DELL",   # kenangrace1 — servidores IA
    "HOOD",   # fintech
    "NBIS",   # charlesbuildswealth — Nebius AI cloud
    "ASTS",   # AST SpaceMobile
    "RKLB",   # Rocket Lab
    "OKLO",   # energia nuclear
    "CIFR",   # Cipher Mining
    "CRWV",   # CoreWeave
    "IREN",   # Iris Energy
]

st.set_page_config(
    page_title="Stock Analyzer por Sector",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Analisador de Ações — Por Sector de Investimento")
st.markdown(
    "Extrai tickers de screenshots → analisa fundamentos + momentum → "
    "categoriza por **sector** (IA, Espaço, Nuclear, Cripto…) → encontra os melhores ETFs."
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Para extrair tickers automaticamente de screenshots.",
    )
    st.markdown("---")
    st.markdown("""
### Score (0–100)
Composto por:
- **Momentum** 1A + 3M → 25 %
- **Qualidade** ROE + margens → 25 %
- **Crescimento** receita + EPS → 20 %
- **Valuation** P/E + P/S → 20 %
- **Analistas** + saúde financeira → 10 %

| Score | Veredicto |
|-------|-----------|
| ≥ 70 | 🟢 Forte Compra |
| ≥ 58 | 🔵 Compra |
| ≥ 45 | 🟡 Neutro |
| ≥ 32 | 🟠 Evitar |
| < 32 | 🔴 Vender/Ignorar |
""")

# ── Input ─────────────────────────────────────────────────────────────────────
col_up, col_man = st.columns([3, 2])

with col_up:
    uploaded_files = st.file_uploader(
        "📸 Screenshots (podes selecionar dezenas de uma vez)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

with col_man:
    manual_input = st.text_area(
        "Tickers (pré-carregados dos teus screenshots — edita à vontade):",
        value="\n".join(SEED_TICKERS),
        height=230,
    )

if not st.button("🔍 Analisar e Categorizar por Sector", type="primary", use_container_width=True):
    st.stop()

# ── Collect tickers ───────────────────────────────────────────────────────────
from analyzer import (
    SECTOR_DESC, SECTOR_ETFS, analyze_stocks
)
from etf_finder import find_etfs_for_stocks

all_tickers: set = set()

if uploaded_files and api_key:
    from extractor import extract_stocks_from_images
    images = [(f.name, f.read()) for f in uploaded_files]
    with st.spinner(f"A extrair ações de {len(images)} screenshot(s)…"):
        extracted = extract_stocks_from_images(images, api_key)
    with st.expander(f"📸 Extracção — {len(images)} screenshots", expanded=False):
        for fname, tks in extracted.items():
            st.write(f"**{fname}**: {', '.join(tks) if tks else '_nenhuma_'}")
            all_tickers.update(tks)
elif uploaded_files and not api_key:
    st.warning("⚠️ API Key em falta — screenshots ignorados. A usar lista manual.")

for line in manual_input.strip().splitlines():
    t = line.strip().upper().replace(" ", "")
    if t and 1 <= len(t) <= 7:
        all_tickers.add(t)

if not all_tickers:
    st.error("Nenhuma ação encontrada.")
    st.stop()

st.info(f"**{len(all_tickers)} ações únicas** a analisar: {', '.join(sorted(all_tickers))}")

# ── Analysis ──────────────────────────────────────────────────────────────────
st.markdown("---")
df = analyze_stocks(list(all_tickers))

if df.empty:
    st.error("Não foi possível obter dados financeiros.")
    st.stop()

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_sector, tab_ranking, tab_etf = st.tabs([
    "🏭 Por Sector",
    "📊 Ranking Geral",
    "🏦 ETFs Recomendados",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — By Sector
# ─────────────────────────────────────────────────────────────────────────────
DISPLAY_COLS = [
    "Ticker", "Nome", "Score", "Veredicto",
    "Preço", "P/E Fwd", "ROE", "Margem Liq.",
    "Cresc. Receita", "Ret. 1 Ano", "Upside Analysts", "Recomendação",
]

with tab_sector:
    st.subheader("Ações agrupadas por sector de investimento")

    # Summary cards
    sectors_present = df["_sector_key"].unique()
    cols_per_row = 3
    sector_list = sorted(sectors_present)
    rows = [sector_list[i:i + cols_per_row] for i in range(0, len(sector_list), cols_per_row)]

    for row in rows:
        cols = st.columns(cols_per_row)
        for col, sec in zip(cols, row):
            count = len(df[df["_sector_key"] == sec])
            best_score = df[df["_sector_key"] == sec]["Score"].max()
            sector_label = df[df["_sector_key"] == sec]["Sector"].iloc[0]
            col.metric(
                label=sector_label,
                value=f"{count} ação{'ões' if count != 1 else ''}",
                delta=f"Melhor score: {best_score}",
            )

    st.markdown("---")

    # One section per sector (ordered by best score in sector)
    sector_order = (
        df.groupby("_sector_key")["Score"].max()
        .sort_values(ascending=False)
        .index.tolist()
    )

    for sec_key in sector_order:
        sec_df = df[df["_sector_key"] == sec_key].copy()
        sector_label = sec_df["Sector"].iloc[0]
        description = SECTOR_DESC.get(sec_key, "")
        etf_recs = SECTOR_ETFS.get(sec_key, [])

        # Header
        st.markdown(f"### {sector_label}")
        if description:
            st.markdown(f"> {description}")

        # ETFs for this sector
        if etf_recs:
            st.markdown(f"**ETFs deste sector:** `{'` · `'.join(etf_recs)}`")

        # Stocks table
        show = sec_df[DISPLAY_COLS].reset_index(drop=True)
        show.index = show.index + 1
        st.dataframe(
            show.style.background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True,
            height=min(400, 45 + len(show) * 38),
        )

        # Individual stock notes
        for _, row in sec_df.iterrows():
            note = row.get("_note", "")
            if note:
                st.caption(f"**{row['Ticker']}** — {note}")

        st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Overall Ranking
# ─────────────────────────────────────────────────────────────────────────────
with tab_ranking:
    st.subheader("Todas as ações ordenadas de melhor para pior")

    # Summary pills
    cat_counts = df["Veredicto"].value_counts()
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, v in zip(
        [c1, c2, c3, c4, c5],
        ["🟢 Forte Compra", "🔵 Compra", "🟡 Neutro", "🟠 Evitar", "🔴 Vender/Ignorar"],
    ):
        col.metric(v, cat_counts.get(v, 0))

    st.markdown("")

    rank_cols = ["Ticker", "Nome", "Sector", "Score", "Veredicto",
                 "Preço", "P/E Fwd", "ROE", "Margem Liq.",
                 "Cresc. Receita", "Cresc. EPS", "Ret. 1 Ano",
                 "Ret. 3 Meses", "Upside Analysts", "Recomendação"]
    show_rank = df[rank_cols].reset_index(drop=True)
    show_rank.index = show_rank.index + 1

    st.dataframe(
        show_rank.style.background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100),
        use_container_width=True,
        height=min(800, 45 + len(show_rank) * 38),
    )

    st.download_button(
        "⬇️ Download CSV completo",
        df.to_csv(index=True),
        "stock_analysis_por_sector.csv",
        "text/csv",
    )

    # Top 5
    st.markdown("---")
    st.subheader("🏆 Top 5 — Melhores para Investir Agora")
    top5 = df.head(5)[["Ticker", "Nome", "Sector", "Score", "Veredicto",
                        "Ret. 1 Ano", "Cresc. Receita", "Upside Analysts"]].reset_index(drop=True)
    top5.index = top5.index + 1
    st.table(top5)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — ETFs
# ─────────────────────────────────────────────────────────────────────────────
with tab_etf:
    st.subheader("ETFs que cobrem as tuas melhores ações")

    st.markdown("""
Como não tens dinheiro para comprar tudo, os ETFs permitem-te ter exposição
a **vários sectores ao mesmo tempo** com um único produto.
Abaixo: ETFs recomendados por sector + ETFs que realmente contêm as tuas top ações.
""")

    # Manual ETF table per sector
    etf_rows = []
    for sec_key in sector_order:
        sec_df = df[df["_sector_key"] == sec_key]
        best_ticker = sec_df.iloc[0]["Ticker"]
        best_score = sec_df.iloc[0]["Score"]
        sector_label = sec_df["Sector"].iloc[0]
        etf_recs = SECTOR_ETFS.get(sec_key, [])
        etf_rows.append({
            "Sector": sector_label,
            "Melhor Ação": best_ticker,
            "Score": best_score,
            "ETFs Recomendados": " · ".join(etf_recs) if etf_recs else "—",
        })

    etf_summary = pd.DataFrame(etf_rows)
    st.dataframe(etf_summary, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔍 ETFs que realmente contêm as tuas top ações")

    top_k = min(12, len(df))
    top_tickers = df.head(top_k)["Ticker"].tolist()
    st.info(f"A verificar {top_k} ETFs curados contra as tuas top {top_k} ações…")

    etf_df = find_etfs_for_stocks(top_tickers)

    if etf_df.empty:
        st.warning(
            "Dados de holdings indisponíveis via yfinance. "
            "Usa os ETFs recomendados por sector na tabela acima."
        )
    else:
        st.dataframe(etf_df, use_container_width=True)
        best = etf_df.iloc[0]
        st.success(
            f"**Melhor escolha:** **{best['ETF']}** — {best['Nome']}  \n"
            f"Contém {best['Nº Ações']} das tuas melhores ações: **{best['Ações Top Incluídas']}**  \n"
            f"Peso combinado no ETF: **{best['Peso Combinado (%)']}%**"
        )

    st.markdown("---")
    st.markdown("""
### 💡 Estratégia se tiveres pouco capital

| Objectivo | ETF sugerido | Porquê |
|-----------|-------------|--------|
| Exposição IA + Semis | **SMH** ou **SOXX** | Concentrado em semicondutores; cobre NVDA, AVGO, MU, TSM, AMAT |
| Exposição Nasdaq ampla | **QQQ** | Top 100 Nasdaq; inclui maioria das tuas tech picks |
| Nuclear + Energia limpa | **URA** + **ICLN** | Única forma barata de ter OKLO + outros SMRs |
| Espaço | **UFO** ou **ARKX** | Cobre ASTS, RKLB e outros |
| Cripto (sem comprar BTC) | **WGMI** | Mineiros BTC incluindo CIFR e IREN |
""")

    st.caption(
        "Dados financeiros via Yahoo Finance. Scores e recomendações são indicativos — "
        "não constituem aconselhamento financeiro."
    )
