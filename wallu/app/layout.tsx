import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';
import BottomNav from '@/components/BottomNav';

export const metadata: Metadata = {
  title: 'Wallu — As tuas finanças, simples',
  description: 'Controla as tuas subscrições e finanças num só lugar.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt" style={{ height: '100%', background: '#0D0D1A' }}>
      <body style={{ minHeight: '100%', display: 'flex', background: '#0D0D1A', color: '#F0F0FF', margin: 0 }}>
        <Sidebar />
        <main className="main-content">
          {children}
        </main>
        <BottomNav />
      </body>
    </html>
  );
}
