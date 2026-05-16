'use client';

export type AssetClass = 'cash' | 'crypto' | 'etf' | 'stock';

export interface CryptoAsset {
  id: string;
  symbol: string;
  name: string;
  amount: number;
  emoji: string;
  walletAddress?: string;
  exchange?: string;
  currentPrice?: number;
}

export interface StockAsset {
  id: string;
  ticker: string;
  name: string;
  shares: number;
  emoji: string;
  broker?: string;
  currentPrice?: number;
  type: 'stock' | 'etf';
}

export interface PortfolioSnapshot {
  date: string;
  cash: number;
  crypto: number;
  etf: number;
  stock: number;
}

const CRYPTO_KEY = 'wallu_crypto';
const STOCKS_KEY = 'wallu_stocks';
const SNAPSHOTS_KEY = 'wallu_snapshots';
const PORTFOLIO_SEEDED = 'wallu_portfolio_seeded_v2';

function generateSnapshots(): PortfolioSnapshot[] {
  const snaps: PortfolioSnapshot[] = [];
  const today = new Date();
  // Seed based on real current values: crypto ~€4100, etf ~€294, stock ~€1950, cash ~€75
  let cash = 600, crypto = 3200, etf = 260, stock = 1600;

  for (let i = 89; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    cash   += (Math.random() - 0.45) * 40;
    crypto += (Math.random() - 0.48) * 120;
    etf    += (Math.random() - 0.46) * 8;
    stock  += (Math.random() - 0.47) * 55;
    snaps.push({
      date: d.toISOString().split('T')[0],
      cash:   Math.max(cash, 75),
      crypto: Math.max(crypto, 800),
      etf:    Math.max(etf, 100),
      stock:  Math.max(stock, 300),
    });
  }
  return snaps;
}

export const DEFAULT_CRYPTO: CryptoAsset[] = [
  { id: 'c1', symbol: 'BTC',  name: 'Bitcoin',    amount: 0.0348942,   emoji: '₿',  exchange: 'Tangem',  currentPrice: 71700 },
  { id: 'c2', symbol: 'ETH',  name: 'Ethereum',   amount: 0.44542,     emoji: '⟠',  exchange: 'Tangem',  currentPrice: 1874  },
  { id: 'c3', symbol: 'SOL',  name: 'Solana',     amount: 3.11745595,  emoji: '◎',  exchange: 'Tangem',  currentPrice: 79    },
  { id: 'c4', symbol: 'XRP',  name: 'XRP',        amount: 84.566087,   emoji: '✕',  exchange: 'Tangem',  currentPrice: 1.30  },
  { id: 'c5', symbol: 'LINK', name: 'Chainlink',  amount: 0.96250677,  emoji: '🔗', exchange: 'Tangem',  currentPrice: 8.87  },
  { id: 'c6', symbol: 'DOT',  name: 'Polkadot',   amount: 1.00,        emoji: '●',  exchange: 'Tangem',  currentPrice: 1.16  },
  { id: 'c7', symbol: 'PAXG', name: 'PAX Gold',   amount: 0.052037,    emoji: '🥇', exchange: 'Wallet',  currentPrice: 3895  },
];

export const DEFAULT_STOCKS: StockAsset[] = [
  // ETFs
  { id: 's1', ticker: 'VWCE', name: 'Vanguard FTSE All-World',  shares: 1.84316891, emoji: '🌍', broker: 'Trading 212', type: 'etf',   currentPrice: 159.43 },
  // Stocks — Trading 212
  { id: 's2', ticker: 'PLTR', name: 'Palantir',                  shares: 1.35703569, emoji: '🔭', broker: 'Trading 212', type: 'stock', currentPrice: 114.43 },
  { id: 's3', ticker: 'RGTI', name: 'Rigetti Computing',         shares: 8.44222677, emoji: '⚛️', broker: 'Trading 212', type: 'stock', currentPrice: 15.37  },
  { id: 's4', ticker: 'HRS',  name: 'L3Harris Technologies',     shares: 0.33411293, emoji: '📡', broker: 'Trading 212', type: 'stock', currentPrice: 261.10 },
  { id: 's5', ticker: 'CMP',  name: 'Compass Minerals',          shares: 3.35250836, emoji: '⛏️', broker: 'Trading 212', type: 'stock', currentPrice: 25.99  },
  { id: 's6', ticker: 'FTNT', name: 'Fortinet',                  shares: 0.74235807, emoji: '🔐', broker: 'Trading 212', type: 'stock', currentPrice: 105.35 },
  { id: 's7', ticker: 'Z4Q',  name: 'Kongsberg Maritime',        shares: 3.69385342, emoji: '⚓', broker: 'Trading 212', type: 'stock', currentPrice: 5.43   },
  // Stocks — Robinhood
  { id: 's8', ticker: 'ANET', name: 'Arista Networks',           shares: 2.0376,     emoji: '🌐', broker: 'Robinhood',   type: 'stock', currentPrice: 130.00 },
  { id: 's9', ticker: 'ETN',  name: 'Eaton Corporation',         shares: 0.4549,     emoji: '⚡', broker: 'Robinhood',   type: 'stock', currentPrice: 367.00 },
];

export function seedPortfolioIfNeeded() {
  if (typeof window === 'undefined') return;
  if (localStorage.getItem(PORTFOLIO_SEEDED)) return;
  // Clear any previous seed so fresh data is written
  localStorage.removeItem('wallu_portfolio_seeded');
  localStorage.setItem(CRYPTO_KEY, JSON.stringify(DEFAULT_CRYPTO));
  localStorage.setItem(STOCKS_KEY, JSON.stringify(DEFAULT_STOCKS));
  localStorage.setItem(SNAPSHOTS_KEY, JSON.stringify(generateSnapshots()));
  localStorage.setItem(PORTFOLIO_SEEDED, '1');
}

export function getCrypto(): CryptoAsset[] {
  if (typeof window === 'undefined') return DEFAULT_CRYPTO;
  seedPortfolioIfNeeded();
  try { return JSON.parse(localStorage.getItem(CRYPTO_KEY) || '[]'); } catch { return DEFAULT_CRYPTO; }
}

export function getStocks(): StockAsset[] {
  if (typeof window === 'undefined') return DEFAULT_STOCKS;
  seedPortfolioIfNeeded();
  try { return JSON.parse(localStorage.getItem(STOCKS_KEY) || '[]'); } catch { return DEFAULT_STOCKS; }
}

export function getSnapshots(): PortfolioSnapshot[] {
  if (typeof window === 'undefined') return [];
  seedPortfolioIfNeeded();
  try { return JSON.parse(localStorage.getItem(SNAPSHOTS_KEY) || '[]'); } catch { return []; }
}

export function saveCrypto(assets: CryptoAsset[]) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(CRYPTO_KEY, JSON.stringify(assets));
}

export function saveStocks(assets: StockAsset[]) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STOCKS_KEY, JSON.stringify(assets));
}

export function cryptoValue(assets: CryptoAsset[]): number {
  return assets.reduce((s, a) => s + a.amount * (a.currentPrice || 0), 0);
}

export function etfValue(assets: StockAsset[]): number {
  return assets.filter(a => a.type === 'etf').reduce((s, a) => s + a.shares * (a.currentPrice || 0), 0);
}

export function stockValue(assets: StockAsset[]): number {
  return assets.filter(a => a.type === 'stock').reduce((s, a) => s + a.shares * (a.currentPrice || 0), 0);
}

export function pctChange(snaps: PortfolioSnapshot[], key: keyof Omit<PortfolioSnapshot, 'date'>): number {
  if (snaps.length < 2) return 0;
  const first = snaps[0][key] as number;
  const last  = snaps[snaps.length - 1][key] as number;
  return first > 0 ? ((last - first) / first) * 100 : 0;
}
