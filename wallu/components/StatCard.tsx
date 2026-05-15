interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  icon: string;
  accent?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export default function StatCard({ label, value, sub, icon, accent = '#7C3AED', trend }: StatCardProps) {
  const trendColor = trend === 'up' ? '#10B981' : trend === 'down' ? '#EF4444' : 'var(--muted)';

  return (
    <div className="card fade-in" style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {label}
          </span>
          <span style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.5px' }}>{value}</span>
        </div>
        <div style={{
          width: 42, height: 42,
          background: `${accent}22`,
          borderRadius: 12,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 20,
        }}>
          {icon}
        </div>
      </div>
      {sub && (
        <span style={{ fontSize: 12, color: trendColor }}>{sub}</span>
      )}
    </div>
  );
}
