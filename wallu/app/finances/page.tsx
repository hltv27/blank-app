'use client';

import { useEffect, useState } from 'react';
import { Plus, TrendingUp, TrendingDown, Trash2 } from 'lucide-react';
import { Transaction } from '@/lib/types';
import { getTransactions, saveTransactions, getSubscriptions, monthlyAmount, formatCurrency } from '@/lib/store';

const EMOJIS = ['💰','🏠','🛒','⚡','💼','🍽️','⛽','💊','🎓','✈️','🎮','📱','🛍️','💈','🏋️'];

export default function FinancesPage() {
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [subsCost, setSubsCost] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ description: '', amount: '', type: 'expense' as 'income' | 'expense', category: '', date: new Date().toISOString().split('T')[0], emoji: '🛒' });

  useEffect(() => {
    setTxns(getTransactions());
    const subs = getSubscriptions();
    setSubsCost(subs.reduce((a, s) => a + monthlyAmount(s), 0));
  }, []);

  const persist = (t: Transaction[]) => { setTxns(t); saveTransactions(t); };

  const income = txns.filter(t => t.type === 'income').reduce((a, t) => a + t.amount, 0);
  const expenses = txns.filter(t => t.type === 'expense').reduce((a, t) => a + t.amount, 0);
  const balance = income - expenses;
  const savingsRate = income > 0 ? Math.round(((income - expenses) / income) * 100) : 0;

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.description || !form.amount) return;
    const newTxn: Transaction = {
      id: Date.now().toString(),
      description: form.description,
      amount: parseFloat(form.amount),
      type: form.type,
      category: form.category || (form.type === 'income' ? 'Rendimento' : 'Despesa'),
      date: form.date,
      emoji: form.emoji,
    };
    persist([newTxn, ...txns]);
    setForm({ description: '', amount: '', type: 'expense', category: '', date: new Date().toISOString().split('T')[0], emoji: '🛒' });
    setShowForm(false);
  };

  const handleDelete = (id: string) => persist(txns.filter(t => t.id !== id));

  // Group by date
  const grouped = txns.reduce<Record<string, Transaction[]>>((acc, t) => {
    const key = t.date;
    if (!acc[key]) acc[key] = [];
    acc[key].push(t);
    return acc;
  }, {});

  const sortedDates = Object.keys(grouped).sort((a, b) => b.localeCompare(a));

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.4px' }}>Finanças</h1>
          <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 4 }}>Visão geral do teu mês</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} /> Nova transação
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 24 }}>
        {[
          { label: 'Receita', value: formatCurrency(income), icon: '💰', color: '#10B981' },
          { label: 'Despesas', value: formatCurrency(expenses), icon: '🛒', color: '#EF4444' },
          { label: 'Subscrições', value: formatCurrency(subsCost), icon: '📦', color: '#7C3AED' },
          { label: 'Taxa de poupança', value: `${savingsRate}%`, icon: savingsRate >= 20 ? '🏆' : savingsRate >= 0 ? '📈' : '⚠️', color: savingsRate >= 20 ? '#10B981' : savingsRate >= 0 ? '#F59E0B' : '#EF4444' },
        ].map(c => (
          <div key={c.label} className="card" style={{ padding: '18px 20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <p style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>{c.label}</p>
                <p style={{ fontSize: 22, fontWeight: 700, color: c.color }}>{c.value}</p>
              </div>
              <span style={{ fontSize: 22 }}>{c.icon}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Balance bar */}
      <div className="card" style={{ padding: '18px 22px', marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <span style={{ fontSize: 13, fontWeight: 600 }}>Balanço do mês</span>
          <span style={{ fontSize: 16, fontWeight: 700, color: balance >= 0 ? '#10B981' : '#EF4444' }}>
            {balance >= 0 ? '+' : ''}{formatCurrency(balance)}
          </span>
        </div>
        <div style={{ height: 8, background: 'var(--surface2)', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            width: income > 0 ? `${Math.min((income / (income + expenses)) * 100, 100)}%` : '0%',
            background: 'linear-gradient(90deg, #10B981, #7C3AED)',
            borderRadius: 4, transition: 'width 0.6s ease',
          }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
          <span style={{ fontSize: 11, color: '#10B981', display: 'flex', alignItems: 'center', gap: 3 }}>
            <TrendingUp size={11} /> Receita {formatCurrency(income)}
          </span>
          <span style={{ fontSize: 11, color: '#EF4444', display: 'flex', alignItems: 'center', gap: 3 }}>
            <TrendingDown size={11} /> Despesas {formatCurrency(expenses)}
          </span>
        </div>
      </div>

      {/* Add transaction form */}
      {showForm && (
        <div className="card fade-in" style={{ padding: 20, marginBottom: 20 }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>Nova transação</h3>
          <form onSubmit={handleAdd}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
              <div>
                <label>Descrição *</label>
                <input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="ex: Supermercado" required />
              </div>
              <div>
                <label>Valor (€) *</label>
                <input type="number" step="0.01" min="0" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} placeholder="0.00" required />
              </div>
              <div>
                <label>Tipo</label>
                <select value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value as 'income' | 'expense' }))}>
                  <option value="expense">Despesa</option>
                  <option value="income">Receita</option>
                </select>
              </div>
              <div>
                <label>Data</label>
                <input type="date" value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} />
              </div>
              <div>
                <label>Categoria</label>
                <input value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} placeholder="ex: Alimentação" />
              </div>
              <div>
                <label>Emoji</label>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
                  {EMOJIS.map(em => (
                    <button key={em} type="button" onClick={() => setForm(f => ({ ...f, emoji: em }))} style={{
                      fontSize: 18, background: form.emoji === em ? 'var(--accent)' : 'var(--surface2)',
                      border: '1px solid var(--border)', borderRadius: 7, width: 34, height: 34, cursor: 'pointer',
                    }}>
                      {em}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button type="button" className="btn-ghost" onClick={() => setShowForm(false)} style={{ flex: 1 }}>Cancelar</button>
              <button type="submit" className="btn-primary" style={{ flex: 1, justifyContent: 'center' }}>Adicionar</button>
            </div>
          </form>
        </div>
      )}

      {/* Transactions list grouped by date */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {sortedDates.map(date => (
          <div key={date}>
            <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {new Date(date + 'T00:00:00').toLocaleDateString('pt-PT', { weekday: 'long', day: 'numeric', month: 'long' })}
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {grouped[date].map(t => (
                <div key={t.id} className="card fade-in" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '13px 16px' }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: 10, flexShrink: 0,
                    background: t.type === 'income' ? '#10B98122' : '#EF444422',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17,
                  }}>
                    {t.emoji}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 500 }}>{t.description}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 1 }}>{t.category}</div>
                  </div>
                  <span style={{
                    fontSize: 15, fontWeight: 700,
                    color: t.type === 'income' ? '#10B981' : '#EF4444',
                  }}>
                    {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                  </span>
                  <button onClick={() => handleDelete(t.id)} style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--muted)', padding: 4, borderRadius: 6,
                    display: 'flex', alignItems: 'center',
                  }}>
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
