# Claw Agent v8 — Contexto para Claude

## O que é este projecto
Bot de trading automático para Binance Futures USDC-M (perpétuos).
- Capital: ~240 USDC | Alavancagem: 6x | Margem: Cross
- Conta europeia **BNFCR** (Binance France Crypto Receipt) — tem restrições de API
- Corre em **Termux (Android)** — sem cron, sem /root/, utilizador u0_a1208
- Ficheiros em `~/blank-app/claw_v8/`

## Como arrancar o bot
```bash
cd ~/blank-app && git pull origin claude/setup-project-structure-3xwuR
pkill -f "python.*main.py"; sleep 2
cd ~/blank-app/claw_v8 && nohup python main.py > ~/claw.log 2>&1 &
```

## Branch de desenvolvimento
`claude/setup-project-structure-3xwuR` — NUNCA fazer push para main sem confirmar

## Credenciais
**NUNCA mostrar no chat.** Estão em `~/.bashrc` como variáveis de ambiente:
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

## Bugs corrigidos (histórico)

### 1. STOP_MARKET conflito com TP order
- **Causa**: profit lock tentava colocar 2º closePosition stop sem cancelar o 1º
- **Fix**: cancela stop antigo PRIMEIRO, só depois coloca novo (`execution.py`)

### 2. Bot geria posições manuais do utilizador
- **Causa**: sync em `main.py` detectava qualquer posição em SYMBOLS e geria
- **Custo real**: SUIUSDC -8.76 USDC (posição do bot órfã), ZECUSDC +30 USDC fechado
- **Fix**: `pending_sync[symbol]` escrito antes de colocar ordem; sync só recupera se marcador < 5min

### 3. Profit lock spam no Telegram
- **Causa**: stop falhava, bot não actualizava nível, ciclo infinito de mensagens
- **Fix**: avança `profit_lock_level` e `sl` em memória independentemente do resultado da exchange

### 4. Guards fechavam trades manuais
- **Fix**: todos os guards verificam `if sym not in trades_bot: continue`

### 5. `abrir_trade` fechava posição quando SL falhava
- **Antes**: 3 falhas de SL → fecha posição por segurança → perde a oportunidade
- **Agora**: mantém posição, software SL em memória, avisa no Telegram

---

## Lógica de gestão de posições

### Abertura (`abrir_trade`)
1. Filtros (HTF 4H+1H, Supertrend, Fear&Greed, BB squeeze, CVD, OBI, VWAP)
2. Sizing: `RISCO_USDC=5` / (entry - SL) × entry, cap 20% capital por trade
3. Vol scale: se ATR/price > 0.3%, reduz qty proporcionalmente
4. Escreve `pending_sync[symbol]` → coloca ordem MARKET → coloca STOP_MARKET → coloca TP

### Gestão (`gerir_posicoes`, ciclo de 10s quando há posições)
- **Profit lock**: PnL > 1 USDC → move SL a cada +0.5 USDC. Cancela stop antigo, coloca novo
- **TP1** (2R): fecha 33%, trailing stop para breakeven
- **TP2** (3R): fecha mais 33%, trailing stop para +1R
- **TIME_TP**: 30min aberto + ROI ≥ 5% → fecha
- **Emergency cut**: ROI ≤ -5.5% → fecha imediatamente
- **Software SL**: `price <= sl` (LONG) ou `price >= sl` (SHORT) → fecha via MARKET

### Guards de risco
- BTC crash > 3% → fecha todos os LONGs do bot
- Drawdown 25% do saldo → fecha tudo do bot
- Margem > 35% → fecha tudo do bot
- **Nunca tocam em posições manuais**

### Posições manuais (detectadas no scan)
- Sem `pending_sync` → vai para `posicoes_externas`
- Bot envia alertas de ROI (-5%, -3%, +3%, +5%, +10%, +15%, +20%)
- Bot NÃO coloca stops, NÃO fecha, P&L NÃO conta para circuit breaker

---

## Circuit breaker
- `MAX_LOSS_DIA = 15 USDC` → cooldown 120min
- `MAX_PERDAS_SEGUIDAS = 3` → cooldown 120min
- Veto por símbolo: 3 perdas seguidas → 24h; WR < 30% em 5+ trades → 12h

---

## Parâmetros chave em `config.py`

```python
CAPITAL_MAX_BOT     = 300.0    # capital máximo que o bot usa
RISCO_USDC          = 5.0      # risco por trade em USDC
ALAVANCAGEM         = 6        # leverage
MAX_TRADES_ABERTOS  = 5
MAX_MARGEM_TRADE    = 0.20     # máx 20% do capital por posição
PROFIT_LOCK_USDC    = 1.0      # activa lock a partir de +1 USDC
PROFIT_LOCK_STEP    = 0.5      # move stop a cada +0.5 USDC
EMERGENCY_ROI_CUT   = -5.5     # % ROI para corte de emergência
SESSOES_UTC         = [(5, 23)] # horário de abertura de posições
TOP_N_FUTURES       = 20       # top 20 pares USDC-M por volume
```

---

## Lições aprendidas (não repetir)

1. O utilizador perdeu **234 USDC** numa posição manual sem stop loss
2. O bot perdeu **8.76 USDC** no SUI por bugs no stop (agora corrigidos)
3. O bot fechou o ZEC manual **+30 USDC** por engano (agora corrigido)
4. `reduceOnly=true` não funciona nesta conta → usar sempre `closePosition=true`
5. Nunca mostrar credenciais no chat
