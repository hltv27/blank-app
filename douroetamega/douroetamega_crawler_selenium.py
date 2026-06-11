#!/usr/bin/env python3
"""
Crawler — turismo.douroetamega.pt + aboboreira.douroetamega.pt  (Selenium)
O conteúdo turístico está em dois subdomínios:
  • turismo.douroetamega.pt  — POIs, alojamento, restaurantes, percursos, eventos
  • aboboreira.douroetamega.pt — Serra da Aboboreira (trilhos, megalíticos, fauna)

Instalar:
    pkg install chromium          ← instala chromium + chromedriver
    pip install selenium openpyxl beautifulsoup4

Correr:
    python douroetamega_crawler_selenium.py
"""

import json
import os
import re
import shutil
import time
from collections import Counter, deque
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException

# ── Domínios e configuração ───────────────────────────────────────────────────

TURISMO_URL    = "https://turismo.douroetamega.pt"
ABOBOREIRA_URL = "https://aboboreira.douroetamega.pt"
BASE_URL       = TURISMO_URL   # usado apenas como fallback em _norm

OUTPUT    = "douroetamega_dados.xlsx"
DELAY     = 0.8
MAX_PAGES = 20000

# Subdomínios aceites pelo crawler
_VALID_HOSTS = {
    "turismo.douroetamega.pt",
    "aboboreira.douroetamega.pt",
}

# Pontos de entrada: todas as categorias e sub-categorias conhecidas.
# O BFS segue os links a partir daqui para descobrir todos os items.
CATEGORIAS = [
    # ── turismo.douroetamega.pt ──────────────────────────────────────────
    TURISMO_URL + "/",
    TURISMO_URL + "/o-que-ver",
    TURISMO_URL + "/o-que-ver/patrimonio",
    TURISMO_URL + "/o-que-ver/postos-de-turismo",
    TURISMO_URL + "/o-que-ver/miradouros-e-vistas",
    TURISMO_URL + "/o-que-ver/espacos-verdes",
    TURISMO_URL + "/o-que-fazer",
    TURISMO_URL + "/o-que-fazer/cultura-e-arte",
    TURISMO_URL + "/o-que-fazer/museus",
    TURISMO_URL + "/o-que-fazer/artesanato",
    TURISMO_URL + "/o-que-fazer/comercializacao",
    TURISMO_URL + "/o-que-fazer/animacao-cultural-recreativa-e-de-lazer",
    TURISMO_URL + "/o-que-fazer/agentes-culturais",
    TURISMO_URL + "/o-que-fazer/congressos-e-exposicoes",
    TURISMO_URL + "/o-que-fazer/desporto-e-lazer",
    TURISMO_URL + "/o-que-fazer/empresas-de-animacao-turistica",
    TURISMO_URL + "/o-que-fazer/aldeias-de-portugal",
    TURISMO_URL + "/o-que-fazer/rota-do-romanico",
    TURISMO_URL + "/o-que-fazer/rotas-e-percursos",
    TURISMO_URL + "/o-que-fazer/rotas-e-percursos/percursos-pedestres",
    TURISMO_URL + "/o-que-fazer/rotas-e-percursos/btt",
    TURISMO_URL + "/o-que-fazer/rotas-e-percursos/roteiros-baixo-tamega",
    TURISMO_URL + "/o-que-fazer/rotas-e-percursos/outros-roteiros",
    TURISMO_URL + "/o-que-fazer/rotas-e-percursos/serra-da-aboboreira",
    TURISMO_URL + "/o-que-fazer/escapadinhas",
    TURISMO_URL + "/o-que-fazer/verde-sentido",
    TURISMO_URL + "/o-que-fazer/caves",
    TURISMO_URL + "/onde-dormir",
    TURISMO_URL + "/onde-dormir/turismo-rural",
    TURISMO_URL + "/onde-dormir/turismo-de-habitacao",
    TURISMO_URL + "/onde-dormir/alojamento-local",
    TURISMO_URL + "/onde-dormir/albergues-abrigos-e-pousadas",
    TURISMO_URL + "/onde-dormir/parques-de-campismo",
    TURISMO_URL + "/onde-dormir/hoteis",
    TURISMO_URL + "/onde-comer",
    TURISMO_URL + "/agenda",
    TURISMO_URL + "/agenda/eventos",
    TURISMO_URL + "/rss-feed",
    TURISMO_URL + "/pages/856",   # Aldeias de Portugal
    # ── aboboreira.douroetamega.pt ──────────────────────────────────────
    ABOBOREIRA_URL + "/",
    ABOBOREIRA_URL + "/serra-da-aboboreira",
    ABOBOREIRA_URL + "/rotas-e-percursos",
    ABOBOREIRA_URL + "/paisagem-protegida-regional",
    ABOBOREIRA_URL + "/galeria",
    ABOBOREIRA_URL + "/pages/1008",   # lista de percursos/POIs
]

# Extensões/paths a ignorar no BFS
_SKIP_EXT  = (".pdf",".jpg",".jpeg",".png",".gif",".svg",".webp",
              ".zip",".rar",".doc",".docx",".xls",".xlsx",
              ".mp3",".mp4",".avi",".mov",".woff",".woff2",".css",".js",".ico")
_SKIP_PATH = ("/wp-admin/","/wp-login","/feed/","/xmlrpc",
              "/cart/","/checkout/","/my-account/",
              "/admin/","/manager/","/cms/","/backend/",
              "/login","/logout","/register","/api/",
              "/search/","/tag/","/author/",
              "/ficha-tecnica","/acessibilidade","/contactos","/politica")

# Regex para reconhecer páginas de item (POI, percurso, evento, alojamento…)
_ITEM_RE = re.compile(
    r'/geo_artigo(?:-\d+)?/[^/\?]+|'   # /geo_artigo/slug  ou /geo_artigo-49/slug
    r'/percurso/[^/\?]+|'               # /percurso/slug
    r'/evento/[^/\?]+|'                 # /evento/slug
    r'[?&]geo_article_id=\d+'           # ?geo_article_id=1234
)


def _is_skip(url: str) -> bool:
    low = url.lower()
    return (any(low.endswith(e) for e in _SKIP_EXT) or
            any(p in low for p in _SKIP_PATH) or
            low.startswith(("mailto:", "tel:", "javascript:")) or
            "#" in low)


def _norm(url: str, base_for_relative: str = TURISMO_URL) -> str:
    """Normaliza URL preservando o subdomínio (turismo ou aboboreira).
    Preserva geo_article_id e page= nos query params.
    """
    try:
        p = urlparse(url.split("#")[0])
    except Exception:
        return ""
    if p.scheme not in ("", "http", "https"):
        return ""
    netloc = (p.netloc or "").lower()
    # URLs relativas: usa o domínio da página actual
    if not netloc:
        netloc = urlparse(base_for_relative).netloc.lower()
    # Aceita apenas os dois subdomínios conhecidos
    if netloc not in _VALID_HOSTS:
        return ""
    path = p.path or "/"
    last = path.split("/")[-1]
    # Rejeita paths com extensões de ficheiro
    if "." in last and not last.startswith("."):
        return ""
    if not path.endswith("/"):
        path += "/"
    # Preserva geo_article_id (páginas antigas) e page= (paginação)
    qs = ""
    if p.query:
        if "geo_article_id=" in p.query:
            # Preserva só o geo_article_id, ignora parâmetros de paginação extra
            m = re.search(r"geo_article_id=(\d+)", p.query)
            if m:
                qs = f"?geo_article_id={m.group(1)}"
        else:
            m = re.search(r"(?:page|p)=(\d+)", p.query)
            if m and int(m.group(1)) > 1:
                qs = f"?page={m.group(1)}"
    return f"https://{netloc}{path}{qs}"


def _is_item_page(url: str) -> bool:
    return bool(_ITEM_RE.search(url))


# ── Selenium ──────────────────────────────────────────────────────────────────

def _make_driver() -> webdriver.Chrome:
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
            "Instala com: pkg install chromium"
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


def _get_html_bfs(driver: webdriver.Chrome, url: str) -> str | None:
    """Versão para BFS: espera mais e faz scroll para activar lazy loading."""
    try:
        driver.get(url)
        time.sleep(2.5)
        # Scroll até ao fundo para activar lazy loading de items
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.5)
        # Segundo scroll para carregar mais items (se houver paginação por scroll)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.0)
        return driver.page_source
    except (TimeoutException, WebDriverException) as e:
        print(f"  [ERRO] {url}: {e}")
        return None


# ── FASE 1: BFS ───────────────────────────────────────────────────────────────

def discover_urls(driver: webdriver.Chrome) -> list[str]:
    """BFS a partir de todas as CATEGORIAS conhecidas (turismo + aboboreira).
    Segue links internos e identifica páginas de items pelo padrão geo_artigo/percurso.
    """
    queue: deque[str] = deque(CATEGORIAS)
    visited: set[str] = set()
    items:   set[str] = set()
    nav_count = 0

    print(f"  BFS a partir de {len(CATEGORIAS)} categorias ({TURISMO_URL} + {ABOBOREIRA_URL})")

    while queue and nav_count < MAX_PAGES:
        url  = queue.popleft()
        norm = _norm(url, base_for_relative=url)
        if not norm or norm in visited or _is_skip(norm):
            continue
        visited.add(norm)
        nav_count += 1

        if nav_count % 50 == 0 or nav_count <= 5:
            short = norm.replace(TURISMO_URL, "[T]").replace(ABOBOREIRA_URL, "[A]")
            print(f"  [BFS {nav_count:5}] {short[:70]}  |  items: {len(items)}")

        html = _get_html_bfs(driver, norm)
        if not html:
            continue

        if _is_item_page(norm):
            items.add(norm)

        soup = BeautifulSoup(html, "html.parser")

        new_links = 0
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or _is_skip(href):
                continue
            full  = urljoin(norm, href)
            norm2 = _norm(full, base_for_relative=norm)
            if norm2 and norm2 not in visited:
                queue.append(norm2)
                new_links += 1

        for el in soup.find_all(attrs={"data-href": True}):
            href = el["data-href"].strip()
            full  = urljoin(norm, href)
            norm2 = _norm(full, base_for_relative=norm)
            if norm2 and norm2 not in visited and not _is_skip(norm2):
                queue.append(norm2)
                new_links += 1

        # Debug: nas primeiras 10 páginas mostra quantos links internos encontrou
        if nav_count <= 10:
            item_links = [urljoin(norm, a["href"]) for a in soup.find_all("a", href=True)
                          if _is_item_page(a["href"])]
            print(f"    → {new_links} novos links | {len(item_links)} links de item")
            for lnk in item_links[:3]:
                print(f"       {lnk}")

    print(f"\n  BFS: {nav_count} páginas | {len(items)} items")
    return sorted(items)


# ── FASE 2: Extracção ─────────────────────────────────────────────────────────

def extract_page(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    parsed_url = urlparse(url)
    row: dict = {
        "url":     url,
        "dominio": parsed_url.netloc,
    }

    # Estrutura de path para secao/categoria/etc
    path_parts = [p for p in parsed_url.path.split("/") if p]
    # Identifica posição do geo_artigo/percurso/evento no path
    _item_markers = {"geo_artigo", "percurso", "evento"}
    marker_idx = next(
        (i for i, p in enumerate(path_parts) if p.startswith("geo_artigo") or p in _item_markers),
        len(path_parts)
    )
    row["secao"]        = path_parts[0] if path_parts else ""
    row["categoria"]    = path_parts[1] if len(path_parts) >= 2 else ""
    row["subcategoria"] = path_parts[2] if len(path_parts) >= 3 and marker_idx > 2 else ""
    last = path_parts[-1] if path_parts else ""
    row["slug"]         = last if not last.isdigit() else (path_parts[-2] if len(path_parts) >= 2 else "")
    row["id"]           = ""
    # Para geo_artigo-49/slug o número é o id da categoria, não do item
    # Para ?geo_article_id=N o N é o id do item
    qs = urlparse(url).query
    if qs:
        m = re.search(r"geo_article_id=(\d+)", qs)
        if m:
            row["id"] = m.group(1)
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
            # Campos de percurso/trail
            for src_key, dst_key in [
                ("distance","distancia"), ("length","distancia"),
                ("elevation","elevacao"), ("ascent","elevacao"),
                ("difficulty","dificuldade"),
                ("duration","duracao"), ("estimatedTime","duracao"),
            ]:
                if data.get(src_key) and not row.get(dst_key):
                    row[dst_key] = str(data[src_key])
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
        elif prop == "keywords":
            row["keywords"] = val

    # Título H1/H2
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

    # dl/dt/dd + tabelas — campos estruturados do CMS
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
    # Também procura pares label:valor em spans/divs do CMS
    for el in soup.find_all(class_=re.compile(r"field|label|info|detalhe|detail", re.I)):
        txt = el.get_text(" ", strip=True)
        if ":" in txt:
            parts = txt.split(":", 1)
            if len(parts) == 2 and parts[0] and parts[1]:
                pares.append((parts[0].strip(), parts[1].strip()))

    _label_map = {
        "municipio":     ["município","municipio","concelho"],
        "morada":        ["morada","endereço","address","localização"],
        "telefone":      ["telefone","telef","tel.","contacto telefónico"],
        "email":         ["e-mail","email","correio"],
        "horario":       ["horário","horario","horas","horários","schedule","funcionamento"],
        "website":       ["website","site","página web","página oficial"],
        "preco":         ["preço","preços","entrada","admissão","bilhete","custo"],
        "latitude":      ["latitude","lat"],
        "longitude":     ["longitude","lon","lng"],
        "distancia":     ["distância","distancia","distance","comprimento","length","extensão"],
        "elevacao":      ["elevação","elevacao","desnível","desnivel","altitude máx","cota máxima"],
        "dificuldade":   ["dificuldade","difficulty","nível de dificuldade","grau"],
        "duracao":       ["duração","duracao","duration","tempo estimado","tempo médio"],
        "acessos":       ["acesso","acessos","como chegar","chegada","transporte"],
        "classificacao": ["classificação","classificacao","tipo de percurso","tipologia"],
        "capacidade":    ["capacidade","lugares","camas","quartos"],
        "municipio":     ["município","municipio","concelho","localidade"],
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

    # Imagens — apenas do domínio douroetamega.pt
    _JUNK = ("googlelogo", "sunny.png", "weather", "spinner", "loading",
             "placeholder", "favicon", "maps.gstatic", "gstatic.com",
             "googleapis.com", "icon-", "/icons/", "/logo")
    imgs = []
    for img in soup.find_all("img", src=True):
        src = img["src"].strip()
        if not src:
            continue
        full = urljoin(BASE_URL, src)
        if "douroetamega.pt" not in full:
            continue
        if any(j in full.lower() for j in _JUNK):
            continue
        if full not in imgs:
            imgs.append(full)
    row["imagens"] = " | ".join(imgs[:20])

    # Descrição — evita apanhar texto de menus/nav
    if not row.get("descricao"):
        for tag in soup.find_all(["div","article","section"],
                                  class_=re.compile(
                                      r"desc|content|body|text|intro|summary"
                                      r"|about|corpo|conteudo|article|detail"
                                      r"|ficha|info|main|detalhe", re.I)):
            # Exclui containers de navegação
            cls = " ".join(tag.get("class", []))
            if re.search(r"nav|menu|sidebar|header|footer|bread", cls, re.I):
                continue
            txt = tag.get_text(" ", strip=True)
            if len(txt) > 120:
                row["descricao"] = txt[:3000]
                break
    if not row.get("descricao"):
        for tag in soup.find_all("p"):
            parent = tag.parent
            if parent and parent.name in ("nav", "header", "footer"):
                continue
            txt = tag.get_text(" ", strip=True)
            if len(txt) > 80:
                row["descricao"] = txt[:3000]
                break

    # Tags / badges
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

    # Regex no texto plano para campos de percurso/local
    raw_text = soup.get_text(" ")

    for pat in [r"munic[íi]pio[:\s]+([A-ZÀ-Úa-zà-ú][^\n.,;]{2,40})",
                r"concelho[:\s]+([A-ZÀ-Úa-zà-ú][^\n.,;]{2,40})"]:
        m = re.search(pat, raw_text, re.I)
        if m and not row.get("municipio"):
            row["municipio"] = m.group(1).strip()

    if not row.get("distancia"):
        m = re.search(r"(\d+(?:[.,]\d+)?\s*km)", raw_text, re.I)
        if m:
            row["distancia"] = m.group(1).strip()

    if not row.get("elevacao"):
        m = re.search(r"desnível\s*[:\s]+(\d+\s*m)", raw_text, re.I)
        if not m:
            m = re.search(r"(\d+)\s*m\s*(?:de\s+)?desnível", raw_text, re.I)
        if m:
            row["elevacao"] = m.group(1).strip() + " m"

    if not row.get("dificuldade"):
        m = re.search(r"dificuldade[:\s]+([^\n.,;]{3,30})", raw_text, re.I)
        if m:
            row["dificuldade"] = m.group(1).strip()

    if not row.get("duracao"):
        m = re.search(r"dura[çc][aã]o[:\s]+([\dhHmM: ]+)", raw_text, re.I)
        if not m:
            m = re.search(r"(\d+h\d*(?:min)?|\d+\s*hora[s]?)", raw_text, re.I)
        if m:
            row["duracao"] = m.group(1).strip()

    return row


# ── Excel ─────────────────────────────────────────────────────────────────────

_COLS_PRIORITY = [
    "id", "nome", "h1", "dominio", "secao", "categoria", "subcategoria", "slug", "tipo",
    "descricao", "municipio", "morada", "localidade", "regiao", "pais",
    "latitude", "longitude", "telefone", "email", "website",
    "preco", "horario", "capacidade",
    "distancia", "elevacao", "dificuldade", "duracao", "classificacao", "acessos",
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
    """Extracção com Selenium. Reinicia browser a cada batch para evitar OOM."""
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
                    slug = url.replace(BASE_URL, "").rstrip("/").split("/")[-1]
                    print(f"  [{i:5}/{total}] {slug[:60]}")

                html = _get_html(driver, url, wait=1.5)
                if html:
                    row = extract_page(url, html)
                    dados.append(row)

                if i % 200 == 0 and dados:
                    save_excel(dados, OUTPUT.replace(".xlsx", f"_parcial_{i}.xlsx"))
                    print(f"  [Parcial] guardados {i} items")

                time.sleep(DELAY)
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    return dados


def main():
    print("=" * 60)
    print("  douroetamega.pt — Crawler Selenium (turismo + aboboreira)")
    print("=" * 60)

    # ── Fase 1: BFS (ou reutiliza cache) ─────────────────────────────────────
    if os.path.exists(URLS_FILE):
        with open(URLS_FILE) as f:
            raw = [l.strip() for l in f if l.strip()]
        urls = [u for u in raw if not _is_skip(u) and _is_item_page(u)]
        skipped = len(raw) - len(urls)
        print(f"\n[Fase 1] {len(urls)} URLs de {URLS_FILE}"
              f"{f'  ({skipped} filtrados)' if skipped else ''}"
              f"  (apaga o ficheiro para re-fazer o BFS)\n")
    else:
        print(f"\n[Fase 1] BFS em {BASE_URL}…\n")
        driver = _make_driver()
        try:
            driver.get(BASE_URL + "/")
            time.sleep(2)
            print(f"[Session] {BASE_URL} OK\n")
        except Exception as e:
            print(f"[Session] Aviso: {e}\n")

        try:
            urls = discover_urls(driver)
        finally:
            driver.quit()

        if not urls:
            print("[Aviso] Nenhum URL descoberto. Verifica se o browser consegue aceder ao site.")
            return

        with open(URLS_FILE, "w") as f:
            f.write("\n".join(urls))
        print(f"  URLs guardados em {URLS_FILE}\n")

    # ── Fase 2: Extracção Selenium ────────────────────────────────────────────
    print(f"[Fase 2] A extrair dados de {len(urls)} items (batches de 50)…\n")
    dados = _phase2_selenium(urls, batch_size=50)
    save_excel(dados)

    # ── Fase 3: Download de fotos ─────────────────────────────────────────────
    try:
        from download_fotos import main as download_fotos_main
        print("\n[Fase 3] A descarregar fotos…")
        download_fotos_main()
    except Exception as e:
        print(f"\n[Fase 3] Fotos: {e}")
        print("  Podes descarregar as fotos manualmente: python download_fotos.py")


if __name__ == "__main__":
    main()
