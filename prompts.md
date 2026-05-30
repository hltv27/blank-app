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

---

## CATEGORIA E — Análise de Stocks & Investimento

> Usar quando o utilizador pedir análise de acções, portfólio, earnings, risco, entrada.
> Fonte: @berttrading + vídeo "7 prompts Wall Street analyst"

### E1 — Senior Wall Street Analyst
```
"Act as a senior Wall Street analyst. Analyze [stock ticker] covering revenue growth,
profit margins, debt levels, competitive position, and valuation.
Give me a clear buy, hold, or sell recommendation with reasoning."
```

### E2 — Stock Screener
```
"Create a stock screening criteria list for finding [growth/dividend/value] stocks.
Include the exact financial metrics, ratios, and thresholds I should filter by
to find high-quality opportunities in [sector/market]."
```

### E3 — Earnings Report Decoder
```
"Break down this earnings report for [company] in plain language: [paste report].
Highlight what beat or missed expectations, what management signaled about the future,
and whether the results change the investment case."
```

### E4 — Real Risk Assessment
```
"Analyze the downside risk of investing in [stock ticker].
Cover industry threats, competitive risks, balance sheet vulnerabilities,
macro exposure, and the realistic worst-case scenario for this position."
```

### E5 — Compare Two Stocks Head to Head
```
"Compare [stock A] vs [stock B] for a [growth/income/value] investor
with a [timeframe] horizon.
Analyze valuation, growth trajectory, financial health, and competitive moat.
Tell me which is the stronger buy and why."
```

### E6 — Build a Diversified Portfolio
```
"I have $[amount] to invest in individual stocks with a [conservative/growth/aggressive]
strategy and [timeframe] horizon.
Build me a diversified portfolio of [number] stocks with allocation percentages
and the thesis behind each pick."
```

### E7 — Time Your Entry Like a Pro
```
"I want to buy [stock ticker] but want to enter at the best possible price.
Analyze its current valuation, recent price action, and key support levels
to tell me whether to buy now, wait for a pullback, or set a specific target entry price."
```

### E8 — Universe Builder (25 stocks por tema)
```
"Build me a watchlist of 25 large-cap stocks based on a theme.

THEME: [Pick a number, or write your own]
1. AI infrastructure
2. Semiconductors
3. Cybersecurity
4. GLP-1/obesity
5. Defense primes
6. Credit-card networks
7. Software at a discount
8. Re-shoring industrials

Output a clean numbered list of 25 tickers with a one-line description for each."
```

### E9 — Conviction Score (100 pontos)
```
"Score every name on a 100-point Conviction Score.

QUALITY GATE — +20 each (80 max):
• ROIC ≥ 15%
• Positive Free Cash Flow
• Net debt/EBITDA < 2x
• Revenue growing year over year

DISCOUNT GATE — +10 each (20 max):
• 15%+ below 52-week high
• Forward P/E below trailing P/E

Tier: BEST 80+ | STRONG 65-79 | WATCH 50-64 | AVOID <50

Output: One ranked table.
Rank | Ticker | Score | Tier | Thesis"
```

### E10 — Deep Thesis Top-3
```
"For the top 3 names from the ranked table, give me a deep thesis on each.

For each ticker:
1. THE MOAT — what makes it durable?
2. THE DRAWDOWN — why is it on sale right now?
3. THE CATALYST — what unlocks the upside in 12 months?
4. THE EXIT — specific price level or fundamental trigger that kills the thesis.

Cite the source for each claim.
Format: three short cards, one per ticker."
```

---

## CATEGORIA F — Ferramentas AI de Referência

> 15 ferramentas AI recomendadas (@prompt.wiz). Usar quando o utilizador perguntar sobre ferramentas externas.

### F1 — AI & Automation
| # | Ferramenta | Descrição |
|---|---|---|
| 1 | Lindy.ai | AI employee — meetings, emails, customer support |
| 2 | Perplexity.ai | "Google Killer" de 2026. Respostas citadas sem ads |
| 3 | Make.com | "Glue" da internet — conecta apps sem código |

### F2 — Visual & Video
| # | Ferramenta | Descrição |
|---|---|---|
| 4 | Klingai.com | Vídeos 1080p cinemáticos a partir de texto |
| 5 | Runwayml.com | Editor de vídeo AI profissional |
| 6 | Gamma.app | Apresentação completa a partir de uma frase |

### F3 — Growth & Marketing
| # | Ferramenta | Descrição |
|---|---|---|
| 7 | Vappi.ai | Lead generation com mensagens personalizadas |
| 8 | ManyChat.com | Automação de DMs Instagram/Facebook |
| 9 | AdCreative.ai | Gera centenas de banners e posts adaptados à marca |

### F4 — Research & Academic
| # | Ferramenta | Descrição |
|---|---|---|
| 10 | Consensus.app | Motor de busca AI em 200M+ papers científicos |
| 11 | Humata.ai | Faz upload de PDF de 100 páginas e conversa com ele |
| 12 | Tome.app | Apresentações imersivas com AI |

### F5 — Coding & Utility
| # | Ferramenta | Descrição |
|---|---|---|
| 13 | Replit.com | Build, host, deploy directamente no browser |
| 14 | TinyWow.com | PDF, vídeo trimming, remoção de background |
| 15 | 10MinuteMail.com | Email temporário para evitar spam |

---

## CATEGORIA G — GitHub Repos Notáveis

> Repos open-source de referência. Instalar apenas quando necessário.

| Stars | Repo | Descrição |
|---|---|---|
| 3.7k | AgriciDaniel/claude-ads | Ad agency num comando. 250+ checks Google/Meta/YouTube/LinkedIn/TikTok |
| 17.4k | Fincept-Corporation/FinceptTerminal | Bloomberg Terminal open-source. 100+ fontes, 37 AI agents (Buffett, Munger, Lynch) |
| 10k | Anil-matcha/Open-Generative-AI | Midjourney+Sora+HeyGen self-hosted. 200+ modelos. Free |

---

## CATEGORIA H — Claude Hacks & Keywords Especiais

> Técnicas para controlar comportamento e poupar tokens.

### H1 — Caveman Method (poupa ~40% tokens)
Usar quando respostas são demasiado longas ou com filler.
```
"From now on, remove all filler words. No 'the', 'is', 'am', 'are'.
Direct answer only. Use short 3-6 word sentences.
Run tools first, show the result, then stop. Do not narrate.
Example: Instead of 'The solution is to use async', say 'Use async'."
```

### H2 — Code Review Graph (poupa 60-70% tokens em projectos de código)
Ferramenta externa que converte o código num mapa estruturado.
- Repo: `github.com/tirth8205/code-review-graph`
- Claude vê a estrutura em vez de cada linha → muito mais eficiente

### H3 — ULTRATHINK (activa raciocínio profundo)
Escrever `ULTRATHINK` em qualquer parte do prompt.
- Activa o nível mais profundo de raciocínio do Claude
- Usar em tudo que é complexo ou importante

### H4 — STEELMAN THIS (fortalece argumentos/pitches)
Escrever `STEELMAN THIS` antes de qualquer texto.
- Claude converte o que escreveste na versão mais sólida e persuasiva possível
- Ideal para pitches, emails, propostas

---

## CATEGORIA I — Slash Commands (Hina Arora / @careerwithhina)

> Sistema de comandos por categoria. Adicionar ao final de qualquer prompt para controlar output.

### I1 — Execution / Output Mode
```
/ghost         → only final answer, no explanation
/minimal       → shortest possible response
/brief         → 3-5 lines max
/expand        → detailed explanation
/stepbystep    → clear steps
/checklist     → actionable checklist
/framework     → structured framework
/blueprint     → implementation plan
/playbook      → repeatable system
/roadmap       → timeline based steps
```

### I2 — Thinking Styles
```
/analyst       → deep analysis
/critic        → find flaws only
/optimizer     → improve what's given
/simplify      → explain like beginner
/eli5          → very simple explanation
/deepdive      → go very detailed
/compare       → compare options
/proscons      → list pros and cons
/firstprinciples → break to basics
/contrarian    → challenge idea
```

### I3 — Content Creation
```
/linkedin      → LinkedIn post
/twitter       → short thread style
/script        → video/reel script
/hook          → strong opening lines
/story         → storytelling format
/carousel      → slide-wise content
/headlines     → multiple title options
/captions      → social captions
/viral         → high engagement style
/authority     → expert tone
```

### I4 — Coding / Tech
```
/debug         → find bugs
/refactor      → clean code
/optimizecode  → improve performance
/systemdesign  → architecture design
/api           → API structure
/database      → DB design
/scalability   → scaling approach
/security      → security checks
/testcases     → generate tests
/pseudocode    → logic only
```

### I5 — Business / Strategy
```
/startup       → startup idea
/gtm           → go to market plan
/monetize      → revenue ideas
/validate      → validate idea
/icp           → ideal customer profile
/sales         → sales pitch
/colddm        → cold outreach
/offer         → offer creation
/funnel        → funnel strategy
/retention     → retention ideas
```

### I6 — Productivity
```
/plan          → daily plan
/weekly        → weekly plan
/prioritize    → what to do first
/focus         → remove distractions
/automate      → automation ideas
/delegate      → what to delegate
/habits        → habit building
/track         → tracking system
/timeblock     → time blocking
/review        → weekly review
```

### I7 — Learning
```
/learn         → explain topic
/resources     → best resources
/practice      → practice questions
/quiz          → test knowledge
/mistakes      → common mistakes
/summary       → summarize topic
/revision      → quick revision
/notes         → structured notes
/examples      → real examples
/explainwhy    → reasoning
```

### I8 — Personal Branding
```
/profile       → LinkedIn profile review
/headline      → headline ideas
/bio           → bio rewrite
/contentplan   → content calendar
/niche         → niche clarity
/audience      → target audience
/positioning   → brand positioning
/engagement    → increase engagement
/dms           → DM strategy
/growth        → growth strategy
```

### I9 — Career / Job Help
```
/resume        → improve resume
/interview     → interview Q&A
/mockinterview → simulate interview
/hr            → HR round answers
/portfolio     → project ideas
/roadmapcareer → career roadmap
/jobsearch     → job strategy
/referral      → referral message
/salary        → salary negotiation
/skills        → skills to learn
```

### I10 — Advanced Prompt Control (tom e formato)
```
/toneformal    → formal tone
/tonecasual    → casual tone
/persuasive    → convincing tone
/data          → include stats
/examplesonly  → only examples
/noexamples    → no examples
/limit         → limit words
/expandpoints  → expand each point
/bullet        → bullet format
/nobullet      → paragraph format
```

---

## CATEGORIA J — Wealth Protocol (godofprompt)

> Prompts avançados de riqueza e alavancagem. Usar quando o utilizador quiser analisar o seu modelo de negócio ou rendimentos.

### J1 — The Specific Knowledge Excavator
```
# ROLE:
You are a specific knowledge analyst trained on Naval Ravikant's wealth philosophy.
You reverse-engineer a person's unique intellectual fingerprint — the rare intersection
of obsessions, life detours, and undervalued skills that nobody else holds in the same combination.

# TASK:
Excavate my specific knowledge profile. Identify the knowledge stack I can build
a leveraged income around.

# STEPS:
1. Review my obsessions, career detours, and undervalued skills
2. Cross-reference all three to find the rare intersection
3. Name my specific knowledge niche in one sentence
4. Test it: "Could I be trained for this?" — if yes, discard and re-excavate
5. Propose 3 business models that turn this into leverage (code, media, or capital — not labor)
6. Score each model: market size (1-5), competition (1-5, lower is better), leverage multiplier (1-5)

# RULES:
- Reject generic niches (marketing, coaching, consulting) unless drilling into what makes mine different
- Each business model must specify which leverage type it uses
- Never suggest labor-based models — the goal is zero marginal cost to scale

# INFORMATION ABOUT ME:
- My obsessions (things I read about without being paid to): [LIST 3-5]
- My weird career path: [2-3 SENTENCES]
- Skills others compliment me on that I don't think are special: [LIST 2-3]

# OUTPUT FORMAT:
**Your Specific Knowledge Niche:** [One precise sentence]
**Why This is Rare:** [2-3 sentences]
**3 Leveraged Business Models:** Rank | Leverage Type | Market | Competition | Multiplier | Score
**Recommended Starting Point:** [Top model + first 3 steps]
```

### J2 — The Leverage Stack Auditor
```
# ROLE:
You are a leverage analyst operating on Naval Ravikant's four-lever framework:
labor, capital, code, and media.

# TASK:
Audit my current income streams and work activities. Show me where I have leverage
and where I'm leaking time.

# STEPS:
1. Map every income source and activity into one of four categories:
   Labor (time-for-money), Capital (money working), Code (automation/software), Media (content/audience)
2. Assign each a Leverage Score: 1 (pure time-for-money) to 5 (zero marginal cost to scale)
3. Calculate my overall Leverage Index — weighted average across revenue percentage
4. Identify my biggest leverage leak (most time consumed, least scale potential)
5. Propose 3 concrete upgrade moves to convert at least one Labor activity to Code or Media leverage within 30 days

# INFORMATION ABOUT ME:
- My income sources and hours per week on each: [LIST EACH + HOURS/WEEK]
- My monthly income target: [$AMOUNT]
- Main skills or assets I own: [LIST]

# OUTPUT FORMAT:
**Leverage Audit:** Activity | Leverage Type | Hours/Week | Score | Revenue %
**Your Leverage Index:** [X/5]
**Biggest Leverage Leak:** [Activity + why it's a trap + what it costs you]
**3 Upgrade Moves:** [Convert X to Y] — Score change — Timeline: [X days]
**30-Day First Move:** [Exact action to take this week]
```

### J3 — The Productize Yourself Blueprint
```
# ROLE:
You are a product architect specializing in converting knowledge workers into scalable operators.

# TASK:
Design a complete Productize Yourself blueprint. Convert my expertise into a scalable system —
one that works at 3am without me online.

# STEPS:
1. Identify the single most valuable transformation I can deliver
2. Map 3 product formats that deliver this transformation (digital product, tool, community, course, or other)
3. Score each format: leverage (sells without me), feasibility (buildable in 30 days), margin (above 70%)
4. Design the winning product: contents, delivery mechanism, what makes it irreplaceable
5. Identify one distribution channel that matches my existing specific knowledge
6. Write one positioning sentence I can use to launch

# INFORMATION ABOUT ME:
- My expertise and transformation I provide: [WHAT DO YOU HELP PEOPLE DO OR BECOME]
- My current platforms or audiences: [LIST — EVEN SMALL]
- Time available to build: [HOURS/WEEK]

# OUTPUT FORMAT:
**Your Core Transformation:** I help [WHO] go from [BEFORE] to [AFTER] using [NAMED METHOD]
**3 Product Formats:** Format | Leverage | Feasibility | Margin | Score
**Winning Product Structure:** Name, Contents, Delivery, Price point
**Launch Positioning Statement:** [One sentence]
**Week 1 Build Roadmap:** [3 tasks to start immediately]
```

### J4 — The Time-for-Money Leak Detector
```
# ROLE:
You are a wealth architect trained on Naval Ravikant's equity philosophy.
You expose the time-for-money traps that keep intelligent operators financially stuck —
and design escape paths that convert their skills into ownership.

# TASK:
Audit my work and income structure. Find every hour being rented instead of invested.
Then design the conversion.

# STEPS:
1. Categorize every work activity as: Time-Rented (paid per hour, project, or day)
   or Equity-Building (creates an asset that outlasts my effort)
2. Calculate my time-rent ratio — percentage of working hours building things I own
3. For each time-rented activity, identify what transformation or outcome the buyer actually wants
4. Show how each could be converted to an equity-building equivalent
5. Rank conversions by: effort to convert (low/medium/high) and leverage potential (1-5)

# RULES:
- Hourly work, freelancing, and employment are time-rented — no exceptions regardless of rate
- An activity is equity-building only if stopping it for 6 months doesn't stop the income
- Flag retainer clients who require weekly live calls — these are time-rent disguised as passive income

# INFORMATION ABOUT ME:
- My current work activities and how I'm compensated for each: [DESCRIBE EACH]
- Total hours worked per week: [NUMBER]
- Current income split (active vs passive, approximate): [% / %]

# OUTPUT FORMAT:
**Time Audit:** Activity | Type | Hours/Week | Equity Potential | Conversion Difficulty
**Your Time-Rent Ratio:** [X% rented / Y% equity-building]
**Top 3 Conversion Opportunities:** [Activity] → [Equity equivalent] — Effort — Leverage
**The Equity Gap:** [What your income could look like in 2 years if you convert the top opportunity]
**First Escape Move:** [One action to start this week]
```

---

## CATEGORIA C (ACTUALIZAÇÃO) — Novas Skills Claude Code

> Adicionadas ao lote existente de plugins/skills (@0verlens)

### Novas Skills via npx/plugin
| Nome | Comando | Descrição |
|---|---|---|
| UI-UX PRO MAX | `/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill` | Design thinking real, hierarquia visual, psicologia das cores |
| Emil Kowalski Design | `npx skills add emilkowalski/skill` | Animações, design, código, performance (baseado nos artigos do Emil) |
| App Store Design | `npx skills add ParthJadhav/app-store-screenshots` | Screenshots prontos para App Store iOS em todas as resoluções |
| Garry Tan Gstack | `https://github.com/garrytan/gstack.git` | Avalia design 0-10, detecta "AI Slop", pergunta ao utilizador em cada escolha |
