// components/EmptyState.jsx - friendly placeholder for empty lists.
export default function EmptyState({ icon, title, message, action }) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-icon">{icon}</div>}
      <h3>{title}</h3>
      {message && <p>{message}</p>}
      {action}
    </div>
  )
}
