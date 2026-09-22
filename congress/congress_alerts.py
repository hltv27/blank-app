#!/usr/bin/env python3
"""
Alertas de divulgacoes de trades do Congresso dos EUA.

Faz polling aos registos publicos da Camara e do Senado e manda Telegram
quando aparece uma Periodic Transaction Report (PTR) nova.

Fontes (publicas, gratuitas, sem chave de API):
  Camara  https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{ano}FD.zip
  Senado  https://efdsearch.senate.gov/search/  (precisa de aceitar o aviso legal)

O que isto NAO e': nao sabe de trades em tempo real. O STOCK Act da' 45 dias
para divulgar, por isso o que se apanha e' a SUBMISSAO do documento — que pode
referir-se a uma compra feita ha' mes e meio. Ninguem tem melhor do que isto:
a Unusual Whales, o Capitol Trades e o Quiver fazem polling aos mesmos sites.

Independente do claw_v8 — nao importa nada dele e nao lhe toca.

Uso:
  python3 congress_alerts.py --backfill   # 1a vez: marca o existente sem alertar
  python3 congress_alerts.py --once       # um ciclo e sai (para testar)
  python3 congress_alerts.py              # ciclo continuo
"""
import argparse
import io
import json
import os
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

import requests

# ─────────────────────────────────────────────
#  Configuracao
# ─────────────────────────────────────────────
POLL_MIN = 10                       # minutos entre ciclos
STATE_FILE = Path(__file__).parent / "seen.json"
TIMEOUT = 30

# Nomes a vigiar (apelido, minusculas). Vazio = alerta sobre todos.
WATCHLIST = []                      # ex: ["pelosi", "greene", "crenshaw"]

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

UA = {"User-Agent": "congress-alerts/1.0 (polling publico, 1 pedido/10min)"}

HOUSE_ZIP = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{ano}FD.zip"
HOUSE_PDF = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{ano}/{doc}.pdf"
SENATE_BASE = "https://efdsearch.senate.gov"


# ─────────────────────────────────────────────
#  Estado — que documentos ja' vimos
# ─────────────────────────────────────────────
def load_state() -> set:
    if not STATE_FILE.exists():
        return set()
    try:
        return set(json.loads(STATE_FILE.read_text()).get("vistos", []))
    except Exception as e:
        print(f"[AVISO] estado ilegivel ({e}) — a comecar do zero", file=sys.stderr)
        return set()


def save_state(vistos: set) -> None:
    # guarda os mais recentes; sem limite o ficheiro cresce para sempre
    STATE_FILE.write_text(json.dumps(
        {"vistos": sorted(vistos)[-20000:],
         "actualizado": datetime.now(timezone.utc).isoformat()},
        indent=2))


# ─────────────────────────────────────────────
#  Camara dos Representantes
# ─────────────────────────────────────────────
def fetch_house(ano: int) -> list:
    """O ZIP anual traz um XML com todas as submissoes do ano."""
    url = HOUSE_ZIP.format(ano=ano)
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        nome_xml = next((n for n in z.namelist() if n.lower().endswith(".xml")), None)
        if not nome_xml:
            raise RuntimeError("ZIP da Camara sem XML la' dentro")
        raiz = ElementTree.fromstring(z.read(nome_xml))

    out = []
    for m in raiz.findall(".//Member"):
        def campo(tag):
            el = m.find(tag)
            return (el.text or "").strip() if el is not None else ""

        # FilingType 'P' = Periodic Transaction Report. Os outros sao
        # declaracoes anuais, extensoes, etc. — nao interessam aqui.
        if campo("FilingType") != "P":
            continue
        doc = campo("DocID")
        if not doc:
            continue
        out.append({
            "camara": "House",
            "id": f"H{doc}",
            "nome": f"{campo('First')} {campo('Last')}".strip(),
            "apelido": campo("Last").lower(),
            "estado": campo("StateDst"),
            "data": campo("FilingDate"),
            "url": HOUSE_PDF.format(ano=ano, doc=doc),
        })
    return out


# ─────────────────────────────────────────────
#  Senado
# ─────────────────────────────────────────────
def fetch_senate(ano: int) -> list:
    """
    O Senado exige aceitar um aviso legal antes de pesquisar: GET para obter
    o csrftoken, POST a aceitar, e so' depois a pesquisa. E' fragil por
    natureza — se eles mudarem o formulario, isto parte. Por isso o chamador
    trata a excepcao e continua com a Camara.
    """
    s = requests.Session()
    s.headers.update(UA)

    home = f"{SENATE_BASE}/search/home/"
    s.get(home, timeout=TIMEOUT).raise_for_status()
    csrf = s.cookies.get("csrftoken")
    if not csrf:
        raise RuntimeError("Senado: sem csrftoken")

    s.post(home, timeout=TIMEOUT,
           headers={"Referer": home},
           data={"prohibition_agreement": "1", "csrfmiddlewaretoken": csrf}
           ).raise_for_status()

    csrf = s.cookies.get("csrftoken", csrf)
    r = s.post(f"{SENATE_BASE}/search/report/data/", timeout=TIMEOUT,
               headers={"Referer": f"{SENATE_BASE}/search/",
                        "X-Requested-With": "XMLHttpRequest"},
               data={
                   "start": "0", "length": "100",
                   "report_types": "[11]",          # Periodic Transaction Report
                   "filer_types": "[]",
                   "submitted_start_date": f"01/01/{ano} 00:00:00",
                   "submitted_end_date": "",
                   "candidate_state": "", "senator_state": "",
                   "office_id": "", "first_name": "", "last_name": "",
                   "csrfmiddlewaretoken": csrf,
               })
    r.raise_for_status()
    linhas = r.json().get("data", [])

    out = []
    for linha in linhas:
        # [primeiro, ultimo, orgao, link_html, data]
        if len(linha) < 5:
            continue
        primeiro, ultimo, _org, link_html, data = linha[:5]
        m = re.search(r'href="([^"]+)"', link_html or "")
        if not m:
            continue
        caminho = m.group(1)
        doc = caminho.rstrip("/").split("/")[-1]
        out.append({
            "camara": "Senate",
            "id": f"S{doc}",
            "nome": f"{_limpa(primeiro)} {_limpa(ultimo)}".strip(),
            "apelido": _limpa(ultimo).lower(),
            "estado": "",
            "data": data,
            "url": SENATE_BASE + caminho,
        })
    return out


def _limpa(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html or "").strip()


# ─────────────────────────────────────────────
#  Telegram
# ─────────────────────────────────────────────
def telegram(texto: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[sem Telegram configurado]\n{texto}\n")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            timeout=TIMEOUT,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": texto,
                  "parse_mode": "HTML", "disable_web_page_preview": "false"})
        if r.status_code != 200:
            print(f"[ERRO] Telegram {r.status_code}: {r.text[:200]}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"[ERRO] Telegram: {e}", file=sys.stderr)
        return False


def formata(f: dict) -> str:
    icone = "🏛" if f["camara"] == "House" else "🏦"
    estado = f" ({f['estado']})" if f["estado"] else ""
    return (f"{icone} <b>{f['nome']}</b>{estado}\n"
            f"PTR submetida — {f['data']}\n"
            f"<a href=\"{f['url']}\">ver documento</a>\n\n"
            f"<i>O trade pode ter ate' 45 dias.</i>")


# ─────────────────────────────────────────────
#  Ciclo
# ─────────────────────────────────────────────
def ciclo(vistos: set, backfill: bool) -> set:
    ano = datetime.now(timezone.utc).year
    filings = []

    for nome, fn in (("Camara", fetch_house), ("Senado", fetch_senate)):
        try:
            lote = fn(ano)
            filings += lote
            print(f"  {nome}: {len(lote)} PTRs")
        except Exception as e:
            # uma fonte em baixo nao pode matar a outra
            print(f"  {nome}: falhou — {e}", file=sys.stderr)

    novos = [f for f in filings if f["id"] not in vistos]
    if WATCHLIST:
        novos = [f for f in novos if f["apelido"] in WATCHLIST]

    if backfill:
        print(f"  backfill: {len(filings)} marcados, 0 alertas")
        return vistos | {f["id"] for f in filings}

    for f in sorted(novos, key=lambda x: x["nome"]):
        print(f"  NOVO: {f['camara']} {f['nome']} {f['data']}")
        telegram(formata(f))
        time.sleep(1)                      # cortesia com a API do Telegram

    if not novos:
        print("  sem novidades")
    return vistos | {f["id"] for f in filings}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="um ciclo e sai")
    ap.add_argument("--backfill", action="store_true",
                    help="marca o que ja' existe sem alertar (correr na 1a vez)")
    ap.add_argument("--interval", type=int, default=POLL_MIN,
                    help=f"minutos entre ciclos (default {POLL_MIN})")
    args = ap.parse_args()

    print(f"Alertas do Congresso — polling a cada {args.interval} min")
    print(f"Watchlist: {', '.join(WATCHLIST) if WATCHLIST else 'todos'}")
    print(f"Telegram: {'configurado' if TELEGRAM_TOKEN else 'NAO configurado'}\n")

    vistos = load_state()
    print(f"Estado: {len(vistos)} documentos ja' conhecidos\n")

    while True:
        print(f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC]")
        try:
            vistos = ciclo(vistos, args.backfill)
            save_state(vistos)
        except Exception as e:
            print(f"[ERRO] ciclo: {e}", file=sys.stderr)

        if args.once or args.backfill:
            return 0
        time.sleep(args.interval * 60)


if __name__ == "__main__":
    sys.exit(main())
