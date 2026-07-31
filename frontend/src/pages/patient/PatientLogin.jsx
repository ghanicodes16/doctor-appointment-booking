// pages/patient/PatientLogin.jsx - the patient login page.
// Collects email + password, calls the backend, saves the returned token
// via useAuth().login(), and redirects the patient to the booking page.
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { patientLogin } from '../../api/client.js'
import Alert from '../../components/Alert.jsx'
import Spinner from '../../components/Spinner.jsx'
import { useAuth } from '../../context/AuthContext.jsx'

export default function PatientLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const { login } = useAuth()
  const navigate = useNavigate()

  // Called when the form is submitted.
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await patientLogin(email, password)
      login(data) // store the token + user info
      navigate('/book') // go to the booking page
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="card auth-card">
        <h2>Patient Login</h2>
        <p className="muted">Welcome back. Please sign in to book an appointment.</p>

        {error && <Alert type="error">{error}</Alert>}

        <form onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
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
          Don&apos;t have an account? <Link to="/register">Register here</Link>
        </p>
        <p className="auth-switch">
          Doctor? <Link to="/doctor/login">Doctor login</Link>
        </p>
      </div>
    </div>
  )
}
