'use client';

import { useEffect, useState, useMemo } from 'react';
import { TrendingUp, TrendingDown, Plus, Trash2, RefreshCw, ExternalLink } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import {
  getCrypto, getStocks, getSnapshots, saveCrypto, saveStocks,
  cryptoValue, etfValue, stockValue, pctChange,
  CryptoAsset, StockAsset, PortfolioSnapshot, AssetClass,
} from '@/lib/portfolio';
import { formatCurrency } from '@/lib/store';
import { useT } from '@/lib/i18n';

type Period = '1W' | '15D' | '1M' | '3M' | 'MAX';

const PERIODS: { key: Period; days: number }[] = [
  { key: '1W', days: 7 }, { key: '15D', days: 15 }, { key: '1M', days: 30 },
  { key: '3M', days: 90 }, { key: 'MAX', days: 999 },
];

const CLASS_META = {
  cash:   { color: '#10B981', emoji: '💶', dataKey: 'Cash'   },
  crypto: { color: '#F59E0B', emoji: '₿',  dataKey: 'Crypto' },
  etf:    { color: '#7C3AED', emoji: '🌍', dataKey: 'ETFs'   },
  stock:  { color: '#3B82F6', emoji: '📈', dataKey: 'Stocks' },
};

function Pill({ pct }: { pct: number }) {
  const pos = pct >= 0;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3, padding: '2px 8px', borderRadius: 99, fontSize: 12, fontWeight: 700, background: pos ? '#10B98122' : '#EF444422', color: pos ? '#10B981' : '#EF4444' }}>
      {pos ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
      {pos ? '+' : ''}{pct.toFixed(2)}%
    </span>
  );
}

function FearGreed() {
  const t = useT();
  const [data, setData] = useState<{ value: string; value_classification: string } | null>(null);
  useEffect(() => {
    fetch('/api/fear-greed').then(r => r.json()).then(d => setData(d?.data?.[0])).catch(() => {});
  }, []);
  if (!data) return null;
  const v = parseInt(data.value);
  const color = v <= 25 ? '#EF4444' : v <= 45 ? '#F97316' : v <= 55 ? '#F59E0B' : v <= 75 ? '#84CC16' : '#10B981';
  const labelMap: Record<string, string> = {
    'Extreme Fear': t('portfolio.extreme_fear'),
    'Fear': t('portfolio.fear'),
    'Neutral': t('portfolio.neutral'),
    'Greed': t('portfolio.greed'),
    'Extreme Greed': t('portfolio.extreme_greed'),
  };
  return (
    <div className="card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16 }}>
      <div style={{ position: 'relative', width: 56, height: 56, flexShrink: 0 }}>
        <svg viewBox="0 0 36 36" style={{ width: 56, height: 56, transform: 'rotate(-90deg)' }}>
          <circle cx="18" cy="18" r="15" fill="none" stroke="var(--surface2)" strokeWidth="4" />
          <circle cx="18" cy="18" r="15" fill="none" stroke={color} strokeWidth="4"
            strokeDasharray={`${(v / 100) * 94} 94`} strokeLinecap="round" />
        </svg>
        <span style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 800, color }}>{v}</span>
      </div>
      <div>
        <p style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 2 }}>{t('portfolio.fear_greed_title')}</p>
        <p style={{ fontSize: 15, fontWeight: 700, color }}>{labelMap[data.value_classification] || data.value_classification}</p>
        <p style={{ fontSize: 11, color: 'var(--muted)' }}>{t('portfolio.fear_greed_sub')}</p>
      </div>
    </div>
  );
}

function NewsFeed() {
  const t = useT();
  const [topic, setTopic] = useState<'crypto' | 'finance' | 'europe'>('crypto');
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/news?topic=${topic}`)
      .then(r => r.json())
      .then(d => { setItems(d?.items || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [topic]);

  const tabs: { key: typeof topic; label: string }[] = [
    { key: 'crypto',  label: t('portfolio.tab_crypto') },
    { key: 'finance', label: t('portfolio.tab_markets') },
    { key: 'europe',  label: t('portfolio.tab_europe') },
  ];

  return (
    <div className="card" style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h2 style={{ fontSize: 15, fontWeight: 700 }}>{t('portfolio.news_title')}</h2>
        <div style={{ display: 'flex', gap: 6 }}>
          {tabs.map(({ key, label }) => (
            <button key={key} onClick={() => setTopic(key)} style={{ padding: '4px 10px', borderRadius: 7, border: 'none', cursor: 'pointer', fontSize: 11, fontWeight: 600, background: topic === key ? 'var(--accent)' : 'var(--surface2)', color: topic === key ? 'white' : 'var(--muted)' }}>
              {label}
            </button>
          ))}
        </div>
      </div>
      {loading ? (
        <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--muted)', fontSize: 13 }}>
          <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite', display: 'inline' }} /> {t('portfolio.loading_news')}
        </div>
      ) : items.length === 0 ? (
        <p style={{ color: 'var(--muted)', fontSize: 13 }}>{t('portfolio.no_news')}</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {items.slice(0, 6).map((item, i) => (
            <a key={i} href={item.link} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', display: 'block', padding: '11px 0', borderBottom: i < 5 ? '1px solid var(--border)' : 'none' }}>
              <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)', marginBottom: 3, lineHeight: 1.4 }}>{item.title}</p>
              <p style={{ fontSize: 11, color: 'var(--muted)' }}>
                {new Date(item.pubDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                <ExternalLink size={9} style={{ marginLeft: 4, display: 'inline' }} />
              </p>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

function Converter() {
  const t = useT();
  const [prices, setPrices] = useState<Record<string, any>>({});
  const [amount, setAmount] = useState('1');
  const [fromCoin, setFromCoin] = useState('usd-coin');

  useEffect(() => {
    fetch('/api/prices').then(r => r.json()).then(setPrices).catch(() => {});
  }, []);

  const coin = prices[fromCoin];
  const eurVal = coin ? (parseFloat(amount) || 0) * coin.eur : 0;
  const usdVal = coin ? (parseFloat(amount) || 0) * coin.usd : 0;
  const gbpVal = coin ? (parseFloat(amount) || 0) * coin.gbp : 0;

  const coins = [
    { id: 'usd-coin', label: 'USDC' }, { id: 'tether', label: 'USDT' },
    { id: 'bitcoin', label: 'BTC' }, { id: 'ethereum', label: 'ETH' },
  ];

  return (
    <div className="card" style={{ padding: 20 }}>
      <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 14 }}>💱 {t('portfolio.converter_title')}</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <input type="number" value={amount} onChange={e => setAmount(e.target.value)} style={{ flex: 1 }} placeholder="1" />
        <select value={fromCoin} onChange={e => setFromCoin(e.target.value)} style={{ width: 90 }}>
          {coins.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
        </select>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {[{ flag: '🇪🇺', label: 'EUR', val: eurVal }, { flag: '🇺🇸', label: 'USD', val: usdVal }, { flag: '🇬🇧', label: 'GBP', val: gbpVal }].map(({ flag, label, val }) => (
          <div key={label} className="card-sm" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px' }}>
            <span style={{ fontSize: 13, color: 'var(--muted)' }}>{flag} {label}</span>
            <span style={{ fontSize: 16, fontWeight: 700 }}>
              {new Intl.NumberFormat('en-US', { style: 'currency', currency: label }).format(val)}
            </span>
          </div>
        ))}
      </div>
      {coin && (
        <p style={{ fontSize: 11, color: 'var(--muted)', marginTop: 10, textAlign: 'center' }}>
          1 {coins.find(c => c.id === fromCoin)?.label} = {formatCurrency(coin.eur)} · {t('portfolio.updated_5min')}
        </p>
      )}
    </div>
  );
}

function Insights({ cashBalance, cVal, eVal, sVal, snaps }: { cashBalance: number; cVal: number; eVal: number; sVal: number; snaps: PortfolioSnapshot[] }) {
  const t = useT();
  const total = cashBalance + cVal + eVal + sVal;
  const insights = useMemo(() => {
    const list: { emoji: string; text: string; type: 'info' | 'warn' | 'good' }[] = [];
    const cashPct = total > 0 ? (cashBalance / total) * 100 : 0;
    const cryptoPct = total > 0 ? (cVal / total) * 100 : 0;
    const emergencyMonths = cashBalance / 888;

    if (cashPct > 60) list.push({ emoji: '⚠️', text: t('portfolio.insight_cash_high', { pct: cashPct.toFixed(0) }), type: 'warn' });
    if (cryptoPct > 40) list.push({ emoji: '🎲', text: t('portfolio.insight_crypto_high', { pct: cryptoPct.toFixed(0) }), type: 'warn' });
    if (emergencyMonths >= 3 && emergencyMonths < 6) list.push({ emoji: '🛡️', text: t('portfolio.insight_emergency_partial', { months: emergencyMonths.toFixed(1) }), type: 'info' });
    if (emergencyMonths >= 6) list.push({ emoji: '✅', text: t('portfolio.insight_emergency_good', { months: emergencyMonths.toFixed(1) }), type: 'good' });
    if (eVal === 0) list.push({ emoji: '💡', text: t('portfolio.insight_no_etf'), type: 'info' });
    if (snaps.length > 7) {
      const weekAgo = snaps[snaps.length - 8];
      const now = snaps[snaps.length - 1];
      const totalNow = now.cash + now.crypto + now.etf + now.stock;
      const totalThen = weekAgo.cash + weekAgo.crypto + weekAgo.etf + weekAgo.stock;
      const weekChange = ((totalNow - totalThen) / totalThen) * 100;
      if (weekChange > 3) list.push({ emoji: '📈', text: t('portfolio.insight_week_up', { pct: weekChange.toFixed(1) }), type: 'good' });
      if (weekChange < -3) list.push({ emoji: '📉', text: t('portfolio.insight_week_down', { pct: Math.abs(weekChange).toFixed(1) }), type: 'warn' });
    }
    return list.slice(0, 4);
  }, [cashBalance, cVal, eVal, sVal, total, snaps, t]);

  const typeColor = { info: '#3B82F6', warn: '#F59E0B', good: '#10B981' };
  const typeBg = { info: '#3B82F622', warn: '#F59E0B22', good: '#10B98122' };

  return (
    <div className="card" style={{ padding: 20 }}>
      <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 14 }}>{t('portfolio.insights_title')}</h2>
      {insights.length === 0 ? (
        <p style={{ color: 'var(--muted)', fontSize: 13 }}>{t('portfolio.no_insights')}</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {insights.map((ins, i) => (
            <div key={i} style={{ padding: '10px 14px', borderRadius: 10, fontSize: 13, lineHeight: 1.5, background: typeBg[ins.type], borderLeft: `3px solid ${typeColor[ins.type]}` }}>
              {ins.emoji} {ins.text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function PortfolioPage() {
  const t = useT();
  const [crypto, setCrypto]    = useState<CryptoAsset[]>([]);
  const [stocks, setStocks]    = useState<StockAsset[]>([]);
  const [snaps, setSnaps]      = useState<PortfolioSnapshot[]>([]);
  const [cashBalance]          = useState(1261.40);
  const [period, setPeriod]    = useState<Period>('3M');
  const [active, setActive]    = useState<Set<AssetClass>>(new Set(['cash','crypto','etf','stock']));
  const [showAddCrypto, setShowAddCrypto] = useState(false);
  const [showAddStock,  setShowAddStock]  = useState(false);
  const [addStockType, setAddStockType]   = useState<'etf'|'stock'>('etf');
  const [newCrypto, setNewCrypto] = useState({ symbol:'', name:'', amount:'', price:'', emoji:'🪙', exchange:'' });
  const [newStock,  setNewStock]  = useState({ ticker:'', name:'', shares:'', price:'', emoji:'📊', broker:'', type:'etf' as 'etf'|'stock' });

  useEffect(() => {
    setCrypto(getCrypto()); setStocks(getStocks()); setSnaps(getSnapshots());
  }, []);

  const days = PERIODS.find(p => p.key === period)?.days ?? 90;
  const filteredSnaps = useMemo(() => snaps.slice(-days), [snaps, days]);

  const classConfig = {
    cash:   { label: t('portfolio.cash'),   ...CLASS_META.cash },
    crypto: { label: t('portfolio.crypto'), ...CLASS_META.crypto },
    etf:    { label: t('portfolio.etf'),    ...CLASS_META.etf },
    stock:  { label: t('portfolio.stocks'), ...CLASS_META.stock },
  };

  const chartData = useMemo(() => filteredSnaps.map(s => ({
    date: new Date(s.date + 'T00:00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }),
    ...(active.has('cash')   ? { Cash:   Math.round(s.cash)   } : {}),
    ...(active.has('crypto') ? { Crypto: Math.round(s.crypto) } : {}),
    ...(active.has('etf')    ? { ETFs:   Math.round(s.etf)    } : {}),
    ...(active.has('stock')  ? { Stocks: Math.round(s.stock)  } : {}),
  })), [filteredSnaps, active]);

  const cVal = cryptoValue(crypto);
  const eVal = etfValue(stocks);
  const sVal = stockValue(stocks);
  const totalNet = cashBalance + cVal + eVal + sVal;

  const toggleClass = (cls: AssetClass) => setActive(prev => {
    const n = new Set(prev); n.has(cls) ? n.delete(cls) : n.add(cls); return n.size === 0 ? prev : n;
  });
  const toggleAll = () => setActive(prev => prev.size === 4 ? new Set<AssetClass>(['cash']) : new Set<AssetClass>(['cash','crypto','etf','stock']));

  const totalPct = filteredSnaps.length >= 2 ? (() => {
    const first = filteredSnaps[0]; const last = filteredSnaps[filteredSnaps.length - 1];
    const fTotal = first.cash + first.crypto + first.etf + first.stock;
    const lTotal = last.cash  + last.crypto  + last.etf  + last.stock;
    return fTotal > 0 ? ((lTotal - fTotal) / fTotal) * 100 : 0;
  })() : 0;

  const addCrypto = () => {
    if (!newCrypto.symbol || !newCrypto.amount) return;
    const a: CryptoAsset = { id: Date.now().toString(), symbol: newCrypto.symbol.toUpperCase(), name: newCrypto.name || newCrypto.symbol, amount: parseFloat(newCrypto.amount), emoji: newCrypto.emoji, exchange: newCrypto.exchange, currentPrice: parseFloat(newCrypto.price) || 0 };
    const u = [...crypto, a]; setCrypto(u); saveCrypto(u);
    setNewCrypto({ symbol:'', name:'', amount:'', price:'', emoji:'🪙', exchange:'' }); setShowAddCrypto(false);
  };
  const addStock = () => {
    if (!newStock.ticker || !newStock.shares) return;
    const a: StockAsset = { id: Date.now().toString(), ticker: newStock.ticker.toUpperCase(), name: newStock.name || newStock.ticker, shares: parseFloat(newStock.shares), emoji: newStock.emoji, broker: newStock.broker, type: addStockType, currentPrice: parseFloat(newStock.price) || 0 };
    const u = [...stocks, a]; setStocks(u); saveStocks(u);
    setNewStock({ ticker:'', name:'', shares:'', price:'', emoji:'📊', broker:'', type:'etf' }); setShowAddStock(false);
  };
  const removeCrypto = (id: string) => { const u = crypto.filter(c => c.id !== id); setCrypto(u); saveCrypto(u); };
  const removeStock  = (id: string) => { const u = stocks.filter(s => s.id !== id); setStocks(u); saveStocks(u); };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.4px' }}>{t('portfolio.title')}</h1>
        <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 4 }}>{t('portfolio.subtitle')}</p>
      </div>

      <div className="card" style={{ padding: 22, marginBottom: 16, background: 'linear-gradient(135deg, #161628, #1a1040)' }}>
        <p style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>{t('portfolio.total')}</p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
          <span style={{ fontSize: 36, fontWeight: 800, letterSpacing: '-1px' }}>{formatCurrency(totalNet)}</span>
          <Pill pct={totalPct} />
        </div>
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          {(['cash', 'crypto', 'etf', 'stock'] as AssetClass[]).map(cls => {
            const val = cls === 'cash' ? cashBalance : cls === 'crypto' ? cVal : cls === 'etf' ? eVal : sVal;
            const pct = pctChange(filteredSnaps, cls);
            const cfg = classConfig[cls];
            return (
              <div key={cls}>
                <p style={{ fontSize: 11, color: cfg.color, fontWeight: 600, marginBottom: 2 }}>{cfg.emoji} {cfg.label}</p>
                <p style={{ fontSize: 14, fontWeight: 700, marginBottom: 2 }}>{formatCurrency(val)}</p>
                <Pill pct={pct} />
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
          <button onClick={toggleAll} style={{ padding: '5px 10px', borderRadius: 7, border: '1px solid var(--border)', cursor: 'pointer', background: active.size === 4 ? 'var(--surface2)' : 'transparent', color: active.size === 4 ? 'var(--text)' : 'var(--muted)', fontSize: 11, fontWeight: 600 }}>
            {t('portfolio.all_toggle')}
          </button>
          {(['cash','crypto','etf','stock'] as AssetClass[]).map(cls => {
            const cfg = classConfig[cls];
            return (
              <button key={cls} onClick={() => toggleClass(cls)} style={{ padding: '5px 10px', borderRadius: 7, border: `1px solid ${active.has(cls) ? cfg.color+'66' : 'var(--border)'}`, cursor: 'pointer', fontSize: 11, fontWeight: 600, background: active.has(cls) ? cfg.color+'22' : 'transparent', color: active.has(cls) ? cfg.color : 'var(--muted)' }}>
                {cfg.emoji} {cfg.label}
              </button>
            );
          })}
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {PERIODS.map(p => (
            <button key={p.key} onClick={() => setPeriod(p.key)} style={{ padding: '5px 10px', borderRadius: 7, border: 'none', cursor: 'pointer', fontSize: 11, fontWeight: 600, background: period === p.key ? 'var(--accent)' : 'var(--surface2)', color: period === p.key ? 'white' : 'var(--muted)' }}>
              {p.key}
            </button>
          ))}
        </div>
      </div>

      <div className="card" style={{ padding: '18px 6px 6px', marginBottom: 20 }}>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
            <defs>
              {(['cash','crypto','etf','stock'] as AssetClass[]).map(cls => (
                <linearGradient key={cls} id={`g-${cls}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={CLASS_META[cls].color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={CLASS_META[cls].color} stopOpacity={0}   />
                </linearGradient>
              ))}
            </defs>
            <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#6B6B8A' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 9, fill: '#6B6B8A' }} tickLine={false} axisLine={false} tickFormatter={v => `${(v/1000).toFixed(0)}k`} width={28} />
            <Tooltip contentStyle={{ background: '#1E1E35', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, fontSize: 12 }} labelStyle={{ color: '#9B59F5', fontWeight: 600 }} formatter={(v: number, n: string) => [formatCurrency(v), n]} />
            {active.has('cash')   && <Area type="monotone" dataKey="Cash"   stroke={CLASS_META.cash.color}   fill="url(#g-cash)"   strokeWidth={2} dot={false} name={classConfig.cash.label}   />}
            {active.has('crypto') && <Area type="monotone" dataKey="Crypto" stroke={CLASS_META.crypto.color} fill="url(#g-crypto)" strokeWidth={2} dot={false} name={classConfig.crypto.label} />}
            {active.has('etf')    && <Area type="monotone" dataKey="ETFs"   stroke={CLASS_META.etf.color}    fill="url(#g-etf)"    strokeWidth={2} dot={false} name={classConfig.etf.label}    />}
            {active.has('stock')  && <Area type="monotone" dataKey="Stocks" stroke={CLASS_META.stock.color}  fill="url(#g-stock)"  strokeWidth={2} dot={false} name={classConfig.stock.label}  />}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="dashboard-grid" style={{ marginBottom: 20 }}>
        <FearGreed />
        <Converter />
      </div>

      <div style={{ marginBottom: 20 }}><Insights cashBalance={cashBalance} cVal={cVal} eVal={eVal} sVal={sVal} snaps={snaps} /></div>
      <div style={{ marginBottom: 20 }}><NewsFeed /></div>

      {/* Crypto */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700 }}>₿ {t('portfolio.my_crypto')} <span style={{ color: 'var(--muted)', fontWeight: 400, fontSize: 13 }}>{formatCurrency(cVal)}</span></h2>
          <button className="btn-primary" style={{ padding: '6px 12px', fontSize: 12 }} onClick={() => setShowAddCrypto(!showAddCrypto)}><Plus size={13} /> {t('portfolio.add_btn')}</button>
        </div>
        {showAddCrypto && (
          <div className="card fade-in" style={{ padding: 16, marginBottom: 12 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
              <div><label>{t('portfolio.symbol')}</label><input value={newCrypto.symbol} onChange={e => setNewCrypto(p => ({...p, symbol: e.target.value}))} placeholder="BTC" /></div>
              <div><label>{t('portfolio.name_field')}</label><input value={newCrypto.name} onChange={e => setNewCrypto(p => ({...p, name: e.target.value}))} placeholder="Bitcoin" /></div>
              <div><label>{t('portfolio.amount_field')}</label><input type="number" value={newCrypto.amount} onChange={e => setNewCrypto(p => ({...p, amount: e.target.value}))} placeholder="0.01" /></div>
              <div><label>{t('portfolio.current_price')}</label><input type="number" value={newCrypto.price} onChange={e => setNewCrypto(p => ({...p, price: e.target.value}))} placeholder="62400" /></div>
              <div><label>{t('portfolio.exchange')}</label><input value={newCrypto.exchange} onChange={e => setNewCrypto(p => ({...p, exchange: e.target.value}))} placeholder="Binance" /></div>
              <div><label>Emoji</label><input value={newCrypto.emoji} onChange={e => setNewCrypto(p => ({...p, emoji: e.target.value}))} maxLength={2} style={{ fontSize: 20, textAlign: 'center' }} /></div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-ghost" style={{ flex: 1 }} onClick={() => setShowAddCrypto(false)}>{t('portfolio.cancel')}</button>
              <button className="btn-primary" style={{ flex: 1, justifyContent: 'center' }} onClick={addCrypto}>{t('portfolio.add_btn')}</button>
            </div>
          </div>
        )}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {crypto.map(a => {
            const val = a.amount * (a.currentPrice || 0);
            return (
              <div key={a.id} className="card-sm" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px' }}>
                <div style={{ width: 36, height: 36, borderRadius: 9, background: '#F59E0B22', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17, flexShrink: 0 }}>{a.emoji}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 13, fontWeight: 600 }}>{a.name} <span style={{ color: 'var(--muted)', fontSize: 11 }}>{a.symbol}</span></p>
                  <p style={{ fontSize: 11, color: 'var(--muted)' }}>{a.amount} {a.symbol}{a.exchange ? ` · ${a.exchange}` : ''}</p>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <p style={{ fontSize: 14, fontWeight: 700 }}>{formatCurrency(val)}</p>
                  {a.currentPrice ? <p style={{ fontSize: 10, color: 'var(--muted)' }}>{formatCurrency(a.currentPrice)}{t('portfolio.per_unit')}</p> : null}
                </div>
                <button onClick={() => removeCrypto(a.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: 4 }}><Trash2 size={13} /></button>
              </div>
            );
          })}
        </div>
      </div>

      {/* ETFs + Stocks */}
      {(['etf', 'stock'] as const).map(type => {
        const filtered = stocks.filter(s => s.type === type);
        const val = type === 'etf' ? eVal : sVal;
        const color = type === 'etf' ? '#7C3AED' : '#3B82F6';
        const emoji = type === 'etf' ? '🌍' : '📈';
        const label = type === 'etf' ? t('portfolio.my_etfs') : t('portfolio.my_stocks');
        return (
          <div key={type} style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <h2 style={{ fontSize: 15, fontWeight: 700 }}>{emoji} {label} <span style={{ color: 'var(--muted)', fontWeight: 400, fontSize: 13 }}>{formatCurrency(val)}</span></h2>
              <button className="btn-primary" style={{ padding: '6px 12px', fontSize: 12 }} onClick={() => { setAddStockType(type); setShowAddStock(!showAddStock); }}><Plus size={13} /> {t('portfolio.add_btn')}</button>
            </div>
            {showAddStock && addStockType === type && (
              <div className="card fade-in" style={{ padding: 16, marginBottom: 12 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
                  <div><label>{t('portfolio.ticker')}</label><input value={newStock.ticker} onChange={e => setNewStock(p => ({...p, ticker: e.target.value}))} placeholder={type === 'etf' ? 'VWCE' : 'AAPL'} /></div>
                  <div><label>{t('portfolio.name_field')}</label><input value={newStock.name} onChange={e => setNewStock(p => ({...p, name: e.target.value}))} placeholder={type === 'etf' ? 'Vanguard All-World' : 'Apple Inc.'} /></div>
                  <div><label>{t('portfolio.shares')}</label><input type="number" value={newStock.shares} onChange={e => setNewStock(p => ({...p, shares: e.target.value}))} placeholder="10" /></div>
                  <div><label>{t('portfolio.current_price')}</label><input type="number" value={newStock.price} onChange={e => setNewStock(p => ({...p, price: e.target.value}))} placeholder="114" /></div>
                  <div><label>{t('portfolio.broker')}</label><input value={newStock.broker} onChange={e => setNewStock(p => ({...p, broker: e.target.value}))} placeholder="DEGIRO" /></div>
                  <div><label>Emoji</label><input value={newStock.emoji} onChange={e => setNewStock(p => ({...p, emoji: e.target.value}))} maxLength={2} style={{ fontSize: 20, textAlign: 'center' }} /></div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn-ghost" style={{ flex: 1 }} onClick={() => setShowAddStock(false)}>{t('portfolio.cancel')}</button>
                  <button className="btn-primary" style={{ flex: 1, justifyContent: 'center' }} onClick={addStock}>{t('portfolio.add_btn')}</button>
                </div>
              </div>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {filtered.map(a => {
                const v = a.shares * (a.currentPrice || 0);
                return (
                  <div key={a.id} className="card-sm" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px' }}>
                    <div style={{ width: 36, height: 36, borderRadius: 9, background: color+'22', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17, flexShrink: 0 }}>{a.emoji}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: 13, fontWeight: 600 }}>{a.name} <span style={{ color: 'var(--muted)', fontSize: 11 }}>{a.ticker}</span></p>
                      <p style={{ fontSize: 11, color: 'var(--muted)' }}>
                        {a.shares} {type === 'etf' ? t('portfolio.units') : t('portfolio.shares_label')}{a.broker ? ` · ${a.broker}` : ''}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <p style={{ fontSize: 14, fontWeight: 700 }}>{formatCurrency(v)}</p>
                      {a.currentPrice ? <p style={{ fontSize: 10, color: 'var(--muted)' }}>{formatCurrency(a.currentPrice)}{t('portfolio.per_unit')}</p> : null}
                    </div>
                    <button onClick={() => removeStock(a.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: 4 }}><Trash2 size={13} /></button>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
