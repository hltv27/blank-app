'use client';

import { Subscription } from '@/lib/types';
import { daysUntil, formatCurrency } from '@/lib/store';
import { useT } from '@/lib/i18n';

interface Props { subscriptions: Subscription[]; }

export default function UpcomingRenewals({ subscriptions }: Props) {
  const t = useT();

  const upcoming = subscriptions
    .filter(s => s.active)
    .map(s => ({ ...s, days: daysUntil(s.nextBillingDate) }))
    .filter(s => s.days >= 0 && s.days <= 30)
    .sort((a, b) => a.days - b.days)
    .slice(0, 6);

  const urgencyColor = (days: number) => {
    if (days <= 3) return '#EF4444';
    if (days <= 7) return '#F59E0B';
    return 'var(--muted)';
  };

  const urgencyLabel = (days: number) => {
    if (days === 0) return t('common.today');
    if (days === 1) return t('common.tomorrow');
    return t('renewals.days', { n: days });
  };

  if (upcoming.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--muted)', fontSize: 14 }}>
        {t('renewals.none')}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {upcoming.map(sub => (
        <div key={sub.id} className="card-sm" style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '12px 14px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 34, height: 34, borderRadius: 9,
              background: `${sub.color}22`,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
            }}>
              {sub.emoji}
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{sub.name}</div>
              <div style={{ fontSize: 11, color: 'var(--muted)' }}>
                {new Date(sub.nextBillingDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
            <span style={{ fontSize: 13, fontWeight: 700 }}>{formatCurrency(sub.amount, sub.currency)}</span>
            <span style={{ fontSize: 11, fontWeight: 600, color: urgencyColor(sub.days) }}>
              {urgencyLabel(sub.days)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
