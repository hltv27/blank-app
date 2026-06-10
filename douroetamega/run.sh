#!/usr/bin/env bash
set -e

echo "=== Instalar dependências ==="
pip install playwright openpyxl beautifulsoup4

echo "=== Instalar Chromium ==="
playwright install chromium || pkg install chromium

echo "=== A iniciar crawler ==="
python douroetamega_crawler.py
