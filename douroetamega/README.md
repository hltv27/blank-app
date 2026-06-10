# Crawler — douroetamega.pt

## Ficheiros

| Ficheiro | Função |
|---|---|
| `douroetamega_crawler.py` | Crawler principal — BFS completo, descobre e extrai todos os POIs, artigos, eventos, rotas e municípios |
| `run.sh` | Script de instalação e arranque |

## Instalar dependências

```bash
pip install playwright openpyxl beautifulsoup4
playwright install chromium
```

Se `playwright install chromium` falhar (Android/ARM):
```bash
pkg install chromium
pip install playwright openpyxl beautifulsoup4
```

## Correr o crawler

```bash
cd douroetamega
python douroetamega_crawler.py
```

ou simplesmente:

```bash
cd douroetamega
bash run.sh
```

Gera `douroetamega_dados.xlsx` com 3 sheets:
- **Dados** — valores extraídos de cada item
- **Presença** — `X` se o campo está preenchido, vazio se não
- **Resumo** — contagem de items por secção e categoria

## Como funciona

O crawler usa o **Playwright** (browser Chromium real) para:
1. Arrancar na homepage e seguir todos os links internos (BFS)
2. Executar o JavaScript do site — essencial para páginas que carregam conteúdo via AJAX
3. Detectar páginas de conteúdo (POIs, artigos, eventos...) pela profundidade e padrão do URL
4. Extrair dados estruturados: JSON-LD, Open Graph, meta tags, tabelas, pares label/valor
5. Guardar parcialmente a cada 500 items para não perder progresso

## Dados extraídos por item

| Campo | Origem |
|---|---|
| `nome` | JSON-LD → og:title → H1 → `<title>` |
| `descricao` | JSON-LD → meta description → texto da página |
| `tipo` | JSON-LD `@type` |
| `morada`, `localidade`, `regiao` | JSON-LD `address` |
| `latitude`, `longitude` | JSON-LD `geo` |
| `telefone`, `email`, `website` | JSON-LD |
| `preco`, `horario` | JSON-LD |
| `data_inicio`, `data_fim` | JSON-LD (eventos) |
| `municipio` | Regex no HTML |
| `imagens` | `<img>` com paths de upload/media |
| `tags` | Elementos com class tag/badge/category |
| `redes_sociais` | Links para Facebook, Instagram, etc. |
| `campo_*` | Pares dl/dt/dd e tabelas th/td detectados |
| `secao`, `categoria`, `slug` | Parseados do URL |
