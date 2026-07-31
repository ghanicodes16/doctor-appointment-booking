// context/AuthContext.jsx - global login state management.
//
// This is a React Context. It lets any component in the app know:
//   - who is currently logged in (the "user" object)
//   - their role ("patient" or "doctor")
//   - and provides login() / logout() functions.
//
// The login info is saved in localStorage, so if the user refreshes the
// page they stay logged in.
import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  // Initialize state from localStorage (the user's saved session).
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user')
    return saved ? JSON.parse(saved) : null
  })
  const [role, setRole] = useState(() => localStorage.getItem('role') || null)

  /**
   * Save the login response (token + user + role) into state and localStorage.
   */
  const login = (data) => {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    localStorage.setItem('role', data.role)
    setUser(data.user)
    setRole(data.role)
  }

  /**
   * Clear everything when the user logs out.
   */
  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    localStorage.removeItem('role')
    setUser(null)
    setRole(null)
  }

  return (
    <AuthContext.Provider value={{ user, role, isLoggedIn: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// A custom hook so components can easily read the auth state.
export function useAuth() {
  return useContext(AuthContext)
}
