// components/DateStrip.jsx - horizontal strip of the next N days used to
// pick a date when booking an appointment.
import { nextDays, DAY_SHORT } from '../utils/format.js'

export default function DateStrip({ selected, onSelect, count = 14 }) {
  const days = nextDays(count)
  return (
    <div className="date-strip" role="listbox" aria-label="Pick a date">
      {days.map((d) => {
        const active = d.iso === selected
        const today = d.iso === nextDays(1)[0].iso
        return (
          <button
            key={d.iso}
            className={`date-chip ${active ? 'date-chip-active' : ''}`}
            onClick={() => onSelect(d.iso)}
            role="option"
            aria-selected={active}
          >
            <span className="date-chip-week">{today ? 'Today' : DAY_SHORT[d.weekday]}</span>
            <span className="date-chip-day">{d.day}</span>
            <span className="date-chip-month">{d.month}</span>
          </button>
        )
      })}
    </div>
  )
}
