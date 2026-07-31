// components/ProtectedRoute.jsx - route guard.
//
// This component wraps pages that need a login. If the user is not
// logged in (or logged in as the wrong role) they are redirected.
// This is how we implement role-based access control on the frontend.
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function ProtectedRoute({ children, requiredRole }) {
  const { isLoggedIn, role } = useAuth()

  // Not logged in -> send to the matching login page.
  if (!isLoggedIn) {
    return <Navigate to={requiredRole === 'doctor' ? '/doctor/login' : '/login'} replace />
  }

  // Logged in but as the wrong role -> send to the user's home.
  if (requiredRole && role !== requiredRole) {
    return <Navigate to={role === 'doctor' ? '/doctor/dashboard' : '/appointments'} replace />
  }

  // All good - render the protected page.
  return children
}
