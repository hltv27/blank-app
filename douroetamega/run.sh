#!/usr/bin/env bash
set -e

echo "=== Instalar dependências base ==="
pip install openpyxl beautifulsoup4

echo "=== A tentar Playwright ==="
if pip install playwright 2>/dev/null; then
    playwright install chromium 2>/dev/null || pkg install chromium 2>/dev/null || true
    echo "=== Crawler Playwright ==="
    python douroetamega_crawler.py

elif pip install selenium 2>/dev/null && command -v chromium-browser &>/dev/null || command -v chromium &>/dev/null; then
    echo "=== Crawler Selenium (ARM) ==="
    python douroetamega_crawler_selenium.py

else
    echo "=== Sem browser disponível — a instalar Chromium ==="
    pkg install chromium
    pip install selenium
    echo "=== Crawler Selenium ==="
    python douroetamega_crawler_selenium.py
fi
