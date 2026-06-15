# AutoDream Memory — CLAW Agent v8

## Ficheiros de memória
| Ficheiro | Conteúdo |
|----------|----------|
| `context.md` | Estado actual do bot, parâmetros, arquitectura |
| `decisions.md` | Decisões técnicas importantes e porquê |
| `bugs.md` | Bugs pendentes e corrigidos |
| `dream.log` | Histórico de ciclos de memória |

## Projecto
- **Nome:** CLAW Agent v8 (Claw Trading Bot)
- **Linguagem:** Python 3
- **Exchange:** Binance Futures USDC-M (perpétuos)
- **Conta:** BNFCR (Binance France — conta europeia com restrições de API)
- **VPS:** `178.105.52.219` (IP fixo whitelisted na Binance)
- **Repositório:** `hltv27/blank-app` → `/root/blank-app/claw_v8/`
- **Log:** `/root/claw.log`
- **DB:** `claw_v8.db` (SQLite)
- **Notificações:** Telegram

## Ficheiros principais
| Ficheiro | Função |
|----------|--------|
| `main.py` | Loop principal, scan de pares, sync de posições |
| `config.py` | Todas as constantes |
| `execution.py` | Abrir/gerir trades, profit lock, guards |
| `exchange.py` | HTTP à Binance e Telegram |
| `strategy.py` | Sinais, SL/TP, market mode |
| `filters.py` | Filtros HTF, funding, volatility regime |
| `risk.py` | Circuit breaker, veto por símbolo |
| `storage.py` | SQLite + memória JSON |
| `indicators.py` | ATR, ADX, RSI, Supertrend, etc. |
| `markov.py` | Markov regime signal |

## Performance actual (2026-06-15)
- **Trades:** 13
- **PnL:** +7.09 USDC
- **Win rate:** 61.5%
- **Saldo real:** ~165 USDC
