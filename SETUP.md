# Affiliate Bot — Guia de Setup

## Pré-requisitos
- Python 3.11+
- VPS com acesso SSH
- Contas criadas nas plataformas abaixo

---

## 1. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 2. Configurar as chaves de API

```bash
cp .env.example .env
nano .env   # preenche os valores
```

### 2a. AliExpress Affiliate API
1. Vai a: https://portals.aliexpress.com/
2. Regista-te como afiliado → My Apps → Create App
3. Copia **App Key**, **App Secret** e **Tracking ID**

### 2b. Telegram Bot
1. Fala com @BotFather no Telegram → `/newbot`
2. Copia o **Bot Token**
3. Adiciona o bot ao teu canal como **Administrador** com permissão de publicar
4. O `TELEGRAM_CHANNEL_ID` é o `@username` do canal ou o ID numérico (`-100xxxxxxxxx`)
   - Para obter o ID: reencaminha uma mensagem do canal para @userinfobot

### 2c. Instagram Business Graph API
1. Vai a https://developers.facebook.com/ → My Apps → Create App → Business
2. Adiciona o produto **Instagram Graph API**
3. Liga a tua conta Instagram Business
4. Vai a Graph API Explorer → Gera token com permissões:
   - `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`
5. Converte para **Long-Lived Token** (válido 60 dias — renova mensalmente):
   ```
   GET https://graph.facebook.com/v19.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id=APP_ID
     &client_secret=APP_SECRET
     &fb_exchange_token=SHORT_TOKEN
   ```
6. O `INSTAGRAM_BUSINESS_ACCOUNT_ID` encontras em:
   - Instagram → Settings → Account → Professional Account → Account ID

### 2d. TikTok API
1. Vai a https://developers.tiktok.com/ → Manage Apps → Create App
2. Adiciona o produto **Content Posting API**
3. Pede aprovação para `video.publish` scope
4. Gera **Access Token** via OAuth flow
5. Copia **Client Key**, **Client Secret**, **Access Token**

### 2e. Anthropic (Claude)
1. Vai a https://console.anthropic.com/ → API Keys → Create Key
2. Copia a chave para `ANTHROPIC_API_KEY`

---

## 3. Testar as ligações

```bash
python bot.py --check
```

Deverás ver:
```
  Telegram     ✅ OK
  Instagram    ✅ OK
  TikTok       ✅ OK
```

---

## 4. Testar um post real

```bash
python bot.py --test
```

Isto publica **1 post** em cada canal e termina. Verifica os canais.

---

## 5. Iniciar o bot 24/7

```bash
# Usando screen (simples)
screen -S affiliatebot
python bot.py
# Ctrl+A, D para desligar sem parar o bot

# Usando systemd (recomendado para VPS)
sudo nano /etc/systemd/system/affiliatebot.service
```

Conteúdo do serviço systemd:
```ini
[Unit]
Description=Affiliate Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/blank-app
ExecStart=/usr/bin/python3 /home/ubuntu/blank-app/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable affiliatebot
sudo systemctl start affiliatebot
sudo systemctl status affiliatebot
```

---

## 6. Ver estatísticas

```bash
python bot.py --stats
```

---

## Frequência de publicação (padrão)

| Canal     | Posts/dia | Horário         |
|-----------|-----------|-----------------|
| Telegram  | 8         | 7h–23h (UTC)    |
| Instagram | 4         | 7h–23h (UTC)    |
| TikTok    | 3         | 7h–23h (UTC)    |

Edita `affiliate_bot/niches/config.json` para alterar.

---

## Nichos activos

| Niche               | Keywords principais                    |
|---------------------|----------------------------------------|
| Tech & Gadgets      | earbuds, smartwatch, power bank...     |
| Casa Inteligente    | storage, smart plug, kitchen gadget... |
| Fitness & Saúde     | resistance bands, yoga mat, massage... |
| Moda & Acessórios   | watch, sunglasses, bracelet...         |

---

## Logs

```bash
tail -f affiliate_bot.log
```
