// App.jsx - defines the routes (URLs) of the application.
//
// Routing table:
//   /                  -> Home (landing page)
//   /search            -> advanced doctor search
//   /doctors/:id       -> public doctor profile + booking
//   /login, /register  -> patient auth
//   /dashboard         -> patient dashboard (patient only)
//   /appointments      -> patient appointments (patient only)
//   /favorites         -> patient favourites (patient only)
//   /doctor/login      -> doctor login
//   /doctor/register   -> doctor registration
//   /doctor/dashboard  -> doctor dashboard (doctor only)
//   /doctor/appointments, /doctor/schedule, /doctor/profile
import { Navigate, Route, Routes } from 'react-router-dom'

import Navbar from './components/Navbar.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Home from './pages/Home.jsx'
import Search from './pages/Search.jsx'
import DoctorProfile from './pages/DoctorProfile.jsx'
import PatientLogin from './pages/patient/Login.jsx'
import PatientRegister from './pages/patient/Register.jsx'
import PatientDashboard from './pages/patient/Dashboard.jsx'
import MyAppointments from './pages/patient/Appointments.jsx'
import Favorites from './pages/patient/Favorites.jsx'
import DoctorLogin from './pages/doctor/Login.jsx'
import DoctorRegister from './pages/doctor/Register.jsx'
import DoctorDashboard from './pages/doctor/Dashboard.jsx'
import DoctorAppointments from './pages/doctor/Appointments.jsx'
import DoctorSchedule from './pages/doctor/Schedule.jsx'
import DoctorProfileEdit from './pages/doctor/Profile.jsx'

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />

          {/* Public */}
          <Route path="/search" element={<Search />} />
          <Route path="/doctors/:id" element={<DoctorProfile />} />

          {/* Patient authentication */}
          <Route path="/login" element={<PatientLogin />} />
          <Route path="/register" element={<PatientRegister />} />

          {/* Patient pages (protected) */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute requiredRole="patient">
                <PatientDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/appointments"
            element={
              <ProtectedRoute requiredRole="patient">
                <MyAppointments />
              </ProtectedRoute>
            }
          />
          <Route
            path="/favorites"
            element={
              <ProtectedRoute requiredRole="patient">
                <Favorites />
              </ProtectedRoute>
            }
          />

          {/* Doctor authentication */}
          <Route path="/doctor/login" element={<DoctorLogin />} />
          <Route path="/doctor/register" element={<DoctorRegister />} />

          {/* Doctor pages (protected) */}
          <Route
            path="/doctor/dashboard"
            element={
              <ProtectedRoute requiredRole="doctor">
                <DoctorDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/doctor/appointments"
            element={
              <ProtectedRoute requiredRole="doctor">
                <DoctorAppointments />
              </ProtectedRoute>
            }
          />
          <Route
            path="/doctor/schedule"
            element={
              <ProtectedRoute requiredRole="doctor">
                <DoctorSchedule />
              </ProtectedRoute>
            }
          />
          <Route
            path="/doctor/profile"
            element={
              <ProtectedRoute requiredRole="doctor">
                <DoctorProfileEdit />
              </ProtectedRoute>
            }
          />

          {/* Any unknown URL -> home page */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
