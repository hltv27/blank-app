# REBORNFENIX — Guia Magic Eden Creator Studio

Depois de mintares todos os NFTs, este guia explica como configurar a venda
no Magic Eden, o maior marketplace de NFTs Solana.

---

## Pré-requisitos antes de começar

- [ ] 22.222 NFTs mintados (passo 3 concluído)
- [ ] `collection_address.json` com o endereço da coleção
- [ ] Carteira Solana com a coleção (Phantom, Backpack, ou Solflare)
- [ ] Website da coleção (pelo menos básico)
- [ ] Conta de Twitter/X da coleção
- [ ] Imagem do banner (1400×400 px recomendado)
- [ ] Imagem de perfil (400×400 px)

---

## Passo 1 — Aceder ao Creator Studio

1. Vai a https://magiceden.io/creators
2. Clica em **"Get Started"** ou **"Apply Now"**
3. Conecta a tua carteira Solana (a mesma que usaste para criar a coleção)

> **Importante:** Usa a carteira que é a autoridade da coleção.
> Se usaste outra carteira durante o deploy, tens de usar essa.

---

## Passo 2 — Submeter a candidatura

Preenche o formulário com estes dados:

| Campo | Valor |
|-------|-------|
| **Collection Name** | REBORNFENIX |
| **Symbol/Ticker** | RBFX |
| **Total Supply** | 22,222 |
| **Mint Price** | 10 USDC |
| **Blockchain** | Solana |
| **Collection Address** | (o endereço em `collection_address.json`) |
| **Category** | Art / PFP |
| **Description** | 22,222 Viking warriors forged in the fires of Ragnarök... |
| **Twitter/X** | @REBORNFENIX (ou o teu handle) |
| **Website** | https://rebornfenix.io |
| **Discord** | (se tiveres) |

### Imagens necessárias
- **Profile Image:** 400×400 px, o teu phoenix logo
- **Banner Image:** 1400×400 px (versão alargada do logo)
- **Feature Image:** para a página principal do Magic Eden

---

## Passo 3 — Configurar a mint page

Após aprovação, o Magic Eden vai dar-te acesso ao painel de configuração:

1. **Mint Price:** Define como **10 USDC** (não SOL, para evitar volatilidade)
   - No painel, selecciona USDC como moeda de mint
   - Introduz o valor: `10`

2. **Mint Limit por Carteira:** Recomendado `5-10` para evitar bots

3. **Reveal:** Se queres fazer reveal imediato ou delayed
   - **Imediato:** os NFTs aparecem com os atributos logo ao mint
   - **Delayed:** os NFTs aparecem como "mystery box" até revelares
   - Para REBORNFENIX, recomendado **imediato** (já tens o metadata gerado)

4. **Allowlist (Whitelist):**
   - Podes configurar uma fase de allowlist antes do public mint
   - Útil para recompensar early supporters

---

## Passo 4 — Documentos e informações que o Magic Eden pode pedir

- Prova de que és o criador da coleção (assinar uma mensagem com a carteira)
- Links para as redes sociais activas
- Plano de roadmap/utilidade da coleção
- Amostras dos NFTs (podem pedir 5-10 exemplos)
- Identidade do fundador (algumas vezes — opcional)

---

## Passo 5 — Timeline e o que esperar

| Fase | Tempo estimado |
|------|---------------|
| Submissão da candidatura | Imediato |
| Revisão pelo Magic Eden | 3-7 dias úteis |
| Aprovação e configuração | 1-2 dias |
| Mint page live | Configurável por ti |

**Dicas para aprovação mais rápida:**
- Tem as redes sociais activas com posts sobre a coleção
- Mostra comunidade (Discord/Telegram com membros)
- Imagens de alta qualidade e metadata completo
- Website funcional (mesmo que simples)

---

## Alternativas ao Magic Eden

Se a aprovação demorar ou for recusada:

### Tensor
- https://www.tensor.trade
- Processo de listagem mais simples para cNFTs
- Vai a **"List Collection"** e segue o processo

### Launchpad próprio
- Podes criar uma página de mint directamente
- Usa o SDK do Bubblegum para integrar o mint no teu website
- Mais trabalho mas controlo total

---

## Configurar royalties no Magic Eden

Após listagem, confirma que os royalties estão configurados:
- Vai ao painel da coleção → **"Royalties"**
- Deve mostrar **5%** (configurado durante o deploy)
- Endereço de recepção: a tua carteira

---

## Após o lançamento

1. **Monitorizar o volume:** Magic Eden mostra stats em tempo real
2. **Anunciar no Twitter:** "REBORNFENIX agora disponível no Magic Eden!"
3. **Preço secundário:** começa a monitorizar o floor price
4. **Engage com a comunidade:** responde a compradores, faz posts

---

## Contacto Magic Eden

- Twitter: @MagicEden
- Discord: https://discord.gg/magiceden
- Email de suporte: support@magiceden.io (para questões de criadores)
