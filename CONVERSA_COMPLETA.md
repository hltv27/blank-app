# Affiliate Bot — Resumo Completo da Conversa

**Data:** 23 de Maio de 2026  
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
- **Telegram** (principal — mais fácil)
- **Instagram Reels** (segundo)
- **TikTok** (terceiro)

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
- Legendas geradas com **Claude Haiku** (IA)
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

## Problema com a API do AliExpress

**Problema:** A API oficial (portals.aliexpress.com) exige aprovação via OAuth que redireciona para Taobao e dá erro 500 — bug do lado deles.

**Tentativas:**
1. portals.aliexpress.com → Apply for API → erro 500 Taobao
2. open.aliexpress.com → foi parar ao portal errado (service providers chineses)

**Solução:** Trocámos para **RapidAPI AliExpress DataHub**
- Sem aprovações
- Sem OAuth
- Só uma chave API
- Chave obtida pelo Hugo em rapidapi.com

---

## APIs & Serviços

| Serviço | Estado | Observação |
|---------|--------|------------|
| RapidAPI AliExpress DataHub | ✅ Chave obtida | Não partilhar publicamente — regenerar se necessário |
| AliExpress Tracking ID | ⏳ Falta | portals.aliexpress.com → Tools → Link Generator |
| Telegram Bot Token | ✅ Existe | Mesmo token do bot de trading |
| Telegram Canal | ⏳ Falta criar | Canal público novo para afiliados |
| Anthropic Claude | ⏳ Opcional | console.anthropic.com — bot funciona sem ele |
| Instagram Graph API | ⏳ Futuro | Adicionar depois |
| TikTok Content API | ⏳ Futuro | Adicionar depois |

---

## Ficheiros criados

```
affiliate-bot/
├── bot.py                          ← entry point (--test / --check / --stats)
├── .env.example                    ← template de configuração
├── requirements.txt                ← dependências Python
├── SETUP.md                        ← guia completo de setup
├── PROGRESSO.md                    ← resumo do progresso
├── setup_termux.sh                 ← instalação Termux (não necessário com VPS)
├── start_bot.sh                    ← arranque com wake lock
├── stop_bot.sh                     ← parar o bot
├── .termux/boot/                   ← auto-arranque no telemóvel
└── affiliate_bot/
    ├── config.py                   ← lê .env, valida chaves
    ├── database.py                 ← SQLite: produtos, posts, evita repetições 30 dias
    ├── scheduler.py                ← APScheduler: 15 posts/dia distribuídos 7h–23h
    ├── fetchers/
    │   └── aliexpress.py           ← RapidAPI DataHub: busca produtos por keyword
    ├── generators/
    │   ├── content.py              ← Claude Haiku gera legenda (fallback sem chave)
    │   └── image.py                ← Pillow: card 1080x1080 com cores por niche
    ├── publishers/
    │   ├── telegram.py             ← Telegram Bot API
    │   ├── instagram.py            ← Instagram Graph API
    │   └── tiktok.py               ← TikTok Content Posting API v2
    └── niches/
        └── config.json             ← 4 nichos, keywords, hashtags, horários
```

---

## Como o bot publica

1. APScheduler dispara o job (hora configurada)
2. Busca produtos no AliExpress via RapidAPI (keyword do niche)
3. Ordena por score: desconto × vendas
4. Verifica na base de dados se o produto já foi publicado (últimos 30 dias)
5. Gera imagem 1080x1080 com Pillow
6. Gera legenda com Claude Haiku (ou fallback se sem chave)
7. Publica no canal activo
8. Regista na base de dados

---

## Frequência de publicação

| Canal | Posts/dia | Horário |
|-------|-----------|---------|
| Telegram | 8 | 7h–23h UTC |
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

## Ficheiro .env (configuração do servidor)

```env
# ✅ Já tens
RAPIDAPI_KEY=fa20537...   ← NÃO partilhar — regenerar se necessário

# ⏳ Falta (obrigatório para Telegram)
TELEGRAM_BOT_TOKEN=        ← mesmo token do bot de trading
TELEGRAM_CHANNEL_ID=       ← @username do novo canal de afiliados

# ⏳ Opcional (bot funciona sem isto)
ALIEXPRESS_TRACKING_ID=    ← portals.aliexpress.com → Tools → Link Generator
ANTHROPIC_API_KEY=         ← console.anthropic.com → API Keys

# ⏳ Futuro (Instagram e TikTok)
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=
TIKTOK_ACCESS_TOKEN=
```

---

## Próximos passos (por ordem)

- [ ] **1.** Criar canal Telegram público (nome + @username)
- [ ] **2.** Adicionar bot de trading como Admin no novo canal
- [ ] **3.** Copiar TELEGRAM_BOT_TOKEN do bot de trading
- [ ] **4.** Preencher `.env` no servidor: `nano ~/affiliate-bot/.env`
- [ ] **5.** Actualizar código: `cd ~/affiliate-bot && git pull`
- [ ] **6.** Testar: `python3 bot.py --check`
- [ ] **7.** Primeiro post: `python3 bot.py --test`
- [ ] **8.** Arrancar 24/7: `python3 bot.py` (ou systemd)
- [ ] **9.** Configurar Instagram (quando estiver pronto)
- [ ] **10.** Configurar TikTok (quando estiver pronto)

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

# Ver estatísticas de posts
cd ~/affiliate-bot && python3 bot.py --stats
```

---

## Arranque automático 24/7 com systemd (fazer no final)

```bash
nano /etc/systemd/system/affiliatebot.service
```

```ini
[Unit]
Description=Affiliate Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/affiliate-bot
ExecStart=/usr/bin/python3 /root/affiliate-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable affiliatebot
systemctl start affiliatebot
systemctl status affiliatebot
```

---

*Gerado em 23/05/2026 — Conversa com Claude Code*
