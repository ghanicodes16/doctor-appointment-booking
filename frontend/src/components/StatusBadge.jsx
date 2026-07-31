// components/StatusBadge.jsx - a coloured label for appointment status.
// Booked = blue, Completed = green, Cancelled = red/gray.
export default function StatusBadge({ status }) {
  const colorMap = {
    Booked: 'blue',
    Completed: 'green',
    Cancelled: 'red',
  }
  const cls = colorMap[status] || 'gray'
  return <span className={`badge badge-${cls}`}>{status}</span>
}
