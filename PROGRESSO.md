# Affiliate Bot — Progresso & Estado Actual

## O que estamos a construir

Bot automático 24/7 que:
1. Busca produtos no AliExpress (via RapidAPI)
2. Gera imagens de produto (1080x1080) com IA
3. Escreve legendas por plataforma com Claude AI
4. Publica automaticamente em Telegram, Instagram e TikTok
5. Evita repetir produtos (base de dados SQLite)
6. Corre no servidor Hetzner (Claw-bot) sem intervenção humana

---

## Infraestrutura

| Item | Detalhe |
|------|---------|
| Servidor | Hetzner Claw-bot — 2 vCPU, 4 GB RAM, 40 GB disco |
| IP | 178.105.52.219 |
| OS | Ubuntu (Python 3.10.12, Git 2.34.1) |
| Repositório | github.com/hltv27/blank-app |
| Branch | `claude/affiliate-bot-automation-5rsFF` |
| Localização no servidor | `/root/affiliate-bot` |

---

## Nichos escolhidos (4 de 5)

| Niche | Emoji | Keywords principais |
|-------|-------|---------------------|
| Tech & Gadgets | 📱 | earbuds, smartwatch, power bank, gaming mouse |
| Casa & Vida Inteligente | 🏠 | storage, smart plug, robot vacuum, led strip |
| Fitness & Saúde | 💪 | resistance bands, yoga mat, massage gun |
| Moda & Acessórios | 👗 | watch, sunglasses, bracelet, handbag |

---

## Canais de publicação

| Canal | Posts/dia | Dificuldade | Estado |
|-------|-----------|-------------|--------|
| Telegram | 8 | ⭐ Fácil | ⏳ Falta criar canal |
| Instagram | 4 | ⭐⭐⭐ Médio | ⏳ A configurar |
| TikTok | 3 | ⭐⭐⭐⭐ Difícil | ⏳ A configurar |

---

## APIs & Serviços

| Serviço | Propósito | Estado |
|---------|-----------|--------|
| RapidAPI — AliExpress DataHub | Buscar produtos | ✅ Chave obtida |
| AliExpress Portals | Tracking ID para links de afiliado | ⏳ Falta obter Tracking ID |
| Telegram Bot | Publicar no canal | ✅ Token já existe (mesmo do bot de trading) |
| Telegram Canal | Canal de afiliados | ⏳ Falta criar |
| Instagram Graph API | Publicar posts/reels | ⏳ Falta configurar |
| TikTok Content API | Publicar vídeos/fotos | ⏳ Falta configurar |
| Anthropic Claude | Gerar legendas por plataforma | ⏳ Falta obter chave |

---

## Ficheiros criados no repositório

```
affiliate_bot/
├── __init__.py
├── config.py                  ← lê o .env, valida chaves
├── database.py                ← SQLite: produtos, posts, evita repetições (30 dias)
├── scheduler.py               ← APScheduler: distribui posts 7h–23h UTC
├── fetchers/
│   └── aliexpress.py          ← RapidAPI DataHub (substituiu API oficial)
├── generators/
│   ├── content.py             ← Claude Haiku gera legenda por plataforma
│   └── image.py               ← Pillow: card 1080x1080 com cores por niche
├── publishers/
│   ├── telegram.py            ← Telegram Bot API
│   ├── instagram.py           ← Instagram Graph API (2-step publish)
│   └── tiktok.py              ← TikTok Content Posting API v2
└── niches/
    └── config.json            ← 4 nichos, keywords, hashtags, horários

bot.py                         ← entry point: --test / --check / --stats
.env.example                   ← template de configuração
setup_termux.sh                ← instalação para Termux (não necessário — temos VPS)
start_bot.sh                   ← arranque com wake lock (para Termux)
SETUP.md                       ← guia completo de setup
```

---

## Decisões tomadas durante a conversa

### AliExpress API
- **Problema:** A API oficial do AliExpress (portals.aliexpress.com) exige aprovação via OAuth que redireciona para Taobao e dá erro 500 — bug do lado deles.
- **Solução:** Trocámos para **RapidAPI AliExpress DataHub** — sem aprovações, sem OAuth, só uma chave.

### Infraestrutura
- Começámos a pensar em Termux (só telemóvel) mas descobrimos que tens VPS Hetzner.
- O bot de trading já corre 24/7 no mesmo servidor — o affiliate bot corre em paralelo.
- Não é necessário criar novo servidor.

### Plataforma de conteúdo
- Conteúdo: **Imagens geradas com Pillow + legendas com Claude Haiku** (mais barato e rápido que Opus/Sonnet).
- Cada plataforma recebe uma legenda diferente (Telegram: directo; Instagram: hashtags; TikTok: viral).

---

## Estado actual do servidor

```bash
# O código está no servidor mas precisa de ser actualizado:
cd ~/affiliate-bot
git pull   # buscar as últimas alterações (switch para RapidAPI)
```

---

## Ficheiro .env — O que falta preencher

```env
# ✅ Tens isto
RAPIDAPI_KEY=fa20537...  (não partilhar publicamente — regenerar se necessário)

# ⏳ Falta obter
ALIEXPRESS_TRACKING_ID=   → portals.aliexpress.com → Tools → Link Generator
TELEGRAM_BOT_TOKEN=       → mesmo token do bot de trading
TELEGRAM_CHANNEL_ID=      → @username do novo canal de afiliados (falta criar)
ANTHROPIC_API_KEY=        → console.anthropic.com → API Keys
INSTAGRAM_ACCESS_TOKEN=   → Facebook Developer → Instagram Graph API
INSTAGRAM_BUSINESS_ACCOUNT_ID= → Settings da conta Instagram Business
TIKTOK_ACCESS_TOKEN=      → TikTok for Developers
```

---

## Próximos passos por ordem

- [ ] 1. Criar canal Telegram de afiliados + adicionar bot como admin
- [ ] 2. Obter `TELEGRAM_CHANNEL_ID` (@username do canal)
- [ ] 3. Obter `ALIEXPRESS_TRACKING_ID` do portals
- [ ] 4. Obter `ANTHROPIC_API_KEY` em console.anthropic.com
- [ ] 5. Preencher `.env` no servidor: `nano ~/affiliate-bot/.env`
- [ ] 6. Correr `git pull` no servidor para buscar última versão
- [ ] 7. Testar: `python bot.py --check`
- [ ] 8. Primeiro post real: `python bot.py --test`
- [ ] 9. Configurar Instagram Business + Graph API
- [ ] 10. Configurar TikTok Content API
- [ ] 11. Configurar systemd para arranque automático 24/7
- [ ] 12. Monitorizar logs: `tail -f ~/affiliate-bot/affiliate_bot.log`

---

## Comandos úteis no servidor

```bash
# Entrar no servidor
ssh root@178.105.52.219

# Actualizar código
cd ~/affiliate-bot && git pull

# Editar configuração
nano ~/affiliate-bot/.env

# Testar ligações
cd ~/affiliate-bot && python3 bot.py --check

# Publicar 1 post de teste
cd ~/affiliate-bot && python3 bot.py --test

# Arrancar bot 24/7
cd ~/affiliate-bot && python3 bot.py

# Ver logs em tempo real
tail -f ~/affiliate-bot/affiliate_bot.log

# Ver estatísticas
cd ~/affiliate-bot && python3 bot.py --stats
```

---

## Frequência de publicação (automática)

Posts distribuídos aleatoriamente entre as **7h e as 23h UTC** com jitter de ±10 minutos para parecer orgânico.

| Canal | Posts/dia | Rotação de nichos |
|-------|-----------|-------------------|
| Telegram | 8 | Tech → Casa → Fitness → Moda → Tech... |
| Instagram | 4 | rotação pelos 4 nichos |
| TikTok | 3 | rotação pelos 4 nichos |

**Total: 15 posts/dia automáticos** em 3 plataformas.
