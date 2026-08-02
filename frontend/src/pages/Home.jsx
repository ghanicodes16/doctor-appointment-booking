// pages/Home.jsx - landing page with hero search, popular specialties,
// recommended doctors and a simple "how it works" section.
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { searchDoctors, getSpecializations, getRecommendations, addFavorite, removeFavorite } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useToast } from '../context/ToastContext.jsx'
import DoctorCard from '../components/DoctorCard.jsx'
import Skeleton from '../components/Skeleton.jsx'
import {
  SearchIcon,
  StethoscopeIcon,
  CalendarIcon,
  UserIcon,
  CheckIcon,
  ShieldIcon,
} from '../components/icons.jsx'

const HERO_BG = {
  backgroundImage:
    'radial-gradient(ellipse at top left, var(--hero-glow-1), transparent 55%), radial-gradient(ellipse at bottom right, var(--hero-glow-2), transparent 55%)',
}

export default function Home() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const { user, role, isLoggedIn } = useAuth()
  const [query, setQuery] = useState('')
  const [city, setCity] = useState('')
  const [specializations, setSpecializations] = useState([])
  const [topDoctors, setTopDoctors] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getSpecializations(), getRecommendations()])
      .then(([specs, recs]) => {
        setSpecializations(specs)
        setRecommendations(recs)
        return searchDoctors({ sort: 'rating' })
      })
      .then(setTopDoctors)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const submitSearch = (e) => {
    e.preventDefault()
    navigate(`/search?q=${encodeURIComponent(query)}${city ? `&city=${city}` : ''}`)
  }

  const toggleFavorite = (doctor) => {
    if (doctor.is_favorite) {
      removeFavorite(doctor.id)
        .then(() => {
          setTopDoctors((prev) => prev.map((d) => (d.id === doctor.id ? { ...d, is_favorite: false } : d)))
          showToast({ type: 'info', message: 'Removed from favorites' })
        })
        .catch((err) => showToast({ type: 'error', message: err.message }))
    } else {
      addFavorite(doctor.id)
        .then(() => {
          setTopDoctors((prev) => prev.map((d) => (d.id === doctor.id ? { ...d, is_favorite: true } : d)))
          showToast({ type: 'success', message: 'Added to favorites' })
        })
        .catch((err) => showToast({ type: 'error', message: err.message }))
    }
  }

  return (
    <div className="page">
      {/* Hero */}
      <section className="hero" style={HERO_BG}>
        <div className="container hero-inner">
          <div className="hero-content">
            <span className="hero-badge">
              <ShieldIcon size="sm" /> Trusted by patients across Pakistan
            </span>
            <h1>
              Find the right doctor for <span>every symptom</span>
            </h1>
            <p>
              Search by doctor, specialty or symptom — check live availability, compare
              consultation fees and book your appointment online in seconds.
            </p>

            <form className="hero-search" onSubmit={submitSearch}>
              <div className="hero-search-field">
                <SearchIcon size="sm" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Doctor name, specialty or symptom…"
                  aria-label="Search"
                />
              </div>
              <select value={city} onChange={(e) => setCity(e.target.value)} aria-label="City">
                <option value="">All cities</option>
                {['Lahore', 'Karachi', 'Islamabad', 'Rawalpindi', 'Faisalabad', 'Multan', 'Peshawar', 'Quetta'].map(
                  (c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  )
                )}
              </select>
              <button className="btn btn-primary btn-lg" type="submit">
                <SearchIcon size="sm" /> Search
              </button>
            </form>

            <div className="hero-quick">
              <span>Popular:</span>
              {['Tooth pain', 'Stomach pain', 'Skin rash', 'Chest pain'].map((s) => (
                <button key={s} className="chip" onClick={() => navigate(`/search?q=${encodeURIComponent(s)}`)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Specialties */}
      <section className="section container">
        <div className="section-head">
          <div>
            <h2>Browse by specialty</h2>
            <p>Verified doctors across 15+ specialities, all in one place</p>
          </div>
          <Link to="/search" className="btn btn-ghost btn-sm">
            View all
          </Link>
        </div>
        <div className="spec-grid">
          {loading
            ? Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} variant="card" height="96px" />)
            : specializations.slice(0, 8).map((s) => (
                <Link key={s.id} to={`/search?specialization=${encodeURIComponent(s.name)}`} className="spec-card">
                  <span className="spec-icon">
                    <StethoscopeIcon />
                  </span>
                  <div>
                    <strong>{s.name}</strong>
                    <small>{s.doctor_count} doctors</small>
                  </div>
                </Link>
              ))}
        </div>
      </section>

      {/* Top doctors */}
      <section className="section container">
        <div className="section-head">
          <div>
            <h2>Top-rated doctors</h2>
            <p>Highest rated by patients this month</p>
          </div>
        </div>
        <div className="doctor-grid">
          {loading
            ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} variant="card" height="180px" />)
            : topDoctors.slice(0, 6).map((d) => (
                <DoctorCard key={d.id} doctor={d} onToggleFavorite={toggleFavorite} />
              ))}
        </div>
      </section>

      {/* How it works */}
      <section className="section container">
        <div className="section-head center">
          <h2>How ShifaBook works</h2>
          <p>From symptom to appointment in three simple steps</p>
        </div>
        <div className="how-grid">
          {[
            { icon: <UserIcon />, title: 'Describe your symptom', text: 'Tell us what you’re feeling — we’ll match you with the right specialist.' },
            { icon: <CalendarIcon />, title: 'Pick a doctor & time', text: 'Compare fees and ratings, then book a slot that fits your day.' },
            { icon: <CheckIcon />, title: 'Visit & confirm', text: 'Get instant confirmation and reminders. No waiting rooms online.' },
          ].map((step, i) => (
            <div key={i} className="how-card">
              <span className="how-step">0{i + 1}</span>
              <div className="how-icon">{step.icon}</div>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="section container">
        <div className="cta-banner">
          <div>
            <h2>Are you a doctor?</h2>
            <p>Create your profile, manage your schedule and reach more patients online.</p>
          </div>
          <Link to="/doctor/register" className="btn btn-light btn-lg">
            Join as a doctor
          </Link>
        </div>
      </section>
    </div>
  )
}
