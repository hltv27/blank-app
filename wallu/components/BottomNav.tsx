'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, CreditCard, BarChart2, Settings, PieChart, Target } from 'lucide-react';

const links = [
  { href: '/', label: 'Início', icon: LayoutDashboard },
  { href: '/subscriptions', label: 'Subscr.', icon: CreditCard },
  { href: '/portfolio', label: 'Carteira', icon: PieChart },
  { href: '/goals', label: 'Metas', icon: Target },
  { href: '/settings', label: 'Defin.', icon: Settings },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="bottom-nav">
      {links.map(({ href, label, icon: Icon }) => {
        const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
        return (
          <Link key={href} href={href} style={{ textDecoration: 'none', flex: 1 }}>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 4,
              padding: '8px 0',
              color: active ? '#9B59F5' : '#6B6B8A',
              transition: 'color 0.15s',
            }}>
              <Icon size={22} />
              <span style={{ fontSize: 10, fontWeight: active ? 600 : 400 }}>{label}</span>
            </div>
          </Link>
        );
      })}
    </nav>
  );
}
