# Community evidence: do open-source trading bots make money live (vs. backtests)?

> **Access note (read first):** I could not reach Reddit directly. reddit.com, old.reddit JSON, the Reddit wiki and every Reddit mirror tried (lr.sudovanilla.org, reddit.sentinel-team.org) were blocked or failed DNS. Hacker News and HN Algolia also failed DNS, Firecrawl had no credits left (HTTP 402), and WebFetch could not resolve dev.to either. Everything below comes from **web search result snippets and summaries**, not full pages I read. No Reddit thread could be opened to check live PnL numbers, dates or capital. Where a thread is cited, only its URL and snippet were seen. Treat all numbers as unverified unless stated otherwise. **I did not invent any Reddit threads to fill the gap.** Missing items are listed under Gaps.

## 1. What do communities say about Freqtrade, NostalgiaForInfinity, Hummingbot, Passivbot, grid/DCA, funding-arb and market-making bots? (live results)

### Takeaway
None of the sources I could reach had a credible, verifiable long-run live track record (dated, with capital and net PnL after fees) for any of these open-source bots. The evidence splits three ways:
- **Self-reported winners.** These are blogs, résumés and vendor pages.
- **Backtest-only claims.** NFI's GitHub pull requests are the main example.
- **Modest or underperforming reports.** Passivbot vs. buy-and-hold, and Hummingbot miners who were "somewhat, though not substantially profitable".

Even the bot projects themselves warn against treating them as money printers.

### Cited Findings
**Freqtrade**
- The official docs say to start in dry-run and not to commit money before you understand how the bot works — [Freqtrade docs](https://www.freqtrade.io/en/stable/) / [bot basics](https://www.freqtrade.io/en/stable/bot-basics/)
- Self-reported case of backtest-vs-forward decay: a strategy won 72% of trades in backtest but only 45% in forward testing. The author blames overfitting and says "if your backtest looks too good, it probably is" and "the transition from backtest to live is where most bots fail". This is a single author; the post headline still calls the bot "profitable" — [DEV: How I built a profitable bot with Freqtrade and Bybit](https://dev.to/trendrider/how-i-built-a-profitable-crypto-trading-bot-with-freqtrade-and-bybit-5g6a); [DEV: Freqtrade Tutorial 2026 (67.9% win rate)](https://dev.to/trendrider/freqtrade-tutorial-2026-how-i-set-up-a-crypto-bot-that-hits-679-win-rate-18i5)
- One builder reported that a hyperopt run of 150 epochs came out about 4x worse out-of-sample than the hand-tuned defaults. The same builder flagged that Freqtrade applies stoploss/ROI to the leveraged profit ratio: a −7% stop at 5x leverage is a −1.4% price move. This source is low-reliability (search snippet only) — [succubuns.com technical deep dive](https://succubuns.com/naughty-bots/a28f5c8e-990f-4849-ae9a-bdd0b0425a73?page=7)
- A claim of "+100% in six months live with Freqtrade" appears only as an unverifiable résumé line — [web3.career profile](https://web3.career/@abrosedon)
- Third-party review caveat: better historical results do not guarantee future performance — [Finestel Freqtrade review 2026](https://finestel.com/blog/freqtrade-review/); [Gainium Freqtrade review](https://gainium.io/review/freqtrade)

**NostalgiaForInfinity (NFI, a Freqtrade strategy)**
- I found no user-reported live PnL. Visible evidence is developer backtest tables in GitHub pull requests. PR #1351 calls the 2022 bear rally the hardest window — [PR #1351](https://github.com/iterativv/NostalgiaForInfinity/pull/1351)
- One futures backtest period showed net PnL of about −59,146 USDT and a closed-trade drawdown of about 66% — [PR #1323](https://github.com/iterativv/NostalgiaForInfinity/pull/1323)
- Raw signal 506 recorded 185 liquidations and −35,423 across ten test windows, including the August 2024 carry unwind — [PR #1310](https://github.com/iterativv/NostalgiaForInfinity/pull/1310)
- PR #1354 has a row labelled "2026 live 97t/+2,350". It is unclear whether that is real live trading. PR titles such as "70 losses down to zero, profit +88%" suggest signals are tuned to specific windows, a classic overfitting pattern — [PR #1354](https://github.com/iterativv/NostalgiaForInfinity/pull/1354)
- Third-party aggregated backtests exist but are not live — [freqst.com NFI Next](https://www.freqst.com/strategy/fd554bdf4f1aa315284f0f5bee980a038539e2873d17c963717dcd0a5f28abf902dabdbdf1c5c/); [strat.ninja NFIX](https://strat.ninja/overview.php?strategy=NostalgiaForInfinityX); [NFI repo](https://github.com/iterativv/NostalgiaForInfinity)

**Passivbot**
- Described as grid/martingale-like. One user reported about 6.3% annualised over 100 days, while holding BTC returned about 16% in the same period. Per the review, results are "mixed" and the bot "misses larger market moves" — [Gainium Passivbot review](https://gainium.io/review/passivbot)
- The README says "used at one's own risk". The bot realises small losses to unstick positions, caps drawdown against peak balance, and in newer versions has the TWEL exposure enforcer. A March 2026 review says it suits advanced users who actively monitor risk — [Gainium Passivbot blog](https://gainium.io/blog/passivbot); [GitHub releases](https://github.com/enarjord/passivbot/releases)

**Hummingbot / market making**
- Hummingbot's own academy lists "Hummingbot is a money printer" and "an optimal config that prints money exists" as beginner misconceptions. The author reports "losing 20% in 20 minutes" and has also seen miners "profit 100% in a few months" — [Hummingbot: Top Beginner Misconceptions about Market Making](https://docs.hummingbot.org/academy-content/top-beginner-misconceptions-about-market-making/)
- A liquidity miner interviewed by Hummingbot was "somewhat, though not substantially profitable". Hummingbot itself says it does not guarantee profits — [Interview with David Salter](https://hummingbot.org/blog/interview-with-liquidity-miner-david-salter/)
- The early 2019 "10–50% annually" figure for liquidity mining came from **simulations**, not measured results — [Hummingbot 2019 archive](https://docs.hummingbot.org/blog/archive/2019/)
- The community market-making experiment asked whether retail "would get destroyed by more sophisticated players". The write-up focuses on volume, not net profit — [Does community-based market making work?](https://hummingbot.org/blog/does-community-based-market-making-work/)

**Grid / DCA bots**
- First-hand six-month BTC grid on Gate.io: in rallies the bot sells into strength and you miss the upside. In sustained declines it keeps buying ("a grid bot never knows the trend changed"), building unrealised losses and liquidation risk — [DEV: I ran a Gate.io BTC grid bot for 6 months](https://dev.to/joe_hans_6c082d6c1caf189f/i-ran-a-gateio-btc-grid-bot-for-6-months-real-returns-and-3-fatal-mistakes-2i1p)
- Pionex's FAQ shows that "grid profit" can differ from what you keep. Leftover coins are booked at the exit price, so floating losses can appear later — [Pionex grid FAQ](https://intercom.help/pionex/en/articles/15500905-grid-trading-bot-faq)
- Hands-on 2026 test of Bybit's built-in bots: grid netted about $2.84 over 12 cycles after fees, DCA about $1.80. These are tiny and short — [coinspot Bybit bot review](https://coinspot.io/en/reviews/bybit-trading-bot/)

**Funding-rate arbitrage**
- Vendor blogs give an average delta-neutral funding-arb yield of 19.26% for 2025 (14.39% in 2024), with max drawdown under 2%. The figures repeat across articles and probably trace to one source. They are unaudited — [Medium: Funding Rate Arbitrage in 2026](https://medium.com/@arbitrageghost/funding-rate-arbitrage-in-2026-the-complete-guide-with-real-calculations-40e6cf341e52); [Gate Learn 2025](https://www.gate.com/learn/articles/perpetual-contract-funding-rate-arbitrage/2166)
- Practical capital minimum is cited as $10k–$50k, so that returns beat operational overhead; at small size, fees dominate — [VoiceOfChain academy](https://voiceofchain.com/academy/crypto-funding-rate-arbitrage-bot); [youcanbuildthings substack](https://youcanbuildthings.substack.com/p/crypto-funding-rate-arbitrage-bot)
- The often-cited "115.9% in 6 months, 1.92% max DD" is a backtest across 60 scenarios, not typical retail live performance — same sources as above

**Older Hacker News evidence (2018, outside the 2023–26 window)**
- "Ask HN: Anyone making money through algorithmic trading?" Replies are mixed. One commenter lost about $100k; another argued the market is negative-sum, so any abstract strategy has negative expected excess return; another cited a person who made millions on options algorithmically, second-hand — [HN 16922538](https://news.ycombinator.com/item?id=16922538)
- "Ask HN: What algorithms are you using to make money?" One commenter argues published strategies get arbitraged away and that sellers profit more from selling — [HN 16400169](https://news.ycombinator.com/item?id=16400169)

### Inferences
- The pattern matches survivorship bias. Public "it works" claims are self-reported, short, or backtests. The projects' own docs (Freqtrade, Hummingbot, Passivbot) are the most cautious sources.
- The NFI PR culture of "N losses down to zero" per signal is a strong sign of curve-fitting to known windows. Its backtest drawdowns (66%, mass liquidations) show tail risk on futures.
- Grid, martingale and DCA bots (Passivbot, exchange grids) earn from range-bound chop and lose or underperform in trends. The one data point found (6.3% vs 16% BTC hold) fits that.
- Funding arbitrage and market making are the closest thing to a structural edge, but they need capital, low fees or rebates, and execution quality. Small accounts are disadvantaged.

### Gaps
- No Reddit threads (r/algotrading, r/freqtrade, r/hummingbot, r/CryptoCurrency, r/Daytrading, r/quant, r/options, r/Forex) could be opened. Specific live-result posts with dates, capital and net PnL could not be found or verified.
- Nothing found for Jesse, OctoBot, or Passivbot user threads with numbers.
- Freqtrade and Hummingbot Discord summaries were not found publicly.

## 2. Most cited reasons bots fail live (overfitting, fees, slippage, regime change, look-ahead, leverage) — and small accounts destroyed by fees

### Takeaway
The sources I could reach consistently name three causes of failure:
- **Overfitting.** Backtest win rates fall sharply in forward testing.
- **Fees and slippage.** These are decisive for high-frequency strategies on small accounts.
- **Regime change.** Grids and DCA break in trends; trend systems bleed in chop.

Leverage then turns these into liquidations.

### Cited Findings
- Overfitting: a 72% backtest win rate became 45% in forward testing — [DEV trendrider](https://dev.to/trendrider/how-i-built-a-profitable-crypto-trading-bot-with-freqtrade-and-bybit-5g6a). Hyperopt was 4x worse out-of-sample than defaults — [succubuns snippet](https://succubuns.com/naughty-bots/a28f5c8e-990f-4849-ae9a-bdd0b0425a73?page=7)
- Fees: "most bots don't fail because the strategy is bad; they fail because fees eat an edge that was only a few bps wide". A taker round trip on futures is estimated at about 10–12 bps. Worked example: 50 trades a day on a $200 balance with 0.25% fees plus 0.15% slippage per round trip costs more than $4 a day, which is near or below break-even — [trade-reclaim: Are crypto trading bots profitable? The fee math](https://trade-reclaim.com/en/blog/are-crypto-trading-bots-profitable) (vendor-ish, illustrative)
- Bots pay the same maker/taker fees as manual traders. Limit or maker orders can reduce fees or earn rebates — [coincub](https://coincub.com/are-crypto-trading-bots-worth-it-2025); [arbitragescanner](https://arbitragescanner.io/blog/trading-bot-strategies-how-to-automate-profitable-cryptocurrency-trading)
- Win rate is not profitability: a 70% win rate with a 5% average loss can still lose. A 25% drawdown needs about 34% to recover — [Packt, Zero to Hero in Crypto Trading ch. 8](https://www.packtpub.com/en-us/product/zero-to-hero-in-cryptocurrency-trading-8-9781837631285/chapter/chapter-8-automated-trading/coding-a-strategy-in-freqtrade)
- Regime: a grid bot "keeps buying the dip that never ends" — [DEV grid 6 months](https://dev.to/joe_hans_6c082d6c1caf189f/i-ran-a-gateio-btc-grid-bot-for-6-months-real-returns-and-3-fatal-mistakes-2i1p). Grids are ineffective when price leaves the range — [Gainium grid bot](https://gainium.io/grid-bot)
- Leverage / liquidation: NFI futures backtests show mass liquidations in crash windows, such as the August 2024 carry unwind — [NFI PR #1310](https://github.com/iterativv/NostalgiaForInfinity/pull/1310). Automation "scales small configuration mistakes into bigger drawdowns when volatility spikes" — [coinspot Bybit review](https://coinspot.io/en/reviews/bybit-trading-bot/)
- Edge decay (Reddit thread, Feb 2026, via snapshot snippet only): "edge isn't harder to find; it's harder to keep. Simple strategies still work, but only in the regimes they were built for"; patterns get arbitraged faster once obvious — [Reddit snapshot (sentinel-team mirror)](https://reddit.sentinel-team.org/posts/1r8q206/snapshots/2026-02-21T03%3A33%3A30.48473Z)

### Inferences
- For a ~200–300 USDC account trading futures at taker fees, each round trip costs about 0.10–0.12% of notional. At 6x leverage that is about 0.6–0.7% of margin per trade. Any strategy with a small average edge per trade gets wiped out. This matches the project's own internal data in CLAUDE.md, which is not external evidence: 588 live trades, gross −11.01 USDC, fees 85.94, net about −97 USDC.
- Look-ahead bias was not specifically cited in the sources reached. The usual Freqtrade-community answer is that dry-run and forward testing catch it, but I could not find a source for that.

### Gaps
- No specific Reddit thread on "small account destroyed by fees on futures" could be opened or quoted. The fee evidence comes from vendor and blog sources.
- No source reached quantified slippage on Binance USDC-M perps for retail size.

## 3. Strategies the community sees as durable retail edge vs. dead

### Takeaway
Sources favour diversified trend following across futures (modest Sharpe, deep drawdowns) and combining uncorrelated strategies. Crypto is seen as less efficient than mature markets. Simple published patterns are seen as decaying fast. I could not confirm an explicit r/algotrading consensus list of "dead" strategies.

### Cited Findings
- Backtest of trend following on 23 futures (2000–2022): about 12.5% annualised, 39.9% max drawdown, Sharpe about 0.65. An ensemble with mean reversion raises Sharpe because the two are weakly correlated — [Price Action Lab 2023](https://www.priceactionlab.com/Blog/2023/02/combining-trend-following-mean-reversion/)
- Trend following profits in directional moves and loses in chop; mean reversion is the opposite, so pairing them diversifies across regimes — [Algomatic Trading](https://www.algomatictrading.com/post/why-two-strategies-are-better-than-one-trend-following-mean-reversion); [Algomatic dual-edge](https://www.algomatictrading.com/post/dual-edge-diversification-trend-following-on-commodities-mean-reversion-on-equity-index-futures)
- Antonacci (via Concretum): mean reversion should complement trend following, not replace it — [Concretum substack](https://concretumgroup.substack.com/p/gary-antonacci-from-dual-momentum)
- Managed-futures trend following: high returns with high drawdowns — [Virtus intro to managed futures (PDF)](https://www.virtus.com/assets/files/71d/an_introduction_to_managed_futures_4756.pdf)
- Retail structural advantages: small size means little market impact, and retail traders are free from mandate constraints, so they can stay uncorrelated with funds — [QuantStart: Can algorithmic traders still succeed at the retail level?](https://www.quantstart.com/articles/Can-Algorithmic-Traders-Still-Succeed-at-the-Retail-Level/)
- Reddit (Feb 2026 snapshot snippet): edge persists in pairs or ensembles, and "crypto is still fairly new and less efficient" — [Reddit snapshot](https://reddit.sentinel-team.org/posts/1r8q206/snapshots/2026-02-21T03%3A33%3A30.48473Z). An r/quant thread from Jul 2024, "does retail quant trading exist", is mostly opinion — [r/quant mirror](https://lr.sudovanilla.org/r/quant/comments/1dvx838/does_retail_quant_trading_exists) (not opened)
- Portfolio-of-edges framework for retail — [Harbourfront Quant: Do retail traders have an edge?](https://harbourfrontquant.substack.com/p/do-retail-traders-have-an-edge)
- Prediction-market arbitrage shows extreme compression: only 0.51% of Polymarket wallets made more than $1,000 profit from Apr 2024 to Dec 2025 — [Simple Mondays](https://simplemondays.com/technology/are-polymarket-trading-bots-actually-profitable-the-math-behind-2026-s-predictio/)

### Inferences
- For a small crypto-futures account, the edges the sources treat as more durable are slow, low-turnover trend or momentum, where fees are a small share of each trade's expected move, and funding carry (delta-neutral) with enough capital. High-turnover intraday signal stacking is the profile most exposed to fee drag and overfitting.
- Retail market making on major pairs is widely seen as being out-competed. Even Hummingbot frames it as risky; any profit tends to be on illiquid pairs or comes from liquidity-mining rewards.

### Gaps
- Could not access the r/algotrading wiki/FAQ or Quant.StackExchange threads. A first-hand "dead strategies" consensus is not sourced.

## 4. Community views on commercial-but-open bots and paid strategy/signal sellers

### Takeaway
The recurring heuristic is "if it worked consistently, they wouldn't need to sell it". Red flags are near-100% win rates, sock-puppet promotion, and get-rich promises. Even the open-source projects' own materials disclaim guaranteed profit.

### Cited Findings
- A post warning about an "algo" spammed from multiple accounts: a 100% win rate does not exist, and "if you could consistently make money with this strategy you wouldn't be here" — [Teamblind](https://www.teamblind.com/post/microsoft-dwt1-is-spamming-about-this-algo-to-scam-ppl-w-multiple-accounts-7dhjuxg2)
- HN commenter: published strategies get arbitraged away, and sellers make more money from selling than from trading — [HN 16400169](https://news.ycombinator.com/item?id=16400169)
- TradingView author: no bot wins all the time, and there will be losing months. If someone promises riches, "run… you will pay twice" — [TradingView: Bots for everybody](https://tr.tradingview.com/chart/ALICEUSDTPERP/xjexYvTH-1-Bots-for-everybody)
- Examples of sales pages with unverifiable claims ("permitted us to quit the 9to5") — [algotrade.gumroad](https://algotrade.gumroad.com/l/AutoTrading); [forexblue.gumroad](https://forexblue.gumroad.com/l/fzfog)
- Hummingbot itself disclaims guaranteed profits — [Hummingbot interview](https://hummingbot.org/blog/interview-with-liquidity-miner-david-salter/)

### Inferences
- "Proven" claims for bots or strategies should require verifiable, exchange-linked live statements over at least 6–12 months, net of fees. None of the open-source bots reviewed publishes such an audited record.

### Gaps
- Could not retrieve Reddit threads on specific signal-seller scams (Telegram/Discord groups, 3Commas or Cryptohopper marketplaces), or the 3Commas API-key leak discussions.
- No Elite Trader threads were retrieved.
