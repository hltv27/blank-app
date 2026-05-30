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

---

## CATEGORIA E (EXTENSÃO) — Análise Avançada de Mercados (@uncover.ai)

> Prompts de nível institucional para análise profunda de investimento.

### E11 — BlackRock-Style Portfolio Construction
```
"You are a senior portfolio strategist at BlackRock managing multi-asset portfolios worth $500M+ for institutional clients.
I need a custom investment portfolio built from scratch for my situation.

Create:
• Exact asset allocation with percentages across stocks, bonds, alternatives
• Specific ETF or fund recommendations for each category with ticker symbols
• Core holdings vs satellite positions clearly labeled
• Expected annual return range based on historical data
• Expected maximum drawdown in a bad year
• Rebalancing schedule and trigger rules
• Tax efficiency strategy for my account type
• Dollar cost averaging plan if I invest monthly
• Benchmark to measure my performance against
• One-page investment policy statement I can follow

Format as a professional investment policy document with an allocation pie chart description.

My details: [DESCRIBE YOUR AGE, INCOME, SAVINGS, GOALS, RISK TOLERANCE, AND ACCOUNT TYPE - 401K, IRA, TAXABLE]"
```

### E12 — Citadel-Grade Technical Analysis System
```
"You are a senior quantitative trader at Citadel who combines technical analysis
with statistical models to time entries and exits.

I need a full technical analysis breakdown of a stock. Analyze:
• Current trend direction on daily, weekly, and monthly timeframes
• Key support and resistance levels with exact price points
• Moving average analysis (50-day, 100-day, 200-day) and crossover signals
• RSI, MACD, and Bollinger Band readings with plain-English interpretation
• Volume trend analysis and what it signals about buyer/seller strength
• Chart pattern identification (head and shoulders, cup and handle, etc.)
• Fibonacci retracement levels for potential bounce zones
• Ideal entry price, stop-loss level, and profit target
• Risk-to-reward ratio for the current setup
• Confidence rating: strong buy, buy, neutral, sell, strong sell

Format as a technical analysis report card with a clear trade plan summary.

The stock to analyze: [ENTER TICKER SYMBOL AND YOUR CURRENT POSITION IF ANY]"
```

### E13 — Harvard Endowment Dividend Strategy
```
"You are the chief investment strategist for Harvard's $50B endowment fund
specializing in income-generating equity strategies.

I need a dividend income portfolio that generates reliable passive income.

Build:
• 15-20 dividend stock picks with ticker symbols and current yield
• Dividend safety score for each stock (1-10 scale)
• Consecutive years of dividend growth for each pick
• Payout ratio analysis to flag any unsustainable dividends
• Monthly income projection based on my investment amount
• Sector diversification breakdown to avoid concentration
• Dividend growth rate estimate for the next 5 years
• DRIP reinvestment projection showing compounding over 10 years
• Tax implications summary for dividends in my account type
• Ranked list from safest to most aggressive picks

Format as a dividend portfolio blueprint with an income projection table.

My situation: [ENTER YOUR TOTAL INVESTMENT AMOUNT, MONTHLY INCOME GOAL, ACCOUNT TYPE, AND TAX BRACKET]"
```

### E14 — Bain-Style Competitive Advantage Analysis
```
"You are a senior partner at Bain & Company conducting a competitive strategy analysis
for a major investment fund evaluating an industry.

I need a full competitive landscape report to find the best stock to buy in a sector.
Provide:
• Top 5-7 competitors in the sector with market cap comparison
• Revenue and profit margin comparison in a table format
• Competitive moat analysis for each company (brand, cost, network, switching)
• Market share trends over the last 3 years
• Management quality rating based on capital allocation track record
• Innovation pipeline and R&D spending comparison
• Biggest threats to the sector (regulation, disruption, macro)
• SWOT analysis for the top 2 companies
• My single best stock pick with a clear rationale
• Catalysts that could move the winner stock in the next 12 months

Format as a Bain-style competitive strategy deck summary with comparison tables.

The sector I want analyzed: [ENTER INDUSTRY OR SECTOR NAME]"
```

### E15 — Renaissance Technologies Pattern Finder
```
"You are a quantitative researcher at Renaissance Technologies using data-driven methods
to find statistical edges in the stock market.

I need you to identify hidden patterns and anomalies in a stock's behavior.

Research:
• Seasonal patterns: best and worst months historically
• Day-of-week performance patterns if any exist
• Correlation with major market events (Fed meetings, CPI reports)
• Insider buying and selling patterns from recent filings
• Institutional ownership trend: are big funds buying or selling
• Short interest analysis and squeeze potential
• Unusual options activity signals worth watching
• Price behavior around earnings (pre-run, post-gap patterns)
• Sector rotation signals that affect this stock
• Statistical edge summary: what gives this stock a quantifiable advantage

Format as a quantitative research memo with data tables and pattern summaries.

The stock to investigate: [ENTER TICKER SYMBOL AND TIME PERIOD YOU CARE ABOUT]"
```

### E16 — McKinsey-Level Macro Impact Assessment
```
"You are a senior partner at McKinsey's Global Institute who advises sovereign wealth funds
on how macroeconomic trends affect equity markets.

I need a macro analysis showing how current economic conditions affect my portfolio.

Analyze:
• Current interest rate environment and its impact on growth vs value stocks
• Inflation trend analysis and which sectors benefit or suffer
• GDP growth forecast and what it means for corporate earnings
• US dollar strength impact on international vs domestic holdings
• Employment data trends and consumer spending implications
• Federal Reserve policy outlook for the next 6-12 months
• Global risk factors (geopolitics, trade wars, supply chains)
• Sector recommendation based on current economic cycle
• Specific portfolio adjustments I should consider right now
• Timeline: when these macro factors will most likely impact markets

Format as an executive macro strategy briefing with a clear action plan.

My current holdings: [LIST YOUR PORTFOLIO AND DESCRIBE YOUR BIGGEST CONCERN ABOUT THE ECONOMY]"
```

---

## CATEGORIA K — Claude Code: Memória & Automação (@construyendoia)

> Prompts para dar ao Claude Code memória persistente, personalidade e automação.

### K1 — Sistema de Memória Persistente
```
"Crea un sistema de memoria persistente para mí.
Haz un directorio /memory con estos archivos: decisions.md, people.md, preferences.md y user.md.
Luego escribe un CLAUDE.md que le indique leer todos esos archivos al inicio de cada sesión,
y crea un hook que los actualice al terminar."
```

### K2 — Dar Personalidade ao Claude Code
```
"Lee todo lo que hay en mi directorio /memory y escribe un personality.md
que defina cómo debes pensar, comunicarte y tomar decisiones cuando trabajas conmigo.
Basate únicamente en los patrones que observes en mis archivos.
Este archivo se convierte en tu personalidad para cada sesión futura.
Información adicional: [agrega aquí cualquier dato relevante]"
```

### K3 — Briefing Matutino Automatizado
```
"Configura un briefing matutino automatizado usando las tareas programadas de Claude Code.
Cada día a las 8am debes: leer mis archivos /memory, revisar active.md en /todos,
resumir en qué estaba trabajando y generar mis 3 prioridades del día.
Luego envía el briefing a mi Slack como DM usando un webhook.
Guarda la URL del webhook en mi archivo .env como SLACK_WEBHOOK_URL."
```

### K4 — Dashboard de Tarefas em Tempo Real
```
"Constrúyeme un dashboard de tareas en tiempo real usando Next.js y Supabase.
Crea una tabla 'todos' en Supabase con los campos: title, status, priority, assigned_agent y updated_at.
Activa Supabase Realtime en la tabla para que la interfaz se actualice automáticamente
vía websockets, sin recargar la página.
Cuando un agente complete una tarea, debe actualizar el estado directamente en Supabase
y el dashboard lo refleja al instante.
Estilo: oscuro, minimalista y limpio."
```

---

## CATEGORIA L — YouTube & Conteúdo Faceless (@razvanpbusiness)

> Prompts para canais YouTube sem rosto. Usar quando o utilizador quiser criar conteúdo vídeo.

### L1 — Competitor Channel Analysis
```
"You are a YouTube channel intelligence analyst specializing in faceless content.
I am building a faceless YouTube channel in the [NICHE] space.

Analyze the following competitor channels: [CHANNEL 1], [CHANNEL 2], [CHANNEL 3]

For each channel, break down:
- Their core content pillars and what topics they return to most
- Upload cadence and how it affects their growth trajectory
- Their best-performing video formats (listicles, explainers, docustyle, etc.)
- Thumbnail and title patterns that appear across their top 20 videos
- Gaps in their content — topics their audience asks about but they never cover
- Comment section sentiment: what do viewers love, complain about, or wish existed

Finish with a strategic opportunity map: where can a new channel enter this space,
differentiate, and grow fastest without directly competing."
```

### L2 — Viral Idea Finding
```
"You are a viral content strategist for faceless YouTube channels.
My channel is in the [NICHE] space and targets [TARGET AUDIENCE].

Generate 20 video ideas with genuine viral potential. For each idea:
- Write a working title using a proven psychological trigger (curiosity gap, controversy, fear of missing out, status, or forbidden knowledge)
- Explain in one sentence WHY this idea would make someone stop scrolling and click
- Identify the emotional hook: what feeling drives the click (shock, validation, aspiration, outrage, fear)?
- Rate its monetization ceiling (low/medium/high) based on advertiser interest in this topic

Prioritize ideas that: have search volume AND trending momentum, can be produced without original footage,
and have a clear narrative arc. Flag any ideas that have been overdone and suggest a fresh angle instead."
```

### L3 — Choosing The Right Title
```
"You are a content strategist and data analyst for faceless YouTube channels.
I have the following video ideas I am considering for my next upload:

[PASTE YOUR LIST OF IDEAS]

Score each idea across five dimensions on a scale of 1 to 10:
1. Search demand — is there an existing audience actively searching for this?
2. Trend velocity — is interest growing, stable, or declining right now?
3. Competition density — how saturated is this topic on YouTube?
4. Production feasibility — how easily can this be made without original footage or a face?
5. Monetization value — would advertisers pay premium CPM for this content?

Calculate a weighted total score (search demand x2, trend velocity x2, others x1).

Recommend the top 2 ideas to pursue now and explain your reasoning.
For the winner, outline the ideal angle, target keyword, and the one thing that will make this video
stand out from everything else already ranking."
```

### L4 — Studying Viral Transcripts
```
"You are a YouTube content forensics expert.
I am going to give you the transcript of a viral video from my niche that performed exceptionally well.

[PASTE TRANSCRIPT]

Reverse engineer why this video worked by analyzing:
- The hook structure: what happens in the first 30 seconds and why it earns the next click-through?
- Pacing and information density: how does the script balance revelation, tension, and payoff throughout?
- Retention mechanics: where does the script re-hook the viewer and how (open loops, pattern interrupts, stakes escalation)?
- Language and tone: what vocabulary, sentence length, and emotional register does the script use?
- The story architecture: does it follow a specific narrative framework (problem-agitate-solve, hero journey, countdown, etc.)?"
```

### L5 — Writing Viral Scripts
```
"You are a professional YouTube scriptwriter specializing in high-retention faceless content.
Write a full script for the following video:

Topic: [VIDEO TOPIC]
Target length: [X] minutes
Tone: [authoritative / conversational / dramatic / investigative]
Target audience: [DESCRIBE AUDIENCE]

Script requirements:
- Open with a hook that creates an immediate curiosity gap or emotional trigger — no intros, no channel plugs, no 'welcome back'
- Every 60 to 90 seconds, plant a new open loop or raise the stakes to protect retention
- Write in short punchy sentences designed to be read aloud — no walls of text
- Include [B-ROLL CUE] markers throughout suggesting what footage or graphics should appear on screen"
```

### L6 — Thumbnail and Title Analysis
```
"You are a YouTube thumbnail and title conversion specialist.
My video is about [TOPIC] and targets [AUDIENCE].

Analyze the top 10 performing thumbnails in this niche based on the following competitor videos:
[LIST VIDEO TITLES OR URLS]

Break down:
- The visual formula: what elements appear repeatedly (faces, text overlays, color schemes, arrows, contrast ratios, negative space usage)?
- Emotional cues: what psychological state does the thumbnail create — curiosity, fear, excitement, disbelief?
- Text strategy: how much text is used, where is it placed, and what font weight and color patterns dominate?
- The clickable moment: what single visual element is doing the most work in driving the click?

Then for my video, generate thumbnail and title recommendations."
```

---

## CATEGORIA E (EXTENSÃO 2) — Análise Avançada de Mercados (@uncover.ai)

### E17 — JPMorgan-Level Earnings Breakdown
```
"You are a senior research analyst at JPMorgan preparing a pre-earnings research brief
for institutional clients before a major company reports quarterly results.

I need a full pre-earnings breakdown for [COMPANY NAME] ([TICKER]).

Deliver:
• Consensus EPS estimate and revenue forecast with analyst range
• The company's historical earnings beat/miss rate for the last 8 quarters
• The 3 most important metrics Wall Street is watching this quarter (not just EPS)
• Guidance analysis: what did management say last quarter and was it credible?
• Key risks that could cause a miss this quarter
• One bullish scenario and one bearish scenario with price targets for each
• Options market implied move: how much the stock is expected to move on earnings day
• My single recommendation: buy before earnings, wait until after, or avoid entirely

Format as a JPMorgan earnings preview note with a clear actionable summary at the top.

Company to analyze: [ENTER COMPANY NAME, TICKER, AND EARNINGS DATE]"
```

### E18 — Bridgewater-Inspired Risk Analysis Framework
```
"You are a senior risk analyst at Bridgewater Associates applying Ray Dalio's All Weather
and Pure Alpha risk frameworks to evaluate a portfolio's resilience.

I need a full risk analysis for my current portfolio.

Assess:
• Correlation matrix: how do my holdings move together in a downturn?
• Concentration risk: which single position or sector could hurt me most?
• Stress test results: what happens to my portfolio if specific crisis scenarios occur?
• Factor exposure: am I unknowingly overweight growth, leverage, or rate sensitivity?
• Liquidity risk: which positions would be hardest to exit in a panic market?
• Tail risk events: what low-probability, high-impact events threaten my portfolio?
• Hedging recommendations: specific instruments to protect against my top 3 risks
• Portfolio balance score: am I truly diversified or just holding correlated assets?
• Drawdown simulation: estimated max loss in a 2008-style or 2020-style crash
• Action plan: the 3 changes that would reduce my risk the most right now

Format as a Bridgewater risk memo with a risk dashboard summary table.

My portfolio: [LIST YOUR HOLDINGS WITH PERCENTAGES AND TOTAL PORTFOLIO SIZE]"
```

### E19 — Morgan Stanley-Style DCF Valuation Deep Dive
```
"You are a senior equity analyst at Morgan Stanley conducting a discounted cash flow
valuation for a major institutional client considering a significant investment.

I need a complete DCF valuation for [COMPANY NAME] ([TICKER]).

Build:
• 5-year revenue growth forecast with bull, base, and bear case assumptions
• EBITDA margin trajectory and operating leverage analysis
• Free cash flow projection for each year across all 3 scenarios
• WACC calculation with cost of equity and debt components explained
• Terminal value using both exit multiple and perpetuity growth methods
• Intrinsic value per share for bull, base, and bear scenarios
• Current price vs intrinsic value: is the stock cheap, fair, or expensive?
• Sensitivity table showing how value changes with different growth and margin assumptions
• Key risks that would invalidate the bull case thesis
• My verdict: buy, hold, or sell, and at what price would I change my view

Format as a Morgan Stanley equity research DCF model summary with scenario table.

Company to value: [ENTER COMPANY NAME, TICKER, AND ANY SPECIFIC CONCERNS YOU HAVE]"
```

### E20 — Goldman Sachs-Level Stock Screener
```
"You are a senior portfolio strategist at Goldman Sachs running a quantitative screen
to find the top 10 stocks most likely to outperform the market over the next 12 months.

Screen for stocks that meet these criteria:
• Revenue growth above sector average for the last 4 quarters
• Net profit margin expanding year-over-year
• Free cash flow positive with a FCF yield above X%
• Price-to-earnings ratio below the sector median or justified by growth
• Return on equity above 15% consistently
• Low debt-to-equity ratio relative to peers
• Institutional ownership increasing over the last 2 quarters
• Management with strong capital allocation track record (buybacks, dividends, M&A)
• Identifiable economic moat (brand, cost, network, switching, or regulatory)
• A clear near-term catalyst in the next 3-6 months

For each of the top 10 stocks found:
• Give the ticker, sector, and one-line thesis
• Price target with bull and bear case
• The single biggest risk to owning this stock

Format as a Goldman Sachs conviction list with a ranking rationale.

My filters: [ENTER YOUR PREFERRED MARKET CAP RANGE, SECTORS TO INCLUDE OR EXCLUDE, AND GEOGRAPHIC PREFERENCE]"
```

---

## CATEGORIA M — Aprendizagem & Documentos (@create_daniel2)

> Prompts para transformar documentos, PDFs e conteúdo complexo em material de estudo organizado.

### M1 — Mapa Mental Automático
```
"Transforma este [DOCUMENTO/PDF/TEXTO] num mapa mental completo e estruturado.

Cria uma hierarquia visual clara:
• Tópico central no centro
• Ramos principais para cada conceito-chave
• Sub-ramos com detalhes, exemplos e definições
• Conexões entre ramos relacionados claramente indicadas
• Código de cores sugerido para cada categoria principal

Formato: usa indentação e símbolos para simular a estrutura visual do mapa mental.
Inclui no final um resumo de 3 frases sobre os conceitos mais importantes.

[COLA O TEU DOCUMENTO AQUI]"
```

### M2 — Conceitos-Chave & Definições Essenciais
```
"Analisa este [DOCUMENTO/PDF/TEXTO] e extrai todos os conceitos-chave e definições essenciais.

Para cada conceito encontrado:
• Nome do conceito em negrito
• Definição clara e simples em 1-2 frases
• Exemplo prático do mundo real
• Por que é importante saber isto
• Como se relaciona com outros conceitos do documento

Organiza por ordem de importância (mais fundamental primeiro).
No final, cria um glossário rápido de referência.

[COLA O TEU DOCUMENTO AQUI]"
```

### M3 — Simplificar Conteúdo Difícil
```
"Pega neste [DOCUMENTO/PDF/TEXTO] complexo e simplifica-o para que alguém sem
conhecimento técnico da área o possa entender completamente.

Faz isto:
• Reescreve cada secção em linguagem simples e directa
• Substitui jargão técnico por explicações do quotidiano
• Usa analogias e metáforas para conceitos abstractos
• Adiciona exemplos concretos onde o texto é vago
• Destaca os 5 pontos mais importantes que o leitor DEVE reter
• Termina com um resumo de 1 parágrafo como se explicasses a um amigo

[COLA O TEU DOCUMENTO AQUI]"
```

### M4 — Aulas Estruturadas por Capítulo
```
"Transforma este [DOCUMENTO/PDF/LIVRO] numa série de aulas estruturadas e progressivas.

Para cada capítulo/secção, cria:
• Título da aula e objectivo de aprendizagem
• Resumo dos conceitos principais (bullet points)
• Explicação aprofundada dos pontos mais importantes
• 3-5 perguntas de revisão para testar a compreensão
• Exercício prático ou aplicação do conteúdo
• Ligação ao próximo capítulo/conceito

Organiza as aulas por ordem de dificuldade crescente.
No início, cria um índice com estimativa de tempo por aula.

[COLA O TEU DOCUMENTO AQUI]"
```

### M5 — Ensina-me do Zero
```
"Usa este [DOCUMENTO/PDF/TEXTO] para me ensinar [TÓPICO] do zero, assumindo que não sei nada sobre o assunto.

Segue esta progressão pedagógica:
1. Contexto: Porquê é que este assunto importa? Qual o problema que resolve?
2. Fundamentos: As 3-5 ideias base que preciso de entender primeiro
3. Desenvolvimento: Como os conceitos se constroem uns sobre os outros
4. Aplicação: Exemplos práticos e casos de uso reais
5. Síntese: Como tudo se liga numa visão coerente
6. Próximos passos: O que devo estudar a seguir para aprofundar

Usa o método socrático quando relevante — faz-me perguntas para consolidar o conhecimento.
Tom: paciente, claro, encorajador.

[COLA O TEU DOCUMENTO AQUI]"
```

---

## CATEGORIA N — Travel Hacking & Voos Baratos (@entrepreneurshipquotes)

> Prompts para encontrar voos baratos, explorar brechas de preços e optimizar viagens.

### N1 — Hidden Route Scanner
```
"You are an expert flight hacker who finds cheap routes that most travelers miss.

I want to fly from [ORIGIN] to [DESTINATION] around [DATE RANGE].

Find hidden route options by:
• Identifying indirect routes with connections that cost significantly less than direct
• Spotting nearby alternative airports within 2-3 hours that could save money
• Finding positioning flights: cheap flights to a hub where better deals originate
• Checking if splitting the trip into 2 separate one-way tickets beats round-trip pricing
• Identifying open-jaw routes (fly into one city, out of another) that unlock cheaper fares
• Flagging any lesser-known carriers operating this corridor that aggregators often miss

For each option found: total travel time, total cost estimate, and the catch (if any).
Rank by best value considering time vs money trade-off.

My constraints: [ENTER YOUR BUDGET, MAX TRAVEL TIME, AND ANY FLEXIBILITY IN DATES OR AIRPORTS]"
```

### N2 — Price Manipulation Detector
```
"You are a pricing analyst who understands how airlines manipulate fares using dynamic pricing algorithms.

I am trying to book a flight for [ROUTE] on [DATE].

Expose the pricing tricks airlines use and how to beat them:
• Cookie and browser history manipulation: does clearing cookies actually change prices?
• Device and location pricing differences: do prices vary by mobile vs desktop?
• Time-of-day pricing patterns: when do airlines typically drop prices in a 24-hour cycle?
• Day-of-week purchase patterns: which day is statistically cheapest to buy tickets?
• How far in advance to buy for this specific route type (short-haul vs long-haul)
• Flash sales and error fare patterns: when and where do they appear?
• How to set price alerts correctly without triggering demand detection

Give me an action plan: exactly what steps to take in what order to book this flight at the lowest possible price.

My situation: [ENTER ROUTE, TRAVEL DATE, CURRENT PRICE YOU FOUND, AND HOW FLEXIBLE YOU ARE]"
```

### N3 — Geo-Pricing Bypass
```
"You are a travel hacker specializing in geographic price discrimination by airlines.

I need to check if airlines are charging different prices based on the country of purchase.

Investigate:
• Which countries or regions typically show cheaper fares for my route
• How to safely use a VPN to access foreign booking sites
• Which foreign airline websites to check directly (not just aggregators)
• How to pay without foreign transaction fees when booking from another country's site
• Currency conversion strategy: book in which currency for the best rate
• Whether the fare difference is real or cancelled out by taxes and fees
• Risks: can the airline cancel a ticket booked via geo-arbitrage?

Provide a step-by-step geo-pricing check routine I can run in 15 minutes for any flight.

My route: [ENTER ORIGIN, DESTINATION, DATE, AND CURRENT BEST PRICE FOUND]"
```

### N4 — Timing Sweet Spot Finder
```
"You are a data analyst specialized in airline fare timing patterns.

I need to book a flight for [ROUTE] and want to buy at the perfect moment.

Analyze timing strategy:
• The typical booking window sweet spot for this route type (domestic vs international)
• How prices move in the days leading up to departure for this kind of flight
• Best months to fly this route for lowest fares historically
• How school holidays, local events, and peak seasons affect prices on this corridor
• Whether last-minute deals exist for this route or if it tends to sell out expensive
• The 72-hour rule: do prices drop 3 days before departure on this route?
• Red-eye and off-peak timing discounts available for this flight

Deliver a personalized booking timeline: book by [DATE] to avoid price spikes, watch for drops around [DATE].

My details: [ENTER ROUTE, DESIRED TRAVEL DATES, HOW FAR IN ADVANCE YOU ARE PLANNING, AND FLEXIBILITY]"
```

### N5 — Fare Rule Exploiter
```
"You are an airline fare rules expert who knows how to use ticket rules to maximize flexibility and value.

I need to understand the fare rules for the cheapest tickets available for [ROUTE].

Break down:
• Refundability: under what conditions can I get money back?
• Change fees: how much does it cost to change dates, and are there free change windows?
• Name change policy: can the ticket be transferred if I can no longer travel?
• Fare class upgrades: which fare class gets me lounge access or priority boarding for the least extra cost?
• Stopovers and open jaws: does this ticket allow a free or cheap stopover in the connecting city?
• Mileage accrual: which loyalty program benefits from this ticket most?
• Hidden city ticketing risk: is it applicable here and what are the consequences?

Recommend the specific fare class and booking conditions I should look for when purchasing.

My route and needs: [ENTER ROUTE, TRAVEL DATE, WHETHER YOU NEED FLEXIBILITY, AND YOUR LOYALTY PROGRAM]"
```

### N6 — Airline vs OTA Comparison
```
"You are a consumer travel advocate who knows when to book directly with airlines vs third-party platforms.

I found a flight from [ORIGIN] to [DESTINATION] on [DATE].
Current prices: [AIRLINE WEBSITE PRICE] direct vs [OTA NAME] at [OTA PRICE].

Compare booking channels:
• Price difference after all fees: is the OTA actually cheaper when everything is included?
• Flexibility comparison: which channel offers easier changes, cancellations, and refunds?
• Customer service in a disruption: who will help me faster if the flight is cancelled?
• Seat selection and ancillary fees: which channel makes it cheaper to add bags, seats, meals?
• Loyalty points: does booking via OTA forfeit airline miles or status credits?
• Payment protection: does one channel offer better credit card protection?
• The hidden risks of OTA booking: itinerary changes, refund delays, double-booking errors

Final verdict: book direct or via OTA, and exactly where to click to get the best deal.

My situation: [PASTE THE FLIGHT DETAILS AND PRICES YOU FOUND ON EACH PLATFORM]"
```

### N7 — Price Drop Watch Strategy
```
"You are a flight deal monitoring expert who knows how to track prices and buy at the right moment.

I want to monitor prices for [ROUTE] around [DATE RANGE] and buy when the price drops.

Build me a monitoring system:
• Which price alert tools to use (Google Flights, Kayak, Hopper, Skyscanner) and how to set them up correctly
• What price threshold to set as my target and why
• How often prices typically fluctuate for this route in my booking window
• Signs that a price is about to drop vs about to spike
• How to avoid alert fatigue: filter for real deals vs normal fluctuations
• When to stop waiting and just book: the data-driven cut-off point
• How to use airline newsletter deals and mistake fare alerts for this route

Create a 30-day monitoring plan with weekly check-in actions I should take.

My situation: [ENTER ROUTE, TRAVEL DATE, CURRENT PRICE, BUDGET TARGET, AND HOW FAR OUT YOUR TRAVEL DATE IS]"
```

---

## CATEGORIA L (EXTENSÃO) — YouTube Simples (@create_daniel2)

> Prompts directos para criar e crescer um canal YouTube. Complementam os prompts avançados de L1-L6.

### L7 — Viral YouTube Video Ideas
```
"I want to create a YouTube channel about [insert niche].
Generate a list of 10 video ideas that could go viral, based on current trends,
hot topics, and what's working best in my niche right now."
```

### L8 — Viral YouTube Video Script
```
"Write a YouTube video script for my idea on [insert topic].
Make sure to include a strong hook to grab attention, an interesting story to keep people watching,
and a persuasive call to action that boosts engagement."
```

### L9 — YouTube Channel Automation
```
"I want to start a faceless YouTube channel in [niche].
Show me how to use ChatGPT for writing scripts, AI voices for narration, stock footage,
and editing tools to automate everything and generate passive income."
```

### L10 — Boost YouTube Video Views (SEO)
```
"Review the latest YouTube SEO trends and create a high-ranking video title, description,
and tags for my video on [insert video topic].
Make sure it's designed to grab attention and perform well in search results."
```

### L11 — Irresistible YouTube Video Hook
```
"Help me craft a catchy 15-second intro for my YouTube video on [insert video topic].
Make it attention-grabbing so viewers get hooked right away and want to keep watching."
```

### L12 — 30-Day YouTube Growth Strategy
```
"I'm launching a new YouTube channel about [niche].
Help me create a 30-day plan with video ideas, an upload schedule, strategies to grow my audience,
and ways to start monetizing."
```

### L13 — Repurpose YouTube Content
```
"I have a YouTube video about [insert topic].
Show me how to turn this video into a blog post, Instagram reel, TikTok, and Threads
to increase my reach and revenue."
```

---

## CATEGORIA O — Instagram & Theme Pages (@abundancewithchelsea + @wizofai)

> Prompts para criar, crescer e monetizar páginas de Instagram sem rosto (theme pages).

### O1 — Niche Finder
```
"List 10 Instagram theme page niches with low competition, high growth potential,
and strong monetization opportunities."
```

### O2 — Viral Content Blueprint
```
"For [chosen niche], give me 20 viral reel or carousel ideas I can recreate without showing my face."
```

### O3 — Caption Generator
```
"Write a viral-style Instagram caption with a strong hook and CTA for this post: [paste content idea]."
```

### O4 — Hashtag & Hook Formula
```
"Generate 15 high-performing hashtags and 5 scroll-stopping hook texts for my theme page in [niche]."
```

### O5 — Content Schedule
```
"Build me a 30-day content calendar for my theme page, optimized for engagement and growth."
```

### O6 — Monetization Map
```
"List 5 ways to monetize an Instagram theme page in [niche], including affiliates, shoutouts, and digital products."
```

### O7 — Automation Setup
```
"Show me how to batch content, schedule posts, and automate captions so my theme page runs on autopilot."
```

### O8 — Viral Instagram Content Ideas
```
"I want to create a faceless Instagram page about [insert niche].
Generate a list of 10 content ideas that could go viral, based on current trends,
hot topics, and what's working best in my niche right now."
```

### O9 — Viral Instagram Caption (Full)
```
"Write an Instagram caption for my post about [insert topic].
Make sure to include a strong hook to grab attention, an engaging story to keep people reading,
and a clear call to action that boosts engagement."
```

### O10 — Instagram Page Automation
```
"I want to start a faceless Instagram page in [niche].
Show me how to use ChatGPT for writing captions, AI tools for creating content,
and scheduling apps to automate everything and generate consistent cash-flow."
```

### O11 — Instagram Growth Strategy
```
"I'm launching a new faceless Instagram page about [niche].
Help me create a 30-day plan with content ideas, posting schedule,
strategies to grow my audience, and ways to start monetizing through promo posts and affiliate links."
```

### O12 — Instagram Reel Hook
```
"Help me craft a catchy 3-second hook for my Instagram reel about [insert topic].
Make it attention-grabbing so viewers stop scrolling immediately and want to keep watching."
```

### O13 — Repurpose Content Across Platforms
```
"I have an Instagram post about [insert topic].
Show me how to turn this post into different formats: Instagram reels, Stories, carousels,
and even adapt it for other platforms to maximize reach."
```

### O14 — Boost Instagram Engagement
```
"Analyze the current Instagram algorithm and create high-performing hashtags, caption structure,
and posting times for my faceless page in [niche] to maximize reach and engagement."
```

---

## CATEGORIA P — Produtividade & Objetivos (Google/Gemini + @gurudoprompt)

> Prompts para criar rotinas, alcançar metas e construir hábitos duradouros.

### P1 — Custom Workout Plan
```
"I want to run the New York City marathon in 6 months. I recently finished a half marathon in 2 hours,
and I can train 5 days a week.
Create a monthly training plan that will help me continue to build my endurance."
```

### P2 — Declutter Your Home
```
"I want to organize and declutter my apartment this month.
Create a 30-day plan that breaks the process into simple, daily tasks that take no more than 20 minutes each
and won't require me to purchase any new items."
```

### P3 — Learn a New Language
```
"I'd like to learn basic French.
Generate a 30-day guided learning plan for these topics and create an interactive multiple-choice quiz
on the verb conjugations. Please also generate a set of flashcards for the 50 phrases."
```

### P4 — Advance Your Career (Interview Prep)
```
"I have a job interview next week for [role].
Simulate a live, conversational interview with me, focusing on behavioral questions.
Second, create a detailed feedback report after I upload my video rehearsal,
analyzing my speaking pace, body language and use of filler words."
```

### P5 — Weekly Meal Plan
```
"I want to eat healthier. Every Sunday at 9 a.m., please create a 7-day, high-protein and vegetarian-friendly
dinner plan. I have about 45 minutes to cook each night. Include a grocery list for the week."
```

### P6 — Better Budget
```
"Analyze the uploaded Google Sheet containing my monthly spending for the last quarter
and identify 3 areas of non-essential spending.
Suggest practical weekly budgeting rules I can immediately implement to save 15%."
```

### P7 — Custom Reading List
```
"I want to read 12 business books in 2026.
Schedule a recurring action for the first of every month:
Suggest a list of 5 non-fiction titles related to advertising and create a sample monthly reading and review schedule."
```

### P8 — Replace a Bad Habit
```
"I want to reduce my phone screen time by 2 hours a week.
Outline a 'Habit Replacement Plan' that identifies my typical trigger times
and suggests a positive alternative activity for each."
```

### P9 — Overcome the Blank Page
```
"Give me 7 unique, one-sentence journaling prompts for the week
that encourage reflection on my goals and progress."
```

### P10 — Plan for Long-Term Success
```
"It's July 1st. I've successfully maintained my resolution to [resolution name] for 6 months.
Create a 3-part maintenance plan to help me make this a permanent habit
and set a bigger goal for the rest of 2026."
```

### P11 — Agenda Antifrágil de Alta Performance (@gurudoprompt)
```
"Você é meu Gestor de Tempo. Monte meu dia para render no caos.
Crie três blocos de foco profundo (50 min) e dois blocos leves (20-30 min) alinhados a {META_DO_DIA}.
Para cada bloco, entregue: objetivo claro, 3 passos, definição de 'pronto', risco provável e contramedida.
Insira micro-pausas (5 min) com respiração/alongamento, e um 'Plano B' de 15 min caso tudo desande.
Inclua: Regra 80/20 (o que eliminar), limites de comunicação (quando e como responder),
alarme de retorno ao foco e checklist anti-interrupção.
Gere versão 'intensa' e 'dias turbulentos'.
Finalize com placar do dia (3 métricas) e vitória mínima que me deixa satisfeito mesmo se o resto falhar."
```

### P12 — Plano de Estudos 14 Dias com Projeto-Âncora (@gurudoprompt)
```
"Seja meu Coach de Aprendizagem para {TEMA}.
Construa um plano de 14 dias (60-90 min/dia) focado em aprender fazendo.
Para cada dia, liste: objetivo, conteúdo essencial (links/tipos de fontes), prática ativa com correção,
quiz rápido e revisão espaçada.
Defina um projeto-âncora que comprove a habilidade em 2 semanas (escopo, critérios de avaliação, checklist).
Inclua mapa de competências, erros comuns, como detectar e corrigir, e rubrica de qualidade.
Crie ritual semanal: destilar → aplicar → ensinar (post curto explicando o aprendido).
Entregue também um template de anotações (captura atômica + Zettelkasten simples)
e métricas de retenção/aplicação."
```

---

## CATEGORIA E (EXTENSÃO 3) — Quick Investing Prompts (@theaiguyhere)

> Prompts de investimento directos e práticos para análise rápida.

### E21 — Market Analysis
```
"Analyze the current trends in the stock market, focusing on [input sector or stock].
Identify any emerging patterns and suggest potential investment opportunities.
Consider recent earnings reports and industry news in your analysis."
```

### E22 — Portfolio Diversification
```
"Given a portfolio with a mix of [input current sectors or stocks], suggest strategies to diversify further
while minimizing risk. Include potential sectors to explore and specific stocks to consider."
```

### E23 — Risk Management for Traders
```
"Discuss effective risk management techniques for a stock trader.
Provide detailed examples of how to implement stop-loss orders, diversification, and position sizing
in a trading strategy. Use [input current trading strategy or stock] as a reference."
```

### E24 — Technical Analysis Quick
```
"Using technical analysis, evaluate the stock of [input stock].
Analyze recent price movements, volume, and key indicators such as moving averages and RSI.
Provide a buy, sell, or hold recommendation."
```

### E25 — Value Investing
```
"Describe the principles of value investing and how to identify undervalued stocks.
Use real-world examples, including [input stock or company], to illustrate how investors
can apply this strategy in the current market."
```

### E26 — Growth Stock vs Dividend Stocks
```
"Compare and contrast growth stocks and dividend stocks.
Discuss the benefits and risks of each type of investment and suggest scenarios where one might be more suitable
than the other. Reference [input specific growth stock and dividend stock]."
```

---

## CATEGORIA H (ADIÇÃO 2) — Truth Protocol System (@coleenoteroceo / @create_daniel2)

### H6 — Truth Protocol System
```
"You are operating under the Truth Protocol System. Your rules are strict:
• Always tell the truth and use factual info.
• Base answers on verified, credible, and current information. Cite sources clearly when making factual claims.
• If information is uncertain or unavailable, explicitly say 'I cannot confirm this' instead of guessing.
• Never invent data, events, people, studies, or quotes.
• Do not speculate or present interpretations without strong supporting evidence, and always identify when you are doing so.
• Prioritize accuracy over speed or creativity.
• Provide step-by-step reasoning for complex answers.
• Show calculations when giving numbers or statistics.
• Be transparent about limitations and confidence levels in every response.

Failsafe Check (before every response):
• Internally ask yourself, 'Is every statement I'm about to provide true, sourced, and transparent?'
• If the answer is no, revise until it is yes."
```

---

## CATEGORIA H (ADIÇÃO) — FULL REPRINT RULE

### H5 — FULL REPRINT RULE
```
Sempre que fizeres uma alteração a um texto, e-mail, documento ou código, apresenta
SEMPRE a versão final completa num único bloco — nunca respostas parciais, nunca "o resto
fica igual", nunca snippets fragmentados.

Regra de ouro: se eu precisar de copiar/colar, deve funcionar na primeira tentativa,
sem ter de juntar peças ou reinterpretar o que ficou por escrever.

Como aplicar:
• Alteração de e-mail → mostra o e-mail completo reescrito
• Alteração de código → mostra o ficheiro ou função completa
• Alteração de documento → mostra a secção completa com o contexto necessário
• Revisão de texto → mostra o texto completo com todas as alterações integradas

Nunca digas "... (resto igual) ..." ou "... (sem alterações acima) ...".
Se for demasiado longo, divide em partes numeradas claramente delimitadas.
```
