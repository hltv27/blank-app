# Wallu — Project Documentation

## What this is

Wallu is a privacy-first personal finance web app built with Next.js. All data lives in `localStorage` — no backend, no accounts, no data sent anywhere. Target market: privacy-conscious Europeans who want a clean, visual alternative to bloated finance apps.

**Positioning**: Privacy-first + European-native + multi-asset portfolio tracking at €4.99/month vs competitors at €12–18/month.

---

## Stack

- **Framework**: Next.js App Router (started with `--webpack` flag — no Turbopack, required for Android/Termux/arm64)
- **Language**: TypeScript strict mode
- **Styling**: Tailwind CSS v4 (`@import "tailwindcss"`) + CSS custom properties for theming
- **Icons**: Lucide React
- **Charts**: Recharts (AreaChart)
- **i18n**: Custom `LangProvider` + `useT()` hook + JSON translation files

**Run command** (inside `wallu/`):
```bash
npm run dev -- --webpack
```

---

## Repository layout

```
blank-app/
  wallu/                  ← Next.js app root
    app/
      page.tsx            ← Dashboard
      layout.tsx          ← Root layout (server component, uses Providers)
      subscriptions/page.tsx
      finances/page.tsx
      portfolio/page.tsx
      goals/page.tsx
      settings/page.tsx
      globals.css         ← Dark theme, CSS vars, layout classes
      api/                ← Proxy routes (CoinGecko, Alternative.me, RSS)
        converter/
    components/
      Providers.tsx        ← Client wrapper: LangProvider + Sidebar + BottomNav
      Sidebar.tsx          ← Desktop nav (uses useT)
      BottomNav.tsx        ← Mobile nav (uses useT)
      AddSubscriptionModal.tsx
      StatCard.tsx
      UpcomingRenewals.tsx
    lib/
      types.ts             ← TypeScript interfaces
      store.ts             ← localStorage helpers + formatCurrency (en-US locale)
      data.ts              ← POPULAR_SERVICES, CATEGORY_LABELS, DEFAULT_TRANSACTIONS
      goals.ts             ← SavingsGoal type, getGoals/saveGoals, DEFAULT_GOALS
      portfolio.ts         ← Portfolio localStorage helpers
      i18n.tsx             ← LangProvider, useT, useLang, LANGUAGES list
    messages/
      en.json              ← Base language (English)
      pt.json              ← Português
      es.json              ← Español
      fr.json              ← Français
      de.json              ← Deutsch
      zh.json              ← 中文 (Simplified)
      hi.json              ← हिन्दी
      ar.json              ← العربية (RTL)
      ru.json              ← Русский
      ja.json              ← 日本語
```

---

## i18n system

**How it works**:
1. `wallu/lib/i18n.tsx` imports all 10 JSON files statically
2. `flatten()` converts nested JSON to dot-notation keys at module load: `{ "nav": { "dashboard": "..." } }` → `"nav.dashboard"`
3. `LangProvider` reads saved lang from `localStorage` key `wallu_lang`, sets `document.documentElement.lang/dir`
4. Arabic (`ar`) sets `dir="rtl"` on `<html>`
5. `useT()` returns `t(key, vars?)` — falls back to `en` if key missing, supports `{{varName}}` interpolation

**Adding translations**: Add the key to `messages/en.json` first, then add it to all other language files. Run the app to verify.

**Important — Recharts chart dataKeys**: Chart `dataKey` props must always use fixed English strings (defined in `CLASS_META` in `portfolio/page.tsx`), never translated labels. Translated display names are computed separately via `useT()`.

---

## Pages

### Dashboard (`app/page.tsx`)
- Stat cards: subscriptions/month, income, expenses, balance
- Upcoming renewals (next 30 days)
- Spending by category (bar chart)
- Recent transactions (last 5)

### Subscriptions (`app/subscriptions/page.tsx`)
- List with search + filter (all/active/paused)
- Add/edit modal (`AddSubscriptionModal.tsx`) with:
  - Quick-fill from 20+ popular services
  - Emoji, name, amount, billing cycle (monthly/yearly/weekly)
  - Next billing date, category, color picker
  - Crypto payment method selector (BTC, ETH, USDT, USDC, BNB, SOL, XRP, DOGE, ADA, AVAX)
  - Active/paused toggle

### Finances (`app/finances/page.tsx`)
- Stat cards: income, expenses, subscription cost, savings rate
- Monthly balance progress bar
- Add transaction form (description, amount, type, date, category, emoji)
- Transactions grouped by date

### Portfolio (`app/portfolio/page.tsx`)
- Area chart of total wealth over time (Cash, Crypto, ETFs, Stocks)
- Manage assets: crypto holdings, ETFs, stocks
- Crypto Fear & Greed Index (via Alternative.me proxy)
- Crypto/fiat converter (via CoinGecko proxy)
- News feed with 3 tabs: Crypto, Markets, Europe (RSS via rss2json proxy)
- AI Insights (rule-based, not actual AI)

### Goals (`app/goals/page.tsx`)
- Savings goals with progress rings
- Summary: total saved, overall %, completed count
- Per-goal: deposit inline, edit, delete
- Deadline tracking with color-coded urgency

### Settings (`app/settings/page.tsx`)
- **Language selector** — flags + names for all 10 languages, persisted to localStorage
- Profile (name/email, display only)
- Preferences (currency, month start day, renewal reminder days)
- Data export (JSON) and delete all data
- Plan selector: Free / Pro €4.99/mo / Lifetime €149
- Crypto payment wallets for plan upgrade

---

## Data model

```typescript
// lib/types.ts
type BillingCycle = 'monthly' | 'yearly' | 'weekly';
type Category = 'streaming' | 'music' | 'software' | 'gaming' | 'cloud' | 'news' | 'fitness' | 'food' | 'finance' | 'other';

interface Subscription {
  id: string; name: string; amount: number; currency: string;
  billingCycle: BillingCycle; nextBillingDate: string; category: Category;
  color: string; emoji: string; active: boolean; cryptoPayment?: string;
}

interface Transaction {
  id: string; description: string; amount: number;
  type: 'income' | 'expense'; category: string; date: string; emoji: string;
}

// lib/goals.ts
interface SavingsGoal {
  id: string; name: string; emoji: string; target: number; current: number;
  currency: string; deadline?: string; color: string;
}
```

**localStorage keys**: `wallu_subscriptions`, `wallu_transactions`, `wallu_goals`, `wallu_portfolio`, `wallu_lang`

---

## CSS theme

All colors via CSS custom properties in `globals.css`:
- `--bg`, `--surface`, `--surface2`, `--border`, `--text`, `--muted`
- `--accent` (#7C3AED purple), `--green` (#10B981), `--red` (#EF4444), `--yellow` (#F59E0B)

Key layout classes: `.main-content`, `.stats-grid`, `.dashboard-grid`, `.card`, `.btn-primary`, `.btn-ghost`, `.fade-in`, `.modal-in`

---

## Git

- **Repo**: `hltv27/blank-app`
- **Dev branch**: `claude/implement-think-command-2WiDI`
- **Push command**: `git push -u origin claude/implement-think-command-2WiDI`

---

## Pricing (agreed)

| Plan | Price |
|------|-------|
| Free | €0 (max 5 subscriptions, basic features) |
| Pro | €4.99/month |
| Yearly | €49.99/year |
| Lifetime | €149 one-time |

---

## Planned features (not yet built)

- **Wallu Score**: 0–100 financial health gamification
- **FIRE Dashboard**: Financial Independence / Retire Early calculator
- **Subscription Intelligence**: price change alerts, overlap detector, subscription weight %
- **P&L chart**: profit/loss per portfolio asset
- **Auto savings suggestion**: monthly amount needed to hit goal by deadline
- **Cash flow forecast**: "what will my balance be on the 28th?"
- **Bengali (bn)**: 11th language, not yet added (current: en/pt/es/fr/de/zh/hi/ar/ru/ja)
