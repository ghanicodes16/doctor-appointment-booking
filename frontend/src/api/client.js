// api/client.js - the single helper for every backend call.
//
// It adds the JWT token, sends JSON, parses the response and throws a
// readable Error (handles FastAPI 422 validation arrays correctly).

const BASE_URL = '/api'

export async function apiRequest(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' }

  const token = localStorage.getItem('access_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  let data = null
  try {
    data = await response.json()
  } catch {
    // empty body
  }

  if (!response.ok) {
    let message
    if (typeof data?.detail === 'string') {
      message = data.detail
    } else if (Array.isArray(data?.detail)) {
      message = data.detail
        .map((item) => {
          if (typeof item === 'object' && item !== null) {
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

// ------------------------- Authentication -------------------------
export const patientLogin = (email, password) =>
  apiRequest('/auth/login/patient', { method: 'POST', body: { email, password } })
export const doctorLogin = (email, password) =>
  apiRequest('/auth/login/doctor', { method: 'POST', body: { email, password } })
export const patientRegister = (name, email, phone, password) =>
  apiRequest('/auth/register', { method: 'POST', body: { name, email, phone, password } })
export const doctorRegister = (payload) =>
  apiRequest('/auth/register/doctor', { method: 'POST', body: payload })

// ------------------------- Doctors -------------------------
export const getDoctors = () => apiRequest('/doctors')
export const getDoctor = (id) => apiRequest(`/doctors/${id}`)
export const getDoctorSchedule = (id) => apiRequest(`/doctors/${id}/schedule`)
export const getMyDoctorProfile = () => apiRequest('/doctors/me')
export const updateMyDoctorProfile = (payload) =>
  apiRequest('/doctors/me', { method: 'PATCH', body: payload })
export const setBookingEnabled = (value) =>
  apiRequest('/doctors/me/booking', { method: 'PATCH', body: { booking_enabled: value } })

// ------------------------- Availability -------------------------
export const getMySchedule = () => apiRequest('/doctors/me/schedule')
export const saveSchedule = (schedule) =>
  apiRequest('/doctors/me/schedule', { method: 'PUT', body: { schedule } })
export const getUnavailableDates = () => apiRequest('/doctors/me/unavailable-dates')
export const addUnavailableDate = (date, reason) =>
  apiRequest('/doctors/me/unavailable-dates', { method: 'POST', body: { date, reason } })
export const deleteUnavailableDate = (id) =>
  apiRequest(`/doctors/me/unavailable-dates/${id}`, { method: 'DELETE' })
export const getBlockedSlots = () => apiRequest('/doctors/me/blocked-slots')
export const addBlockedSlot = (date, start_time) =>
  apiRequest('/doctors/me/blocked-slots', { method: 'POST', body: { date, start_time } })
export const deleteBlockedSlot = (id) =>
  apiRequest(`/doctors/me/blocked-slots/${id}`, { method: 'DELETE' })

// ------------------------- Search -------------------------
export const searchDoctors = (params) => {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') qs.set(key, value)
  })
  return apiRequest(`/search/doctors?${qs.toString()}`)
}
export const getSpecializations = () => apiRequest('/search/specializations')
export const getSymptoms = (q) => apiRequest(`/search/symptoms${q ? `?q=${encodeURIComponent(q)}` : ''}`)
export const getRecommendations = () => apiRequest('/search/recommendations')

// ------------------------- Slots & Appointments -------------------------
export const getAvailableSlots = (doctorId, date) =>
  apiRequest(`/slots?doctor_id=${doctorId}&appointment_date=${date}`)

export const bookAppointment = (doctorId, appointmentDate, appointmentTime) =>
  apiRequest('/appointments', {
    method: 'POST',
    body: { doctor_id: doctorId, appointment_date: appointmentDate, appointment_time: appointmentTime },
  })
export const getMyAppointments = (upcoming) =>
  apiRequest(upcoming === undefined ? '/appointments' : `/appointments?upcoming=${upcoming}`)
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

// ------------------------- Dashboard stats -------------------------
export const getDoctorStats = () => apiRequest('/doctors/me/stats')
export const getPatientStats = () => apiRequest('/patients/me/stats')

// ------------------------- Favorites -------------------------
export const getFavorites = () => apiRequest('/patients/me/favorites')
export const addFavorite = (doctorId) =>
  apiRequest(`/patients/me/favorites/${doctorId}`, { method: 'POST' })
export const removeFavorite = (doctorId) =>
  apiRequest(`/patients/me/favorites/${doctorId}`, { method: 'DELETE' })

// ------------------------- Notifications -------------------------
export const getMyNotifications = () => apiRequest('/notifications')
export const getDoctorNotifications = () => apiRequest('/notifications/doctor')
export const markNotificationRead = (id) => apiRequest(`/notifications/${id}/read`, { method: 'PATCH' })
export const markDoctorNotificationRead = (id) =>
  apiRequest(`/notifications/doctor/${id}/read`, { method: 'PATCH' })

// ------------------------- Reviews -------------------------
export const getDoctorReviews = (doctorId) => apiRequest(`/reviews?doctor_id=${doctorId}`)
export const addReview = (doctorId, rating, comment) =>
  apiRequest(`/reviews?doctor_id=${doctorId}`, { method: 'POST', body: { rating, comment } })
