import type { Metadata } from 'next';
import './globals.css';
import Providers from '@/components/Providers';

export const metadata: Metadata = {
  title: 'Wallu — Your finances, simplified',
  description: 'Track your subscriptions and finances in one place.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" style={{ background: '#0D0D1A' }}>
      <body style={{ background: '#0D0D1A', color: '#F0F0FF', margin: 0, width: '100%' }}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
