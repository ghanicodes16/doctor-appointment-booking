// pages/doctor/Dashboard.jsx - doctor dashboard: today's appointments,
// revenue, weekly chart, booking toggle and profile completion.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDoctorStats, getMyDoctorProfile, setBookingEnabled } from '../../api/client.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useToast } from '../../context/ToastContext.jsx'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import StatCard from '../../components/StatCard.jsx'
import WeeklyChart from '../../components/WeeklyChart.jsx'
import Skeleton from '../../components/Skeleton.jsx'
import { CalendarIcon, ClockIcon, UsersIcon, RupeeIcon, BellIcon } from '../../components/icons.jsx'
import { formatCurrency } from '../../utils/format.js'

export default function Dashboard() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [stats, setStats] = useState(null)
  const [doctor, setDoctor] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getDoctorStats(), getMyDoctorProfile()])
      .then(([s, d]) => {
        setStats(s)
        setDoctor(d)
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setLoading(false))
  }, [])

  const toggleBooking = () => {
    if (!doctor) return
    setBookingEnabled(!doctor.booking_enabled)
      .then((d) => {
        setDoctor(d)
        showToast({
          type: 'success',
          message: d.booking_enabled ? 'Online booking is now open.' : 'Online booking is now off.',
        })
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
  }

  const weeklyData = stats?.weekly
    ? stats.weekly.labels.map((day, i) => ({ day, count: stats.weekly.counts[i] }))
    : []

  return (
    <DashboardLayout title={`Salam, Dr. ${user?.name?.split(' ').slice(-1)[0]}`}>
      <div className="stats-grid">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} variant="card" height="96px" />)
        ) : (
          <>
            <StatCard icon={<CalendarIcon />} label="Today's appointments" value={stats.today_count} tone="blue" />
            <StatCard icon={<ClockIcon />} label="Upcoming" value={stats.upcoming_count} tone="green" />
            <StatCard icon={<UsersIcon />} label="Total patients" value={stats.total_patients} tone="purple" />
            <StatCard icon={<RupeeIcon />} label="Revenue (all time)" value={formatCurrency(stats.total_revenue)} tone="rose" />
          </>
        )}
      </div>

      <div className="dash-grid-2">
        <WeeklyChart data={weeklyData} title="Appointments this week" />

        <section className="card">
          <h2 className="card-title">Quick actions</h2>
          <div className="quick-actions">
            <button className="btn btn-primary" onClick={toggleBooking} disabled={!doctor}>
              {doctor?.booking_enabled ? 'Pause online booking' : 'Resume online booking'}
            </button>
            <Link to="/doctor/schedule" className="btn btn-outline">
              Manage my schedule
            </Link>
            <Link to="/doctor/appointments" className="btn btn-outline">
              View all appointments
            </Link>
            <Link to="/doctor/profile" className="btn btn-ghost">
              Edit profile
            </Link>
          </div>

          <div className="completion">
            <div className="completion-head">
              <span>Profile completion</span>
              <strong>{loading ? '…' : `${stats.profile_completion}%`}</strong>
            </div>
            <div className="progress">
              <div className="progress-fill" style={{ width: loading ? '0%' : `${stats.profile_completion}%` }} />
            </div>
            {!loading && stats.profile_completion < 100 && (
              <p className="hint">
                Complete your profile to appear higher in search results.{' '}
                <Link to="/doctor/profile">Complete now</Link>
              </p>
            )}
          </div>
        </section>
      </div>

      <section className="card">
        <div className="card-head">
          <h2 className="card-title">
            <RupeeIcon size="sm" /> This month
          </h2>
        </div>
        {loading ? (
          <Skeleton height="80px" />
        ) : (
          <div className="mini-stats">
            <div>
              <span>Appointments this month</span>
              <strong>{stats.monthly_count}</strong>
            </div>
            <div>
              <span>Revenue this month</span>
              <strong>{formatCurrency(stats.monthly_revenue)}</strong>
            </div>
            <div>
              <span>Total patients treated</span>
              <strong>{doctor?.patients_treated ?? 0}</strong>
            </div>
          </div>
        )}
      </section>
    </DashboardLayout>
  )
}
