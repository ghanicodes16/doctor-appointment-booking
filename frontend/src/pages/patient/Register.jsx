// pages/patient/Register.jsx - patient registration.
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { patientRegister } from '../../api/client.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useToast } from '../../context/ToastContext.jsx'
import { StethoscopeIcon } from '../../components/icons.jsx'

const PHONE_RE = /^(\+?92|0)3\d{2}[ -]?\d{7}$/

export default function Register() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { showToast } = useToast()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!PHONE_RE.test(phone.trim())) {
      setError('Please enter a valid Pakistani phone number, e.g. 0300-1234567.')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    setLoading(true)
    try {
      const data = await patientRegister(name, email, phone, password)
      login(data)
      showToast({ type: 'success', message: `Account created. Welcome, ${name}!` })
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card card">
        <div className="auth-logo">
          <StethoscopeIcon size="lg" />
        </div>
        <h1>Create Account</h1>
        <p className="auth-sub">Book doctor appointments in seconds.</p>

        <form onSubmit={submit}>
          <div className="field">
            <label htmlFor="name">Full name</label>
            <input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Ali Raza" required />
          </div>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
          </div>
          <div className="field">
            <label htmlFor="phone">Phone (Pakistan)</label>
            <input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="0300-1234567" required />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min. 6 characters" required />
          </div>
          {error && <p className="form-error">{error}</p>}
          <button className="btn btn-primary btn-lg w-full" type="submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Register'}
          </button>
        </form>

        <p className="auth-foot">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  )
}
