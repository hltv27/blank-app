# Claw Agent v8 — Contexto Rápido (para claude.ai)

> **LEMBRA-TE**: Se estás a retomar uma conversa antiga, vai buscar a versão mais recente deste ficheiro ao repo `hltv27/blank-app` → `claw_v8/context.md` (branch main). O bot evolui — contexto desactualizado = erros.

---

## O que é
Bot de trading automático — Binance Futures USDC-M (perpétuos).
- Capital: ~240 USDC | Alavancagem: 6x | Margem: Cross
- Conta europeia **BNFCR** — tem restrições de API
- VPS: `178.105.52.219` | Ficheiros: `/root/blank-app/claw_v8/`
- Auto-deploy: commits em `main` → bot reinicia automaticamente

## Arquitectura

| Ficheiro | Função |
|---|---|
| `config.py` | Constantes (risco, estratégia, pares) |
| `main.py` | Loop principal, scan de pares, sync posições |
| `execution.py` | Abrir trades, gerir posições, profit lock, guards |
| `exchange.py` | Chamadas HTTP Binance + Telegram |
| `strategy.py` | Sinais trending, SL/TP, market mode |
| `filters.py` | Filtros HTF, funding rate, volatility regime |
| `risk.py` | Circuit breaker, veto por símbolo |
| `storage.py` | SQLite + memória JSON |
| `indicators.py` | ATR, ADX, RSI, Supertrend, VWAP, etc. |

## Parâmetros chave
- Risco/trade: 5 USDC | Max trades: 5 | Max margem/trade: 20%
- Profit lock: activa +1 USDC, step +0.5 USDC, trailing a +4 USDC
- Emergency: ROI -5.5% ou PnL -3 USDC → fecha
- Score mínimo entrada: 6/10+ | ADX: 22.5 (majors) / 30 (alts)
- Sessão: 05:00-23:00 UTC | Top 150 pares por volume

## Regras de saída
| Regra | Condição | Acção |
|---|---|---|
| Profit lock | PnL > 1 USDC | Move SL +0.5 USDC |
| Trailing | PnL ≥ 4 USDC | Trailing stop |
| TP1/TP2 | 2R / 3R | Fecha 33% cada |
| TIME_TP | >10min + ROI ≥7% | Fecha tudo |
| STAGNADO | >60min + PnL -0.5~+1.0 | Fecha |
| EMERGENCY | ROI≤-5.5% ou PnL>-3 | Fecha imediatamente |

## Guards de risco
- BTC crash >3% → fecha LONGs | Drawdown 25% → fecha tudo
- Margem >35% → fecha tudo | Margem global >50% → fecha positivos
- Nunca toca em posições manuais

## Circuit breaker
- Loss dia >15 USDC → cooldown 2h | 3 perdas seguidas → cooldown 2h
- Veto símbolo: 3 perdas → 24h; WR<30% em 5+ trades → 12h

## Restrições CRÍTICAS (BNFCR)
1. `reduceOnly=true` NÃO funciona → usar `closePosition=true`
2. Só 1 STOP_MARKET closePosition por símbolo de cada vez
3. `place_stop_market` usa `/fapi/v1/algoOrder` (endpoint especial BNFCR)
4. Profit lock cancela stop antigo ANTES de colocar novo

## Bugs já corrigidos (não repetir)
1. STOP_MARKET conflito com TP → cancela antigo primeiro
2. Bot geria posições manuais → `pending_sync` antes da ordem
3. Profit lock spam Telegram → avança nível em memória sempre
4. Guards fechavam manuais → verifica `trades_bot`
5. SL falhado fechava posição → mantém + software SL
6. Spam "posição manual detectada" → `load_memory()` corrigido
7. trades_abertos={} após restart → mesmo fix #6
8. STAGNADO fechava perdedoras → condição -0.5~+1.0, min 60min
9. Stop price precision errada → `PRICE_PRECISION` separado
10. Score muito baixo → SCORE_ALERTA=6
11. Margem falso positivo → `get_margin_ratio_global()`

## Credenciais
NUNCA mostrar no chat. Estão no VPS em `~/.bashrc` e `/etc/environment`.
