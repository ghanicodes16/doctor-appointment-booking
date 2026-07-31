// pages/patient/MyAppointments.jsx - the patient's appointment list.
//
// Shows all of the patient's appointments with tabs for All / Upcoming /
// Previous. Each appointment card includes the doctor's name, specialty,
// date, time and status. Booked appointments can be rescheduled or
// cancelled.
import { useCallback, useEffect, useState } from 'react'

import {
  cancelAppointment,
  getAvailableSlots,
  getMyAppointments,
  rescheduleAppointment,
} from '../../api/client.js'
import Alert from '../../components/Alert.jsx'
import Spinner from '../../components/Spinner.jsx'
import StatusBadge from '../../components/StatusBadge.jsx'

export default function MyAppointments() {
  const [appointments, setAppointments] = useState([])
  const [tab, setTab] = useState('all') // 'all' | 'upcoming' | 'previous'
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState(null)

  // The appointment currently being rescheduled (null = modal closed).
  const [rescheduleTarget, setRescheduleTarget] = useState(null)
  const [newDate, setNewDate] = useState('')
  const [newSlots, setNewSlots] = useState([])
  const [newSlot, setNewSlot] = useState('')
  const [loadingSlots, setLoadingSlots] = useState(false)

  // Load the appointments. This function is re-created only when `tab`
  // changes, and it is called again after every cancel/reschedule.
  const loadAppointments = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getMyAppointments(
        tab === 'upcoming' ? true : tab === 'previous' ? false : undefined
      )
      setAppointments(data)
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setLoading(false)
    }
  }, [tab])

  useEffect(() => {
    loadAppointments()
  }, [loadAppointments])

  // Cancel an appointment (backend changes its status to Cancelled).
  const handleCancel = async (id) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) return
    try {
      await cancelAppointment(id)
      setMessage({ type: 'success', text: 'Appointment cancelled.' })
      loadAppointments()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
  }

  // Open the reschedule modal for an appointment.
  const openReschedule = (appointment) => {
    setRescheduleTarget(appointment)
    setNewDate(appointment.appointment_date)
    setNewSlot('')
    setNewSlots([])
  }

  // When the date in the modal changes, fetch the free slots.
  useEffect(() => {
    if (!rescheduleTarget || !newDate) {
      setNewSlots([])
      setNewSlot('')
      return
    }
    setLoadingSlots(true)
    getAvailableSlots(rescheduleTarget.doctor_id, newDate)
      .then((data) => setNewSlots(data.available_slots))
      .catch((err) => setMessage({ type: 'error', text: err.message }))
      .finally(() => setLoadingSlots(false))
  }, [rescheduleTarget, newDate])

  // Save the new date/time.
  const handleRescheduleSave = async () => {
    try {
      await rescheduleAppointment(rescheduleTarget.id, newDate, newSlot)
      setMessage({ type: 'success', text: 'Appointment rescheduled successfully.' })
      setRescheduleTarget(null)
      loadAppointments()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
  }

  return (
    <div className="page">
      <h1 className="page-title">My Appointments</h1>

      {message && <Alert type={message.type} onClose={() => setMessage(null)}>{message.text}</Alert>}

      {/* Tab switcher */}
      <div className="tabs">
        {['all', 'upcoming', 'previous'].map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? 'tab-active' : ''}`}
            onClick={() => setTab(t)}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <Spinner />
      ) : appointments.length === 0 ? (
        <div className="card empty-state">
          <p>No appointments here yet.</p>
        </div>
      ) : (
        <div className="appointment-list">
          {appointments.map((appointment) => (
            <div className="card appointment-card" key={appointment.id}>
              <div className="appointment-avatar">
                {appointment.doctor?.name?.charAt(0) || 'D'}
              </div>
              <div className="appointment-info">
                <h4>
                  {appointment.doctor?.name || 'Doctor'} ({appointment.doctor?.specialty})
                </h4>
                <p className="muted">
                  {appointment.appointment_date} at {appointment.appointment_time}
                </p>
                <p className="muted">Booked on {new Date(appointment.created_at).toLocaleDateString()}</p>
              </div>
              <StatusBadge status={appointment.status} />
              <div className="appointment-actions">
                {appointment.status === 'Booked' && (
                  <>
                    <button className="btn btn-outline btn-sm" onClick={() => openReschedule(appointment)}>
                      Reschedule
                    </button>
                    <button className="btn btn-danger-outline btn-sm" onClick={() => handleCancel(appointment.id)}>
                      Cancel
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reschedule modal */}
      {rescheduleTarget && (
        <div className="modal-overlay" onClick={() => setRescheduleTarget(null)}>
          <div className="modal card" onClick={(e) => e.stopPropagation()}>
            <h3>Reschedule Appointment</h3>
            <p className="muted">
              {rescheduleTarget.doctor?.name} - current time{' '}
              {rescheduleTarget.appointment_date} at {rescheduleTarget.appointment_time}
            </p>

            <label className="field">
              <span>New date</span>
              <input
                type="date"
                value={newDate}
                min={new Date().toISOString().split('T')[0]}
                onChange={(e) => setNewDate(e.target.value)}
              />
            </label>

            {loadingSlots ? (
              <Spinner small />
            ) : (
              newSlots.length > 0 && (
                <>
                  <p className="muted">Available time slots:</p>
                  <div className="slot-grid">
                    {newSlots.map((slot) => (
                      <button
                        key={slot}
                        type="button"
                        className={`slot ${newSlot === slot ? 'slot-selected' : ''}`}
                        onClick={() => setNewSlot(slot)}
                      >
                        {slot}
                      </button>
                    ))}
                  </div>
                </>
              )
            )}

            <div className="modal-actions">
              <button className="btn btn-outline" onClick={() => setRescheduleTarget(null)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                disabled={!newSlot}
                onClick={handleRescheduleSave}
              >
                Save changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
