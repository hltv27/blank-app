'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import { Subscription, Category, BillingCycle } from '@/lib/types';
import { POPULAR_SERVICES, CATEGORY_LABELS } from '@/lib/data';

interface Props {
  onClose: () => void;
  onSave: (sub: Omit<Subscription, 'id'>) => void;
  existing?: Subscription;
}

const COLORS = ['#7C3AED','#10B981','#3B82F6','#F59E0B','#EF4444','#EC4899','#06B6D4','#84CC16','#F97316','#1DB954'];

export default function AddSubscriptionModal({ onClose, onSave, existing }: Props) {
  const [name, setName] = useState(existing?.name ?? '');
  const [amount, setAmount] = useState(existing?.amount?.toString() ?? '');
  const [billingCycle, setBillingCycle] = useState<BillingCycle>(existing?.billingCycle ?? 'monthly');
  const [nextBillingDate, setNextBillingDate] = useState(existing?.nextBillingDate ?? new Date().toISOString().split('T')[0]);
  const [category, setCategory] = useState<Category>(existing?.category ?? 'other');
  const [color, setColor] = useState(existing?.color ?? COLORS[0]);
  const [emoji, setEmoji] = useState(existing?.emoji ?? '📱');
  const [active, setActive] = useState(existing?.active ?? true);
  const [cryptoPayment, setCryptoPayment] = useState(existing?.cryptoPayment ?? '');

  const CRYPTO_OPTIONS = [
    { id: '', label: 'Cartão / débito', emoji: '💳' },
    { id: 'btc', label: 'Bitcoin (BTC)', emoji: '₿' },
    { id: 'eth', label: 'Ethereum (ETH)', emoji: 'Ξ' },
    { id: 'usdt', label: 'Tether (USDT)', emoji: '₮' },
    { id: 'usdc', label: 'USD Coin (USDC)', emoji: '◎' },
    { id: 'bnb', label: 'BNB', emoji: '⬡' },
    { id: 'sol', label: 'Solana (SOL)', emoji: '◎' },
    { id: 'xrp', label: 'XRP', emoji: '✕' },
    { id: 'doge', label: 'Dogecoin (DOGE)', emoji: 'Ð' },
    { id: 'ada', label: 'Cardano (ADA)', emoji: '₳' },
    { id: 'avax', label: 'Avalanche (AVAX)', emoji: '▲' },
  ];

  const handleQuickFill = (svc: typeof POPULAR_SERVICES[0]) => {
    setName(svc.name);
    setEmoji(svc.emoji);
    setColor(svc.color);
    setCategory(svc.category as Category);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !amount) return;
    onSave({ name, amount: parseFloat(amount), currency: 'EUR', billingCycle, nextBillingDate, category, color, emoji, active, cryptoPayment: cryptoPayment || undefined });
    onClose();
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20,
    }} onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="card modal-in" style={{ width: '100%', maxWidth: 480, padding: 28, maxHeight: '90vh', overflowY: 'auto' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>{existing ? 'Editar' : 'Nova'} Subscrição</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: 4 }}>
            <X size={20} />
          </button>
        </div>

        {/* Quick fill */}
        {!existing && (
          <div style={{ marginBottom: 20 }}>
            <label>Serviços populares</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
              {POPULAR_SERVICES.slice(0, 12).map(svc => (
                <button key={svc.name} onClick={() => handleQuickFill(svc)} style={{
                  background: 'var(--surface2)', border: '1px solid var(--border)',
                  borderRadius: 8, padding: '5px 10px', cursor: 'pointer',
                  color: 'var(--text)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4,
                  transition: 'all 0.15s',
                }}>
                  <span>{svc.emoji}</span> {svc.name}
                </button>
              ))}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Emoji + Name */}
          <div style={{ display: 'grid', gridTemplateColumns: '60px 1fr', gap: 10 }}>
            <div>
              <label>Ícone</label>
              <input value={emoji} onChange={e => setEmoji(e.target.value)} maxLength={2} style={{ textAlign: 'center', fontSize: 22, padding: '8px 4px' }} />
            </div>
            <div>
              <label>Nome *</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="ex: Netflix" required />
            </div>
          </div>

          {/* Amount + Cycle */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label>Valor (€) *</label>
              <input type="number" step="0.01" min="0" value={amount} onChange={e => setAmount(e.target.value)} placeholder="0.00" required />
            </div>
            <div>
              <label>Ciclo</label>
              <select value={billingCycle} onChange={e => setBillingCycle(e.target.value as BillingCycle)}>
                <option value="monthly">Mensal</option>
                <option value="yearly">Anual</option>
                <option value="weekly">Semanal</option>
              </select>
            </div>
          </div>

          {/* Next billing + Category */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label>Próxima cobrança</label>
              <input type="date" value={nextBillingDate} onChange={e => setNextBillingDate(e.target.value)} />
            </div>
            <div>
              <label>Categoria</label>
              <select value={category} onChange={e => setCategory(e.target.value as Category)}>
                {Object.entries(CATEGORY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
          </div>

          {/* Color picker */}
          <div>
            <label>Cor</label>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
              {COLORS.map(c => (
                <button key={c} type="button" onClick={() => setColor(c)} style={{
                  width: 28, height: 28, borderRadius: '50%', background: c, border: 'none', cursor: 'pointer',
                  outline: color === c ? `3px solid white` : 'none',
                  outlineOffset: 2, transition: 'outline 0.15s',
                }} />
              ))}
            </div>
          </div>

          {/* Crypto payment */}
          <div>
            <label>Método de pagamento</label>
            <select value={cryptoPayment} onChange={e => setCryptoPayment(e.target.value)} style={{ marginTop: 4 }}>
              {CRYPTO_OPTIONS.map(o => (
                <option key={o.id} value={o.id}>{o.emoji} {o.label}</option>
              ))}
            </select>
          </div>

          {/* Active toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button type="button" onClick={() => setActive(!active)} style={{
              width: 42, height: 24, borderRadius: 12,
              background: active ? 'var(--accent)' : 'var(--surface2)',
              border: 'none', cursor: 'pointer', position: 'relative', transition: 'background 0.2s',
            }}>
              <div style={{
                width: 18, height: 18, borderRadius: '50%', background: 'white',
                position: 'absolute', top: 3, left: active ? 21 : 3, transition: 'left 0.2s',
              }} />
            </button>
            <span style={{ fontSize: 13, color: 'var(--muted)' }}>
              {active ? 'Subscrição ativa' : 'Subscrição pausada'}
            </span>
          </div>

          {/* Buttons */}
          <div style={{ display: 'flex', gap: 10, paddingTop: 4 }}>
            <button type="button" onClick={onClose} className="btn-ghost" style={{ flex: 1 }}>Cancelar</button>
            <button type="submit" className="btn-primary" style={{ flex: 1, justifyContent: 'center' }}>
              {existing ? 'Guardar' : 'Adicionar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
