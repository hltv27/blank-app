"""
Claw Agent v8.0 — Registo "sombra" do Kronos
Guarda, por cada sinal avaliado, o que o Kronos previu e o que o seu bónus de
score fez à decisão. NÃO altera score, filtros nem ordens: só escreve num
ficheiro (kronos_log.jsonl) para depois isolar o efeito do Kronos nos trades em
papel (ver kronos_report.py).

Dois tipos de linha:
  "sinal"   — uma por sinal avaliado (antes dos filtros de entrada)
  "entrada" — uma por tentativa de abrir trade (imediatamente antes de abrir_trade)

Qualquer erro aqui é engolido: o registo nunca pode partir o loop do bot.
"""
import json
import os
import re
import threading
import time

_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(_DIR, "kronos_log.jsonl")

# Janela máxima entre a tentativa de entrada registada e a abertura do trade em papel.
JANELA_ENTRADA_S = 300
# Janela máxima entre o sinal e a tentativa de entrada (mesma iteração do scan).
JANELA_SINAL_S = 900

_lock = threading.Lock()

# Formato produzido por kronos_signal.kronos_score: "KRONOS LONG +0.35%"
_RE_PREVISAO = re.compile(r"^KRONOS (LONG|SHORT|NEUTRAL) ([+-]?\d+(?:\.\d+)?)%$")


def interpretar(detalhe: str) -> dict:
    """Extrai (previsão, variação %) do texto devolvido por kronos_score.
    Se não houve previsão (OFF, cooldown, erro...), devolve o motivo."""
    m = _RE_PREVISAO.match(detalhe or "")
    if m:
        return {"previsao": m.group(1), "pct": float(m.group(2)), "motivo": None}
    return {"previsao": None, "pct": None, "motivo": detalhe or "SEM_DETALHE"}


def _decisivo(score_base: int, score_final: int, min_score: int) -> str | None:
    """O bónus/penalidade do Kronos mudou o resultado do teste ao score mínimo?"""
    if score_base < min_score <= score_final:
        return "ABRIU_POR_BONUS"
    if score_final < min_score <= score_base:
        return "BLOQUEADO_POR_PENALIDADE"
    return None


def _escrever(rec: dict):
    try:
        with _lock, open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception as e:  # nunca partir o loop principal
        print(f"[KRONOS_LOG] Falha a escrever: {e}")


def registar_sinal(symbol: str, direction: str, score_base: int, k_bonus: int,
                   k_detail: str, score_final: int, min_score: int):
    try:
        rec = {
            "evento": "sinal", "ts": int(time.time()), "symbol": symbol,
            "direcao": direction, "score_base": score_base, "k_bonus": k_bonus,
            "score_final": score_final, "min_score": min_score,
            "decisivo": _decisivo(score_base, score_final, min_score),
        }
        rec.update(interpretar(k_detail))
        _escrever(rec)
    except Exception as e:
        print(f"[KRONOS_LOG] Falha a registar sinal {symbol}: {e}")


def registar_entrada(symbol: str, direction: str):
    try:
        _escrever({"evento": "entrada", "ts": int(time.time()),
                   "symbol": symbol, "direcao": direction})
    except Exception as e:
        print(f"[KRONOS_LOG] Falha a registar entrada {symbol}: {e}")


def ler_log() -> list[dict]:
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            out = []
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    out.append(json.loads(linha))
                except json.JSONDecodeError:
                    continue  # linha truncada (ex: corte a meio de uma escrita)
            return out
    except FileNotFoundError:
        return []


def associar(trades: list[dict], log: list[dict]) -> list[tuple[dict, dict | None]]:
    """Liga cada trade fechado em papel ao registo de sinal do Kronos que o originou.

    Trade → última "entrada" do mesmo símbolo/lado com ts <= aberta_ts (<= JANELA_ENTRADA_S)
          → último "sinal" do mesmo símbolo/direção com ts <= entrada.ts (<= JANELA_SINAL_S).
    Sem correspondência (ex: trades anteriores a este registo) → None.
    """
    entradas = [r for r in log if r.get("evento") == "entrada"]
    sinais = [r for r in log if r.get("evento") == "sinal"]
    usadas = set()
    por_posicao = {}  # (symbol, lado, aberta_ts) -> sinal | None
    # Várias linhas de paper_trades.jsonl com o mesmo aberta_ts são fechos parciais
    # da MESMA posição: partilham o mesmo sinal e consomem uma só tentativa de entrada.
    for chave in sorted({(t["symbol"], t["lado"], t["aberta_ts"]) for t in trades},
                        key=lambda k: k[2]):
        sym, lado, aberta = chave
        cand = [(i, e) for i, e in enumerate(entradas)
                if i not in usadas and e["symbol"] == sym and e["direcao"] == lado
                and 0 <= aberta - e["ts"] <= JANELA_ENTRADA_S]
        if not cand:
            por_posicao[chave] = None
            continue
        i, ent = max(cand, key=lambda ie: ie[1]["ts"])
        usadas.add(i)
        sc = [s for s in sinais if s["symbol"] == sym and s["direcao"] == lado
              and 0 <= ent["ts"] - s["ts"] <= JANELA_SINAL_S]
        por_posicao[chave] = max(sc, key=lambda s: s["ts"]) if sc else None
    return [(t, por_posicao[(t["symbol"], t["lado"], t["aberta_ts"])])
            for t in sorted(trades, key=lambda x: x["aberta_ts"])]
