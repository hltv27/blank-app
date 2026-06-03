# Crawler — guidedbynature.pt

## Ficheiros

| Ficheiro | Função |
|---|---|
| `guidedbynature_crawler.py` | Crawler principal — descobre e extrai todos os POIs, hotéis, restaurantes, tours e eventos |
| `find_api.py` | Script de diagnóstico — descobre endpoints de API e analisa ficheiros JS do site |

## Instalar dependências

```bash
pip install playwright openpyxl beautifulsoup4
playwright install chromium
```

Se `playwright install chromium` falhar (Android/ARM):
```bash
pkg install chromium   # Termux
pip install playwright openpyxl beautifulsoup4
```

## Correr o crawler

```bash
python guidedbynature_crawler.py
```

Gera `guidedbynature_dados.xlsx` com 3 sheets:
- **Dados** — valores extraídos de cada item
- **Presença** — `X` se o campo está preenchido, vazio se não
- **Resumo** — contagem de items por tipo e categoria

## Diagnóstico (se o crawler não encontrar items)

```bash
python find_api.py
```

Analisa os ficheiros JS do site e testa endpoints de API. Gera:
- `debug_cat.html` — HTML estático de uma página de categoria
- `debug_api_candidates.txt` — lista de endpoints candidatos encontrados no JS

## Estrutura de URLs do site

```
/pt/poi/{categoria}/{slug}/{id}/     → pontos de interesse
/pt/event/{categoria}/{slug}/{id}/   → eventos
/pt/tour/{categoria}/{slug}/{id}/    → tours/percursos
/pt/p/{tipo}/{id}/                   → outros
```
