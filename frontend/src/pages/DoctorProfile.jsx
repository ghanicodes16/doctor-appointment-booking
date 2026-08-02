// pages/DoctorProfile.jsx - public doctor profile with booking widget
// (date strip + slots), fees, schedule summary and patient reviews.
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  getDoctor,
  getAvailableSlots,
  getDoctorSchedule,
  getDoctorReviews,
  bookAppointment,
  addFavorite,
  removeFavorite,
} from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useToast } from '../context/ToastContext.jsx'
import { useTheme } from '../context/ThemeContext.jsx'
import StarRating from '../components/StarRating.jsx'
import Skeleton from '../components/Skeleton.jsx'
import DateStrip from '../components/DateStrip.jsx'
import EmptyState from '../components/EmptyState.jsx'
import {
  LocationIcon,
  HeartIcon,
  StethoscopeIcon,
  RupeeIcon,
  PhoneIcon,
  ClockIcon,
  BriefcaseIcon,
  ShieldIcon,
  CalendarIcon,
} from '../components/icons.jsx'
import { formatCurrency, formatTime12h, formatDateLong, DAY_NAMES } from '../utils/format.js'

export default function DoctorProfile() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const { isLoggedIn, role, user } = useAuth()

  const [doctor, setDoctor] = useState(null)
  const [schedule, setSchedule] = useState([])
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState('')
  const [slots, setSlots] = useState([])
  const [slotsMessage, setSlotsMessage] = useState('')
  const [slotsLoading, setSlotsLoading] = useState(false)
  const [booking, setBooking] = useState(false)

  useEffect(() => {
    Promise.all([getDoctor(id), getDoctorSchedule(id), getDoctorReviews(id)])
      .then(([d, sched, revs]) => {
        setDoctor(d)
        setSchedule(sched)
        setReviews(revs)
        setSelectedDate('')
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!selectedDate) {
      setSlots([])
      setSlotsMessage('')
      return
    }
    setSlotsLoading(true)
    setSlotsMessage('')
    getAvailableSlots(id, selectedDate)
      .then((res) => {
        setSlots(res.available_slots || [])
        if (res.is_available === false && res.message) setSlotsMessage(res.message)
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setSlotsLoading(false))
  }, [selectedDate, id])

  const toggleFavorite = () => {
    if (!isLoggedIn) return navigate('/login')
    const fn = doctor.is_favorite ? removeFavorite : addFavorite
    fn(doctor.id)
      .then(() => {
        setDoctor((prev) => ({ ...prev, is_favorite: !prev.is_favorite }))
        showToast({ type: 'success', message: doctor.is_favorite ? 'Removed from favorites' : 'Added to favorites' })
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
  }

  const handleBook = (slot) => {
    if (!isLoggedIn || role !== 'patient') return navigate('/login')
    setBooking(true)
    bookAppointment(doctor.id, selectedDate, slot)
      .then(() => {
        showToast({ type: 'success', message: `Appointment booked with ${doctor.name} on ${formatDateLong(selectedDate)} at ${formatTime12h(slot)}` })
        setSlots((prev) => prev.filter((s) => s.time !== slot && s !== slot))
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setBooking(false))
  }

  if (loading) {
    return (
      <div className="page container">
        <div className="profile-layout">
          <Skeleton variant="card" height="300px" />
          <Skeleton variant="card" height="300px" />
        </div>
      </div>
    )
  }

  if (!doctor) {
    return (
      <div className="page container">
        <EmptyState title="Doctor not found" message="This profile may have been removed." />
      </div>
    )
  }

  const workingDays = schedule.filter((d) => d.is_available)
  const workingIndices = new Set(workingDays.map((w) => w.day_of_week))

  return (
    <div className="page container">
      {/* Header card */}
      <section className="profile-header">
        <div className="avatar avatar-xl" data-specialty={doctor.specialization}>
          {doctor.name
            .split(' ')
            .slice(-2)
            .map((w) => w[0])
            .join('')
            .toUpperCase()}
        </div>
        <div className="profile-header-info">
          <div className="profile-name-row">
            <h1>{doctor.name}</h1>
            <button
              className={`icon-btn fav-btn ${doctor.is_favorite ? 'fav-active' : ''}`}
              onClick={toggleFavorite}
              aria-label="Toggle favourite"
            >
              <HeartIcon />
            </button>
          </div>
          <p className="profile-spec">
            <StethoscopeIcon size="sm" /> {doctor.specialization}
            {doctor.years_of_experience && (
              <span className="profile-exp">
                <BriefcaseIcon size="xs" /> {doctor.years_of_experience} yrs experience
              </span>
            )}
          </p>
          <div className="profile-meta">
            {doctor.city && (
              <span>
                <LocationIcon size="sm" /> {doctor.city}
              </span>
            )}
            {doctor.clinic_address && <span>{doctor.clinic_address}</span>}
            {doctor.phone && (
              <span>
                <PhoneIcon size="sm" /> {doctor.phone}
              </span>
            )}
          </div>
          <div className="profile-rating">
            <StarRating value={doctor.rating_avg || 0} size="lg" />
            <span className="rating-num">{(doctor.rating_avg || 0).toFixed(1)}</span>
            <span className="rating-count">({doctor.rating_count || 0} reviews)</span>
            <span className="verified-badge">
              <ShieldIcon size="xs" /> PMDC {doctor.pmdc_number || 'Verified'}
            </span>
          </div>
        </div>
        <div className="profile-fees">
          <div className="fee-box">
            <small>First visit</small>
            <strong>{formatCurrency(doctor.first_visit_fee)}</strong>
          </div>
          <div className="fee-box">
            <small>Follow-up</small>
            <strong>{formatCurrency(doctor.followup_fee)}</strong>
          </div>
        </div>
      </section>

      {/* Availability warning / body */}
      <section className="availability-banner">
        <span className={`status-pill ${doctor.booking_enabled ? 'status-on' : 'status-off'}`}>
          {doctor.booking_enabled ? 'Online booking is open' : 'Online booking is currently off'}
        </span>
        {!doctor.booking_enabled && <p>This doctor is not accepting online bookings right now.</p>}
      </section>

      <div className="profile-layout">
        {/* Booking widget */}
        <section className="card booking-card">
          <h2 className="card-title">
            <CalendarIcon size="sm" /> Book an appointment
          </h2>
          {doctor.booking_enabled === false ? (
            <EmptyState
              title="Booking unavailable"
              message="This doctor has turned off online booking. Please try again later."
            />
          ) : (
            <>
              <p className="card-sub">Select a date to see available time slots</p>
              <DateStrip selected={selectedDate} onSelect={setSelectedDate} />
              <div className="slot-area">
                {!selectedDate ? (
                  <p className="hint">Pick a date above to view slots.</p>
                ) : slotsLoading ? (
                  <div className="slot-grid">
                    {Array.from({ length: 8 }).map((_, i) => (
                      <Skeleton key={i} variant="text" height="36px" />
                    ))}
                  </div>
                ) : slotsMessage ? (
                  <p className="hint">{slotsMessage}</p>
                ) : slots.length === 0 ? (
                  <p className="hint">No available slots on {formatDateLong(selectedDate)}.</p>
                ) : (
                  <div className="slot-grid">
                    {slots.map((s, i) => {
                      const time = typeof s === 'string' ? s : s.time
                      return (
                        <button
                          key={i}
                          className="slot-chip"
                          disabled={booking}
                          onClick={() => handleBook(time)}
                        >
                          {formatTime12h(time)}
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
              <p className="fee-note">
                <RupeeIcon size="xs" />
                First visit <strong>{formatCurrency(doctor.first_visit_fee)}</strong> · Follow-up{' '}
                <strong>{formatCurrency(doctor.followup_fee)}</strong>. Pay at the clinic.
              </p>
            </>
          )}
        </section>

        {/* About + schedule + reviews */}
        <div className="profile-side">
          <section className="card">
            <h2 className="card-title">About</h2>
            <p className="about-text">
              {doctor.biography || 'Dr. ' + doctor.name + ' is a verified ' + doctor.specialization + ' based in ' + (doctor.city || 'Pakistan') + '.'}
            </p>
            {doctor.qualifications && (
              <p className="about-quals">
                <ShieldIcon size="xs" /> {doctor.qualifications}
              </p>
            )}
          </section>

          <section className="card">
            <h2 className="card-title">
              <ClockIcon size="sm" /> Clinic schedule
            </h2>
            <ul className="schedule-list">
              {DAY_NAMES.map((day, i) => {
                const entry = workingDays.find((w) => w.day_of_week === i)
                return (
                  <li key={day} className={entry ? '' : 'closed'}>
                    <span>{day}</span>
                    <span>
                      {entry ? `${formatTime12h(entry.start_time)} – ${formatTime12h(entry.end_time)}` : 'Closed'}
                    </span>
                  </li>
                )
              })}
            </ul>
          </section>

          <section className="card">
            <h2 className="card-title">Patient reviews</h2>
            {reviews.length === 0 ? (
              <p className="hint">No reviews yet.</p>
            ) : (
              <div className="review-list">
                {reviews.map((r) => (
                  <div key={r.id} className="review-item">
                    <div className="review-head">
                      <strong>{r.patient_name}</strong>
                      <StarRating value={r.rating} />
                    </div>
                    {r.comment && <p>{r.comment}</p>}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}
