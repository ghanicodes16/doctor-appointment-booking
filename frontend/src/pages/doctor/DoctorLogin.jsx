// pages/doctor/DoctorLogin.jsx - the doctor login page.
// Almost identical to the patient login page, but it calls the doctor
// login endpoint and redirects the doctor to their dashboard.
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { doctorLogin } from '../../api/client.js'
import Alert from '../../components/Alert.jsx'
import Spinner from '../../components/Spinner.jsx'
import { useAuth } from '../../context/AuthContext.jsx'

export default function DoctorLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await doctorLogin(email, password)
      login(data)
      navigate('/doctor/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="card auth-card">
        <h2>Doctor Login</h2>
        <p className="muted">Sign in to manage your appointments.</p>

        {error && <Alert type="error">{error}</Alert>}

        <form onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="doctor@clinic.com"
              required
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Your password"
              required
            />
          </label>
          <button className="btn btn-primary btn-block" disabled={loading}>
            {loading ? <Spinner small /> : 'Log in'}
          </button>
        </form>

        <p className="auth-switch">
          Patient? <Link to="/login">Patient login</Link>
        </p>
      </div>
    </div>
  )
}
