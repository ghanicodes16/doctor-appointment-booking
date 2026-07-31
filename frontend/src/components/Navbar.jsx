// components/Navbar.jsx - the top navigation bar shown on every page.
// It contains the brand name and, depending on login state, either
// login/register links or the current user's name and a logout button.
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Navbar() {
  const { user, role, isLoggedIn, logout } = useAuth()
  const navigate = useNavigate()

  // Log the user out and send them back to the home page.
  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="brand">
          <span className="brand-icon">+</span>
          <span className="brand-text">MediBook</span>
        </Link>

        <nav className="navbar-links">
          {!isLoggedIn && (
            <>
              <Link to="/login" className="nav-link">
                Patient Login
              </Link>
              <Link to="/doctor/login" className="nav-link">
                Doctor Login
              </Link>
            </>
          )}

          {isLoggedIn && (
            <>
              {role === 'patient' && (
                <>
                  <Link to="/book" className="nav-link">
                    Book Appointment
                  </Link>
                  <Link to="/appointments" className="nav-link">
                    My Appointments
                  </Link>
                </>
              )}
              {role === 'doctor' && (
                <Link to="/doctor/dashboard" className="nav-link">
                  Dashboard
                </Link>
              )}
              <span className="nav-user">{user?.name}</span>
              <button className="btn btn-outline btn-sm" onClick={handleLogout}>
                Logout
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
