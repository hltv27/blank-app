#!/usr/bin/env bash
set -e

echo "=== Instalar dependências base ==="
pip install openpyxl beautifulsoup4

echo "=== A limpar dados anteriores (domínio errado www.douroetamega.pt) ==="
rm -f douroetamega_urls.txt douroetamega_dados.xlsx douroetamega_dados_parcial_*.xlsx

echo "=== A tentar Selenium com Chromium ==="
if command -v chromium-browser &>/dev/null || command -v chromium &>/dev/null; then
    pip install selenium
    echo "=== Crawler Selenium — turismo.douroetamega.pt ==="
    python -u douroetamega_crawler_selenium.py

else
    echo "=== Sem browser disponível — a instalar Chromium ==="
    pkg install chromium -y
    pip install selenium
    echo "=== Crawler Selenium ==="
    python -u douroetamega_crawler_selenium.py
fi
