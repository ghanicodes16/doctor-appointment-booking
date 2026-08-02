// utils/format.js - Pakistan-aware formatting helpers (PKR, 12h time, dates).

// Currency: 2500 -> "Rs. 2,500"
export function formatCurrency(amount) {
  if (amount === null || amount === undefined) return 'Rs. 0'
  return `Rs. ${Number(amount).toLocaleString('en-PK')}`
}

// 24h "14:30" -> "02:30 PM", and "09:00" -> "9:00 AM"
export function formatTime12h(time24) {
  if (!time24) return ''
  const [h, m] = time24.split(':').map(Number)
  const period = h >= 12 ? 'PM' : 'AM'
  const hour = h % 12 || 12
  return `${hour}:${String(m).padStart(2, '0')} ${period}`
}

// "2026-08-10" -> "10 Aug 2026"  (day month year)
export function formatDate(isoDate) {
  if (!isoDate) return ''
  const d = new Date(`${isoDate}T00:00:00`)
  if (isNaN(d)) return isoDate
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

// "2026-08-10" -> "Monday, 10 August 2026"
export function formatDateLong(isoDate) {
  if (!isoDate) return ''
  const d = new Date(`${isoDate}T00:00:00`)
  if (isNaN(d)) return isoDate
  return d.toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

// day of week index (0=Mon) -> name
export const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
export const DAY_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

// The next 30 days (used by the booking date picker / calendar).
export function nextDays(count = 14) {
  const days = []
  const today = new Date()
  for (let i = 0; i < count; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() + i)
    const iso = d.toISOString().split('T')[0]
    days.push({ iso, weekday: d.getDay(), name: d.toLocaleDateString('en-GB', { weekday: 'short' }), day: d.getDate(), month: d.toLocaleDateString('en-GB', { month: 'short' }) })
  }
  return days
}

// Pakistani cities + provinces
export const PAK_CITIES = [
  'Lahore', 'Karachi', 'Islamabad', 'Rawalpindi', 'Faisalabad', 'Multan',
  'Peshawar', 'Quetta', 'Sialkot', 'Gujranwala', 'Hyderabad', 'Bahawalpur',
  'Sargodha', 'Abbottabad', 'Sukkur',
]

export const PAK_PROVINCES = ['Punjab', 'Sindh', 'KPK', 'Balochistan', 'ICT', 'Gilgit-Baltistan', 'AJK']

export const GENDERS = ['Male', 'Female', 'Other']
