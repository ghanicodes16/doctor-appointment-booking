// pages/doctor/Schedule.jsx - manage weekly working hours, unavailable
// dates and blocked slots.
import { useEffect, useState } from 'react'
import {
  getMySchedule,
  saveSchedule,
  getUnavailableDates,
  addUnavailableDate,
  deleteUnavailableDate,
  getBlockedSlots,
  addBlockedSlot,
  deleteBlockedSlot,
} from '../../api/client.js'
import { useToast } from '../../context/ToastContext.jsx'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import Skeleton from '../../components/Skeleton.jsx'
import { ClockIcon, XIcon, CalendarIcon } from '../../components/icons.jsx'
import { DAY_NAMES, formatDate, formatTime12h } from '../../utils/format.js'

const DURATIONS = [15, 20, 30, 60]

const emptyDay = (i) => ({
  day_of_week: i,
  is_available: false,
  start_time: '09:00',
  end_time: '17:00',
  duration_minutes: 30,
})

export default function Schedule() {
  const { showToast } = useToast()
  const [schedule, setSchedule] = useState(Array.from({ length: 7 }, (_, i) => emptyDay(i)))
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [unavailable, setUnavailable] = useState([])
  const [unavailDate, setUnavailDate] = useState('')
  const [unavailReason, setUnavailReason] = useState('')

  const [blocked, setBlocked] = useState([])
  const [blockDate, setBlockDate] = useState('')
  const [blockTime, setBlockTime] = useState('')

  useEffect(() => {
    Promise.all([getMySchedule(), getUnavailableDates(), getBlockedSlots()])
      .then(([sched, unav, blk]) => {
        if (sched && sched.length) {
          setSchedule(
            Array.from({ length: 7 }, (_, i) => {
              const found = sched.find((s) => s.day_of_week === i)
              return found
                ? { day_of_week: i, is_available: found.is_available, start_time: found.start_time, end_time: found.end_time, duration_minutes: found.duration_minutes }
                : emptyDay(i)
            })
          )
        }
        setUnavailable(unav || [])
        setBlocked(blk || [])
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setLoading(false))
  }, [])

  const updateDay = (i, patch) => setSchedule((prev) => prev.map((d) => (d.day_of_week === i ? { ...d, ...patch } : d)))

  const toggleDay = (i) => updateDay(i, { is_available: !schedule[i].is_available })

  const save = () => {
    const days = schedule.filter((d) => d.is_available)
    setSaving(true)
    saveSchedule(days)
      .then(() => showToast({ type: 'success', message: 'Schedule saved.' }))
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setSaving(false))
  }

  const submitUnavailable = (e) => {
    e.preventDefault()
    if (!unavailDate) return
    addUnavailableDate(unavailDate, unavailReason || undefined)
      .then((row) => {
        setUnavailable((prev) => [row, ...prev])
        setUnavailDate('')
        setUnavailReason('')
        showToast({ type: 'success', message: 'Date marked unavailable.' })
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
  }

  const removeUnavailable = (id) => {
    deleteUnavailableDate(id)
      .then(() => {
        setUnavailable((prev) => prev.filter((u) => u.id !== id))
        showToast({ type: 'info', message: 'Unavailable date removed.' })
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
  }

  const submitBlocked = (e) => {
    e.preventDefault()
    if (!blockDate || !blockTime) return
    addBlockedSlot(blockDate, blockTime)
      .then((row) => {
        setBlocked((prev) => [...prev, row])
        setBlockDate('')
        setBlockTime('')
        showToast({ type: 'success', message: 'Slot blocked.' })
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
  }

  const removeBlocked = (id) => {
    deleteBlockedSlot(id)
      .then(() => {
        setBlocked((prev) => prev.filter((b) => b.id !== id))
        showToast({ type: 'info', message: 'Slot unblocked.' })
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
  }

  const nextDays = (n) => {
    const out = []
    for (let i = 0; i < n; i++) {
      const d = new Date()
      d.setDate(d.getDate() + i)
      out.push(d.toISOString().split('T')[0])
    }
    return out
  }
  const minDate = nextDays(1)[0]

  return (
    <DashboardLayout title="My Schedule">
      {loading ? (
        <Skeleton height="400px" />
      ) : (
        <>
          <section className="card">
            <div className="card-head">
              <h2 className="card-title">
                <ClockIcon size="sm" /> Weekly working hours
              </h2>
              <button className="btn btn-primary" onClick={save} disabled={saving}>
                {saving ? 'Saving…' : 'Save schedule'}
              </button>
            </div>
            <p className="card-sub">Toggle the days you work and set clinic hours per day.</p>

            <div className="schedule-editor">
              {schedule.map((d, i) => (
                <div key={i} className={`schedule-day ${d.is_available ? '' : 'day-off'}`}>
                  <div className="schedule-day-head">
                    <label className="switch">
                      <input type="checkbox" checked={d.is_available} onChange={() => toggleDay(i)} />
                      <span className="switch-slider" />
                    </label>
                    <strong>{DAY_NAMES[i]}</strong>
                  </div>
                  <div className="schedule-day-times">
                    <div className="field">
                      <label>Start</label>
                      <input
                        type="time"
                        value={d.start_time}
                        disabled={!d.is_available}
                        onChange={(e) => updateDay(i, { start_time: e.target.value })}
                      />
                    </div>
                    <div className="field">
                      <label>End</label>
                      <input
                        type="time"
                        value={d.end_time}
                        disabled={!d.is_available}
                        onChange={(e) => updateDay(i, { end_time: e.target.value })}
                      />
                    </div>
                    <div className="field">
                      <label>Duration</label>
                      <select
                        value={d.duration_minutes}
                        disabled={!d.is_available}
                        onChange={(e) => updateDay(i, { duration_minutes: Number(e.target.value) })}
                      >
                        {DURATIONS.map((dur) => (
                          <option key={dur} value={dur}>
                            {dur} min
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <div className="dash-grid-2">
            <section className="card">
              <h2 className="card-title">
                <CalendarIcon size="sm" /> Unavailable dates
              </h2>
              <p className="card-sub">Vacations, conferences or leave — patients won't see these dates.</p>
              <form className="inline-form" onSubmit={submitUnavailable}>
                <input type="date" min={minDate} value={unavailDate} onChange={(e) => setUnavailDate(e.target.value)} required />
                <input type="text" value={unavailReason} onChange={(e) => setUnavailReason(e.target.value)} placeholder="Reason (optional)" />
                <button className="btn btn-primary btn-sm" type="submit">
                  Add
                </button>
              </form>
              {unavailable.length === 0 ? (
                <p className="hint">No unavailable dates.</p>
              ) : (
                <ul className="chip-list">
                  {unavailable.map((u) => (
                    <li key={u.id}>
                      <span>
                        <strong>{formatDate(u.date)}</strong>
                        {u.reason && <small>{u.reason}</small>}
                      </span>
                      <button className="icon-btn" onClick={() => removeUnavailable(u.id)} aria-label="Remove">
                        <XIcon size="sm" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card">
              <h2 className="card-title">
                <ClockIcon size="sm" /> Blocked time slots
              </h2>
              <p className="card-sub">Block a specific slot on a specific day (e.g. a personal errand).</p>
              <form className="inline-form" onSubmit={submitBlocked}>
                <input type="date" min={minDate} value={blockDate} onChange={(e) => setBlockDate(e.target.value)} required />
                <input type="time" value={blockTime} onChange={(e) => setBlockTime(e.target.value)} required />
                <button className="btn btn-primary btn-sm" type="submit">
                  Block
                </button>
              </form>
              {blocked.length === 0 ? (
                <p className="hint">No blocked slots.</p>
              ) : (
                <ul className="chip-list">
                  {blocked.map((b) => (
                    <li key={b.id}>
                      <span>
                        <strong>{formatDate(b.date)}</strong>
                        <small>{formatTime12h(b.start_time)}</small>
                      </span>
                      <button className="icon-btn" onClick={() => removeBlocked(b.id)} aria-label="Unblock">
                        <XIcon size="sm" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </DashboardLayout>
  )
}
