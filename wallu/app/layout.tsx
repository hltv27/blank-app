import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';

export const metadata: Metadata = {
  title: 'Wallu — As tuas finanças, simples',
  description: 'Controla as tuas subscrições e finanças num só lugar.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt" style={{ height: '100%' }}>
      <body style={{ minHeight: '100%', display: 'flex' }}>
        <Sidebar />
        <main style={{ flex: 1, marginLeft: 240, minHeight: '100vh', padding: '32px 36px', overflowX: 'hidden' }}>
          {children}
        </main>
      </body>
    </html>
  );
}
