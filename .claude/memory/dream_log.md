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

## Ciclo #3 — 2026-08-27

**Trigger:** Manual pelo utilizador ("Faz uma condensação da conversa até aqui").
**Sessão:** Activação completa do affiliate bot — GitHub Pages, GITHUB_TOKEN, Facebook (parcial).

**Feito nesta sessão:**
- ✅ GitHub Pages activado em hltv27.github.io/blank-app/ (branch claude/affiliate-bot-automation-5rsFF, /docs)
- ✅ GITHUB_TOKEN adicionado ao VPS .env (via python3 getpass, 40 chars)
- ✅ website.py branch corrigido: main → claude/affiliate-bot-automation-5rsFF (SHA 6573ae1)
- ✅ PR #25 criado (draft)
- ✅ products.json actualizado via GitHub API (testado, Website: True)
- ❌ Facebook: token gerado mas 403 Forbidden — pages_manage_posts não activo na app TopDealsBot
- ⚠️ .env linha 15 malformada (tentativas de token falhadas) — inofensivo

**Próxima sessão (Facebook):**
1. developers.facebook.com → TopDealsBot → App Review → Permissions → Adicionar `pages_manage_posts`
2. Gerar novo token no Graph API Explorer com essa permissão incluída
3. Actualizar FACEBOOK_PAGE_TOKEN no VPS com `python3 -c "import getpass..."` (evita mascaramento)

---

## Ciclo #4 — 2026-09-03

**Trigger:** Manual pelo utilizador ("relembra o histórico e faz .md").
**Sessão:** Continuação do Ciclo #3 — Facebook resolvido, .env limpo, metal bot planeado.

**Feito nesta sessão:**
- ✅ Facebook resolvido: Access Token Tool → app **TopDealsGadget** (já tinha `pages_manage_posts`) → User Token → `me/accounts` → Page Token 207 chars → `Facebook: True`
- ✅ .env limpo: removidas linhas 15-16 malformadas (restos de tentativas falhadas de token insertion)
- ✅ Affiliate bot completo: Telegram ✅ + Instagram ✅ + Facebook ✅ + Website ✅

**Lições aprendidas:**
- Graph API Explorer NÃO mostra `pages_manage_posts` se a app não tiver o Use Case correcto
- Solução: **Access Token Tool** lista todas as apps → TopDealsGadget já tinha a permissão
- `python3 getpass.getpass()` obrigatório para tokens longos — Claude Code mascara tokens no chat

**Metal bot planeado:**
- @internationalmetall (60k seguidores, metal music)
- 1 post/dia: YouTube API v3 → yt-dlp → Claude Haiku caption → instagrapi
- Aguarda: YouTube Data API v3 key + credenciais Instagram da conta

**Actualizações:**
- `context.md` — reescrito: parâmetros CLAW corrigidos, affiliate bot all-OK, Facebook fix, metal bot planeado
- `dream_log.md` — este ciclo adicionado

**Próxima sessão (metal bot):**
1. Utilizador obtém YouTube Data API v3 key em console.cloud.google.com
2. Adicionar credenciais @internationalmetall ao VPS .env via getpass
3. Construir `metal_bot/` no repo

---
