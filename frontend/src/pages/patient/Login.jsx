// pages/patient/Login.jsx - patient login.
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { patientLogin } from '../../api/client.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useToast } from '../../context/ToastContext.jsx'
import { StethoscopeIcon, CheckIcon } from '../../components/icons.jsx'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { showToast } = useToast()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await patientLogin(email, password)
      login(data)
      showToast({ type: 'success', message: `Welcome back, ${data.user.name}!` })
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
        <h1>Patient Login</h1>
        <p className="auth-sub">Welcome back! Please log in to continue.</p>

        <form onSubmit={submit}>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          {error && <p className="form-error">{error}</p>}
          <button className="btn btn-primary btn-lg w-full" type="submit" disabled={loading}>
            {loading ? 'Logging in…' : 'Login'}
          </button>
        </form>

        <p className="auth-foot">
          New to ShifaBook? <Link to="/register">Create an account</Link>
        </p>
        <div className="demo-creds">
          <strong>Demo:</strong> alice@example.com / patient123
          <span>
            <CheckIcon size="xs" /> 3 patients, 15 doctors
          </span>
        </div>
      </div>
    </div>
  )
}
