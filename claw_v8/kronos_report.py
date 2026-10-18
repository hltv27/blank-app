"""
Efeito do Kronos nos trades em papel — corre manualmente no VPS:
    cd /root/blank-app/claw_v8 && python3 kronos_report.py
Cruza paper_trades.jsonl (resultados) com kronos_log.jsonl (previsões) e compara o
líquido por trade conforme o Kronos concordou, discordou ou não tinha opinião.
Só usa a biblioteca padrão — não carrega o modelo.

Limitação estrutural: os sinais que a penalidade (−1) bloqueou não geram trade, por
isso o seu resultado nunca existe. Só se mede o efeito nos trades que abriram.
"""
from collections import Counter

import kronos_log
from paper import ler_trades

MIN_AMOSTRA = 30  # abaixo disto, o t-stat entre grupos não diz nada


def _stats(liquidos: list[float]) -> dict:
    n = len(liquidos)
    if n == 0:
        return {"n": 0, "soma": 0.0, "media": 0.0, "wr": 0.0, "var": 0.0}
    media = sum(liquidos) / n
    var = sum((x - media) ** 2 for x in liquidos) / (n - 1) if n >= 2 else 0.0
    return {"n": n, "soma": sum(liquidos), "media": media,
            "wr": sum(1 for x in liquidos if x > 0) / n * 100, "var": var}


def _welch(a: dict, b: dict) -> float | None:
    """t de Welch para a diferença de médias a−b; None se não for calculável."""
    if a["n"] < 2 or b["n"] < 2:
        return None
    se2 = a["var"] / a["n"] + b["var"] / b["n"]
    return (a["media"] - b["media"]) / se2 ** 0.5 if se2 > 0 else None


def _linha(nome: str, s: dict) -> str:
    if s["n"] == 0:
        return f"  {nome:<34}    0 trades"
    return (f"  {nome:<34}{s['n']:>5} trades  líquido {s['soma']:+8.2f}  "
            f"{s['media']:+.3f}/trade  WR {s['wr']:.0f}%")


def _grupo(rec: dict | None) -> str:
    if rec is None:
        return "sem_registo"
    if rec["k_bonus"] > 0:
        return "concordou"
    if rec["k_bonus"] < 0:
        return "discordou"
    return "neutro" if rec["previsao"] == "NEUTRAL" else "sem_previsao"


def main():
    trades = ler_trades()
    log = kronos_log.ler_log()
    sinais = [r for r in log if r.get("evento") == "sinal"]

    print(f"Trades em papel: {len(trades)} | sinais registados: {len(sinais)}")
    if not sinais:
        print("kronos_log.jsonl ainda não tem sinais — o registo só começa depois do deploy.")
        return

    c = Counter(_grupo(r) for r in sinais)
    dec = Counter(r["decisivo"] for r in sinais if r["decisivo"])
    print("\nSinais avaliados (inclui os que não abriram trade):")
    print(f"  Kronos concordou {c['concordou']} | discordou {c['discordou']} | "
          f"neutro {c['neutro']} | sem previsão {c['sem_previsao']}")
    print(f"  Bónus decisivo (abriu só por causa dele): {dec['ABRIU_POR_BONUS']}")
    print(f"  Penalidade decisiva (bloqueou um sinal que passava): {dec['BLOQUEADO_POR_PENALIDADE']}"
          f"  ← resultado desconhecido, não gerou trade")

    pares = kronos_log.associar(trades, log)
    grupos: dict[str, list[float]] = {k: [] for k in
                                      ("concordou", "discordou", "neutro", "sem_previsao", "sem_registo")}
    so_bonus, resto = [], []
    for t, rec in pares:
        g = _grupo(rec)
        grupos[g].append(t["liquido"])
        if rec is not None:
            (so_bonus if rec["decisivo"] == "ABRIU_POR_BONUS" else resto).append(t["liquido"])

    print("\nLíquido por trade (papel), segundo o Kronos no momento da entrada:")
    nomes = {"concordou": "Kronos concordou (+2)", "discordou": "Kronos discordou (−1)",
             "neutro": "Kronos neutro (0)", "sem_previsao": "Sem previsão (off/cooldown/erro)",
             "sem_registo": "Sem registo (antes do log)"}
    st = {k: _stats(v) for k, v in grupos.items()}
    for k, nome in nomes.items():
        print(_linha(nome, st[k]))

    sb, rs = _stats(so_bonus), _stats(resto)
    print("\nIsolar o efeito do bónus (só trades com registo):")
    print(_linha("Abriram SÓ por causa do bónus", sb))
    print(_linha("Todos os outros", rs))

    print("\nDiferenças (t de Welch, indicativo):")
    for titulo, a, b in (("concordou − discordou", st["concordou"], st["discordou"]),
                         ("só-por-bónus − outros", sb, rs)):
        t_val = _welch(a, b)
        pequeno = min(a["n"], b["n"]) < MIN_AMOSTRA
        txt = "n/d" if t_val is None else f"{t_val:+.2f}"
        aviso = f"  ⚠ amostra < {MIN_AMOSTRA} num dos grupos — ruído" if pequeno else ""
        print(f"  {titulo:<26} t = {txt}{aviso}")


if __name__ == "__main__":
    main()
