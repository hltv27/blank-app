# REBORNFENIX — Guia Magic Eden Launchpad (Sem Chave Privada)

Tudo feito pelo browser. Só precisas da Phantom ligada.

---

## O que é o Magic Eden Launchpad

Em vez de fazeres deploy técnico, o Magic Eden trata da infraestrutura de mint por ti.
Tu forneces o artwork, o metadata e os detalhes — eles criam a página de mint.
**Não precisas de exportar chaves privadas.** Só assinares com a Phantom.

---

## FASE 1 — Preparação (faz isto primeiro)

### 1.1 — Cria as contas nas redes sociais

O Magic Eden exige evidência de projecto real antes de aprovar.

| Rede | Handle sugerido | Prioridade |
|------|----------------|------------|
| Twitter/X | @REBORNFENIX ou @RebornFenixNFT | **Obrigatório** |
| Discord | Servidor REBORNFENIX | Recomendado |
| Telegram | @RebornFenix | Opcional |

Faz 3-5 posts antes de candidatar. O manifesto que criei está em
`marketing/manifesto.md` — usa excertos para os primeiros posts.

### 1.2 — Prepara as imagens

Precisas de 3 formatos do teu logo:

| Imagem | Dimensão | Uso |
|--------|----------|-----|
| Perfil | 400 × 400 px | Ícone da coleção |
| Banner | 1400 × 400 px | Cabeçalho da página |
| Feature | 600 × 400 px | Destaque no Magic Eden |

O teu ficheiro original está em `assets/phoenix_logo.png`.
Para redimensionar grátis: **Canva** (canva.com) ou **remove.bg** para fundo transparente.

### 1.3 — Sobe o logo para IPFS (grátis)

O metadata de cada NFT precisa de um URL permanente para a imagem.

**NFT.Storage (gratuito, recomendado):**
1. Vai a `nft.storage`
2. Cria conta gratuita com o teu email
3. Clica em **"Upload"**
4. Sobe o ficheiro `assets/phoenix_logo.png`
5. Copia o **CID** que aparece (parece: `bafybeig...`)
6. O URL fica: `ipfs://SEU_CID_AQUI/phoenix_logo.png`

Guarda este URL — vai ser preciso no passo seguinte.

---

## FASE 2 — Candidatura ao Magic Eden Launchpad

### 2.1 — Aceder ao formulário

1. Abre o browser no telemóvel
2. Vai a: `magiceden.io/launchpad`
3. Clica em **"Apply for Launchpad"** ou **"Submit Project"**
4. Liga a tua Phantom quando pedir

### 2.2 — Preencher o formulário

Copia e cola estes valores:

**Informações base:**
```
Collection Name:  REBORNFENIX
Symbol/Ticker:    RBFX
Blockchain:       Solana
Total Supply:     22,222
Mint Price:       10 USDC
Mint Limit/Wallet: 1
```

**Descrição curta (para o formulário):**
```
22,222 Viking warriors forged in Ragnarök's fire. Each soul carries
a unique Elder Futhark rune — ancient wisdom burned into the blockchain.
Born from loss. Built for those who refused to break. One per wallet.
No replicas. No surrender.
```

**Descrição longa** — copia de `marketing/magic_eden_listing.md`

**Links:**
```
Twitter:  https://twitter.com/REBORNFENIX  (ou o teu handle)
Website:  (deixa em branco por agora, ou usa um link temporário)
Discord:  (opcional)
```

### 2.3 — Roadmap para o formulário

```
Fase 1 — Mint (Mês 1)
Lançamento das 22.222 runas. Cada holder recebe o seu NFT único
com a runa Elder Futhark designada pelo destino.

Fase 2 — Comunidade (Mês 2-3)
Servidor Discord activo. Eventos semanais para holders.
Wallet de tesouraria comunitária com 5% da receita do mint.

Fase 3 — Utilidade (Mês 4-6)
Acesso exclusivo a sinais de trading para holders.
Parceria com plataformas cripto para benefícios Fenix.

Fase 4 — O Renascimento (Mês 6+)
Segunda coleção para os 22 Reborn (ultra-raros).
Expansão do universo REBORNFENIX.
```

---

## FASE 3 — Enquanto aguardas aprovação (3-7 dias)

### 3.1 — Gerar o artwork dos NFTs

Cada NFT precisa de uma imagem própria. Tens duas opções:

**Opção A — Simples (recomendado para começar):**
Todos os 22.222 NFTs usam o mesmo logo base (a fénix).
A diferença é o **texto da runa** sobreposto.
Fica único pelo metadata, não pela imagem.
Muitas coleções fazem isto e resulta.

**Opção B — Generativo (mais impacto visual):**
Script Python que sobrepõe a runa unicode no logo base.
Se quiseres, peço para gerar esse script.

### 3.2 — Activa as redes sociais

Publica o primeiro post com o manifesto.
O texto está pronto em `marketing/twitter_threads.md` — Thread 1.

### 3.3 — Cria o servidor Discord

A estrutura completa está em `marketing/discord_server_structure.md`.
Usa o Discord gratuito — não precisas de nada pago.

---

## FASE 4 — Após aprovação do Magic Eden

### 4.1 — Configurar o painel

Quando aprovado recebes acesso ao Creator Studio:

1. **Upload do artwork:** Podes carregar as imagens directamente no painel
2. **Upload do metadata:** Os ficheiros JSON estão em `metadata/generated/`
   - Para os 22.222 completos: corre `python metadata/metadata_generator.py --full`
3. **Preço:** Define 10 USDC
4. **Data de mint:** Escolhe com pelo menos 1 semana de antecedência para marketing
5. **Reveal:** Escolhe "Instant" (imediato)

### 4.2 — Assinar com a Phantom

O Magic Eden vai pedir para assinares uma transacção com a Phantom
para confirmar que és o dono da coleção. **Não custa nada** (é só uma assinatura).

---

## Alternativas se o Magic Eden recusar ou demorar

### Tensor Trade
- `tensor.trade` → "Create Collection"
- Processo mais simples, menos burocracia
- Audiência mais técnica mas igualmente válida

### Launch directamente no teu website
- O ficheiro `website/index.html` já tem o botão de mint integrado
- Só precisas de um domínio (~$20) e hosting (Netlify = gratuito)
- Pedes a alguém técnico para fazer a integração final com Candy Machine

---

## Checklist final antes de lançar

- [ ] Twitter/X criado com 3+ posts
- [ ] Logo subido para IPFS (tens o URL `ipfs://...`)
- [ ] Formulário Magic Eden submetido
- [ ] Metadata dos 22.222 NFTs gerado (`python metadata_generator.py --full`)
- [ ] Discord criado (mesmo que vazio)
- [ ] Data de mint definida
- [ ] Threads de lançamento prontas para publicar (`twitter_threads.md`)

---

## Contacto Magic Eden

- Twitter: @MagicEden
- Discord oficial do Magic Eden (para criadores)
- Email: creators@magiceden.io
