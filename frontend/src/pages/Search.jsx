// pages/Search.jsx - advanced doctor search with filters (specialty,
// city, rating, max fee), sorting and symptom matching.
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  searchDoctors,
  getSpecializations,
  getSymptoms,
  addFavorite,
  removeFavorite,
} from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useToast } from '../context/ToastContext.jsx'
import DoctorCard from '../components/DoctorCard.jsx'
import Skeleton from '../components/Skeleton.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { SearchIcon, StethoscopeIcon } from '../components/icons.jsx'
import { PAK_CITIES } from '../utils/format.js'

export default function Search() {
  const [params, setParams] = useSearchParams()
  const { showToast } = useToast()
  const { role } = useAuth()

  const q = params.get('q') || ''
  const spec = params.get('specialization') || ''
  const city = params.get('city') || ''
  const minRating = params.get('min_rating') || ''
  const maxFee = params.get('fee_max') || ''
  const sort = params.get('sort') || 'relevance'

  const [specializations, setSpecializations] = useState([])
  const [symptomSuggestions, setSymptomSuggestions] = useState([])
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSpecializations().then(setSpecializations).catch(() => {})
  }, [])

  useEffect(() => {
    if (q) {
      getSymptoms(q).then(setSymptomSuggestions).catch(() => {})
    } else {
      setSymptomSuggestions([])
    }
  }, [q])

  useEffect(() => {
    setLoading(true)
    searchDoctors({ q, specialization: spec, city, min_rating: minRating, fee_max: maxFee, sort })
      .then(setResults)
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setLoading(false))
  }, [q, spec, city, minRating, maxFee, sort])

  const setParam = (key, value) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: false })
  }

  const toggleFavorite = (doctor) => {
    const fn = doctor.is_favorite ? removeFavorite : addFavorite
    fn(doctor.id)
      .then(() => {
        setResults((prev) => prev.map((d) => (d.id === doctor.id ? { ...d, is_favorite: !doctor.is_favorite } : d)))
        showToast({ type: 'success', message: doctor.is_favorite ? 'Removed from favorites' : 'Added to favorites' })
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
  }

  return (
    <div className="page container">
      <div className="page-head">
        <h1>Find a doctor</h1>
        <p>
          {loading
            ? 'Searching…'
            : `${results.length} ${results.length === 1 ? 'doctor' : 'doctors'} found`}
          {q && (
            <>
              {' '}
              for “<strong>{q}</strong>”
            </>
          )}
        </p>
      </div>

      <div className="search-layout">
        {/* Filters sidebar */}
        <aside className="filters">
          <form
            className="filter-search"
            onSubmit={(e) => {
              e.preventDefault()
              setParam('q', e.target.q.value)
            }}
          >
            <SearchIcon size="sm" />
            <input name="q" defaultValue={q} placeholder="Search symptom, name…" />
          </form>

          {symptomSuggestions.length > 0 && (
            <div className="symptom-suggest">
              <p className="filter-label">Matching symptoms</p>
              {symptomSuggestions.map((s) => (
                <button
                  key={s.id}
                  className="chip"
                  onClick={() => setParam('q', s.name)}
                >
                  {s.name}
                </button>
              ))}
            </div>
          )}

          <div className="filter-group">
            <label className="filter-label">Specialty</label>
            <select value={spec} onChange={(e) => setParam('specialization', e.target.value)}>
              <option value="">All specialties</option>
              {specializations.map((s) => (
                <option key={s.id} value={s.name}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">City</label>
            <select value={city} onChange={(e) => setParam('city', e.target.value)}>
              <option value="">All cities</option>
              {PAK_CITIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">Minimum rating</label>
            <select value={minRating} onChange={(e) => setParam('min_rating', e.target.value)}>
              <option value="">Any rating</option>
              <option value="4.5">4.5+</option>
              <option value="4">4.0+</option>
              <option value="3.5">3.5+</option>
              <option value="3">3.0+</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">Max fee (Rs.)</label>
            <select value={maxFee} onChange={(e) => setParam('fee_max', e.target.value)}>
              <option value="">Any fee</option>
              <option value="1000">Under 1,000</option>
              <option value="2000">Under 2,000</option>
              <option value="3000">Under 3,000</option>
              <option value="5000">Under 5,000</option>
            </select>
          </div>

          <button className="btn btn-ghost btn-sm" onClick={() => setParams(new URLSearchParams())}>
            Clear all filters
          </button>
        </aside>

        {/* Results */}
        <div className="search-results">
          <div className="sort-row">
            <label className="filter-label">Sort by</label>
            <select value={sort} onChange={(e) => setParam('sort', e.target.value)}>
              <option value="relevance">Relevance</option>
              <option value="rating">Highest rated</option>
              <option value="fee_low">Fee: low to high</option>
              <option value="fee_high">Fee: high to low</option>
            </select>
          </div>

          {loading ? (
            <div className="doctor-grid">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} variant="card" height="180px" />
              ))}
            </div>
          ) : results.length === 0 ? (
            <EmptyState
              icon={<StethoscopeIcon size="lg" />}
              title="No doctors found"
              message="Try a different symptom, city or remove some filters."
            />
          ) : (
            <div className="doctor-grid">
              {results.map((d) => (
                <DoctorCard key={d.id} doctor={d} onToggleFavorite={role === 'patient' ? toggleFavorite : undefined} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
