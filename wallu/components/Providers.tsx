'use client';

import { LangProvider } from '@/lib/i18n';
import Sidebar from '@/components/Sidebar';
import BottomNav from '@/components/BottomNav';

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <LangProvider>
      <Sidebar />
      <main className="main-content">{children}</main>
      <BottomNav />
    </LangProvider>
  );
}
