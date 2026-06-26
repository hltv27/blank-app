# Claw Agent v8

Bot de trading automático para Binance Futures USDC-M (perpétuos).
Cross Margin | Top 150 pares por volume | Modo Trending.

Código em `claw_v8/` (refactor modular da v7 — mesma estratégia base, ficheiros separados por responsabilidade).

## Estratégia

- **Trending mode:** EMA + RSI + ADX + ATR + Supertrend + VWAP, com filtros HTF (4H+1H), Fear&Greed, BB squeeze, CVD, OBI
- **Risco fixo:** 5.0 USDC por trade | Capital máx: 370 USDC
- **Alavancagem:** 6x Cross Margin
- **Circuit breaker:** loss diária 15 USDC ou 3 perdas seguidas → pausa 120 min
- **Sessões UTC:** 05h–23h
- **Ciclo:** scan a cada 4 min, gestão de posições a cada 10-30s

## Pares

Top 150 pares Futures USDC-M por volume (`TOP_N_FUTURES`), seleccionados dinamicamente — não é uma lista fixa.

## Requisitos

- Python 3.10+
- Conta Binance Futures (BNFCR — Binance France Crypto Receipt) com saldo USDC
- Bot Telegram criado via @BotFather

## Instalação

```bash
git clone https://github.com/hltv27/blank-app.git
cd blank-app/claw_v8

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r ../requirements.txt
```

## Configuração

Define as variáveis de ambiente antes de correr:

```bash
export TELEGRAM_TOKEN="<token>"
export TELEGRAM_CHAT_ID="<chat_id>"
export BINANCE_API_KEY="<api_key>"
export BINANCE_API_SECRET="<api_secret>"
```

Ou edita directamente as constantes em `claw_v8/config.py`.

## Execução

Em produção (Termux/Android, sem systemd/cron), correr sempre via `run_loop.sh` para garantir auto-restart após crash ou watchdog:

```bash
cd claw_v8
chmod +x run_loop.sh
nohup ./run_loop.sh &
```

## Ficheiros principais

| Ficheiro | Função |
|---|---|
| `config.py` | Constantes (risco, estratégia, pares) |
| `main.py` | Loop principal, scan de pares, sync de posições, watchdog |
| `execution.py` | Abrir trades, gerir posições, profit lock, guards |
| `exchange.py` | Chamadas HTTP à Binance e Telegram |
| `strategy.py` | Sinais trending, cálculo SL/TP, market mode |
| `filters.py` | Filtros HTF, funding rate, volatility regime |
| `risk.py` | Circuit breaker, veto por símbolo, sessão |
| `storage.py` | SQLite + memória JSON |
| `indicators.py` | ATR, ADX, RSI, Supertrend, VWAP |
| `run_loop.sh` | Wrapper que reinicia `main.py` automaticamente (Termux) |

## Ficheiros de estado

| Ficheiro | Descrição |
|---|---|
| SQLite (via `storage.py`) | Trades abertos, circuit breaker, histórico, posições externas |
| `status.json` | Snapshot do relatório diário (actualizado às 23:00 UTC) |
| `status_history.jsonl` | Histórico diário, nunca sobrescrito |

## Aviso

Este bot opera com dinheiro real. Testa sempre em conta demo antes de usar em produção.
Não é aconselhamento financeiro.
