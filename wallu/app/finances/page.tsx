'use client';

import { useEffect, useState } from 'react';
import { Plus, TrendingUp, TrendingDown, Trash2 } from 'lucide-react';
import { Transaction } from '@/lib/types';
import { getTransactions, saveTransactions, getSubscriptions, monthlyAmount, formatCurrency } from '@/lib/store';
import { useT } from '@/lib/i18n';

const EMOJIS = ['💰','🏠','🛒','⚡','💼','🍽️','⛽','💊','🎓','✈️','🎮','📱','🛍️','💈','🏋️'];

export default function FinancesPage() {
  const t = useT();
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [subsCost, setSubsCost] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ description: '', amount: '', type: 'expense' as 'income' | 'expense', category: '', date: new Date().toISOString().split('T')[0], emoji: '🛒' });

  useEffect(() => {
    setTxns(getTransactions());
    const subs = getSubscriptions();
    setSubsCost(subs.reduce((a, s) => a + monthlyAmount(s), 0));
  }, []);

  const persist = (tx: Transaction[]) => { setTxns(tx); saveTransactions(tx); };

  const income = txns.filter(tx => tx.type === 'income').reduce((a, tx) => a + tx.amount, 0);
  const expenses = txns.filter(tx => tx.type === 'expense').reduce((a, tx) => a + tx.amount, 0);
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
      category: form.category || (form.type === 'income' ? t('finances.default_income_cat') : t('finances.default_expense_cat')),
      date: form.date,
      emoji: form.emoji,
    };
    persist([newTxn, ...txns]);
    setForm({ description: '', amount: '', type: 'expense', category: '', date: new Date().toISOString().split('T')[0], emoji: '🛒' });
    setShowForm(false);
  };

  const handleDelete = (id: string) => persist(txns.filter(tx => tx.id !== id));

  const grouped = txns.reduce<Record<string, Transaction[]>>((acc, tx) => {
    if (!acc[tx.date]) acc[tx.date] = [];
    acc[tx.date].push(tx);
    return acc;
  }, {});
  const sortedDates = Object.keys(grouped).sort((a, b) => b.localeCompare(a));

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.4px' }}>{t('finances.title')}</h1>
          <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 4 }}>{t('finances.subtitle')}</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} /> {t('finances.new_txn')}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 24 }}>
        {[
          { label: t('finances.income'),        value: formatCurrency(income),     icon: '💰', color: '#10B981' },
          { label: t('finances.expenses'),       value: formatCurrency(expenses),   icon: '🛒', color: '#EF4444' },
          { label: t('finances.subscriptions'), value: formatCurrency(subsCost),   icon: '📦', color: '#7C3AED' },
          { label: t('finances.savings_rate'),  value: `${savingsRate}%`,          icon: savingsRate >= 20 ? '🏆' : savingsRate >= 0 ? '📈' : '⚠️', color: savingsRate >= 20 ? '#10B981' : savingsRate >= 0 ? '#F59E0B' : '#EF4444' },
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

      <div className="card" style={{ padding: '18px 22px', marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <span style={{ fontSize: 13, fontWeight: 600 }}>{t('finances.monthly_balance')}</span>
          <span style={{ fontSize: 16, fontWeight: 700, color: balance >= 0 ? '#10B981' : '#EF4444' }}>
            {balance >= 0 ? '+' : ''}{formatCurrency(balance)}
          </span>
        </div>
        <div style={{ height: 8, background: 'var(--surface2)', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: income > 0 ? `${Math.min((income / (income + expenses)) * 100, 100)}%` : '0%', background: 'linear-gradient(90deg, #10B981, #7C3AED)', borderRadius: 4, transition: 'width 0.6s ease' }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
          <span style={{ fontSize: 11, color: '#10B981', display: 'flex', alignItems: 'center', gap: 3 }}>
            <TrendingUp size={11} /> {t('finances.income')} {formatCurrency(income)}
          </span>
          <span style={{ fontSize: 11, color: '#EF4444', display: 'flex', alignItems: 'center', gap: 3 }}>
            <TrendingDown size={11} /> {t('finances.expenses')} {formatCurrency(expenses)}
          </span>
        </div>
      </div>

      {showForm && (
        <div className="card fade-in" style={{ padding: 20, marginBottom: 20 }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>{t('finances.new_title')}</h3>
          <form onSubmit={handleAdd}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
              <div>
                <label>{t('finances.description')}</label>
                <input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder={t('finances.desc_placeholder')} required />
              </div>
              <div>
                <label>{t('finances.amount')}</label>
                <input type="number" step="0.01" min="0" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} placeholder="0.00" required />
              </div>
              <div>
                <label>{t('finances.type')}</label>
                <select value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value as 'income' | 'expense' }))}>
                  <option value="expense">{t('finances.expense')}</option>
                  <option value="income">{t('finances.income_opt')}</option>
                </select>
              </div>
              <div>
                <label>{t('finances.date')}</label>
                <input type="date" value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} />
              </div>
              <div>
                <label>{t('finances.category')}</label>
                <input value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} placeholder={t('finances.cat_placeholder')} />
              </div>
              <div>
                <label>Emoji</label>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
                  {EMOJIS.map(em => (
                    <button key={em} type="button" onClick={() => setForm(f => ({ ...f, emoji: em }))} style={{ fontSize: 18, background: form.emoji === em ? 'var(--accent)' : 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 7, width: 34, height: 34, cursor: 'pointer' }}>
                      {em}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button type="button" className="btn-ghost" onClick={() => setShowForm(false)} style={{ flex: 1 }}>{t('common.cancel')}</button>
              <button type="submit" className="btn-primary" style={{ flex: 1, justifyContent: 'center' }}>{t('common.add')}</button>
            </div>
          </form>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {sortedDates.map(date => (
          <div key={date}>
            <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {new Date(date + 'T00:00:00').toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })}
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {grouped[date].map(tx => (
                <div key={tx.id} className="card fade-in" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '13px 16px' }}>
                  <div style={{ width: 38, height: 38, borderRadius: 10, flexShrink: 0, background: tx.type === 'income' ? '#10B98122' : '#EF444422', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17 }}>
                    {tx.emoji}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 500 }}>{tx.description}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 1 }}>{tx.category}</div>
                  </div>
                  <span style={{ fontSize: 15, fontWeight: 700, color: tx.type === 'income' ? '#10B981' : '#EF4444' }}>
                    {tx.type === 'income' ? '+' : '-'}{formatCurrency(tx.amount)}
                  </span>
                  <button onClick={() => handleDelete(tx.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: 4, borderRadius: 6, display: 'flex', alignItems: 'center' }}>
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
