// pages/doctor/Profile.jsx - view & edit doctor profile and fees.
import { useEffect, useState } from 'react'
import { updateMyDoctorProfile, getMyDoctorProfile } from '../../api/client.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useToast } from '../../context/ToastContext.jsx'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import Skeleton from '../../components/Skeleton.jsx'
import { ShieldIcon, StarIcon } from '../../components/icons.jsx'
import { PAK_CITIES, PAK_PROVINCES, GENDERS } from '../../utils/format.js'

const LANGS = ['English', 'Urdu', 'Punjabi', 'Sindhi', 'Pashto', 'Balochi', 'Saraiki']

export default function Profile() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [form, setForm] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getMyDoctorProfile()
      .then((d) => {
        setForm({
          name: d.name,
          phone: d.phone,
          pmdc_number: d.pmdc_number || '',
          gender: d.gender || 'Male',
          years_of_experience: d.years_of_experience || 0,
          qualifications: d.qualifications || '',
          specialization: d.specialization,
          hospital_name: d.hospital_name || '',
          clinic_address: d.clinic_address || '',
          city: d.city || '',
          province: d.province || 'Punjab',
          languages: d.languages || ['English', 'Urdu'],
          biography: d.biography || '',
          first_visit_fee: d.first_visit_fee || 0,
          followup_fee: d.followup_fee || 0,
        })
      })
      .catch((err) => showToast({ type: 'error', message: err.message }))
      .finally(() => setLoading(false))
  }, [])

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  const toggleLang = (lang) => {
    setForm((f) => ({
      ...f,
      languages: f.languages.includes(lang) ? f.languages.filter((l) => l !== lang) : [...f.languages, lang],
    }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await updateMyDoctorProfile({
        ...form,
        years_of_experience: Number(form.years_of_experience) || 0,
        first_visit_fee: Number(form.first_visit_fee),
        followup_fee: Number(form.followup_fee),
      })
      showToast({ type: 'success', message: 'Profile updated.' })
    } catch (err) {
      showToast({ type: 'error', message: err.message })
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <DashboardLayout title="My Profile"><Skeleton height="400px" /></DashboardLayout>
  if (!form) return <DashboardLayout title="My Profile" />

  return (
    <DashboardLayout title="My Profile">
      <div className="dash-grid-2">
        <form className="card form-grid" onSubmit={submit}>
          <h2 className="card-title field-full">Personal details</h2>
          <div className="field">
            <label htmlFor="name">Full name</label>
            <input id="name" value={form.name} onChange={(e) => set('name', e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="phone">Phone</label>
            <input id="phone" value={form.phone} onChange={(e) => set('phone', e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="pmdc">PMDC Number</label>
            <input id="pmdc" value={form.pmdc_number} onChange={(e) => set('pmdc_number', e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="gender">Gender</label>
            <select id="gender" value={form.gender} onChange={(e) => set('gender', e.target.value)}>
              {GENDERS.map((g) => (
                <option key={g}>{g}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="exp">Years of experience</label>
            <input id="exp" type="number" min="0" max="70" value={form.years_of_experience} onChange={(e) => set('years_of_experience', e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="quals">Qualifications</label>
            <input id="quals" value={form.qualifications} onChange={(e) => set('quals', e.target.value)} />
          </div>

          <h2 className="card-title field-full">Practice details</h2>
          <div className="field">
            <label htmlFor="spec">Specialization</label>
            <input id="spec" value={form.specialization} onChange={(e) => set('specialization', e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="hospital">Hospital / Clinic</label>
            <input id="hospital" value={form.hospital_name} onChange={(e) => set('hospital_name', e.target.value)} />
          </div>
          <div className="field field-full">
            <label htmlFor="address">Clinic address</label>
            <input id="address" value={form.clinic_address} onChange={(e) => set('clinic_address', e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="city">City</label>
            <select id="city" value={form.city} onChange={(e) => set('city', e.target.value)}>
              <option value="">Select city</option>
              {PAK_CITIES.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="province">Province</label>
            <select id="province" value={form.province} onChange={(e) => set('province', e.target.value)}>
              {PAK_PROVINCES.map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </div>
          <div className="field field-full">
            <label>Languages spoken</label>
            <div className="chip-row">
              {LANGS.map((l) => (
                <button type="button" key={l} className={`chip ${form.languages.includes(l) ? 'chip-active' : ''}`} onClick={() => toggleLang(l)}>
                  {l}
                </button>
              ))}
            </div>
          </div>
          <div className="field field-full">
            <label htmlFor="bio">Biography</label>
            <textarea id="bio" rows="4" value={form.biography} onChange={(e) => set('biography', e.target.value)} />
          </div>

          <h2 className="card-title field-full">Fees (PKR)</h2>
          <div className="field">
            <label htmlFor="fee1">First visit fee</label>
            <input id="fee1" type="number" min="0" value={form.first_visit_fee} onChange={(e) => set('first_visit_fee', e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="fee2">Follow-up fee</label>
            <input id="fee2" type="number" min="0" value={form.followup_fee} onChange={(e) => set('followup_fee', e.target.value)} />
          </div>

          <div className="field-full">
            <button className="btn btn-primary btn-lg w-full" type="submit" disabled={saving}>
              {saving ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </form>

        <aside className="card">
          <h2 className="card-title">Public preview</h2>
          <div className="profile-preview">
            <div className="avatar avatar-lg" data-specialty={form.specialization}>
              {form.name
                ?.split(' ')
                .slice(-2)
                .map((w) => w[0])
                .join('')
                .toUpperCase()}
            </div>
            <h3>{form.name}</h3>
            <p className="doctor-spec">{form.specialization}</p>
            <p className="doctor-exp">{form.years_of_experience} yrs experience</p>
            <div className="doctor-rating">
              <StarIcon size="sm" />
              <span>Verified profile</span>
            </div>
            <p className="hint">
              <ShieldIcon size="xs" /> PMDC {form.pmdc_number || 'not set'}
            </p>
          </div>
          <p className="hint">
            This is how patients see you. Add your clinic address, bio and languages to rank higher in search.
          </p>
        </aside>
      </div>
    </DashboardLayout>
  )
}
