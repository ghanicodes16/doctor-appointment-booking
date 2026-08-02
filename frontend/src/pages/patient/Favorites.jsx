// pages/patient/Favorites.jsx - the patient's saved doctors.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getFavorites, removeFavorite } from '../../api/client.js'
import { useToast } from '../../context/ToastContext.jsx'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import DoctorCard from '../../components/DoctorCard.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import Skeleton from '../../components/Skeleton.jsx'
import { HeartIcon } from '../../components/icons.jsx'

export default function Favorites() {
  const { showToast } = useToast()
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getFavorites()
      .then(setFavorites)
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setLoading(false))
  }, [])

  const toggleFavorite = (doctor) => {
    removeFavorite(doctor.id)
      .then(() => {
        setFavorites((prev) => prev.filter((d) => d.id !== doctor.id))
        showToast({ type: 'info', message: 'Removed from favorites' })
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
  }

  return (
    <DashboardLayout title="Favorite Doctors">
      {loading ? (
        <div className="doctor-grid">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} variant="card" height="180px" />
          ))}
        </div>
      ) : favorites.length === 0 ? (
        <EmptyState
          icon={<HeartIcon size="lg" />}
          title="No favourites yet"
          message="Tap the heart icon on any doctor to save them here for quick access."
          action={
            <Link to="/search" className="btn btn-primary btn-sm">
              Find doctors
            </Link>
          }
        />
      ) : (
        <div className="doctor-grid">
          {favorites.map((d) => (
            <DoctorCard key={d.id} doctor={d} onToggleFavorite={toggleFavorite} />
          ))}
        </div>
      )}
    </DashboardLayout>
  )
}
