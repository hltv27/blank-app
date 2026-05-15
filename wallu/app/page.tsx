'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, TrendingUp, TrendingDown } from 'lucide-react';
import StatCard from '@/components/StatCard';
import UpcomingRenewals from '@/components/UpcomingRenewals';
import { Subscription, Transaction } from '@/lib/types';
import { getSubscriptions, getTransactions, monthlyAmount, formatCurrency } from '@/lib/store';
import { CATEGORY_COLORS } from '@/lib/data';

export default function DashboardPage() {
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

  // Category breakdown
  const categoryTotals: Record<string, number> = {};
  subs.filter(s => s.active).forEach(s => {
    categoryTotals[s.category] = (categoryTotals[s.category] || 0) + monthlyAmount(s);
  });
  const topCategories = Object.entries(categoryTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4);

  const now = new Date();
  const greeting = now.getHours() < 12 ? 'Bom dia' : now.getHours() < 18 ? 'Boa tarde' : 'Boa noite';

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.4px' }}>{greeting} 👋</h1>
        <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 4 }}>
          {now.toLocaleDateString('pt-PT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
        </p>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <StatCard
          label="Subscrições/mês"
          value={formatCurrency(totalSubs)}
          sub={`${activeSubs} ativas`}
          icon="📦"
          accent="#7C3AED"
          trend="neutral"
        />
        <StatCard
          label="Receita"
          value={formatCurrency(income)}
          sub="Este mês"
          icon="💰"
          accent="#10B981"
          trend="up"
        />
        <StatCard
          label="Despesas"
          value={formatCurrency(expenses)}
          sub="Este mês"
          icon="🛒"
          accent="#EF4444"
          trend="down"
        />
        <StatCard
          label="Saldo"
          value={formatCurrency(balance)}
          sub={balance >= 0 ? '✅ No positivo' : '⚠️ Em défice'}
          icon="📊"
          accent={balance >= 0 ? '#10B981' : '#EF4444'}
          trend={balance >= 0 ? 'up' : 'down'}
        />
      </div>

      {/* Main content: 2 columns */}
      <div className="dashboard-grid">

        {/* Upcoming renewals */}
        <div className="card" style={{ padding: 22 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 style={{ fontSize: 15, fontWeight: 700 }}>Renovações próximas</h2>
            <Link href="/subscriptions" style={{ textDecoration: 'none' }}>
              <span style={{ fontSize: 12, color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 3 }}>
                Ver todas <ArrowRight size={12} />
              </span>
            </Link>
          </div>
          <UpcomingRenewals subscriptions={subs} />
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Category breakdown */}
          <div className="card" style={{ padding: 22 }}>
            <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Por categoria</h2>
            {topCategories.length === 0 ? (
              <p style={{ color: 'var(--muted)', fontSize: 13 }}>Sem subscrições ativas</p>
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
                        <div style={{
                          height: '100%', borderRadius: 3,
                          background: CATEGORY_COLORS[cat] || 'var(--accent)',
                          width: `${pct}%`, transition: 'width 0.5s ease',
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Recent transactions */}
          <div className="card" style={{ padding: 22 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: 15, fontWeight: 700 }}>Transações recentes</h2>
              <Link href="/finances" style={{ textDecoration: 'none' }}>
                <span style={{ fontSize: 12, color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 3 }}>
                  Ver todas <ArrowRight size={12} />
                </span>
              </Link>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {txns.slice(0, 5).map(t => (
                <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 8,
                    background: t.type === 'income' ? '#10B98122' : '#EF444422',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 14,
                  }}>
                    {t.emoji}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{t.description}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>
                      {new Date(t.date).toLocaleDateString('pt-PT', { day: 'numeric', month: 'short' })}
                    </div>
                  </div>
                  <span style={{
                    fontSize: 13, fontWeight: 700,
                    color: t.type === 'income' ? '#10B981' : '#EF4444',
                    display: 'flex', alignItems: 'center', gap: 3,
                  }}>
                    {t.type === 'income' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
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
