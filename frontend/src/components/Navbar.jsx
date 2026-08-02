// components/Navbar.jsx - public navigation bar with search, theme toggle
// and a notifications bell for logged-in users.
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { useTheme } from '../context/ThemeContext.jsx'
import { getMyNotifications, getDoctorNotifications, markNotificationRead, markDoctorNotificationRead } from '../api/client.js'
import {
  SearchIcon,
  BellIcon,
  SunIcon,
  MoonIcon,
  MenuIcon,
  XIcon,
  StethoscopeIcon,
  LogoutIcon,
  UserIcon,
} from './icons.jsx'
import { formatTime12h, formatDate } from '../utils/format.js'

export default function Navbar() {
  const { user, role, isLoggedIn, logout } = useAuth()
  const { dark, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const [notifications, setNotifications] = useState([])
  const notifRef = useRef(null)

  const home = role === 'doctor' && isLoggedIn ? '/doctor/dashboard' : '/'
  const dashboardLink = role === 'doctor' ? '/doctor/dashboard' : '/dashboard'

  const submitSearch = (e) => {
    e.preventDefault()
    navigate(query.trim() ? `/search?q=${encodeURIComponent(query.trim())}` : '/search')
    setQuery('')
    setMobileOpen(false)
  }

  const loadNotifications = () => {
    if (!isLoggedIn) return
    const fetcher = role === 'doctor' ? getDoctorNotifications : getMyNotifications
    fetcher()
      .then(setNotifications)
      .catch(() => {})
  }

  useEffect(() => {
    if (notifOpen) loadNotifications()
  }, [notifOpen, isLoggedIn, role])

  useEffect(() => {
    const onClick = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) setNotifOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  const markRead = (n) => {
    const fn = role === 'doctor' ? markDoctorNotificationRead : markNotificationRead
    fn(n.id).then(() => {
      setNotifications((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)))
    })
  }

  const unread = notifications.filter((n) => !n.is_read).length

  const notifItem = (n, i) => (
    <button key={i} className={`notif-item ${n.is_read ? '' : 'notif-unread'}`} onClick={() => markRead(n)}>
      <div className="notif-text">
        <strong>{n.title}</strong>
        <p>{n.message}</p>
      </div>
      <span className="notif-time">{formatDate(n.created_at.split('T')[0])}</span>
    </button>
  )

  const userArea = isLoggedIn ? (
    <>
      <div className="nav-notif" ref={notifRef}>
        <button className="icon-btn" onClick={() => setNotifOpen((o) => !o)} aria-label="Notifications">
          <BellIcon />
          {unread > 0 && <span className="notif-dot">{unread}</span>}
        </button>
        {notifOpen && (
          <div className="notif-panel">
            <div className="notif-head">
              <h4>Notifications</h4>
              <Link to={role === 'doctor' ? '/doctor/dashboard' : '/dashboard'} onClick={() => setNotifOpen(false)}>
                View all
              </Link>
            </div>
            <div className="notif-list">
              {notifications.length === 0 ? (
                <p className="notif-empty">No notifications yet</p>
              ) : (
                notifications.slice(0, 8).map((n, i) => notifItem(n, i))
              )}
            </div>
          </div>
        )}
      </div>
      <div className="nav-user">
        <div className="avatar avatar-sm" data-specialty={role}>
          {user.name?.slice(0, 1).toUpperCase()}
        </div>
        <Link to={dashboardLink} className="nav-user-name">
          {user.name?.split(' ')[0]}
        </Link>
        <button className="icon-btn" onClick={logout} aria-label="Logout" title="Logout">
          <LogoutIcon />
        </button>
      </div>
    </>
  ) : (
    <div className="nav-auth">
      <Link to="/login" className="btn btn-ghost btn-sm">
        Patient Login
      </Link>
      <Link to="/doctor/login" className="btn btn-outline btn-sm">
        Doctor Login
      </Link>
      <Link to="/register" className="btn btn-primary btn-sm">
        Register
      </Link>
    </div>
  )

  return (
    <header className="navbar">
      <div className="nav-inner container">
        <Link to={home} className="brand" onClick={() => setMobileOpen(false)}>
          <span className="brand-logo">
            <StethoscopeIcon />
          </span>
          <span className="brand-text">
            <strong>Shifa</strong>Book
            <small>Doctor Appointment</small>
          </span>
        </Link>

        <form className="nav-search" onSubmit={submitSearch}>
          <SearchIcon size="sm" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search doctors, specialties, symptoms…"
            aria-label="Search doctors"
          />
        </form>

        <nav className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/search">Find Doctors</Link>
          {isLoggedIn && <Link to={dashboardLink}>Dashboard</Link>}
        </nav>

        <div className="nav-actions">
          <button className="icon-btn" onClick={toggleTheme} aria-label="Toggle theme" title="Toggle dark mode">
            {dark ? <SunIcon /> : <MoonIcon />}
          </button>
          {userArea}
          <button className="icon-btn nav-burger" onClick={() => setMobileOpen((o) => !o)} aria-label="Menu">
            {mobileOpen ? <XIcon /> : <MenuIcon />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="nav-mobile">
          <form className="nav-search" onSubmit={submitSearch}>
            <SearchIcon size="sm" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search doctors…"
              aria-label="Search doctors"
            />
          </form>
          <div className="nav-mobile-links">
            <Link to="/" onClick={() => setMobileOpen(false)}>
              Home
            </Link>
            <Link to="/search" onClick={() => setMobileOpen(false)}>
              Find Doctors
            </Link>
            {isLoggedIn && (
              <Link to={dashboardLink} onClick={() => setMobileOpen(false)}>
                Dashboard
              </Link>
            )}
            {!isLoggedIn && (
              <>
                <Link to="/login" onClick={() => setMobileOpen(false)}>
                  <UserIcon size="sm" /> Patient Login
                </Link>
                <Link to="/doctor/login" onClick={() => setMobileOpen(false)}>
                  Doctor Login
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
