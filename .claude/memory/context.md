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
**Branch dev:** `claude/affiliate-bot-automation-5rsFF` | **PR:** #25 (draft)
**Repo code:** `affiliate_bot/` em `hltv27/blank-app`

### Estado actual (2026-08-27)
| Plataforma | Estado | Notas |
|------------|--------|-------|
| Telegram   | ✅ OK  | 8 posts/dia agendados via APScheduler |
| Instagram  | ✅ OK  | 4 posts/dia em @hugo.deals |
| Facebook   | ❌ PENDENTE | Token tem 403 — falta `pages_manage_posts` na app |
| Website    | ✅ OK  | GitHub Pages em hltv27.github.io/blank-app/ |
| TikTok     | ⚪ Não configurado | — |

### Facebook — próximo passo
**Problema:** Token gerado pelo Graph API Explorer dá 403 porque `pages_manage_posts` não está activo na app TopDealsBot.

**Fix:**
1. Ir a developers.facebook.com → **My Apps → TopDealsBot**
2. Menu esquerdo: **App Review → Permissions and Features**
3. Encontrar `pages_manage_posts` → clicar **"Request"** ou **"Add"**
4. Voltar ao **Graph API Explorer** → agora deve aparecer no dropdown
5. Gerar novo token com `pages_manage_posts` + `pages_show_list` + `pages_read_engagement`
6. Query `me/accounts?fields=name,id,access_token` → copiar token da página
7. No VPS (usar `python3 -c "import getpass..."` para evitar mascaramento):
   ```bash
   python3 -c "
   import getpass, re
   tok = getpass.getpass('Token: ')
   with open('/root/affiliate-bot/.env','r') as f: content = f.read()
   content = re.sub(r'FACEBOOK_PAGE_TOKEN=.*\n?', '', content)
   content += 'FACEBOOK_PAGE_TOKEN=' + tok + '\n'
   with open('/root/affiliate-bot/.env','w') as f: f.write(content)
   print('OK, comprimento:', len(tok))
   "
   ```
8. `systemctl restart affiliatebot`

**Detalhes Facebook App:**
- App ID: `1378146421031971`
- Página: "Top Deals Gadget" (ID: `1189959324190844`)
- Admin: Hugo Vaz (hugoluisvaz@gmail.com)

### GitHub Pages (website de deals)
- URL: **https://hltv27.github.io/blank-app/**
- Serve de: branch `claude/affiliate-bot-automation-5rsFF` → pasta `/docs`
- Actualiza automaticamente após cada post (via `publishers/website.py` + GITHUB_TOKEN)
- `GITHUB_TOKEN` configurado no VPS .env (token `ghp_F0l6...`, 40 chars)
- ⚠️ `.env` tem uma linha malformada (linha 15) — inofensivo mas limpar com: `grep -n "^[^A-Z#]" /root/affiliate-bot/.env`

### Niches configurados
`tech_gadgets`, `home_smart`, `fitness_health`, `fashion_accessories`
Cache: 72h TTL, 531 produtos em DB, refresh 06:00 UTC diário. Posts: 7:00–23:00 UTC.
Tracking ID AliExpress: `hltv27` (via `ALIEXPRESS_TRACKING_ID` em .env)
