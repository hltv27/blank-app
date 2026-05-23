# REBORNFENIX — Guia de Upload para IPFS

Antes de fazer o deploy da coleção, precisas de colocar a imagem do phoenix e
o ficheiro de metadata da coleção num serviço de armazenamento descentralizado
(IPFS). Este guia explica dois serviços gratuitos.

---

## O que precisas de fazer upload

1. **A imagem do phoenix** — `rebornfenix/assets/phoenix_logo.png`
2. **O metadata JSON da coleção** — gerado pelo `deploy_collection.js`
   (ficheiro `collection_metadata.json` na pasta `deploy/`)

---

## Opção A — NFT.Storage (recomendado, 100% gratuito)

### 1. Criar conta
- Vai a https://nft.storage
- Clica em **Login** e cria uma conta gratuita (podes usar GitHub ou e-mail)

### 2. Fazer upload da imagem
- Clica em **Upload** → **Files**
- Selecciona o ficheiro `phoenix_logo.png`
- Após o upload, clica no ficheiro e copia o **CID** (parece um hash longo:
  `bafybeig...`)
- O teu URL de imagem fica: `ipfs://<CID>/phoenix_logo.png`

### 3. Atualizar o metadata
- Abre `deploy/collection_metadata.json`
- Substitui o campo `"image"` pelo URL IPFS da imagem:
  ```json
  "image": "ipfs://bafybeig.../phoenix_logo.png"
  ```
- Guarda o ficheiro

### 4. Fazer upload do metadata JSON
- Volta ao NFT.Storage → **Upload** → **Files**
- Faz upload do `collection_metadata.json` já actualizado
- Copia o novo CID do JSON
- O teu URL de metadata fica: `ipfs://<CID>/collection_metadata.json`

### 5. Configurar no .env
```bash
COLLECTION_IMAGE_URI=ipfs://bafybeig.../phoenix_logo.png
COLLECTION_METADATA_URI=ipfs://bafybeig.../collection_metadata.json
```

---

## Opção B — Pinata (alternativa popular)

### 1. Criar conta
- Vai a https://pinata.cloud
- Cria uma conta gratuita (tier gratuito: 1 GB)

### 2. Fazer upload da imagem
- Clica em **Upload** → **File**
- Selecciona `phoenix_logo.png`
- Após o upload, vai aparecer na lista com um **CID**
- O URL fica: `https://gateway.pinata.cloud/ipfs/<CID>`
  ou em formato nativo IPFS: `ipfs://<CID>`

### 3. Atualizar e fazer upload do metadata
- Edita `collection_metadata.json` com o URL da imagem
- Faz upload do JSON também no Pinata
- Usa o CID do JSON como `COLLECTION_METADATA_URI`

### 4. Verificar o upload
- Abre o URL no browser para confirmar que funciona:
  `https://ipfs.io/ipfs/<CID>/phoenix_logo.png`

---

## Dica: Verificar se o IPFS URL está acessível

Depois de fazer upload, confirma no browser:
- NFT.Storage: `https://nftstorage.link/ipfs/<CID>`
- Pinata: `https://gateway.pinata.cloud/ipfs/<CID>`
- Gateway geral: `https://ipfs.io/ipfs/<CID>`

Se a imagem carregar no browser, está tudo certo!

---

## Exemplo de metadata JSON final

Depois de teres os URLs IPFS, o teu `collection_metadata.json` deve ficar assim:

```json
{
  "name": "REBORNFENIX",
  "symbol": "RBFX",
  "description": "22,222 Viking warriors forged in the fires of Ragnarök...",
  "image": "ipfs://bafybeig.../phoenix_logo.png",
  "external_url": "https://rebornfenix.io",
  "attributes": [],
  "properties": {
    "files": [
      {
        "uri": "ipfs://bafybeig.../phoenix_logo.png",
        "type": "image/png"
      }
    ],
    "category": "image"
  }
}
```

---

## Próximo passo

Com os URLs IPFS configurados no `.env`, podes correr:
```bash
node deploy_collection.js
```
