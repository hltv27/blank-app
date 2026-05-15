'use client';

import { useState } from 'react';
import { CheckCircle } from 'lucide-react';

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.4px' }}>Definições</h1>
        <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 4 }}>Personaliza a tua experiência Wallu</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Profile section */}
        <div className="card" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>👤 Perfil</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label>Nome</label>
              <input placeholder="O teu nome" defaultValue="Utilizador Wallu" />
            </div>
            <div>
              <label>Email</label>
              <input type="email" placeholder="email@exemplo.pt" />
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div className="card" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>⚙️ Preferências</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label>Moeda</label>
              <select defaultValue="EUR">
                <option value="EUR">EUR — Euro €</option>
                <option value="USD">USD — Dólar $</option>
                <option value="GBP">GBP — Libra £</option>
                <option value="BRL">BRL — Real R$</option>
              </select>
            </div>
            <div>
              <label>Dia de início do mês</label>
              <select defaultValue="1">
                {Array.from({ length: 28 }, (_, i) => i + 1).map(d => (
                  <option key={d} value={d}>Dia {d}</option>
                ))}
              </select>
            </div>
            <div>
              <label>Lembrete de renovação (dias antes)</label>
              <select defaultValue="3">
                <option value="1">1 dia antes</option>
                <option value="3">3 dias antes</option>
                <option value="7">7 dias antes</option>
                <option value="14">14 dias antes</option>
              </select>
            </div>
          </div>
        </div>

        {/* Data */}
        <div className="card" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>💾 Dados</h2>
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
              📤 Exportar dados (JSON)
            </button>
            <button className="btn-ghost" style={{ textAlign: 'left', justifyContent: 'flex-start', color: 'var(--red)', borderColor: '#EF444433' }}
              onClick={() => {
                if (confirm('Apagar todos os dados? Esta ação não pode ser revertida.')) {
                  localStorage.removeItem('wallu_subscriptions');
                  localStorage.removeItem('wallu_transactions');
                  window.location.reload();
                }
              }}>
              🗑️ Apagar todos os dados
            </button>
          </div>
        </div>

        {/* About */}
        <div className="card" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>ℹ️ Sobre o Wallu</h2>
          <div style={{ fontSize: 13, color: 'var(--muted)', lineHeight: 1.8 }}>
            <p><strong style={{ color: 'var(--text)' }}>Wallu</strong> é uma app de gestão financeira pessoal.</p>
            <p>Controla as tuas subscrições e finanças de forma simples e visual.</p>
            <p style={{ marginTop: 8 }}>Versão: <strong style={{ color: 'var(--accent)' }}>0.1.0 MVP</strong></p>
            <p>Feito com ❤️ em Portugal</p>
          </div>
        </div>

        <button className="btn-primary" style={{ justifyContent: 'center', padding: '12px 24px' }} onClick={handleSave}>
          {saved ? <><CheckCircle size={16} /> Guardado!</> : 'Guardar alterações'}
        </button>
      </div>
    </div>
  );
}
