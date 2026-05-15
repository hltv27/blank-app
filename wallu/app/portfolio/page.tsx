'use client';

import { useEffect, useState, useMemo } from 'react';
import { TrendingUp, TrendingDown, Plus, Trash2, RefreshCw } from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import {
  getCrypto, getStocks, getSnapshots, saveCrypto, saveStocks,
  cryptoValue, etfValue, stockValue, pctChange,
  CryptoAsset, StockAsset, PortfolioSnapshot, AssetClass,
} from '@/lib/portfolio';
import { getSubscriptions, formatCurrency } from '@/lib/store';
import { monthlyAmount } from '@/lib/store';

type Period = '1M' | '3M' | 'MAX';
type ActiveClass = AssetClass | 'all';

const CLASS_CONFIG = {
  cash:   { label: 'Dinheiro', color: '#10B981', emoji: '💶' },
  crypto: { label: 'Cripto',   color: '#F59E0B', emoji: '₿'  },
  etf:    { label: 'ETFs',     color: '#7C3AED', emoji: '🌍' },
  stock:  { label: 'Ações',    color: '#3B82F6', emoji: '📈' },
};

const PERIODS: Period[] = ['1M', '3M', 'MAX'];

function Pill({ positive, value }: { positive: boolean; value: number }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 3,
      padding: '2px 8px', borderRadius: 99, fontSize: 12, fontWeight: 700,
      background: positive ? '#10B98122' : '#EF444422',
      color: positive ? '#10B981' : '#EF4444',
    }}>
      {positive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
      {positive ? '+' : ''}{value.toFixed(2)}%
    </span>
  );
}

export default function PortfolioPage() {
  const [crypto, setCrypto]       = useState<CryptoAsset[]>([]);
  const [stocks, setStocks]       = useState<StockAsset[]>([]);
  const [snaps, setSnaps]         = useState<PortfolioSnapshot[]>([]);
  const [cashBalance, setCash]    = useState(0);
  const [period, setPeriod]       = useState<Period>('3M');
  const [active, setActive]       = useState<Set<AssetClass>>(new Set(['cash','crypto','etf','stock']));
  const [showAddCrypto, setShowAddCrypto] = useState(false);
  const [showAddStock,  setShowAddStock]  = useState(false);
  const [newCrypto, setNewCrypto] = useState({ symbol: '', name: '', amount: '', price: '', emoji: '🪙', exchange: '' });
  const [newStock,  setNewStock]  = useState({ ticker: '', name: '', shares: '', price: '', emoji: '📊', broker: '', type: 'etf' as 'etf' | 'stock' });

  useEffect(() => {
    const c = getCrypto(); const s = getStocks(); const sn = getSnapshots();
    const subs = getSubscriptions();
    const cash = 1261.40; // from finances page balance
    setCrypto(c); setStocks(s); setSnaps(sn); setCash(cash);
  }, []);

  const filteredSnaps = useMemo(() => {
    const days = period === '1M' ? 30 : period === '3M' ? 90 : 999;
    return snaps.slice(-days);
  }, [snaps, period]);

  const chartData = useMemo(() => filteredSnaps.map(s => ({
    date: new Date(s.date).toLocaleDateString('pt-PT', { day: 'numeric', month: 'short' }),
    ...(active.has('cash')   ? { 'Dinheiro': Math.round(s.cash) }   : {}),
    ...(active.has('crypto') ? { 'Cripto':   Math.round(s.crypto) } : {}),
    ...(active.has('etf')    ? { 'ETFs':     Math.round(s.etf) }    : {}),
    ...(active.has('stock')  ? { 'Ações':    Math.round(s.stock) }  : {}),
  })), [filteredSnaps, active]);

  const cVal = cryptoValue(crypto);
  const eVal = etfValue(stocks);
  const sVal = stockValue(stocks);
  const totalNet = cashBalance + cVal + eVal + sVal;

  const toggleClass = (cls: AssetClass) => {
    setActive(prev => {
      const n = new Set(prev);
      n.has(cls) ? n.delete(cls) : n.add(cls);
      return n.size === 0 ? prev : n;
    });
  };

  const toggleAll = () => {
    const all: AssetClass[] = ['cash','crypto','etf','stock'];
    setActive(prev => prev.size === 4 ? new Set(['cash']) : new Set(all));
  };

  const addCrypto = () => {
    if (!newCrypto.symbol || !newCrypto.amount) return;
    const asset: CryptoAsset = {
      id: Date.now().toString(),
      symbol: newCrypto.symbol.toUpperCase(),
      name: newCrypto.name || newCrypto.symbol,
      amount: parseFloat(newCrypto.amount),
      emoji: newCrypto.emoji,
      exchange: newCrypto.exchange,
      currentPrice: parseFloat(newCrypto.price) || 0,
    };
    const updated = [...crypto, asset];
    setCrypto(updated); saveCrypto(updated);
    setNewCrypto({ symbol: '', name: '', amount: '', price: '', emoji: '🪙', exchange: '' });
    setShowAddCrypto(false);
  };

  const addStock = () => {
    if (!newStock.ticker || !newStock.shares) return;
    const asset: StockAsset = {
      id: Date.now().toString(),
      ticker: newStock.ticker.toUpperCase(),
      name: newStock.name || newStock.ticker,
      shares: parseFloat(newStock.shares),
      emoji: newStock.emoji,
      broker: newStock.broker,
      type: newStock.type,
      currentPrice: parseFloat(newStock.price) || 0,
    };
    const updated = [...stocks, asset];
    setStocks(updated); saveStocks(updated);
    setNewStock({ ticker: '', name: '', shares: '', price: '', emoji: '📊', broker: '', type: 'etf' });
    setShowAddStock(false);
  };

  const removeCrypto = (id: string) => { const u = crypto.filter(c => c.id !== id); setCrypto(u); saveCrypto(u); };
  const removeStock  = (id: string) => { const u = stocks.filter(s => s.id !== id); setStocks(u); saveStocks(u); };

  const cPct = pctChange(filteredSnaps, 'crypto');
  const ePct = pctChange(filteredSnaps, 'etf');
  const sPct = pctChange(filteredSnaps, 'stock');
  const cashPct = pctChange(filteredSnaps, 'cash');
  const totalPct = filteredSnaps.length >= 2
    ? ((totalNet - (filteredSnaps[0].cash + filteredSnaps[0].crypto + filteredSnaps[0].etf + filteredSnaps[0].stock)) /
       (filteredSnaps[0].cash + filteredSnaps[0].crypto + filteredSnaps[0].etf + filteredSnaps[0].stock)) * 100
    : 0;

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.4px' }}>Carteira</h1>
        <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 4 }}>Evolução do teu patrimônio total</p>
      </div>

      {/* Net worth hero */}
      <div className="card" style={{ padding: '24px', marginBottom: 20, background: 'linear-gradient(135deg, #161628 0%, #1a1040 100%)' }}>
        <p style={{ fontSize: 12, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>Patrimônio Total</p>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 38, fontWeight: 800, letterSpacing: '-1px' }}>{formatCurrency(totalNet)}</span>
          <Pill positive={totalPct >= 0} value={totalPct} />
        </div>
        <div style={{ display: 'flex', gap: 16, marginTop: 16, flexWrap: 'wrap' }}>
          {[
            { label: 'Dinheiro', val: cashBalance, pct: cashPct, cls: 'cash' as AssetClass },
            { label: 'Cripto',   val: cVal,        pct: cPct,    cls: 'crypto' as AssetClass },
            { label: 'ETFs',     val: eVal,        pct: ePct,    cls: 'etf' as AssetClass },
            { label: 'Ações',    val: sVal,        pct: sPct,    cls: 'stock' as AssetClass },
          ].map(({ label, val, pct, cls }) => (
            <div key={cls} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <span style={{ fontSize: 11, color: CLASS_CONFIG[cls].color, fontWeight: 600 }}>
                {CLASS_CONFIG[cls].emoji} {label}
              </span>
              <span style={{ fontSize: 14, fontWeight: 700 }}>{formatCurrency(val)}</span>
              <Pill positive={pct >= 0} value={pct} />
            </div>
          ))}
        </div>
      </div>

      {/* Chart controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        {/* Asset toggles */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <button onClick={toggleAll} style={{
            padding: '6px 12px', borderRadius: 8, border: '1px solid var(--border)', cursor: 'pointer',
            background: active.size === 4 ? 'var(--surface2)' : 'transparent',
            color: active.size === 4 ? 'var(--text)' : 'var(--muted)', fontSize: 12, fontWeight: 600,
          }}>Tudo</button>
          {(Object.entries(CLASS_CONFIG) as [AssetClass, typeof CLASS_CONFIG.cash][]).map(([cls, cfg]) => (
            <button key={cls} onClick={() => toggleClass(cls)} style={{
              padding: '6px 12px', borderRadius: 8, border: `1px solid ${active.has(cls) ? cfg.color + '66' : 'var(--border)'}`,
              cursor: 'pointer', fontSize: 12, fontWeight: 600, transition: 'all 0.15s',
              background: active.has(cls) ? cfg.color + '22' : 'transparent',
              color: active.has(cls) ? cfg.color : 'var(--muted)',
            }}>
              {cfg.emoji} {cfg.label}
            </button>
          ))}
        </div>
        {/* Period */}
        <div style={{ display: 'flex', gap: 4 }}>
          {PERIODS.map(p => (
            <button key={p} onClick={() => setPeriod(p)} style={{
              padding: '5px 12px', borderRadius: 7, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600,
              background: period === p ? 'var(--accent)' : 'var(--surface2)',
              color: period === p ? 'white' : 'var(--muted)',
            }}>{p}</button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="card" style={{ padding: '20px 8px 8px', marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
            <defs>
              {(Object.entries(CLASS_CONFIG) as [AssetClass, typeof CLASS_CONFIG.cash][]).map(([cls, cfg]) => (
                <linearGradient key={cls} id={`grad-${cls}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={cfg.color} stopOpacity={0.25} />
                  <stop offset="95%" stopColor={cfg.color} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6B6B8A' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 10, fill: '#6B6B8A' }} tickLine={false} axisLine={false} tickFormatter={v => `${(v/1000).toFixed(0)}k`} width={32} />
            <Tooltip
              contentStyle={{ background: '#1E1E35', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, fontSize: 12 }}
              labelStyle={{ color: '#9B59F5', fontWeight: 600, marginBottom: 4 }}
              formatter={(val: number, name: string) => [formatCurrency(val), name]}
            />
            {active.has('cash')   && <Area type="monotone" dataKey="Dinheiro" stroke={CLASS_CONFIG.cash.color}   fill={`url(#grad-cash)`}   strokeWidth={2} dot={false} />}
            {active.has('crypto') && <Area type="monotone" dataKey="Cripto"   stroke={CLASS_CONFIG.crypto.color} fill={`url(#grad-crypto)`} strokeWidth={2} dot={false} />}
            {active.has('etf')    && <Area type="monotone" dataKey="ETFs"     stroke={CLASS_CONFIG.etf.color}    fill={`url(#grad-etf)`}    strokeWidth={2} dot={false} />}
            {active.has('stock')  && <Area type="monotone" dataKey="Ações"    stroke={CLASS_CONFIG.stock.color}  fill={`url(#grad-stock)`}  strokeWidth={2} dot={false} />}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Crypto assets */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700 }}>₿ Cripto <span style={{ color: 'var(--muted)', fontWeight: 400, fontSize: 13 }}>{formatCurrency(cVal)}</span></h2>
          <button className="btn-primary" style={{ padding: '6px 12px', fontSize: 12 }} onClick={() => setShowAddCrypto(!showAddCrypto)}>
            <Plus size={13} /> Adicionar
          </button>
        </div>

        {showAddCrypto && (
          <div className="card fade-in" style={{ padding: 16, marginBottom: 12 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
              <div><label>Símbolo *</label><input value={newCrypto.symbol} onChange={e => setNewCrypto(p => ({...p, symbol: e.target.value}))} placeholder="BTC" /></div>
              <div><label>Nome</label><input value={newCrypto.name} onChange={e => setNewCrypto(p => ({...p, name: e.target.value}))} placeholder="Bitcoin" /></div>
              <div><label>Quantidade *</label><input type="number" value={newCrypto.amount} onChange={e => setNewCrypto(p => ({...p, amount: e.target.value}))} placeholder="0.01" /></div>
              <div><label>Preço actual (€)</label><input type="number" value={newCrypto.price} onChange={e => setNewCrypto(p => ({...p, price: e.target.value}))} placeholder="62400" /></div>
              <div><label>Exchange / Wallet</label><input value={newCrypto.exchange} onChange={e => setNewCrypto(p => ({...p, exchange: e.target.value}))} placeholder="Binance" /></div>
              <div><label>Emoji</label><input value={newCrypto.emoji} onChange={e => setNewCrypto(p => ({...p, emoji: e.target.value}))} maxLength={2} style={{ fontSize: 20, textAlign: 'center' }} /></div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-ghost" style={{ flex: 1 }} onClick={() => setShowAddCrypto(false)}>Cancelar</button>
              <button className="btn-primary" style={{ flex: 1, justifyContent: 'center' }} onClick={addCrypto}>Adicionar</button>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {crypto.map(a => {
            const val = a.amount * (a.currentPrice || 0);
            return (
              <div key={a.id} className="card-sm" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px' }}>
                <div style={{ width: 38, height: 38, borderRadius: 10, background: '#F59E0B22', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>{a.emoji}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{a.name} <span style={{ color: 'var(--muted)', fontSize: 12 }}>{a.symbol}</span></div>
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>{a.amount} {a.symbol} {a.exchange && `· ${a.exchange}`}</div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 700 }}>{formatCurrency(val)}</div>
                  {a.currentPrice && <div style={{ fontSize: 11, color: 'var(--muted)' }}>{formatCurrency(a.currentPrice)}/un</div>}
                </div>
                <button onClick={() => removeCrypto(a.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: 4 }}><Trash2 size={13} /></button>
              </div>
            );
          })}
        </div>
      </div>

      {/* ETFs */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700 }}>🌍 ETFs <span style={{ color: 'var(--muted)', fontWeight: 400, fontSize: 13 }}>{formatCurrency(eVal)}</span></h2>
          <button className="btn-primary" style={{ padding: '6px 12px', fontSize: 12 }} onClick={() => { setNewStock(p => ({...p, type: 'etf'})); setShowAddStock(!showAddStock); }}>
            <Plus size={13} /> Adicionar
          </button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {stocks.filter(s => s.type === 'etf').map(a => {
            const val = a.shares * (a.currentPrice || 0);
            return (
              <div key={a.id} className="card-sm" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px' }}>
                <div style={{ width: 38, height: 38, borderRadius: 10, background: '#7C3AED22', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>{a.emoji}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{a.name} <span style={{ color: 'var(--muted)', fontSize: 12 }}>{a.ticker}</span></div>
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>{a.shares} unidades {a.broker && `· ${a.broker}`}</div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 700 }}>{formatCurrency(val)}</div>
                  {a.currentPrice && <div style={{ fontSize: 11, color: 'var(--muted)' }}>{formatCurrency(a.currentPrice)}/un</div>}
                </div>
                <button onClick={() => removeStock(a.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: 4 }}><Trash2 size={13} /></button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Stocks */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700 }}>📈 Ações <span style={{ color: 'var(--muted)', fontWeight: 400, fontSize: 13 }}>{formatCurrency(sVal)}</span></h2>
          <button className="btn-primary" style={{ padding: '6px 12px', fontSize: 12 }} onClick={() => { setNewStock(p => ({...p, type: 'stock'})); setShowAddStock(!showAddStock); }}>
            <Plus size={13} /> Adicionar
          </button>
        </div>

        {showAddStock && (
          <div className="card fade-in" style={{ padding: 16, marginBottom: 12 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
              <div><label>Ticker *</label><input value={newStock.ticker} onChange={e => setNewStock(p => ({...p, ticker: e.target.value}))} placeholder="AAPL" /></div>
              <div><label>Nome</label><input value={newStock.name} onChange={e => setNewStock(p => ({...p, name: e.target.value}))} placeholder="Apple Inc." /></div>
              <div><label>Nº acções *</label><input type="number" value={newStock.shares} onChange={e => setNewStock(p => ({...p, shares: e.target.value}))} placeholder="10" /></div>
              <div><label>Preço actual (€)</label><input type="number" value={newStock.price} onChange={e => setNewStock(p => ({...p, price: e.target.value}))} placeholder="189" /></div>
              <div><label>Broker</label><input value={newStock.broker} onChange={e => setNewStock(p => ({...p, broker: e.target.value}))} placeholder="DEGIRO" /></div>
              <div>
                <label>Tipo</label>
                <select value={newStock.type} onChange={e => setNewStock(p => ({...p, type: e.target.value as 'etf'|'stock'}))}>
                  <option value="stock">Ação</option>
                  <option value="etf">ETF</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-ghost" style={{ flex: 1 }} onClick={() => setShowAddStock(false)}>Cancelar</button>
              <button className="btn-primary" style={{ flex: 1, justifyContent: 'center' }} onClick={addStock}>Adicionar</button>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {stocks.filter(s => s.type === 'stock').map(a => {
            const val = a.shares * (a.currentPrice || 0);
            return (
              <div key={a.id} className="card-sm" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px' }}>
                <div style={{ width: 38, height: 38, borderRadius: 10, background: '#3B82F622', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>{a.emoji}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{a.name} <span style={{ color: 'var(--muted)', fontSize: 12 }}>{a.ticker}</span></div>
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>{a.shares} acções {a.broker && `· ${a.broker}`}</div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 700 }}>{formatCurrency(val)}</div>
                  {a.currentPrice && <div style={{ fontSize: 11, color: 'var(--muted)' }}>{formatCurrency(a.currentPrice)}/un</div>}
                </div>
                <button onClick={() => removeStock(a.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: 4 }}><Trash2 size={13} /></button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Disclaimer */}
      <div style={{ padding: '12px 16px', borderRadius: 10, background: 'var(--surface2)', fontSize: 11, color: 'var(--muted)', marginBottom: 20 }}>
        <RefreshCw size={11} style={{ display: 'inline', marginRight: 4 }} />
        Dados demo — os preços são estáticos. Em breve: ligação automática à Binance, DEGIRO, Trading 212 via API.
      </div>
    </div>
  );
}
