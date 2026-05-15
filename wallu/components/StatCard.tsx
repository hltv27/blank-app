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
    <div className="card stat-card fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 0, flex: 1 }}>
          <span className="stat-label">{label}</span>
          <span className="stat-value">{value}</span>
        </div>
        <div className="stat-icon" style={{ background: `${accent}22`, flexShrink: 0 }}>
          {icon}
        </div>
      </div>
      {sub && (
        <span style={{ fontSize: 12, color: trendColor, marginTop: 8, display: 'block' }}>{sub}</span>
      )}
    </div>
  );
}
