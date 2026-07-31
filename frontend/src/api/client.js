// api/client.js - a small helper around the browser's fetch() function.
//
// Every API call goes through `apiRequest`, which:
//   1. Adds the Authorization header with the saved JWT token.
//   2. Sends JSON data.
//   3. Parses the JSON response.
//   4. Throws a readable Error if the request failed.
//
// The base URL is "/api", which the Vite dev server proxies to the
// FastAPI backend on port 8000.

const BASE_URL = '/api'

/**
 * Perform a fetch request to the backend.
 *
 * @param {string} path  - API path, e.g. "/appointments"
 * @param {object} options - { method, body } optional
 * @returns {Promise<any>} parsed JSON response
 */
export async function apiRequest(path, { method = 'GET', body } = {}) {
  // Build the headers object.
  const headers = { 'Content-Type': 'application/json' }

  // If we have a saved token, attach it so the backend knows who we are.
  const token = localStorage.getItem('access_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  // Try to parse the response body as JSON.
  let data = null
  try {
    data = await response.json()
  } catch {
    // empty response body - that's fine
  }

  // If the request failed, throw an error with the backend's message.
  if (!response.ok) {
    let message

    if (typeof data?.detail === 'string') {
      // Simple error message, e.g. "Incorrect email or password".
      message = data.detail
    } else if (Array.isArray(data?.detail)) {
      // FastAPI 422 validation error: detail is a list of objects like
      //   [{ loc: ["body","phone"], msg: "String should have at least 7 characters", ... }]
      // Convert them into one readable sentence instead of "[object Object]".
      message = data.detail
        .map((item) => {
          if (typeof item === 'object' && item !== null) {
            // Remove trailing dots so the final joined sentence reads well.
            return String(item.msg || '').replace(/\.+$/, '')
          }
          return String(item)
        })
        .filter(Boolean)
        .join('. ')
    } else if (typeof data === 'string') {
      message = data
    } else {
      message = `Request failed with status ${response.status}`
    }

    const error = new Error(message)
    error.status = response.status
    throw error
  }

  return data
}

// Named helper functions to keep page components clean and readable.
export const getDoctors = () => apiRequest('/doctors')
export const getAvailableSlots = (doctorId, date) =>
  apiRequest(`/slots?doctor_id=${doctorId}&appointment_date=${date}`)

export const patientLogin = (email, password) =>
  apiRequest('/auth/login/patient', { method: 'POST', body: { email, password } })
export const doctorLogin = (email, password) =>
  apiRequest('/auth/login/doctor', { method: 'POST', body: { email, password } })
export const patientRegister = (name, email, phone, password) =>
  apiRequest('/auth/register', { method: 'POST', body: { name, email, phone, password } })

export const getMyAppointments = (upcoming) =>
  apiRequest(upcoming === undefined ? '/appointments' : `/appointments?upcoming=${upcoming}`)
export const bookAppointment = (doctorId, appointmentDate, appointmentTime) =>
  apiRequest('/appointments', {
    method: 'POST',
    body: { doctor_id: doctorId, appointment_date: appointmentDate, appointment_time: appointmentTime },
  })
export const rescheduleAppointment = (id, appointmentDate, appointmentTime) =>
  apiRequest(`/appointments/${id}`, {
    method: 'PATCH',
    body: { appointment_date: appointmentDate, appointment_time: appointmentTime },
  })
export const cancelAppointment = (id) => apiRequest(`/appointments/${id}`, { method: 'DELETE' })

export const getDoctorAppointments = (date) =>
  apiRequest(date ? `/doctors/me/appointments?appointment_date=${date}` : '/doctors/me/appointments')
export const updateAppointmentStatus = (id, status) =>
  apiRequest(`/doctors/me/appointments/${id}/status`, { method: 'PATCH', body: { status } })
