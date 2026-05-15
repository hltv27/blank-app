'use client';

export interface SavingsGoal {
  id: string;
  name: string;
  emoji: string;
  target: number;
  current: number;
  currency: string;
  deadline?: string;
  color: string;
}

const KEY = 'wallu_goals';
const SEEDED = 'wallu_goals_seeded';

export const DEFAULT_GOALS: SavingsGoal[] = [
  { id: 'g1', name: 'Férias no Algarve', emoji: '🏖️', target: 2000, current: 650, currency: 'EUR', deadline: '2026-08-01', color: '#F59E0B' },
  { id: 'g2', name: 'Fundo de emergência', emoji: '🛡️', target: 5000, current: 1261, currency: 'EUR', color: '#10B981' },
  { id: 'g3', name: 'Novo portátil', emoji: '💻', target: 1500, current: 320, currency: 'EUR', deadline: '2026-12-01', color: '#7C3AED' },
];

export function getGoals(): SavingsGoal[] {
  if (typeof window === 'undefined') return DEFAULT_GOALS;
  if (!localStorage.getItem(SEEDED)) {
    localStorage.setItem(KEY, JSON.stringify(DEFAULT_GOALS));
    localStorage.setItem(SEEDED, '1');
  }
  try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch { return DEFAULT_GOALS; }
}

export function saveGoals(goals: SavingsGoal[]) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(KEY, JSON.stringify(goals));
}
