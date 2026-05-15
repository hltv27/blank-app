'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, CreditCard, Settings, PieChart, Target } from 'lucide-react';
import { useT } from '@/lib/i18n';

export default function BottomNav() {
  const pathname = usePathname();
  const t = useT();

  const links = [
    { href: '/',              label: t('nav.home'),          icon: LayoutDashboard },
    { href: '/subscriptions', label: t('nav.subscriptions').slice(0, 6), icon: CreditCard },
    { href: '/portfolio',     label: t('nav.portfolio'),     icon: PieChart },
    { href: '/goals',         label: t('nav.goals'),         icon: Target },
    { href: '/settings',      label: t('nav.settings').slice(0, 6), icon: Settings },
  ];

  return (
    <nav className="bottom-nav">
      {links.map(({ href, label, icon: Icon }) => {
        const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
        return (
          <Link key={href} href={href} style={{ textDecoration: 'none', flex: 1 }}>
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              gap: 4, padding: '8px 0',
              color: active ? '#9B59F5' : '#6B6B8A', transition: 'color 0.15s',
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
