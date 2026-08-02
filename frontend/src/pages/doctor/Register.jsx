// pages/doctor/Register.jsx - doctor self-registration (PMDC, fees,
// clinic details, languages). A multi-step feel in one form.
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { doctorRegister } from '../../api/client.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useToast } from '../../context/ToastContext.jsx'
import { StethoscopeIcon } from '../../components/icons.jsx'
import { PAK_CITIES, PAK_PROVINCES, GENDERS } from '../../utils/format.js'

const LANGS = ['English', 'Urdu', 'Punjabi', 'Sindhi', 'Pashto', 'Balochi', 'Saraiki']
const PHONE_RE = /^(\+?92|0)3\d{2}[ -]?\d{7}$/

export default function Register() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { showToast } = useToast()
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    pmdc_number: '',
    gender: 'Male',
    date_of_birth: '',
    years_of_experience: '',
    qualifications: '',
    specialization: '',
    hospital_name: '',
    clinic_address: '',
    city: '',
    province: 'Punjab',
    languages: ['English', 'Urdu'],
    biography: '',
    first_visit_fee: '',
    followup_fee: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  const toggleLang = (lang) => {
    setForm((f) => ({
      ...f,
      languages: f.languages.includes(lang)
        ? f.languages.filter((l) => l !== lang)
        : [...f.languages, lang],
    }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!PHONE_RE.test(form.phone.trim())) {
      setError('Please enter a valid Pakistani phone number, e.g. 0300-1234567.')
      return
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    if (form.biography.trim().length < 20) {
      setError('Biography must be at least 20 characters.')
      return
    }
    if (!form.first_visit_fee || !form.followup_fee) {
      setError('Please set both consultation fees.')
      return
    }
    setLoading(true)
    try {
      const data = await doctorRegister({
        ...form,
        years_of_experience: Number(form.years_of_experience) || 0,
        first_visit_fee: Number(form.first_visit_fee),
        followup_fee: Number(form.followup_fee),
      })
      login(data)
      showToast({ type: 'success', message: `Welcome to ShifaBook, Dr. ${form.name}!` })
      navigate('/doctor/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card auth-card-lg card">
        <div className="auth-logo">
          <StethoscopeIcon size="lg" />
        </div>
        <h1>Join ShifaBook as a Doctor</h1>
        <p className="auth-sub">Register your practice and start receiving online bookings.</p>

        <form onSubmit={submit} className="form-grid">
          <div className="field">
            <label htmlFor="name">Full name *</label>
            <input id="name" value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="Dr. Full Name" required />
          </div>
          <div className="field">
            <label htmlFor="email">Email *</label>
            <input id="email" type="email" value={form.email} onChange={(e) => set('email', e.target.value)} placeholder="doctor@clinic.com" required />
          </div>
          <div className="field">
            <label htmlFor="phone">Phone (Pakistan) *</label>
            <input id="phone" value={form.phone} onChange={(e) => set('phone', e.target.value)} placeholder="0300-1234567" required />
          </div>
          <div className="field">
            <label htmlFor="password">Password *</label>
            <input id="password" type="password" value={form.password} onChange={(e) => set('password', e.target.value)} placeholder="Min. 6 characters" required />
          </div>
          <div className="field">
            <label htmlFor="pmdc">PMDC Number *</label>
            <input id="pmdc" value={form.pmdc_number} onChange={(e) => set('pmdc_number', e.target.value)} placeholder="e.g. 12345-P" required />
          </div>
          <div className="field">
            <label htmlFor="dob">Date of birth *</label>
            <input id="dob" type="date" value={form.date_of_birth} onChange={(e) => set('date_of_birth', e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="gender">Gender *</label>
            <select id="gender" value={form.gender} onChange={(e) => set('gender', e.target.value)}>
              {GENDERS.map((g) => (
                <option key={g}>{g}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="exp">Years of experience *</label>
            <input id="exp" type="number" min="0" max="70" value={form.years_of_experience} onChange={(e) => set('years_of_experience', e.target.value)} placeholder="e.g. 8" required />
          </div>
          <div className="field">
            <label htmlFor="quals">Qualifications *</label>
            <input id="quals" value={form.qualifications} onChange={(e) => set('qualifications', e.target.value)} placeholder="e.g. MBBS, FCPS (Cardiology)" required />
          </div>
          <div className="field">
            <label htmlFor="spec">Specialization *</label>
            <input id="spec" value={form.specialization} onChange={(e) => set('specialization', e.target.value)} placeholder="e.g. Cardiologist" required />
          </div>
          <div className="field">
            <label htmlFor="hospital">Hospital / Clinic name *</label>
            <input id="hospital" value={form.hospital_name} onChange={(e) => set('hospital_name', e.target.value)} placeholder="e.g. Shifa International Hospital" required />
          </div>
          <div className="field">
            <label htmlFor="address">Clinic address *</label>
            <input id="address" value={form.clinic_address} onChange={(e) => set('clinic_address', e.target.value)} placeholder="e.g. Main Boulevard, Gulberg III" required />
          </div>
          <div className="field">
            <label htmlFor="city">City *</label>
            <select id="city" value={form.city} onChange={(e) => set('city', e.target.value)} required>
              <option value="">Select city</option>
              {PAK_CITIES.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="province">Province *</label>
            <select id="province" value={form.province} onChange={(e) => set('province', e.target.value)}>
              {PAK_PROVINCES.map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </div>
          <div className="field field-full">
            <label>Languages spoken *</label>
            <div className="chip-row">
              {LANGS.map((l) => (
                <button
                  type="button"
                  key={l}
                  className={`chip ${form.languages.includes(l) ? 'chip-active' : ''}`}
                  onClick={() => toggleLang(l)}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>
          <div className="field field-full">
            <label htmlFor="bio">Biography * (min 20 chars)</label>
            <textarea id="bio" rows="3" value={form.biography} onChange={(e) => set('biography', e.target.value)} placeholder="Tell patients about your practice, experience and approach…" required />
          </div>
          <div className="field">
            <label htmlFor="fee1">First visit fee (Rs.) *</label>
            <input id="fee1" type="number" min="0" value={form.first_visit_fee} onChange={(e) => set('first_visit_fee', e.target.value)} placeholder="e.g. 2500" required />
          </div>
          <div className="field">
            <label htmlFor="fee2">Follow-up fee (Rs.) *</label>
            <input id="fee2" type="number" min="0" value={form.followup_fee} onChange={(e) => set('followup_fee', e.target.value)} placeholder="e.g. 1500" required />
          </div>

          {error && <p className="form-error field-full">{error}</p>}

          <div className="field-full">
            <button className="btn btn-primary btn-lg w-full" type="submit" disabled={loading}>
              {loading ? 'Creating your profile…' : 'Register as a doctor'}
            </button>
          </div>
        </form>

        <p className="auth-foot">
          Already registered? <Link to="/doctor/login">Doctor login</Link>
        </p>
      </div>
    </div>
  )
}
