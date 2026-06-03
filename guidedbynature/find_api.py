#!/usr/bin/env python3
"""
Diagnóstico — encontra a API do guidedbynature.pt
Corre: python find_api.py
"""

try:
    import cloudscraper
    session = cloudscraper.create_scraper()
except ImportError:
    import requests as _r
    session = _r.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9",
})

from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re, json, time

BASE = "https://guidedbynature.pt"

# Categorias conhecidas com muitos items
TEST_CATS = [
    "/pt/poi/onde-dormir/",
    "/pt/poi/onde-comer/",
    "/pt/poi/praias-ou-piscinas/",
    "/pt/poi/paisagens/",
    "/pt/poi/historia-e-cultura/",
    "/pt/poi/",
]

def get(url, accept=None):
    h = {"Accept": accept} if accept else {}
    try:
        r = session.get(url, timeout=25, headers=h)
        if r.ok:
            return r
    except Exception as e:
        print(f"  ERRO {url}: {e}")
    return None

print("=" * 60)
print("  Diagnóstico API — guidedbynature.pt")
print("=" * 60)

# ── 1. Analisar HTML de categoria ─────────────────────────────────────────────
print("\n[1] A analisar páginas de categoria...")
for cat_path in TEST_CATS:
    r = get(BASE + cat_path)
    if not r:
        continue
    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    # Contar links de items
    item_links = re.findall(r'/pt/(poi|event|tour|p)/[^"\'<>\s]+/\d+', html)
    print(f"\n  {cat_path}")
    print(f"  → {len(set(item_links))} links de items no HTML estático")

    # Guardar HTML desta categoria para análise
    with open("debug_cat.html", "w", encoding="utf-8") as f:
        f.write(html)

    # Procurar fetch/axios/XHR no HTML inline
    inline_apis = set()
    for script in soup.find_all("script"):
        text = script.string or ""
        for m in re.finditer(r'''(?:fetch|axios\.(?:get|post)|XMLHttpRequest)[^'"]*['"]([^'"]{5,100})['"]''', text):
            u = m.group(1)
            if u.startswith("/") or "http" in u:
                inline_apis.add(u)
    if inline_apis:
        print(f"  → APIs em scripts inline: {inline_apis}")

    # Procurar __NEXT_DATA__ ou window.__STATE__ (React/Next.js)
    for pat in [r'__NEXT_DATA__\s*=\s*({.+?})\s*</script>',
                r'window\.__(?:STATE|DATA|INITIAL_STATE)__\s*=\s*({.+?});?\s*</script>',
                r'window\.__nuxt__\s*=\s*(.+?);?\s*</script>']:
        m = re.search(pat, html, re.DOTALL)
        if m:
            print(f"  → Dados embutidos encontrados ({pat[:30]}...)!")
            try:
                data = json.loads(m.group(1))
                with open("debug_state.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"    Guardado em debug_state.json")
            except Exception as e:
                print(f"    (erro a parsear JSON: {e})")

    break  # analisar só a primeira categoria disponível

# ── 2. Analisar ficheiros JS ──────────────────────────────────────────────────
print("\n[2] A analisar ficheiros JS do bundle...")
r = get(BASE + "/pt/")
if r:
    soup = BeautifulSoup(r.text, "html.parser")
    js_files = [
        urljoin(BASE, s["src"])
        for s in soup.find_all("script", src=True)
    ]
    print(f"  {len(js_files)} ficheiros JS encontrados")

    api_candidates = set()
    for js_url in js_files:
        js_r = get(js_url)
        if not js_r:
            continue
        js = js_r.text
        # URLs de API
        for m in re.finditer(r'''['"`](/(?:api|rest|graphql|_next/data)[^'"`\s]{2,80})['"`]''', js):
            api_candidates.add(BASE + m.group(1))
        # fetch/axios
        for m in re.finditer(r'''(?:fetch|axios\.(?:get|post))\s*\(\s*['"`]([^'"`\s]{5,100})['"`]''', js):
            u = m.group(1)
            api_candidates.add(u if u.startswith("http") else BASE + u)
        time.sleep(0.3)

    print(f"  {len(api_candidates)} endpoints candidatos:")
    for u in sorted(api_candidates)[:30]:
        print(f"    {u}")

    # Guardar todos
    if api_candidates:
        with open("debug_api_candidates.txt", "w") as f:
            f.write("\n".join(sorted(api_candidates)))
        print(f"\n  Lista completa em debug_api_candidates.txt")

# ── 3. Tentar endpoints directamente ─────────────────────────────────────────
print("\n[3] A testar endpoints directos...")
test_urls = [
    "/api/v1/poi/",
    "/api/v1/pois/",
    "/api/poi/",
    "/api/v1/places/",
    "/api/v1/locations/",
    "/api/v1/content/",
    "/api/v1/items/",
    "/api/v2/poi/",
    "/api/v2/pois/",
    "/graphql",
    "/_next/data/",
    "/api/search/",
    "/pt/api/poi/",
    "/api/v1/category/",
    "/api/v1/tags/",
    "/api/",
    "/rest/",
    "/rest/v1/",
]
for path in test_urls:
    r = get(BASE + path, accept="application/json")
    if r and r.status_code == 200:
        ct = r.headers.get("content-type", "")
        snippet = r.text[:200].replace("\n", " ")
        print(f"  ✓ {path}  [{r.status_code}] {ct[:40]}")
        print(f"    {snippet}")
        try:
            data = r.json()
            print(f"    JSON keys: {list(data.keys())[:10] if isinstance(data, dict) else f'lista com {len(data)} items'}")
        except Exception:
            pass
    time.sleep(0.2)

print("\n[4] Página de categoria guardada em debug_cat.html")
print("    Partilha esse ficheiro se precisares de mais ajuda.\n")
