// components/DoctorCard.jsx - the standard doctor card used in search
// results, the home page and favorites.
import { useNavigate } from 'react-router-dom'
import { LocationIcon, HeartIcon, StethoscopeIcon, RupeeIcon, CheckIcon } from './icons.jsx'
import StarRating from './StarRating.jsx'
import { formatCurrency } from '../utils/format.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function DoctorCard({ doctor, onToggleFavorite }) {
  const navigate = useNavigate()
  const { isLoggedIn, role } = useAuth()
  const isFavorite = doctor.is_favorite

  const toggleFavorite = (e) => {
    e.stopPropagation()
    if (!isLoggedIn || role !== 'patient') {
      navigate('/login')
      return
    }
    onToggleFavorite?.(doctor)
  }

  return (
    <article className="doctor-card" onClick={() => navigate(`/doctors/${doctor.id}`)}>
      <div className="doctor-card-top">
        <div className="avatar avatar-lg" data-specialty={doctor.specialization}>
          {doctor.name
            .split(' ')
            .slice(-2)
            .map((w) => w[0])
            .join('')
            .toUpperCase()}
        </div>
        <div className="doctor-card-info">
          <h3 className="doctor-name">{doctor.name}</h3>
          <p className="doctor-spec">
            <StethoscopeIcon size="xs" /> {doctor.specialization}
          </p>
          <p className="doctor-exp">{doctor.years_of_experience ? `${doctor.years_of_experience} yrs experience` : 'Specialist'}</p>
        </div>
        <button
          className={`icon-btn fav-btn ${isFavorite ? 'fav-active' : ''}`}
          onClick={toggleFavorite}
          aria-label="Toggle favourite"
        >
          <HeartIcon />
        </button>
      </div>

      <div className="doctor-card-body">
        <div className="doctor-meta">
          {doctor.city && (
            <span>
              <LocationIcon size="xs" /> {doctor.city}
            </span>
          )}
          {doctor.first_visit_fee != null && (
            <span className="fee">
              <RupeeIcon size="xs" /> {formatCurrency(doctor.first_visit_fee)}
            </span>
          )}
        </div>
        <div className="doctor-rating">
          <StarRating value={doctor.rating_avg || 0} />
          <span className="rating-num">{(doctor.rating_avg || 0).toFixed(1)}</span>
          <span className="rating-count">({doctor.rating_count || 0} reviews)</span>
        </div>
        {doctor.booking_enabled === true && (
          <span className="available-tag">
            <CheckIcon size="xs" /> Booking open
          </span>
        )}
      </div>
    </article>
  )
}
