// App.jsx - defines the routes (URLs) of the application.
//
// Routing table:
//   /                  -> Home (landing page)
//   /login             -> patient login
//   /register          -> patient registration
//   /book              -> patient: book an appointment   (patient only)
//   /appointments      -> patient: my appointments       (patient only)
//   /doctor/login      -> doctor login
//   /doctor/dashboard  -> doctor: dashboard              (doctor only)
import { Navigate, Route, Routes } from 'react-router-dom'

import Navbar from './components/Navbar.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Home from './pages/Home.jsx'
import PatientLogin from './pages/patient/PatientLogin.jsx'
import PatientRegister from './pages/patient/PatientRegister.jsx'
import BookAppointment from './pages/patient/BookAppointment.jsx'
import MyAppointments from './pages/patient/MyAppointments.jsx'
import DoctorLogin from './pages/doctor/DoctorLogin.jsx'
import DoctorDashboard from './pages/doctor/DoctorDashboard.jsx'

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />

          {/* Patient authentication */}
          <Route path="/login" element={<PatientLogin />} />
          <Route path="/register" element={<PatientRegister />} />

          {/* Patient pages (protected) */}
          <Route
            path="/book"
            element={
              <ProtectedRoute requiredRole="patient">
                <BookAppointment />
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

          {/* Doctor authentication and dashboard (protected) */}
          <Route path="/doctor/login" element={<DoctorLogin />} />
          <Route
            path="/doctor/dashboard"
            element={
              <ProtectedRoute requiredRole="doctor">
                <DoctorDashboard />
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
