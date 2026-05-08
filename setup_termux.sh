#!/data/data/com.termux/files/usr/bin/bash
# Affiliate Bot — Instalação automática para Termux
set -e

echo ""
echo "====================================="
echo "  Affiliate Bot — Setup Termux"
echo "====================================="
echo ""

# 1. Actualizar pacotes base
echo "[1/7] Actualizando pacotes..."
pkg update -y && pkg upgrade -y

# 2. Instalar dependências do sistema
echo "[2/7] Instalando Python e dependências..."
pkg install -y python python-pillow libjpeg-turbo libpng freetype fontconfig

# 3. Instalar fontes para as imagens
echo "[3/7] Instalando fontes DejaVu..."
pkg install -y fontconfig
fc-cache -fv 2>/dev/null || true

# 4. Instalar Termux:API (para wake lock e notificações)
echo "[4/7] Instalando Termux:API..."
pkg install -y termux-api

# 5. Instalar dependências Python
echo "[5/7] Instalando bibliotecas Python..."
pip install --upgrade pip
pip install anthropic requests APScheduler python-dotenv

# 6. Configurar permissão de armazenamento
echo "[6/7] Configurando acesso ao armazenamento..."
termux-setup-storage 2>/dev/null || echo "  (aceita a permissão de armazenamento quando aparecer)"

# 7. Criar ficheiro .env se não existir
echo "[7/7] Preparando configuração..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "  ✅ Ficheiro .env criado."
    echo "  ⚠️  Abre o .env e preenche as tuas chaves de API:"
    echo "      nano .env"
else
    echo "  .env já existe — não foi alterado."
fi

# Criar pasta de imagens
mkdir -p generated_images

echo ""
echo "====================================="
echo "  Instalação concluída!"
echo "====================================="
echo ""
echo "Próximos passos:"
echo "  1. nano .env              ← preenche as chaves de API"
echo "  2. python bot.py --check  ← testa as ligações"
echo "  3. python bot.py --test   ← publica 1 post de teste"
echo "  4. bash start_bot.sh      ← inicia o bot 24/7"
echo ""
