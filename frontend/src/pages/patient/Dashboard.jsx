// pages/patient/Dashboard.jsx - the patient dashboard: stats, upcoming
// appointments, favourite doctors and a weekly activity chart.
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPatientStats, getMyAppointments, getFavorites, getRecommendations } from '../../api/client.js'
import { useAuth } from '../../context/AuthContext.jsx'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import StatCard from '../../components/StatCard.jsx'
import WeeklyChart from '../../components/WeeklyChart.jsx'
import DoctorCard from '../../components/DoctorCard.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import Skeleton from '../../components/Skeleton.jsx'
import { CalendarIcon, HeartIcon, ClockIcon, CheckIcon, XIcon, ChartIcon, StethoscopeIcon, SparklesIcon } from '../../components/icons.jsx'
import { formatDate, formatTime12h, DAY_SHORT } from '../../utils/format.js'

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [upcoming, setUpcoming] = useState([])
  const [favorites, setFavorites] = useState([])
  const [recs, setRecs] = useState([])
  const [all, setAll] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getPatientStats(), getMyAppointments(true), getFavorites(), getRecommendations()])
      .then(([s, up, fav, r]) => {
        setStats(s)
        setUpcoming(up)
        setFavorites(fav)
        setRecs(r)
      })
      .catch(() => {})
    getMyAppointments()
      .then(setAll)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const weekly = useMemo(() => {
    const counts = [0, 0, 0, 0, 0, 0, 0]
    all.forEach((a) => {
      if (a.status === 'Cancelled') return
      const d = new Date(`${a.appointment_date}T00:00:00`)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const diff = Math.round((today - d) / 86400000)
      if (diff >= 0 && diff < 7) counts[6 - diff] += 1
    })
    return DAY_SHORT.map((day, i) => ({ day, count: counts[i] }))
  }, [all])

  return (
    <DashboardLayout title={`Salam, ${user?.name?.split(' ')[0]}`}>
      <div className="stats-grid">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} variant="card" height="96px" />)
        ) : (
          <>
           <StatCard icon={<CalendarIcon />} label="Total appointments" value={stats?.total ?? 0} tone="blue" />
           <StatCard icon={<ClockIcon />} label="Upcoming" value={stats?.upcoming ?? 0} tone="green" />
           <StatCard icon={<CheckIcon />} label="Completed" value={stats?.completed ?? 0} tone="purple" />
           <StatCard icon={<HeartIcon />} label="Favourites" value={stats?.favorite_count ?? 0} tone="rose" />
          </>
        )}
      </div>

      <div className="dash-grid-2">
        <section className="card">
          <div className="card-head">
            <h2 className="card-title">Upcoming appointments</h2>
            <Link to="/appointments" className="btn btn-ghost btn-sm">
              View all
            </Link>
          </div>
          {loading ? (
            <Skeleton height="120px" />
          ) : upcoming.length === 0 ? (
            <EmptyState
              icon={<CalendarIcon size="lg" />}
              title="No upcoming appointments"
              message="Find a doctor and book your first appointment."
              action={
                <Link to="/search" className="btn btn-primary btn-sm">
                  Find a doctor
                </Link>
              }
            />
          ) : (
            <ul className="appt-mini-list">
              {upcoming.slice(0, 4).map((a) => (
                <li key={a.id}>
                  <div className="avatar avatar-sm" data-specialty={a.doctor?.specialization}>
                    {a.doctor?.name?.slice(0, 1)}
                  </div>
                  <div className="appt-mini-info">
                    <strong>{a.doctor?.name}</strong>
                    <span>
                      {a.doctor?.specialization} · {formatDate(a.appointment_date)} at {formatTime12h(a.appointment_time)}
                    </span>
                  </div>
                  <span className="status-pill status-on">{a.status}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <WeeklyChart data={weekly} title="Your last 7 days" />
      </div>

      <section className="card">
        <div className="card-head">
          <h2 className="card-title">
            <HeartIcon size="sm" /> Favourite doctors
          </h2>
          <Link to="/favorites" className="btn btn-ghost btn-sm">
            View all
          </Link>
        </div>
        {loading ? (
          <Skeleton height="100px" />
        ) : favorites.length === 0 ? (
          <EmptyState icon={<HeartIcon size="lg" />} title="No favourites yet" message="Tap the heart on any doctor to save them here." />
        ) : (
          <div className="doctor-grid compact">
            {favorites.slice(0, 3).map((d) => (
              <DoctorCard key={d.id} doctor={d} />
            ))}
          </div>
        )}
      </section>

      <section className="card">
        <div className="card-head">
          <h2 className="card-title">
            <StethoscopeIcon size="sm" /> Recommended specialists
          </h2>
        </div>
        <div className="chip-row">
          {recs.map((s) => (
            <Link key={s.id} to={`/search?specialization=${encodeURIComponent(s.name)}`} className="chip">
              {s.name}
            </Link>
          ))}
        </div>
      </section>

      <section className="card ai-dash-card">
        <div className="ai-dash-card-icon">
          <SparklesIcon size="lg" />
        </div>
        <div className="ai-dash-card-body">
          <h2 className="card-title">ShifaBook AI Health Assistant</h2>
          <p>
            Upload a medical report, prescription or test result and get a simple, safe explanation plus a
            recommendation for the right specialist.
          </p>
        </div>
        <Link to="/ai-assistant" className="btn btn-primary">
          Analyze my report
        </Link>
      </section>
    </DashboardLayout>
  )
}
