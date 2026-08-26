# AutoDream Memory — hltv27/blank-app (CLAW v8 + Affiliate Bot)

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

## Projectos cobertos
- **CLAW Agent v8** — bot trading Binance Futures USDC-M (claw_v8/)
- **Affiliate Bot** — posts automáticos AliExpress → Telegram/Instagram/Facebook (affiliate_bot/)

## Último ciclo AutoDream
- **#1** 2026-06-15 — init claw_v8
- **#2** 2026-08-26 — actualização claw_v8 params + estado affiliate bot
