export type BillingCycle = 'monthly' | 'yearly' | 'weekly';

export type Category =
  | 'streaming'
  | 'music'
  | 'software'
  | 'gaming'
  | 'cloud'
  | 'news'
  | 'fitness'
  | 'food'
  | 'finance'
  | 'other';

export interface Subscription {
  id: string;
  name: string;
  amount: number;
  currency: string;
  billingCycle: BillingCycle;
  nextBillingDate: string;
  category: Category;
  color: string;
  emoji: string;
  active: boolean;
  notes?: string;
}

export interface Transaction {
  id: string;
  description: string;
  amount: number;
  type: 'income' | 'expense';
  category: string;
  date: string;
  emoji: string;
}

export interface FinancialSummary {
  totalIncome: number;
  totalExpenses: number;
  subscriptionsCost: number;
  balance: number;
}
