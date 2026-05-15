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
const PORTFOLIO_SEEDED = 'wallu_portfolio_seeded';

// Generate realistic historical data for demo
function generateSnapshots(): PortfolioSnapshot[] {
  const snaps: PortfolioSnapshot[] = [];
  const today = new Date();
  let cash = 1100, crypto = 420, etf = 2800, stock = 950;

  for (let i = 89; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    cash   += (Math.random() - 0.45) * 60;
    crypto += (Math.random() - 0.48) * 85;
    etf    += (Math.random() - 0.46) * 45;
    stock  += (Math.random() - 0.47) * 55;
    snaps.push({
      date: d.toISOString().split('T')[0],
      cash:   Math.max(cash, 200),
      crypto: Math.max(crypto, 50),
      etf:    Math.max(etf, 500),
      stock:  Math.max(stock, 100),
    });
  }
  return snaps;
}

export const DEFAULT_CRYPTO: CryptoAsset[] = [
  { id: 'c1', symbol: 'BTC', name: 'Bitcoin', amount: 0.012, emoji: '₿', exchange: 'Binance', currentPrice: 62400 },
  { id: 'c2', symbol: 'ETH', name: 'Ethereum', amount: 0.45, emoji: '⟠', exchange: 'Binance', currentPrice: 3180 },
  { id: 'c3', symbol: 'SOL', name: 'Solana', amount: 3.2, emoji: '◎', exchange: 'Coinbase', currentPrice: 148 },
];

export const DEFAULT_STOCKS: StockAsset[] = [
  { id: 's1', ticker: 'VWCE', name: 'Vanguard FTSE All-World', shares: 12, emoji: '🌍', broker: 'DEGIRO', type: 'etf', currentPrice: 114 },
  { id: 's2', ticker: 'CSPX', name: 'iShares S&P 500', shares: 8, emoji: '🇺🇸', broker: 'DEGIRO', type: 'etf', currentPrice: 520 },
  { id: 's3', ticker: 'AAPL', name: 'Apple Inc.', shares: 5, emoji: '🍎', broker: 'Trading 212', type: 'stock', currentPrice: 189 },
  { id: 's4', ticker: 'MSFT', name: 'Microsoft', shares: 3, emoji: '🪟', broker: 'Trading 212', type: 'stock', currentPrice: 415 },
];

export function seedPortfolioIfNeeded() {
  if (typeof window === 'undefined') return;
  if (localStorage.getItem(PORTFOLIO_SEEDED)) return;
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
