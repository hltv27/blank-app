# Contexto — hltv27/blank-app (2026-08-26)

---

## CLAW Agent v8 — Bot Binance Futures

**Onde corre:** Termux (Android, dados móveis — IP instável, sem IP fixo)
**Arranque:** `cd ~/blank-app && git pull origin main && cd claw_v8 && ./run_loop.sh`
**Log:** `~/claw.log` | **DB:** `claw_v8.db`
**Branch produção:** `main` — NUNCA push para main sem confirmar com o utilizador

### Parâmetros actuais (config.py — source of truth: CLAUDE.md)
```
CAPITAL_MAX_BOT     = 370.0
RISCO_USDC          = 6.0
ALAVANCAGEM         = 6
MAX_TRADES_ABERTOS  = 5
MAX_MARGEM_TRADE    = 0.30
PROFIT_LOCK_USDC    = 0.5     (activa lock a +0.5 USDC)
PROFIT_LOCK_STEP    = 0.25    (move stop a cada +0.25 USDC)
TRAILING_LOCK_USDC  = 2.0     (muda para trailing a +2 USDC)
EMERGENCY_ROI_CUT   = -25.0%
EMERGENCY_PNL_CUT   = 7.0 USDC
SCORE_LONG_MIN      = 6
SCORE_SHORT_MIN     = 8       (SHORTs exigem score mais alto)
SCORE_FORTE         = 8
ADX_TREND_MIN_MAJOR = 22.5
ADX_TREND_MIN_ALT   = 25.0
RSI_OVERSOLD        = 40.0
RSI_OVERBOUGHT      = 60.0
ROI_TP_IMEDIATO     = 12.0%
PEAK_PROFIT_MIN_USDC= 1.0
PEAK_DRAWDOWN_PCT   = 0.40
TOP_N_FUTURES       = 40
SESSOES_UTC         = [(5, 23)]
```

### Restrições críticas da conta BNFCR
1. `STOP_MARKET reduceOnly=true` → NÃO funciona → usar `closePosition=true`
2. Só **1** STOP_MARKET closePosition por símbolo de cada vez
3. **NUNCA colocar TP como closePosition** (cancela o SL — BUG-F16) → TP é só software
4. Stops usam `/fapi/v1/algoOrder`

### IP instável (Termux/dados móveis)
Quando muda o IP → Binance bloqueia → bot envia `🔒 IP bloqueado` 1x/10min.
Fix: Binance → API Management → adicionar IP da mensagem à whitelist.
Não é bug do bot, vai repetir-se.

### Kill switch
`touch ~/blank-app/claw_v8/KILL_SWITCH`

---

## Affiliate Bot — Bot de Afiliados AliExpress

**Onde corre:** VPS `178.105.52.219` como serviço systemd `affiliatebot.service`
**Caminho:** `/root/affiliate-bot/` | **Config:** `.env`
**Branch dev:** `claude/affiliate-bot-automation-5rsFF`
**Repo code:** `affiliate_bot/` em `hltv27/blank-app`

### Estado actual (2026-08-26)
| Plataforma | Estado | Notas |
|------------|--------|-------|
| Telegram   | ✅ OK  | 16 jobs agendados via APScheduler |
| Instagram  | ✅ OK  | Sessão renovada, posta em @hugo.deals |
| Facebook   | ❌ PENDENTE | Token sem `pages_manage_posts` |
| TikTok     | ⚪ Não configurado | — |

### Facebook — próximo passo (sessão 2026-08-26 parou aqui)
Tenho um `long_lived_token` com `pages_manage_posts` obtido via OAuth:
```
EAATlarffxCMBScjj09ha35Mg3JDSonoZAqh0tOAMO2AOanrLkWNtTZB69jSYZAG2lgRNhKqnmxoMUvE5frmYsGcaQdAdZBYFN8JqdXN22sJRSoGWNP2dXbv0iVqZCLZBWc761BxOHhUtf5NzBYlMZAbNJkKj8Wg5apIxMMgZAaNctnFWoXoJTgqM5JyokKZASuxknpJXU61EcGRraryjBuIz8wKF3PcLEGKWh65StCFs000zL
```
**Falta:**
1. Graph API Explorer → colar token → query `me/accounts?fields=name,id,access_token`
2. Copiar `access_token` da linha "Top Deals Gadget" (page ID: 1189959324190844)
3. No VPS: `sed -i 's/FACEBOOK_PAGE_TOKEN=.*/FACEBOOK_PAGE_TOKEN=<novo_token>/' /root/affiliate-bot/.env`
4. `systemctl restart affiliatebot` e confirmar com `python -c "from affiliate_bot import publishers; print(publishers.facebook.test_connection())"`

### Detalhes Facebook App
- App ID: `1378146421031971`
- Página: "Top Deals Gadget" (ID: `1189959324190844`)
- Admin: Hugo Vaz (hugoluisvaz@gmail.com) — confirmado via facebook.com/pages
- `pages_manage_posts` está em Use Cases ("Ready for testing") — não aparece no dropdown do Graph API Explorer (UI bug), mas funciona via URL OAuth manual

### Niches configurados
`tech_gadgets`, `home_smart`, `fitness_health`, `fashion_accessories`
Cache refresh: 06:00 UTC diário. Posts: 7:00–23:00 UTC.

### Bug corrigido nesta sessão
`scheduler.py` — `mark_cache_refreshed()` só chamado quando `len(products) > 0`.
Antes: 429 silencioso → cache marcada como actualizada → loop infinito sem produtos.
SHA: a360a70 | Branch: `claude/affiliate-bot-automation-5rsFF`
