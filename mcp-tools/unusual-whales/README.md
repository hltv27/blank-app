# Unusual Whales MCP — configuração

Liga o Claude Code ao servidor MCP oficial da [Unusual Whales](https://unusualwhales.com/)
— fluxo de opções, dark pool, trades do congresso, exposição a gregas, volatilidade
e futuros. Mais de 200 endpoints.

**Independente do Claw Agent v8** (`claw_v8/`) — não tem relação com o bot de trading
descrito no `CLAUDE.md` da raiz.

## ⚠️ Correcção — a versão anterior deste ficheiro estava errada

A primeira versão apontava para `https://unusual-whales.com/public-api/mcp`, que
tinha três problemas ao mesmo tempo e nunca teria funcionado:

| | Errado | Certo |
|---|---|---|
| Domínio | `unusual-whales.com` (com hífen) | `unusualwhales.com` |
| Caminho | `/public-api/mcp` | `api.unusualwhales.com/api/mcp` |
| Autenticação | ausente | `Authorization: Bearer <chave>` |

O segundo é o mais fácil de errar, e a documentação oficial avisa: **`unusualwhales.com/public-api/mcp`
é a página de documentação, não o servidor.** É esse o link que aparece nas publicações
da Unusual Whales, e copiá-lo directamente para um `.mcp.json` não funciona.

## Chave de API

Obtém-se em `unusualwhales.com/settings/api-dashboard` (requer subscrição; há trials).

**A chave nunca entra neste repositório.** O `.mcp.json` lê-a da variável de ambiente
`UNUSUAL_WHALES_API_KEY`, que defines na tua máquina:

```bash
# no teu ~/.bashrc, ~/.zshrc ou equivalente
export UNUSUAL_WHALES_API_KEY="a-tua-chave"
```

## Como usar

### Opção A — global (recomendado)

Não precisa deste repositório. Numa sessão interactiva do Claude Code:

```bash
claude mcp add --transport http unusualwhales \
  https://api.unusualwhales.com/api/mcp \
  --header "Authorization: Bearer $UNUSUAL_WHALES_API_KEY"
```

Fica disponível em todos os projectos.

### Opção B — project-scoped (este ficheiro)

```bash
cd blank-app/mcp-tools/unusual-whales
claude
```

O Claude Code deteta o `.mcp.json` e pede aprovação para ligar ao servidor.
Só funciona quando abres o Claude Code **dentro desta pasta**.

## Verificar

```bash
claude mcp get unusualwhales
```

Se a variável de ambiente não estiver definida, o header vai literalmente como
`Bearer ${UNUSUAL_WHALES_API_KEY}` e o servidor devolve 401.
