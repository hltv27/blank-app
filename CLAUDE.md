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
- Capital: ~300 USDC | Alavancagem: 6x | Margem: Cross
- Conta europeia **BNFCR** (Binance France Crypto Receipt) — tem restrições de API
- Corre actualmente na **VPS `178.105.52.219`** (hostname `Claw-bot`) — ver secção abaixo
- Histórico: Termux → VPS → Termux → **VPS** (actual)
- Ficheiros em `/root/blank-app/claw_v8/` | Log: `/root/claw.log`
- **Sem auto-deploy** — após cada `git push` para `main`, é preciso `git fetch` + `reset --hard` + restart na VPS (ver abaixo)

## Como arrancar o bot (VPS, ambiente actual)
Uma linha só — o utilizador pede sempre assim:
```bash
pkill -f "python.*main.py"; pkill -f "run_loop.sh"; sleep 2; cd /root/blank-app && git fetch origin main && git reset --hard origin/main && cd claw_v8 && chmod +x run_loop.sh && nohup ./run_loop.sh > /tmp/run_loop.log 2>&1 & sleep 5 && tail -20 /root/claw.log
```
**`git pull` não chega** — já falhou com "Already up to date" mesmo com commits novos em `main`. Usar sempre `git fetch` + `git reset --hard origin/main`.
Antes de relançar, matar SEMPRE todas as instâncias (`pkill` das duas linhas) — já aconteceu ficarem 5 processos em paralelo a duplicar logs e ordens.
`run_loop.sh` reinicia automaticamente o `main.py` sempre que ele terminar (crash ou watchdog) — não correr `python -u main.py` directamente em produção, senão perde-se o auto-restart.

Esta sessão remota **não tem acesso SSH** à VPS — qualquer diagnóstico depende de output/screenshots colados pelo utilizador.

## ⚠️ IP instável (Termux/dados móveis) — requer whitelist manual frequente
(Histórico — aplicava-se ao Termux, que corria sem IP fixo. A VPS tem IP fixo, pelo que isto deixou de acontecer.) O Termux corria em dados móveis, **sem IP fixo**. Sempre que o IP mudar (reinício do telemóvel, troca de torre/rede), a Binance bloqueia as chamadas da API e o bot envia `🔒 IP bloqueado` no Telegram repetidamente (1x/10min, ver `exchange.py:171`) até o IP ser adicionado.
- **Acção quando aparecer "IP bloqueado"**: Binance → API Management → Edit restrictions → adicionar o IP indicado na mensagem em "Restrict access to trusted IPs only"
- Isto NÃO é um bug do bot — é uma limitação inerente a correr sem IP fixo. Vai repetir-se.
- (Infra antiga, já não em uso) Comandos VPS com IP fixo `178.105.52.219` — mantidos apenas como referência histórica caso o bot volte para lá:
  ```bash
  ssh root@178.105.52.219
  cd /root/blank-app && git pull origin main
  pkill -f "python.*main.py"; sleep 2
  cd /root/blank-app/claw_v8
  PYTHONUNBUFFERED=1 nohup python3 main.py > /root/claw.log 2>&1 &
  echo $! > /root/claw.pid
  sleep 3 && tail -20 /root/claw.log
  ```

## Kill switch de emergência
```bash
touch /root/blank-app/claw_v8/KILL_SWITCH
```

## Branches
- **Desenvolvimento**: `claude/setup-project-structure-3xwuR`
- **Produção**: `main` — pushes vão sempre para `main` no GitHub (hltv27/blank-app)
- NUNCA fazer push para main sem confirmar com o utilizador

## Credenciais
**NUNCA mostrar no chat.** Estão em `~/.bashrc` e `/etc/environment` no VPS, e em GitHub Secrets (ver secção "Segunda via de execução" abaixo):
`TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `BINANCE_API_KEY`, `BINANCE_API_SECRET`

---

## ⚠️ Segunda via de execução (histórico): GitHub Actions (`run_bot.yml`) — DESACTIVADA em 2026-07-02

Durante algum tempo o bot correu **também diariamente via GitHub Actions**, em paralelo com o Termux, sem que o utilizador tivesse noção disso — **não era intencional**. Foi desactivado assim que descoberto.

```
.github/workflows/run_bot.yml
```

- **Estado actual**: o trigger `schedule` está comentado no ficheiro (só resta `workflow_dispatch` manual) — não corre mais sozinho
- **Como corria antes**: `cron '0 5 * * *'` (arrancava 05:00 UTC), `timeout-minutes: 350` (~5h50m), corria `python3 claw_v8/main.py` directamente (sem `run_loop.sh`, sem auto-restart do watchdog)
- **Credenciais**: usa GitHub Secrets (`TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `BINANCE_API_KEY`, `BINANCE_API_SECRET`) — as mesmas contas Binance/Telegram do Termux
- **Estado (SQLite)**: cada run era um checkout limpo — `claw_v8.db` e `KILL_SWITCH` locais ao runner, não persistiam entre execuções nem eram partilhados com o Termux
- **Confirmado que esteve activo**: 44 runs diários consecutivos com sucesso (23 Jun – 2 Jul 2026), todos no branch `main`, cada um a correr ~5h50m com as credenciais reais — ou seja, dois processos do bot a gerir a mesma conta Binance em simultâneo nesse período, cada um com a sua própria memória `trades_abertos`

Se aparecerem bugs antigos de "posição tratada como manual" ou conflitos de STOP_MARKET datados deste período (23 Jun – 2 Jul), considerar esta execução duplicada como causa provável. Para reactivar esta via no futuro (só se o Termux deixar de ser produção), descomentar o bloco `schedule` — ver comentário no próprio ficheiro. Para confirmar se voltou a correr nalgum momento, usa `mcp__github__actions_list` (`list_workflow_runs`, `resource_id: "run_bot.yml"`).

---

## Arquitectura — ficheiros principais

| Ficheiro | Função |
|---|---|
| `config.py` | Todas as constantes (risco, estratégia, pares) |
| `main.py` | Loop principal, scan de pares, sync de posições, watchdog, relatório diário |
| `execution.py` | Abrir trades, gerir posições, profit lock (bot + externas), guards |
| `exchange.py` | Todas as chamadas HTTP à Binance e Telegram |
| `strategy.py` | Sinais trending, cálculo SL/TP, market mode |
| `filters.py` | Filtros HTF, funding rate, volatility regime, etc. |
| `risk.py` | Circuit breaker, veto por símbolo, sessão |
| `storage.py` | SQLite + memória JSON |
| `indicators.py` | ATR, ADX, RSI, Supertrend, VWAP, etc. |
| `markov.py` | Detecção de regime via cadeia de Markov (5 estados: BULL/BEAR/VOL_UP/VOL_DOWN/RANGING), +2 ao score quando confirma direcção |
| `telegram_handler.py` | Comandos Telegram (`/status /fechar /pause /resume /pairs /help`), poll a cada 15s |
| `analytics.py` | Relatórios de performance por filtro (filter attribution) a partir do SQLite |
| `backtest.py` | Motor de backtest standalone sobre dados históricos públicos da Binance (`python backtest.py --symbol BTCUSDC --days 90`) |
| `spot_scanner.py` | Scanner multi-timeframe independente para Binance Spot (não é o bot de futures; alertas Telegram apenas, não executa ordens) |
| `check_results.py` | Query rápida ao SQLite (`../claw_v8.db`) para win/loss e stats — corre manualmente, não faz parte do loop |
| `run_loop.sh` | Wrapper que reinicia `main.py` automaticamente (Termux) |

---

## Restrição crítica da conta EU (BNFCR)

**`STOP_MARKET` com `reduceOnly=true` NÃO é suportado.**
Usar sempre `closePosition=true`. Ver `exchange.py:place_stop_market`.

Consequência: só pode haver **um** STOP_MARKET closePosition por símbolo de cada vez.
O profit lock cancela o stop antigo ANTES de colocar o novo. Ver `execution.py`.

---

## Parâmetros actuais em `config.py`

**Nota:** este bloco reflecte `claw_v8/config.py` no branch `main`; confirmar sempre no ficheiro antes de assumir valores desactualizados aqui.

```python
CAPITAL_MAX_BOT     = 300.0    # capital máximo que o bot usa (alinhado com saldo real)
RISCO_USDC          = 6.0      # risco por trade em USDC
ALAVANCAGEM         = 6        # leverage
MAX_TRADES_ABERTOS  = 5
MAX_MARGEM_TRADE    = 0.30     # máx 30% do capital por posição
PROFIT_LOCK_USDC    = 2.0      # só toca no stop a +2 USDC de lucro REAL (era 0.5 — matava wins)
PROFIT_LOCK_STEP    = 1.0      # move stop a cada +1 USDC (era 0.25 — stop demasiado perto)
TRAILING_LOCK_USDC  = 2.0      # trailing stop activa junto com profit lock a +2 USDC
EMERGENCY_ROI_CUT   = -25.0    # % ROI para corte de emergência (nunca dispara antes do ATR SL)
EMERGENCY_PNL_CUT   = 7.0      # fecha se perda absoluta > 7 USDC (nunca dispara antes do SL técnico)
SCORE_ALERTA        = 6        # Fase 2b: subido de 5→6 (43% STAGNADO com score 5)
SCORE_LONG_MIN      = 6        # LONGs: score mínimo (Fase 2b: era 5)
SCORE_SHORT_MIN     = 7        # SHORTs: score mínimo (Fase 2b: era 6 — SHORTs WR pior)
SCORE_FORTE         = 7        # score forte (Fase 2: era 8)
ADX_TREND_MIN_MAJOR = 22.5     # BTC/ETH/BNB
ADX_TREND_MIN_ALT   = 25.0     # alts com ADX 25+
ATR_MIN_PCT         = 0.003    # ATR mínimo para TRENDING (Fase 2: era 0.0008)
EMA_SLOPE_MIN       = 0.003    # slope mínimo EMA99 (Fase 2: era 0.0005)
SCAN_ALIGN_MIN      = 60       # scan 1×/hora com vela fechada (Fase 2: era 15)
ATR_SL_MULT_MIN     = 2.0      # SL mínimo (1H ATR)
ATR_SL_MULT_MAX     = 2.5      # SL em mercado volátil
ROI_TP_IMEDIATO     = 12.0     # % ROI → fecha imediatamente
PEAK_PROFIT_MIN_USDC= 1.0      # protecção de recuo de pico (Fase 1: era 2.0)
PEAK_DRAWDOWN_PCT   = 0.40     # fecha se recuar ≥40% do pico atingido
MARKOV_SCORE        = 0        # Fase 2: desactivado (adicionava ruído)
LIQUIDATION_GUARD_PCT = 50.0   # margem global > 50% → fecha posições a positivo
SESSOES_UTC         = [(5, 23)]
TOP_N_FUTURES       = 40       # top 40 pares USDC-M por volume
```

---

## Lógica de gestão de posições

### Abertura (`abrir_trade`)
1. Filtros (HTF 4H+1H, Supertrend, Fear&Greed, BB squeeze, CVD, OBI, VWAP, **BTC trend gate para SHORTs**)
2. Score mínimo: LONGs ≥ `SCORE_LONG_MIN` (6), SHORTs ≥ `SCORE_SHORT_MIN` (7)
3. BTC trend gate: SHORTs em alts bloqueados quando BTC 4H EMA9 > EMA21 (tendência bullish)
4. Sizing: `RISCO_USDC=6` / (entry - SL) × entry, cap 30% capital por trade
5. Vol scale: se ATR/price > 0.6%, reduz qty proporcionalmente
6. Escreve `pending_sync[symbol]` → coloca ordem MARKET → coloca STOP_MARKET → coloca TP

### Saídas (`gerir_posicoes`, ciclo de 15s quando há posições)
| Regra | Condição | Acção |
|---|---|---|
| **Profit lock progressivo** | PnL ≥ 2.0 USDC | Move SL a cada +1.0 USDC. Aplica-se a **trades do bot e a posições externas** |
| **Trailing lock** | PnL ≥ 2.0 USDC | Activa simultaneamente com profit lock — trailing stop |
| **MINIMAL_ROI** | Desactivado (`[]`) — cortava winners prematuramente |
| **PEAK_DRAWDOWN** | PnL atingiu ≥1 USDC + recuou ≥40% do pico + sinal fraco | Fecha — protege lucro de recuos |
| **GRAD_EXIT** | 3-5h + perda > 1.5 USDC + sinal fraco | Corte antecipado de perdas lentas (Fase 2b: era 4-8h) |
| **SIGNAL_INV** | Sinal oposto score≥8 após 1h (sem profit lock) | Fecha tudo |
| **STAGNADO** | 5-7h + PnL < 0.5 + sinal não confirma | Fecha (7h+ incondicional) (Fase 2b: era 8-10h) |
| **EMERGENCY_PNL** | Perda > 6.5 USDC absolutos | Fecha imediatamente |
| **EMERGENCY_ROI** | ROI ≤ -25% | Fecha imediatamente (nunca dispara antes do ATR SL) |
| **Software SL** | price ≤ sl (LONG) / price ≥ sl (SHORT) | Fecha via MARKET (grace period de 3min) |

**Fase 1 (2026-08-06):** BREAKEVEN_1R, TP1 (2R), TP2 (3R) removidos — código morto, nunca disparavam. STAGNADO estendido de 6h→8h. Saída graduada adicionada. PEAK_DRAWDOWN corrigido (bug que o tornava impossível). `ROI_TP_IMEDIATO` (12%) continua activo.

**Profit lock alargado (2026-08-10):** PROFIT_LOCK_USDC 0.5→2.0, PROFIT_LOCK_STEP 0.25→1.0. Razão: com step 0.25 o stop ficava a ~0.04% do preço — ruído normal de 1H (0.1-0.5%) batia imediatamente, fechando winners a +0.7/+0.8 USDC. Agora o SL original baseado em ATR fica intacto até +2 USDC de lucro real, permitindo que as trades respirem e corram a +3, +4, +6 USDC. MINIMAL_ROI desactivado (`[]`) pelo mesmo motivo — cortava lucros a +0.8 USDC enquanto perdas corriam a -3/-6 USDC.

### Relatório diário
`_relatorio_diario` corre normalmente às 23:00 UTC e escreve `status.json` + `status_history.jsonl`. O último dia reportado (`ultimo_relatorio_dia`) é persistido no SQLite; se o bot esteve em baixo à hora do relatório (IP bloqueado, restart), faz **catch-up imediato** no primeiro ciclo do dia seguinte em vez de saltar o dia.

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
- **Profit lock activo**: a partir de `PROFIT_LOCK_USDC` (+2.0 USDC) o bot coloca/move um `STOP_MARKET closePosition` a cada `PROFIT_LOCK_STEP` (+1.0 USDC), igual ao que faz nas trades do próprio bot
- **Software stop enforcement**: se o stop da exchange falhar, o bot fecha via MARKET assim que o PnL cai abaixo do nível já protegido pelo lock (ver bug #13) — antes disso só actualizava o stop, nunca reagia à reversão
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

### 12. Loop principal ficava preso indefinidamente (sem trades há horas, `status.json` nunca actualizava)
- **Causa**: o watchdog (`main.py`) só enviava alerta no Telegram quando o loop ficava 5min sem heartbeat, mas nunca reiniciava o processo — bot ficava preso (provavelmente em `_relatorio_diario`, que corre uma vez por dia às 23:00 UTC e nunca mais actualizou desde Jun-03)
- **Fix**: watchdog agora força `os._exit(1)` ao detectar 5min sem heartbeat; novo `run_loop.sh` reinicia automaticamente o `main.py` sempre que ele terminar (Termux não tem systemd/cron). Arrancar sempre via `run_loop.sh`, nunca `python -u main.py` directamente.

### 13. Profit lock não reagia quando o stop da exchange falhava (posições externas)
- **Causa**: quando o profit lock estava activo mas o STOP_MARKET na exchange falhou ("SOFTWARE ⚠️"), o bot continuava a mover o nível protegido para cima mas nunca fechava quando o preço revertia abaixo desse nível
- **Fix**: a cada ciclo verifica se PnL caiu abaixo do lock e fecha imediatamente via MARKET (`main.py`)
- **GitHub**: SHA a364799

### 14. Trades do próprio bot sem profit lock progressivo
- **Causa**: o profit lock a cada +0.5 USDC só existia para posições externas; trades do bot podiam chegar a +1.5 USDC e reverter até ao SL original (perda real registada: -2.56 USDC)
- **Fix**: mesmo mecanismo de lock progressivo + enforcement por software aplicado a `trades_abertos` (não só `posicoes_externas`); breakeven_1R e TP1/TP2 já não fazem downgrade do stop se o profit lock o moveu mais acima (`execution.py`)
- **GitHub**: SHA f65fb83

### 15. Relatório diário saltava dias quando o bot estava em baixo às 23:00 UTC
- **Causa**: `_relatorio_diario` só corria exactamente às 23:00 UTC; se o processo estivesse parado nessa hora (IP bloqueado, restart), o dia ficava sem relatório em `status.json`/`status_history.jsonl`
- **Fix**: detecta `ultimo_relatorio_dia` (SQLite) diferente de "ontem" e gera catch-up imediato no primeiro ciclo do dia seguinte (`main.py`)
- **GitHub**: SHA ae6030e

### 16. TP na exchange cancelava o SL — stops desapareciam em TODOS os trades
- **Causa**: `place_take_profit` usava `closePosition=true` via `/fapi/v1/algoOrder`, igual ao `place_stop_market`; como BNFCR só permite UM `closePosition` por símbolo, ao colocar o TP ~2s depois do SL, o TP substituía o SL — cada trade ficava sem stop loss
- **Custo real**: saldo caiu de 310 → 195 USDC (3 SHORTs sem SL: ETHUSDC -6.58, XRPUSDC -6.59, SOLUSDC -7.64, mais trades subsequentes sem protecção)
- **Fix**: removida a chamada `place_take_profit` de `abrir_trade` em `execution.py`; TP passa a ser gerido inteiramente por software (ROI_TP_IMEDIATO 12%, TP1 a 2R, TP2 a 3R, profit lock progressivo, TIME_TP)
- O SL na exchange (`place_stop_market`) mantém-se como única ordem `closePosition` por símbolo

---

## Regras importantes que NÃO mudar

1. `reduceOnly=true` não funciona nesta conta → usar sempre `closePosition=true`
2. Só pode haver **um** STOP_MARKET closePosition por símbolo de cada vez — **NUNCA colocar TP como closePosition** (bug #16: cancela o SL); TP é sempre por software
3. `_fechar_com_retry` — 3 tentativas antes de registar fecho (evita posições órfãs)
4. `place_stop_market` usa `/fapi/v1/algoOrder` (orderType+algoId) — Binance rejeitou o endpoint regular para contas BNFCR (SHA ef11229)
5. `get_balance` usa `/fapi/v2/account` assets[].marginBalance com fallback totalMarginBalance
6. Nunca mostrar credenciais no chat
7. NUNCA push para main sem confirmar com o utilizador

---

## Resto do repositório — fora do âmbito do bot

Este repositório (`hltv27/blank-app`) começou como um template Streamlit em branco e acumulou vários subprojectos não relacionados. **Não editar nem assumir relação com o Claw Agent** a menos que explicitamente pedido:

| Caminho | O que é | Estado |
|---|---|---|
| `claw_v8/` | **Claw Agent v8 — o bot descrito neste documento** | Activo |
| `claw_agent_v7.py`, `main.py` (raiz), `claw_v8_single.py` | Versões anteriores do bot (v7 monolítico, v8 em ficheiro único) | Arquivadas — não usar, mantidas por referência histórica |
| `spot_signal.py` | Bot de sinais Binance Spot standalone (só alertas Telegram, não abre ordens) | Independente do `claw_v8/spot_scanner.py`; verificar qual está em uso antes de mexer |
| `affiliate_bot/`, `bot.py`, `start_bot.sh`, `stop_bot.sh`, `setup_termux.sh` | Bot de afiliados (AliExpress → Telegram/Instagram/TikTok), ver `PROGRESSO.md` | Projecto separado, infra própria (Hetzner/Termux) |
| `douroetamega/`, `guidedbynature/`, `guidedbynature_crawler.py`, `find_api.py` | Web crawlers para projectos de scraping distintos | Projectos separados |
| `streamlit_app.py`, `.devcontainer/` | Boilerplate do template original do repo | Não usado pelo bot |
| `biblioteca_cw` | Ficheiro solto vazio (1 byte) | Resíduo, sem conteúdo |
| `portfolio_tracker.json` | Snapshots manuais do portfólio pessoal do utilizador (múltiplas carteiras/exchanges), mantido por sessões Claude via commits directos | Dados, não código — não é lido pelo `claw_v8` |
| `PROJECTO_CLAW_COMPLETO.md`, `CLAW_MASTER.md`, `CHANGELOG.md`, `SESSAO_*.md`, `.claude/memory/*.md` | Documentação histórica/notas de sessões anteriores sobre o bot | Podem estar desactualizadas — `CLAUDE.md` (este ficheiro) e `claw_v8/status.json` são as fontes de verdade actuais; `.claude/memory/` reflecte estado de 2026-06-15, já ultrapassado pelas secções acima |

## Convenções de desenvolvimento (Claw Agent v8)

- **Mensagens de commit**: descritivas, em português, focadas no "porquê" (ex: `Profit lock progressivo para trades do bot (+0.5 USDC)`), seguidas de rodapé `Co-Authored-By` — ver `git log` para o estilo exacto
- **Sem suite de testes automatizada** para `claw_v8/` — validação é feita por: `backtest.py` (dados históricos), `check_results.py` (consulta ao SQLite em produção), e observação directa via Telegram/`status.json` depois do deploy
- **Sem CI de lint/type-check** — o único workflow GitHub Actions (`run_bot.yml`) corre o bot em produção, não testes
- Alterações a `config.py` ou lógica de saída/entrada devem, idealmente, ser validadas com `backtest.py` antes do deploy, dado que afectam dinheiro real
- Este projecto não usa `requirements.txt` da raiz (esse é do `affiliate_bot/`) — `claw_v8` depende apenas de `requests` (ver imports em `exchange.py`); confirmar dependências reais no código antes de assumir
