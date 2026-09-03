# Bugs — CLAW Agent v8

## 🔴 Pendentes

### BUG-AFF-P2: Instagram sessão expirada — login via VPS bloqueado
**Ficheiro:** `affiliate_bot/publishers/instagram.py`, `instagram_session.json`
**Sintoma:** Desde 27/08 todos os posts em Instagram falham com `{"message":"login_required","status":"fail"}` (403 no upload de foto). A sessão gravada expirou.
**Causa:** Tentativa de novo login via instagrapi no VPS falha com `"Sorry, there was a problem with your request"` mesmo com password correta (confirmado — login funciona no browser do telemóvel). Motivo provável: Instagram bloqueia login novo vindo de IP de datacenter/VPS (178.105.52.219) como suspeito.
**Conta:** @hugo.deals | Password confirmada: correcta (login OK no browser mobile)
**Fix pendente:** Extrair `sessionid` de uma sessão de browser válida (PC, Chrome DevTools → Application → Cookies) e usar `cl.login_by_sessionid(SESSIONID)` no VPS em vez de `cl.login(user, pass)` — evita o processo de login que está a ser bloqueado.
**Status:** Aguarda utilizador ter acesso a PC para extrair sessionid.
**Impacto:** Instagram (4 posts/dia) não publica. Telegram e Facebook não afectados.

### ~~BUG-AFF-P1~~: Facebook `pages_manage_posts` — ✅ RESOLVIDO (2026-08-27)
Token obtido via Access Token Tool (TopDealsGadget app, User Token com pages_manage_posts) → me/accounts → Page Token 207 chars. Facebook a publicar.

---

### BUG-P1: CAPITAL_MAX_BOT desactualizado (⚠️ provavelmente já corrigido)
**Ficheiro:** `config.py`
**Status:** CLAUDE.md indica `CAPITAL_MAX_BOT = 370.0` — verificar se já está correcto no ficheiro antes de agir.

### BUG-P2: VETO_SR_LONG / VETO_SR_SHORT — revisar limiares
**Ficheiro:** `config.py` linhas 68-69, `strategy.py` linhas 59-63
**Problema:** `STOCH_VETO_LONG = 95.0` e `STOCH_VETO_SHORT = 2.5` — praticamente nunca vedam nada (StochRSI raramente chega a 95 ou 2.5).
**Pergunta:** O utilizador quer que o veto seja mais agressivo? Valores típicos seriam 80/20.
**Impacto:** Possível — se StochRSI for usado como filtro real, limiares actuais são quase inúteis.
**Status:** Em análise — aguarda decisão do utilizador.

### BUG-P3: place_take_profit — verificar se está a funcionar
**Ficheiro:** `exchange.py`
**Problema:** Utilizador reporta como pendente. Historicamente: após SHA ef11229 o TP foi movido para `/fapi/v1/order` (errado para BNFCR) → corrigido em cb6021b de volta para `/fapi/v1/algoOrder`.
**Status:** Aparentemente corrigido (SHA cb6021b, a1443ba). Verificar nos logs se `tp_order_id` está a ser preenchido nas novas entradas. Se logs mostrarem `tp_order_id: None` → ainda quebrado.

---

## ✅ Corrigidos

### BUG-F1: STOP_MARKET conflito com TP (profit lock spam)
Profit lock tentava colocar 2º closePosition sem cancelar o 1º. Fix: cancela primeiro, depois coloca novo. | SHA: ~d691f48

### BUG-F2: Bot geria posições manuais
`pending_sync` não persistia após restart → posições do bot tratadas como manuais. | SHA: d691f48

### BUG-F3: Profit lock spam Telegram
Stop falhava → não actualizava nível → ciclo infinito. Fix: avança `profit_lock_level` em memória independentemente. | SHA: d691f48

### BUG-F4: Guards fechavam trades manuais
Fix: todos os guards verificam `if sym not in trades_bot: continue`. | SHA: d691f48

### BUG-F5: `abrir_trade` fechava posição quando SL falhava silenciosamente
Fix: abort explícito + alerta Telegram "TRADE ABORTADO". | Session Jun-12

### BUG-F6: `posicoes_externas` e `pending_sync` perdidos em restart
`load_memory()` não incluía estas chaves → reset a `{}`. | SHA: d691f48

### BUG-F7: STAGNADO fechava posições perdedoras (ex: -2 USDC)
Condição antiga `pnl < 0.5`. Fix: `-0.5 <= pnl < 1.0` e mínimo 60min. | SHA: 92e1a97

### BUG-F8: Stop/TP com preço errado — SYMBOL_PRECISION em vez de PRICE_PRECISION
ZECUSDC ex: precisão de qty=4 mas Binance exige price precision=2. Fix: PRICE_PRECISION dedicado. | SHA: de19dff

### BUG-F9: SCORE_ALERTA=4 demasiado permissivo
Fix: aumentado para 6. | SHA: e0003ea

### BUG-F10: MARGEM CRÍTICA falso positivo (cross-collateral USDT-M)
Fix: usar `get_margin_ratio_global()`. | SHA: 0487fd0

### BUG-F11: `algoType: "CONDITIONAL"` inválido no algoOrder
Causava "Mandatory parameter 'type'" em todos os stops. Fix: remover parâmetro. | SHA: a1443ba

### BUG-F12: TIME_TP cortava winners prematuramente
Fechava posições a 5% ROI após 10min antes do TP da exchange. Fix: removido. | SHA: cb6021b

### BUG-F13: `get_balance()` retornava None ("Saldo: n/d")
Fix: tentar múltiplos campos + fallback totalMarginBalance. | SHA: a1443ba

### BUG-F14: auto_deploy.sh não tinha cron configurado
Bot nunca foi actualizado automaticamente desde arranque em Jun-04. Fix: `crontab -e`. | Session Jun-12

### BUG-F15: auto_deploy.sh usava `python` em vez de `python3`
Bot reiniciado com executável errado. Fix: corrigido para `python3`. | SHA: bd30f04
