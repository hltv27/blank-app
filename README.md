# Claw Agent v7

Bot de trading automático para Binance Futures USDC.
Cross Margin | 10 pares | Modos Trending + Ranging.

## Estratégia

- **Trending mode:** EMA 9/21/99 + RSI + ATR + StochRSI
- **Ranging mode:** Bollinger Bands mean-reversion
- **Risco fixo:** 1.0 USDC por trade | Capital máx: 50 USDC
- **Alavancagem:** 10x Cross Margin
- **Circuit breaker:** loss diária 3 USDC ou 4 perdas seguidas → pausa 15 min
- **Sessões UTC:** 07h–12h e 13h–20h
- **Ciclo:** 4 minutos

## Pares

`BTCUSDC` `ETHUSDC` `BNBUSDC` `SOLUSDC` `XRPUSDC`
`DOGEUSDC` `AVAXUSDC` `LINKUSDC` `SUIUSDC` `PEPEUSDC`

## Requisitos

- Python 3.10+
- Conta Binance Futures com saldo USDC
- Bot Telegram criado via @BotFather

## Instalação

```bash
git clone https://github.com/hltv27/blank-app.git
cd blank-app

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Configuração

Define as variáveis de ambiente antes de correr:

```bash
export TELEGRAM_TOKEN="<token>"
export TELEGRAM_CHAT_ID="<chat_id>"
export BINANCE_API_KEY="<api_key>"
export BINANCE_API_SECRET="<api_secret>"
```

Ou edita directamente as constantes no topo de `claw_agent_v7.py`.

## Execução

```bash
python main.py
```

## Ficheiros de Estado

| Ficheiro | Descrição |
|---|---|
| `claw_memory_v7.json` | Estado do bot (trades abertos, circuit breaker, PnL diário) |
| `claw_pnl_v7.json` | Histórico de todos os trades |

## Aviso

Este bot opera com dinheiro real. Testa sempre em conta demo antes de usar em produção.
Não é aconselhamento financeiro.
