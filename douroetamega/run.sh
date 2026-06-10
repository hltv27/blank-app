#!/usr/bin/env bash
set -e

echo "=== Instalar dependências base ==="
pip install openpyxl beautifulsoup4

echo "=== A tentar instalar Playwright ==="
if pip install playwright 2>/dev/null; then
    echo "Playwright instalado. A instalar Chromium…"
    playwright install chromium 2>/dev/null || pkg install chromium 2>/dev/null || true
    echo "=== A iniciar crawler (Playwright) ==="
    python douroetamega_crawler.py
else
    echo "Playwright não disponível nesta plataforma. A usar versão requests."
    pip install cloudscraper 2>/dev/null || true
    echo "=== A iniciar crawler (requests) ==="
    python douroetamega_crawler_requests.py
fi
