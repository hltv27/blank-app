# Dream Log — CLAW Agent v8

---

## Ciclo #1 — 2026-06-15

**Trigger:** Inicialização manual pelo utilizador.
**Estado ao iniciar:** 13 trades, +7.09 USDC, 61.5% WR. Saldo real ~165 USDC.

**Memória consolidada:**
- Arquitectura completa lida e mapeada (config, execution, exchange, strategy, filters, risk, storage, indicators, markov)
- 15 bugs corrigidos documentados em bugs.md
- 3 bugs pendentes identificados (CAPITAL_MAX_BOT, VETO_SR, place_take_profit verificação)
- Decisões técnicas críticas registadas em decisions.md
- Contexto operacional completo em context.md

**Acções tomadas:**
- Criado `.claude/memory/` com 5 ficheiros
- Nenhuma alteração ao código neste ciclo

**Próximas revisões sugeridas:**
1. Verificar nos logs se `tp_order_id` está preenchido nas últimas entradas (BUG-P3)
2. Decidir se STOCH_VETO_LONG/SHORT devem ser mais agressivos (BUG-P2)
3. Actualizar CAPITAL_MAX_BOT para reflectir saldo real (BUG-P1)
4. Após 20-30 trades limpos: avaliar STAGNADO e outras regras de saída

---

## Ciclo #2 — 2026-08-26

**Trigger:** Manual pelo utilizador ("condensa todo o histórico").
**Sessão:** Trabalho no affiliate_bot (Telegram ✅, Instagram ✅, Facebook ❌ pendente).

**Actualizações:**
- `context.md` — reescrito: parâmetros claw_v8 actualizados (370 USDC, novos thresholds Fase 1) + secção affiliate bot com estado e próximo passo Facebook
- `bugs.md` — BUG-P1 marcado como provavelmente já corrigido; BUG-AFF-P1 adicionado (Facebook pages_manage_posts)
- BUG-P3 (place_take_profit): coberto pelo BUG-F16 (TP removido da exchange, só software)

**Próxima sessão (affiliate bot):**
1. Abrir Graph API Explorer com `long_lived_token` de 2026-08-26 (ver context.md)
2. Query `me/accounts?fields=name,id,access_token` → copiar token "Top Deals Gadget"
3. Actualizar FACEBOOK_PAGE_TOKEN no VPS e restart do serviço

---
