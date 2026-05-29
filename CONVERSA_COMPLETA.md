# Affiliate Bot — Resumo Completo da Conversa

**Última actualização:** 29 de Maio de 2026
**Utilizador:** Hugo Vaz
**Repositório:** github.com/hltv27/blank-app
**Branch:** `claude/affiliate-bot-automation-5rsFF`

---

## Ideia inicial

Construir um bot automático 24/7 que:
- Vai buscar produtos via link de afiliado
- Publica os produtos à venda nas redes sociais
- Escolhe os melhores nichos (mais pessoas = mais lucro)
- Corre sem intervenção humana

---

## Decisões tomadas

### Programa de afiliados
- **Amazon Associates** + **AliExpress** (escolha do Hugo)
- Depois simplificámos para focar no **AliExpress** via **RapidAPI DataHub** (sem burocracia)

### Canais de publicação
- **Telegram** ✅ A funcionar
- **Instagram Reels** ⏳ Em configuração
- **TikTok** ⏳ Futuro

### Mercado alvo
- **Global** (conteúdo em inglês)

### Nichos escolhidos (4)
| Niche | Emoji | Porquê |
|-------|-------|--------|
| Tech & Gadgets | 📱 | Alto volume, boas comissões |
| Casa & Vida Inteligente | 🏠 | Muito viral no TikTok/Instagram |
| Fitness & Saúde | 💪 | Público fiel com poder de compra |
| Moda & Acessórios | 👗 | Margens altas, muito visual |

### Tipo de conteúdo
- Imagens geradas com **Pillow** (1080x1080, cores por niche)
- Legendas geradas com **Claude Haiku** (IA) — opcional, bot funciona sem ela
- Cada plataforma recebe conteúdo adaptado

### Infraestrutura
- Começou como Termux (só telemóvel)
- Descobrimos que Hugo tem **VPS Hetzner** (Claw-bot)
- Bot corre no mesmo servidor do bot de trading — sem custo extra

---

## Servidor Hetzner

| Detalhe | Valor |
|---------|-------|
| Nome | Claw-bot |
| IP | 178.105.52.219 |
| Specs | 2 vCPU, 4 GB RAM, 40 GB disco |
| OS | Ubuntu (Python 3.10.12, Git 2.34.1) |
| Preço | €4.91/mês |
| Acesso | `ssh root@178.105.52.219` |
| Código | `/root/affiliate-bot` |

---

## Problemas resolvidos

### AliExpress API oficial — RESOLVIDO
- **Problema:** OAuth redireccionava para Taobao e dava erro 500
- **Solução:** Trocámos para **RapidAPI AliExpress DataHub**

### RapidAPI DataHub primeira chave — RESOLVIDO
- **Problema:** Chave `fa20537...` dava erro 5008 "data gather failed"
- **Solução:** Nova chave `7e295416...` de conta fresca funciona correctamente

### Parsing da resposta DataHub — RESOLVIDO
- **Problema:** Campos errados (`averageStar`, `totalOrders`, URLs sem `https:`)
- **Solução:** Corrigido para `averageStarRate`, `sales`, `_fix_url()`

---

## APIs & Serviços

| Serviço | Estado | Observação |
|---------|--------|------------|
| RapidAPI AliExpress DataHub | ✅ A funcionar | Chave `7e295416...` — não partilhar |
| AliExpress Tracking ID | ⏳ Opcional | portals.aliexpress.com → Tools → Link Generator |
| Telegram Bot | ✅ Configurado | `@hltv27_bot` — mesmo do bot de trading |
| Telegram Canal | ✅ Criado | `@TopDealsGadgetss` |
| Anthropic Claude | ⏳ Opcional | console.anthropic.com — bot funciona sem ele |
| Instagram Graph API | ⏳ Em configuração | Tem conta Business/Creator |
| TikTok Content API | ⏳ Futuro | Adicionar depois |

---

## Estado actual do .env no servidor

```env
RAPIDAPI_KEY=7e295416famshf37b06a5532e422p10a6c7jsnc48b85f0aed6
ALIEXPRESS_TRACKING_ID=
TELEGRAM_BOT_TOKEN=8612510987:AAGZAeejYZ_L4wssnojosN0SfA2U1jUslOc
TELEGRAM_CHANNEL_ID=@TopDealsGadgetss
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=
TIKTOK_ACCESS_TOKEN=
ANTHROPIC_API_KEY=
LOG_LEVEL=INFO
DB_PATH=affiliate_bot.db
IMAGES_DIR=generated_images
```

---

## Marcos concluídos ✅

- [x] Código completo construído e no GitHub
- [x] Servidor Hetzner identificado e acessível
- [x] Código clonado no servidor (`/root/affiliate-bot`)
- [x] RapidAPI DataHub a funcionar com nova chave
- [x] `.env` configurado com Telegram + RapidAPI
- [x] Canal Telegram `@TopDealsGadgetss` criado
- [x] Bot `@hltv27_bot` adicionado como Admin ao canal
- [x] Primeiro post publicado com sucesso (Lenovo XT53 earphones)
- [x] Bot a correr 24/7 via systemd (`affiliatebot.service`)
- [x] Logo criado (`logo_instagram.png` em `/storage/emulated/0/Download/`)

---

## Frequência de publicação

| Canal | Posts/dia | Horário |
|-------|-----------|---------|
| Telegram | 8 | 7h–23h UTC ✅ activo |
| Instagram | 4 | 7h–23h UTC (quando configurado) |
| TikTok | 3 | 7h–23h UTC (quando configurado) |
| **Total** | **15** | com jitter ±10 min para parecer orgânico |

---

## Como o dinheiro funciona

**Não há loja, não há IBAN no bot, não há pagamentos.**

1. Bot publica produto com link de afiliado
2. Pessoa clica → vai para o AliExpress
3. Pessoa compra → AliExpress regista comissão
4. AliExpress paga directamente para conta bancária/PayPal do Hugo
5. Configurado em portals.aliexpress.com → Payment

---

## Próximos passos

- [x] ~~Telegram configurado e a publicar~~
- [ ] **Instagram** — configurar Graph API (conta Business já existe)
  - Criar Facebook Page dedicada para deals
  - Criar App em developers.facebook.com
  - Gerar access token com permissão `instagram_content_publish`
  - Obter Instagram Business Account ID
  - Preencher `.env`: `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_BUSINESS_ACCOUNT_ID`
- [ ] **Logo** — copiar para Downloads: `cp ~/logo_instagram.png /storage/emulated/0/Download/`
- [ ] **TikTok** — configurar depois do Instagram
- [ ] **Anthropic** — opcional, melhora as legendas: console.anthropic.com

---

## Ficheiros criados

```
affiliate-bot/
├── bot.py                          ← entry point (--test / --check / --stats)
├── .env.example                    ← template de configuração
├── requirements.txt                ← dependências Python
├── SETUP.md                        ← guia completo de setup
├── PROGRESSO.md                    ← resumo do progresso
├── CONVERSA_COMPLETA.md            ← este ficheiro
└── affiliate_bot/
    ├── config.py                   ← lê .env, valida chaves
    ├── database.py                 ← SQLite: produtos, posts, evita repetições 30 dias
    ├── scheduler.py                ← APScheduler: 15 posts/dia distribuídos 7h–23h
    ├── fetchers/
    │   └── aliexpress.py           ← RapidAPI DataHub (campo correcto: averageStarRate, sales)
    ├── generators/
    │   ├── content.py              ← Claude Haiku gera legenda (fallback sem chave)
    │   └── image.py                ← Pillow: card 1080x1080 com cores por niche
    ├── publishers/
    │   ├── telegram.py             ← Telegram Bot API ✅
    │   ├── instagram.py            ← Instagram Graph API ⏳
    │   └── tiktok.py               ← TikTok Content Posting API v2 ⏳
    └── niches/
        └── config.json             ← 4 nichos, keywords, hashtags, horários
```

---

## Comandos úteis no servidor

```bash
# Entrar no servidor
ssh root@178.105.52.219

# Ver se o bot está a correr
systemctl status affiliatebot

# Ver posts em tempo real
tail -f /root/affiliate-bot/affiliate_bot.log

# Ver estatísticas
cd /root/affiliate-bot && python3 bot.py --stats

# Publicar post de teste
cd /root/affiliate-bot && python3 bot.py --test

# Reiniciar o bot
systemctl restart affiliatebot

# Actualizar código
cd /root/affiliate-bot && git pull && systemctl restart affiliatebot
```

---

## systemd — já configurado ✅

```bash
# Estado
systemctl status affiliatebot

# O serviço está em:
# /etc/systemd/system/affiliatebot.service
```

---

*Actualizado em 29/05/2026 — Conversa com Claude Code*
