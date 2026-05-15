'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, CreditCard, BarChart2, Settings, Wallet, PieChart, Target } from 'lucide-react';

const links = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/subscriptions', label: 'Subscrições', icon: CreditCard },
  { href: '/finances', label: 'Finanças', icon: BarChart2 },
  { href: '/portfolio', label: 'Carteira', icon: PieChart },
  { href: '/goals', label: 'Metas', icon: Target },
  { href: '/settings', label: 'Definições', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="desktop-sidebar" style={{
      width: 240,
      minHeight: '100vh',
      background: 'var(--surface)',
      borderRight: '1px solid var(--border)',
      position: 'fixed',
      left: 0, top: 0, bottom: 0,
      flexDirection: 'column',
      padding: '24px 16px',
      gap: 4,
      zIndex: 100,
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 8px 28px' }}>
        <div style={{
          width: 36, height: 36,
          background: 'linear-gradient(135deg, #7C3AED, #9B59F5)',
          borderRadius: 10,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 18,
        }}>
          <Wallet size={18} color="white" />
        </div>
        <span style={{ fontWeight: 700, fontSize: 18, letterSpacing: '-0.3px' }}>Wallu</span>
      </div>

      {/* Nav links */}
      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {links.map(({ href, label, icon: Icon }) => {
          const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link key={href} href={href} style={{ textDecoration: 'none' }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 12px',
                borderRadius: 10,
                background: active ? 'rgba(124,58,237,0.15)' : 'transparent',
                color: active ? '#9B59F5' : 'var(--muted)',
                fontWeight: active ? 600 : 400,
                fontSize: 14,
                transition: 'all 0.15s',
                cursor: 'pointer',
              }}
                onMouseEnter={e => { if (!active) (e.currentTarget as HTMLDivElement).style.background = 'var(--surface2)'; }}
                onMouseLeave={e => { if (!active) (e.currentTarget as HTMLDivElement).style.background = 'transparent'; }}
              >
                <Icon size={17} />
                {label}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{ padding: '16px 8px 0', borderTop: '1px solid var(--border)' }}>
        <p style={{ fontSize: 11, color: 'var(--muted)', lineHeight: 1.6 }}>
          Wallu v0.1 — MVP<br />
          <span style={{ opacity: 0.6 }}>Feito com ❤️ em Portugal</span>
        </p>
      </div>
    </aside>
  );
}
