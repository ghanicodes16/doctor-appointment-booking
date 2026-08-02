# ShifaBook - Doctor Appointment Booking System (Pakistan)

A full-stack **Pakistan healthcare platform** that lets **patients** find the
right doctor (even by symptom), compare consultation fees, check live
availability and book appointments online — and lets **doctors**
self-register with PMDC credentials, manage their own schedule, fees and
appointments from a rich dashboard.

- **Frontend:** React 18 (Vite), React Router 6, custom CSS design system
  with light/dark mode, toasts, skeletons and SVG charts
- **Backend:** Python + FastAPI (REST API, auto-documented at `/docs`)
- **Database:** PostgreSQL (SQLite fallback for a zero-setup demo)

> 📖 **For a complete, beginner-friendly explanation of the whole project**
> (architecture, database, every endpoint, every page, step-by-step
> workflows, and a presentation guide) read the **[INFO.md](./INFO.md)** file.

---

## Features

**Patient side**

- Register / log in (Pakistani phone validation, PKR, 12-hour times)
- **Symptom-based doctor search** — type *"tooth pain"* and get dentists,
  *"chest pain"* → cardiologists, etc. (31 mapped symptoms)
- Advanced filters: specialty, city, minimum rating, max fee; sort by
  rating / fee
- Public doctor profiles with PMDC badge, fees (first visit / follow-up),
  clinic schedule and patient reviews
- Live time-slot picker that respects working hours, custom slot durations,
  **unavailable dates**, **blocked slots** and already-booked slots
- Book / reschedule / cancel appointments; automatic **fee capture**
  (first visit vs follow-up)
- Patient dashboard: stats, weekly activity chart, upcoming appointments
- Favorite doctors, in-app notifications, star-rating reviews

**Doctor side**

- **Self-registration** with PMDC number, gender, DOB, experience,
  qualifications, clinic details, languages (English/Urdu/Punjabi/Sindhi…)
- Profile editing with live "public preview"
- **Availability manager**: weekly schedule (per-day hours + slot duration),
  unavailable dates, blocked slots, and an online-booking on/off switch
- Dashboard analytics: today's/upcoming appointments, total patients,
  revenue (completed-only), monthly figures, weekly chart and a profile
  completion meter
- Appointment queue with date filter; mark appointments Completed/Cancelled
  (patients are notified instantly)

---

## Tech Stack

| Layer      | Technology                                          |
| ---------- | --------------------------------------------------- |
| Frontend   | React 18, Vite, React Router 6, custom CSS + SVG    |
| Backend    | Python 3, FastAPI, SQLAlchemy ORM                   |
| Database   | PostgreSQL (or SQLite for a quick demo)             |
| Auth       | JWT (PyJWT) + bcrypt password hashing               |
| API        | REST (auto-documented at `http://127.0.0.1:8000/docs`) |

---

## Project Structure

```
doctor-appointment-booking/
├── backend/                  # Python FastAPI backend
│   ├── app/
│   │   ├── main.py           # FastAPI entry point + router registration
│   │   ├── config.py         # Reads settings from .env
│   │   ├── database.py       # Database connection + session
│   │   ├── models.py         # SQLAlchemy models (12 tables)
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── security.py       # Password hashing + JWT helpers
│   │   ├── deps.py           # Auth dependencies (role checks)
│   │   ├── utils.py          # Shared helpers (rating, notifications, times)
│   │   ├── seed.py           # Creates tables + demo data
│   │   └── routers/          # API endpoint groups
│   │       ├── auth.py       # patient/doctor register + login
│   │       ├── doctors.py    # profiles, schedule, availability, stats
│   │       ├── patients.py   # patient profile, favorites, stats
│   │       ├── appointments.py  # slots / booking / reschedule / cancel
│   │       ├── search.py     # symptom-mapped search + catalog
│   │       ├── reviews.py    # doctor reviews
│   │       └── notifications.py # in-app notifications
│   ├── sql/
│   │   ├── schema.sql        # PostgreSQL DDL (12 tables)
│   │   └── sample_data.sql   # Optional demo data
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Example environment file
│   └── .env                  # Local settings
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── main.jsx          # Entry point (Theme/Toast/Auth providers)
│   │   ├── App.jsx           # Route definitions
│   │   ├── api/client.js     # fetch() helper for all API calls
│   │   ├── context/          # Auth, Theme (dark mode), Toast contexts
│   │   ├── utils/format.js   # PKR, 12h time, date + Pakistan helpers
│   │   ├── components/       # Navbar, dashboards, cards, chart, modal, ...
│   │   ├── pages/            # Home, Search, patient/ and doctor/ pages
│   │   └── styles/styles.css # design system (light/dark themes)
│   ├── package.json
│   └── vite.config.js        # dev server + /api proxy
├── start_backend.bat         # Windows: start the backend
├── start_frontend.bat        # Windows: start the frontend
├── README.md
└── INFO.md                   # Full beginner-friendly documentation
```

---

## Installation

### 1. Install PostgreSQL (recommended)

1. Download PostgreSQL from <https://www.postgresql.org/download/> and install it.
2. Remember the password you set for the `postgres` superuser.
3. Create the database. Open `psql` (or pgAdmin) and run:
   ```sql
   CREATE DATABASE appointment_db;
   ```
4. Create the tables and demo data (optional — the backend also does this automatically):
   ```bash
   cd backend
   psql -U postgres -d appointment_db -f sql/schema.sql
   psql -U postgres -d appointment_db -f sql/sample_data.sql
   ```

> **No PostgreSQL? No problem.** The backend defaults to SQLite and works
> out of the box for demonstrations. Just skip this section.

### 2. Backend setup

```bash
cd backend

# (recommended) create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

# install dependencies
pip install -r requirements.txt

# configure the database (optional)
#   copy .env.example to .env and set DATABASE_URL to your PostgreSQL URL
#   example: DATABASE_URL=postgresql://postgres:your_password@localhost:5432/appointment_db

# start the API
uvicorn app.main:app --reload
```

The API is now running at **http://127.0.0.1:8000** (interactive docs at `/docs`).

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The app opens at **http://localhost:5173/doctor-appointment-booking/**.

> The Vite dev server automatically forwards `/api/*` requests to the
> backend on port 8000, so no CORS configuration is needed.

### 4. Windows one-click start

If you are on Windows you can double-click:

- **`start_backend.bat`** — installs dependencies (first time) and starts the API
- **`start_frontend.bat`** — installs dependencies (first time) and starts the React app

---

## Demo Accounts

| Role    | Email                | Password     |
| ------- | -------------------- | ------------ |
| Patient | `alice@example.com`  | `patient123` |
| Patient | `bob@example.com`    | `patient123` |
| Patient | `carol@example.com`  | `patient123` |
| Doctor  | `smitchell@clinic.com` | `doctor123` |
| Doctor  | `jcarter@clinic.com` | `doctor123` |
| Doctor  | `erodriguez@clinic.com` | `doctor123` |
| Doctor  | `mchen@clinic.com`   | `doctor123` |
| Doctor  | `lpark@clinic.com`   | `doctor123` |
| Doctor  | `araza@clinic.com`   | `doctor123` |
| Doctor  | `fkhan@clinic.com`   | `doctor123` |

...and 5 more doctors (`ahassan@clinic.com`, `amalik@clinic.com`,
`isheikh@clinic.com`, `mtariq@clinic.com`, `uchaudhry@clinic.com`,
`nakhtar@clinic.com`, `kali@clinic.com`, `sbatool@clinic.com`) — all `doctor123`.

---

## REST API Overview

### Auth & patients

| Method | Endpoint                                 | Who     | Description                              |
| ------ | ---------------------------------------- | ------- | ---------------------------------------- |
| POST   | `/api/auth/register`                     | public  | Register a patient (returns a token)     |
| POST   | `/api/auth/register/doctor`              | public  | Doctor self-registration (PMDC, fees…)   |
| POST   | `/api/auth/login/patient`                | public  | Patient login                            |
| POST   | `/api/auth/login/doctor`                 | public  | Doctor login                             |
| GET    | `/api/patients/me`                       | patient | Patient profile                          |
| GET    | `/api/patients/me/stats`                 | patient | Dashboard numbers                        |
| GET    | `/api/patients/me/favorites`             | patient | Favorite doctors                         |
| POST   | `/api/patients/me/favorites/{doctor_id}` | patient | Add a favorite                           |
| DELETE | `/api/patients/me/favorites/{doctor_id}` | patient | Remove a favorite                        |

### Search & catalog

| Method | Endpoint                      | Who    | Description                                   |
| ------ | ----------------------------- | ------ | --------------------------------------------- |
| GET    | `/api/search/doctors`         | public | Symptom-mapped search + filters + sort        |
| GET    | `/api/search/specializations` | public | Specializations (with doctor counts)          |
| GET    | `/api/search/symptoms`        | public | Symptom autocomplete                          |
| GET    | `/api/search/recommendations` | public | Popular specializations for the homepage      |

### Doctors (public + doctor-only)

| Method | Endpoint                                  | Who    | Description                          |
| ------ | ----------------------------------------- | ------ | ------------------------------------ |
| GET    | `/api/doctors`                            | public | List all doctors                     |
| GET    | `/api/doctors/{id}`                       | public | Doctor public profile                |
| GET    | `/api/doctors/{id}/schedule`              | public | Weekly schedule (for booking UI)     |
| GET    | `/api/doctors/me`                         | doctor | Own profile                          |
| PATCH  | `/api/doctors/me`                         | doctor | Update profile + fees                |
| GET/PUT| `/api/doctors/me/schedule`                | doctor | Weekly working hours                 |
| GET/POST/DELETE | `/api/doctors/me/unavailable-dates`       | doctor | Vacations / leave                    |
| GET/POST/DELETE | `/api/doctors/me/blocked-slots`           | doctor | Block specific slots                 |
| PATCH  | `/api/doctors/me/booking`                 | doctor | Enable/disable online booking        |
| GET    | `/api/doctors/me/stats`                   | doctor | Dashboard analytics + weekly chart   |
| GET    | `/api/doctors/me/appointments`            | doctor | Appointments (optional date filter)  |
| PATCH  | `/api/doctors/me/appointments/{id}/status`| doctor | Mark Completed / Cancelled           |

### Appointments & reviews & notifications

| Method | Endpoint                       | Who     | Description                             |
| ------ | ------------------------------ | ------- | --------------------------------------- |
| GET    | `/api/slots?doctor_id=&appointment_date=` | public | Free slots for a doctor + date   |
| POST   | `/api/appointments`            | patient | Book (fee captured automatically)       |
| GET    | `/api/appointments?upcoming=`  | patient | Patient's appointments                  |
| PATCH  | `/api/appointments/{id}`       | patient | Reschedule                              |
| DELETE | `/api/appointments/{id}`       | patient | Cancel                                  |
| GET    | `/api/reviews?doctor_id=`      | public  | A doctor's reviews                      |
| POST   | `/api/reviews?doctor_id=`      | patient | Write a review (rating 1–5)             |
| GET    | `/api/notifications`           | patient | Patient notifications                   |
| GET    | `/api/notifications/doctor`    | doctor  | Doctor notifications                    |
| PATCH  | `/api/notifications/{id}/read` | patient | Mark notification read                  |
| PATCH  | `/api/notifications/doctor/{id}/read` | doctor | Mark notification read            |

---

## How Double Booking Is Prevented

The backend checks availability **twice**:

1. **Application level** — before saving, it rebuilds the slot list for the
   doctor+date (removing blocked slots, unavailable dates and already-booked
   times) and rejects any time that is not in that list.
2. **Database level** — a **partial unique index**
   `uq_doctor_slot_active` on `(doctor_id, appointment_date,
   appointment_time)` prevents two *active* appointments on the same slot,
   so even simultaneous requests cannot create duplicates — while a
   **cancelled** appointment frees its time for re-booking.

A patient booking for the *second* time with the same doctor is
automatically charged the **follow-up fee** instead of the first-visit fee.

---

## License

This project was built as an academic/demonstration project. Use it freely for learning and presentations.
