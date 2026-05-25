#!/usr/bin/env python3
"""
Crawler v4 — guidedbynature.pt
Sem pandas, sem lxml — compatível com Termux/Android.

Descoberta em cascata:
  1. Sitemap XML  (mais rápido e completo)
  2. URLs em <script> JSON embutido  (para sites React/Vue)
  3. BFS por links + atributos data-*  (fallback geral)

Dependências:
    pip install beautifulsoup4 openpyxl cloudscraper

Correr:
    python guidedbynature_crawler.py

Ficheiro gerado: guidedbynature_dados.xlsx  (Dados | Presença | Resumo)
"""

try:
    import cloudscraper
    session = cloudscraper.create_scraper()
    session.headers.update({
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
        "Cache-Control":   "max-age=0",
    })
    print("[Info] cloudscraper activo")
except ImportError:
    import requests
    session = requests.Session()
    session.headers.update({
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
    })
    print("[Info] requests simples")

from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from urllib.parse import urljoin, urlparse
from collections import deque
import json
import re
import time

BASE_URL  = "https://guidedbynature.pt"
OUTPUT    = "guidedbynature_dados.xlsx"
DELAY     = 0.8    # segundos entre pedidos
MAX_VISIT = 8000   # limite de segurança para BFS

# URL de item individual (com ID numérico no fim)
_ITEM_RE = re.compile(
    r"/pt/(poi|event|tour)/[^/?#]+/[^/?#]+/\d+/?$"
    r"|/pt/p/[^/?#]+/\d+/?$"
)
# URL de item em qualquer formato — usado para extrair de scripts/JSON
_ITEM_RE_LOOSE = re.compile(r"/pt/(poi|event|tour|p)/[^\"'\s]+/\d+")

_SKIP = [
    "/api/", "/admin/", "/static/", "/media/", "/files/",
    "/en/", "/es/", "/fr/", "/de/",
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg",
    ".zip", ".js", ".css", ".ico",
]


# ── Utilitários de URL ────────────────────────────────────────────────────────

def _normalize(url: str) -> str:
    try:
        p = urlparse(url)
    except Exception:
        return ""
    netloc = p.netloc.replace("www.", "")
    base_netloc = BASE_URL.replace("https://", "").replace("http://", "").replace("www.", "")
    if p.netloc and netloc != base_netloc:
        return ""
    if p.scheme and p.scheme not in ("http", "https"):
        return ""
    path = p.path or "/"
    if not path.endswith("/"):
        path += "/"
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
    return not any(s in path for s in _SKIP)


# ── HTTP ─────────────────────────────────────────────────────────────────────

def get_raw(url: str, timeout=25) -> str | None:
    """Retorna o texto bruto da página, sem parsear."""
    for attempt in range(3):
        try:
            r = session.get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.text
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                print(f"  [ERRO] {url}: {e}")
    return None


def get_page(url: str):
    html = get_raw(url)
    return BeautifulSoup(html, "html.parser") if html else None


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


# ── Descoberta 1: Sitemap XML ─────────────────────────────────────────────────

def _parse_sitemap(url: str, item_urls: set, visited: set, depth=0):
    if url in visited or depth > 6:
        return
    visited.add(url)
    html = get_raw(url, timeout=20)
    if not html:
        return

    # Extrair todos os <loc>
    locs = re.findall(r"<loc>\s*([^<]+)\s*</loc>", html)

    # Se tem <sitemapindex> ou <sitemap>, são sub-sitemaps
    if "<sitemapindex" in html or ("<sitemap>" in html and "<loc>" in html and ".xml" in html):
        sub = [l.strip() for l in locs if l.strip().endswith(".xml")]
        print(f"  [Sitemap índice] {len(sub)} sub-sitemaps em {url}")
        for s in sub:
            _parse_sitemap(s, item_urls, visited, depth + 1)
        return

    # Folha: extrair URLs de items
    before = len(item_urls)
    for loc in locs:
        loc = loc.strip()
        if _ITEM_RE.search(loc):
            item_urls.add(loc.rstrip("/") + "/")
    added = len(item_urls) - before
    if added:
        print(f"  [Sitemap] +{added} items ({len(item_urls)} total) — {url}")
    time.sleep(0.3)


def discover_via_sitemap() -> set:
    item_urls: set = set()
    visited:   set = set()

    # 1. robots.txt
    html = get_raw(BASE_URL + "/robots.txt", timeout=10)
    if html:
        for m in re.finditer(r"(?i)Sitemap:\s*(\S+)", html):
            _parse_sitemap(m.group(1).strip(), item_urls, visited)

    # 2. Localizações comuns
    if not item_urls:
        for path in [
            "/sitemap.xml", "/sitemap_index.xml",
            "/pt/sitemap.xml", "/sitemap-pt.xml",
            "/sitemaps/index.xml", "/sitemap/sitemap.xml",
        ]:
            _parse_sitemap(BASE_URL + path, item_urls, visited)
            if item_urls:
                break

    return item_urls


# ── Descoberta 2: URLs embutidas em <script> ──────────────────────────────────

def _urls_from_scripts(html: str, base: str) -> set:
    """Extrai URLs de items que estejam embutidas em JSON/JS na página."""
    found = set()
    for m in _ITEM_RE_LOOSE.finditer(html):
        raw = m.group(0).rstrip("\"'\\,; ")
        norm = _normalize(urljoin(base, raw))
        if norm and _is_item(norm):
            found.add(norm)
    return found


def _urls_from_data_attrs(soup, base: str) -> set:
    """Extrai URLs de atributos data-url, data-href, data-link, etc."""
    found = set()
    for el in soup.find_all(True):
        for attr in ("data-url", "data-href", "data-link", "data-path", "data-target"):
            val = el.get(attr, "")
            if val and _ITEM_RE.search(val):
                norm = _normalize(urljoin(base, val))
                if norm:
                    found.add(norm)
    return found


# ── Descoberta 3: BFS completo ────────────────────────────────────────────────

def discover_via_bfs(known_items: set) -> set:
    seeds = [
        BASE_URL + "/pt/",
        BASE_URL + "/",
        BASE_URL + "/pt/poi/",
        BASE_URL + "/pt/event/",
        BASE_URL + "/pt/tour/",
        BASE_URL + "/pt/p/",
    ]

    queue     = deque(seeds)
    visited   = set()
    item_urls = set(known_items)
    nav_count = 0

    print(f"[BFS] Inicio — {len(seeds)} sementes, {len(known_items)} items já conhecidos")

    while queue and nav_count < MAX_VISIT:
        url  = queue.popleft()
        norm = _normalize(url)
        if not norm or norm in visited or not _is_crawlable(norm):
            continue
        visited.add(norm)
        nav_count += 1

        if _is_item(norm):
            item_urls.add(norm)
            continue

        if nav_count % 20 == 0 or nav_count <= 5:
            print(f"  [BFS {nav_count:4}] {norm}  |  items: {len(item_urls)}")

        html = get_raw(norm)
        if not html:
            time.sleep(DELAY)
            continue

        soup = BeautifulSoup(html, "html.parser")

        # Extrair URLs de <script> e atributos data-*
        for u in _urls_from_scripts(html, norm):
            item_urls.add(u)
        for u in _urls_from_data_attrs(soup, norm):
            item_urls.add(u)

        # Links <a href>
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("javascript") or href.startswith("mailto") or href.startswith("tel"):
                continue
            full  = urljoin(norm, href).split("#")[0]
            norm2 = _normalize(full)
            if not norm2 or not _is_crawlable(norm2) or norm2 in visited:
                continue
            if _is_item(norm2):
                item_urls.add(norm2)
            else:
                queue.append(norm2)

        time.sleep(DELAY)

    print(f"[BFS] {nav_count} páginas nav | {len(item_urls)} items no total")
    return item_urls


# ── Extracção de dados de um item ─────────────────────────────────────────────

def extract_jsonld(soup) -> dict:
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


def extract_meta(soup) -> dict:
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

    meta = extract_meta(soup)
    if not row.get("nome"):
        row["nome"] = meta.get("og:title", meta.get("title", ""))
    if not row.get("descricao"):
        row["descricao"] = meta.get("og:description", meta.get("description", ""))
    row["og_image"] = meta.get("og:image", "")

    h1 = soup.find("h1")
    if h1:
        row["h1"] = _text(h1)

    pares = []
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
    for lbl, val in pares:
        if not lbl or not val or lbl == val:
            continue
        key = "campo_" + re.sub(r"[^\w]", "_", lbl.lower().strip("_"))[:40]
        if key not in row:
            row[key] = val

    imgs = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if any(x in src for x in ["/photo", "/image", "/media", "/upload", "/poi", "/tour", "/event"]):
            imgs.append(urljoin(BASE_URL, src))
    row["imagens"] = " | ".join(dict.fromkeys(imgs))

    if not row.get("descricao"):
        for tag in soup.find_all(["p", "div"],
                                  class_=re.compile(r"desc|content|body|text|about", re.I)):
            txt = _text(tag)
            if len(txt) > 120:
                row["descricao"] = txt[:3000]
                break

    tags = []
    for tag in soup.find_all(class_=re.compile(r"\btag\b|\bbadge\b|\blabel\b|\bchip\b", re.I)):
        t = _text(tag)
        if t and len(t) < 60:
            tags.append(t)
    row["tags"] = " | ".join(dict.fromkeys(tags))

    sociais = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(s in href for s in ["facebook.com", "instagram.com", "twitter.com",
                                    "youtube.com", "tiktok.com", "linkedin.com"]):
            sociais.append(href)
    row["redes_sociais"] = " | ".join(dict.fromkeys(sociais))

    return row


# ── Excel com openpyxl ────────────────────────────────────────────────────────

_COLS_PRIORITY = [
    "id_poi", "nome", "h1", "tipo_url", "categoria", "slug", "tipo",
    "descricao", "morada", "localidade", "regiao", "pais",
    "latitude", "longitude", "telefone", "email", "website",
    "preco", "horario", "imagem_jsonld", "og_image", "imagens",
    "tags", "redes_sociais", "url",
]

_HDR_FILL  = PatternFill("solid", fgColor="1F4E79")
_HDR_FONT  = Font(color="FFFFFF", bold=True)
_X_FILL    = PatternFill("solid", fgColor="E2EFDA")


def _write_sheet(ws, headers, rows, presence=False):
    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = _HDR_FILL
        cell.font = _HDR_FONT
        cell.alignment = Alignment(horizontal="center")

    for row in rows:
        values = []
        for col in headers:
            val = str(row.get(col, "") or "").strip()
            values.append("X" if presence and val else ("" if presence else val))
        ws.append(values)

    if presence:
        for r in ws.iter_rows(min_row=2):
            for cell in r:
                if cell.value == "X":
                    cell.fill = _X_FILL
                    cell.alignment = Alignment(horizontal="center")

    for col_idx, col_name in enumerate(headers, 1):
        max_len = len(col_name)
        for r in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
            for cell in r:
                if cell.value:
                    max_len = max(max_len, min(len(str(cell.value)), 60))
        ws.column_dimensions[get_column_letter(col_idx)].width = max_len + 2


def _write_resumo(ws, dados):
    from collections import Counter
    ws.append(["tipo_url", "categoria", "total"])
    for col_idx in range(1, 4):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = _HDR_FILL
        cell.font = _HDR_FONT
        cell.alignment = Alignment(horizontal="center")
    counter = Counter()
    for row in dados:
        counter[(str(row.get("tipo_url", "")), str(row.get("categoria", "")))] += 1
    for (tipo, cat), total in sorted(counter.items()):
        ws.append([tipo, cat, total])
    for i in range(1, 4):
        ws.column_dimensions[get_column_letter(i)].width = 25


def save_excel(dados, output=OUTPUT):
    if not dados:
        print("[Erro] Sem dados para guardar.")
        return

    all_keys, seen = [], set()
    for row in dados:
        for k in row:
            if k not in seen:
                seen.add(k); all_keys.append(k)

    priority = [c for c in _COLS_PRIORITY if c in seen]
    headers  = priority + [c for c in all_keys if c not in priority]

    wb = Workbook()
    ws_dados = wb.active
    ws_dados.title = "Dados"
    _write_sheet(ws_dados, headers, dados)

    ws_pres = wb.create_sheet("Presença")
    _write_sheet(ws_pres, headers, dados, presence=True)

    ws_res = wb.create_sheet("Resumo")
    _write_resumo(ws_res, dados)

    wb.save(output)
    print(f"\n✅  {output}")
    print(f"    {len(dados)} linhas × {len(headers)} colunas")
    print(f"    Sheets: Dados | Presença (X/vazio) | Resumo por categoria")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  guidedbynature.pt — Crawler v4")
    print("=" * 60)

    try:
        r = session.get(BASE_URL + "/pt/", timeout=20)
        print(f"[Session] HTTP {r.status_code}")
    except Exception as e:
        print(f"[Session] {e}")

    # ── Fase 1: Sitemap ──────────────────────────────────────────────────────
    print("\n[Fase 1] Sitemap XML...")
    item_urls = discover_via_sitemap()
    print(f"  → {len(item_urls)} items via sitemap")

    # ── Fase 2: BFS (sempre corre — apanha o que o sitemap perdeu) ───────────
    print("\n[Fase 2] BFS completo (links + scripts + data-attrs)...")
    item_urls = discover_via_bfs(item_urls)
    print(f"  → {len(item_urls)} items no total")

    if not item_urls:
        print("\n[Aviso] Nenhum item encontrado.")
        print("Causa provável: conteúdo 100% renderizado em JS (precisa de Selenium).")
        return

    urls  = sorted(item_urls)
    total = len(urls)
    print(f"\n[Fase 3] Extracção de dados: {total} items\n")

    # ── Fase 3: extracção ────────────────────────────────────────────────────
    dados = []
    for i, url in enumerate(urls, 1):
        if i <= 10 or i % 50 == 0:
            print(f"[{i:5}/{total}] {url}")
        row = extract_item(url)
        if row:
            dados.append(row)

        if i % 300 == 0 and dados:
            save_excel(dados, OUTPUT.replace(".xlsx", f"_parcial_{i}.xlsx"))

        time.sleep(DELAY)

    save_excel(dados)


if __name__ == "__main__":
    main()
