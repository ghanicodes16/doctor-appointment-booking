// pages/doctor/DoctorDashboard.jsx - the doctor's dashboard.
//
// Shows:
//   - A greeting and the doctor's profile.
//   - Statistic cards (total, booked, completed, cancelled).
//   - A date filter to view appointments for a specific day.
//   - A table with every appointment: patient name, patient id, phone,
//     date, time and status.
//   - Buttons to mark appointments as Completed or Cancelled.
import { useCallback, useEffect, useState } from 'react'

import { getDoctorAppointments, updateAppointmentStatus } from '../../api/client.js'
import Alert from '../../components/Alert.jsx'
import Spinner from '../../components/Spinner.jsx'
import StatusBadge from '../../components/StatusBadge.jsx'
import { useAuth } from '../../context/AuthContext.jsx'

export default function DoctorDashboard() {
  const { user } = useAuth()

  const [appointments, setAppointments] = useState([])
  const [filterDate, setFilterDate] = useState('')
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(null) // id of the appointment being updated
  const [message, setMessage] = useState(null)

  // Load the appointments whenever the date filter changes.
  const loadAppointments = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getDoctorAppointments(filterDate || undefined)
      setAppointments(data)
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setLoading(false)
    }
  }, [filterDate])

  useEffect(() => {
    loadAppointments()
  }, [loadAppointments])

  // Change the status of an appointment (Completed or Cancelled).
  const handleStatusChange = async (appointment, newStatus) => {
    setUpdating(appointment.id)
    try {
      await updateAppointmentStatus(appointment.id, newStatus)
      setMessage({ type: 'success', text: `Appointment marked as ${newStatus}.` })
      loadAppointments()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setUpdating(null)
    }
  }

  // Statistics computed from the loaded appointments.
  const stats = {
    total: appointments.length,
    booked: appointments.filter((a) => a.status === 'Booked').length,
    completed: appointments.filter((a) => a.status === 'Completed').length,
    cancelled: appointments.filter((a) => a.status === 'Cancelled').length,
  }

  return (
    <div className="page dashboard">
      {/* Greeting */}
      <div className="dashboard-header">
        <div>
          <h1 className="page-title">Welcome, Dr. {user?.name?.split(' ').pop()}</h1>
          <p className="muted">Here is an overview of your appointments.</p>
        </div>
      </div>

      {message && <Alert type={message.type} onClose={() => setMessage(null)}>{message.text}</Alert>}

      {/* Statistic cards */}
      <div className="stat-grid">
        <div className="card stat-card">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Total shown</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value stat-blue">{stats.booked}</div>
          <div className="stat-label">Booked</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value stat-green">{stats.completed}</div>
          <div className="stat-label">Completed</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value stat-red">{stats.cancelled}</div>
          <div className="stat-label">Cancelled</div>
        </div>
      </div>

      {/* Date filter */}
      <div className="card filter-bar">
        <label className="field filter-field">
          <span>Filter by date</span>
          <input
            type="date"
            value={filterDate}
            onChange={(e) => setFilterDate(e.target.value)}
          />
        </label>
        {filterDate && (
          <button className="btn btn-outline" onClick={() => setFilterDate('')}>
            Show all dates
          </button>
        )}
      </div>

      {/* Appointments table */}
      <div className="card">
        <h3>Appointments</h3>

        {loading ? (
          <Spinner />
        ) : appointments.length === 0 ? (
          <p className="muted">No appointments found{filterDate ? ` for ${filterDate}` : ''}.</p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Patient ID</th>
                  <th>Patient Name</th>
                  <th>Phone</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((appointment) => (
                  <tr key={appointment.id}>
                    <td>{appointment.patient?.id ?? '-'}</td>
                    <td>
                      <strong>{appointment.patient?.name ?? '-'}</strong>
                    </td>
                    <td>{appointment.patient?.phone ?? '-'}</td>
                    <td>{appointment.appointment_date}</td>
                    <td>{appointment.appointment_time}</td>
                    <td>
                      <StatusBadge status={appointment.status} />
                    </td>
                    <td>
                      {appointment.status === 'Booked' ? (
                        <div className="row-actions">
                          <button
                            className="btn btn-success btn-sm"
                            disabled={updating === appointment.id}
                            onClick={() => handleStatusChange(appointment, 'Completed')}
                          >
                            Complete
                          </button>
                          <button
                            className="btn btn-danger-outline btn-sm"
                            disabled={updating === appointment.id}
                            onClick={() => handleStatusChange(appointment, 'Cancelled')}
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <span className="muted">No action</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
