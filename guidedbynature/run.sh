#!/bin/bash
# Crawler guidedbynature.pt — instalação e arranque

set -e

# 1. Actualizar repo
git pull origin main

# 2. Entrar na pasta
cd "$(dirname "$0")"

# 3. Instalar dependências Python
pip install playwright openpyxl beautifulsoup4

# 4. Instalar browser Chromium (tenta playwright primeiro, depois pkg do Termux)
playwright install chromium 2>/dev/null || pkg install chromium -y 2>/dev/null || echo "[Aviso] Instala chromium manualmente"

# 5. Correr o crawler
python guidedbynature_crawler.py
