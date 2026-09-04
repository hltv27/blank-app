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

## Ciclo #5 — 2026-09-03 (noite)

**Trigger:** Manual pelo utilizador ("Compacta e faz .md").
**Sessão:** Bot totalmente parado (RapidAPI 429) → diagnosticado e corrigido → publicação manual de 16 produtos → descoberta de sessão Instagram expirada.

**Feito nesta sessão:**
- ✅ Diagnosticado "tudo parado": RapidAPI a dar 429 em todos os pedidos desde ~30/08 (rate limit do plano Basic, não quota mensal — essa estava a 0%)
- ✅ Fix: `get_any_products()` fallback para produtos stale do DB; `refresh_product_cache` pára ao 1º 429; reduzido a 1 keyword/niche (4 pedidos/dia); `QuotaExceededError` explícita (commits 7f8f77c, 6032943)
- ✅ Bot voltou a publicar imediatamente com os 531+ produtos existentes
- ✅ Criados `post_now.py` e `publish_bulk.py` — publicação manual de produtos específicos por item ID (fora do scheduler)
- ✅ Publicados 16 produtos manualmente que o utilizador foi enviando (links AliExpress → extraído item ID → niche → publish_bulk)
- ⚠️ Descoberto: Instagram não publica desde 27/08 (`login_required`, 403 no upload) — sessão expirada
- ❌ Tentativa de renovar via `cl.login()` no VPS falhou mesmo com password correta (confirmado: login funciona no browser do telemóvel) — Instagram bloqueia login novo vindo de IP de datacenter
- 📝 BUG-AFF-P2 registado em bugs.md — fix requer `sessionid` extraído de um browser (PC) + `cl.login_by_sessionid()`. Aguarda utilizador ter PC disponível.

**Lições aprendidas:**
- RapidAPI free tier: "Quota Usage 0%" no dashboard é quota MENSAL — não protege contra rate limit por minuto/segundo. Espaçar pedidos (10-15s) é essencial mesmo com quota disponível
- Instagram bloqueia `instagrapi.login()` a partir de IPs de VPS/datacenter mesmo com credenciais corretas — usar sempre `login_by_sessionid()` para servidores, nunca login fresco por password
- Para publicação manual de produtos (fora do fetch automático), usar o endpoint `item_detail_2` da RapidAPI com o item ID extraído do URL do produto
- Links de afiliado gerados (aliexpress.com/item/ID?aff_fcid=hltv27) são preferíveis a short links (s.click.aliexpress.com) para posts — parecem mais confiáveis e não dependem de um encurtador externo

**Actualizações:**
- `context.md` — estado Instagram marcado 🔴, secção RapidAPI fix documentada, secção publicação manual adicionada
- `bugs.md` — BUG-AFF-P2 adicionado (Instagram sessão expirada, aguarda sessionid)
- `dream_log.md` — este ciclo

**Próxima sessão:**
1. Se utilizador enviar `sessionid` do Instagram: renovar com `cl.login_by_sessionid()` no VPS, testar post, `systemctl restart affiliatebot`
2. Continuar metal bot (@internationalmetall) — ainda aguarda YouTube API key

---
