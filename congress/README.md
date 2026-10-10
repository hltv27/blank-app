# Alertas de divulgações do Congresso dos EUA

Faz polling aos registos públicos da Câmara e do Senado e manda Telegram quando
aparece uma **Periodic Transaction Report** (PTR) nova.

**Independente do Claw Agent v8** (`claw_v8/`) — não importa nada dele, não lhe
toca, e não executa ordens. Só lê e avisa.

## ⚠️ O que isto não é

**Não sabe de trades em tempo real.** O STOCK Act dá **45 dias** para divulgar,
por isso o que se apanha é a *submissão do documento* — que pode referir-se a uma
compra feita há mês e meio.

Ninguém tem melhor do que isto. A Unusual Whales, o Capitol Trades e o Quiver
fazem polling aos mesmos sites públicos; o que vendem é conveniência, não acesso
privilegiado. Quem anunciar "alertas em tempo real das compras da Pelosi" está a
vender outra coisa.

## Fontes

| | |
|---|---|
| Câmara | `disclosures-clerk.house.gov` — ZIP anual com índice XML |
| Senado | `efdsearch.senate.gov` — exige aceitar o aviso legal antes de pesquisar |

Públicas, gratuitas, sem chave de API.

## Instalar na VPS

```bash
cd /root && git clone -b main https://github.com/hltv27/blank-app.git ca-tmp \
  && cp -r ca-tmp/congress /root/congress && rm -rf ca-tmp
cd /root/congress
```

As credenciais do Telegram são as mesmas do `claw_v8` (`TELEGRAM_TOKEN` e
`TELEGRAM_CHAT_ID`), já no ambiente da VPS.

## Usar

**Primeira vez — marcar o que já existe sem disparar centenas de alertas:**
```bash
python3 congress_alerts.py --backfill
```

**Testar um ciclo:**
```bash
python3 congress_alerts.py --once
```

**Correr em contínuo:**
```bash
nohup python3 congress_alerts.py > /root/congress.log 2>&1 &
```

## Configuração

No topo do `congress_alerts.py`:

| | |
|---|---|
| `POLL_MIN` | minutos entre ciclos (default 10) |
| `WATCHLIST` | apelidos em minúsculas; vazio = alerta sobre todos |

Exemplo para vigiar só alguns:
```python
WATCHLIST = ["pelosi", "greene", "tuberville"]
```

Com a lista vazia recebes tudo — são tipicamente dezenas por semana, o que
enche o Telegram depressa.

## Robustez

- **Estado em `seen.json`** — os documentos já vistos não voltam a alertar,
  mesmo depois de reiniciar
- **O Senado a falhar não mata a Câmara.** O fluxo do `efdsearch` depende de um
  formulário com CSRF que eles podem mudar sem aviso; quando parte, a Câmara
  continua a funcionar e o erro fica no log
- **Um pedido por fonte a cada 10 minutos**, com User-Agent identificado

## Testado

Parser alimentado com XML no formato real da Câmara: separa PTRs de declarações
anuais, ignora entradas sem `DocID`, constrói o URL do PDF, não repete alertas
entre ciclos, filtra pela watchlist, o estado sobrevive a reinício, e uma falha
do Senado não interrompe a Câmara.
