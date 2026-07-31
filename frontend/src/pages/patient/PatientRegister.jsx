// pages/patient/PatientRegister.jsx - the patient registration page.
// Creates a new patient account and, on success, logs the patient in
// automatically (the backend returns a token right away).
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { patientRegister } from '../../api/client.js'
import Alert from '../../components/Alert.jsx'
import Spinner from '../../components/Spinner.jsx'
import { useAuth } from '../../context/AuthContext.jsx'

export default function PatientRegister() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
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
      const data = await patientRegister(name, email, phone, password)
      login(data) // register + auto login in one step
      navigate('/book')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="card auth-card">
        <h2>Patient Registration</h2>
        <p className="muted">Create a free account to book doctor appointments.</p>

        {error && <Alert type="error">{error}</Alert>}

        <form onSubmit={handleSubmit}>
          <label className="field">
            <span>Full name</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Alice Johnson"
              required
            />
          </label>
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
            <span>Phone number</span>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="e.g. 555-1234"
              required
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 6 characters"
              minLength={6}
              required
            />
          </label>
          <button className="btn btn-primary btn-block" disabled={loading}>
            {loading ? <Spinner small /> : 'Create account'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  )
}
