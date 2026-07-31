// pages/patient/BookAppointment.jsx - the booking page (core patient feature).
//
// Flow:
//   1. Patient picks a doctor from a dropdown.
//   2. Patient picks a date.
//   3. The app asks the backend for the free time slots of that
//      doctor+date and shows them as buttons.
//   4. Patient clicks a slot, sees a summary and clicks "Confirm booking".
//   5. The backend validates the slot again. If it was already booked
//      (e.g. by another patient at the same moment) the exact message
//      "This appointment slot is already booked..." is displayed.
import { useEffect, useState } from 'react'

import {
  bookAppointment,
  getAvailableSlots,
  getDoctors,
} from '../../api/client.js'
import Alert from '../../components/Alert.jsx'
import Spinner from '../../components/Spinner.jsx'

export default function BookAppointment() {
  const [doctors, setDoctors] = useState([])
  const [doctorId, setDoctorId] = useState('')
  const [date, setDate] = useState('')
  const [slots, setSlots] = useState([])
  const [selectedSlot, setSelectedSlot] = useState('')
  const [loadingDoctors, setLoadingDoctors] = useState(true)
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [booking, setBooking] = useState(false)
  const [message, setMessage] = useState(null) // { type: 'success'|'error', text }
  const [selectedDoctor, setSelectedDoctor] = useState(null)

  // Load the list of doctors once when the page opens.
  useEffect(() => {
    getDoctors()
      .then((data) => setDoctors(data))
      .catch((err) => setMessage({ type: 'error', text: err.message }))
      .finally(() => setLoadingDoctors(false))
  }, [])

  // Whenever doctor or date changes, fetch the free slots.
  useEffect(() => {
    if (!doctorId || !date) {
      setSlots([])
      setSelectedSlot('')
      return
    }
    setLoadingSlots(true)
    setSelectedSlot('')
    getAvailableSlots(doctorId, date)
      .then((data) => {
        setSlots(data.available_slots)
        setSelectedDoctor(doctors.find((d) => String(d.id) === String(doctorId)) || null)
      })
      .catch((err) => setMessage({ type: 'error', text: err.message }))
      .finally(() => setLoadingSlots(false))
  }, [doctorId, date, doctors])

  // Today's date in YYYY-MM-DD format (used as the min date on the input).
  const today = new Date().toISOString().split('T')[0]

  // Send the booking request to the backend.
  const handleBook = async () => {
    if (!doctorId || !date || !selectedSlot) return
    setMessage(null)
    setBooking(true)
    try {
      await bookAppointment(doctorId, date, selectedSlot)
      setMessage({ type: 'success', text: 'Your appointment has been booked successfully!' })
      setSelectedSlot('')
      // Refresh the slots so the booked one disappears from the list.
      const data = await getAvailableSlots(doctorId, date)
      setSlots(data.available_slots)
    } catch (err) {
      // If the slot was taken in the meantime, this exact message is shown:
      setMessage({ type: 'error', text: err.message })
      // Refresh the slots so the patient can see the updated availability.
      const data = await getAvailableSlots(doctorId, date)
      setSlots(data.available_slots)
    } finally {
      setBooking(false)
    }
  }

  return (
    <div className="page">
      <h1 className="page-title">Book an Appointment</h1>

      {message && <Alert type={message.type}>{message.text}</Alert>}

      <div className="booking-grid">
        {/* Left card: choose doctor + date */}
        <div className="card">
          <h3>1. Choose doctor and date</h3>

          <label className="field">
            <span>Doctor</span>
            {loadingDoctors ? (
              <Spinner small />
            ) : (
              <select value={doctorId} onChange={(e) => setDoctorId(e.target.value)} required>
                <option value="">-- Select a doctor --</option>
                {doctors.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.specialty})
                  </option>
                ))}
              </select>
            )}
          </label>

          <label className="field">
            <span>Date</span>
            <input
              type="date"
              value={date}
              min={today}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </label>
        </div>

        {/* Right card: pick a free time slot */}
        <div className="card">
          <h3>2. Choose a time slot</h3>

          {!doctorId || !date ? (
            <p className="muted">Select a doctor and a date to see the available time slots.</p>
          ) : loadingSlots ? (
            <Spinner small />
          ) : slots.length === 0 ? (
            <p className="muted">No free slots on this date. Please choose another date.</p>
          ) : (
            <>
              <p className="muted">
                Free slots for {selectedDoctor?.name} on {date}:
              </p>
              <div className="slot-grid">
                {slots.map((slot) => (
                  <button
                    key={slot}
                    type="button"
                    className={`slot ${selectedSlot === slot ? 'slot-selected' : ''}`}
                    onClick={() => setSelectedSlot(slot)}
                  >
                    {slot}
                  </button>
                ))}
              </div>

              {selectedSlot && (
                <div className="booking-summary">
                  <div>
                    <strong>{selectedDoctor?.name}</strong>
                    <div className="muted">
                      {selectedDoctor?.specialty}
                    </div>
                    <div className="muted">
                      {date} at {selectedSlot}
                    </div>
                  </div>
                  <button className="btn btn-primary" onClick={handleBook} disabled={booking}>
                    {booking ? <Spinner small /> : 'Confirm booking'}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
