// components/WeeklyChart.jsx - pure-SVG bar chart showing appointments
// booked over the last 7 days (used on both dashboards).
import { DAY_SHORT } from '../utils/format.js'

export default function WeeklyChart({ data, title }) {
  // data: array of 7 { day: 'Monday', count: n } or an object map
  const arr = Array.isArray(data) ? data : Array.from({ length: 7 }, (_, i) => ({ day: DAY_SHORT[i], count: 0 }))
  const max = Math.max(...arr.map((d) => d.count), 1)
  const W = 560
  const H = 200
  const pad = 28
  const bw = (W - pad * 2) / arr.length
  const barMax = H - 45

  return (
    <div className="chart-card">
      {title && <h3 className="card-title">{title}</h3>}
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img" aria-label={title}>
        {[0, 1, 2, 3].map((i) => (
          <line
            key={i}
            x1={pad}
            x2={W - pad}
            y1={pad + (barMax / 4) * i}
            y2={pad + (barMax / 4) * i}
            className="chart-grid"
          />
        ))}
        {arr.map((d, i) => {
          const h = (d.count / max) * barMax
          const x = pad + i * bw + bw * 0.22
          const y = pad + (barMax - h)
          return (
            <g key={i}>
              <rect
                className="chart-bar"
                x={x}
                y={y}
                width={bw * 0.56}
                height={h}
                rx="4"
                data-count={d.count}
              >
                <title>{`${d.day}: ${d.count}`}</title>
              </rect>
              <text x={x + (bw * 0.28)} y={y - 6} className="chart-label" textAnchor="middle">
                {d.count > 0 ? d.count : ''}
              </text>
              <text x={pad + i * bw + bw / 2} y={H - 8} className="chart-axis" textAnchor="middle">
                {d.day}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
