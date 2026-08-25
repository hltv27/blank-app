# Unusual Whales MCP — configuração

Config MCP (project-scoped) para ligar o Claude Code ao servidor MCP público da
[Unusual Whales](https://unusual-whales.com/) (dados de fluxo de opções, dark pool, etc.).

**Independente do Claw Agent v8** (`claw_v8/`) — não relacionado com o bot de trading
descrito no `CLAUDE.md` da raiz do repositório.

## O que é

`.mcp.json` nesta pasta regista o servidor `unusual-whales` via transporte HTTP:

```json
{
  "mcpServers": {
    "unusual-whales": {
      "type": "http",
      "url": "https://unusual-whales.com/public-api/mcp"
    }
  }
}
```

## Como usar

1. Clona o repo (ou faz `git pull`) em qualquer máquina.
2. Abre o Claude Code **dentro desta pasta** (`mcp-tools/unusual-whales/`):
   ```bash
   cd blank-app/mcp-tools/unusual-whales
   claude
   ```
3. O Claude Code deteta o `.mcp.json` do projecto e pede aprovação para ligar
   ao servidor `unusual-whales` — aceita quando pedido.
4. Se o servidor exigir autenticação (API key da tua conta Unusual Whales),
   o Claude Code guia-te pelo fluxo (ou é preciso adicionar um header
   `Authorization` — ver `claude mcp get unusual-whales` depois de ligado).

## Alternativa: adicionar globalmente (sem repo)

Em vez de usar este ficheiro, também podes adicionar o servidor directamente
no teu Claude Code local, sem precisar deste repositório:

```bash
claude mcp add --transport http unusual-whales https://unusual-whales.com/public-api/mcp
```

## Nota

Este ficheiro foi criado a pedido do utilizador com base num vídeo do
Instagram (`colton.ai.dean`) que demonstrava este setup. Não confirmei a
legitimidade completa do endpoint além de ser o domínio oficial da Unusual
Whales — revê os termos de uso e a política de dados antes de autorizar em
produção.
