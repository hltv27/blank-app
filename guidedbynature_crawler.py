#!/usr/bin/env python3
"""
Crawler — guidedbynature.pt (Playwright)
Usa um browser real para navegar o site e exporta para Excel.

Instalar dependências (uma vez só):
    pip install playwright pandas openpyxl
    playwright install chromium

Correr:
    python guidedbynature_crawler.py

Ficheiro gerado: guidedbynature_dados.xlsx
"""

import asyncio
import json
import re
import time
from urllib.parse import urljoin

import pandas as pd
from playwright.async_api import async_playwright, Page, BrowserContext

BASE_URL = "https://guidedbynature.pt"
OUTPUT   = "guidedbynature_dados.xlsx"
DELAY    = 0.5   # segundos entre páginas de detalhe

# Categorias a crawlar — (tipo, slug)
CATEGORIAS = [
    # PASSEAR
    ("tour", "caminhadas"),
    ("tour", "bicicleta"),
    ("tour", "roteiros-tematicos"),
    ("tour", "caminhada-de-longa-distancia"),
    ("tour", "caminhada"),
    ("tour", "btt"),
    ("tour", "ciclismo"),
    ("tour", "trail"),
    # MERGULHAR
    ("poi", "praias-ou-piscinas"),
    ("poi", "docas-cais-e-fluvinas"),
    ("poi", "termas-e-spa"),
    # CONHECER
    ("poi", "paisagens"),
    ("poi", "historia-e-cultura"),
    ("poi", "gastronomia"),
    ("poi", "miradouros"),
    ("poi", "monumentos"),
    ("poi", "museus"),
    ("poi", "aldeias"),
    ("poi", "cascatas"),
    ("poi", "lagos"),
    ("poi", "praias-fluviais"),
    # PLANEAR
    ("poi", "onde-comer"),
    ("poi", "onde-dormir"),
    ("poi", "postos-de-turismo"),
    # EVENTOS
    ("event", "feiras-e-tradicoes"),
    ("event", "festivais"),
    ("event", "mercados"),
    ("event", "concertos"),
    ("event", "desporto"),
    ("event", "cultura"),
    ("event", "natureza"),
    # PARTICIPAR
    ("p", "desafios"),
    ("p", "experiencias-guiadas"),
    ("p", "comprar-produtos-locais"),
]


# ── Descoberta de URLs ─────────────────────────────────────────────────────────

def _extract_links(html: str, base: str) -> set[str]:
    """Extrai URLs de items (poi/event/tour/p) do HTML."""
    urls = set()
    for m in re.finditer(r'href="(/pt/(poi|event|tour|p)/[^"]+/(\d+)/)"', html):
        full = urljoin(base, m.group(1)).rstrip("/") + "/"
        urls.add(full)
    return urls


async def discover_urls(context: BrowserContext) -> list[str]:
    urls: set[str] = set()
    page = await context.new_page()

    for tipo, cat in CATEGORIAS:
        cat_url = f"{BASE_URL}/pt/{tipo}/{cat}/"
        print(f"[Cat] {tipo}/{cat}")

        for pg in range(1, 100):
            url = cat_url if pg == 1 else f"{cat_url}?page={pg}"
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                if not resp or resp.status == 404:
                    break
            except Exception as e:
                print(f"  [ERRO] {url}: {e}")
                break

            await page.wait_for_timeout(1200)
            content = await page.content()
            found = _extract_links(content, BASE_URL)

            # Se não encontrou links nesta página, a categoria acabou
            if not found:
                break

            new = found - urls
            urls.update(found)
            print(f"  pág {pg}: +{len(new)} (total {len(urls)})")

            # Se encontrou muito poucos links novos, provavelmente é a última página
            if len(new) == 0:
                break

        await asyncio.sleep(0.3)

    await page.close()
    print(f"\n[Descoberta] {len(urls)} URLs no total\n")
    return list(urls)


# ── Extracção de dados de cada página ─────────────────────────────────────────

def _text(el) -> str:
    return el.inner_text().strip() if el else ""


async def extract_page(page: Page, url: str) -> dict | None:
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        if not resp or resp.status >= 400:
            return None
    except Exception as e:
        print(f"  [ERRO] {url}: {e}")
        return None

    await page.wait_for_timeout(800)

    row: dict = {"url": url}

    # Derivar campos da URL
    parts = url.rstrip("/").split("/")
    row["id"] = parts[-1] if parts[-1].isdigit() else ""
    if "/pt/poi/" in url:
        row["tipo_url"] = "poi"
        row["slug"]     = parts[-2]
        row["categoria"]= parts[-3] if len(parts) >= 3 else ""
    elif "/pt/event/" in url:
        row["tipo_url"] = "evento"
        row["slug"]     = parts[-2]
        row["categoria"]= parts[-3] if len(parts) >= 3 else ""
    elif "/pt/tour/" in url:
        row["tipo_url"] = "tour"
        row["slug"]     = parts[-2]
        row["categoria"]= parts[-3] if len(parts) >= 3 else ""
    elif "/pt/p/" in url:
        row["tipo_url"] = parts[-2]
        row["slug"]     = ""
        row["categoria"]= parts[-2]
    else:
        row["tipo_url"] = ""
        row["slug"]     = parts[-2] if len(parts) >= 2 else ""
        row["categoria"]= parts[-3] if len(parts) >= 3 else ""

    # JSON-LD
    jld_tags = await page.query_selector_all('script[type="application/ld+json"]')
    for tag in jld_tags:
        try:
            data = json.loads(await tag.inner_text())
            if isinstance(data, list):
                data = data[0]
            row["nome"]      = data.get("name", "")
            row["descricao"] = data.get("description", "")
            row["tipo"]      = data.get("@type", "")
            row["website"]   = data.get("url", "")
            row["telefone"]  = data.get("telephone", "")
            row["email"]     = data.get("email", "")
            addr = data.get("address", {})
            if isinstance(addr, dict):
                row["morada"]    = addr.get("streetAddress", "")
                row["localidade"]= addr.get("addressLocality", "")
                row["regiao"]    = addr.get("addressRegion", "")
                row["pais"]      = addr.get("addressCountry", "")
            geo = data.get("geo", {})
            if isinstance(geo, dict):
                row["latitude"]  = geo.get("latitude", "")
                row["longitude"] = geo.get("longitude", "")
            row["preco"]   = str(data.get("priceRange", "") or data.get("price", ""))
            row["horario"] = str(data.get("openingHours", "") or "")
            row["imagem"]  = str(data.get("image", ""))
            break
        except Exception:
            pass

    # Open Graph como fallback
    if not row.get("nome"):
        el = await page.query_selector('meta[property="og:title"]')
        row["nome"] = (await el.get_attribute("content") or "") if el else ""
    if not row.get("descricao"):
        el = await page.query_selector('meta[property="og:description"], meta[name="description"]')
        row["descricao"] = (await el.get_attribute("content") or "") if el else ""
    og_img = await page.query_selector('meta[property="og:image"]')
    row["og_image"] = (await og_img.get_attribute("content") or "") if og_img else ""

    # H1
    h1 = await page.query_selector("h1")
    if h1 and not row.get("nome"):
        row["nome"] = await h1.inner_text()

    # Dados específicos de tours (distância, desnível, dificuldade, duração)
    for label in ["distância", "desnível", "dificuldade", "duração", "distance",
                  "elevation", "difficulty", "duration", "comprimento"]:
        els = await page.query_selector_all(f'[class*="detail"], [class*="info"], dl dt, th')
        for el in els:
            txt = (await el.inner_text()).strip().lower()
            if label in txt:
                # tenta encontrar o valor associado
                parent = await el.evaluate_handle("el => el.parentElement")
                val_el = await parent.query_selector("dd, td, [class*='value']")
                if val_el:
                    val = (await val_el.inner_text()).strip()
                    key = re.sub(r"[^\w]", "_", label)
                    if val and key not in row:
                        row[f"campo_{key}"] = val

    # Tags / badges
    tags = []
    tag_els = await page.query_selector_all('[class*="tag"], [class*="badge"], [class*="chip"]')
    for el in tag_els:
        t = (await el.inner_text()).strip()
        if t and len(t) < 60:
            tags.append(t)
    row["tags"] = " | ".join(dict.fromkeys(tags))

    # Redes sociais
    sociais = []
    links = await page.query_selector_all("a[href]")
    for a in links:
        href = await a.get_attribute("href") or ""
        if any(s in href for s in ["facebook.com", "instagram.com", "twitter.com",
                                   "youtube.com", "tiktok.com", "linkedin.com"]):
            sociais.append(href)
    row["redes_sociais"] = " | ".join(dict.fromkeys(sociais))

    return row


# ── Main ───────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("  guidedbynature.pt — Crawler (Playwright)")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/136.0.0.0 Safari/537.36",
            locale="pt-PT",
        )

        # Warm-up
        page = await context.new_page()
        await page.goto(BASE_URL + "/pt/", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1000)
        await page.close()
        print("[Session] cookies obtidos\n")

        # Descoberta
        urls = await discover_urls(context)

        if not urls:
            print("[Aviso] Nenhuma URL descoberta — a usar exemplos de fallback")
            urls = [
                f"{BASE_URL}/pt/tour/caminhadas/ecopista-do-tamega/63694722/",
                f"{BASE_URL}/pt/poi/paisagens/zona-de-lazer-de-fermil/803708969/",
            ]

        # Extracção
        print(f"A processar {len(urls)} páginas...\n")
        dados = []
        page = await context.new_page()

        for i, url in enumerate(urls, 1):
            slug = url.rstrip("/").split("/")[-2]
            print(f"[{i:4}/{len(urls)}] {slug}")
            row = await extract_page(page, url)
            if row:
                dados.append(row)
            await asyncio.sleep(DELAY)

        await page.close()
        await browser.close()

    if not dados:
        print("\n[Erro] Nenhum dado extraído.")
        return

    df = pd.DataFrame(dados)
    priority = ["id", "nome", "categoria", "slug", "tipo_url", "tipo",
                "descricao", "morada", "localidade", "regiao", "pais",
                "latitude", "longitude", "telefone", "email", "website",
                "preco", "horario", "imagem", "og_image", "tags",
                "redes_sociais", "url"]
    cols = [c for c in priority if c in df.columns]
    extra = [c for c in df.columns if c not in cols]
    df = df[cols + extra]

    df.to_excel(OUTPUT, index=False)
    print(f"\nExportado: {OUTPUT}")
    print(f"   {len(dados)} linhas  ×  {len(df.columns)} colunas")
    print(f"\nCampos: {', '.join(df.columns.tolist())}")


if __name__ == "__main__":
    asyncio.run(main())
