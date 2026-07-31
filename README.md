# MediBook - Doctor Appointment Booking System

A full-stack web application that lets **patients** book doctor appointments online and lets **doctors** manage those appointments from their own dashboard.

- **Frontend:** React.js (Vite), React Router, Material-Design-inspired CSS
- **Backend:** Python + FastAPI (REST API)
- **Database:** PostgreSQL (SQLite fallback for a zero-setup demo)

> 📖 **For a complete, beginner-friendly explanation of the whole project**
> (architecture, database, every endpoint, every page, step-by-step
> workflows, and a presentation guide) read the **[INFO.md](./INFO.md)** file.

---

## Features

**Patient side**

- Register and log in
- Book an appointment by picking a doctor, date and free time slot
- Clear error message if a slot is already booked:
  *"This appointment slot is already booked. Please choose another date or time."*
- View upcoming / previous appointments (tabs)
- Reschedule and cancel booked appointments

**Doctor side**

- Secure doctor login (JWT, role-based access)
- Dashboard with statistics (booked / completed / cancelled)
- Table of all appointments with patient name, patient ID, phone, date, time, status
- Filter appointments by date
- Mark appointments as **Completed** or **Cancelled**

---

## Tech Stack

| Layer      | Technology                                          |
| ---------- | --------------------------------------------------- |
| Frontend   | React 18, Vite, React Router 6                       |
| Backend    | Python 3, FastAPI, SQLAlchemy ORM                    |
| Database   | PostgreSQL (or SQLite for a quick demo)              |
| Auth       | JWT (PyJWT) + bcrypt password hashing                |
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
│   │   ├── models.py         # SQLAlchemy table models
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── security.py       # Password hashing + JWT helpers
│   │   ├── deps.py           # Auth dependencies (role checks)
│   │   ├── seed.py           # Creates tables + demo data
│   │   └── routers/          # API endpoint groups
│   │       ├── auth.py       # register / patient login / doctor login
│   │       ├── doctors.py    # doctor list + dashboard endpoints
│   │       ├── patients.py   # patient profile endpoint
│   │       └── appointments.py  # booking / slots / reschedule / cancel
│   ├── sql/
│   │   ├── schema.sql        # PostgreSQL table creation script
│   │   └── sample_data.sql   # Optional demo data for PostgreSQL
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Example environment file
│   └── .env                  # Local settings (SQLite by default)
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── main.jsx          # React entry point
│   │   ├── App.jsx           # Route definitions
│   │   ├── api/client.js     # fetch() helper for all API calls
│   │   ├── context/AuthContext.jsx  # global login state
│   │   ├── components/       # Navbar, ProtectedRoute, Spinner, Alert, ...
│   │   ├── pages/            # Home, patient/ and doctor/ pages
│   │   └── styles/styles.css # all styling (Material-inspired)
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
4. Create the tables and demo data (optional - the backend also does this automatically):
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

The app opens at **http://127.0.0.1:5173**.

> The Vite dev server automatically forwards `/api/*` requests to the
> backend on port 8000, so no CORS configuration is needed.

### 4. Windows one-click start

If you are on Windows you can double-click:

- **`start_backend.bat`** - installs dependencies (first time) and starts the API
- **`start_frontend.bat`** - installs dependencies (first time) and starts the React app

---

## Demo Accounts

| Role    | Email                | Password    |
| ------- | -------------------- | ----------- |
| Patient | `alice@example.com`  | `patient123` |
| Patient | `bob@example.com`    | `patient123` |
| Patient | `carol@example.com`  | `patient123` |
| Doctor  | `smitchell@clinic.com` | `doctor123` |
| Doctor  | `jcarter@clinic.com` | `doctor123` |
| Doctor  | `erodriguez@clinic.com` | `doctor123` |
| Doctor  | `mchen@clinic.com`   | `doctor123` |
| Doctor  | `lpark@clinic.com`   | `doctor123` |

---

## REST API Overview

| Method | Endpoint                                  | Who        | Description                              |
| ------ | ----------------------------------------- | ---------- | ---------------------------------------- |
| POST   | `/api/auth/register`                      | public     | Register a new patient (returns a token) |
| POST   | `/api/auth/login/patient`                 | public     | Patient login (returns a token)          |
| POST   | `/api/auth/login/doctor`                  | public     | Doctor login (returns a token)           |
| GET    | `/api/doctors`                            | public     | List all doctors                         |
| GET    | `/api/doctors/{id}`                       | public     | Doctor details                           |
| GET    | `/api/doctors/me`                         | doctor     | Current doctor's profile                 |
| GET    | `/api/doctors/me/appointments?date=`      | doctor     | Doctor's appointments (date filter)      |
| PATCH  | `/api/doctors/me/appointments/{id}/status`| doctor     | Mark Completed / Cancelled               |
| GET    | `/api/patients/me`                        | patient    | Current patient's profile                |
| GET    | `/api/slots?doctor_id=&appointment_date=` | public     | Free time slots for a doctor+date        |
| POST   | `/api/appointments`                       | patient    | Book an appointment                      |
| GET    | `/api/appointments?upcoming=`             | patient    | The patient's appointments               |
| PATCH  | `/api/appointments/{id}`                  | patient    | Reschedule an appointment                |
| DELETE | `/api/appointments/{id}`                  | patient    | Cancel an appointment                    |

---

## How Double Booking Is Prevented

The backend checks availability **twice**:

1. **Application level** - before saving, it queries for an existing
   appointment with the same doctor, date and time. If one exists, the
   patient gets a clear error message.
2. **Database level** - the `appointments` table has a
   `UNIQUE (doctor_id, appointment_date, appointment_time)` constraint,
   so even simultaneous requests cannot create duplicates.

---

## License

This project was built as an academic/demonstration project. Use it freely for learning and presentations.
