# ShifaBook — Complete Guide (INFO.md)

This file is a beginner-friendly walkthrough of the whole **ShifaBook**
project: what it does, how it is built, how the database works, every page
and every API endpoint, plus step-by-step workflows.

> Quick start? See **[README.md](./README.md)**.

---

## 1. What is ShifaBook?

ShifaBook is a **doctor appointment booking platform for Pakistan** with
two very different kinds of users:

| User      | They want to… |
| --------- | ------------- |
| **Patient** | find the right doctor (even by typing a *symptom*), compare fees, see when the doctor is free, and book/reschedule/cancel appointments. |
| **Doctor**  | create a professional profile (PMDC verified), define clinic hours, block days off, set fees, and run their practice from a dashboard with analytics. |

Everything is localised for Pakistan: prices in **PKR (Rs.)**, **12-hour
times**, Pakistani mobile-number validation, Pakistani cities/provinces, and
a **languages** field (English, Urdu, Punjabi, Sindhi, Pashto…).

---

## 2. How to run the project

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv          # first time only
.venv\Scripts\activate        # Windows  (source .venv/bin/activate on Mac/Linux)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- API base: `http://127.0.0.1:8000/api`
- Interactive docs (try every endpoint!): `http://127.0.0.1:8000/docs`

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

- App: `http://localhost:5173/doctor-appointment-booking/`
- The Vite server proxies `/api/*` to the backend, so there is **no CORS** setup.

### Database

- Default is **SQLite** (zero setup). For PostgreSQL set in `backend/.env`:
  ```
  DATABASE_URL=postgresql://postgres:your_password@localhost:5432/appointment_db
  ```
- On first run the backend **creates the tables and seeds demo data**
  automatically (see `seed.py`). You can also run `backend/sql/schema.sql`
  and `backend/sql/sample_data.sql` yourself.

---

## 3. Architecture

```
Browser (React)
   │  fetch("/api/...")  ──proxied by Vite──▶  FastAPI on :8000
   ▼
/api/search/*      → symptom mapping + filters
/api/doctors/*     → profiles, schedule, availability, stats
/api/patients/*    → profile, favourites, stats
/api/appointments  → slots, booking, reschedule, cancel
/api/reviews       → ratings
/api/notifications → in-app alerts
   ▼
SQLAlchemy ORM  ──▶  PostgreSQL / SQLite  (12 tables)
```

- **Backend** validates every request with Pydantic schemas, hashes
  passwords with bcrypt and issues **JWT tokens** that carry the user's
  role (`patient` or `doctor`).
- **Frontend** stores the token in `localStorage`, sends it as
  `Authorization: Bearer …`, and guards routes with `ProtectedRoute`.

### Frontend file layout

| File | Purpose |
| ---- | ------- |
| `src/main.jsx` | Entry point; wraps the app in `AuthProvider`, `ThemeProvider`, `ToastProvider`. |
| `src/App.jsx` | All routes (home, search, doctor profiles, patient & doctor dashboards). |
| `src/api/client.js` | One small `fetch` helper used by every page (adds the token, parses errors). |
| `src/context/` | Auth (login state), Theme (dark mode), Toast (pop-up messages). |
| `src/utils/format.js` | `formatCurrency` (PKR), `formatTime12h`, dates, Pakistani cities. |
| `src/components/` | Reusable UI: Navbar, DashboardLayout, DoctorCard, StarRating, WeeklyChart, Modal, Skeleton, etc. |
| `src/pages/` | Home, Search, `patient/` (dashboard, appointments, favourites, auth) and `doctor/` (dashboard, schedule, profile, auth). |
| `src/styles/styles.css` | The whole design system — CSS variables + `[data-theme="dark"]` palette. |

---

## 4. Database (12 tables)

| Table | Stores |
| ----- | ------ |
| `patients` | name, email, phone, password hash |
| `doctors` | full profile: PMDC number, gender, DOB, experience, qualifications, specialization, clinic/hospital, city, province, languages, biography, fees (first visit / follow-up / online), `booking_enabled`, `is_verified`, `patients_treated` |
| `specializations` | canonical list (Cardiologist, Dentist, …) |
| `symptoms` | 31 symptoms (Tooth Pain, Stomach Pain, …) |
| `symptom_mappings` | which **symptom → specialization** |
| `doctor_schedules` | weekly working hours per doctor: day (0=Mon…6=Sun), start/end, `duration_minutes` (15/20/30/60) |
| `unavailable_dates` | dates the doctor is off (vacation, leave) |
| `blocked_slots` | one specific date+time the doctor blocked |
| `appointments` | doctor, patient, date, time, status, `consultation_fee`, `visit_type` (First/Follow-up) |
| `patient_favorites` | which patient saved which doctor |
| `notifications` | in-app alerts for patients & doctors (`is_read`) |
| `reviews` | patient rating (1–5) + comment for a doctor |

Two important design decisions:

1. **Appointment status** is a native PostgreSQL `enum`
   (`Booked` / `Completed` / `Cancelled`).
2. The `appointments` table has a **partial unique index**
   `uq_doctor_slot_active` on `(doctor_id, appointment_date, appointment_time)`
   that only counts active rows — the **database itself** cannot create a
   double booking, yet a *cancelled* appointment frees its slot for re-booking.

---

## 5. The key feature: symptom-based search

When a patient types a symptom, the backend:

1. Looks it up in the `symptoms` table (fuzzy, `ILIKE`).
2. Follows the `symptom_mappings` to find the target **specialization(s)**.
3. Searches doctors in those specializations (plus a general text search
   over name / hospital / city / qualifications).

Seeded examples:

| Symptom you type | Doctor you get |
| ---------------- | -------------- |
| Tooth Pain       | Dentist (e.g. Dr. Ahmed Raza) |
| Stomach Pain     | Gastroenterologist (Dr. Fatima Khan) |
| Chest Pain       | Cardiologist (Dr. Sarah Mitchell) |
| Skin Rash        | Dermatologist (Dr. Emily Rodriguez) |
| Ear Pain         | ENT Specialist (Dr. Ali Hassan) |
| Eye Infection    | Ophthalmologist (Dr. Nadia Akhtar) |
| Child Specialist | Pediatrician (Dr. Michael Chen) |
| Diabetes         | Endocrinologist (Dr. Mariam Tariq) |
| Pregnancy        | Gynecologist (Dr. Ayesha Malik) |

Search also supports filters (`specialization`, `city`, `min_rating`,
`fee_max`) and sorting (`relevance`, `rating`, `fee_low`, `fee_high`).

---

## 6. Every page

### Public
- **Home** — hero search, popular specialties (with doctor counts),
  top-rated doctors, "how it works", and a CTA for doctors.
- **Search** — advanced filters + sort + live results.
- **Doctor profile** (`/doctors/:id`) — PMDC badge, fees, clinic schedule,
  reviews, and the **booking widget** (date strip → free slots).

### Patient
- **Login / Register** (phone regex `03XX-XXXXXXX` or `+92 3XX…`).
- **Dashboard** — stat cards (total/upcoming/completed/favourites), weekly
  activity chart, upcoming appointments, favourite doctors.
- **My Appointments** — tabs by status, reschedule (new date → slots) and
  cancel (with confirmation modal).
- **Favourites** — saved doctors with one-tap booking.

### Doctor
- **Register** — the big self-registration form (PMDC, DOB, experience,
  languages chips, fees, biography ≥ 20 chars).
- **Dashboard** — today's/upcoming appointments, total patients, revenue,
  monthly figures, weekly chart, booking on/off switch, profile completion.
- **Appointments** — date filter + mark Completed/Cancelled.
- **Schedule** — toggle each weekday, set hours + slot duration, manage
  unavailable dates and blocked slots.
- **Profile** — edit everything with a live "public preview" card.

---

## 7. Main workflows (step by step)

### Patient books an appointment
1. On **Home**, type *"tooth pain"* → lands on **Search** showing dentists.
2. Open **Dr. Ahmed Raza** → see fees, schedule, reviews.
3. Pick a date on the strip → **free slots** appear.
4. Click a slot → confirm toast → appointment saved with the **First visit**
   fee (Rs. 1,500) and status `Booked`.
5. If the same patient books again with the same doctor, the **Follow-up**
   fee (Rs. 1,200) is charged instead.
6. The doctor gets an in-app notification; the patient sees the appointment
   in **My Appointments** and the dashboard.

### Doctor manages availability
1. In **Schedule**, turn on Monday–Friday, set 09:00–17:00, 30-min slots → **Save**.
2. Mark next Thursday **unavailable** (reason: "Conference") → patients no
   longer see that date.
3. Block Wednesday 12:00 → that exact slot disappears from the booking UI.
4. Toggle **online booking off** → profile shows *"Online booking is
   currently off"* and `/api/slots` returns `is_available: false`.

### Doctor completes a visit
1. In **Appointments**, click **Complete** on a `Booked` row.
2. Status becomes `Completed`; the fee moves into **revenue**;
   `patients_treated` increments; the patient gets a notification.

---

## 8. Key API examples

### Search with symptom mapping
```
GET /api/search/doctors?q=Tooth%20Pain&city=Lahore&sort=rating
```
```json
[
  {
    "id": 6,
    "name": "Dr. Ahmed Raza",
    "specialization": "Dentist",
    "city": "Lahore",
    "first_visit_fee": 1500,
    "followup_fee": 1200,
    "rating_avg": 5.0,
    "rating_count": 3,
    "is_favorite": false,
    "booking_enabled": true
  }
]
```

### Get free slots
```
GET /api/slots?doctor_id=6&appointment_date=2026-08-06
```
```json
{
  "doctor_id": 6,
  "appointment_date": "2026-08-06",
  "is_available": true,
  "message": null,
  "available_slots": ["09:00", "09:30", "10:00", "10:30", "11:00"]
}
```
If the doctor is off that day: `"is_available": false` and a friendly
`message` explains why.

### Book (patient token required)
```
POST /api/appointments
{ "doctor_id": 6, "appointment_date": "2026-08-06", "appointment_time": "10:30" }
```
Returns the appointment with `consultation_fee` and `visit_type` already
computed. Attempts to book a taken slot return
`"This appointment slot is already booked. Please choose another date or time."`

### Doctor dashboard stats (doctor token required)
```
GET /api/doctors/me/stats
```
```json
{
  "today_count": 3,
  "upcoming_count": 5,
  "total_patients": 42,
  "monthly_count": 17,
  "weekly": { "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
              "counts": [2, 4, 0, 3, 1, 0, 0] },
  "total_revenue": 45000,
  "monthly_revenue": 19500,
  "profile_completion": 92
}
```

---

## 9. How fees & revenue work

- `first_visit_fee` is charged for a patient's **first** appointment with a
  doctor; `followup_fee` for later ones. Detected by looking for any
  previous non-cancelled appointment with the same doctor.
- Revenue (`total_revenue` / `monthly_revenue`) only counts **Completed**
  appointments (money actually collected).
- Fees are shown in **PKR** throughout the UI (`formatCurrency`).

---

## 10. How notifications work

Whenever something happens, the backend inserts a row into `notifications`:

- Patient books → notification to the **doctor**.
- Doctor marks Completed/Cancelled → notification to the **patient**.
- The bell icons (top bar / dashboard) poll `/api/notifications` (patients)
  or `/api/notifications/doctor` (doctors) and show an unread badge.

---

## 11. Troubleshooting

| Problem | Fix |
| ------- | --- |
| `connection refused` on port 8000 | Start the backend first (`uvicorn app.main:app --reload` in `backend/`). |
| Frontend can't reach `/api` | Make sure Vite runs and the proxy targets port **8000** in `frontend/vite.config.js`. |
| `Could not validate credentials` | You forgot the `Authorization: Bearer <token>` header. |
| PostgreSQL password error | Update `DATABASE_URL` in `backend/.env` to match your install. |
| Slots show "doctor unavailable" | The day is off, a date is marked unavailable, or `booking_enabled` is false. |
| Old data / weird demo rows | Delete the DB and let `seed.py` recreate it (or rerun `sql/schema.sql` + `sql/sample_data.sql`). |

---

## 12. Ideas to extend it

- **Email/SMS reminders** before an appointment (notification hook exists).
- **Online consultation** — the `online_fee` field is already in the schema;
  wire it into the booking flow and add a video-call room.
- **Payment gateway** (JazzCash / Easypaisa / Stripe) for online booking.
- **Admin panel** for PMDC-verification of newly registered doctors.
- **Email OTP** in place of password-only login.

---

*Built as an academic/demonstration project. Use freely for learning and presentations.*
