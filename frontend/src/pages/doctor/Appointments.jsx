// pages/doctor/Appointments.jsx - doctor's appointment queue with date
// filter and status actions (Complete / Cancel).
import { useEffect, useState } from 'react'
import { getDoctorAppointments, updateAppointmentStatus } from '../../api/client.js'
import { useToast } from '../../context/ToastContext.jsx'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import StatusBadge from '../../components/StatusBadge.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import Skeleton from '../../components/Skeleton.jsx'
import { CalendarIcon, CheckIcon, XIcon, PhoneIcon } from '../../components/icons.jsx'
import { formatDate, formatTime12h } from '../../utils/format.js'

export default function Appointments() {
  const { showToast } = useToast()
  const [appointments, setAppointments] = useState([])
  const [dateFilter, setDateFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)

  const load = (date) => {
    setLoading(true)
    getDoctorAppointments(date || undefined)
      .then(setAppointments)
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setLoading(false))
  }

  useEffect(() => load(dateFilter), [dateFilter])

  const setStatus = (appt, status) => {
    setBusyId(appt.id)
    updateAppointmentStatus(appt.id, status)
      .then(() => {
        showToast({ type: 'success', message: `Appointment marked ${status}.` })
        load(dateFilter)
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setBusyId(null))
  }

  const today = new Date().toISOString().split('T')[0]

  return (
    <DashboardLayout title="Appointments">
      <div className="card">
        <div className="card-head">
          <div className="field field-inline">
            <label htmlFor="dateFilter" className="filter-label">
              Filter by date
            </label>
            <input id="dateFilter" type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} />
            {dateFilter && (
              <button className="btn btn-ghost btn-sm" onClick={() => setDateFilter('')}>
                Clear
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <Skeleton height="200px" />
        ) : appointments.length === 0 ? (
          <EmptyState
            icon={<CalendarIcon size="lg" />}
            title="No appointments"
            message={dateFilter ? `No appointments on ${formatDate(dateFilter)}.` : 'You have no appointments yet.'}
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Date & time</th>
                  <th>Phone</th>
                  <th>Visit</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <div className="cell-user">
                        <div className="avatar avatar-sm" data-specialty="patient">
                          {a.patient?.name?.slice(0, 1)}
                        </div>
                        <div>
                          <strong>{a.patient?.name}</strong>
                        </div>
                      </div>
                    </td>
                    <td>
                      {formatDate(a.appointment_date)} · {formatTime12h(a.appointment_time)}
                      {a.appointment_date === today && <span className="chip chip-small chip-today">Today</span>}
                    </td>
                    <td>
                      <span className="cell-phone">
                        <PhoneIcon size="xs" /> {a.patient?.phone}
                      </span>
                    </td>
                    <td>
                      <span className="visit-type">{a.visit_type || 'Visit'}</span>
                    </td>
                    <td>
                      <StatusBadge status={a.status} />
                    </td>
                    <td>
                      {a.status === 'Booked' ? (
                        <div className="row-actions">
                          <button
                            className="btn btn-outline btn-sm"
                            disabled={busyId === a.id}
                            onClick={() => setStatus(a, 'Completed')}
                          >
                            <CheckIcon size="xs" /> Complete
                          </button>
                          <button
                            className="btn btn-danger-ghost btn-sm"
                            disabled={busyId === a.id}
                            onClick={() => setStatus(a, 'Cancelled')}
                          >
                            <XIcon size="xs" /> Cancel
                          </button>
                        </div>
                      ) : (
                        <span className="hint">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
