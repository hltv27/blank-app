'use client';

import { useState } from 'react';
import { CheckCircle, Copy } from 'lucide-react';
import { useT, useLang, LANGUAGES } from '@/lib/i18n';

const CRYPTO_WALLETS = [
  { id: 'btc', name: 'Bitcoin', symbol: 'BTC', emoji: '₿', color: '#F7931A', address: '3FZbgi29cpjq2GjdwV8eyHuJJnkLtktZc5' },
  { id: 'eth', name: 'Ethereum', symbol: 'ETH', emoji: 'Ξ', color: '#627EEA', address: '0x71C7656EC7ab88b098defB751B7401B5f6d8976F' },
  { id: 'usdt', name: 'Tether', symbol: 'USDT', emoji: '₮', color: '#26A17B', address: 'TN3W4H6rK2ce4vX9YnFQHwKx6C2XmzHN' },
  { id: 'usdc', name: 'USD Coin', symbol: 'USDC', emoji: '◎', color: '#2775CA', address: '0x71C7656EC7ab88b098defB751B7401B5f6d8976F' },
  { id: 'bnb', name: 'BNB', symbol: 'BNB', emoji: '⬡', color: '#F3BA2F', address: 'bnb1grpf0955h0ykzq3ar5nmum7y6gdfl6lx8xu7hm' },
  { id: 'sol', name: 'Solana', symbol: 'SOL', emoji: '◎', color: '#9945FF', address: 'DRpbCBMxVnDK7maPdrC6P6nHZs6kGNbMjFgpxjCjZmh' },
  { id: 'xrp', name: 'XRP', symbol: 'XRP', emoji: '✕', color: '#00AAE4', address: 'rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh' },
  { id: 'doge', name: 'Dogecoin', symbol: 'DOGE', emoji: 'Ð', color: '#C2A633', address: 'D7Y55bgc8DFGzdHYR1WMV2RnMVnpuMZGaG' },
  { id: 'ada', name: 'Cardano', symbol: 'ADA', emoji: '₳', color: '#0D1E2D', address: 'addr1qxy8u...addr_shortened' },
  { id: 'avax', name: 'Avalanche', symbol: 'AVAX', emoji: '▲', color: '#E84142', address: '0x71C7656EC7ab88b098defB751B7401B5f6d8976F' },
];

export default function SettingsPage() {
  const t = useT();
  const { lang, setLang } = useLang();
  const [saved, setSaved] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState('free');
  const [selectedCrypto, setSelectedCrypto] = useState('btc');
  const [copied, setCopied] = useState(false);

  const PLANS = [
    { id: 'free', label: t('settings.plan_free'), price: t('settings.price_free'), features: [t('settings.free_f1'), t('settings.free_f2'), t('settings.free_f3')] },
    { id: 'pro', label: t('settings.plan_pro'), price: t('settings.price_pro'), features: [t('settings.pro_f1'), t('settings.pro_f2'), t('settings.pro_f3'), t('settings.pro_f4'), t('settings.pro_f5'), t('settings.pro_f6')] },
    { id: 'lifetime', label: t('settings.plan_lifetime'), price: t('settings.price_lifetime'), features: [t('settings.life_f1'), t('settings.life_f2'), t('settings.life_f3'), t('settings.life_f4')] },
  ];

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const copyAddress = (addr: string) => {
    navigator.clipboard.writeText(addr).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const activeCrypto = CRYPTO_WALLETS.find(c => c.id === selectedCrypto)!;

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.4px' }}>{t('settings.title')}</h1>
        <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 4 }}>{t('settings.subtitle')}</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Language */}
        <div className="card" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>{t('settings.language_section')}</h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {LANGUAGES.map(l => (
              <button key={l.code} onClick={() => setLang(l.code)}
                style={{
                  padding: '7px 14px', borderRadius: 20, fontSize: 13, cursor: 'pointer',
                  background: lang === l.code ? 'rgba(124,58,237,0.15)' : 'var(--surface2)',
                  border: lang === l.code ? '1.5px solid var(--accent)' : '1.5px solid var(--border)',
                  color: lang === l.code ? 'var(--accent)' : 'var(--text)',
                  fontWeight: lang === l.code ? 600 : 400,
                  transition: 'all 0.15s',
                }}>
                {l.flag} {l.label}
              </button>
            ))}
          </div>
        </div>

        {/* Profile */}
        <div className="card" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>{t('settings.profile')}</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label>{t('settings.name_label')}</label>
              <input placeholder={t('settings.name_placeholder')} defaultValue="Wallu User" />
            </div>
            <div>
              <label>{t('settings.email_label')}</label>
              <input type="email" placeholder={t('settings.email_placeholder')} />
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div className="card" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>{t('settings.preferences')}</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label>{t('settings.currency')}</label>
              <select defaultValue="EUR">
                <option value="EUR">EUR — Euro €</option>
                <option value="USD">USD — Dollar $</option>
                <option value="GBP">GBP — Pound £</option>
                <option value="BRL">BRL — Real R$</option>
              </select>
            </div>
            <div>
              <label>{t('settings.month_start')}</label>
              <select defaultValue="1">
                {Array.from({ length: 28 }, (_, i) => i + 1).map(d => (
                  <option key={d} value={d}>{t('settings.day_n', { n: d })}</option>
                ))}
              </select>
            </div>
            <div>
              <label>{t('settings.reminder')}</label>
              <select defaultValue="3">
                <option value="1">{t('settings.day_1_before')}</option>
                <option value="3">{t('settings.days_before', { n: 3 })}</option>
                <option value="7">{t('settings.days_before', { n: 7 })}</option>
                <option value="14">{t('settings.days_before', { n: 14 })}</option>
              </select>
            </div>
          </div>
        </div>

        {/* Data */}
        <div className="card" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>{t('settings.data_section')}</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <button className="btn-ghost" style={{ textAlign: 'left', justifyContent: 'flex-start' }}
              onClick={() => {
                const data = {
                  subscriptions: localStorage.getItem('wallu_subscriptions'),
                  transactions: localStorage.getItem('wallu_transactions'),
                };
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = 'wallu-backup.json'; a.click();
              }}>
              {t('settings.export')}
            </button>
            <button className="btn-ghost" style={{ textAlign: 'left', justifyContent: 'flex-start', color: 'var(--red)', borderColor: '#EF444433' }}
              onClick={() => {
                if (confirm(t('settings.confirm_delete'))) {
                  localStorage.removeItem('wallu_subscriptions');
                  localStorage.removeItem('wallu_transactions');
                  window.location.reload();
                }
              }}>
              {t('settings.delete_data')}
            </button>
          </div>
        </div>

        {/* Subscription Plans */}
        <div className="card" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>{t('settings.plan_title')}</h2>
          <p style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 16 }}>{t('settings.plan_sub')}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 16 }}>
            {PLANS.map(plan => (
              <button key={plan.id} onClick={() => setSelectedPlan(plan.id)}
                style={{
                  background: selectedPlan === plan.id ? 'rgba(124,58,237,0.15)' : 'var(--surface2)',
                  border: selectedPlan === plan.id ? '1.5px solid var(--accent)' : '1.5px solid var(--border)',
                  borderRadius: 12, padding: '14px 12px', cursor: 'pointer', textAlign: 'left',
                }}>
                <div style={{ fontWeight: 700, fontSize: 13, color: selectedPlan === plan.id ? 'var(--accent)' : 'var(--text)', marginBottom: 4 }}>{plan.label}</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>{plan.price}</div>
                {plan.features.map(f => (
                  <div key={f} style={{ fontSize: 11, color: 'var(--muted)', lineHeight: 1.7 }}>✓ {f}</div>
                ))}
              </button>
            ))}
          </div>
          {selectedPlan !== 'free' && (
            <div style={{ background: 'var(--surface2)', borderRadius: 12, padding: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>{t('settings.pay_crypto')}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
                {CRYPTO_WALLETS.map(c => (
                  <button key={c.id} onClick={() => setSelectedCrypto(c.id)}
                    style={{
                      padding: '5px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: 'pointer',
                      background: selectedCrypto === c.id ? c.color + '33' : 'transparent',
                      border: selectedCrypto === c.id ? `1.5px solid ${c.color}` : '1.5px solid var(--border)',
                      color: selectedCrypto === c.id ? c.color : 'var(--muted)',
                    }}>
                    {c.symbol}
                  </button>
                ))}
              </div>
              <div style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6 }}>{activeCrypto.name} address</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{
                    flex: 1, background: 'var(--surface)', border: '1px solid var(--border)',
                    borderRadius: 8, padding: '8px 12px', fontSize: 12, fontFamily: 'monospace',
                    wordBreak: 'break-all', color: 'var(--text)',
                  }}>{activeCrypto.address}</div>
                  <button className="btn-ghost" onClick={() => copyAddress(activeCrypto.address)}
                    style={{ padding: 10, flexShrink: 0, color: copied ? '#10B981' : 'var(--muted)' }}>
                    {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
                  </button>
                </div>
              </div>
              <div style={{ fontSize: 11, color: 'var(--muted)', lineHeight: 1.6, padding: '10px 12px', background: 'rgba(124,58,237,0.08)', borderRadius: 8 }}>
                {t('settings.crypto_note')} <strong style={{ color: 'var(--accent)' }}>support@wallu.app</strong> {t('settings.crypto_activate')}
              </div>
            </div>
          )}
        </div>

        {/* About */}
        <div className="card" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>{t('settings.about_title')}</h2>
          <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.8 }}>
            <p><strong style={{ color: 'var(--text)' }}>Wallu</strong> {t('settings.about_desc1')}</p>
            <p>{t('settings.about_desc2')}</p>
            <p style={{ marginTop: 8 }}>{t('settings.version')} <strong style={{ color: 'var(--accent)' }}>0.1.0 MVP</strong></p>
            <p>{t('settings.made_with')}</p>
          </div>
        </div>

        <button className="btn-primary" style={{ justifyContent: 'center', padding: '12px 24px' }} onClick={handleSave}>
          {saved ? <><CheckCircle size={16} /> {t('settings.saved')}</> : t('settings.save_btn')}
        </button>
      </div>
    </div>
  );
}
