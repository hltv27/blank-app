#!/usr/bin/env python3
"""
Crawler — guidedbynature.pt
Descobre todos os POIs e Eventos e exporta para Excel.

Padrões de URL conhecidos:
  /pt/poi/{categoria}/{slug}/{id}/   → pontos de interesse
  /pt/p/{tipo}/{id}/                 → eventos e outros

Instalar dependências (uma vez só):
    pip install requests beautifulsoup4 pandas openpyxl lxml

Correr:
    python guidedbynature_crawler.py

Ficheiro gerado: guidedbynature_dados.xlsx
"""

try:
    import cloudscraper
    _scraper = cloudscraper.create_scraper()
    _USE_CLOUDSCRAPER = True
except ImportError:
    import requests as _requests_fallback
    _scraper = None
    _USE_CLOUDSCRAPER = False

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import re
import os
from urllib.parse import urljoin

BASE_URL  = "https://guidedbynature.pt"
OUTPUT    = "guidedbynature_dados.xlsx"
DELAY     = 0.8   # segundos entre pedidos (não sobrecarregar o servidor)
DEBUG_HTML = False  # True → guarda o HTML da primeira página para inspeção

HEADERS = {
    "User-Agent":                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                                  "image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language":           "pt-PT,pt;q=0.9,en-GB;q=0.8,en;q=0.7",
    "Accept-Encoding":           "gzip, deflate, br",
    "Connection":                "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest":            "document",
    "Sec-Fetch-Mode":            "navigate",
    "Sec-Fetch-Site":            "none",
    "Sec-Fetch-User":            "?1",
    "Sec-CH-UA":                 '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "Sec-CH-UA-Mobile":          "?0",
    "Sec-CH-UA-Platform":        '"Windows"',
    "Cache-Control":             "max-age=0",
}

if _USE_CLOUDSCRAPER:
    session = _scraper
    session.headers.update(HEADERS)
    print("[Info] cloudscraper activo")
else:
    session = requests.Session()
    session.headers.update(HEADERS)
    print("[Info] requests (sem cloudscraper — instala com: pip install cloudscraper)")


def _warm_session():
    """Visita a homepage primeiro para obter cookies de sessão."""
    for url in [BASE_URL + "/pt/", BASE_URL + "/"]:
        try:
            r = session.get(url, timeout=20)
            if r.ok:
                print(f"[Session] cookies obtidos de {url}")
                return True
        except Exception:
            pass
    return False


# ── Utilitários ───────────────────────────────────────────────────────────────

def get_page(url: str) -> BeautifulSoup | None:
    global DEBUG_HTML
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        if DEBUG_HTML:
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(r.text)
            print(f"[DEBUG] HTML guardado em debug_page.html")
            DEBUG_HTML = False
        return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"  [ERRO] {url}: {e}")
        return None


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


# ── Extracção de campos ───────────────────────────────────────────────────────

def extract_jsonld(soup: BeautifulSoup) -> dict:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            return data
        except Exception:
            pass
    return {}


def extract_meta(soup: BeautifulSoup) -> dict:
    meta = {}
    for tag in soup.find_all("meta"):
        key = tag.get("property") or tag.get("name") or ""
        val = tag.get("content", "").strip()
        if key and val:
            meta[key] = val
    return meta


def extract_poi(url: str) -> dict | None:
    soup = get_page(url)
    if not soup:
        return None

    row: dict = {"url": url}

    # ── Derivar campos da URL ────────────────────────────────────────────────
    # Padrões conhecidos:
    #   /pt/poi/{categoria}/{slug}/{id}/
    #   /pt/event/{categoria}/{slug}/{id}/
    #   /pt/p/{tipo}/{id}/
    parts = url.rstrip("/").split("/")
    row["id_poi"] = parts[-1] if parts[-1].isdigit() else ""

    if "/pt/poi/" in url:
        row["tipo_url"]  = "poi"
        row["slug"]      = parts[-2] if len(parts) >= 2 else ""
        row["categoria"] = parts[-3] if len(parts) >= 3 else ""
    elif "/pt/event/" in url:
        row["tipo_url"]  = "evento"
        row["slug"]      = parts[-2] if len(parts) >= 2 else ""
        row["categoria"] = parts[-3] if len(parts) >= 3 else ""
    elif "/pt/tour/" in url:
        row["tipo_url"]  = "tour"
        row["slug"]      = parts[-2] if len(parts) >= 2 else ""
        row["categoria"] = parts[-3] if len(parts) >= 3 else ""
    elif "/pt/p/" in url:
        row["tipo_url"]  = parts[-2] if len(parts) >= 2 else "p"
        row["slug"]      = ""
        row["categoria"] = row["tipo_url"]
    else:
        row["tipo_url"]  = ""
        row["slug"]      = parts[-2] if len(parts) >= 2 else ""
        row["categoria"] = parts[-3] if len(parts) >= 3 else ""

    # ── JSON-LD (dados estruturados — mais fiáveis) ──────────────────────────
    jld = extract_jsonld(soup)
    if jld:
        row["nome"]      = jld.get("name", "")
        row["descricao"] = jld.get("description", "")
        row["tipo"]      = jld.get("@type", "")
        row["website"]   = jld.get("url", "")
        row["telefone"]  = jld.get("telephone", "")
        row["email"]     = jld.get("email", "")

        addr = jld.get("address", {})
        if isinstance(addr, dict):
            row["morada"]    = addr.get("streetAddress", "")
            row["localidade"]= addr.get("addressLocality", "")
            row["regiao"]    = addr.get("addressRegion", "")
            row["pais"]      = addr.get("addressCountry", "")
        elif isinstance(addr, str):
            row["morada"] = addr

        geo = jld.get("geo", {})
        if isinstance(geo, dict):
            row["latitude"]  = geo.get("latitude", "")
            row["longitude"] = geo.get("longitude", "")

        row["preco"]         = str(jld.get("priceRange", "") or jld.get("price", ""))
        row["horario"]       = str(jld.get("openingHours", "") or jld.get("openingHoursSpecification", ""))
        row["imagem_jsonld"] = str(jld.get("image", ""))

    # ── Open Graph / meta tags ───────────────────────────────────────────────
    meta = extract_meta(soup)
    if not row.get("nome"):
        row["nome"] = meta.get("og:title", meta.get("title", ""))
    if not row.get("descricao"):
        row["descricao"] = meta.get("og:description", meta.get("description", ""))
    row["og_image"] = meta.get("og:image", "")

    # ── Título H1 ────────────────────────────────────────────────────────────
    h1 = soup.find("h1")
    if h1:
        row["h1"] = _text(h1)

    # ── Pares label → valor (dt/dd, th/td, strong+span, etc.) ───────────────
    pares: list[tuple[str, str]] = []

    for dl in soup.find_all("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            pares.append((_text(dt), _text(dd)))

    for tr in soup.find_all("tr"):
        ths = tr.find_all("th")
        tds = tr.find_all("td")
        for th, td in zip(ths, tds):
            pares.append((_text(th), _text(td)))

    for el in soup.find_all(class_=re.compile(r"field|detail|info|meta|attr|prop", re.I)):
        label = el.find(["label", "strong", "b", "dt", "th", "span"],
                        class_=re.compile(r"label|key|title|name", re.I))
        value = el.find(["span", "p", "div", "dd", "td"],
                        class_=re.compile(r"value|content|data|text", re.I))
        if label and value:
            pares.append((_text(label), _text(value)))

    for label_txt, val_txt in pares:
        if not label_txt or not val_txt or label_txt == val_txt:
            continue
        key = re.sub(r"[^\w]", "_", label_txt.lower().strip("_"))[:40]
        key = f"campo_{key}"
        if key not in row:
            row[key] = val_txt

    # ── Imagens ──────────────────────────────────────────────────────────────
    imgs = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if any(x in src for x in ["/photo", "/image", "/media", "/upload", "/poi"]):
            imgs.append(urljoin(BASE_URL, src))
    row["imagens"] = " | ".join(dict.fromkeys(imgs))  # sem duplicados

    # ── Descrição longa (texto livre) ────────────────────────────────────────
    if not row.get("descricao"):
        for tag in soup.find_all(["p", "div"],
                                 class_=re.compile(r"desc|content|body|text|about", re.I)):
            txt = _text(tag)
            if len(txt) > 120:
                row["descricao"] = txt[:3000]
                break

    # ── Tags / categorias adicionais ─────────────────────────────────────────
    tags = []
    for tag in soup.find_all(class_=re.compile(r"\btag\b|\bbadge\b|\blabel\b|\bchip\b", re.I)):
        t = _text(tag)
        if t and len(t) < 60:
            tags.append(t)
    row["tags"] = " | ".join(dict.fromkeys(tags))

    # ── Redes sociais ────────────────────────────────────────────────────────
    sociais = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(s in href for s in ["facebook.com", "instagram.com", "twitter.com",
                                   "youtube.com", "tiktok.com", "linkedin.com"]):
            sociais.append(href)
    row["redes_sociais"] = " | ".join(dict.fromkeys(sociais))

    return row


# ── Descoberta de URLs ────────────────────────────────────────────────────────

# Categorias de fallback (caso a descoberta automática não encontre nada)
_FALLBACK_CATS: dict[str, list[str]] = {
    "poi": [
        # MERGULHAR
        "praias-ou-piscinas", "docas-cais-e-fluvinas", "termas-e-spa",
        # CONHECER
        "paisagens", "historia-e-cultura", "gastronomia",
        # PLANEAR
        "onde-comer", "onde-dormir", "postos-de-turismo",
        # categorias anteriores
        "outras-paisagens", "trilhos", "experiencias", "alojamentos",
        "restaurantes", "praias", "parques", "miradouros", "monumentos",
        "museus", "aldeias", "cascatas", "lagos", "praias-fluviais",
        "atividades", "pontos-de-interesse",
    ],
    "event": [
        "feiras-e-tradicoes", "festivais", "mercados", "concertos",
        "desporto", "cultura", "gastronomia", "natureza", "outros",
    ],
    "tour": [
        # PASSEAR (menu visível)
        "caminhadas", "bicicleta", "roteiros-tematicos",
        # categorias anteriores
        "caminhada-de-longa-distancia", "caminhada", "btt", "ciclismo",
        "trail", "canoagem", "escalada", "equitacao", "outros",
    ],
    "p": [
        # PARTICIPAR
        "desafios", "experiencias-guiadas", "comprar-produtos-locais",
        # anteriores
        "contactos", "praias-fluviais-ou-piscinas", "eventos", "noticias",
        "percursos", "alojamento", "restauracao", "servicos", "outros",
    ],
}


def _collect_links(soup: BeautifulSoup, urls: set, base: str) -> int:
    """Recolhe todos os links de items (poi, event, tour, p) de uma página."""
    found = 0
    for a in soup.find_all("a", href=True):
        href = a["href"].split("#")[0]
        if re.search(r"/pt/(poi|event|tour|p)/", href) and re.search(r"/\d+/?$", href):
            full = urljoin(base, href).rstrip("/") + "/"
            if full not in urls:
                urls.add(full)
                found += 1
    return found


def _discover_nav_categories() -> dict[str, list[str]]:
    """
    Crawla a navegação do site para descobrir automaticamente todas as
    categorias existentes. Retorna {tipo: [slug, ...]}
    """
    found: dict[str, set[str]] = {"poi": set(), "event": set(), "tour": set(), "p": set()}

    for path in ["/pt/", "/"]:
        soup = get_page(BASE_URL + path)
        if not soup:
            continue
        for a in soup.find_all("a", href=True):
            href = urljoin(BASE_URL, a["href"].split("#")[0]).rstrip("/")
            m = re.match(r"https?://[^/]+/pt/(poi|event|tour|p)/([^/?#]+)$", href)
            if m:
                tipo, slug = m.group(1), m.group(2)
                if not re.search(r"^\d+$", slug):  # ignorar IDs directos
                    found[tipo].add(slug)

    result = {k: sorted(v) for k, v in found.items() if v}
    if result:
        for tipo, cats in result.items():
            print(f"[Nav] {tipo}: {', '.join(cats)}")
    return result


def _crawl_categories(base_type: str, cats: list[str], urls: set):
    """Pagina por cada categoria e recolhe URLs de items."""
    for cat in cats:
        for page in range(1, 50):
            soup = get_page(f"{BASE_URL}/pt/{base_type}/{cat}/?page={page}")
            if not soup:
                break
            found = _collect_links(soup, urls, BASE_URL)
            if found == 0:
                break
            print(f"  [{base_type}/{cat}] pág {page}: +{found}")
            time.sleep(DELAY)


def discover_urls() -> list[str]:
    urls: set[str] = set()

    # 1. Sitemap
    for path in ["/sitemap.xml", "/sitemap_index.xml", "/pt/sitemap.xml"]:
        try:
            r = session.get(BASE_URL + path, timeout=15)
            if not r.ok:
                continue
            soup = BeautifulSoup(r.text, "lxml")
            for loc in soup.find_all("loc"):
                u = loc.get_text(strip=True)
                if re.search(r"/pt/(poi|event|tour|p)/", u) and re.search(r"/\d+/?$", u):
                    urls.add(u)
            if urls:
                print(f"[Sitemap] {len(urls)} URLs em {path}")
                return list(urls)
        except Exception:
            pass

    # 2. Descoberta automática de categorias a partir da navegação
    nav_cats = _discover_nav_categories()

    # 3. Para cada tipo, usa categorias da nav + fallback (sem duplicados)
    for tipo in ("poi", "event", "tour", "p"):
        nav = nav_cats.get(tipo, [])
        fallback = _FALLBACK_CATS.get(tipo, [])
        # nav primeiro; fallback acrescenta categorias não descobertas pela nav
        all_cats = list(dict.fromkeys(nav + [c for c in fallback if c not in nav]))
        _crawl_categories(tipo, all_cats, urls)

    # 4. Páginas de topo (apanha links soltos)
    for path in ["/pt/poi/", "/pt/event/", "/pt/tour/", "/pt/p/", "/pt/", "/"]:
        soup = get_page(BASE_URL + path)
        if soup:
            _collect_links(soup, urls, BASE_URL)

    print(f"[Descoberta] {len(urls)} URLs no total")
    return list(urls)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  guidedbynature.pt — Crawler")
    print("=" * 60)

    _warm_session()
    urls = discover_urls()

    if not urls:
        print("\n[Aviso] Não foi possível descobrir URLs automaticamente.")
        print("A usar URLs de exemplo fornecidos.")
        urls = [
            "https://guidedbynature.pt/pt/poi/outras-paisagens/zona-de-lazer-de-fermil/803708969/",
            "https://guidedbynature.pt/pt/poi/outras-paisagens/parque-da-fraga-do-rio/803708890/",
            "https://guidedbynature.pt/pt/poi/outras-paisagens/praia-fluvial-de-espadanedo/803709017/",
            "https://guidedbynature.pt/pt/event/feiras-e-tradicoes/festa-do-caldo-de-quintandona/810958021/",
            "https://guidedbynature.pt/pt/p/eventos/803757503/",
            "https://guidedbynature.pt/pt/p/contactos/803158587/",
            "https://guidedbynature.pt/pt/p/praias-fluviais-ou-piscinas/803158567/",
            "https://guidedbynature.pt/pt/tour/caminhada-de-longa-distancia/gr47-grande-rota-de-montemuro/66287236/",
        ]

    print(f"\nA processar {len(urls)} POIs...\n")

    dados = []
    for i, url in enumerate(urls, 1):
        print(f"[{i:4}/{len(urls)}] {url.split('/')[-2] or url}")
        row = extract_poi(url)
        if row:
            dados.append(row)
        time.sleep(DELAY)

    if not dados:
        print("\n[Erro] Nenhum dado extraído. O site pode estar a bloquear.")
        print("Abra debug_page.html no browser para ver o HTML.")
        return

    df = pd.DataFrame(dados)

    # Reordenar colunas: campos principais primeiro
    priority = ["id_poi", "nome", "h1", "categoria", "slug", "tipo",
                 "descricao", "morada", "localidade", "regiao", "pais",
                 "latitude", "longitude", "telefone", "email", "website",
                 "preco", "horario", "imagem_jsonld", "og_image", "imagens",
                 "tags", "redes_sociais", "url"]
    cols = [c for c in priority if c in df.columns]
    extra = [c for c in df.columns if c not in cols]
    df = df[cols + extra]

    df.to_excel(OUTPUT, index=False)
    print(f"\n✅ Exportado: {OUTPUT}")
    print(f"   {len(dados)} linhas  ×  {len(df.columns)} colunas")
    print(f"\nCampos extraídos: {', '.join(df.columns.tolist())}")


if __name__ == "__main__":
    main()
