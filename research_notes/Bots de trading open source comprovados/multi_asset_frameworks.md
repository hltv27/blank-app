# Multi-Asset Open-Source Algorithmic Trading Frameworks (state as of 2026-10-10)

Method note: I pulled the GitHub metrics (stars, archived flag, last push, license, language) in one batch through the GitHub repository search API on 2026-10-10. I pulled the latest release versions and dates from the PyPI JSON API (`pypi.org/pypi/<pkg>/json`) on the same day. Where only one source was available, that is flagged. Some sites could not be fetched from this environment (DNS failures): nautilustrader.io, lumibot.lumiwealth.com, quantconnect.com, esma.europa.eu. For those I used the GitHub README pages and search snippets instead. Firecrawl was out of credits.

## Current state of each framework (active vs dead, hard metrics)

### Takeaway
Clearly active in Oct 2026, with commits in the last weeks and recent PyPI releases: NautilusTrader, LEAN, Lumibot, vectorbt (OSS), vnpy, RQAlpha, Qlib, alpaca-py, MetaTrader5, StockSharp, freqtrade, hummingbot, jesse. Effectively unmaintained: Backtrader (last push Aug 2024, last PyPI release Apr 2023) and Blankly (last push Dec 2024, last PyPI release a 2023 beta). ib_insync is archived; its successor ib_async is active. OANDA's official v20-python SDK is stale (last push 2021, last PyPI release 2018). pysystemtrade has moved to the `pst-group` org.

### Cited Findings
**Metrics table (GitHub API via MCP search, 2026-10-10; PyPI JSON API same day)**

| Project | Stars | Archived? | Last push | License | Core lang | Latest PyPI release (date) |
|---|---|---|---|---|---|---|
| [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) (crypto only, reference) | 55,197 | No | 2026-10-10 | GPL-3.0 | Python | 2026.9 (2026-09-29) — [PyPI](https://pypi.org/project/freqtrade/) |
| [microsoft/qlib](https://github.com/microsoft/qlib) | 49,255 | No | 2026-10-08 | MIT | Python | pyqlib 0.9.7 (2025-08-15) — [PyPI](https://pypi.org/project/pyqlib/) |
| [vnpy/vnpy](https://github.com/vnpy/vnpy) (VeighNa) | 45,792 | No | 2026-10-06 | MIT | Python | 4.5.0 (2026-10-06) — [PyPI](https://pypi.org/project/vnpy/) |
| [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | 29,796 | No | 2026-10-10 | LGPL-3.0 | Rust (+Python) | 1.231.0 (2026-08-02) — [PyPI](https://pypi.org/project/nautilus_trader/) |
| [mementum/backtrader](https://github.com/mementum/backtrader) | 23,449 | No (but dormant) | 2024-08-19 | GPL-3.0 | Python | 1.9.78.123 (2023-04-19) — [PyPI](https://pypi.org/project/backtrader/) |
| [QuantConnect/Lean](https://github.com/QuantConnect/Lean) | 21,947 | No | 2026-10-09 | Apache-2.0 | C# | lean CLI 1.0.229 (2026-08-28) — [PyPI](https://pypi.org/project/lean/); quantconnect-stubs published 2026-10-09 |
| [hummingbot/hummingbot](https://github.com/hummingbot/hummingbot) (crypto, reference) | 20,374 | No | 2026-10-06 | Apache-2.0 | Python | — |
| [quantopian/zipline](https://github.com/quantopian/zipline) (original) | 20,145 | No (dead, Quantopian closed) | 2024-02-13 | Apache-2.0 | Python | — |
| [StockSharp/StockSharp](https://github.com/StockSharp/StockSharp) | 10,860 | No | 2026-10-10 | NOASSERTION (custom) | C# | n/a (.NET) |
| [polakowo/vectorbt](https://github.com/polakowo/vectorbt) (OSS) | 9,327 | No | 2026-10-09 | NOASSERTION (custom) | Python | 1.1.2 (2026-10-09) — [PyPI](https://pypi.org/project/vectorbt/) |
| [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | 9,031 | No | 2026-08-05 | AGPL-3.0 | Python | 0.6.6 (2026-07-22) — [PyPI](https://pypi.org/project/backtesting/) |
| [jesse-ai/jesse](https://github.com/jesse-ai/jesse) (crypto) | 8,623 | No | 2026-10-05 | MIT | Python | — |
| [ricequant/rqalpha](https://github.com/ricequant/rqalpha) | 6,818 | No | 2026-10-10 | NOASSERTION | Python | 6.4.1 (2026-10-09) — [PyPI](https://pypi.org/project/rqalpha/) |
| [nkaz001/hftbacktest](https://github.com/nkaz001/hftbacktest) | 4,871 | No | 2025-12-23 | MIT | Rust | 2.4.4 (2025-12-10) — [PyPI](https://pypi.org/project/hftbacktest/) |
| [pst-group/pysystemtrade](https://github.com/pst-group/pysystemtrade) | 3,548 | No | updated 2026-10-10 | (not retrieved) | Python | not on PyPI (installed from git) |
| [erdewit/ib_insync](https://github.com/erdewit/ib_insync) | 3,283 | **Yes (archived)** | 2024-03-14 | BSD-2 | Python | — |
| [blankly-finance/blankly](https://github.com/blankly-finance/blankly) | 2,480 | No (dormant) | 2024-12-30 | LGPL-3.0 | Python | 1.18.25b0 (2023-07-23) — [PyPI](https://pypi.org/project/blankly/) |
| [barter-rs/barter-rs](https://github.com/barter-rs/barter-rs) (newer, Rust) | 2,335 | No | 2026-08-24 | MIT | Rust | — |
| [Lumiwealth/lumibot](https://github.com/Lumiwealth/lumibot) | 2,115 | No | 2026-10-10 | GPL-3.0 | Python | 4.6.18 (2026-10-10) — [PyPI](https://pypi.org/project/lumibot/) |
| [stefan-jansen/zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded) | ~2.0k (page) | No | (not retrieved) | Apache-2.0 | Python | 3.1.1 (2025-07-19) — [PyPI](https://pypi.org/project/zipline-reloaded/) |
| [ib-api-reloaded/ib_async](https://github.com/ib-api-reloaded/ib_async) | 1,754 | No | 2026-08-19 | BSD-2 | Python | 2.1.0 (2025-12-08) — [PyPI](https://pypi.org/project/ib_async/) |
| [alpacahq/alpaca-py](https://github.com/alpacahq/alpaca-py) | 1,545 | No | 2026-10-10 | Apache-2.0 | Python | 0.44.0 (2026-08-11) — [PyPI](https://pypi.org/project/alpaca-py/) |
| [oanda/v20-python](https://github.com/oanda/v20-python) | 267 | No (stale) | 2021-08-01 | MIT | Python | v20 3.0.25.0 (2018-09-28) — [PyPI](https://pypi.org/project/v20/) |
| [quantrocket-llc/quantrocket-client](https://github.com/quantrocket-llc/quantrocket-client) | 32 | No | 2026-09-17 | Apache-2.0 | Python | (client only; the platform itself is commercial) |
| MetaTrader5 (MetaQuotes, closed source on PyPI) | n/a | n/a | n/a | MIT (per PyPI) | Python wrapper | 5.0.6231 (2026-09-27) — [PyPI](https://pypi.org/project/MetaTrader5/) |
| [wilsonfreitas/awesome-quant](https://github.com/wilsonfreitas/awesome-quant) (list) | 30,022 | No | 2026-10-10 | — | — | — |

**Per-project notes**
- NautilusTrader has a Rust-native core with Python as the "control plane for strategy logic, configuration, and orchestration" (PyO3 bindings for the v2 runtime). The README says it aims for a bi-weekly release schedule and warns that "breaking changes can occur between releases" — [GitHub README](https://github.com/nautechsystems/nautilus_trader)
- NautilusTrader integrations (all marked stable in the README): AX Exchange, Betfair, Binance, Bybit, Coinbase, Databento (data), Deribit, Derive, dYdX, Hyperliquid, Interactive Brokers (multi-venue brokerage), Kraken, Lighter, Lighter on Robinhood, OKX, Polymarket, Tardis (data). There is no OANDA, MT5, Alpaca, Tradier or Tradovate adapter in the list. The README says it covers "traditional markets (FX, equities, futures, options)" (through IB) — [GitHub README](https://github.com/nautechsystems/nautilus_trader)
- Conflict to flag: the README says bi-weekly releases, yet the newest version on PyPI is 1.231.0 from 2026-08-02, about 10 weeks old, while the repo was pushed on 2026-10-10. This may reflect a v2/Rust packaging transition. Not verified — [PyPI](https://pypi.org/project/nautilus_trader/)
- LEAN: Apache-2.0; "event-driven, professional-caliber algorithmic trading platform"; `lean live` CLI command "Start live trading a project locally using Docker" — [GitHub README](https://github.com/QuantConnect/Lean)
- LEAN CLI live brokerage menu (21 entries): Paper Trading, Interactive Brokers, Tradier, OANDA, Bitfinex, Coinbase Advanced Trade, Binance, Zerodha, Samco, Terminal Link, Trading Technologies, Kraken, Charles Schwab, Bybit, TradeStation, Alpaca, Tastytrade, Eze, dYdX, Webull, Public — [QuantConnect docs (search snippet)](https://www.quantconnect.com/docs/v2/lean-cli/datasets/brokerages); [OANDA/CFD page](https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/cfd-and-forex-brokerages); [Tradier page](https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/tradier). I could not fetch the page directly.
- The LEAN CLI reportedly "requires a paid tier organization membership". This comes from a search summary only and the page could not be fetched, so treat it as unconfirmed — [QuantConnect docs](https://www.quantconnect.com/docs/v2/lean-cli/datasets/brokerages)
- Lumibot brokers: Alpaca, Interactive Brokers (TWS and REST), Tradier, Schwab, Tradovate, TopstepX futures (ProjectX), Bitunix, Polymarket, plus "selected CCXT crypto paths". The README says: "Lumibot does not claim blanket support for every CCXT exchange." Asset classes: "stocks, options, crypto, futures, forex, indexes, and prediction contracts." Backtest data: Yahoo, Alpaca, IBKR REST, ThetaData, Polygon/Massive, DataBento, Tradier, Schwab, CCXT (Kraken, Binance, KuCoin, BitMEX, Bybit, OKX), pandas/CSV — [GitHub README](https://github.com/Lumiwealth/lumibot)
- zipline-reloaded: not archived; README mentions "Release 3.05 … compatible with Numpy 2.0"; quickstart is backtest-only and there is no live trading. Zipline was historically Quantopian's backtest and live engine — [GitHub](https://github.com/stefan-jansen/zipline-reloaded). The latest PyPI release is 3.1.1 (2025-07-19), so there has been no release in about 15 months — [PyPI](https://pypi.org/project/zipline-reloaded/)
- pysystemtrade: "In January 2026 Rob moved pysystemtrade to a new github 'organisation'" (pst-group, "owned by Andy and Rob"); "In 2024 Andy Geach took over as primary maintainer"; "uses the ib_async library to connect to interactive brokers"; "A fully automated system for futures trading (for interactive brokers)" — [GitHub README](https://github.com/pst-group/pysystemtrade)
- vectorbt PRO is a paid membership that includes a private GitHub repo. Plans are monthly, 12-month or lifetime, and commercial use requires contacting the vendor — [vectorbt.pro FAQ](https://vectorbt.pro/faq). Official pages position it as backtesting and research. A third-party review says vectorbt "does not natively support live trading" — [stork.ai](https://www.stork.ai/en/vectorbt) (secondary source); [vectorbt.pro](https://vectorbt.pro/)
- MetaTrader5 Python package: Windows-only. On Linux it needs Wine plus an RPC bridge (`mt5linux`: Wine + rpyc + Windows Python, default port 18812) — [mt5linux PyPI](https://pypi.org/project/mt5linux); [tiloye/mt5linux](https://github.com/tiloye/mt5linux)
- Newcomers seen: barter-rs, "Open-source Rust framework for building event-driven live-trading & backtesting systems" (2,335 stars, last push 2026-08-24, MIT) — [GitHub](https://github.com/barter-rs/barter-rs). It is crypto-focused, based on its topics.

### Inferences
- Backtrader is a no-go for new builds. It is still the 2nd-most-starred Python backtester, but has had no commits for over 2 years and no PyPI release for 3.5 years. Its IB integration relied on the old IbPy. Blankly is effectively dead (its last PyPI release is a 2023 beta).
- ib_insync to ib_async: any framework or code still importing `ib_insync` should migrate. pysystemtrade has already done so (per its README).
- Qlib, vectorbt, backtesting.py and zipline-reloaded are research and backtest tools, not live multi-broker execution frameworks. They suit the research layer, not the "trade everything" execution layer.
- vnpy and RQAlpha are very active, but their broker ecosystems center on Chinese markets (CTP and similar). This is from prior knowledge and was not re-verified here. They are unlikely to suit an EU retail trader.

### Gaps
- Exact last-release dates on GitHub (vs PyPI) for NautilusTrader and LEAN: the GitHub REST releases endpoint was blocked in this session.
- License of pysystemtrade and the last push of zipline-reloaded were not retrieved.
- The exact license texts behind StockSharp, vectorbt and RQAlpha's "NOASSERTION" were not verified. vectorbt is widely reported as Apache-2.0 with Commons Clause, but that is unverified here.
- I did not verify which brokers StockSharp or QuantRocket support (QuantRocket is a commercial platform, IB-centric per prior knowledge, unverified).
- No Backtrader2 fork (`backtrader2/backtrader`) showed up in the GitHub search, so its status is unverified.

## Backtest–live parity, event-driven vs vectorized, realism (fees, slippage, funding, partial fills)

### Takeaway
True same-code parity, with an event-driven engine, exists in NautilusTrader, LEAN and Lumibot. Of these, NautilusTrader makes the strongest explicit claim, sharing execution semantics and the time model between backtest and live. Vectorized tools (vectorbt, backtesting.py, Qlib) give no live parity. pysystemtrade has its own backtest and production stack for IB futures.

### Cited Findings
- NautilusTrader: "The same strategy and execution-algorithm code can run across backtest and live systems, reducing deployment divergence". It also warns that live adds "venue, transport, timing, persistence" effects a simulation may not reproduce. It features "Identical strategy implementations between research and live deployment" — [GitHub README](https://github.com/nautechsystems/nautilus_trader)
- Nautilus docs claim the same execution semantics and time model in backtest and live — [nautilustrader.io institutional (search snippet)](https://nautilustrader.io/institutional/); [docs overview](https://docs.nautilustrader.io/concepts/overview.html)
- Lumibot: "The strategy class can stay the same. The code that starts it must select a backtest or a broker run"; "Build agents that run identically in backtests and live trading" — [GitHub README](https://github.com/Lumiwealth/lumibot)
- LEAN: event-driven, modular and pluggable, with `lean backtest` and `lean live` on the same project — [GitHub README](https://github.com/QuantConnect/Lean). The README itself does not state a parity guarantee in so many words.
- zipline-reloaded: backtest only (no live) — [GitHub](https://github.com/stefan-jansen/zipline-reloaded)
- vectorbt: vectorized research engine, no native live trading (secondary source) — [stork.ai](https://www.stork.ai/en/vectorbt)

### Inferences
- These come from prior knowledge, not re-verified this session; treat them as claims to check in the docs.
  - NautilusTrader models fill and latency through configurable fill and latency models. It also handles L1/L2/L3 order-book data, partial fills, and venue-specific fee models, with funding for perps in its crypto adapters.
  - LEAN has pluggable fee, slippage and fill models per brokerage model, plus margin and buying-power models.
  - Lumibot's realism is simpler: flat or percentage fees and basic slippage.
- For a Binance-Futures-first user, funding-rate simulation matters. The user's own paper engine currently does not simulate funding. NautilusTrader is the most likely of the three to handle perps natively. This needs confirmation in its Binance adapter docs.

### Gaps
- I could not fetch the Nautilus or LEAN docs pages on fill, fee, slippage and funding models (DNS failure). Fee, funding and partial-fill handling is therefore not verified with a primary-source citation in these notes.

## Production use evidence

### Takeaway
Evidence is mostly self-reported. LEAN powers QuantConnect's own live-trading service (the brokerages are wired into its CLI and cloud). NautilusTrader sells an institutional tier but names no clients. Rob Carver trades his own money with systematic futures methods, and his IB-connected system is pysystemtrade, though the README frames it as his backtesting environment.

### Cited Findings
- Nautilus institutional page: it offers a direct relationship for "proprietary trading firms, hedge funds, market makers, asset managers, family offices". No named users or case studies were found — [nautilustrader.io/institutional](https://nautilustrader.io/institutional/) (vendor claim)
- LEAN: brokerages are integrated into the QuantConnect CLI deployment and documented per broker — [QuantConnect docs](https://www.quantconnect.com/docs/v2/lean-cli/datasets/brokerages); a 2026 third-party review says it integrates with "over 20 brokers" — [newyorkcityservers.com](https://newyorkcityservers.com/blog/quantconnect-review) (secondary)
- Carver "trades and invests with his own money using the methods … in his books" — [Trend Following Radio ep. 1184](https://www.trendfollowing.com/2023/05/28/ep-1184-robert-carver-interview-with-michael-covel-on-trend-following-radio/). He is ex-AHL and left the industry in 2013, per his Harriman House author profile — [Harriman House](https://harriman-house.com/authors/profile/robertcarver/17482). A self-written EliteTrader profile says he trades "about 100 futures on a fully automated basis" and lists the IB API — [EliteTrader](https://elitetrader.com/et/members/globalarbtrader.487113/about) (undated, self-reported)
- pysystemtrade README: "Backtesting environment that Rob uses to test all the strategies in his various books" + "fully automated system for futures trading (for interactive brokers)" — [GitHub](https://github.com/pst-group/pysystemtrade)

### Inferences
- pysystemtrade is the best-documented "one serious individual runs this live" case: IB futures, daily or slower frequency, with years of blog commentary on qoppac.blogspot.com. That blog was not fetched in this session. However, it is futures-only and IB-only, so it is not a multi-asset "trade everything" engine.

### Gaps
- No independent verification of named institutional NautilusTrader users.
- Carver's blog posts on live performance were not retrieved (search returned none).

## EU (Portugal) retail broker access and regulatory constraints

### Takeaway
The realistic multi-asset path for a Portuguese retail trader is IBKR: stocks, UCITS ETFs, futures, options and FX through one API, usable from NautilusTrader, LEAN, Lumibot and pysystemtrade. US-domiciled ETFs are blocked by PRIIPs/KID; the fix is UCITS equivalents. ESMA caps retail CFD/FX leverage at 30:1 down to 2:1. Alpaca's EU presence (via the WealthKernel acquisition, CNMV-licensed) is B2B/platform-oriented, and direct Portuguese retail eligibility is unconfirmed. MT5 brokers work, but the Python API is Windows-only.

### Cited Findings
- PRIIPs: US ETF issuers generally don't produce KIDs, so EEA and UK retail clients cannot buy them, and IBKR is required to block trading in a PRIIP without a KID. Workarounds: EU/UCITS equivalents, CFDs on large US ETFs issued by IBKR's EU entities, or reclassification as a professional client — [IBKR PRIIPs Regulation](https://ibkb.interactivebrokers.com/node/2993); [IBKR PRIIPs Overview](https://ibkb.interactivebrokers.com/de/node/3324). Existing holders can hold or sell but not buy more — [justETF](https://www.justetf.com/ch-en/news/etf/us-domiciled-etfs.html)
- ESMA 2018 product intervention for retail CFDs: leverage caps from 30:1 (major FX pairs) through 20:1, 10:1 and 5:1 down to 2:1 (crypto); margin close-out rule per account; negative balance protection; standardised risk warning; binary options banned for retail — [ESMA](https://www.esma.europa.eu/node/84933); [FinanceFeeds](https://financefeeds.com/esma-bans-offering-binary-options-retail-investors-introduces-restrictions-cfds/). Per my prior knowledge, these became permanent national measures (including in Portugal by CMVM), but that is not verified here.
- Alpaca Europe: Alpaca completed its acquisition of WealthKernel (announced 2026-04-21), giving it UK and EU licensed brokerage and custody. The EU entity is WealthKernel Spain A.V., S.L.U., CNMV reg. no. 328. EU equities: Xetra live, Euronext and LSE to follow. The offering is aimed at platforms integrating via API — [Alpaca blog](https://alpaca.markets/blog/alpaca-expands-into-europe-and-launches-european-equities-trading/); [alpaca.markets/eu](https://alpaca.markets/eu); [FintechFutures](https://www.fintechfutures.com/press-releases/alpaca-expands-into-europe-with-wealthkernel-acquisition-and-launch-of-european-equities-trading)
- OANDA: FTMO acquired OANDA (from CVC Asia Fund) and said local operations are unchanged (Mar 2026) — [Finance Magnates tag page](https://www.financemagnates.com/tag/oanda/). The v20 API offers live (`api-fxtrade.oanda.com`) and practice endpoints — [Celigo docs](https://docs.celigo.com/hc/en-us/articles/360038548412-Set-up-a-connection-to-OANDA). The official Python SDK has been stale since 2018 (PyPI) / 2021 (GitHub) — [PyPI v20](https://pypi.org/project/v20/)
- MT5 Python API is Windows-only; Linux requires Wine + rpyc bridge — [mt5linux](https://pypi.org/project/mt5linux)

### Inferences
- With ~200–300 USDC of capital, the minimums matter. IBKR futures contract sizes (even micros) and options margin will constrain diversification. Rob Carver's books discuss minimum capital for futures diversification, which was not verified here. Crypto perps on Binance remain the most capital-efficient venue for small accounts, with up to 2:1 for crypto CFDs under ESMA. Binance perps are not CFDs, though, and the BNFCR account has its own restrictions.
- If the user's MT5 broker is the FX/CFD route, they would need a Windows host or Wine on the VPS. LEAN, Nautilus and Lumibot have no native MT5 adapter (based on the lists above).

### Gaps
- I could not confirm whether Portuguese individuals can open Alpaca Europe accounts directly.
- I could not confirm OANDA Europe's current acceptance of Portuguese residents. OANDA Europe's regulator and entity were not verified this session.
- The CMVM (Portugal) national implementation of the ESMA CFD measures was not verified.

## Recommendation: migrating a custom Python Binance-Futures bot to a multi-asset architecture

### Takeaway
NautilusTrader is the best fit as the core engine. It has stable native Binance and Bybit adapters plus Interactive Brokers for stocks, ETFs, futures, options and FX. It is event-driven, makes an explicit same-code backtest/live claim, is actively developed (29.8k stars, pushed 2026-10-10), uses LGPL-3.0, and has a Rust core with a Python strategy API. Lumibot is the simpler fallback if ease matters more than rigor, but its crypto/Binance-Futures support is only via "selected CCXT paths". LEAN is strongest on broker breadth (21 brokers including OANDA, Tradier, Alpaca, Binance, Bybit), but its core is C# and local live trading via the CLI may require a paid QuantConnect tier.

### Cited Findings
- Nautilus integrations include Binance, Bybit, IB (multi-venue), Databento and Tardis, all marked stable — [GitHub README](https://github.com/nautechsystems/nautilus_trader)
- Nautilus warns of breaking changes between releases — [GitHub README](https://github.com/nautechsystems/nautilus_trader)
- Lumibot CCXT caveat: "does not claim blanket support for every CCXT exchange" — [GitHub README](https://github.com/Lumiwealth/lumibot)
- LEAN's 21-brokerage CLI list and possible paid-tier requirement — [QuantConnect docs](https://www.quantconnect.com/docs/v2/lean-cli/datasets/brokerages)

### Inferences
- Migration risk specific to this user: their Binance account is BNFCR (EU). It rejects `STOP_MARKET reduceOnly=true`, requires `closePosition=true` via `/fapi/v1/algoOrder`, and allows only one closePosition stop per symbol (per the project's CLAUDE.md). Any framework's Binance adapter, Nautilus's included, will likely assume standard reduce-only stops, so the user must test stop placement on BNFCR in sandbox or paper mode before going live. This may need a custom adapter override.
- Suggested architecture:
  - Start with NautilusTrader backtests on Binance perps using the existing strategy logic.
  - Run Nautilus paper/sandbox in parallel with the current paper bot to compare.
  - Add an IB adapter later for UCITS ETFs and micro futures.
  - Keep vectorbt or backtesting.py only as a fast research and screening layer.
- The LGPL-3.0 license (Nautilus) permits private use without open-sourcing strategies. GPL-3.0 (Lumibot) is also fine for private, non-distributed use. AGPL (backtesting.py) only matters if offered as a network service.

### Gaps
- I did not verify Nautilus's handling of Binance USDC-M perps or BNFCR-specific order restrictions. The adapter docs were unreachable.
- No benchmark numbers (throughput or latency) were verified for any framework.
