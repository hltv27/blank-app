#!/usr/bin/env python3
"""
Crawler — douroetamega.pt  (Selenium + Chromium)
Funciona em ARM 32-bit / Termux onde Playwright não instala.

Instalar:
    pkg install chromium          ← instala chromium + chromedriver
    pip install selenium openpyxl beautifulsoup4

Correr:
    python douroetamega_crawler_selenium.py

Saída: douroetamega_dados.xlsx  (Dados | Presença | Resumo)
"""

import json
import re
import time
from collections import Counter, deque
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

BASE_URL  = "https://www.douroetamega.pt"
OUTPUT    = "douroetamega_dados.xlsx"
DELAY     = 0.8    # segundos entre páginas
MAX_PAGES = 15000  # limite de segurança

_SKIP_EXT  = (".pdf",".jpg",".jpeg",".png",".gif",".svg",".webp",
              ".zip",".rar",".doc",".docx",".xls",".xlsx",
              ".mp3",".mp4",".avi",".mov",".woff",".woff2",".css",".js",".ico")
_SKIP_PATH = ("/wp-admin/","/wp-login","/feed/","/xmlrpc",
              "/cart/","/checkout/","/my-account/")


def _is_skip(url: str) -> bool:
    low = url.lower()
    return (any(low.endswith(e) for e in _SKIP_EXT) or
            any(p in low for p in _SKIP_PATH) or
            low.startswith(("mailto:","tel:","javascript:")) or
            "#" in low)


def _norm(url: str) -> str:
    try:
        p = urlparse(url.split("#")[0])
    except Exception:
        return ""
    if p.scheme not in ("", "http", "https"):
        return ""
    netloc = (p.netloc or "").replace("www.", "")
    if netloc and netloc != "douroetamega.pt":
        return ""
    path = p.path or "/"
    last = path.split("/")[-1]
    if "." in last and not last.startswith("."):
        return ""
    if not path.endswith("/"):
        path += "/"
    qs = ""
    if p.query:
        m = re.search(r"(?:page|p)=(\d+)", p.query)
        if m and int(m.group(1)) > 1:
            qs = f"?{p.query}"
    return f"{BASE_URL}{path}{qs}"


def _is_content_page(url: str) -> bool:
    path  = urlparse(url).path
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        return False
    return any(p.isdigit() or len(p) >= 5 for p in parts)


def _make_driver() -> webdriver.Chrome:
    import os, shutil

    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")
    opts.add_argument("--lang=pt-PT")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )

    # Localizar binário do chromium
    chromium_candidates = [
        "/data/data/com.termux/files/usr/bin/chromium-browser",
        "/data/data/com.termux/files/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        shutil.which("chromium-browser") or "",
        shutil.which("chromium") or "",
    ]
    chromium_bin = next((p for p in chromium_candidates if p and os.path.exists(p)), None)
    if chromium_bin:
        opts.binary_location = chromium_bin
        print(f"[Browser] Chromium: {chromium_bin}")

    # Localizar chromedriver — OBRIGATÓRIO em Android/aarch64
    # (selenium-manager não suporta esta plataforma)
    driver_candidates = [
        "/data/data/com.termux/files/usr/bin/chromedriver",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        shutil.which("chromedriver") or "",
    ]
    driver_bin = next((p for p in driver_candidates if p and os.path.exists(p)), None)
    if not driver_bin:
        raise RuntimeError(
            "chromedriver não encontrado.\n"
            "Instala com: pkg install chromium\n"
            "(o chromedriver vem incluído no mesmo pacote)"
        )
    print(f"[Browser] chromedriver: {driver_bin}")

    svc = Service(executable_path=driver_bin)
    return webdriver.Chrome(service=svc, options=opts)


def _get_html(driver: webdriver.Chrome, url: str, wait: float = 1.5) -> str | None:
    try:
        driver.get(url)
        time.sleep(wait)
        return driver.page_source
    except (TimeoutException, WebDriverException) as e:
        print(f"  [ERRO] {url}: {e}")
        return None


# ── FASE 1: BFS com browser real ─────────────────────────────────────────────

def discover_urls(driver: webdriver.Chrome) -> list[str]:
    """
    BFS: browser executa JavaScript → links de items aparecem no DOM.
    """
    queue   = deque([BASE_URL + "/"])
    visited: set[str] = set()
    content: set[str] = set()
    nav_count = 0

    print(f"  BFS a partir de {BASE_URL}")

    while queue and nav_count < MAX_PAGES:
        url  = queue.popleft()
        norm = _norm(url)
        if not norm or norm in visited or _is_skip(norm):
            continue
        visited.add(norm)
        nav_count += 1

        if nav_count % 50 == 0 or nav_count <= 5:
            print(f"  [BFS {nav_count:5}] {norm.replace(BASE_URL,'')}  |  items: {len(content)}")

        html = _get_html(driver, norm, wait=1.2)
        if not html:
            continue

        if _is_content_page(norm):
            content.add(norm)

        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or _is_skip(href):
                continue
            full  = urljoin(norm, href)
            norm2 = _norm(full)
            if norm2 and norm2 not in visited:
                queue.append(norm2)

        time.sleep(DELAY)

    print(f"\n  BFS: {nav_count} páginas | {len(content)} items")
    return sorted(content)


# ── FASE 2: Extracção ─────────────────────────────────────────────────────────

def extract_page(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    row: dict = {"url": url}

    path_parts = [p for p in urlparse(url).path.split("/") if p]
    last = path_parts[-1] if path_parts else ""
    row["id"]           = last if last.isdigit() else ""
    row["slug"]         = last if not last.isdigit() else (path_parts[-2] if len(path_parts) >= 2 else "")
    row["secao"]        = path_parts[0] if path_parts else ""
    row["categoria"]    = path_parts[1] if len(path_parts) >= 2 else ""
    row["subcategoria"] = path_parts[2] if len(path_parts) >= 3 else ""
    row["profundidade"] = str(len(path_parts))

    # JSON-LD
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

    # Open Graph / meta
    for tag in soup.find_all("meta"):
        prop = tag.get("property") or tag.get("name") or ""
        val  = (tag.get("content") or "").strip()
        if not val:
            continue
        if prop == "og:title" and not row.get("nome"):
            row["nome"] = val
        elif prop in ("og:description","description") and not row.get("descricao"):
            row["descricao"] = val
        elif prop == "og:image":
            row["og_image"] = val
        elif prop == "og:type":
            row["og_tipo"] = val
        elif prop == "article:published_time":
            row["data_publicacao"] = val
        elif prop == "article:modified_time":
            row["data_modificacao"] = val
        elif prop == "keywords":
            row["keywords"] = val

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
        row["nome"] = title.get_text(strip=True).split("|")[0].split("–")[0].strip()

    # dl/dt/dd + tabelas + campos
    pares: list[tuple] = []
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

    _label_map = {
        "municipio": ["município","municipio","concelho"],
        "morada":    ["morada","endereço","address","localização"],
        "telefone":  ["telefone","telef","tel ","contacto"],
        "email":     ["e-mail","email","correio"],
        "horario":   ["horário","horario","horas"],
        "website":   ["website","site","página web"],
        "preco":     ["preço","entrada","admissão","bilhete"],
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

    imgs = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if any(x in src.lower() for x in ["/upload","/media","/photo","/image",
                                            "/content","/assets","/files","/img",
                                            "/fotos","/galeria","/gallery"]):
            full = urljoin(BASE_URL, src)
            if full not in imgs:
                imgs.append(full)
    row["imagens"] = " | ".join(imgs[:10])

    if not row.get("descricao"):
        for tag in soup.find_all(["p","div"],
                                  class_=re.compile(
                                      r"desc|content|body|text|intro|summary"
                                      r"|about|corpo|conteudo|article", re.I)):
            txt = tag.get_text(" ", strip=True)
            if len(txt) > 80:
                row["descricao"] = txt[:3000]
                break

    tags = []
    for el in soup.find_all(class_=re.compile(
            r"\btag\b|\bbadge\b|\bchip\b|\bcategory\b|\bcategoria\b", re.I)):
        t = el.get_text(" ", strip=True)
        if t and len(t) < 80:
            tags.append(t)
    row["tags"] = " | ".join(dict.fromkeys(tags))

    sociais = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(s in href for s in ["facebook.com","instagram.com","twitter.com",
                                    "youtube.com","tiktok.com","linkedin.com",
                                    "x.com/","threads.net"]):
            if href not in sociais:
                sociais.append(href)
    row["redes_sociais"] = " | ".join(sociais)

    raw_text = soup.get_text(" ")
    for pat in [r"munic[íi]pio[:\s]+([A-ZÀ-Úa-zà-ú][^\n<.,]{2,40})",
                r"concelho[:\s]+([A-ZÀ-Úa-zà-ú][^\n<.,]{2,40})"]:
        m = re.search(pat, raw_text, re.I)
        if m and not row.get("municipio"):
            row["municipio"] = m.group(1).strip()

    return row


# ── Excel ─────────────────────────────────────────────────────────────────────

_COLS_PRIORITY = [
    "id", "nome", "h1", "secao", "categoria", "subcategoria", "slug", "tipo",
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
        (str(r.get("secao","")), str(r.get("categoria",""))) for r in dados
    )
    for (s, c), n in sorted(counter.items()):
        ws3.append([s, c, n])
    for i in range(1, 4):
        ws3.column_dimensions[get_column_letter(i)].width = 28
    wb.save(output)
    print(f"\n✅  {output}  —  {len(dados)} linhas × {len(headers)} colunas")
    print(f"    Sheets: Dados | Presença (X/vazio) | Resumo")


# ── Main ──────────────────────────────────────────────────────────────────────

URLS_FILE = "douroetamega_urls.txt"


def _phase2_selenium(urls: list[str], batch_size: int = 50) -> list[dict]:
    """
    Fase 2 com Selenium — executa JS para obter conteúdo completo.
    Reinicia o browser a cada batch_size páginas para evitar crashes de RAM.
    """
    total = len(urls)
    dados = []

    for batch_start in range(0, total, batch_size):
        batch = urls[batch_start:batch_start + batch_size]
        print(f"\n  [Batch] {batch_start+1}–{batch_start+len(batch)} de {total} — a iniciar browser…")

        driver = _make_driver()
        try:
            for j, url in enumerate(batch, 1):
                i = batch_start + j
                if i <= 10 or i % 50 == 0:
                    slug = url.rstrip("/").split("/")[-1] or url.rstrip("/").split("/")[-2]
                    print(f"  [{i:5}/{total}] {slug}")

                html = _get_html(driver, url, wait=1.2)
                if html:
                    row = extract_page(url, html)
                    dados.append(row)

                if i % 200 == 0 and dados:
                    save_excel(dados, OUTPUT.replace(".xlsx", f"_parcial_{i}.xlsx"))
                    print(f"  [Parcial] {i} items guardados")

                time.sleep(DELAY)
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    return dados


def main():
    import os
    print("=" * 60)
    print("  douroetamega.pt — Crawler (Selenium BFS + requests extracção)")
    print("=" * 60)

    # ── Fase 1: BFS com browser (ou reutiliza URLs guardados) ────────────────
    if os.path.exists(URLS_FILE):
        with open(URLS_FILE) as f:
            urls = [l.strip() for l in f if l.strip()]
        print(f"\n[Fase 1] Reutilizando {len(urls)} URLs de {URLS_FILE} (apaga o ficheiro para re-fazer o BFS)\n")
    else:
        print("\n[Browser] A iniciar Chromium para BFS…")
        driver = _make_driver()
        try:
            driver.get(BASE_URL + "/")
            time.sleep(2)
            print(f"[Session] {BASE_URL} acessível\n")
        except Exception as e:
            print(f"[Session] Aviso: {e}\n")

        print("[Fase 1] BFS — a descobrir todos os URLs…\n")
        try:
            urls = discover_urls(driver)
        finally:
            driver.quit()

        if not urls:
            print("[Aviso] Nenhum URL descoberto.")
            return

        # Guarda URLs para não repetir o BFS se interrompido
        with open(URLS_FILE, "w") as f:
            f.write("\n".join(urls))
        print(f"  URLs guardados em {URLS_FILE}\n")

    # ── Fase 2: Extracção com Selenium em batches de 50 ─────────────────────
    # Reinicia o browser a cada 50 páginas para libertar RAM e evitar crashes
    print(f"[Fase 2] A extrair dados de {len(urls)} items (Selenium, batches de 50)…\n")
    dados = _phase2_selenium(urls, batch_size=50)
    save_excel(dados)


if __name__ == "__main__":
    main()
