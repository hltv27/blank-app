#!/usr/bin/env python3
"""
Crawler v2 — guidedbynature.pt
BFS completo por todos os links internos do site.
Exporta Excel com dois sheets:
  "Dados"    — valores reais extraídos
  "Presença" — X se campo preenchido, vazio se não

Instalar dependências:
    pip install requests beautifulsoup4 pandas openpyxl lxml cloudscraper

Correr:
    python guidedbynature_crawler.py

Ficheiro gerado: guidedbynature_dados.xlsx
"""

try:
    import cloudscraper
    _scraper = cloudscraper.create_scraper()
    _USE_CLOUDSCRAPER = True
except ImportError:
    _scraper = None
    _USE_CLOUDSCRAPER = False

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import re
from urllib.parse import urljoin, urlparse
from collections import deque

BASE_URL  = "https://guidedbynature.pt"
OUTPUT    = "guidedbynature_dados.xlsx"
DELAY     = 1.0     # segundos entre pedidos
MAX_VISIT = 5000    # limite de segurança (páginas de listagem/nav)

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Sec-Fetch-Dest":  "document",
    "Sec-Fetch-Mode":  "navigate",
    "Cache-Control":   "max-age=0",
}

if _USE_CLOUDSCRAPER:
    session = _scraper
    session.headers.update(HEADERS)
    print("[Info] cloudscraper activo")
else:
    session = requests.Session()
    session.headers.update(HEADERS)
    print("[Info] requests simples (pip install cloudscraper para mais bypass)")

# URL de item: termina em /poi/{cat}/{slug}/{id}/ ou /p/{tipo}/{id}/
_ITEM_RE = re.compile(
    r"/pt/(poi|event|tour)/[^/?#]+/[^/?#]+/\d+/?$"
    r"|/pt/p/[^/?#]+/\d+/?$"
)

# Paths a ignorar no BFS
_SKIP_PATHS = [
    "/api/", "/admin/", "/static/", "/media/", "/files/",
    "/en/", "/es/", "/fr/", "/de/",
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg",
    ".zip", ".xml", ".js", ".css", ".ico",
    "mailto:", "tel:", "javascript:",
]


# ── Utilitários de URL ────────────────────────────────────────────────────────

def _normalize(url: str) -> str:
    """
    Normaliza URL: mantém só o domínio BASE_URL + path + ?page=N se existir.
    Retorna "" se for externo ou inválido.
    """
    try:
        p = urlparse(url)
    except Exception:
        return ""

    # Só aceitar o mesmo domínio
    if p.netloc and p.netloc not in BASE_URL:
        return ""
    if p.scheme and p.scheme not in ("http", "https"):
        return ""

    path = p.path
    if not path:
        path = "/"
    if not path.endswith("/"):
        path += "/"

    # Preservar paginação
    q = ""
    m = re.search(r"page=(\d+)", p.query or "")
    if m and int(m.group(1)) > 1:
        q = f"?page={m.group(1)}"

    return f"{BASE_URL}{path}{q}"


def _is_item(url: str) -> bool:
    return bool(_ITEM_RE.search(url))


def _is_crawlable(url: str) -> bool:
    if not url.startswith(BASE_URL):
        return False
    path = urlparse(url).path.lower()
    return not any(s in path for s in _SKIP_PATHS)


# ── HTTP ─────────────────────────────────────────────────────────────────────

def get_page(url: str, retries: int = 2) -> BeautifulSoup | None:
    for attempt in range(retries + 1):
        try:
            r = session.get(url, timeout=25)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return BeautifulSoup(r.text, "lxml")
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
            else:
                print(f"  [ERRO] {url}: {e}")
    return None


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


# ── Extracção de dados de um item ─────────────────────────────────────────────

def extract_jsonld(soup: BeautifulSoup) -> dict:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            if isinstance(data, dict):
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


def extract_item(url: str) -> dict | None:
    soup = get_page(url)
    if not soup:
        return None

    row: dict = {"url": url}

    # Campos da URL
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

    # JSON-LD (fonte mais fiável)
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
            row["morada"]     = addr.get("streetAddress", "")
            row["localidade"] = addr.get("addressLocality", "")
            row["regiao"]     = addr.get("addressRegion", "")
            row["pais"]       = addr.get("addressCountry", "")
        elif isinstance(addr, str):
            row["morada"] = addr

        geo = jld.get("geo", {})
        if isinstance(geo, dict):
            row["latitude"]  = geo.get("latitude", "")
            row["longitude"] = geo.get("longitude", "")

        row["preco"]         = str(jld.get("priceRange", "") or jld.get("price", ""))
        row["horario"]       = str(jld.get("openingHours", "") or jld.get("openingHoursSpecification", ""))
        row["imagem_jsonld"] = str(jld.get("image", ""))

    # Open Graph / meta tags (fallback)
    meta = extract_meta(soup)
    if not row.get("nome"):
        row["nome"] = meta.get("og:title", meta.get("title", ""))
    if not row.get("descricao"):
        row["descricao"] = meta.get("og:description", meta.get("description", ""))
    row["og_image"] = meta.get("og:image", "")

    # H1
    h1 = soup.find("h1")
    if h1:
        row["h1"] = _text(h1)

    # Pares label→valor (dl/dt/dd, tabelas, elementos com classes field/detail)
    pares: list[tuple[str, str]] = []
    for dl in soup.find_all("dl"):
        for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
            pares.append((_text(dt), _text(dd)))
    for tr in soup.find_all("tr"):
        for th, td in zip(tr.find_all("th"), tr.find_all("td")):
            pares.append((_text(th), _text(td)))
    for el in soup.find_all(class_=re.compile(r"field|detail|info|meta|attr|prop", re.I)):
        lbl = el.find(["label", "strong", "b", "dt", "th", "span"],
                      class_=re.compile(r"label|key|title|name", re.I))
        val = el.find(["span", "p", "div", "dd", "td"],
                      class_=re.compile(r"value|content|data|text", re.I))
        if lbl and val:
            pares.append((_text(lbl), _text(val)))

    for label_txt, val_txt in pares:
        if not label_txt or not val_txt or label_txt == val_txt:
            continue
        key = "campo_" + re.sub(r"[^\w]", "_", label_txt.lower().strip("_"))[:40]
        if key not in row:
            row[key] = val_txt

    # Imagens
    imgs = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if any(x in src for x in ["/photo", "/image", "/media", "/upload", "/poi", "/tour", "/event"]):
            imgs.append(urljoin(BASE_URL, src))
    row["imagens"] = " | ".join(dict.fromkeys(imgs))

    # Descrição longa (fallback)
    if not row.get("descricao"):
        for tag in soup.find_all(["p", "div"],
                                  class_=re.compile(r"desc|content|body|text|about", re.I)):
            txt = _text(tag)
            if len(txt) > 120:
                row["descricao"] = txt[:3000]
                break

    # Tags / badges
    tags = []
    for tag in soup.find_all(class_=re.compile(r"\btag\b|\bbadge\b|\blabel\b|\bchip\b", re.I)):
        t = _text(tag)
        if t and len(t) < 60:
            tags.append(t)
    row["tags"] = " | ".join(dict.fromkeys(tags))

    # Redes sociais
    sociais = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(s in href for s in ["facebook.com", "instagram.com", "twitter.com",
                                    "youtube.com", "tiktok.com", "linkedin.com"]):
            sociais.append(href)
    row["redes_sociais"] = " | ".join(dict.fromkeys(sociais))

    return row


# ── Descoberta BFS ────────────────────────────────────────────────────────────

def discover_urls() -> list[str]:
    """
    BFS completo a partir das páginas de entrada do site.
    Visita todas as páginas internas em /pt/ e recolhe URLs de items.
    Segue paginação ilimitada nas listagens.
    """
    # Sementes: homepage + raízes de cada secção
    seeds = [
        BASE_URL + "/pt/",
        BASE_URL + "/",
        BASE_URL + "/pt/poi/",
        BASE_URL + "/pt/event/",
        BASE_URL + "/pt/tour/",
        BASE_URL + "/pt/p/",
    ]

    queue    = deque(seeds)
    visited  = set()          # páginas de navegação já visitadas
    item_urls = set()         # URLs de items a extrair

    nav_count = 0

    print(f"[BFS] A iniciar com {len(seeds)} sementes...")

    while queue and nav_count < MAX_VISIT:
        url = queue.popleft()
        norm = _normalize(url)
        if not norm or norm in visited:
            continue
        if not _is_crawlable(norm):
            continue
        visited.add(norm)
        nav_count += 1

        is_item = _is_item(norm)
        if is_item:
            item_urls.add(norm)
            # Items não precisam de ser crawlados para links
            continue

        if nav_count % 10 == 0 or nav_count <= 5:
            print(f"  [BFS nav {nav_count:4}] {norm}  |  items: {len(item_urls)}")

        soup = get_page(norm)
        if not soup:
            time.sleep(DELAY)
            continue

        # Recolher todos os links desta página
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("javascript") or href.startswith("mailto") or href.startswith("tel"):
                continue
            full = urljoin(norm, href).split("#")[0]
            norm2 = _normalize(full)
            if not norm2 or not _is_crawlable(norm2) or norm2 in visited:
                continue

            if _is_item(norm2):
                item_urls.add(norm2)
            else:
                queue.append(norm2)

        time.sleep(DELAY)

    print(f"\n[BFS] Concluído: {nav_count} páginas nav | {len(item_urls)} items encontrados")
    return list(item_urls)


# ── Colunas principais (ordem preferida no Excel) ─────────────────────────────

_COLS_PRIORITY = [
    "id_poi", "nome", "h1", "tipo_url", "categoria", "slug", "tipo",
    "descricao", "morada", "localidade", "regiao", "pais",
    "latitude", "longitude", "telefone", "email", "website",
    "preco", "horario", "imagem_jsonld", "og_image", "imagens",
    "tags", "redes_sociais", "url",
]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  guidedbynature.pt — Crawler v2 (BFS completo)")
    print("=" * 60)

    # Aquece sessão (cookies)
    try:
        r = session.get(BASE_URL + "/pt/", timeout=20)
        print(f"[Session] HTTP {r.status_code} — cookies: {dict(r.cookies)}")
    except Exception as e:
        print(f"[Session] Aviso: {e}")

    # ── Fase 1: descoberta ───────────────────────────────────────────────────
    print("\n[Fase 1] Descoberta de URLs por BFS...\n")
    urls = discover_urls()

    if not urls:
        print("[Aviso] Nenhuma URL de item descoberta.")
        print("Possíveis causas: site bloqueado por Cloudflare, ou conteúdo renderizado em JS.")
        return

    total = len(urls)
    print(f"\n[Fase 2] Extracção de dados: {total} items\n")

    # ── Fase 2: extracção ────────────────────────────────────────────────────
    dados = []
    for i, url in enumerate(sorted(urls), 1):
        if i <= 10 or i % 50 == 0:
            print(f"[{i:5}/{total}] {url}")
        row = extract_item(url)
        if row:
            dados.append(row)

        # Guarda parcialmente a cada 300 items
        if i % 300 == 0 and dados:
            pd.DataFrame(dados).fillna("").to_excel(
                OUTPUT.replace(".xlsx", f"_parcial_{i}.xlsx"), index=False
            )
            print(f"  [Parcial] {i}/{total} guardados")

        time.sleep(DELAY)

    if not dados:
        print("[Erro] Nenhum dado extraído.")
        return

    df = pd.DataFrame(dados).fillna("")

    # Reordenar colunas
    cols = [c for c in _COLS_PRIORITY if c in df.columns]
    cols += [c for c in df.columns if c not in cols]
    df = df[cols]

    # ── Sheet "Presença": X se campo tem valor, vazio se não ─────────────────
    df_pres = df.copy()
    for col in df_pres.columns:
        df_pres[col] = df_pres[col].apply(lambda v: "X" if str(v).strip() else "")

    # ── Exportar ─────────────────────────────────────────────────────────────
    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Dados", index=False)
        df_pres.to_excel(writer, sheet_name="Presença", index=False)

        # Sheet de resumo por categoria
        resumo = (
            df.groupby(["tipo_url", "categoria"])
              .agg(total=("url", "count"))
              .reset_index()
              .sort_values(["tipo_url", "categoria"])
        )
        resumo.to_excel(writer, sheet_name="Resumo", index=False)

    print(f"\n✅  Exportado: {OUTPUT}")
    print(f"    {len(dados)} linhas × {len(df.columns)} colunas")
    print(f"    Sheets: 'Dados' | 'Presença' (X/vazio) | 'Resumo' (por categoria)")
    print(f"\nCampos extraídos: {', '.join(df.columns.tolist())}")


if __name__ == "__main__":
    main()
