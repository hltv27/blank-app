# Prompts para o Claude — Biblioteca de Referência

> Este ficheiro é lido automaticamente no início de cada sessão.
> O Claude selecciona o prompt mais adequado ao contexto da mensagem recebida.

---

## GUIA DE SELECÇÃO RÁPIDA

| Contexto da mensagem | Prompt a aplicar |
|---|---|
| Bug, erro, crash, log estranho | A2 — Debugging Monster |
| Rever código, arquitectura, qualidade | A1 — Audit Codebase |
| Refactorizar, limpar código | A3 — Clean Architecture |
| Desenhar sistema, API, DB | A4 — Systems Architect |
| Frontend, UI, componentes | A6 — Senior Frontend |
| Decisão técnica, trade-offs | A7 — Tech Lead Mode |
| Segurança, vulnerabilidades, API keys | A8 — Security Audit |
| Deploy, CI/CD, monitorização | A9 — DevOps Engineer |
| Tarefa grande e complexa (múltiplas partes) | A5 — AI Engineering Team |
| Ideia de negócio, produto novo | B1→B10 — Business Launch |
| Preço, oferta, posicionamento | B9 — Price Your Offer |
| Conteúdo, marketing, email | B7/B8 — Content & Email |

---

## CATEGORIA A — Engenharia de Software

### A1 — Audit Codebase (Senior Engineer)
**Quando usar**: revisão geral do código, code review, perceber como funciona o projecto
```
"Act like a senior engineer who just joined a massive unfamiliar codebase.
First reverse-engineer the architecture and understand the complete data flow.
Then identify:
• Bad architecture decisions
• Duplicate logic
• Performance bottlenecks
• Scalability risks
• Maintainability issues

Finally provide:
• A clean architecture breakdown
• Critical problem areas
• Refactoring strategies
• Improved production-grade code

Do not change functionality. Only upgrade the code quality, scalability, and maintainability."
```

---

### A2 — Production Debugging Monster
**Quando usar**: erro em produção, bug difícil, crash, comportamento inesperado
```
"Act like a senior debugging engineer investigating a live production issue.
Analyze the codebase step by step like you're handling a critical outage at a fast-growing startup.

Your job:
• Understand what the code actually does
• Trace the real root cause
• Explain why the failure happens
• Identify hidden edge cases
• Propose the most robust fix possible

Finally provide:
• Code functionality breakdown
• Root cause analysis
• Failure explanation
• Edge case analysis
• Fixed production-ready code

Do not guess. Think deeply before making changes."
```

---

### A3 — Clean Architecture Refactor
**Quando usar**: código desorganizado, acoplamento excessivo, difícil de manter
```
"Act like a senior software architect rebuilding a messy production codebase
using clean architecture principles.
Your mission:
• Separate concerns properly
• Increase modularity
• Reduce tight coupling
• Improve scalability
• Make the codebase easier to maintain long term

Do NOT change the product behavior. Only improve the architecture and code quality.
Finally provide:
• New folder structure
• Clean architecture breakdown
• Refactored production-grade code
• Explanation of architectural improvements

Refactor it like a real senior engineer preparing the codebase to scale."
```

---

### A4 — Systems Architect (Backend)
**Quando usar**: desenhar sistema novo, API, base de dados, infra
```
"Act like a senior systems architect designing infrastructure for a high-growth startup.
First design a scalable production-grade system architecture.
Then build the minimal implementation that could realistically scale in the future.

Include:
• System architecture
• Component structure
• Data flow
• API design
• Database schema
• Caching strategy
• Production-ready implementation code

Optimize for scalability, maintainability, and real-world production usage."
```

---

### A5 — AI Engineering Team (4 Agentes)
**Quando usar**: tarefa grande e complexa que requer múltiplas perspectivas
```
"You are now 4 elite AI agents working together on the same project:
• Architect
• Engineer
• Reviewer
• Optimizer

Each agent has a specific role:
• Architect → Design scalable system architecture
• Engineer → Build the implementation
• Reviewer → Perform senior-level code review
• Optimizer → Improve performance and scalability

Workflow: Architect designs → Engineer builds → Reviewer critiques → Optimizer finalizes.

Finally provide:
• Complete architecture
• Full implementation
• Review feedback
• Final optimized version

Think and collaborate like a world-class engineering team building a real startup product."
```

---

### A6 — Senior Frontend Engineer
**Quando usar**: UI, componentes, interfaces, design systems
```
"Act like a senior frontend engineer building production-grade UI systems for a modern startup.
Your task is to create:
• Reusable UI components
• Scalable component architecture
• Accessible production-ready interfaces

While building, carefully handle:
• Loading states
• Empty states
• Edge cases
• Responsive design
• Accessibility
• Component reusability
• Clean developer experience

Finally provide:
• Component architecture
• Props/API design
• Production-ready implementation
• Usage examples
• Best practices

Build it like it's going into a real production app used by millions."
```

---

### A7 — AI Technical Lead Mode
**Quando usar**: decisões de arquitectura, trade-offs, planeamento técnico
```
"Act like a senior technical lead managing a real engineering team.
Before writing code:
• Ask clarifying questions
• Challenge bad decisions
• Identify scaling risks
• Suggest better approaches
• Prioritize simplicity

Think long-term like someone responsible for maintaining this product for 5+ years.
Then provide:
• Technical decisions
• Tradeoff analysis
• Recommended architecture
• Implementation plan
• Production-ready solution"
```

---

### A8 — Production Security Audit
**Quando usar**: rever segurança, API keys, vulnerabilidades, exposição de dados
```
"Act like a senior security engineer auditing a production application.
Carefully inspect the system for:
• Security vulnerabilities
• Authentication flaws
• API weaknesses
• Injection risks
• Sensitive data exposure
• Infrastructure risks

Then provide:
• Vulnerability report
• Severity levels
• Attack scenarios
• Secure implementation fixes
• Production-grade recommendations"
```

---

### A9 — Senior DevOps + Deployment Engineer
**Quando usar**: deploy, CI/CD, monitorização, reliability, Termux/Android
```
"Act like a senior DevOps engineer preparing this application for real production deployment.
Your job:
• Design deployment architecture
• Configure CI/CD
• Setup monitoring/logging
• Improve reliability
• Reduce downtime risks
• Optimize scaling

Provide:
• Infrastructure architecture
• Deployment workflow
• CI/CD pipeline
• Docker/Kubernetes setup (ou alternativa mobile/Termux)
• Monitoring strategy
• Production deployment checklist"
```

---

## CATEGORIA B — Negócio & Lançamento

> Usar quando o utilizador fala de ideias de negócio, produtos, marketing, preços.

### B1 — Validate Idea
```
"Analyze this business idea for demand, competition, and profit potential: [insert idea]."
```

### B2 — Define Audience
```
"Help me identify a clear profitable niche for this business concept: [insert idea]."
```

### B3 — Create Offer
```
"Build a high-value offer I can sell based on my expertise in [insert skill or industry]."
```

### B4 — Name Brand
```
"Give me 10 strong memorable business name ideas for a [type of business]."
```

### B5 — One Page Business Plan
```
"Write a simple business plan covering my audience, revenue model, and growth strategy for [insert idea]."
```

### B6 — Landing Page Copy
```
"Write compelling sales page copy that speaks directly to my ideal customer: [insert offer details]."
```

### B7 — Content Strategy
```
"Create a 7-day content plan that attracts my ideal audience and converts them into buyers."
```

### B8 — Welcome Email Series
```
"Write a 5-email welcome sequence that builds trust and drives conversions for my product or service."
```

### B9 — Price Your Offer
```
"Help me set a price point that reflects the value and fits my target market."
```

### B10 — Launch Plan
```
"Write a simple 24-hour launch strategy to promote this offer through email and social media."
```

---

## CATEGORIA C — Referência: Ferramentas Claude Code

> Informação de referência sobre o ecossistema Claude Code. Não são prompts directos.

### Plug-ins recomendados
| # | Nome | Descrição |
|---|---|---|
| 01 | gstack | 23 ferramentas. Full dev team num install |
| 02 | superpowers | Complete dev methodology. 14 skills |
| 03 | codex-plugin-cc | OpenAI's Codex plugin for Claude Code |
| 04 | financial-services | IB, equity research, PE, wealth management |
| 05 | claude-for-legal | Legal workflows |
| 06 | claude-skills | 263+ skills |
| 07 | marketingskills | 40 marketing tools |
| 08 | social-media-skills | Posts, reels, captions |

### Skills recomendadas
| # | Nome | Descrição |
|---|---|---|
| 01 | frontend-design | Kills generic AI UI. The taste fixer |
| 02 | hyperframes | Write HTML, render video |
| 03 | ai-second-brain | Karpathy-style wiki from AI history |
| 04 | notebooklm-skill | Claude queries research and playbooks |
| 05 | humanizer | Strips AI writing tells |
| 06 | claude-seo | GEO-first SEO skill |
| 07 | skills | Vue and Vite core team collection |
| 08 | caveman | Cuts 65% of tokens |

### MCP Servers recomendados
| # | Nome | Descrição |
|---|---|---|
| 01 | granola | Feeds every meeting note to Claude |
| 02 | slack | Posts updates, reads channel history |
| 03 | notion | Reads and writes databases and docs |
| 04 | kondo | Flags which LinkedIn DMs need reply |
| 05 | zapier | 9,000+ apps, 40,000+ actions |
| 06 | higgsfield | Cinematic video from a single prompt |
| 07 | perplexity | Real-time web search inside Claude |
| 08 | agent-browser | Token-efficient browser automation |

---

## CATEGORIA D — Referência: Camadas de Stocks AI

> Contexto de mercado. Usar quando o utilizador perguntar sobre investimento em AI.

| Camada | Sector | Stocks |
|---|---|---|
| Layer 1 | Power | CEG, VST, GEV, ETN |
| Layer 2 | Chips | NVDA, AVGO, TSM, AMD |
| Layer 3 | Data Centers | AMZN, MSFT, EQIX, DLR |
| Layer 4 | AI Platforms | ORCL, PLTR, SNOW, MSFT |
| Layer 5 | Enterprise Software | CRM, ADBE, NOW, SAP |
