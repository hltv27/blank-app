import os

import pandas as pd
import streamlit as st

# ── All tickers extracted from user's screenshots (batches 1 & 2) ─────────────
SEED_TICKERS = [
    # ── IA & Semicondutores ──────────────────────────────────────────────────
    "NVDA", "ALAB", "AVGO", "AMD", "MRVL", "QCOM", "INTC", "ON", "TXN",
    "CRDO", "AMKR", "SIVEF", "POET",
    # ── Memória & Armazenamento ──────────────────────────────────────────────
    "MU", "WDC",
    # ── Foundry & Fabrico de Chips ───────────────────────────────────────────
    "TSM", "TSEM", "GFS", "UMC",
    # ── Equipamento Semicondutores ───────────────────────────────────────────
    "AMAT", "ASML", "LRCX", "KLAC", "TER", "ADI", "NXPI",
    # ── EDA & Design de Chips ────────────────────────────────────────────────
    "SNPS", "CDNS", "ARM",
    # ── IA Cloud & Infraestrutura ────────────────────────────────────────────
    "NBIS", "CRWV", "DELL", "SMCI", "NET", "DDOG",
    # ── Defesa & Drones ──────────────────────────────────────────────────────
    "AVAV", "KTOS", "HWM", "UMAC", "RCAT", "ONDS", "DPRO", "UAVS",
    # ── Espaço & Comunicações ─────────────────────────────────────────────────
    "ASTS", "RKLB",
    # ── Energia Nuclear & Grid ───────────────────────────────────────────────
    "OKLO", "VST",
    # ── Cripto Mining ────────────────────────────────────────────────────────
    "CIFR", "IREN",
    # ── Fintech ──────────────────────────────────────────────────────────────
    "HOOD",
]

# Companies seen in screenshots that are NOT yet publicly traded
PRIVATE_COMPANIES = [
    ("Physical Intelligence (π)", "Robotics IA — valuation $11B (Series B). Sem IPO anunciado."),
    ("Aetherflux",                "Space data centers — Series B $2B. Privada."),
    ("Starcloud",                 "AI cloud compute — Series A $1.1B. Privada."),
]

st.set_page_config(
    page_title="Stock Analyzer por Sector",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Analisador de Ações — Por Sector de Investimento")
st.markdown(
    "Extrai tickers de screenshots → analisa fundamentos + momentum → "
    "categoriza por **sector** (IA & Semis, Defesa, Espaço, Nuclear, Drones…) → "
    "encontra os melhores ETFs."
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
    st.markdown("---")
    st.markdown("""
### Estratégia simples 🇵🇹
De **miguelduartevfd** (vídeo nos screenshots):
- **60% VWCE** — 3.600 empresas mundiais, 0,22%/ano
- **30% QDVE** — S&P 500 Tech sector
- **10% liquidez** — fundo emergência

*"O simples bate o complicado quase sempre"*
""")

# ── Private companies warning ─────────────────────────────────────────────────
with st.expander("⚠️ Empresas nos screenshots que ainda NÃO têm cotação", expanded=False):
    for name, desc in PRIVATE_COMPANIES:
        st.markdown(f"- **{name}**: {desc}")
    st.caption("Não é possível investir directamente nestas — esperar por IPO ou usar ETFs temáticos.")

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
        "Tickers (pré-carregados dos teus 34 screenshots — edita à vontade):",
        value="\n".join(SEED_TICKERS),
        height=280,
    )

if not st.button("🔍 Analisar e Categorizar por Sector", type="primary", use_container_width=True):
    st.stop()

# ── Collect tickers ───────────────────────────────────────────────────────────
from analyzer import SECTOR_DESC, SECTOR_ETFS, analyze_stocks
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

n = len(all_tickers)
st.info(f"**{n} ações únicas** a analisar. Pode demorar {n // 3}–{n // 2} minutos (rate limit Yahoo Finance).")

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

DISPLAY_COLS = [
    "Ticker", "Nome", "Score", "Veredicto",
    "Preço", "P/E Fwd", "ROE", "Margem Liq.",
    "Cresc. Receita", "Ret. 1 Ano", "Upside Analysts", "Recomendação",
]

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — By Sector
# ─────────────────────────────────────────────────────────────────────────────
with tab_sector:
    st.subheader("Ações agrupadas por sector — do melhor sector para o pior")

    # Summary metric cards
    sector_order = (
        df.groupby("_sector_key")["Score"]
        .max()
        .sort_values(ascending=False)
        .index.tolist()
    )

    cols_per_row = 4
    for i in range(0, len(sector_order), cols_per_row):
        chunk = sector_order[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, sec in zip(cols, chunk):
            sec_df = df[df["_sector_key"] == sec]
            label = sec_df["Sector"].iloc[0]
            count = len(sec_df)
            best = sec_df["Score"].max()
            col.metric(label=label, value=f"{count} ação{'ões' if count != 1 else ''}", delta=f"Top score: {best}")

    st.markdown("---")

    # One section per sector
    for sec_key in sector_order:
        sec_df = df[df["_sector_key"] == sec_key].copy()
        sector_label = sec_df["Sector"].iloc[0]
        description = SECTOR_DESC.get(sec_key, "")
        etf_recs = SECTOR_ETFS.get(sec_key, [])

        st.markdown(f"### {sector_label}")
        if description:
            st.markdown(f"> {description}")
        if etf_recs:
            st.markdown(f"**ETFs deste sector:** `{'` · `'.join(etf_recs)}`")

        show = sec_df[DISPLAY_COLS].reset_index(drop=True)
        show.index = show.index + 1
        st.dataframe(
            show.style.background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True,
            height=min(450, 45 + len(show) * 38),
        )

        # Per-stock notes
        notes_shown = False
        for _, row in sec_df.iterrows():
            note = row.get("_note", "")
            if note:
                st.caption(f"**{row['Ticker']}** — {note}")
                notes_shown = True

        st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Overall Ranking
# ─────────────────────────────────────────────────────────────────────────────
with tab_ranking:
    st.subheader(f"Todas as {len(df)} ações ordenadas de melhor para pior")

    cat_counts = df["Veredicto"].value_counts()
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, v in zip(
        [c1, c2, c3, c4, c5],
        ["🟢 Forte Compra", "🔵 Compra", "🟡 Neutro", "🟠 Evitar", "🔴 Vender/Ignorar"],
    ):
        col.metric(v, cat_counts.get(v, 0))

    st.markdown("")

    rank_cols = [
        "Ticker", "Nome", "Sector", "Score", "Veredicto",
        "Preço", "P/E Fwd", "ROE", "Margem Liq.",
        "Cresc. Receita", "Cresc. EPS", "Ret. 1 Ano",
        "Ret. 3 Meses", "Upside Analysts", "Recomendação",
    ]
    show_rank = df[rank_cols].reset_index(drop=True)
    show_rank.index = show_rank.index + 1

    st.dataframe(
        show_rank.style.background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100),
        use_container_width=True,
        height=min(900, 45 + len(show_rank) * 38),
    )

    st.download_button(
        "⬇️ Download CSV completo",
        df.to_csv(index=True),
        "stock_analysis_por_sector.csv",
        "text/csv",
    )

    st.markdown("---")
    st.subheader("🏆 Top 10 — Melhores para Investir Agora")
    top10 = df.head(10)[["Ticker", "Nome", "Sector", "Score", "Veredicto",
                          "Ret. 1 Ano", "Cresc. Receita", "Upside Analysts"]].reset_index(drop=True)
    top10.index = top10.index + 1
    st.table(top10)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — ETFs
# ─────────────────────────────────────────────────────────────────────────────
with tab_etf:
    st.subheader("ETFs que cobrem os teus sectores — para investir sem comprar tudo")

    st.markdown("""
Se não tens capital para comprar todas as ações individualmente, os ETFs dão-te
exposição diversificada a um sector inteiro com **uma única compra**.
""")

    # ETF per sector table
    etf_rows = []
    for sec_key in sector_order:
        sec_df = df[df["_sector_key"] == sec_key]
        best_ticker = sec_df.iloc[0]["Ticker"]
        best_score = sec_df.iloc[0]["Score"]
        sector_label = sec_df["Sector"].iloc[0]
        etf_recs = SECTOR_ETFS.get(sec_key, [])
        all_tickers_in_sector = ", ".join(sec_df["Ticker"].tolist())
        etf_rows.append({
            "Sector": sector_label,
            "Ações no sector": all_tickers_in_sector,
            "Melhor Score": best_score,
            "ETFs Recomendados": " · ".join(etf_recs) if etf_recs else "—",
        })

    etf_summary = pd.DataFrame(etf_rows)
    st.dataframe(etf_summary, use_container_width=True, hide_index=True)

    # Auto ETF finder
    st.markdown("---")
    st.subheader("🔍 ETFs que realmente contêm as tuas top ações")

    top_k = min(15, len(df))
    top_tickers = df.head(top_k)["Ticker"].tolist()
    st.info(f"A verificar {top_k} ETFs curados com as tuas top {top_k} ações…")

    etf_df = find_etfs_for_stocks(top_tickers)

    if etf_df.empty:
        st.warning("Dados de holdings indisponíveis via yfinance. Usa a tabela por sector acima.")
    else:
        st.dataframe(etf_df, use_container_width=True)
        best = etf_df.iloc[0]
        st.success(
            f"**Melhor escolha:** **{best['ETF']}** — {best['Nome']}  \n"
            f"Contém {best['Nº Ações']} das tuas melhores ações: **{best['Ações Top Incluídas']}**  \n"
            f"Peso combinado no ETF: **{best['Peso Combinado (%)']}%**"
        )

    # Strategy guide
    st.markdown("---")
    st.markdown("""
### 💡 Estratégia por capital disponível

| Capital | Abordagem sugerida | ETFs |
|---------|-------------------|------|
| < €500 | 1-2 ETFs amplos | **QQQ** + **SMH** |
| €500–2k | Cobertura por sector | **QQQ** + **SMH** + **ITA** (defesa) + **URA** (nuclear) |
| €2k–10k | ETFs + top picks individuais | ETFs + **NVDA**, **ASML**, **AVAV** individualmente |
| > €10k | Selectivo por sector | Compra as top 2 ações por sector |

### 📊 Estratégia simples 🇵🇹 (miguelduartevfd)
Para quem não quer complexidade — bate 90% dos gestores:
- **60% VWCE** — Vanguard FTSE All-World; 3.600 empresas, 0,22%/ano
- **30% QDVE** — iShares S&P 500 Info Tech; exposição directa a tech
- **10% fundo de emergência** — Trade Republic a 2-3%/ano antes de investir

### 🚫 Empresas privadas dos screenshots — sem forma de investir ainda
""")
    for name, desc in PRIVATE_COMPANIES:
        st.markdown(f"- **{name}**: {desc}")

    st.caption(
        "Dados financeiros via Yahoo Finance. Scores e recomendações são indicativos — "
        "não constituem aconselhamento financeiro."
    )
