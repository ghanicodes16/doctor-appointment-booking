// components/DashboardLayout.jsx - sidebar + topbar shell for the
// patient and doctor dashboards.
import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { useTheme } from '../context/ThemeContext.jsx'
import { getMyNotifications, getDoctorNotifications } from '../api/client.js'
import {
  StethoscopeIcon,
  BellIcon,
  SunIcon,
  MoonIcon,
  LogoutIcon,
  MenuIcon,
  CalendarIcon,
  HeartIcon,
  ChartIcon,
  UsersIcon,
  ClockIcon,
  BriefcaseIcon,
} from './icons.jsx'

const patientNav = [
  { to: '/dashboard', label: 'Dashboard', icon: <ChartIcon size="sm" />, end: true },
  { to: '/appointments', label: 'My Appointments', icon: <CalendarIcon size="sm" /> },
  { to: '/favorites', label: 'Favorite Doctors', icon: <HeartIcon size="sm" /> },
  { to: '/search', label: 'Find Doctors', icon: <UsersIcon size="sm" /> },
]

const doctorNav = [
  { to: '/doctor/dashboard', label: 'Dashboard', icon: <ChartIcon size="sm" />, end: true },
  { to: '/doctor/appointments', label: 'Appointments', icon: <CalendarIcon size="sm" /> },
  { to: '/doctor/schedule', label: 'My Schedule', icon: <ClockIcon size="sm" /> },
  { to: '/doctor/profile', label: 'Profile', icon: <BriefcaseIcon size="sm" /> },
]

export default function DashboardLayout({ children, title }) {
  const { user, role, logout } = useAuth()
  const { dark, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const [notifications, setNotifications] = useState([])

  const nav = role === 'doctor' ? doctorNav : patientNav

  useEffect(() => {
    const fetcher = role === 'doctor' ? getDoctorNotifications : getMyNotifications
    fetcher()
      .then(setNotifications)
      .catch(() => {})
  }, [role])

  const unread = notifications.filter((n) => !n.is_read).length

  const logoutBtn = (
    <button
      className="btn btn-ghost btn-sm w-full"
      onClick={() => {
        logout()
        navigate(role === 'doctor' ? '/doctor/login' : '/login')
      }}
    >
      <LogoutIcon size="sm" /> Logout
    </button>
  )

  return (
    <div className="dash-layout">
      <aside className={`dash-sidebar ${open ? 'open' : ''}`}>
        <div className="dash-brand">
          <span className="brand-logo">
            <StethoscopeIcon />
          </span>
          <strong>ShifaBook</strong>
        </div>

        <div className="dash-role">
          <div className="avatar avatar-md" data-specialty={role}>
            {user?.name?.slice(0, 1).toUpperCase()}
          </div>
          <div>
            <strong>{user?.name}</strong>
            <small>{role === 'doctor' ? 'Doctor' : 'Patient'}</small>
          </div>
        </div>

        <nav className="dash-nav">
          {nav.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} onClick={() => setOpen(false)}>
              {item.icon} {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="dash-sidebar-bottom">{logoutBtn}</div>
      </aside>

      {open && <div className="dash-backdrop" onClick={() => setOpen(false)} />}

      <div className="dash-main">
        <div className="dash-topbar">
          <button className="icon-btn dash-burger" onClick={() => setOpen(true)} aria-label="Menu">
            <MenuIcon />
          </button>
          <h1 className="dash-title">{title}</h1>
          <div className="dash-actions">
            <button className="icon-btn" onClick={toggleTheme} aria-label="Toggle theme">
              {dark ? <SunIcon /> : <MoonIcon />}
            </button>
            <div className="dash-notif">
              <button className="icon-btn" onClick={() => setNotifOpen((o) => !o)} aria-label="Notifications">
                <BellIcon />
                {unread > 0 && <span className="notif-dot">{unread}</span>}
              </button>
              {notifOpen && (
                <div className="notif-panel">
                  <div className="notif-head">
                    <h4>Notifications</h4>
                  </div>
                  <div className="notif-list">
                    {notifications.length === 0 ? (
                      <p className="notif-empty">No notifications yet</p>
                    ) : (
                      notifications.slice(0, 8).map((n, i) => (
                        <div key={i} className={`notif-item ${n.is_read ? '' : 'notif-unread'}`}>
                          <div className="notif-text">
                            <strong>{n.title}</strong>
                            <p>{n.message}</p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        <main className="dash-content">{children}</main>
      </div>
    </div>
  )
}
