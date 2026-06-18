# Claw Agent v8 — Contexto para Claude

## Estado do Bot — LER NO INÍCIO DE CADA SESSÃO

**Antes de qualquer conversa sobre o bot, ler sempre:**

```
hltv27/blank-app → claw_v8/status.json (branch: main)
```

Usar `mcp__github__get_file_contents` com `{"owner":"hltv27","repo":"blank-app","path":"claw_v8/status.json"}`.
O ficheiro é actualizado automaticamente pelo bot às 23:00 UTC com o relatório do dia.
Se `ts == 0` o bot ainda não enviou o primeiro relatório.

Para análise histórica (vários dias), ler `claw_v8/status_history.jsonl` — uma linha JSON por dia, nunca sobrescrito.
O `ultimo_relatorio_dia` é persistido no SQLite — restarts não perdem dias nem disparam duplicados.

## O que é este projecto
Bot de trading automático para Binance Futures USDC-M (perpétuos).
- Capital: ~240 USDC | Alavancagem: 6x | Margem: Cross
- Conta europeia **BNFCR** (Binance France Crypto Receipt) — tem restrições de API
- Corre no **VPS** `178.105.52.219` — IP fixo whitelisted na Binance
- Ficheiros em `/root/blank-app/claw_v8/` | Log: `/root/claw.log`
- Auto-deploy activo: `auto_deploy.sh` detecta commits em `main` e reinicia o bot

## Como aceder ao VPS
```bash
ssh root@178.105.52.219
```

## Como arrancar o bot (no VPS)
```bash
cd /root/blank-app && git pull origin main
pkill -f "python.*main.py"; sleep 2
cd /root/blank-app/claw_v8
PYTHONUNBUFFERED=1 nohup python3 main.py > /root/claw.log 2>&1 &
echo $! > /root/claw.pid
sleep 3 && tail -20 /root/claw.log
```

## Monitorizar log em tempo real
```bash
ssh root@178.105.52.219 "tail -f /root/claw.log"
```

## Kill switch de emergência
```bash
ssh root@178.105.52.219 "touch /root/blank-app/claw_v8/KILL_SWITCH"
```

## Branches
- **Desenvolvimento**: `claude/setup-project-structure-3xwuR`
- **Produção**: `main` — pushes vão sempre para `main` no GitHub (hltv27/blank-app)
- NUNCA fazer push para main sem confirmar com o utilizador

## Credenciais
**NUNCA mostrar no chat.** Estão em `~/.bashrc` e `/etc/environment` no VPS:
`TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `BINANCE_API_KEY`, `BINANCE_API_SECRET`

---

## Arquitectura — ficheiros principais

| Ficheiro | Função |
|---|---|
| `config.py` | Todas as constantes (risco, estratégia, pares) |
| `main.py` | Loop principal, scan de pares, sync de posições |
| `execution.py` | Abrir trades, gerir posições, profit lock, guards |
| `exchange.py` | Todas as chamadas HTTP à Binance e Telegram |
| `strategy.py` | Sinais trending, cálculo SL/TP, market mode |
| `filters.py` | Filtros HTF, funding rate, volatility regime, etc. |
| `risk.py` | Circuit breaker, veto por símbolo, sessão |
| `storage.py` | SQLite + memória JSON |
| `indicators.py` | ATR, ADX, RSI, Supertrend, VWAP, etc. |

---

## Restrição crítica da conta EU (BNFCR)

**`STOP_MARKET` com `reduceOnly=true` NÃO é suportado.**
Usar sempre `closePosition=true`. Ver `exchange.py:place_stop_market`.

Consequência: só pode haver **um** STOP_MARKET closePosition por símbolo de cada vez.
O profit lock cancela o stop antigo ANTES de colocar o novo. Ver `execution.py`.

---

## Parâmetros actuais em `config.py`

```python
CAPITAL_MAX_BOT     = 300.0    # capital máximo que o bot usa
RISCO_USDC          = 5.0      # risco por trade em USDC
ALAVANCAGEM         = 6        # leverage
MAX_TRADES_ABERTOS  = 5
MAX_MARGEM_TRADE    = 0.20     # máx 20% do capital por posição
PROFIT_LOCK_USDC    = 0.5      # activa lock a partir de +0.5 USDC
PROFIT_LOCK_STEP    = 0.5      # move stop a cada +0.5 USDC
TRAILING_LOCK_USDC  = 4.0      # ao atingir 4 USDC muda para trailing stop
EMERGENCY_ROI_CUT   = -5.5     # % ROI para corte de emergência
EMERGENCY_PNL_CUT   = 3.0      # fecha se perda absoluta > 3 USDC
SCORE_ALERTA        = 6        # score mínimo para abrir trade (era 4)
SCORE_FORTE         = 6        # score considerado forte
ADX_TREND_MIN_MAJOR = 22.5     # BTC/ETH/BNB
ADX_TREND_MIN_ALT   = 30.0     # alts — exige tendência mais forte
ROI_TP_IMEDIATO     = 7.0      # % ROI → fecha imediatamente
TIME_TP_MIN_MIN     = 10       # minutos mínimos para TIME_TP
SESSOES_UTC         = [(5, 23)]
TOP_N_FUTURES       = 150      # top 150 pares USDC-M por volume
```

---

## Lógica de gestão de posições

### Abertura (`abrir_trade`)
1. Filtros (HTF 4H+1H, Supertrend, Fear&Greed, BB squeeze, CVD, OBI, VWAP)
2. Sizing: `RISCO_USDC=5` / (entry - SL) × entry, cap 20% capital por trade
3. Vol scale: se ATR/price > 0.3%, reduz qty proporcionalmente
4. Escreve `pending_sync[symbol]` → coloca ordem MARKET → coloca STOP_MARKET → coloca TP

### Saídas (`gerir_posicoes`, ciclo de 10s quando há posições)
| Regra | Condição | Acção |
|---|---|---|
| **Profit lock** | PnL > 1 USDC | Move SL a cada +0.5 USDC |
| **Trailing lock** | PnL ≥ 4 USDC | Muda stop fixo → trailing stop |
| **TP1** | 2R atingido | Fecha 33%, trailing para breakeven |
| **TP2** | 3R atingido | Fecha mais 33% |
| **TIME_TP** | >10min + ROI ≥ 7% | Fecha tudo |
| **SIGNAL_INV** | Sinal oposto score≥6 após 5min | Fecha tudo |
| **STAGNADO** | >60min + PnL entre -0.5 e +1.0 | Fecha (sem trailing lock) |
| **EMERGENCY_PNL** | Perda > 3 USDC absolutos | Fecha imediatamente |
| **EMERGENCY_ROI** | ROI ≤ -5.5% | Fecha imediatamente |
| **Software SL** | price ≤ sl (LONG) / price ≥ sl (SHORT) | Fecha via MARKET |

### Guards de risco
- BTC crash > 3% → fecha todos os LONGs do bot
- Drawdown 25% do saldo → fecha tudo do bot
- Margem > 35% → fecha tudo do bot
- Margem global > 50% → fecha posições a positivo (liquidation guard)
- **Guards de drawdown/margem/BTC-crash nunca tocam em posições manuais**

### Posições manuais (detectadas no scan)
- Sem `pending_sync` → vai para `posicoes_externas`
- Bot envia alertas de ROI (-5%, -3%, +3%, +5%, +10%, +15%, +20%)
- Bot NÃO fecha, P&L NÃO conta para circuit breaker
- **Profit lock activo**: a partir de `PROFIT_LOCK_USDC` (+0.5 USDC) o bot coloca/move um `STOP_MARKET closePosition` a cada `PROFIT_LOCK_STEP` (+0.5 USDC), igual ao que faz nas trades do próprio bot
- Na primeira activação cancela qualquer stop pré-existente no símbolo (`get_open_algo_orders` + `cancel_algo_order`) antes de colocar o seu — evita conflito com stop manual já colocado pelo utilizador (só pode existir 1 `closePosition` stop por símbolo)
- Implementado em `main.py`, bloco "Monitorização de posições externas"

### Circuit breaker
- `MAX_LOSS_DIA = 15 USDC` → cooldown 120min
- `MAX_PERDAS_SEGUIDAS = 3` → cooldown 120min
- Veto por símbolo: 3 perdas seguidas → 24h; WR < 30% em 5+ trades → 12h

---

## Bugs corrigidos — histórico completo

### 1. STOP_MARKET conflito com TP order
- **Causa**: profit lock tentava colocar 2º closePosition stop sem cancelar o 1º
- **Fix**: cancela stop antigo PRIMEIRO, só depois coloca novo (`execution.py`)

### 2. Bot geria posições manuais do utilizador
- **Custo real**: SUIUSDC -8.76 USDC (posição do bot órfã), ZECUSDC +30 USDC fechado
- **Fix**: `pending_sync[symbol]` escrito antes de colocar ordem; sync só recupera se marcador < 5min

### 3. Profit lock spam no Telegram
- **Causa**: stop falhava, bot não actualizava nível, ciclo infinito de mensagens
- **Fix**: avança `profit_lock_level` e `sl` em memória independentemente do resultado da exchange

### 4. Guards fechavam trades manuais
- **Fix**: todos os guards verificam `if sym not in trades_bot: continue`

### 5. `abrir_trade` fechava posição quando SL falhava
- **Fix**: mantém posição, software SL em memória, avisa no Telegram

### 6. "Posição manual detectada" spam a cada 10-30s (`storage.py`)
- **Causa**: `load_memory()` não incluía `posicoes_externas` nem `pending_sync` → reset a `{}` em cada ciclo
- **Fix**: adicionadas as duas chaves ao `load_memory()` em `storage.py`
- **GitHub**: SHA d691f48

### 7. `trades_abertos = {}` após restart (posições tratadas como externas)
- **Causa**: mesmo bug do `load_memory()` + pending_sync expirado (>5min)
- **Fix**: mesmo fix do bug 6

### 8. STAGNADO fechava posições perdedoras (ex: -2 USDC após 68min)
- **Causa**: regra antiga `pnl < 0.5` fechava qualquer posição com menos de 0.5 USDC de lucro
- **Fix**: nova condição `-0.5 <= pnl < 1.0` e tempo mínimo de 60min (era 45min)
- **GitHub**: SHA 92e1a97

### 9. Stop loss com preço errado — ordens rejeitadas pela Binance (`exchange.py`)
- **Causa**: `place_stop_market`, `place_take_profit`, `place_trailing_stop` usavam `SYMBOL_PRECISION` (casas decimais da QUANTIDADE) para formatar o `stopPrice`
- **Exemplo**: ZECUSDC preço ~617, qty precision=4 → enviava 617.3475; Binance exige price precision=2 → 617.35
- **Fix**: todas as funções de preço usam agora `PRICE_PRECISION` (default 2)
- `get_top_futures_symbols` agora também extrai `PRICE_FILTER` tickSize e retorna 3-tuple
- `main.py` actualiza `config.PRICE_PRECISION` dinamicamente ao arrancar e a cada 24h
- **GitHub**: SHA de19dff

### 10. Score mínimo de entrada demasiado baixo
- **Causa**: `SCORE_ALERTA = 4` permitia entradas com apenas 4/10+ indicadores a confirmar
- **Fix**: `SCORE_ALERTA = 6` — exige sinal forte antes de abrir qualquer trade
- **GitHub**: SHA e0003ea

### 11. MARGEM CRÍTICA falso positivo — cross-collateral USDT-M (`execution.py`)
- **Causa**: guard de margem usava `get_margin_ratio()` que soma `maintMargin` do asset BNFCR; quando existe posição USDT-M com cross-collateral (ex: BTCUSDT 150x), o `maintMargin` do BNFCR inclui os requisitos dessa posição → rácio aparece 244-360% em vez dos verdadeiros 18%
- **Fix**: guard usa agora `get_margin_ratio_global()` que lê `totalMaintMargin / totalMarginBalance` da conta inteira — valor correcto independentemente de posições USDT-M
- **GitHub**: SHA 0487fd0

---

## Regras importantes que NÃO mudar

1. `reduceOnly=true` não funciona nesta conta → usar sempre `closePosition=true`
2. Só pode haver **um** STOP_MARKET closePosition por símbolo de cada vez
3. `_fechar_com_retry` — 3 tentativas antes de registar fecho (evita posições órfãs)
4. `place_stop_market` usa `/fapi/v1/algoOrder` (orderType+algoId) — Binance rejeitou o endpoint regular para contas BNFCR (SHA ef11229)
5. `get_balance` usa `/fapi/v2/account` assets[].marginBalance com fallback totalMarginBalance
6. Nunca mostrar credenciais no chat
7. NUNCA push para main sem confirmar com o utilizador
