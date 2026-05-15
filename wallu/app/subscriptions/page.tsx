'use client';

import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, PauseCircle, PlayCircle, Search } from 'lucide-react';
import { Subscription } from '@/lib/types';
import { getSubscriptions, saveSubscriptions, monthlyAmount, formatCurrency, daysUntil } from '@/lib/store';
import AddSubscriptionModal from '@/components/AddSubscriptionModal';
import { CATEGORY_LABELS } from '@/lib/data';
import { useT } from '@/lib/i18n';

export default function SubscriptionsPage() {
  const t = useT();
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Subscription | undefined>();
  const [search, setSearch] = useState('');
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'paused'>('all');

  useEffect(() => { setSubs(getSubscriptions()); }, []);

  const persist = (updated: Subscription[]) => { setSubs(updated); saveSubscriptions(updated); };

  const handleSave = (data: Omit<Subscription, 'id'>) => {
    if (editing) {
      persist(subs.map(s => s.id === editing.id ? { ...data, id: editing.id } : s));
    } else {
      persist([...subs, { ...data, id: Date.now().toString() }]);
    }
    setEditing(undefined);
  };

  const handleDelete = (id: string) => {
    if (confirm(t('subscriptions.confirm_delete'))) persist(subs.filter(s => s.id !== id));
  };

  const handleToggle = (id: string) => {
    persist(subs.map(s => s.id === id ? { ...s, active: !s.active } : s));
  };

  const filtered = subs
    .filter(s => filterActive === 'all' ? true : filterActive === 'active' ? s.active : !s.active)
    .filter(s => s.name.toLowerCase().includes(search.toLowerCase()));

  const totalMonthly = subs.filter(s => s.active).reduce((a, s) => a + monthlyAmount(s), 0);
  const totalYearly = totalMonthly * 12;

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.4px' }}>{t('subscriptions.title')}</h1>
          <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 4 }}>
            {subs.filter(s => s.active).length} {t('subscriptions.active').toLowerCase()} · {formatCurrency(totalMonthly)}/mo · {formatCurrency(totalYearly)}/yr
          </p>
        </div>
        <button className="btn-primary" onClick={() => { setEditing(undefined); setShowModal(true); }}>
          <Plus size={16} /> {t('subscriptions.add')}
        </button>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
          <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)' }} />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder={t('common.search')} style={{ paddingLeft: 34 }} />
        </div>
        {(['all', 'active', 'paused'] as const).map(f => (
          <button key={f} onClick={() => setFilterActive(f)} style={{
            padding: '8px 16px', borderRadius: 8, border: '1px solid var(--border)', cursor: 'pointer',
            background: filterActive === f ? 'var(--accent)' : 'var(--surface2)',
            color: filterActive === f ? 'white' : 'var(--muted)',
            fontSize: 13, fontWeight: 500, transition: 'all 0.15s',
          }}>
            {f === 'all' ? t('subscriptions.all') : f === 'active' ? t('subscriptions.active') : t('subscriptions.paused')}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--muted)' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📭</div>
          <p style={{ fontSize: 15 }}>{t('subscriptions.empty')}</p>
          <p style={{ fontSize: 13, marginTop: 6 }}>{t('subscriptions.empty_sub')}</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.map(sub => {
            const days = daysUntil(sub.nextBillingDate);
            const urgent = days >= 0 && days <= 7;
            return (
              <div key={sub.id} className="card fade-in" style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px 20px', opacity: sub.active ? 1 : 0.6, transition: 'opacity 0.2s' }}>
                <div style={{ width: 46, height: 46, borderRadius: 12, flexShrink: 0, background: `${sub.color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, border: `2px solid ${sub.color}44` }}>
                  {sub.emoji}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 15, fontWeight: 600 }}>{sub.name}</span>
                    {!sub.active && (
                      <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 99, background: 'var(--surface2)', color: 'var(--muted)', fontWeight: 600 }}>
                        {t('subscriptions.paused_badge')}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    <span style={{ textTransform: 'capitalize' }}>{CATEGORY_LABELS[sub.category] || sub.category}</span>
                    <span>·</span>
                    <span>{sub.billingCycle === 'monthly' ? t('common.monthly') : sub.billingCycle === 'yearly' ? t('common.yearly') : t('common.weekly')}</span>
                    {sub.cryptoPayment && (
                      <>
                        <span>·</span>
                        <span style={{ color: '#F59E0B', fontWeight: 600 }}>⬡ {sub.cryptoPayment.toUpperCase()}</span>
                      </>
                    )}
                    {sub.active && (
                      <>
                        <span>·</span>
                        <span style={{ color: urgent ? (days <= 3 ? '#EF4444' : '#F59E0B') : 'var(--muted)' }}>
                          {days === 0 ? t('common.today') : days === 1 ? t('common.tomorrow') : days < 0 ? t('common.overdue') : `${days}d`}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                <div style={{ textAlign: 'right', minWidth: 80 }}>
                  <div style={{ fontSize: 16, fontWeight: 700 }}>{formatCurrency(sub.amount)}</div>
                  {sub.billingCycle !== 'monthly' && (
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>{formatCurrency(monthlyAmount(sub))}/mo</div>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                  <button onClick={() => handleToggle(sub.id)} style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, width: 32, height: 32, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: sub.active ? 'var(--yellow)' : 'var(--green)', transition: 'all 0.15s' }}>
                    {sub.active ? <PauseCircle size={15} /> : <PlayCircle size={15} />}
                  </button>
                  <button onClick={() => { setEditing(sub); setShowModal(true); }} style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, width: 32, height: 32, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', transition: 'all 0.15s' }}>
                    <Pencil size={14} />
                  </button>
                  <button onClick={() => handleDelete(sub.id)} style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, width: 32, height: 32, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--red)', transition: 'all 0.15s' }}>
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showModal && (
        <AddSubscriptionModal
          onClose={() => { setShowModal(false); setEditing(undefined); }}
          onSave={handleSave}
          existing={editing}
        />
      )}
    </div>
  );
}
