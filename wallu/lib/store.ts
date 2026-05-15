'use client';

import { Subscription, Transaction } from './types';
import { DEFAULT_SUBSCRIPTIONS, DEFAULT_TRANSACTIONS } from './data';

const SUBS_KEY = 'wallu_subscriptions';
const TXN_KEY = 'wallu_transactions';

export function getSubscriptions(): Subscription[] {
  if (typeof window === 'undefined') return DEFAULT_SUBSCRIPTIONS;
  try {
    const raw = localStorage.getItem(SUBS_KEY);
    return raw ? JSON.parse(raw) : DEFAULT_SUBSCRIPTIONS;
  } catch {
    return DEFAULT_SUBSCRIPTIONS;
  }
}

export function saveSubscriptions(subs: Subscription[]): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(SUBS_KEY, JSON.stringify(subs));
}

export function getTransactions(): Transaction[] {
  if (typeof window === 'undefined') return DEFAULT_TRANSACTIONS;
  try {
    const raw = localStorage.getItem(TXN_KEY);
    return raw ? JSON.parse(raw) : DEFAULT_TRANSACTIONS;
  } catch {
    return DEFAULT_TRANSACTIONS;
  }
}

export function saveTransactions(txns: Transaction[]): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TXN_KEY, JSON.stringify(txns));
}

export function monthlyAmount(sub: Subscription): number {
  if (!sub.active) return 0;
  switch (sub.billingCycle) {
    case 'weekly': return sub.amount * 4.33;
    case 'yearly': return sub.amount / 12;
    default: return sub.amount;
  }
}

export function daysUntil(dateStr: string): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(dateStr);
  target.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

export function formatCurrency(amount: number, currency = 'EUR'): string {
  return new Intl.NumberFormat('pt-PT', { style: 'currency', currency }).format(amount);
}
