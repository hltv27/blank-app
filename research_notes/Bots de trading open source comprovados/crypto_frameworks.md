# Frameworks open source de bots de trading cripto: maturidade, funcionalidades e provas de desempenho real (estado em Out 2026)

Nota de método: as métricas do GitHub abaixo foram obtidas em tempo real a 2026-10-10 através da API de pesquisa do GitHub (ferramenta GitHub MCP `search_repositories`, objectos completos do repo). A API REST/`gh` por repositório e os endpoints de releases ficaram bloqueados para repos fora do âmbito desta sessão, por isso as datas de release vêm das páginas públicas `/releases` (WebFetch). Os domínios freqtrade.io, jesse.trade e octobot.cloud não resolveram por DNS a partir deste ambiente; as afirmações da documentação vêm por isso dos ficheiros markdown da documentação/README publicados em raw.githubusercontent.com (a mesma fonte que gera os sites de documentação) e do código-fonte. O Firecrawl estava sem créditos. **O número de contribuidores activos não foi verificado em nenhum repo** (endpoint bloqueado).

## Que projectos estão realmente maduros e mantidos activamente em 2026?

### Conclusão
Freqtrade é claramente o líder (55k estrelas, releases mensais até 2026.9, commit no próprio dia). Hummingbot (20k, v2.17.0 em Set 2026), Jesse (8.6k), OctoBot (6.7k), Superalgos (5.7k) e Passivbot (2.1k, v8.1.0 em Ago 2026) estão vivos. Gekko e Zenbot estão **arquivados** (mortos). Krypto-trading-bot está parado desde Dez 2024. Gunbot é comercial/fechado. CCXT é uma biblioteca, não um bot. NautilusTrader é o novato de maior peso (29.8k estrelas, núcleo em Rust).

### Factos citados
Tabela com dados ao vivo do GitHub (2026-10-10) — [GitHub search API, repo:freqtrade/freqtrade etc.](https://github.com/search?q=repo%3Afreqtrade%2Ffreqtrade&type=repositories):

| Repo | Estrelas | Forks | Arquivado | Último push | Licença | Linguagem | Issues abertas |
|---|---|---|---|---|---|---|---|
| [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) | 55,197 | 11,394 | não | 2026-10-10 | GPL-3.0 | Python | 30 |
| [ccxt/ccxt](https://github.com/ccxt/ccxt) (biblioteca) | 44,310 | 8,871 | não | 2026-10-08 | MIT | Python/JS/multi | 739 |
| [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | 29,796 | 3,956 | não | 2026-10-10 | LGPL-3.0 | Rust (+Python) | 125 |
| [hummingbot/hummingbot](https://github.com/hummingbot/hummingbot) | 20,374 | 4,978 | não | 2026-10-06 | Apache-2.0 | Python | 182 |
| [askmike/gekko](https://github.com/askmike/gekko) | 10,174 | 3,778 | **SIM** | 2020-02-16 | MIT | JavaScript | 0 |
| [jesse-ai/jesse](https://github.com/jesse-ai/jesse) | 8,623 | 1,249 | não | 2026-10-05 | MIT | Python | 9 |
| [DeviaVir/zenbot](https://github.com/DeviaVir/zenbot) | 8,260 | 1,963 | **SIM** | 2022-02-14 | MIT | JS (HTML marcado) | 295 |
| [Drakkar-Software/OctoBot](https://github.com/Drakkar-Software/OctoBot) | 6,703 | 1,282 | não | 2026-10-08 | GPL-3.0 | Python | 170 |
| [Superalgos/Superalgos](https://github.com/Superalgos/Superalgos) | 5,684 | 6,003 | não | 2026-10-08 | Apache-2.0 | JavaScript | 118 |
| [freqtrade/freqtrade-strategies](https://github.com/freqtrade/freqtrade-strategies) | 5,537 | 1,450 | não | 2026-09-08 | GPL-3.0 | Python | 12 |
| [ctubio/Krypto-trading-bot](https://github.com/ctubio/Krypto-trading-bot) | 3,719 | 826 | não | **2024-12-15** | NOASSERTION | C++ | 64 |
| [iterativv/NostalgiaForInfinity](https://github.com/iterativv/NostalgiaForInfinity) | 3,460 | 760 | não | 2026-10-09 | GPL-3.0 | Python | 86 |
| [enarjord/passivbot](https://github.com/enarjord/passivbot) | 2,122 | 676 | não | 2026-10-10 | Unlicense | Python (+Rust) | 80 |

Outros repos activos (pesquisa no GitHub `crypto trading bot stars:>1500 pushed:>2026-06-01`, ordenada por estrelas): Haehnchen/crypto-trading-bot 3,536 (TypeScript); alsk1992/CloddsBot 2,954 (criado em **Jan 2026**, "agente de trading com IA", construído sobre Claude — sem histórico); asavinov/intelligent-trading-bot 1,879 (ML); c9s/bbgo 1,673 (Go); rodrigo-brito/ninjabot 1,626 (Go, Binance) — [GitHub search](https://github.com/search?q=crypto+trading+bot&type=repositories&s=stars).

- Releases do Freqtrade: 2026.9 (29 Set), 2026.8 (31 Ago), 2026.7 (31 Jul) — cadência mensal. A 2026.9 acrescenta verificação de desvio do relógio face à exchange, dados de open interest, avisos de liquidação configuráveis em futuros, corrige o funding fee a ser reposto a 0 e corrige o tratamento da carteira em bots cross-margin — [freqtrade releases](https://github.com/freqtrade/freqtrade/releases)
- Releases do Hummingbot: v2.17.0 (22 Set), v2.16.0 (29 Jul; acrescentou suporte a ordens post-only LIMIT_MAKER para Bitget, backtesting na Hyperliquid, CLI `hbot`), v2.15.0 (16 Jun) — [hummingbot releases](https://github.com/hummingbot/hummingbot/releases)
- Releases do Passivbot: v8.1.0 (10 Ago 2026), v8.0.0 (14 Jul, ruptura: estratégia canónica `trailing_martingale`, runtime partilhado em Rust para live/backtest/optimizer, novo "Equity Hard Stop Loss"), v7.11.0 (13 Mai 2026) — [passivbot releases](https://github.com/enarjord/passivbot/releases)
- Gunbot: não encontrei nenhuma release open source do núcleo; é vendido com licença paga (ex.: "Standard license $199 → $99 lifetime"); só ferramentas de terceiros (gunbot-quant, gunthy-gui) são open source — [OpenHub gunbot-quant](https://www.openhub.net/p/gunbot-quant); [Geekflare Gunbot](https://geekflare.com/recommends/gunbot); [gunthy-gui](https://github.com/Sjakil/gunthy-gui/releases)
- O README do OctoBot diz que a nova beta é "trabalho em curso" e que o backtesting está "only available in manual OctoBots" (a versão mais recente corre por omissão em modo node) — [OctoBot README](https://raw.githubusercontent.com/Drakkar-Software/OctoBot/master/README.md)

### Inferências
- O número de estrelas mede popularidade, não rentabilidade. O Gekko continua com 10k estrelas apesar de arquivado desde 2020.
- O baixo número de issues abertas do Freqtrade (30) face às 55k estrelas sugere uma triagem activa — um bom indicador de maturidade.
- O "3Commas-like" em open source é sobretudo coberto pelos executores DCA/grid do OctoBot e do Hummingbot; não encontrei nenhum clone dedicado e bem mantido (não pesquisado a fundo).

### Lacunas
- Número de contribuidores activos (90 dias) de cada repo: não verificado (API de contribuidores bloqueada).
- Datas da última release do Jesse, OctoBot e Superalgos: não verificadas (só se confirmou a data do último push).

## Suportam Binance Futures com stops closePosition / contas UE (BNFCR)? Modelam comissões e slippage? Têm modo dry-run/paper?

### Conclusão
O Freqtrade suporta explicitamente o **modo BNFCR da Binance** (contas UE), mas o seu stoploss na exchange em futuros envia `reduceOnly=True` (não `closePosition`). Isto contradiz directamente a restrição BNFCR documentada pelo próprio utilizador e tem de ser testado. Os backtests do Freqtrade aplicam comissões mas **não simulam slippage**. Todos os frameworks principais têm paper/dry-run.

### Factos citados
- Freqtrade: "BNFCR mode are a special type of futures mode on Binance to work around regulatory issues in Europe." Exige `trading_mode: futures`, `margin_mode: cross`, `proxy_coin: BNFCR`, e na conta Multi-asset Mode + One-way position mode — [freqtrade docs/exchanges.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/exchanges.md)
- Freqtrade: "On futures, Binance supports both `stop-limit` as well as `stop-market` orders"; escolhe-se via `order_types.stoploss` — [docs/exchanges.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/exchanges.md)
- Código do Freqtrade: em futuros, `create_stoploss` define `params["reduceOnly"] = True`; nos tipos de stop de futuros da Binance `{"limit": "stop", "market": "stop_market"}`; tem `stoploss_algo_order_info_id: "actualOrderId"` (trata os algo orders da Binance); `proxy_coin_mapping: {"BNFCR": "USDC", "BFUSD": "USDT"}`. Não encontrei `closePosition` em `binance.py` nem em `exchange.py` — [freqtrade/exchange/binance.py](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/freqtrade/exchange/binance.py); [freqtrade/exchange/exchange.py](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/freqtrade/exchange/exchange.py) (grep feito a 2026-10-10)
- Comissões no backtest do Freqtrade: "By default, Backtesting fetches the default fee from the exchange pair/market info"; `--fee` "will be applied twice (once for trade entry, and once for trade exit)" — [docs/backtesting.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/backtesting.md)
- Slippage no backtest do Freqtrade: "All orders are filled at the requested price (no slippage) as long as the price is within the candle's high/low range"; as saídas por stoploss preenchem ao preço do stop mesmo que o mínimo da vela seja inferior; `--timeframe-detail` reduz o viés intra-vela; "Backtesting never replaces dry-run testing" — [docs/backtesting.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/backtesting.md)
- Dry-run do Freqtrade: `dry_run` "Defaults to `true`"; `dry_run_wallet` por omissão 1000 — [docs/configuration.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/configuration.md)
- Hummingbot: o conector `binance_perpetual` está listado (nível de patrocinadores); o README não menciona USDC-M; o paper trade usa o conector `binance_paper_trade` com dados de mercado reais, sem chaves de API; as configs dos controllers V2 "can be backtested" (sem detalhes) — [hummingbot README](https://raw.githubusercontent.com/hummingbot/hummingbot/master/README.md)
- Jesse: backtest, optimize (Optuna), live e paper; o live/paper exige o plugin `jesse_live` com um LICENSE_API_TOKEN de uma conta jesse.trade; suporte a Binance Perpetual Futures referido no changelog — [docs.jesse.trade livetrade](https://docs.jesse.trade/docs/livetrade); [Jesse README](https://raw.githubusercontent.com/jesse-ai/jesse/master/README.md). Preço da licença em conflito: $899–$999 lifetime ([ToolRadar](https://toolradar.com/tools/jesse/pricing)) vs "$1600/licença" ([Gainium](https://gainium.io/blog/jesse)) — não verificado no site oficial (DNS falhou)
- OctoBot: "Binance spot and futures trading using the REST and websocket APIs"; paper trading com fundos simulados; usa CCXT — [OctoBot README](https://raw.githubusercontent.com/Drakkar-Software/OctoBot/master/README.md)
- Passivbot: só perpétuos; exchanges: Bybit, OKX, Bitget, Bitunix, GateIO, Binance, Kucoin, Hyperliquid, WEEX, Lighter; o README não diz se as ordens são só maker nem como modela comissões — [passivbot README](https://raw.githubusercontent.com/enarjord/passivbot/master/README.md)

### Inferências
- **Questão crítica para o utilizador:** o CLAUDE.md do utilizador diz que `STOP_MARKET` com `reduceOnly=true` NÃO é suportado na sua conta BNFCR. O Freqtrade envia exactamente isso, mas anuncia suporte a BNFCR e trata algo orders (`actualOrderId`). Ou o Freqtrade/CCXT encaminha os stops pelo endpoint de algo orders, onde o reduceOnly é aceite, ou o stoploss na exchange vai falhar na conta do utilizador. Tem de ser testado com uma posição mínima antes de confiar nele. O stoploss do Freqtrade também pode correr só por software (`stoploss_on_exchange: false`).
- A ausência de slippage nos backtests do Freqtrade, combinada com fills à abertura da vela, tende a sobrestimar estratégias de alta rotação. O simulador de papel do próprio utilizador (0.05% taker + 0.02% slippage) é mais conservador do que o backtest por omissão do Freqtrade.

### Lacunas
- Se o Hummingbot `binance_perpetual` suporta pares USDC-M e contas BNFCR: não verificado.
- Modelação de comissões/slippage no backtest do Passivbot, Jesse e Hummingbot: não verificada a partir de fontes primárias.
- Se algum framework usa `closePosition=true` nos stops da Binance: não encontrei evidência para nenhum.

## Existe algum histórico público e verificável de resultados reais?

### Conclusão
Não encontrei **nenhum histórico de P&L live auditado e verificável** de nenhum framework open source. A única métrica "live" verificável é o volume agregado do Hummingbot (volume, não lucro). O NFI publica backtests nos comentários dos commits, não resultados live. Os Reference Vaults do Passivbot na Hyperliquid foram referidos, mas sem números.

### Factos citados
- Hummingbot: "Over the past year, Hummingbot users have generated over $34 billion in trading volume across 140+ unique trading venues" — [hummingbot README](https://raw.githubusercontent.com/hummingbot/hummingbot/master/README.md). Um agregador refere ">111,000 instâncias, >$47 mil milhões" (cumulativo, não verificado) — [Stork.ai](https://www.stork.ai/en/hummingbot). O volume é auto-reportado por telemetria dos clientes — [hummingbot.org/reporting](https://hummingbot.org/reporting)
- Passivbot: uma review refere um "Reference Vault" dedicado na Hyperliquid a correr a config por omissão do Passivbot em live, mas sem retornos, drawdown nem período — [Gainium review](https://gainium.io/review/passivbot); o README não faz afirmações de resultados e diz "Used at one's own risk" — [passivbot README](https://raw.githubusercontent.com/enarjord/passivbot/master/README.md)
- Passivbot: a estratégia por omissão é `trailing_martingale` — "starts with a small entry and adds to the position as price moves against it" — [passivbot README](https://raw.githubusercontent.com/enarjord/passivbot/master/README.md); os revisores notam o risco de drawdown estilo martingale — [Gainium review](https://gainium.io/review/passivbot)
- NostalgiaForInfinity: sem afirmações de resultados live; "For backtesting results, check out the comments in the individual commit page"; sem aviso de risco no README; inclui links de referral de exchanges — [NFI README](https://raw.githubusercontent.com/iterativv/NostalgiaForInfinity/main/README.md)
- OctoBot: o único número é a legenda de um backtest de exemplo (8% em grid ETH/BTC); sem promessa de retornos — [OctoBot README](https://raw.githubusercontent.com/Drakkar-Software/OctoBot/master/README.md)

### Inferências
- O volume não é lucro: o volume do Hummingbot é em grande parte gerado por market making que é pago por campanhas de liquidez/rebates, não necessariamente lucrativo para quem corre o bot.
- Sem P&L live verificado, o critério do utilizador (≥100 trades em papel com líquido > 0) é mais rigoroso do que qualquer coisa que estes projectos publiquem.

### Lacunas
- Leaderboards de dry-run da comunidade, resultados de competições Hummingbot e relatórios live de NFI/Passivbot no Discord: não encontrados em fontes indexadas (as pesquisas do NFI deram resultados irrelevantes; o Firecrawl estava sem créditos).

## Qual é a melhor base para o utilizador (bot Python próprio, Binance Futures, ~300 USDC, 6x, prejuízo por comissões: bruto −11 / comissões 86)?

### Conclusão
O Freqtrade é a escolha mais forte para migrar uma estratégia direccional em Python: suporta BNFCR, ordens limit de entrada e saída, `time_in_force: PO` (post-only/maker), escolha do lado do spread, tabelas ROI e hyperopt sobre comissões reais. Os executores do Hummingbot são mais adequados se o utilizador quiser passar a uma abordagem maker/market making. O ganho mais directo sobre o arrasto das comissões vem de entradas/saídas maker limit e de menos trades, não de uma mudança de framework.

### Factos citados
- Freqtrade `order_types`: "This allows to enter using limit orders, exit using limit-orders, and create stoplosses using market orders" — [docs/configuration.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/configuration.md)
- Freqtrade `order_time_in_force` PO: "The order is either placed as a maker order, or it is canceled" (por omissão GTC) — [docs/configuration.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/configuration.md)
- Freqtrade `entry_pricing/exit_pricing.price_side`: `ask`, `bid`, `same`, `other` (por omissão `same`) — [docs/configuration.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/configuration.md)
- Freqtrade `minimal_roi`: chave = minutos, valor = ROI mínimo em rácio — [docs/configuration.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/configuration.md)
- Freqtrade: os backtests aplicam a comissão da exchange nas duas pernas; `--fee` permite testar a sensibilidade a outras comissões — [docs/backtesting.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/backtesting.md)
- Freqtrade: as regras de futuros da Binance proíbem, entre outras coisas, stakes demasiado pequenos espalhados por demasiadas ordens, o que leva a restrições de trading — [docs/exchanges.md](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docs/exchanges.md)
- Hummingbot: executores para position, DCA, grid, arbitragem, XEMM, TWAP; market making (simple_pmm, Avellaneda); post-only LIMIT_MAKER acrescentado para a Bitget na v2.16.0 — [README](https://raw.githubusercontent.com/hummingbot/hummingbot/master/README.md); [releases](https://github.com/hummingbot/hummingbot/releases)
- Passivbot é um "contrarian market maker" que coloca ordens limit em perpétuos — [README](https://raw.githubusercontent.com/enarjord/passivbot/master/README.md)

### Inferências
- 86 USDC de comissões em 588 trades ≈ 0.146 USDC/trade. Com uma taxa taker de ~0.05% por perna, isso implica um nocional médio de ~146 USDC por trade (0.146 / 0.001 round-trip). Mudar as duas pernas para maker (taxas maker mais baixas na Binance) reduziria isto de forma substancial; o Freqtrade com `order_types` limit + `PO` + `price_side: same` implementa isso directamente. Calcular com as taxas USDC-M actuais do utilizador antes de decidir.
- O backtest/hyperopt do Freqtrade com `--fee` fixado na taxa taker real é uma forma barata de verificar se uma estratégia sobrevive às comissões; acrescentar `--timeframe-detail` para reduzir o viés intra-vela.
- Os stops do Freqtrade precisam de validação em BNFCR (ver acima). Se `reduceOnly` falhar, usar `stoploss_on_exchange: false` (stop só por software) ou manter o padrão de stop com `closePosition` do bot próprio.
- Passivbot/martingale com 300 USDC e 6x tem risco de cauda elevado; não é adequado como base sem compreender o equity hard stop.
- Mudar de framework não cria edge: o bruto do utilizador era ≈ 0 (−11). Um framework só reduz custos/bugs; continua a ser preciso uma estratégia com expectância bruta positiva.

### Lacunas
- Taxas maker/taker actuais dos USDC-M da Binance para o nível do utilizador (houve promoções de 0% maker em USDC-M no passado): não verificadas nesta pesquisa.
- Se o PO do Freqtrade funciona nos USDC-M da Binance via CCXT em BNFCR: não verificado.

## Repositórios de estratégias com resultados documentados — o que reportam os utilizadores reais?

### Conclusão
O NostalgiaForInfinity (3.5k estrelas, commits até 2026-10-09) e o freqtrade-strategies (5.5k, push em Set 2026) são os maiores repositórios de estratégias. Nenhum publica resultados live verificados; o NFI só remete para backtests nos comentários dos commits. Não encontrei relatos independentes indexados de utilizadores.

### Factos citados
- NFI: timeframe 5m obrigatório; 6–12 trades abertas com stake ilimitado; pairlist de 40–80 pares (volume pairlist); preferir pares em stablecoins; blacklist de tokens alavancados; `use_exit_signal` true, `exit_profit_only` false — [NFI README](https://raw.githubusercontent.com/iterativv/NostalgiaForInfinity/main/README.md)
- NFI: o README não refere suporte a futuros; não faz afirmações de resultados live — [NFI README](https://raw.githubusercontent.com/iterativv/NostalgiaForInfinity/main/README.md)
- freqtrade-strategies: GPL-3.0, 5,537 estrelas, último push 2026-09-08 — [GitHub](https://github.com/freqtrade/freqtrade-strategies)

### Inferências
- O NFI é uma estratégia spot de 5m com muitos trades; tal como o bot do utilizador, é estruturalmente exposto ao arrasto das comissões, e não deve ser tratado como solução para comissões altas.

### Lacunas
- Relatos de utilizadores no Reddit/Discord sobre o desempenho live do NFI ou do freqtrade-strategies: não encontrados (a pesquisa web devolveu resultados não relacionados; as pesquisas no Firecrawl falharam por falta de créditos). O Discord não está indexado.
