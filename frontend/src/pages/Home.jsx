// pages/Home.jsx - the landing page.
// A hero section introduces the app, then two big cards let the user
// choose between the Patient portal and the Doctor portal.
import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="home">
      {/* Hero section */}
      <section className="hero">
        <div className="hero-inner">
          <span className="hero-badge">Healthcare made simple</span>
          <h1>Book your doctor appointment in seconds</h1>
          <p>
            Find a doctor, choose a date and time, and manage your visits - all from one
            clean, modern application.
          </p>
          <div className="hero-actions">
            <Link to="/login" className="btn btn-primary">
              I am a Patient
            </Link>
            <Link to="/doctor/login" className="btn btn-outline-light">
              I am a Doctor
            </Link>
          </div>
        </div>
      </section>

      {/* Feature cards */}
      <section className="features">
        <div className="feature-card card">
          <div className="feature-icon">&#128197;</div>
          <h3>Online Booking</h3>
          <p>
            Pick a doctor, choose a free time slot and confirm your appointment in just a
            few clicks.
          </p>
        </div>
        <div className="feature-card card">
          <div className="feature-icon">&#128722;</div>
          <h3>Manage Appointments</h3>
          <p>
            View your upcoming and past visits. Reschedule or cancel with a single tap.
          </p>
        </div>
        <div className="feature-card card">
          <div className="feature-icon">&#128737;</div>
          <h3>Doctor Dashboard</h3>
          <p>
            Doctors see all their appointments, filter them by date, and update their
            status.
          </p>
        </div>
      </section>

      {/* Demo credentials card - very handy for presentations */}
      <section className="demo card">
        <h2>Demo accounts</h2>
        <p>Log in with one of these pre-created accounts to explore the app.</p>
        <div className="demo-grid">
          <div>
            <h4>Patients (password: <code>patient123</code>)</h4>
            <ul>
              <li>alice@example.com</li>
              <li>bob@example.com</li>
              <li>carol@example.com</li>
            </ul>
          </div>
          <div>
            <h4>Doctors (password: <code>doctor123</code>)</h4>
            <ul>
              <li>smitchell@clinic.com - Cardiologist</li>
              <li>jcarter@clinic.com - General Physician</li>
              <li>erodriguez@clinic.com - Dermatologist</li>
              <li>mchen@clinic.com - Pediatrician</li>
              <li>lpark@clinic.com - Neurologist</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  )
}
