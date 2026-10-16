# RAM Saver — Suspensor de Separadores

Extensão para Chrome (Manifest V3) que reduz o consumo de RAM suspendendo
automaticamente separadores inactivos em segundo plano, usando a API nativa
`chrome.tabs.discard()`. Um separador suspenso liberta a memória do
processo de renderização mas continua visível na barra de separadores —
recarrega automaticamente quando voltas a clicar nele.

Não pede acesso ao conteúdo das páginas (sem `host_permissions`) — não lê,
modifica nem envia dados de nenhum site. Só usa `tabs` (para saber
título/URL/estado dos separadores), `storage` (definições) e `alarms`
(verificação periódica em segundo plano).

## Funcionalidades

- Suspende automaticamente separadores inactivos ao fim de X minutos
  (configurável, 15 por omissão)
- Nunca suspende: o separador activo, separadores fixos (pinned) por
  omissão, separadores a reproduzir áudio/vídeo por omissão, ou sites na
  lista branca
- Popup com contadores (separadores abertos / suspensos), lista de
  separadores suspensos (clicável para reactivar), botão para suspender
  tudo já, botão para suspender só o separador actual, atalho para
  adicionar o site actual à lista branca
- Página de definições: activar/desactivar, limiar de inactividade,
  excepções, gestão da lista branca
- Atalhos de teclado: `Ctrl+Shift+U` suspende o separador actual,
  `Ctrl+Shift+I` suspende todos os inactivos (configuráveis em
  `chrome://extensions/shortcuts`)

## Instalação (modo developer)

1. Abrir `chrome://extensions`
2. Activar "Modo de programador" (canto superior direito)
3. "Carregar sem compactar" → seleccionar a pasta `chrome-ram-saver/`

## Testes

```bash
node lib/__tests__/rules.test.mjs
```

Testes unitários (sem dependências) para a lógica de elegibilidade —
`isDiscardableUrl`, `isWhitelisted`, `isEligible`. Não há testes automatizados
de UI; popup e definições foram validados manualmente com Playwright/Chromium
durante o desenvolvimento (carregamento da extensão, contadores, persistência
de definições, lista branca).

## Estrutura

| Ficheiro | Função |
|---|---|
| `manifest.json` | Configuração da extensão (MV3) |
| `background.js` | Service worker — temporizador de inactividade, listeners de separadores, badge |
| `lib/storage.js` | Definições (`storage.local`) e actividade por separador (`storage.session`) |
| `lib/rules.js` | Lógica de elegibilidade (o que pode/não pode ser suspenso) |
| `popup.html/js/css` | Interface do ícone da barra de ferramentas |
| `options.html/js/css` | Página de definições |
| `icons/` | Ícones 16/48/128px |

## Porquê `chrome.tabs.discard` e não fechar o separador?

Fechar o separador perde o histórico de navegação e o estado da página.
`discard()` é a mesma técnica usada pelo próprio gestor de memória do
Chrome e por extensões como o "The Great Suspender" — o separador
continua na barra, com o título e favicon, mas o processo de
renderização é libertado até seres tu a reactivá-lo.
