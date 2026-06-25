# Decisões Técnicas — CLAW Agent v8

## Endpoint de ordens (BNFCR)
**Decisão:** Usar `/fapi/v1/algoOrder` para STOP_MARKET e TAKE_PROFIT_MARKET.
**Porquê:** A conta BNFCR rejeita TAKE_PROFIT_MARKET no endpoint regular `/fapi/v1/order`. O endpoint algoOrder aceita ambos os tipos com `closePosition=true`.
**Atenção:** `algoType: "CONDITIONAL"` causa erro "Mandatory parameter type" — não usar.
**SHA:** ef11229 (migração inicial), a1443ba (fix algoType), cb6021b (take_profit de volta ao algoOrder)

## closePosition vs reduceOnly
**Decisão:** Sempre `closePosition=true`, nunca `reduceOnly=true`.
**Porquê:** `reduceOnly=true` não é suportado nesta conta. Único STOP_MARKET por símbolo de cada vez — profit lock cancela o anterior antes de colocar novo.

## pending_sync antes da ordem
**Decisão:** Escrever `pending_sync[symbol]` ANTES de colocar a ordem MARKET.
**Porquê:** Sem este marcador, após restart o bot não reconhece a posição como sua e trata-a como manual → guards não a gerem → risco de posição órfã.
**SHA:** d691f48

## Stop falha → abortar trade
**Decisão:** Se stop falhar 3x → fechar posição MARKET + alerta Telegram.
**Porquê:** Posição sem stop na exchange pode ficar exposta um dia inteiro sem o utilizador saber (incidente HBARUSDC).
**Alternativa rejeitada:** Software SL em memória (insuficiente — depende do bot estar a correr).

## TIME_TP removido
**Decisão:** Remover regra TIME_TP (fecha se >10min e ROI≥5%).
**Porquê:** Estava a cortar winners antes do TP da exchange disparar. Em 101 trades com TP quebrado, contaminou os dados de WR. Com TPs a funcionar, TIME_TP é contraproducente.
**SHA:** cb6021b

## SCORE_ALERTA = 6 (mínimo de entrada)
**Decisão:** Aumentar de 4 para 6.
**Porquê:** Score 4 permitia entradas com apenas 4 indicadores a confirmar — demasiado permissivo. Score 6 exige alinhamento forte.
**SHA:** e0003ea

## ADX_TREND_MIN_ALT = 25 (era 30)
**Decisão:** Baixar de 30 para 25 para alts.
**Porquê:** ADX 30 bloqueava quase todos os alts em mercado lateral normal. 25 mantém o filtro mas permite mais entradas em tendências moderadas.

## RSI_OVERSOLD = 45, RSI_OVERBOUGHT = 55
**Decisão:** Alargar a janela de RSI (era 42/58).
**Porquê:** RSI entre 42-45 e 55-58 é muito comum em tendências reais — alargar dá mais +3 pontos de score em condições válidas.

## get_margin_ratio_global() para guards
**Decisão:** Guards usam `totalMaintMargin / totalMarginBalance` da conta inteira.
**Porquê:** `get_margin_ratio()` por asset incluía cross-collateral de posições USDT-M → falsos positivos (244-360% em vez de 18%).
**SHA:** 0487fd0

## Markov regime signal (+2 pontos)
**Decisão:** Adicionar Markov chain ao score de entrada.
**Porquê:** Detecta persistência de regime (bull/bear) com base na matriz de transição dos últimos 100 candles. Adiciona 2 pontos ao score quando confirma direcção.

## TOP_N_FUTURES = 50 (era 150)
**Decisão:** Reduzir de 150 para 50 pares scanned.
**Porquê:** 150 pares incluía memecoins exóticos de baixo volume com spreads altos e liquidez fraca.

## auto_deploy.sh com detecção de crash
**Decisão:** Script verifica `pgrep python3` e reinicia se morto, com alerta Telegram.
**Porquê:** Bot caiu sem notificação — utilizador só deu conta horas depois.
**Cron:** `* * * * *` no VPS.
