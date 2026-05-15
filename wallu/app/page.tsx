'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, TrendingUp, TrendingDown } from 'lucide-react';
import StatCard from '@/components/StatCard';
import UpcomingRenewals from '@/components/UpcomingRenewals';
import { Subscription, Transaction } from '@/lib/types';
import { getSubscriptions, getTransactions, monthlyAmount, formatCurrency } from '@/lib/store';
import { CATEGORY_COLORS } from '@/lib/data';
import { useT } from '@/lib/i18n';

export default function DashboardPage() {
  const t = useT();
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [txns, setTxns] = useState<Transaction[]>([]);

  useEffect(() => {
    setSubs(getSubscriptions());
    setTxns(getTransactions());
  }, []);

  const totalSubs = subs.reduce((acc, s) => acc + monthlyAmount(s), 0);
  const activeSubs = subs.filter(s => s.active).length;
  const income = txns.filter(t => t.type === 'income').reduce((a, t) => a + t.amount, 0);
  const expenses = txns.filter(t => t.type === 'expense').reduce((a, t) => a + t.amount, 0);
  const balance = income - expenses;

  const categoryTotals: Record<string, number> = {};
  subs.filter(s => s.active).forEach(s => {
    categoryTotals[s.category] = (categoryTotals[s.category] || 0) + monthlyAmount(s);
  });
  const topCategories = Object.entries(categoryTotals).sort((a, b) => b[1] - a[1]).slice(0, 4);

  const now = new Date();
  const h = now.getHours();
  const greeting = h < 12 ? t('dashboard.greeting_morning') : h < 18 ? t('dashboard.greeting_afternoon') : t('dashboard.greeting_evening');

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.4px' }}>{greeting} 👋</h1>
        <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 4 }}>
          {now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
        </p>
      </div>

      <div className="stats-grid">
        <StatCard label={t('dashboard.subs_month')} value={formatCurrency(totalSubs)} sub={t('dashboard.n_active', { n: activeSubs })} icon="📦" accent="#7C3AED" trend="neutral" />
        <StatCard label={t('dashboard.income')} value={formatCurrency(income)} sub={t('dashboard.this_month')} icon="💰" accent="#10B981" trend="up" />
        <StatCard label={t('dashboard.expenses')} value={formatCurrency(expenses)} sub={t('dashboard.this_month')} icon="🛒" accent="#EF4444" trend="down" />
        <StatCard label={t('dashboard.balance')} value={formatCurrency(balance)} sub={balance >= 0 ? t('dashboard.positive') : t('dashboard.deficit')} icon="📊" accent={balance >= 0 ? '#10B981' : '#EF4444'} trend={balance >= 0 ? 'up' : 'down'} />
      </div>

      <div className="dashboard-grid">
        <div className="card" style={{ padding: 22 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 style={{ fontSize: 15, fontWeight: 700 }}>{t('dashboard.upcoming')}</h2>
            <Link href="/subscriptions" style={{ textDecoration: 'none' }}>
              <span style={{ fontSize: 12, color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 3 }}>
                {t('common.see_all')} <ArrowRight size={12} />
              </span>
            </Link>
          </div>
          <UpcomingRenewals subscriptions={subs} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="card" style={{ padding: 22 }}>
            <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>{t('dashboard.by_category')}</h2>
            {topCategories.length === 0 ? (
              <p style={{ color: 'var(--muted)', fontSize: 13 }}>{t('dashboard.no_active_subs')}</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {topCategories.map(([cat, total]) => {
                  const pct = Math.round((total / totalSubs) * 100);
                  return (
                    <div key={cat}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                        <span style={{ fontSize: 13, fontWeight: 500, textTransform: 'capitalize' }}>{cat}</span>
                        <span style={{ fontSize: 13, color: 'var(--muted)' }}>{formatCurrency(total)} · {pct}%</span>
                      </div>
                      <div style={{ height: 5, background: 'var(--surface2)', borderRadius: 3 }}>
                        <div style={{ height: '100%', borderRadius: 3, background: CATEGORY_COLORS[cat] || 'var(--accent)', width: `${pct}%`, transition: 'width 0.5s ease' }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="card" style={{ padding: 22 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: 15, fontWeight: 700 }}>{t('dashboard.recent_txns')}</h2>
              <Link href="/finances" style={{ textDecoration: 'none' }}>
                <span style={{ fontSize: 12, color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 3 }}>
                  {t('common.see_all')} <ArrowRight size={12} />
                </span>
              </Link>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {txns.slice(0, 5).map(tx => (
                <div key={tx.id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, background: tx.type === 'income' ? '#10B98122' : '#EF444422', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
                    {tx.emoji}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{tx.description}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>
                      {new Date(tx.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
                    </div>
                  </div>
                  <span style={{ fontSize: 13, fontWeight: 700, color: tx.type === 'income' ? '#10B981' : '#EF4444', display: 'flex', alignItems: 'center', gap: 3 }}>
                    {tx.type === 'income' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    {tx.type === 'income' ? '+' : '-'}{formatCurrency(tx.amount)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
