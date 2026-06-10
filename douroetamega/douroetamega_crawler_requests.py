#!/usr/bin/env python3
"""
Crawler — douroetamega.pt  (versão requests, sem Playwright)
Duas fases — igual ao guidedbynature:
  Fase 1: Descoberta — percorre todas as secções/categorias + paginação
  Fase 2: Extracção  — visita cada página de item e extrai dados

Instalar:
    pip install cloudscraper openpyxl beautifulsoup4
    (fallback: pip install requests openpyxl beautifulsoup4)

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
    _session = cloudscraper.create_scraper()
    print("[HTTP] cloudscraper OK")
except ImportError:
    import requests
    _session = requests.Session()
    print("[HTTP] requests (sem cloudscraper)")

_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/136.0.0.0 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.douroetamega.pt/",
})

from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

BASE_URL = "https://www.douroetamega.pt"
OUTPUT   = "douroetamega_dados.xlsx"
DELAY    = 0.8

# Regex que identifica URLs de items (não listagens)
# Padrões observados: /secao/slug-longo/, /pages/ID/, /sec/sub/slug/
_ITEM_RE = re.compile(
    r'href=["\']('
    r'/[a-z][a-z0-9-]*/\d+/'                     # /section/123/
    r'|/pages/\d+/'                               # /pages/730/
    r'|/[a-z][a-z0-9-]*/[a-z0-9][a-z0-9-]{4,}/'  # /section/slug-com-5+chars/
    r'|/[a-z][a-z0-9-]*/[a-z0-9-]+/[a-z0-9-]+/'  # /sec/sub/slug/
    r')["\']',
    re.I
)

# Extensões/paths a ignorar
_SKIP_EXT = (".pdf",".jpg",".jpeg",".png",".gif",".svg",".webp",
             ".zip",".rar",".doc",".docx",".xls",".xlsx",
             ".mp3",".mp4",".avi",".mov",".woff",".woff2",".css",".js")
_SKIP_PATH = ("/wp-admin/","/wp-login","/feed/","/xmlrpc",
              "/cart/","/checkout/","/my-account/",
              "/search/","/tag/","/author/")


def _is_skip(url: str) -> bool:
    low = url.lower()
    return (any(low.endswith(e) for e in _SKIP_EXT) or
            any(p in low for p in _SKIP_PATH) or
            low.startswith("mailto:") or low.startswith("tel:") or
            low.startswith("javascript:") or "#" in low)


def _is_internal(url: str) -> bool:
    try:
        p = urlparse(url)
        if not p.netloc:
            return True
        return p.netloc.replace("www.", "") == "douroetamega.pt"
    except Exception:
        return False


def _norm(url: str) -> str:
    """Normaliza URL: remove fragment, garante trailing slash."""
    try:
        p = urlparse(url.split("#")[0])
    except Exception:
        return ""
    if p.scheme not in ("", "http", "https"):
        return ""
    netloc = p.netloc or ""
    if netloc and netloc.replace("www.", "") != "douroetamega.pt":
        return ""
    path = p.path or "/"
    if "." in path.split("/")[-1]:   # ficheiro com extensão
        return ""
    if not path.endswith("/"):
        path += "/"
    qs = ("?" + p.query) if p.query else ""
    return f"{BASE_URL}{path}{qs}"


def _get(url: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            r = _session.get(url, timeout=25)
            if r.ok:
                return r.text
            if r.status_code in (403, 404, 410):
                return None
        except Exception as e:
            if attempt == retries - 1:
                print(f"  [ERRO] {url}: {e}")
        time.sleep(1.5 ** (attempt + 1))
    return None


# ── FASE 1: Descoberta ────────────────────────────────────────────────────────

def _discover_sections(html: str) -> list[str]:
    """Extrai URLs de secções/categorias da homepage e da nav."""
    soup = BeautifulSoup(html, "html.parser")
    sections = []
    seen = set()

    # Nav principal, menus, rodapé
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or _is_skip(href):
            continue
        full = _norm(urljoin(BASE_URL, href))
        if not full or full == BASE_URL + "/":
            continue
        path = urlparse(full).path
        depth = len([p for p in path.split("/") if p])
        # Secções de topo (profundidade 1) ou sub-categorias (profundidade 2)
        if 1 <= depth <= 2 and full not in seen:
            seen.add(full)
            sections.append(full)

    return sections


def _paginate(section_url: str) -> list[str]:
    """
    Para uma secção/categoria, percorre todas as páginas de listagem
    e recolhe URLs de items usando _ITEM_RE.
    Suporta ?page=N, ?p=N, /page/N/.
    """
    found: set[str] = set()

    for pg in range(1, 300):  # até 300 páginas por secção
        if pg == 1:
            url = section_url
        else:
            # Tenta os padrões de paginação mais comuns
            url = section_url.rstrip("/") + f"/?page={pg}"

        html = _get(url)
        if not html:
            break

        before = len(found)
        for m in _ITEM_RE.finditer(html):
            item_path = m.group(1)
            if _is_skip(item_path):
                continue
            full = _norm(BASE_URL + item_path)
            if full:
                found.add(full)

        new_count = len(found) - before

        # Também segue links "próximo / next / ›" explícitos
        soup = BeautifulSoup(html, "html.parser")
        next_found = False
        for a in soup.find_all("a", href=True):
            text = a.get_text(" ", strip=True).lower()
            if any(t in text for t in ["próxima", "seguinte", "next", "›", "»", "mais"]):
                href = _norm(urljoin(url, a["href"]))
                if href and href != url:
                    next_found = True
                    break

        if pg > 1 and new_count == 0 and not next_found:
            break  # última página

    return list(found)


def discover_urls() -> list[str]:
    """
    Fase 1 — Descobre todos os URLs de items do site.
    1. Lê homepage → extrai secções
    2. Para cada secção → pagina e extrai items
    3. BFS de profundidade limitada para apanhar sub-secções
    """
    print("[Fase 1] A descobrir secções a partir da homepage…")
    html_home = _get(BASE_URL + "/")
    if not html_home:
        print("  [ERRO] Não conseguiu aceder à homepage.")
        return []

    sections = _discover_sections(html_home)
    print(f"  {len(sections)} secções encontradas na nav")

    # BFS para também explorar sub-secções (profundidade 2)
    visited_sections: set[str] = {BASE_URL + "/"}
    queue = deque(sections)
    all_sections: list[str] = []

    while queue:
        sec = queue.popleft()
        if sec in visited_sections:
            continue
        visited_sections.add(sec)
        all_sections.append(sec)

        # Explorar sub-secções desta secção
        html = _get(sec)
        if not html:
            continue
        time.sleep(0.3)
        sub = _discover_sections(html)
        for s in sub:
            if s not in visited_sections:
                path = urlparse(s).path
                depth = len([p for p in path.split("/") if p])
                if depth <= 3:  # não vai fundo demais
                    queue.append(s)

    print(f"  {len(all_sections)} secções/sub-secções a percorrer\n")

    # Para cada secção, paginar e recolher items
    all_urls: set[str] = set()
    for i, sec in enumerate(all_sections, 1):
        items = _paginate(sec)
        if items:
            print(f"  [{i:3}/{len(all_sections)}] {sec.split(BASE_URL)[-1]}  →  {len(items)} items")
            all_urls.update(items)
        time.sleep(DELAY)

    # Também apanha items directamente ligados da homepage
    for m in _ITEM_RE.finditer(html_home):
        full = _norm(BASE_URL + m.group(1))
        if full:
            all_urls.add(full)

    print(f"\n[Fase 1] {len(all_urls)} URLs únicos descobertos\n")
    return sorted(all_urls)


# ── FASE 2: Extracção ─────────────────────────────────────────────────────────

def extract_page(url: str, html: str) -> dict:
    """Extrai todos os dados disponíveis de uma página de item."""
    soup = BeautifulSoup(html, "html.parser")
    row: dict = {"url": url}

    # Info do URL
    parts = url.rstrip("/").split("/")
    path_parts = [p for p in urlparse(url).path.split("/") if p]
    row["id"]        = parts[-1] if parts[-1].isdigit() else ""
    row["slug"]      = parts[-1] if not parts[-1].isdigit() else (parts[-2] if len(parts) >= 2 else "")
    row["secao"]     = path_parts[0] if path_parts else ""
    row["categoria"] = path_parts[1] if len(path_parts) >= 2 else ""
    row["profundidade"] = str(len(path_parts))

    # JSON-LD (mais fiável)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            if not isinstance(data, dict):
                continue
            row["nome"]       = data.get("name", "")
            row["descricao"]  = data.get("description", "")
            row["tipo"]       = data.get("@type", "")
            row["website"]    = data.get("url", "")
            row["telefone"]   = data.get("telephone", "")
            row["email"]      = data.get("email", "")
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
            row["preco"]         = str(data.get("priceRange", "") or data.get("price", ""))
            row["horario"]       = str(data.get("openingHours", "") or "")
            row["imagem_jsonld"] = str(data.get("image", ""))
            row["data_inicio"]   = str(data.get("startDate", ""))
            row["data_fim"]      = str(data.get("endDate", ""))
            row["local_evento"]  = str(data.get("location", ""))
            break
        except Exception:
            pass

    # Open Graph / meta tags
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
        elif prop in ("keywords",):
            row["keywords"] = val

    # H1 → nome
    h1 = soup.find("h1")
    if h1:
        row["h1"] = h1.get_text(" ", strip=True)
        if not row.get("nome"):
            row["nome"] = row["h1"]

    # H2 fallback
    if not row.get("nome"):
        h2 = soup.find("h2")
        if h2:
            row["nome"] = h2.get_text(" ", strip=True)

    # <title> último fallback
    title = soup.find("title")
    if title and not row.get("nome"):
        row["nome"] = title.get_text(strip=True).split("|")[0].split("–")[0].strip()

    # Pares label → valor  (dl/dt/dd, tabelas th/td, campos de ficha)
    pares: list[tuple] = []
    for dl in soup.find_all("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            t1 = dt.get_text(" ", strip=True)
            t2 = dd.get_text(" ", strip=True)
            if t1 and t2 and t1 != t2:
                pares.append((t1, t2))
    for tr in soup.find_all("tr"):
        ths = tr.find_all("th")
        tds = tr.find_all("td")
        for th, td in zip(ths, tds):
            t1 = th.get_text(" ", strip=True)
            t2 = td.get_text(" ", strip=True)
            if t1 and t2 and t1 != t2:
                pares.append((t1, t2))
    # Elementos com classes de campo
    for el in soup.find_all(class_=re.compile(
            r"field|detail|info|meta|attr|prop|label|ficha|dado", re.I)):
        lbl = el.find(["label","strong","b","dt","th","span","h4","h5"],
                      class_=re.compile(r"label|key|title|name|campo", re.I))
        val_el = el.find(["span","p","div","dd","td"],
                         class_=re.compile(r"value|content|data|text|body|valor", re.I))
        if lbl and val_el:
            t1 = lbl.get_text(" ", strip=True)
            t2 = val_el.get_text(" ", strip=True)
            if t1 and t2 and t1 != t2:
                pares.append((t1, t2))

    # Detectar campos comuns por label normalizado
    _label_map = {
        "municipio": ["município","municipio","concelho"],
        "morada":    ["morada","endereço","address","localização"],
        "telefone":  ["telefone","telef.","tel","contacto telefónico"],
        "email":     ["e-mail","email","correio electrónico"],
        "horario":   ["horário","horario","horas de funcionamento","horários"],
        "website":   ["website","site","página web","url"],
        "preco":     ["preço","preço/pessoa","entrada","admissão","bilhete"],
        "latitude":  ["latitude","lat"],
        "longitude": ["longitude","lon","lng"],
    }
    for lbl_raw, val_raw in pares:
        lbl_norm = lbl_raw.lower().strip()
        matched = False
        for field, synonyms in _label_map.items():
            if any(s in lbl_norm for s in synonyms):
                if not row.get(field):
                    row[field] = val_raw
                matched = True
                break
        if not matched:
            key = "campo_" + re.sub(r"[^\w]", "_", lbl_raw.lower().strip("_"))[:40]
            if key not in row:
                row[key] = val_raw

    # Imagens de conteúdo
    imgs = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if any(x in src.lower() for x in ["/upload", "/media", "/photo", "/image",
                                            "/content", "/assets", "/files", "/img",
                                            "/fotos", "/galeria", "/gallery"]):
            full = urljoin(BASE_URL, src)
            if full not in imgs:
                imgs.append(full)
    row["imagens"] = " | ".join(imgs[:10])

    # Descrição longa (fallback do corpo da página)
    if not row.get("descricao"):
        for tag in soup.find_all(["p","div"],
                                  class_=re.compile(
                                      r"desc|content|body|text|intro|summary"
                                      r"|about|corpo|conteudo|article", re.I)):
            txt = tag.get_text(" ", strip=True)
            if len(txt) > 80:
                row["descricao"] = txt[:3000]
                break

    # Tags / categorias visíveis
    tags = []
    for el in soup.find_all(class_=re.compile(
            r"\btag\b|\bbadge\b|\bchip\b|\bcategory\b|\bcategoria\b", re.I)):
        t = el.get_text(" ", strip=True)
        if t and len(t) < 80:
            tags.append(t)
    row["tags"] = " | ".join(dict.fromkeys(tags))

    # Redes sociais
    sociais = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(s in href for s in ["facebook.com","instagram.com","twitter.com",
                                    "youtube.com","tiktok.com","linkedin.com",
                                    "x.com/","threads.net"]):
            if href not in sociais:
                sociais.append(href)
    row["redes_sociais"] = " | ".join(sociais)

    # Município (regex no texto)
    raw = soup.get_text(" ")
    for pat in [r"munic[íi]pio[:\s]+([A-ZÀ-Úa-zà-ú][^\n<.,]{2,40})",
                r"concelho[:\s]+([A-ZÀ-Úa-zà-ú][^\n<.,]{2,40})"]:
        m = re.search(pat, raw, re.I)
        if m and not row.get("municipio"):
            row["municipio"] = m.group(1).strip()

    return row


# ── Excel ─────────────────────────────────────────────────────────────────────

_COLS_PRIORITY = [
    "id", "nome", "h1", "secao", "categoria", "slug", "tipo",
    "descricao", "municipio", "morada", "localidade", "regiao", "pais",
    "latitude", "longitude", "telefone", "email", "website",
    "preco", "horario",
    "data_inicio", "data_fim", "local_evento",
    "data_publicacao", "data_modificacao", "keywords",
    "imagem_jsonld", "og_image", "og_tipo",
    "imagens", "tags", "redes_sociais",
    "profundidade", "url",
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
    print(f"    Sheets: Dados | Presença (X/vazio) | Resumo")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  douroetamega.pt — Crawler v2 (requests, duas fases)")
    print("=" * 60)

    # ── Fase 1: descoberta ────────────────────────────────────────────────────
    print("\n[Fase 1] A descobrir todos os URLs de items…\n")
    urls = discover_urls()

    if not urls:
        print("[Aviso] Nenhum URL descoberto. Verifica a ligação à internet.")
        return

    # ── Fase 2: extracção ─────────────────────────────────────────────────────
    total = len(urls)
    print(f"[Fase 2] A extrair dados de {total} items…\n")
    dados = []

    for i, url in enumerate(urls, 1):
        if i <= 10 or i % 50 == 0:
            slug = url.rstrip("/").split("/")[-1] or url.rstrip("/").split("/")[-2]
            print(f"  [{i:5}/{total}] {slug}")

        html = _get(url)
        if html:
            row = extract_page(url, html)
            dados.append(row)

        # Guarda parcialmente a cada 200 items
        if i % 200 == 0 and dados:
            save_excel(dados, OUTPUT.replace(".xlsx", f"_parcial_{i}.xlsx"))
            print(f"  [Parcial] {i} guardado")

        time.sleep(DELAY)

    save_excel(dados)


if __name__ == "__main__":
    main()
