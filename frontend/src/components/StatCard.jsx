// components/StatCard.jsx - a dashboard metric card with icon + number.
export default function StatCard({ icon, label, value, tone = 'blue' }) {
  return (
    <div className={`stat-card stat-${tone}`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-body">
        <strong>{value ?? '—'}</strong>
        <span>{label}</span>
      </div>
    </div>
  )
}
