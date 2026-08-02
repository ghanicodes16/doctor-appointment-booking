// pages/patient/Appointments.jsx - manage my appointments: list with
// status, reschedule (new date + slots) and cancel.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getMyAppointments,
  getAvailableSlots,
  rescheduleAppointment,
  cancelAppointment,
} from '../../api/client.js'
import { useToast } from '../../context/ToastContext.jsx'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import StatusBadge from '../../components/StatusBadge.jsx'
import Modal from '../../components/Modal.jsx'
import DateStrip from '../../components/DateStrip.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import Skeleton from '../../components/Skeleton.jsx'
import { CalendarIcon, ClockIcon, LocationIcon, RupeeIcon } from '../../components/icons.jsx'
import { formatDate, formatDateLong, formatTime12h, formatCurrency } from '../../utils/format.js'

export default function Appointments() {
  const { showToast } = useToast()
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [cancelId, setCancelId] = useState(null)
  const [cancelOpen, setCancelOpen] = useState(false)
  const [resched, setResched] = useState(null) // the appointment being rescheduled
  const [selectedDate, setSelectedDate] = useState('')
  const [slots, setSlots] = useState([])
  const [slotsMsg, setSlotsMsg] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => {
    setLoading(true)
    getMyAppointments()
      .then(setAppointments)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  useEffect(() => {
    if (!resched || !selectedDate) {
      setSlots([])
      setSlotsMsg('')
      return
    }
    getAvailableSlots(resched.doctor_id, selectedDate)
      .then((res) => {
        setSlots(res.available_slots || [])
        setSlotsMsg(res.is_available === false ? res.message || '' : '')
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
  }, [selectedDate, resched])

  const filtered = appointments.filter((a) => (filter === 'all' ? true : a.status === filter))

  const openReschedule = (a) => {
    setResched(a)
    setSelectedDate('')
  }

  const doReschedule = (time) => {
    setBusy(true)
    rescheduleAppointment(resched.id, selectedDate, time)
      .then(() => {
        showToast({ type: 'success', message: 'Appointment rescheduled successfully.' })
        setResched(null)
        load()
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setBusy(false))
  }

  const doCancel = () => {
    setBusy(true)
    cancelAppointment(cancelId)
      .then(() => {
        showToast({ type: 'info', message: 'Appointment cancelled.' })
        setCancelOpen(false)
        load()
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setBusy(false))
  }

  return (
    <DashboardLayout title="My Appointments">
      <div className="tabs-row">
        {['all', 'Booked', 'Completed', 'Cancelled'].map((f) => (
          <button key={f} className={`tab ${filter === f ? 'tab-active' : ''}`} onClick={() => setFilter(f)}>
            {f === 'all' ? 'All' : f}
          </button>
        ))}
      </div>

      {loading ? (
        <Skeleton height="200px" />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<CalendarIcon size="lg" />}
          title="No appointments here"
          message="Book a doctor appointment to see it listed here."
          action={
            <Link to="/search" className="btn btn-primary btn-sm">
              Find a doctor
            </Link>
          }
        />
      ) : (
        <div className="appt-list">
          {filtered.map((a) => (
            <article key={a.id} className="card appt-card">
              <div className="avatar avatar-md" data-specialty={a.doctor?.specialization}>
                {a.doctor?.name?.slice(0, 1)}
              </div>
              <div className="appt-info">
                <h3>{a.doctor?.name}</h3>
                <p className="appt-spec">{a.doctor?.specialization}</p>
                <p className="appt-meta">
                  <span>
                    <CalendarIcon size="xs" /> {formatDateLong(a.appointment_date)}
                  </span>
                  <span>
                    <ClockIcon size="xs" /> {formatTime12h(a.appointment_time)}
                  </span>
                  {a.doctor?.city && (
                    <span>
                      <LocationIcon size="xs" /> {a.doctor.city}
                    </span>
                  )}
                </p>
              </div>
              <div className="appt-side">
                <div className="appt-fees">
                  <span className="visit-type">{a.visit_type || 'Visit'}</span>
                  <strong>
                    <RupeeIcon size="xs" /> {formatCurrency(a.consultation_fee)}
                  </strong>
                </div>
                <StatusBadge status={a.status} />
              </div>
              <div className="appt-actions">
                {a.status === 'Booked' && (
                  <>
                    <button className="btn btn-outline btn-sm" onClick={() => openReschedule(a)}>
                      Reschedule
                    </button>
                    <button
                      className="btn btn-danger-ghost btn-sm"
                      onClick={() => {
                        setCancelId(a.id)
                        setCancelOpen(true)
                      }}
                    >
                      Cancel
                    </button>
                  </>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Reschedule modal */}
      <Modal
        open={!!resched}
        title="Reschedule appointment"
        onClose={() => setResched(null)}
      >
        {resched && (
          <>
            <p className="card-sub">
              {resched.doctor?.name} · currently {formatDate(resched.appointment_date)} at{' '}
              {formatTime12h(resched.appointment_time)}
            </p>
            <DateStrip selected={selectedDate} onSelect={setSelectedDate} />
            <div className="slot-area">
              {!selectedDate ? (
                <p className="hint">Pick a new date above.</p>
              ) : slotsMsg ? (
                <p className="hint">{slotsMsg}</p>
              ) : slots.length === 0 ? (
                <p className="hint">No slots available on this date.</p>
              ) : (
                <div className="slot-grid">
                  {slots.map((s, i) => (
                    <button key={i} className="slot-chip" disabled={busy} onClick={() => doReschedule(s)}>
                      {formatTime12h(s)}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </Modal>

      {/* Cancel confirm */}
      <Modal
        open={cancelOpen}
        title="Cancel appointment?"
        onClose={() => setCancelOpen(false)}
        footer={
          <>
            <button className="btn btn-ghost" onClick={() => setCancelOpen(false)}>
              Keep it
            </button>
            <button className="btn btn-danger" onClick={doCancel} disabled={busy}>
              {busy ? 'Cancelling…' : 'Yes, cancel'}
            </button>
          </>
        }
      >
        <p>This appointment slot will be freed for other patients. This action cannot be undone.</p>
      </Modal>
    </DashboardLayout>
  )
}
