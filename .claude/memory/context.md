# Contexto — hltv27/blank-app (2026-09-03, actualizado à noite)

---

## CLAW Agent v8 — Bot Binance Futures

**Onde corre:** VPS `178.105.52.219` — IP fixo whitelisted na Binance
**Arranque:** `cd /root/blank-app && git pull origin main && pkill -f "python.*main.py"; sleep 2 && cd claw_v8 && PYTHONUNBUFFERED=1 nohup python3 main.py > /root/claw.log 2>&1 &`
**Log:** `/root/claw.log` | **DB:** `claw_v8.db`
**Branch produção:** `main` — NUNCA push para main sem confirmar com o utilizador

### Parâmetros actuais (config.py — source of truth: CLAUDE.md)
```
CAPITAL_MAX_BOT     = 300.0
RISCO_USDC          = 5.0
ALAVANCAGEM         = 6
MAX_TRADES_ABERTOS  = 5
MAX_MARGEM_TRADE    = 0.20
PROFIT_LOCK_USDC    = 1.0
PROFIT_LOCK_STEP    = 0.5
TRAILING_LOCK_USDC  = 4.0
EMERGENCY_ROI_CUT   = -5.5%
EMERGENCY_PNL_CUT   = 3.0 USDC
SCORE_ALERTA        = 6
SCORE_FORTE         = 6
ADX_TREND_MIN_MAJOR = 22.5
ADX_TREND_MIN_ALT   = 30.0
ROI_TP_IMEDIATO     = 7.0%
TOP_N_FUTURES       = 150
SESSOES_UTC         = [(5, 23)]
```

### Restrições críticas da conta BNFCR
1. `STOP_MARKET reduceOnly=true` → NÃO funciona → usar `closePosition=true`
2. Só **1** STOP_MARKET closePosition por símbolo de cada vez
3. **NUNCA colocar TP como closePosition** (cancela o SL) → TP é só software
4. Stops usam `/fapi/v1/algoOrder`

### Kill switch
`touch /root/blank-app/claw_v8/KILL_SWITCH`

---

## Affiliate Bot — Bot de Afiliados AliExpress

**Onde corre:** VPS `178.105.52.219` como serviço systemd `affiliatebot.service`
**Caminho:** `/root/affiliate-bot/` | **Config:** `.env`
**Branch dev:** `claude/affiliate-bot-automation-5rsFF` | **PR:** #25 (draft)
**Repo code:** `affiliate_bot/` em `hltv27/blank-app`

### Estado actual (2026-09-03 noite)
| Plataforma | Estado | Notas |
|------------|--------|-------|
| Telegram   | ✅ OK  | 8 posts/dia — canal @TopDealsGadgetss |
| Instagram  | 🔴 PARADO | @hugo.deals — sessão expirada desde 27/08. Ver BUG-AFF-P2 em bugs.md |
| Facebook   | ✅ OK  | 4 posts/dia — "Top Deals Gadget" (ID: 1189959324190844) |
| Website    | ✅ OK  | hltv27.github.io/blank-app/ — auto-actualizado após cada post |
| TikTok     | ⚪     | Não configurado |

### RapidAPI — quota/rate limit (resolvido 2026-09-03)
**Sintoma:** Bot parado desde 30/08 — todos os pedidos à AliExpress DataHub davam 429 (rate limit, não quota mensal — essa estava a 0%).
**Causa:** Cache refresh diário disparava 12 pedidos (3 keywords × 4 niches) em ~30s — excedia o rate limit do plano Basic. Além disso, cada post cycle com cache expirado tentava a API de novo, agravando o problema.
**Fix aplicado (commits 7f8f77c, 6032943):**
- `database.py`: `get_any_products()` — fallback para produtos antigos do DB, sem chamar API
- `scheduler.py`: `run_post_cycle` usa produtos stale do DB antes de tentar API; `refresh_product_cache` pára ao 1º 429 em vez de continuar a tentar outros niches
- `aliexpress.py`: `QuotaExceededError` explícita no 429; reduzido para **1 keyword/niche** (4 pedidos/dia em vez de 12), delays aumentados (10s entre keywords, 15s entre niches)
**Resultado:** Bot voltou a publicar imediatamente com os 531+ produtos já no DB.

### Publicação manual de produtos (novo — 2026-09-03)
Scripts para publicar produtos específicos fora do scheduler normal (ex: quando o utilizador encontra uma boa oferta manualmente):
- `affiliate_bot/post_now.py` — publica 1 produto por item ID
- `affiliate_bot/publish_bulk.py` — publica vários de uma vez (fetch paralelo + post sequencial)
  ```bash
  python3 -m affiliate_bot.publish_bulk "1005010063076436:tech_gadgets" "1005007594756946:home_smart" ...
  ```
- Usa `item_detail_2` da RapidAPI para obter título/preço/imagem a partir do item ID
- Gera link de afiliado com `ALIEXPRESS_TRACKING_ID` (hltv27) automaticamente — preferir isto a usar short links (`s.click.aliexpress.com`) porque parecem mais confiáveis a quem vê e não dependem do encurtador
- 16 produtos publicados manualmente nesta sessão via este método

### Facebook — como renovar token (expira ~3 meses)
O token actual (207 chars) foi obtido via **Access Token Tool** (não Graph API Explorer):
1. Ir a developers.facebook.com/tools/accesstoken
2. Seleccionar app **TopDealsGadget** (não TopDealsBot)
3. Copiar o User Token → testar no Graph API Explorer
4. Query `me/accounts?fields=name,id,access_token` → copiar Page Token de "Top Deals Gadget"
5. No VPS via `python3 -c "import getpass, re; tok = getpass.getpass('Token: '); ..."` (evitar mascaramento)
6. `systemctl restart affiliatebot`

**Detalhes Facebook App:**
- App usada: TopDealsGadget (tem `pages_manage_posts` nos scopes do User Token)
- Página: "Top Deals Gadget" (ID: `1189959324190844`)
- TopDealsBot NÃO tem pages_manage_posts configurado — não usar

### GitHub Pages (website de deals)
- URL: **https://hltv27.github.io/blank-app/**
- Serve de: branch `claude/affiliate-bot-automation-5rsFF` → pasta `/docs`
- Actualiza automaticamente após cada post (via `publishers/website.py` + GITHUB_TOKEN)
- `GITHUB_TOKEN` configurado no VPS .env (40 chars, `ghp_F0l6...`)
- `website.py` usa `BRANCH = "claude/affiliate-bot-automation-5rsFF"` (corrigido SHA 6573ae1)

### Niches configurados
`tech_gadgets`, `home_smart`, `fitness_health`, `fashion_accessories`
Cache: 72h TTL. Posts: 7:00–23:00 UTC. Tracking ID AliExpress: `hltv27`

### Comandos úteis no VPS
```bash
systemctl status affiliatebot
systemctl restart affiliatebot
journalctl -u affiliatebot -n 50 --no-pager
```

---

## Metal Bot — Bot de Conteúdo Metal (PLANEADO)

**Conta Instagram:** @internationalmetall (60k seguidores, conteúdo de metal)
**Objectivo:** 1 post/dia automático com vídeos virais de metal do YouTube
**Estado:** Planeado — ainda não construído

### O que faz (versão simples)
1. Pesquisa YouTube Data API v3 por vídeos de metal viral (>50k views, últimas 48h)
2. Download com yt-dlp (primeiros 60s se Reel, ou thumbnail para post normal)
3. Gera legenda com Claude Haiku (ou fallback simples)
4. Publica via instagrapi com sessão separada da @hugo.deals
5. APScheduler: 1 post/dia às 18:00 UTC

### O que falta para começar
1. **YouTube Data API v3 key** — console.cloud.google.com → APIs & Services → YouTube Data API v3 → Credentials → API Key
2. **Credenciais @internationalmetall** — adicionar ao VPS .env via getpass (NUNCA no chat)
3. **Construir módulo** `metal_bot/` no repo

### Arquitectura planeada
```
metal_bot/
  config.py          — YOUTUBE_API_KEY, INSTA_METAL_USER, INSTA_METAL_PASS
  fetchers/youtube.py — search API + scoring por views/engagement
  publishers/instagram_metal.py — instagrapi, sessão separada
  scheduler_metal.py — CronTrigger diário 18:00 UTC
bot_metal.py         — entry point (systemd service metal-bot.service)
```
