'use client';

import { useState, useEffect } from 'react';
import { Plus, Trash2, Target, TrendingUp, Calendar, CheckCircle } from 'lucide-react';
import { getGoals, saveGoals, SavingsGoal, DEFAULT_GOALS } from '@/lib/goals';

function randomId() { return Math.random().toString(36).slice(2, 9); }

const COLORS = ['#7C3AED', '#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#EC4899', '#06B6D4', '#F97316'];
const EMOJIS = ['🏖️', '🚗', '🏠', '💻', '💍', '✈️', '🛡️', '📱', '🎓', '💪', '🎯', '🌍'];

function ProgressRing({ pct, color, size = 72 }: { pct: number; color: string; size?: number }) {
  const r = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface2)" strokeWidth={8} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={8}
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
        style={{ transition: 'stroke-dasharray 0.6s ease' }} />
    </svg>
  );
}

export default function GoalsPage() {
  const [goals, setGoals] = useState<SavingsGoal[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [depositId, setDepositId] = useState<string | null>(null);
  const [depositAmt, setDepositAmt] = useState('');
  const [form, setForm] = useState({
    name: '', emoji: '🎯', target: '', current: '', currency: 'EUR', deadline: '', color: COLORS[0],
  });

  useEffect(() => { setGoals(getGoals()); }, []);

  const save = (g: SavingsGoal[]) => { setGoals(g); saveGoals(g); };

  const totalSaved = goals.reduce((s, g) => s + g.current, 0);
  const totalTarget = goals.reduce((s, g) => s + g.target, 0);
  const overallPct = totalTarget > 0 ? Math.min(100, (totalSaved / totalTarget) * 100) : 0;
  const completed = goals.filter(g => g.current >= g.target).length;

  const openAdd = () => {
    setForm({ name: '', emoji: '🎯', target: '', current: '0', currency: 'EUR', deadline: '', color: COLORS[0] });
    setEditId(null);
    setShowAdd(true);
  };

  const openEdit = (g: SavingsGoal) => {
    setForm({ name: g.name, emoji: g.emoji, target: String(g.target), current: String(g.current), currency: g.currency, deadline: g.deadline || '', color: g.color });
    setEditId(g.id);
    setShowAdd(true);
  };

  const submitForm = () => {
    if (!form.name || !form.target) return;
    if (editId) {
      save(goals.map(g => g.id === editId ? { ...g, name: form.name, emoji: form.emoji, target: Number(form.target), current: Number(form.current), currency: form.currency, deadline: form.deadline || undefined, color: form.color } : g));
    } else {
      save([...goals, { id: randomId(), name: form.name, emoji: form.emoji, target: Number(form.target), current: Number(form.current || 0), currency: form.currency, deadline: form.deadline || undefined, color: form.color }]);
    }
    setShowAdd(false);
  };

  const deleteGoal = (id: string) => {
    if (confirm('Apagar esta meta?')) save(goals.filter(g => g.id !== id));
  };

  const deposit = (id: string) => {
    const amt = parseFloat(depositAmt);
    if (!amt || isNaN(amt)) return;
    save(goals.map(g => g.id === id ? { ...g, current: Math.min(g.target, g.current + amt) } : g));
    setDepositId(null);
    setDepositAmt('');
  };

  const daysLeft = (deadline?: string) => {
    if (!deadline) return null;
    const diff = new Date(deadline).getTime() - Date.now();
    return Math.ceil(diff / 86400000);
  };

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28, gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.4px' }}>Metas de Poupança</h1>
          <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 4 }}>Acompanha os teus objetivos financeiros</p>
        </div>
        <button className="btn-primary" onClick={openAdd} style={{ gap: 6, whiteSpace: 'nowrap' }}>
          <Plus size={16} /> Nova meta
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 24 }} className="stats-grid">
        <div className="card" style={{ padding: '18px 20px' }}>
          <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Total poupado</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: '#10B981' }}>
            {totalSaved.toLocaleString('pt-PT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>de {totalTarget.toLocaleString('pt-PT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })}</div>
        </div>
        <div className="card" style={{ padding: '18px 20px' }}>
          <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Progresso global</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--accent)' }}>{overallPct.toFixed(1)}%</div>
          <div style={{ marginTop: 8, height: 4, background: 'var(--surface2)', borderRadius: 2 }}>
            <div style={{ height: '100%', width: `${overallPct}%`, background: 'var(--accent)', borderRadius: 2, transition: 'width 0.6s' }} />
          </div>
        </div>
        <div className="card" style={{ padding: '18px 20px' }}>
          <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Metas concluídas</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: '#F59E0B' }}>{completed} / {goals.length}</div>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
            {completed === goals.length && goals.length > 0 ? '🎉 Todas concluídas!' : `${goals.length - completed} em progresso`}
          </div>
        </div>
      </div>

      {/* Goals grid */}
      {goals.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <Target size={40} color="var(--muted)" style={{ margin: '0 auto 16px' }} />
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Sem metas ainda</div>
          <div style={{ color: 'var(--muted)', fontSize: 14, marginBottom: 20 }}>Cria a tua primeira meta de poupança</div>
          <button className="btn-primary" onClick={openAdd} style={{ margin: '0 auto' }}><Plus size={15} /> Nova meta</button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {goals.map(g => {
            const pct = Math.min(100, (g.current / g.target) * 100);
            const done = g.current >= g.target;
            const days = daysLeft(g.deadline);
            const remaining = g.target - g.current;

            return (
              <div key={g.id} className="card" style={{ padding: '20px 22px' }}>
                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                  {/* Ring */}
                  <div style={{ position: 'relative', flexShrink: 0 }}>
                    <ProgressRing pct={pct} color={done ? '#10B981' : g.color} size={80} />
                    <div style={{
                      position: 'absolute', inset: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexDirection: 'column',
                    }}>
                      {done
                        ? <CheckCircle size={22} color="#10B981" />
                        : <span style={{ fontSize: 22 }}>{g.emoji}</span>
                      }
                    </div>
                  </div>

                  {/* Info */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontWeight: 700, fontSize: 15 }}>{g.name}</span>
                      {done && <span style={{ fontSize: 10, background: '#10B98122', color: '#10B981', padding: '2px 8px', borderRadius: 20, fontWeight: 600 }}>CONCLUÍDA</span>}
                    </div>

                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 10 }}>
                      <span style={{ fontSize: 13, color: 'var(--muted)' }}>
                        <strong style={{ color: done ? '#10B981' : g.color, fontSize: 15 }}>
                          {g.current.toLocaleString('pt-PT', { style: 'currency', currency: g.currency })}
                        </strong>
                        {' '}/ {g.target.toLocaleString('pt-PT', { style: 'currency', currency: g.currency })}
                      </span>
                      <span style={{ fontSize: 13, color: 'var(--muted)' }}>
                        {pct.toFixed(0)}% completo
                      </span>
                    </div>

                    {/* Progress bar */}
                    <div style={{ height: 6, background: 'var(--surface2)', borderRadius: 3, marginBottom: 10 }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: done ? '#10B981' : g.color, borderRadius: 3, transition: 'width 0.6s' }} />
                    </div>

                    {/* Meta info */}
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                      {!done && (
                        <span style={{ fontSize: 12, color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                          <TrendingUp size={12} /> Faltam {remaining.toLocaleString('pt-PT', { style: 'currency', currency: g.currency })}
                        </span>
                      )}
                      {days !== null && (
                        <span style={{ fontSize: 12, color: days < 30 ? '#EF4444' : 'var(--muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                          <Calendar size={12} />
                          {days > 0 ? `${days} dias restantes` : days === 0 ? 'Hoje!' : 'Prazo ultrapassado'}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flexShrink: 0 }}>
                    {!done && (
                      <button className="btn-ghost" onClick={() => { setDepositId(g.id); setDepositAmt(''); }}
                        style={{ fontSize: 12, padding: '6px 12px', color: g.color, borderColor: g.color + '44' }}>
                        + Depositar
                      </button>
                    )}
                    <button className="btn-ghost" onClick={() => openEdit(g)} style={{ fontSize: 12, padding: '6px 12px' }}>
                      Editar
                    </button>
                    <button className="btn-ghost" onClick={() => deleteGoal(g.id)}
                      style={{ fontSize: 12, padding: '6px 12px', color: 'var(--red)', borderColor: '#EF444433' }}>
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

                {/* Deposit inline */}
                {depositId === g.id && (
                  <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)', display: 'flex', gap: 10, alignItems: 'center' }}>
                    <span style={{ fontSize: 13, color: 'var(--muted)' }}>Depositar:</span>
                    <input type="number" placeholder="0.00" value={depositAmt}
                      onChange={e => setDepositAmt(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') deposit(g.id); if (e.key === 'Escape') setDepositId(null); }}
                      style={{ maxWidth: 120, padding: '7px 12px', fontSize: 14 }}
                      autoFocus />
                    <button className="btn-primary" onClick={() => deposit(g.id)} style={{ fontSize: 13, padding: '8px 16px' }}>Confirmar</button>
                    <button className="btn-ghost" onClick={() => setDepositId(null)} style={{ fontSize: 13, padding: '8px 12px' }}>Cancelar</button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add/Edit modal */}
      {showAdd && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div className="card" style={{ width: '100%', maxWidth: 480, padding: 24 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20 }}>{editId ? 'Editar meta' : 'Nova meta de poupança'}</h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {/* Emoji picker */}
              <div>
                <label>Emoji</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
                  {EMOJIS.map(e => (
                    <button key={e} onClick={() => setForm(f => ({ ...f, emoji: e }))}
                      style={{ fontSize: 22, padding: 6, borderRadius: 8, border: form.emoji === e ? `2px solid var(--accent)` : '2px solid transparent', background: form.emoji === e ? 'rgba(124,58,237,0.15)' : 'var(--surface2)', cursor: 'pointer' }}>
                      {e}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label>Nome da meta</label>
                <input placeholder="ex: Férias no Algarve" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label>Objetivo (€)</label>
                  <input type="number" placeholder="2000" value={form.target} onChange={e => setForm(f => ({ ...f, target: e.target.value }))} />
                </div>
                <div>
                  <label>Poupado já (€)</label>
                  <input type="number" placeholder="0" value={form.current} onChange={e => setForm(f => ({ ...f, current: e.target.value }))} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label>Moeda</label>
                  <select value={form.currency} onChange={e => setForm(f => ({ ...f, currency: e.target.value }))}>
                    <option value="EUR">EUR €</option>
                    <option value="USD">USD $</option>
                    <option value="GBP">GBP £</option>
                  </select>
                </div>
                <div>
                  <label>Prazo (opcional)</label>
                  <input type="date" value={form.deadline} onChange={e => setForm(f => ({ ...f, deadline: e.target.value }))} />
                </div>
              </div>

              {/* Color picker */}
              <div>
                <label>Cor</label>
                <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                  {COLORS.map(c => (
                    <button key={c} onClick={() => setForm(f => ({ ...f, color: c }))}
                      style={{ width: 28, height: 28, borderRadius: '50%', background: c, border: form.color === c ? '3px solid white' : '3px solid transparent', cursor: 'pointer' }} />
                  ))}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
              <button className="btn-primary" onClick={submitForm} style={{ flex: 1, justifyContent: 'center' }}>
                {editId ? 'Guardar' : 'Criar meta'}
              </button>
              <button className="btn-ghost" onClick={() => setShowAdd(false)} style={{ flex: 1, justifyContent: 'center' }}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
