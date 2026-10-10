# AI / ML / LLM-agent open-source trading systems (2023-2026): state of the projects and the real evidence

Research date: 2026-10-10. Star counts come from GitHub repository search (GitHub MCP), queried 2026-10-10. Firecrawl ran out of credits partway through and direct arxiv.org access was blocked by the proxy, so several paper figures come from search-engine summaries of the paper pages (marked "via summary"). Treat those as needing verification against the PDF.

## 1. Current state and capabilities of the main projects (stars, activity, license, what they do)

### Takeaway
The most-starred projects split into three groups. (a) ML/quant research platforms: Qlib + RD-Agent, FinRL/FinRL-X, FreqAI, TensorTrade. (b) LLM multi-agent "analyst" frameworks: TradingAgents, ai-hedge-fund, FinRobot, Vibe-Trading. (c) Financial LLMs and data: FinGPT, OpenBB. Star counts are huge (TradingAgents ~110k, ai-hedge-fund ~64k), but star counts measure hype, not trading performance. Most of these projects say outright that they are for research or education. Only one, FinRL-X, publishes a paper-trading record, and it is self-reported. None publishes an audited live record.

### Cited Findings
**Star counts and activity (GitHub search, 2026-10-10):**
- microsoft/qlib: 49,255 stars, 7,775 forks, 489 open issues, created 2020. Describes itself as an "AI-oriented Quant investment platform" supporting supervised learning, market-dynamics modelling and RL, "now equipped with RD-Agent to automate R&D" — [GitHub](https://github.com/microsoft/qlib)
- Qlib README warns about an "Unreleased breaking change: artifact loading" and that "`main`, and tagged/PyPI releases may differ". This means main is moving ahead of the PyPI releases — [Qlib README](https://github.com/microsoft/qlib/blob/main/README.md)
- microsoft/RD-Agent: 14,883 stars, created April 2024. LLM agents automate factor mining and model optimisation. Its paper, R&D-Agent-Quant (arXiv 2505.15155), was accepted to NeurIPS 2025 — [GitHub](https://github.com/microsoft/RD-Agent)
- RD-Agent claim (self-reported, in the README): "at a cost under $10, RD-Agent(Q) achieves approximately 2× higher ARR than benchmark factor libraries while using over 70% fewer factors". This is a backtest on stock markets (Qlib's datasets), not live trading — [RD-Agent README](https://github.com/microsoft/RD-Agent)
- TauricResearch/TradingAgents: 110,456 stars, 21,266 forks, Apache-2.0, last push 2026-10-03, paper arXiv 2412.20138 — [GitHub](https://github.com/TauricResearch/TradingAgents)
- TradingAgents release history (README "News"): v0.2.0 (Feb 2026), then v0.3.x and v0.4.0 (Aug 2026, "look-ahead / point-in-time fixes across FRED macro, social sentiment, and the decision-log memory"), v0.5.0 (Sep 2026, "point-in-time integrity across every dated path"), v0.5.2 ("backtests that see only data published by each analysis date") and v0.6.0 (Oct 2026). Disclaimer: "designed for research purposes… not intended as financial, investment, or trading advice." — [TradingAgents README](https://github.com/TauricResearch/TradingAgents)
- TradingAgents architecture: separate Fundamentals, Sentiment (news headlines, StockTwits, Reddit), News and Technical analysts, then a bull/bear researcher debate, a Trader, a Risk team and a Portfolio Manager. It runs on LangGraph and supports multiple providers (OpenAI, Anthropic, Gemini, Bedrock, Ollama and others) — [TradingAgents README](https://github.com/TauricResearch/TradingAgents)
- Forks of TradingAgents are also popular: hsliuping/TradingAgents-CN has 32,234 stars, and simonlin1212/TradingAgents-astock has 3,658 stars (A-shares) — [GitHub search](https://github.com/hsliuping/TradingAgents-CN), [GitHub](https://github.com/simonlin1212/TradingAgents-astock)
- virattt/ai-hedge-fund: 63,925 stars, 11,226 forks, created Nov 2024 — [GitHub](https://github.com/virattt/ai-hedge-fund)
- ai-hedge-fund README: "This project is for **educational** purposes only and is not intended for real trading or investment." "Note: the system does not actually make any trades." — [README](https://github.com/virattt/ai-hedge-fund/blob/main/README.md)
- AI4Finance-Foundation: FinGPT 21,393 stars; FinRL 16,613 stars (308 open issues); FinRobot 8,197 stars; FinRL-Trading (rebranded "FinRL-X") 3,800 stars; FinRL-Meta 1,947 stars; FinRL_Crypto 204 stars — [GitHub org search](https://github.com/AI4Finance-Foundation)
- FinRL-X (arXiv 2603.21330) is pitched as an "AI-native", "weight-centric" infrastructure. The target portfolio-weight vector is the only interface between strategy and execution, and the same weights run through backtest and live execution. It integrates with Alpaca for live and paper trading, with pre-trade risk checks — [FinRL-Trading README](https://github.com/AI4Finance-Foundation/FinRL-Trading)
- FinGPT: lightweight LoRA fine-tunes of open LLMs. The README claims "less than $300 per fine-tuning", against roughly $3M for BloombergGPT. It released a sentiment model (Aug 2023) and FinGPT-Forecaster (Nov 2023, Dow-30, Llama-2-7B LoRA). The news section's most recent model releases date from 2023 — [FinGPT README](https://github.com/AI4Finance-Foundation/FinGPT)
- OpenBB: 74,061 stars, now described as "Open Data Platform for analysts, quants and AI agents". The search returned the repo under the owner name "openbq-org/OpenBB" (unexpected; possibly an org rename, not verified) — [GitHub](https://github.com/OpenBB-finance/OpenBB)
- freqtrade/freqtrade: 55,197 stars, only 30 open issues, which suggests very active maintenance — [GitHub](https://github.com/freqtrade/freqtrade)
- FreqAI (the ML module inside Freqtrade) was published in JOSS: "FreqAI: generalizing adaptive modeling for chaotic time-series market forecasts", Caulk et al., JOSS 7(80) 4864, Dec 2022. It is a framework for "live deployments of adaptive modeling" with self-adaptive retraining. The paper covers the framework and reports no returns — [JOSS](https://joss.theoj.org/papers/10.21105/joss.04864)
- tensortrade-org/tensortrade: 7,196 stars, Apache-2.0. An RL framework. Its README lists a NumPy<2.0 pin as a known install issue — [GitHub](https://github.com/tensortrade-org/tensortrade)
- asavinov/intelligent-trading-bot: ML signal generation (feature generators, then trained models, then an aggregated "intelligent indicator", then a threshold signal). It supports Binance and Yahoo data only, and periodic retraining makes its backtests "more difficult". It runs a public Telegram signal channel (t.me/intelligent_trading_signals, BTC at 1-min frequency). That channel is the closest thing to a public forward record, but no performance statistics are published — [README](https://github.com/asavinov/intelligent-trading-bot)
- Newer 2026 LLM-agent repos: HKUDS/Vibe-Trading has 35,113 stars (MIT, created April 2026, "Your Personal Trading Agent", MCP and multi-agent). The-Swarm-Corporation/AutoHedge has 6,246 stars. OpenByteInc/QuantDinger has 12,622 stars — [GitHub](https://github.com/HKUDS/Vibe-Trading), [GitHub search](https://github.com/The-Swarm-Corporation/AutoHedge)

### Inferences
- Star growth is fastest for LLM "analyst-team" repos (TradingAgents went from 0 to 110k stars in under two years). They produce research reports and buy/hold/sell ratings, mostly for equities on a daily timeframe. None of them is a production execution engine for leveraged crypto perpetuals.
- The maintained, production-grade execution codebases are still the classical bots (Freqtrade, Hummingbot at 20k stars, Jesse). Their ML layer (FreqAI) is optional.
- TradingAgents has shipped repeated look-ahead fixes (v0.3.1, v0.4.0, v0.5.0, v0.5.2, all in 2026). These are an admission that backtests run on earlier versions could see future data. Any results produced before v0.5 should be discounted.

### Gaps
- I could not retrieve exact star counts or last-release dates for intelligent-trading-bot, FinMem (pipiku915/FinMem-LLM-StockTrading) or FinAgent. The GitHub API was blocked for non-session repos, and those repos did not appear in the search results.
- Licenses were not confirmed in this session for qlib, FinRL, FinGPT, ai-hedge-fund, Freqtrade or OpenBB. Only TradingAgents (Apache-2.0), Vibe-Trading (MIT) and TensorTrade (Apache-2.0) were confirmed.
- OpenBB's agent features and the "openbq-org" owner name were not verified.

## 2. Live or paper track records: what is real?

### Takeaway
Credible live results come almost entirely from public LLM competitions and live benchmarks, and they are poor. Nof1's Alpha Arena used real money on Hyperliquid. In Season 1, 4 of 6 frontier LLMs lost 30-63% in about two weeks. In Season 1.5 (US stock tokens), only one model was profitable. Academic live benchmarks (LiveTradeBench, AI-Trader) report weak returns and weak risk management for most models. The only open-source project with a published paper-trading record is FinRL-X: +19.76% from Oct 2025 to Mar 2026 on Alpaca paper. That record is self-reported, short, and not audited.

### Cited Findings
**Alpha Arena (nof1.ai), Season 1 (18 Oct to 3 Nov 2025):** each model got $10,000 of real money to trade crypto perps on Hyperliquid.
- Winner: Qwen 3 Max with about +22% (one report gives a final account value of $12,231.82). Only two models finished in profit — [GNcrypto](https://www.gncrypto.news/news/qwen-wins-alpha-arena-season-1-with-22-percent-returns/)
- Reported final losses: Claude Sonnet 4.5 −30.8%, Grok 4 −45.3%, Gemini 2.5 Pro −56.7%, GPT-5 −62.7%. Qwen3 Max had +22.3% with a 30.2% win rate over 43 trades — [MEXC blog](https://blog.mexc.com/news/race-against-time-how-ai-models-battled-live-crypto-markets-in-alpha-arena). (Secondary crypto media; DeepSeek, the other profitable model, is not quantified here. Verify on nof1.ai.)
- Overtrading: Gemini 2.5 Pro reportedly made about 238 trades (about 13 a day) and paid about $1,331 in fees, roughly 13% of capital — [iWeaver blog](https://iweaver.ai/blog/alpha-arena-ai-trading-season-1-results) (a blog, unverified)
- Nof1 founder Jay Azhang said the models showed consistent biases that persisted across many prompt iterations, and that "LLMs don't really handle numerical time series data very well" — reported via [Bloomberg Línea](https://www.bloomberglinea.com/mercados/puede-la-ia-reemplazar-a-operadores-de-wall-street-concursos-revelan-los-limites/) and [Wallstreetcn](https://wallstreetcn.com/articles/3771681)

**Alpha Arena, Season 1.5 (from 20 Nov 2025, US stock tokens on trade.xyz, Nasdaq-100 names):**
- A "mystery model", later revealed as Grok 4.20, was the only profitable entrant. Reported results conflict: one source says +12.11%, about $10,000 to $12,193 in 14 trading days; another says $4,844 profit across four parallel competitions. GPT-5.1 was reportedly −3.4% and Gemini 3 −5.7%. Season 1 winner Qwen 3 Max reportedly lost up to about 70% — [GNcrypto](https://www.gncrypto.news/news/mystery-model-alpha-arena-season-1-5-winner/), [AIbase](https://news.aibase.com/news/23442), [Aihola](https://aihola.com/article/grok-wins-alpha-arena-trading), [WEEX mid-season](https://www.weex.com/news/detail/alpha-arena-15-season-update-grok-420-maintains-lead-all-other-ai-models-remain-at-a-loss-262786). The figures disagree (for example, a mid-season +22.38% vs +22.27%); verify on nof1.ai.
- A student research paper on Season 1.5 compares constrained and unconstrained environments. It finds that constraints lowered fees, beta and portfolio volatility — [CYSF paper](https://platform.cysf.org/project/f2ba6e31-844d-4237-9609-212e37d0c578/) (a non-peer-reviewed student project)
- One 2026 comparison guide says there has been no public Alpha Arena run since Dec 2025 — [TradeRank](https://www.traderank.ai/blog/alpha-arena-alternatives-2026) (unverified)

**Academic live benchmarks:**
- LiveTradeBench (UIUC, arXiv 2511.03628) streams live prices and news and tested 21 LLMs on US stocks and Polymarket. Its key finding is that high LMArena scores do not imply better trading outcomes — [arXiv](https://arxiv.org/html/2511.03628v1)
- AI-Trader (HKU, arXiv 2512.10971, Dec 2025) is a fully automated live benchmark across US stocks, A-shares and crypto with six LLMs. The authors report that "most agents showed poor returns and weak risk management", and that risk-control capability determines cross-market robustness — [alphaXiv](https://alphaxiv.org/overview/2512.10971v1) (via summary)

**Paper trading from open-source projects:**
- FinRL-X README: an "Ensemble of Rolling Selection + Adaptive Rotation" deployed on Alpaca paper trading from Oct 2025 to Mar 2026 returned **+19.76%** (1.20x), against −2.51% and −4.79% for the two comparison columns. The backtest table shows Sharpe 0.72-1.10 and annualised returns of 14-26% — [FinRL-Trading README](https://github.com/AI4Finance-Foundation/FinRL-Trading). (Self-reported, about 6 months, US equities, paper only. The benchmark labels were not visible in the extract.)
- intelligent-trading-bot publishes live signals on a public Telegram channel, but no aggregated performance — [README](https://github.com/asavinov/intelligent-trading-bot)
- ai-hedge-fund: "the system does not actually make any trades" — [README](https://github.com/virattt/ai-hedge-fund/blob/main/README.md)

### Inferences
- The only real-money, side-by-side LLM evidence (Alpha Arena) covers short windows (about 2 weeks), uses n=1 per model and has no repeated seeds. The winners changed between seasons: the S1 winner Qwen lost about 70% in S1.5. That pattern looks like variance, not skill.
- Overtrading and fees were the dominant loss mechanism in Alpha Arena. This matches the Claw bot's own history (588 real trades, gross −11 USDC against 85.94 USDC in fees).

### Gaps
- I could not open nof1.ai directly (blocked), so the official per-model final numbers, trade counts and fees are not confirmed. All Alpha Arena figures come from secondary media.
- I found no Season 2 or 2026 Alpha Arena results.
- No independent audit (exchange statements, verified track-record platforms) exists for any of these open-source projects.

## 3. Critical evidence: look-ahead bias, LLM training-data leakage, overfitting

### Takeaway
Since 2025 a body of critical papers has converged on one conclusion: alpha reported by LLM trading agents is mostly an artefact. Its sources are short single windows, test periods that fall inside the model's training data (memorisation), survivorship and data-snooping, and unmodelled costs. When papers re-test after the training cutoff, over long horizons, or net of costs, returns shrink by 50-72% or fall below buy-and-hold.

### Cited Findings
- **Profit Mirage** (arXiv 2510.07920): re-tests agents on data after the backbone LLM's training cutoff. "Total Return decay ranges from 50.18% (TradingAgents) to 71.85% (FinMem)". FinMem shows the most severe degradation; FinAgent is slightly more resilient, which the authors attribute to tool use — [arXiv](https://arxiv.org/html/2510.07920v1) (via summary; its test windows, Q2-Q3 2021 and Q3-Q4 2024, are themselves short)
- **FINSABER** (Li, Kim, Cucuringu, Ma; arXiv 2505.07078, v1-v5): runs backtests over about 20 years (2000-2024) and 100+ symbols, controlling for survivorship, look-ahead and data-snooping. "Previously reported LLM advantages deteriorate significantly under broader cross-section and over a longer-term evaluation." LLM strategies are "overly conservative in bull markets… overly aggressive in bear markets". The authors call for prioritising "trend detection and regime-aware risk controls over mere scaling of framework complexity" — [arXiv](https://arxiv.org/html/2505.07078v5)
- FINSABER's table lists the original evaluation windows of FinMem and FinAgent as about 6 months each, on 5 and 6 symbols respectively — [arXiv](https://arxiv.org/html/2505.07078v5) (via summary; verify against the original papers)
- A survey of LLM trading agents (arXiv 2408.06361) found the **median test period is only 1.3 years**, with dates often chosen arbitrarily. It warns that a "short and single backtesting period may diminish the credibility of the results" — [arXiv](https://arxiv.org/pdf/2408.06361) (via summary)
- **The Alpha Illusion** (arXiv 2605.16895, 16 May 2026): argues that "reported alpha from end-to-end LLM trading agents should not be treated as deployment evidence". It says current evidence "cannot yet distinguish robust predictive ability from temporal contamination, unmodeled frictions, short-window Sharpe uncertainty". It proposes a P1-P6 reporting protocol and a modular alternative in which LLMs serve only as information interfaces, with separate calibration, risk and execution modules — [alphaXiv](https://www.alphaxiv.org/abs/2605.16895v1)
- Alpha Illusion reproduction of TradingAgents (2025-2026, realistic costs): Sharpe fell from 0.43 gross to 0.22 net, and the agent underperformed buy-and-hold on 4 of 5 stocks — reported via [alphaXiv overview](https://www.alphaxiv.org/overview/2605.16895) and German-language summaries (not confirmed from the PDF)
- A community critique of the TradingAgents paper: the paper is cited as claiming 26.62% cumulative return and Sharpe 8.21 on AAPL (2024-06-19 to 2024-11-19), with buy-and-hold losing 5.23%. The author's recomputation finds AAPL actually rose about 9% in that window. The author flags a 0.91% max drawdown as implausible, notes that costs are not modelled, and points to look-ahead Issue #203 in the repo — [DEV Community](https://dev.to/trow126/the-most-starred-llm-trading-paper-claims-buy-and-hold-lost-523-it-actually-gained-912-1jj6) (a single blog; the paper window and Issue #203 were not verified by me)
- Memorisation: GPT-4o can recall S&P 500 closing prices within its training window with high accuracy (citing Lopez-Lira et al.). Memorisation makes forecasting ability "non identified" — [MemGuard-Alpha, arXiv 2603.26797](https://arxiv.org/pdf/2603.26797) (via summary)
- Mitigations under study: FinCAD (arXiv 2605.24564) uses context-aware decoding to suppress memorised outcomes; BlindTrade (arXiv 2603.17692) anonymises tickers. "The Self Driving Portfolio" (arXiv 2604.02279) notes that obfuscation "does not remove information encoded in the model's parameters" — [FinCAD](https://arxiv.org/pdf/2605.24564), [BlindTrade](https://arxiv.org/html/2603.17692), [Self Driving Portfolio](https://arxiv.org/pdf/2604.02279)
- Look-Ahead-Bench (Benhenda, 2026) reportedly compares in-training and post-training periods and finds better in-sample performance, consistent with memorisation — via [HedgeFundAlpha](https://hedgefundalpha.com/education/your-llms-alpha-might-be-mere-memorization/) (arXiv ID not found)

### Inferences
- Any LLM-agent backtest whose test window falls before the backbone model's knowledge cutoff should be treated as contaminated by default. With frontier models, the cutoff is often recent, which leaves very little clean out-of-sample data.
- Classical ML (Qlib, FreqAI, intelligent-trading-bot) avoids the memorisation problem, since its models are trained from scratch on the user's own data. It still faces ordinary overfitting and data-snooping, and FreqAI's rolling retraining is the standard mitigation.
- RD-Agent's "2× ARR" is an in-sample-style backtest on Chinese/US equity datasets. Automated factor mining is itself a data-snooping engine unless held-out periods are strictly enforced.

### Gaps
- I did not read the full Alpha Illusion or Profit Mirage PDFs. The exact numbers above should be verified there.
- I found no independent reproduction of RD-Agent(Q)'s claims, and no critique specific to FreqAI's live performance.

## 4. Which components are worth it for a practical retail bot, and what LLMs cost in the loop

### Takeaway
For a small, fee-sensitive retail crypto-perp bot, the evidence favours cheap, deterministic components: regime and trend detection, robust feature pipelines with rolling retraining (FreqAI-style), and hard risk and frequency limits. LLMs are best kept out of the per-trade decision loop. At most, use one as a slow, low-frequency filter or reviewer (news/sentiment veto, daily risk review), with its decisions logged and evaluated only on post-cutoff data. Per-call cost and latency (seconds to minutes per decision, about $0.20-0.80 per multi-agent ticker analysis) make LLMs uneconomic at hourly scans over dozens of pairs with a few-hundred-USDC account.

### Cited Findings
- FINSABER concludes that the priority should be "trend detection and regime-aware risk controls over mere scaling of framework complexity" — [arXiv 2505.07078](https://arxiv.org/html/2505.07078v5)
- AI-Trader finds that risk-control capability determines robustness across markets — [alphaXiv](https://alphaxiv.org/overview/2512.10971v1)
- The Alpha Illusion recommends using LLMs only as "information interfaces", with separate calibration, risk and execution modules — [alphaXiv](https://www.alphaxiv.org/abs/2605.16895v1)
- In Alpha Arena, low-frequency, disciplined models beat overtraders, and fees ate about 13% of capital for Gemini 2.5 Pro — [MEXC blog](https://blog.mexc.com/news/race-against-time-how-ai-models-battled-live-crypto-markets-in-alpha-arena), [iWeaver](https://iweaver.ai/blog/alpha-arena-ai-trading-season-1-results)
- LLMs "don't really handle numerical time series data very well" (Nof1 founder) — [Bloomberg Línea](https://www.bloomberglinea.com/mercados/puede-la-ia-reemplazar-a-operadores-de-wall-street-concursos-revelan-los-limites/)
- FreqAI provides adaptive retraining, feature engineering and outlier detection inside a mature execution bot (Freqtrade), with a JOSS paper — [JOSS](https://joss.theoj.org/papers/10.21105/joss.04864)
- TradingAgents itself now ships a news/sentiment analyst that screens social posts by stance. Its developers had to fix look-ahead bugs specifically in social sentiment and macro feeds (v0.4.0), so sentiment features are easy to leak — [TradingAgents README](https://github.com/TauricResearch/TradingAgents)
- FinGPT shows a cheap route to a domain sentiment classifier (LoRA fine-tune for under $300 claimed). Its released sentiment model dates from 2023 — [FinGPT README](https://github.com/AI4Finance-Foundation/FinGPT)
- **Cost:** a single TradingAgents analysis with a gpt-4o deep-think model, gpt-4o-mini quick-think and one debate round is estimated at about **$0.20-$0.80 per ticker**, and doubling debate rounds roughly doubles the cost — [Railway template](https://railway.com/deploy/tradingagents-by-tauric-research-open-source-multi-agent-stock-analysis--trading-agents) (a vendor estimate, not a benchmark)
- **Latency:** TradingAgents' `propagate()` is synchronous per ticker-date, and sweeps are typically sharded across processes — [apisrouter guide](https://apisrouter.com/fil/for-tradingagents) (a reseller page; no measured minutes per run found). v0.5.2 added "parallel analysts for a faster analysis" — [README](https://github.com/TauricResearch/TradingAgents)
- RD-Agent(Q) reports a full factor/model research run "at a cost under $10". That is an offline research cost, not an in-loop cost — [RD-Agent README](https://github.com/microsoft/RD-Agent)

### Inferences
- Cost arithmetic for a Claw-like bot (40 pairs, hourly scan): 40 × 24 = 960 analyses a day. At $0.20-0.80 each that is about **$190-770 a day** in LLM spend, against a capital of about 300 USDC. In-loop multi-agent LLMs are clearly uneconomic at this scale. Even a single cheap-model call per candidate signal (only when the technical score passes) would need to cost cents or less to make sense.
- Components worth considering for the Claw bot, ordered by evidence and cost:
  1. Regime/trend detection and a regime-aware risk overlay. FINSABER and AI-Trader both point here, and the bot already has Markov/ADX/HTF filters.
  2. Trade-frequency and fee discipline. This lesson is the same from Alpha Arena and from the bot's own data.
  3. A FreqAI-style rolling-retrained classifier as an extra score input, but only if it is validated walk-forward with fees.
  4. An LLM as a low-frequency veto or reviewer (macro/news event check a few times a day, or a daily post-mortem of trades), not as a signal generator. Log its vetoes and measure them in paper mode before trusting them.
- Not worth it: end-to-end LLM traders, multi-agent "debate" pipelines per trade, deep-RL portfolio agents (FinRL/TensorTrade) for a single-account crypto-perp bot (no credible live evidence, heavy overfitting risk), and any project whose headline numbers come from pre-cutoff backtests.

### Gaps
- I found no rigorous study isolating the value of LLM news sentiment as a *filter* (rather than a signal) on crypto perps, net of fees.
- I found no measured latency figures (seconds per call or minutes per full multi-agent run) for TradingAgents or ai-hedge-fund with current models.
- Current per-token prices for 2026 models were not collected. The cost estimate above uses gpt-4o-era pricing from a vendor page.
