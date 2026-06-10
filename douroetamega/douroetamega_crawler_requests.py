#!/usr/bin/env python3
"""
Crawler — douroetamega.pt  (versão sem Playwright)
BFS com requests/cloudscraper — funciona em Termux ARM 32-bit.
Não executa JavaScript, mas cobre a maioria das páginas estáticas.

Instalar:
    pip install cloudscraper openpyxl beautifulsoup4
    (se cloudscraper falhar: pip install requests openpyxl beautifulsoup4)

Correr:
    python douroetamega_crawler_requests.py
"""

import json
import re
import time
from collections import Counter, deque
from urllib.parse import urljoin, urlparse

try:
    import cloudscraper
    session = cloudscraper.create_scraper()
    print("[HTTP] A usar cloudscraper")
except ImportError:
    import requests
    session = requests.Session()
    print("[HTTP] A usar requests")

from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

BASE_URL  = "https://www.douroetamega.pt"
OUTPUT    = "douroetamega_dados.xlsx"
DELAY     = 0.8
MAX_PAGES = 10000

session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/136.0.0.0 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

_SKIP = [
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".zip", ".rar", ".doc", ".docx", ".xls", ".xlsx",
    ".mp3", ".mp4", ".avi", ".mov",
    "/wp-admin/", "/wp-login", "/feed/", "/xmlrpc",
    "/cart/", "/checkout/", "/my-account/",
    "mailto:", "tel:", "javascript:", "#",
]

_CONTENT_HINTS = re.compile(
    r"/(\d{2,}|[a-z0-9-]{5,})/?$"            # ID numérico (2+ dígitos) ou slug médio
    r"|/(?:poi|event|tour|lugar|local|artigo|noticia|posto|alojamento|restaurante"
    r"|gastronomia|municipio|parish|agenda|percurso|rota|trail|hiking|pages"
    r"|accommodation|restaurant|attraction|place|point-of-interest"
    r"|ficha|detalhe|detail|item|page|post|entry|news|product|service)/",
    re.I
)


def _normalize(url: str) -> str:
    try:
        p = urlparse(url)
    except Exception:
        return ""
    netloc = (p.netloc or "").replace("www.", "")
    base_n = BASE_URL.split("//")[-1].replace("www.", "")
    if p.netloc and netloc != base_n:
        return ""
    if p.scheme and p.scheme not in ("http", "https"):
        return ""
    path = p.path or "/"
    if not path.endswith("/"):
        path += "/"
    q = ""
    m = re.search(r"(?:page|pag|p)=(\d+)", p.query or "")
    if m and int(m.group(1)) > 1:
        q = f"?{p.query}"
    return f"{BASE_URL}{path}{q}"


def _is_skip(url: str) -> bool:
    low = url.lower()
    return any(s in low for s in _SKIP)


def _is_content_page(url: str) -> bool:
    path = urlparse(url).path
    depth = len([p for p in path.split("/") if p])
    # depth 1 só se tiver ID/slug; depth >= 2 sempre aceite
    if depth == 0:
        return False
    return bool(_CONTENT_HINTS.search(path)) or depth >= 2


def _get(url: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=25)
            if r.ok:
                return r.text
            if r.status_code in (403, 404, 410):
                return None
        except Exception as e:
            if attempt == retries - 1:
                print(f"  [ERRO] {url}: {e}")
        time.sleep(1.5 ** attempt)
    return None


def _sitemap_urls() -> list[str]:
    """Tenta descobrir URLs via sitemap.xml."""
    urls = []
    for sm in ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml",
               "/pt/sitemap.xml", "/sitemap/sitemap.xml"]:
        html = _get(BASE_URL + sm)
        if not html:
            continue
        found = re.findall(r"<loc>(https?://[^<]+)</loc>", html)
        # Se for sitemap index, buscar sitemaps filhos
        children = [u for u in found if "sitemap" in u.lower()]
        items    = [u for u in found if "sitemap" not in u.lower()]
        urls.extend(items)
        for child in children[:20]:
            child_html = _get(child)
            if child_html:
                child_urls = re.findall(r"<loc>(https?://[^<]+)</loc>", child_html)
                urls.extend([u for u in child_urls if "sitemap" not in u.lower()])
        if urls:
            print(f"  [Sitemap] {len(urls)} URLs em {sm}")
            break
    return urls


def _extract_data(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    row: dict = {"url": url}

    parts = url.rstrip("/").split("/")
    row["slug"]        = parts[-1] if parts[-1] else (parts[-2] if len(parts) >= 2 else "")
    row["profundidade"]= str(len([p for p in urlparse(url).path.split("/") if p]))
    path_parts = [p for p in urlparse(url).path.split("/") if p]
    row["secao"]     = path_parts[0] if path_parts else ""
    row["categoria"] = path_parts[1] if len(path_parts) >= 2 else ""

    # JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            if not isinstance(data, dict):
                continue
            row["nome"]      = data.get("name", "")
            row["descricao"] = data.get("description", "")
            row["tipo"]      = data.get("@type", "")
            row["website"]   = data.get("url", "")
            row["telefone"]  = data.get("telephone", "")
            row["email"]     = data.get("email", "")
            addr = data.get("address", {})
            if isinstance(addr, dict):
                row["morada"]     = addr.get("streetAddress", "")
                row["localidade"] = addr.get("addressLocality", "")
                row["regiao"]     = addr.get("addressRegion", "")
                row["pais"]       = addr.get("addressCountry", "")
            elif isinstance(addr, str):
                row["morada"] = addr
            geo = data.get("geo", {})
            if isinstance(geo, dict):
                row["latitude"]  = geo.get("latitude", "")
                row["longitude"] = geo.get("longitude", "")
            row["preco"]       = str(data.get("priceRange", "") or data.get("price", ""))
            row["horario"]     = str(data.get("openingHours", "") or "")
            row["imagem_jsonld"]= str(data.get("image", ""))
            row["data_inicio"] = str(data.get("startDate", ""))
            row["data_fim"]    = str(data.get("endDate", ""))
            row["local_evento"]= str(data.get("location", ""))
            break
        except Exception:
            pass

    # Open Graph / meta
    for tag in soup.find_all("meta"):
        prop = tag.get("property") or tag.get("name") or ""
        val  = (tag.get("content") or "").strip()
        if not val:
            continue
        if prop == "og:title" and not row.get("nome"):
            row["nome"] = val
        elif prop in ("og:description", "description") and not row.get("descricao"):
            row["descricao"] = val
        elif prop == "og:image":
            row["og_image"] = val
        elif prop == "og:type":
            row["og_tipo"] = val
        elif prop == "article:published_time":
            row["data_publicacao"] = val
        elif prop == "article:modified_time":
            row["data_modificacao"] = val

    h1 = soup.find("h1")
    if h1:
        row["h1"] = h1.get_text(" ", strip=True)
        if not row.get("nome"):
            row["nome"] = row["h1"]

    if not row.get("nome"):
        h2 = soup.find("h2")
        if h2:
            row["nome"] = h2.get_text(" ", strip=True)

    title = soup.find("title")
    if title and not row.get("nome"):
        row["nome"] = title.get_text(strip=True).split("|")[0].strip()

    # Pares dl/dt/dd e tabelas
    pares = []
    for dl in soup.find_all("dl"):
        for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
            t1 = dt.get_text(" ", strip=True)
            t2 = dd.get_text(" ", strip=True)
            if t1 and t2 and t1 != t2:
                pares.append((t1, t2))
    for tr in soup.find_all("tr"):
        for th, td in zip(tr.find_all("th"), tr.find_all("td")):
            t1 = th.get_text(" ", strip=True)
            t2 = td.get_text(" ", strip=True)
            if t1 and t2 and t1 != t2:
                pares.append((t1, t2))
    for el in soup.find_all(class_=re.compile(r"field|detail|info|meta|attr|prop|label", re.I)):
        lbl = el.find(["label","strong","b","dt","th","span"],
                      class_=re.compile(r"label|key|title|name", re.I))
        val_el = el.find(["span","p","div","dd","td"],
                         class_=re.compile(r"value|content|data|text|body", re.I))
        if lbl and val_el:
            t1 = lbl.get_text(" ", strip=True)
            t2 = val_el.get_text(" ", strip=True)
            if t1 and t2 and t1 != t2:
                pares.append((t1, t2))
    for lbl, val in pares:
        key = "campo_" + re.sub(r"[^\w]", "_", lbl.lower().strip("_"))[:40]
        if key not in row:
            row[key] = val

    # Imagens
    imgs = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if any(x in src.lower() for x in ["/upload", "/media", "/photo", "/image",
                                            "/content", "/assets", "/files", "/img"]):
            full = urljoin(BASE_URL, src)
            if full not in imgs:
                imgs.append(full)
    row["imagens"] = " | ".join(imgs[:10])

    if not row.get("descricao"):
        for tag in soup.find_all(["p","div"],
                                  class_=re.compile(r"desc|content|body|text|intro|summary|about", re.I)):
            txt = tag.get_text(" ", strip=True)
            if len(txt) > 100:
                row["descricao"] = txt[:3000]
                break

    tags = []
    for el in soup.find_all(class_=re.compile(r"\btag\b|\bbadge\b|\bchip\b|\bcategory\b|\bcategoria\b", re.I)):
        t = el.get_text(" ", strip=True)
        if t and len(t) < 80:
            tags.append(t)
    row["tags"] = " | ".join(dict.fromkeys(tags))

    sociais = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(s in href for s in ["facebook.com", "instagram.com", "twitter.com",
                                    "youtube.com", "tiktok.com", "linkedin.com",
                                    "x.com/", "threads.net"]):
            if href not in sociais:
                sociais.append(href)
    row["redes_sociais"] = " | ".join(sociais)

    for pat in [r"munic[íi]pio[:\s]+([A-ZÀ-Ú][^\n<]{2,40})",
                r"concelho[:\s]+([A-ZÀ-Ú][^\n<]{2,40})"]:
        m = re.search(pat, html, re.I)
        if m and not row.get("municipio"):
            row["municipio"] = m.group(1).strip()

    return row


def crawl_all() -> list[dict]:
    print(f"[BFS] Sitemap…")
    sitemap_urls = _sitemap_urls()

    queue   = deque([BASE_URL + "/"] + sitemap_urls)
    visited = set()
    content_pages: list[dict] = []
    nav_count = 0

    print(f"[BFS] A iniciar em {BASE_URL}  ({len(sitemap_urls)} URLs do sitemap)")

    while queue and nav_count < MAX_PAGES:
        url  = queue.popleft()
        norm = _normalize(url)
        if not norm or norm in visited or _is_skip(norm):
            continue
        visited.add(norm)
        nav_count += 1

        if nav_count % 50 == 0 or nav_count <= 5:
            print(f"  [BFS {nav_count:5}] {norm}  |  items: {len(content_pages)}")

        html = _get(norm)
        if not html:
            continue

        if _is_content_page(norm):
            row = _extract_data(norm, html)
            content_pages.append(row)
            if len(content_pages) % 100 == 0:
                print(f"  [Items] {len(content_pages)} páginas extraídas")
                save_excel(content_pages, OUTPUT.replace(".xlsx", f"_parcial_{len(content_pages)}.xlsx"))

        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or _is_skip(href):
                continue
            full  = urljoin(norm, href).split("#")[0]
            norm2 = _normalize(full)
            if norm2 and norm2 not in visited and not _is_skip(norm2):
                queue.append(norm2)

        time.sleep(DELAY)

    print(f"\n[BFS] {nav_count} páginas visitadas | {len(content_pages)} items extraídos")
    return content_pages


# ── Excel ─────────────────────────────────────────────────────────────────────

_COLS_PRIORITY = [
    "nome", "h1", "secao", "categoria", "slug", "tipo",
    "descricao", "morada", "localidade", "municipio", "regiao", "pais",
    "latitude", "longitude", "telefone", "email", "website",
    "preco", "horario", "data_inicio", "data_fim", "local_evento",
    "data_publicacao", "imagem_jsonld", "og_image", "og_tipo",
    "imagens", "tags", "redes_sociais", "profundidade", "url",
]

_HDR_FILL = PatternFill("solid", fgColor="17375E")
_HDR_FONT = Font(color="FFFFFF", bold=True)
_X_FILL   = PatternFill("solid", fgColor="E2EFDA")


def _write_sheet(ws, headers, rows, presence=False):
    ws.append(headers)
    for i in range(1, len(headers) + 1):
        c = ws.cell(row=1, column=i)
        c.fill = _HDR_FILL
        c.font = _HDR_FONT
        c.alignment = Alignment(horizontal="center")
    for row in rows:
        vals = []
        for col in headers:
            v = str(row.get(col, "") or "").strip()
            vals.append("X" if (presence and v) else ("" if presence else v))
        ws.append(vals)
    if presence:
        for r in ws.iter_rows(min_row=2):
            for cell in r:
                if cell.value == "X":
                    cell.fill = _X_FILL
                    cell.alignment = Alignment(horizontal="center")
    for i, name in enumerate(headers, 1):
        mx = len(name)
        for r in ws.iter_rows(min_row=2, min_col=i, max_col=i):
            for cell in r:
                if cell.value:
                    mx = max(mx, min(len(str(cell.value)), 60))
        ws.column_dimensions[get_column_letter(i)].width = mx + 2


def save_excel(dados, output=OUTPUT):
    if not dados:
        print("[Erro] Sem dados para guardar.")
        return

    all_keys, seen = [], set()
    for row in dados:
        for k in row:
            if k not in seen:
                seen.add(k)
                all_keys.append(k)

    priority = [c for c in _COLS_PRIORITY if c in seen]
    headers  = priority + [c for c in all_keys if c not in priority]

    wb = Workbook()
    ws = wb.active
    ws.title = "Dados"
    _write_sheet(ws, headers, dados)

    ws2 = wb.create_sheet("Presença")
    _write_sheet(ws2, headers, dados, presence=True)

    ws3 = wb.create_sheet("Resumo")
    ws3.append(["secao", "categoria", "total"])
    for i in range(1, 4):
        c = ws3.cell(row=1, column=i)
        c.fill = _HDR_FILL; c.font = _HDR_FONT
        c.alignment = Alignment(horizontal="center")
    counter = Counter(
        (str(r.get("secao", "")), str(r.get("categoria", ""))) for r in dados
    )
    for (s, c), n in sorted(counter.items()):
        ws3.append([s, c, n])
    for i in range(1, 4):
        ws3.column_dimensions[get_column_letter(i)].width = 28

    wb.save(output)
    print(f"\n✅  {output}")
    print(f"    {len(dados)} linhas × {len(headers)} colunas")
    print(f"    Sheets: Dados | Presença (X/vazio) | Resumo por secção")


if __name__ == "__main__":
    print("=" * 60)
    print("  douroetamega.pt — Crawler (requests/BFS, sem Playwright)")
    print("=" * 60)
    dados = crawl_all()
    save_excel(dados)
