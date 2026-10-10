# Proven systematic strategies: published evidence, costs, open-source code and anti-overfitting practice

Research notes, 2026-10-10. Context: a multi-asset retail bot (crypto, stocks, ETFs, forex) with small capital. The current Claw v8 bot has 588 real trades: gross -11.01 USDC, fees 85.94 USDC, net about -97 USDC (figures from the repo's CLAUDE.md).

**Source-quality legend:** [PR] = peer-reviewed journal; [WP] = working paper (SSRN/NBER/BIS/arXiv); [PRAC] = practitioner research (AQR, Man); [BLOG] = blog or secondary summary.

**Tooling limits during this session:**
- Firecrawl returned HTTP 402 (out of credits).
- WebFetch could not resolve several hosts (yale.edu, qoppac.blogspot.com, ideas.repec.org).
- The GitHub API was not enabled.

As a result, many figures below come from search-result abstracts and summaries, not from full paper text. Each one is flagged where this applies.

---

## Q1. Which strategies have durable published evidence? (Sharpe, drawdowns, turnover, decay)

### Takeaway
The best-documented edges are low-frequency, diversified risk premia and anomalies.
- **Strongest:** time-series momentum / trend following, carry, cross-sectional momentum and value, and low-beta.
- **Typical Sharpe:** single-strategy, single-asset-class Sharpe is roughly 0.4–0.8. Diversifying across asset classes lifts it to about 1.0–1.6 gross.
- **Decay:** published anomalies lose about half their return after publication.
- **Crypto:** the evidence is newer and mostly working papers. It is positive for trend and momentum and strong for cash-and-carry / funding basis. None of it covers intraday, high-turnover discretionary-style signals.

### Cited Findings

**Time-series momentum / trend following**
- **Moskowitz, Ooi & Pedersen (2012), "Time Series Momentum", JFE [PR].**
  - Covers 58 liquid futures (equity indices, bonds, commodities, currencies), 1985–2009.
  - A diversified TSMOM portfolio "delivers substantial abnormal returns with little exposure to standard asset pricing factors and performs best during extreme markets."
  - — [SSRN](https://papers.ssrn.com/abstract=2089463); [Quantpedia summary](https://quantpedia.com/strategies/time-series-momentum-effect/)
  - The paper's exact diversified Sharpe was not retrieved (see Gaps).
- **Babu, Levine, Ooi, Pedersen & Stamelos, "Trends Everywhere" [WP/PRAC].** Gross Sharpe of 12-month TSMOM:
  - 1.17 on traditional assets;
  - 1.34 on alternative assets;
  - 0.95 on long-short equity factors;
  - 1.60 combined.
  - These are gross of costs. Do not attribute them to the 2012 paper. — [Quantpedia blog](https://quantpedia.com/time-series-momentum-works-everywhere/)
- **Hurst, Ooi & Pedersen, "A Century of Evidence on Trend-Following Investing" (AQR; Journal of Portfolio Management 2017) [PRAC/PR].**
  - Trend following was profitable over about 135 years starting in 1880, with positive returns in every decade.
  - It had near-zero correlation with stocks and bonds. — [AQR PDF copy](https://oxfordstrat.com/coasdfASD32/uploads/2016/03/A-Century-of-Evidence-on-Trend-Following-Investing.pdf); [TrendFollowing.com copy](https://www.TrendFollowing.com/whitepaper/Century_Evidence_Trend_Following.pdf)
  - **Conflicting secondary Sharpe figures:**
    - [ETF.com/Swedroe](https://www.etf.com/sections/index-investor-corner/swedroe-why-financial-trends-persist) reports Sharpe 0.76 after simulated costs and 2/20 fees, and a weakest decade (from 1919) of +4.1%.
    - [CXO Advisory](https://www.cxoadvisory.com/momentum-investing/trend-following-with-intrinsic-momentum-over-the-very-long-run) cites about 0.4 after fees over 1880–2016 on 67 assets.
    - Unresolved. The likely cause is different paper versions or net/gross definitions.
- **Zarattini, Pagani & Barbon (2025), "Catching Crypto Trends" [WP].**
  - Donchian-channel trend models on a rotating top-20 liquid-coin portfolio.
  - Net-of-fees Sharpe above 1.5 and annualized alpha of 10.8% versus BTC.
  - The paper explicitly proposes portfolio techniques to reduce transaction-cost drag. — [Swiss Finance Institute RP 25-80 (IDEAS)](https://ideas.repec.org/p/chf/rpseri/rp2580.html); [author page](https://abarbon.com/papers/catching-crypto-trends)
- **"A Decade of Evidence of Trend Following Investing in Cryptocurrencies" [WP].** Bitstamp hourly data 2011–2019; vanilla, EMA and DEMA trend rules. Headline numbers not retrieved. — [arXiv 2009.12155](https://ar5iv.labs.arxiv.org/html/2009.12155)
- **Man Group, "In crypto we trend" [PRAC].**
  - Crypto trend following works.
  - Past a certain breadth, transaction costs outweigh the diversification benefit. Their optimum is about 10–15 coins. — [Man Group](https://www.man.com/insights/in-crypto-we-trend)

**Cross-sectional momentum in crypto**
- **Liu, Tsyvinski & Wu, "Common Risk Factors in Cryptocurrency", Journal of Finance 2022, 77:1133–1177 [PR].**
  - Three factors (crypto market, size, momentum) capture the cross-section of expected crypto returns.
  - About 9–10 long-short strategies earn significant excess returns, all explained by this three-factor model. — [SSRN](https://papers.ssrn.com/abstract=3379131); [NBER w25882](https://www.nber.org/papers/w25882.pdf)

**Carry**
- **Koijen, Moskowitz, Pedersen & Vrugt, "Carry", JFE 2018 [PR]** (2nd prize, Fama-DFA 2018).
  - Within-asset-class long-short carry: average Sharpe about 0.7.
  - Diversified across asset classes: Sharpe about 1.1 (working-paper figures).
  - The 2012 slides show 1.41 for current carry and 0.93 for 12-month carry, depending on definition. — [CEPR DP13463](https://repec.cepr.org/repec/cpr/ceprdp/DP13463.pdf); [Koijen slides](https://www.fmg.ac.uk/sites/default/files/2020-08/Ralph-Koijen-slides.pdf); [CBS prize note](https://cbs.dk/node/526518)
- **Schmeling, Schrimpf & Todorov, "Crypto Carry", BIS WP 1087 (2023, revised Oct 2025) [WP].**
  - The BTC/ETH cash-and-carry (long spot, short futures) carry averages above 10% a year, far above carry in equities, bonds, FX or commodities.
  - High carry predicts future crypto crashes.
  - There is evidence of segmentation between crypto exchanges and traditional finance. — [BIS](https://www.bis.org/publ/work1087.htm); [PDF](https://www.bis.org/publ/work1087.pdf)
- **He, Manela, Ross & von Wachter, "Fundamentals of Perpetual Futures" (arXiv 2212.06888, v6 Aug 2024) [WP].**
  - Perpetual-futures deviations from no-arbitrage prices are much larger than in traditional FX.
  - A simple strategy exploiting them earns "large Sharpe ratios even for investors paying the highest trading costs on Binance."
  - This claim is from the v2 abstract; exact Sharpe not retrieved. — [arXiv](https://arxiv.org/abs/2212.06888v6)
- **Practitioner caveat [BLOG].** The spot-long / perp-short funding trade carries funding-reversal, margin and counterparty risk. — [tradingstrategy.ai](https://tradingstrategy.ai/docs/learn/carry-trade.html)

**Low-volatility / low-beta**
- **Frazzini & Pedersen, "Betting Against Beta", JFE 2014 [PR].** US BAB factor Sharpe:
  - 0.78 for 1926–Mar 2012;
  - 0.75 for 1926–2009 in the 2010 draft.
  - Reported as about 2x the value Sharpe and 40% higher than momentum over the same period. — [NBER draft](https://conference.nber.org/confer/2010/BEf10/Frazzini.pdf); [CBS publisher version](https://research-api.cbs.dk/ws/portalfiles/portal/60082899/lasse_heje_pedersen_et_al_betting_against_beta_publishersversion.pdf); [Quantpedia](https://quantpedia.com/strategies/betting-against-beta-factor-in-stocks)

**Dual momentum (Antonacci GEM)**
- **Original test and extension:** GEM was tested on monthly data 1974–2011. Antonacci later extended it to 1950–2018, which created out-of-sample periods 1950–73 and 2012–18.
- **ReSolve replication:** found attractive absolute and risk-adjusted performance in and out of sample, and closely matched the author's numbers. — [Hedge Fund Alpha / ReSolve](https://hedgefundalpha.com/strategies/global-equity-momentum-a-craftsmans-perspective/)
- **Caveats:**
  - [Algo Edge](https://algoedgeinsights.beehiiv.com/p/is-gary-antonacci-s-global-equity-momentum-strategy-robust) warns of some data-mining.
  - Live QuantConnect community variants were described as "not looking good" in their first real out-of-sample period. — [QuantConnect forum](https://www.quantconnect.com/forum/discussion/10039) [BLOG]

**Post-publication decay**
- **McLean & Pontiff, "Does Academic Research Destroy Stock Return Predictability?", Journal of Finance 2016 [PR].**
  - Across 97 predictors, returns are 26% lower out of sample and 58% lower after publication.
  - The 26% is an upper bound on data mining. The remaining ~32 points are attributed to investors trading on the publication. — [Ivey PDF](https://ivey.uwo.ca/media/3775549/pontiff.pdf); [Gwern copy](https://Www.Gwern.net/doc/economics/2016-mclean.pdf)
- **Harvey, Liu & Zhu, "...and the Cross-Section of Expected Returns", RFS 2016 [PR].**
  - Given the number of factors tested, a new factor needs a t-statistic above about 3.0, not 2.0.
  - "Most claimed research findings in financial economics are likely false." — [NBER w20592](https://nber.org/papers/w20592); [SSRN](https://papers.ssrn.com/abstract=2513152)

**Realistic Sharpe expectations (practitioner)**
- **Carver, *Systematic Trading* (2015) [BLOG/book].** Backtested Sharpe ratios of 2–3 usually mean over-fitting. A Sharpe consistently above 1.0 is rarely achieved. — [CXO Advisory book notes](https://www.cxoadvisory.com/big-ideas/a-few-notes-on-systematic-trading)
- **Carver (2025) [BLOG].** Uses about 0.30 as the median Sharpe of a single trend strategy. — [qoppac March 2025](https://qoppac.blogspot.com/2025/03/)

### Inferences
- Every strategy with century-scale or multi-asset peer-reviewed support trades slowly: monthly rebalancing, or trend lookbacks of 1–12 months. None depends on hourly scoring of many indicators. Claw v8's design (1H scan, a 6–7-point score from ~10 indicators, 3–7h holding periods) has no counterpart in this literature.
- Expect live Sharpe to land below 50–75% of the backtested figure, based on McLean & Pontiff's 26–58% decay. A backtest Sharpe of 1.0 implies a realistic live 0.4–0.75 before retail costs.
- For crypto, the two most defensible edges for a small account are:
  1. Daily or slower trend / TSMOM on a handful of liquid coins (Zarattini et al.; Man).
  2. Funding/basis carry (BIS; He et al.).
- Carry needs both spot and perp legs and margin management. It is not directional.

### Gaps
- The exact diversified Sharpe of MOP 2012 and the exact Hurst-Ooi-Pedersen net Sharpe were not retrieved; secondary sources conflict (0.76 vs about 0.4).
- No retrieved turnover figures for the academic strategies.
- No retrieved max-drawdown figures for TSMOM, carry or GEM.
- Asness-Moskowitz-Pedersen "Value and Momentum Everywhere" Sharpe figures were not retrieved.
- Risk parity (e.g., Asness-Frazzini-Pedersen "Leverage Aversion and Risk Parity") was not covered by any search.
- The full tables of the BIS crypto-carry paper (sample period, post-2022 carry levels) were not retrieved. Carry compression after ETF launches is unverified.

---

## Q2. How do transaction costs change the picture for small, frequent traders?

### Takeaway
Costs scale with turnover. Leverage multiplies them as a share of equity, while the edge per trade does not grow.
- **Carver's rule:** spend no more than about one third of expected pre-cost Sharpe on costs, i.e. about 0.10–0.13 Sharpe units a year.
- **Claw v8:** fees (85.94 USDC) were about 7.8x the absolute gross P&L. That alone puts the bot far past any sensible speed limit.

### Cited Findings
- **Carver's "speed limit" [BLOG].**
  - Do not allocate to a trading rule if turnover × cost per trade (in Sharpe units) exceeds the limit.
  - The limit is 0.13 SR units a year; 0.10 or 0.13 depending on the book.
  - The original framing is to spend no more than one third of expected pre-cost returns on costs.
  - With a median trend Sharpe of about 0.30, the 2025 budget is about 0.07 SR a year. — [Scream if you want to go faster (Jan 2023)](https://qoppac.blogspot.com/2023/01/scream-if-you-want-to-go-faster.html); [Fast but not furious (Feb 2023)](https://qoppac.blogspot.com/2023/02/fast-but-not-furious-do-fast-trading.html); [How fast should we trade? (2020)](https://qoppac.blogspot.com/2020/04/how-fast-should-we-trade.html); [March 2025](https://qoppac.blogspot.com/2025/03/)
- **Worked example [BLOG].** At a cost of 0.005 SR per trade on a quarterly-rolled instrument, maximum forecast turnover is about 22 round-trips a year. — [Fast but not furious](https://qoppac.blogspot.com/2023/02/fast-but-not-furious-do-fast-trading.html)
- **Scalping [BLOG].** Carver says the speed-limit idea "can't really be used for very fast strategies." He wrote a dedicated post on scalping-bot feasibility. — [Can I build a scalping bot? (May 2025)](https://qoppac.blogspot.com/2025/05/can-i-build-scalping-bot-blogpost-with.html)
  - Full text could not be fetched (DNS failure), so its conclusions are not recorded here.
- **Crypto breadth [PRAC].** Past about 10–15 coins, crypto trend portfolios lose Sharpe to transaction costs. — [Man Group](https://www.man.com/insights/in-crypto-we-trend)
- **Perp mispricing survives Binance's highest fee tier [WP]**, i.e. that edge is large enough to absorb taker costs. — [He et al.](https://arxiv.org/abs/2212.06888v6)

### Inferences (own arithmetic; the inputs are the user's stated parameters and repo data, not external sources)
- **Break-even per trade:**
  - Taker 0.05% per side gives a 0.10% round-trip on notional.
  - With the paper engine's 0.02% slippage per fill, the round-trip is 0.14%.
  - **The average trade must capture more than 0.10–0.14% of notional just to break even.** That is before funding, which the paper engine does not model.
- **Leverage scales the hurdle against margin, not the edge.**
  - At 6x, a 0.10% notional cost is 0.6% of the margin committed per round-trip (0.84% with slippage).
  - Leverage makes the hurdle larger relative to equity, not easier to clear.
- **Claw v8 realized numbers:**
  - 85.94 USDC fees / 588 trades ≈ 0.146 USDC per trade.
  - At a 0.10% round-trip, that implies an average notional of about 146 USDC.
  - Gross P&L per trade ≈ -0.019 USDC, against a hurdle of +0.146. The signal had no measurable gross edge, and costs then turned it into a large net loss.
  - Fees equal about 29% of the 300 USDC capital.
- **Claw v8 against the speed limit:**
  - Assume a 25%/yr volatility target on 300 USDC: 1 SR unit ≈ 75 USDC a year.
  - Carver's 0.13 SR budget is then about 10 USDC a year in costs.
  - 86 USDC in fees ≈ 1.1 SR units. If the 588 trades took under a year, the annualized figure is higher.
  - That is about 8–10x the speed limit. No published edge with a realistic Sharpe of 0.3–1.0 can carry that cost.
- **Levers, in order of impact:**
  1. Cut turnover by roughly 10x (daily or weekly signals, holding periods of days to weeks).
  2. Use maker/limit orders where fees are lower.
  3. Trade fewer, more liquid instruments.
  4. Size so that each trade's notional is large relative to the minimum fee impact.

### Gaps
- Binance's current USDC-M maker/taker schedule (including any 0% maker promotions) was not verified. Check Binance's fee page before modelling the maker-order benefit.
- No peer-reviewed study was retrieved that quantifies maker vs taker execution for retail crypto bots.
- No retrieved study of retail-bot net performance distributions (e.g., the share of freqtrade users who are profitable).

---

## Q3. Open-source implementations

### Takeaway
- **pysystemtrade** is the most faithful open-source implementation of evidence-based multi-asset trend and carry with volatility targeting and cost modelling.
- **freqtrade and Jesse** are crypto bot frameworks; the strategies are user-written.
- **PyPortfolioOpt and Riskfolio-Lib** handle allocation (risk parity, HRP), not signals.
- **Quantpedia and QuantConnect** provide replications of published anomalies.

### Cited Findings
- **pysystemtrade (Rob Carver)** — open-source futures backtest and live engine built on the *Systematic Trading* framework (trend + carry, forecast scaling, vol targeting, cost-aware "speed limit").
  - Open-sourced in Dec 2015. Andy Geach became primary maintainer in 2024.
  - Moved to the `pst-group` GitHub organisation in Jan 2026.
  - Connects to Interactive Brokers via ib_insync. — [fork/README mirror](https://github.com/thekurz/pysystemtrade); [pst-group mirror](https://backiee.wasmer.app/https_github_com/pst-group/pysystemtrade)
  - Original URL from prior knowledge, not live-verified: https://github.com/robcarver17/pysystemtrade
- **freqtrade** — free, open-source Python crypto bot with backtesting, hyperopt, FreqAI adaptive ML, and Telegram/WebUI control. — [skills directory summary](https://www.skillsdirectory.com/skills/mahmoud20138-freqtrade-bot)
  - Repo (prior knowledge): https://github.com/freqtrade/freqtrade; community strategies at https://github.com/freqtrade/freqtrade-strategies
- **Jesse** — crypto strategy research and trading framework. — [quant-wiki listing](https://lzw.me/doc/quant-wiki/repo/quant_learn/); [fork](https://github.com/movy/jesse)
  - Main repo (prior knowledge): https://github.com/jesse-ai/jesse
- **PyPortfolioOpt and Riskfolio-Lib** — portfolio optimisation libraries. PyPortfolioOpt covers mean-variance, Black-Litterman and Hierarchical Risk Parity. — [awesome-systematic-trading list](https://awesome.ecosyste.ms/lists/paperswithbacktest%2Fawesome-systematic-trading?topic=rust)
  - Repos (prior knowledge): https://github.com/robertmartin8/PyPortfolioOpt, https://github.com/dcajasn/Riskfolio-Lib
- **bt** — Python backtesting for allocation strategies. Repo (prior knowledge): https://github.com/pmorissette/bt
- **QuantConnect** — public community implementations, e.g. Antonacci dual-momentum ETF variants and a Bitcoin regime signal citing Liu & Tsyvinski. — [dual momentum forum](https://www.quantconnect.com/forum/discussion/10039); [BTC regime research](https://www.quantconnect.com/research/21195/bitcoin-regime-signal-for-growth-equities/)
- **Quantpedia** — catalogues strategies with links to source papers (TSMOM, BAB, etc.). — [TSMOM](https://quantpedia.com/strategies/time-series-momentum-effect/); [BAB](https://quantpedia.com/strategies/betting-against-beta-factor-in-stocks)
- **R package `pbo`** — implements Bailey et al.'s CSCV / probability of backtest overfitting. — [CRAN README](https://packages.oit.ncsu.edu/cran/web/packages/pbo/readme/README.html)
- **Curated list** — awesome-systematic-trading (paperswithbacktest), a catalogue of backtesters, live engines and optimisers. — [ecosyste.ms](https://awesome.ecosyste.ms/lists/paperswithbacktest%2Fawesome-systematic-trading?topic=rust)

### Inferences
- **Multi-asset bot (stocks/ETFs/futures/FX via IBKR plus crypto):** the natural reference architecture is pysystemtrade's design:
  - continuous forecasts in place of binary entry scores;
  - forecast diversification across trend speeds plus carry;
  - instrument and portfolio vol targeting;
  - a cost-based veto on fast rules.
- **Crypto-only:** freqtrade gives exchange connectivity, backtest and dry-run. Its out-of-the-box hyperopt is a known overfitting risk, so it should be gated by walk-forward and PBO checks.
- **Allocation layer:** Riskfolio-Lib or PyPortfolioOpt (HRP / risk parity) can set cross-asset-class risk weights.

### Gaps
- Stars, licenses, maintenance status and archived flags were not verified (GitHub API blocked this session). The status of mlfinlab (Hudson & Thames), vectorbt and NautilusTrader was not checked.
- Specific freqtrade trend strategies with documented out-of-sample results were not found.

---

## Q4. Avoiding overfitting: methods and how many trades or how much time to trust results

### Takeaway
Use the following tools:
- combinatorial / purged cross-validation (CSCV/CPCV) to estimate the probability of backtest overfitting;
- a deflated or haircut Sharpe that accounts for the number of trials;
- a t-stat hurdle of about 3, not 2.

Statistically, the time or trade count needed scales with 1/edge². A 100-trade paper test can only detect very large edges.

### Cited Findings
- **Bailey, Borwein, López de Prado & Zhu, "The Probability of Backtest Overfitting", Journal of Computational Finance 20(4), 2017 [PR].**
  - Standard hold-out testing is unreliable for investment backtests.
  - They propose the PBO framework, estimated with combinatorially symmetric cross-validation (CSCV), which gives reasonable PBO estimates with small errors.
  - Keywords include minimum backtest length and performance degradation. — [SSRN](https://papers.ssrn.com/abstract=2326253); [eScholarship PDF](https://escholarship.org/content/qt4w1110bb/qt4w1110bb.pdf); [Risk.net](https://www.risk.net/journal-of-computational-finance/2471206/the-probability-of-backtest-overfitting)
- **Software:** an R implementation exists (`pbo`, which uses Omega by default; the authors used Sharpe). — [CRAN](https://packages.oit.ncsu.edu/cran/web/packages/pbo/readme/README.html)
- **Harvey, Liu & Zhu (RFS 2016) [PR].** t > 3.0 hurdle, p ≈ 0.27%. — [NBER](https://nber.org/papers/w20592)
- **McLean & Pontiff [PR].** Expect up to 26% decay from data mining alone. — [Ivey](https://ivey.uwo.ca/media/3775549/pontiff.pdf)
- **Carver [BLOG/book].** Treat backtest Sharpe above about 1 with suspicion; 2–3 is almost always overfit. — [CXO](https://www.cxoadvisory.com/big-ideas/a-few-notes-on-systematic-trading)

### Inferences (standard statistics, own calculation; no external source retrieved for these exact numbers)
- **Time needed.** The t-stat of an annualized Sharpe is about SR × √years. For t = 2:
  - SR 0.5 needs about 16 years;
  - SR 1.0 needs about 4 years.
  - For t = 3, SR 1.0 needs about 9 years.
  - Live or paper trading over months therefore cannot confirm a realistic edge. It can only catch bugs, execution slippage and gross failures.
- **Trades needed.** Per trade, t ≈ (mean / std of R-multiple) × √N. If the true edge is 0.10R per trade with std about 1R:
  - N ≈ (2 / 0.10)² = 400 trades for t = 2;
  - about 900 trades for t = 3.
  - At an edge of 0.05R: 1,600 trades for t = 2, about 3,600 for t = 3.
- **Implication for Claw v8's paper criterion.** The rule "≥100 paper trades with net > 0" detects at t = 2 only edges of about 0.2R per trade or more.
  - A random signal has a sizeable chance of showing net > 0 over 100 trades.
  - Suggested tighter criterion: require t > 2–3 on net per-trade P&L, plus a fixed rule set with no parameter changes during the test window.
- **Recommended pipeline:**
  1. Write down a hypothesis grounded in the literature (trend, carry).
  2. Log every variant tried (the trial count feeds the deflated Sharpe).
  3. Run walk-forward or CPCV.
  4. Compute PBO.
  5. Apply a deflated or haircut Sharpe.
  6. Paper trade to validate execution and costs, not edge.
  7. Go live at small size.

### Gaps
- The deflated Sharpe ratio paper (Bailey & López de Prado 2014, Journal of Portfolio Management) and *Advances in Financial Machine Learning* (2018, purged k-fold / CPCV) were not retrieved this session. Formulas should be cited from the originals.
- No source was retrieved giving a consensus minimum paper-trading duration.

---

## Q5. Position sizing and risk: vol targeting, Kelly, cross-asset portfolio risk

### Takeaway
- **Volatility targeting** reliably reduces tail events everywhere. It raises Sharpe mainly for risk assets (equities, credit).
- **Kelly / fractional Kelly and portfolio vol targets** (Carver suggests modest annual vol targets) control leverage.
- **Cross-asset allocation** should be risk-based (equal risk / HRP), not capital-based.

### Cited Findings
- **Moreira & Muir, "Volatility-Managed Portfolios", Journal of Finance 72(4):1611–1644, 2017 [PR].**
  - Taking less risk when volatility is high produces large alphas and raises factor Sharpe ratios.
  - Covers market, value, momentum, profitability, ROE, investment and FX carry factors, 1926–2015. — [NBER w22208](https://www.nber.org/papers/22208)
- **Harvey, Hoyle, Korgaonkar, Rattray, Sargaison & Van Hemert, "The Impact of Volatility Targeting", Journal of Portfolio Management Fall 2018 [PR].**
  - The Sharpe gain holds only for risk assets (equities, credit). It is negligible for bonds, FX and commodities.
  - It reduces extreme returns across all asset classes.
  - US equities Sharpe goes from about 0.40 to 0.48–0.51 (secondary summary). — [Duke PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf); [Alpha Architect](https://alphaarchitect.com/volatility-targeting-improves-risk-adjusted-returns/); [Quantpedia](https://quantpedia.com/the-impact-of-volatility-targeting-on-equities-bonds-commodities-and-currencies)
- **Carver's framework [BLOG/book]** sizes each instrument to a fixed share of a portfolio annual vol target. A third-party simulator using his code defaults to 15% vol. — [moontower sim](https://trading-sim.moontowermeta.com/)
  - The 15% figure is a third-party default, not verified as Carver's recommendation.

### Inferences
- Claw v8 sizes by fixed USDC risk to the stop (6 USDC). A vol-targeted alternative works like this:
  - Position notional = (target portfolio vol × capital × instrument weight) / (instrument annualized vol × √number of positions, adjusted for correlation).
  - This automatically de-levers in volatile crypto regimes.
- Use fractional Kelly (≤ 0.5 Kelly) on the estimated Sharpe, and only after the edge is statistically established. With unknown edge, Kelly sizing is undefined and dangerous.
- **Multi-asset:** allocate risk budgets per asset class (e.g., equal risk across crypto, equities/ETFs, FX, and bonds/commodities). Crypto's vol is about 3–4x equities, so equal capital means crypto dominates the risk.

### Gaps
- No primary source on Kelly in trading (e.g., Thorp; MacLean-Thorp-Ziemba) was retrieved.
- Carver's specific recommended vol target (often cited around 20–25% in his books) was not verified this session.
- No retrieved study on cross-asset risk-parity performance for retail-sized portfolios.
