-- =====================================================================
--  MediBook - Doctor Appointment Booking System (Pakistan edition)
--  PostgreSQL schema
--  =====================================================================
--  Run it against PostgreSQL with:
--      psql -U postgres -d appointment_db -f schema.sql
--
--  Tables:
--      doctors               extended doctor profiles (PMDC, fees, clinic)
--      patients              patient accounts
--      appointments          bookings (doctor + patient + date + time + fee)
--      specializations       canonical medical specializations
--      symptoms              common diseases/symptoms
--      symptom_mappings      symptom -> specialization mapping (smart search)
--      doctor_schedules      weekly working days / hours / duration
--      doctor_unavailable_dates   vacation / emergency / off days
--      blocked_slots         specific blocked time slots
--      patient_favorites     patient bookmarks of doctors
--      notifications         in-app notifications
--      reviews               ratings + comments (future-ready)
--
--  Key business rule: UNIQUE(doctor_id, appointment_date, appointment_time)
--  prevents a doctor from being double-booked at the same time.
-- =====================================================================

-- Status values an appointment can have.
DO $$ BEGIN
    CREATE TYPE appointment_status AS ENUM ('Booked', 'Completed', 'Cancelled');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ---------------------------------------------------------------------
-- 1. doctors
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    id                SERIAL PRIMARY KEY,
    name              VARCHAR(120) NOT NULL,
    email             VARCHAR(120) UNIQUE NOT NULL,
    phone             VARCHAR(20)  NOT NULL,
    password_hash     VARCHAR(255) NOT NULL,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Professional profile
    pmdc_number       VARCHAR(50),
    gender            VARCHAR(20),
    profile_photo     TEXT,
    date_of_birth     DATE,
    years_of_experience INTEGER NOT NULL DEFAULT 0,
    qualifications    TEXT,
    specialization    VARCHAR(120) NOT NULL,
    languages         VARCHAR(200),
    biography         TEXT,

    -- Clinic
    hospital_name     VARCHAR(200),
    clinic_address    VARCHAR(300),
    city              VARCHAR(80),
    province          VARCHAR(50),

    -- Fees (PKR)
    first_visit_fee   INTEGER NOT NULL DEFAULT 0,
    followup_fee      INTEGER NOT NULL DEFAULT 0,
    online_fee        INTEGER NOT NULL DEFAULT 0,

    -- Status
    is_verified       BOOLEAN NOT NULL DEFAULT FALSE,
    booking_enabled   BOOLEAN NOT NULL DEFAULT TRUE,
    patients_treated  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_doctors_specialization ON doctors (specialization);
CREATE INDEX IF NOT EXISTS idx_doctors_city          ON doctors (city);

-- ---------------------------------------------------------------------
-- 2. patients
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(120) NOT NULL,
    email         VARCHAR(120) UNIQUE NOT NULL,
    phone         VARCHAR(20)  NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- 3. appointments
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    id               SERIAL PRIMARY KEY,
    doctor_id        INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    patient_id       INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status           appointment_status NOT NULL DEFAULT 'Booked',
    consultation_fee INTEGER,
    visit_type       VARCHAR(20),
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- THE DOUBLE-BOOKING GUARANTEE.
-- A partial unique index: only active appointments (Booked/Completed)
-- block a slot. Cancelling an appointment frees its time so a patient
-- can re-book it.
CREATE UNIQUE INDEX IF NOT EXISTS uq_doctor_slot_active
    ON appointments (doctor_id, appointment_date, appointment_time)
    WHERE status <> 'Cancelled';

CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date ON appointments (doctor_id, appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_patient     ON appointments (patient_id);

-- ---------------------------------------------------------------------
-- 4. specializations
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS specializations (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(120) UNIQUE NOT NULL,
    keywords TEXT
);

-- ---------------------------------------------------------------------
-- 5. symptoms
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS symptoms (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL
);

-- ---------------------------------------------------------------------
-- 6. symptom_mappings  (symptom -> specialization)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS symptom_mappings (
    id                SERIAL PRIMARY KEY,
    symptom_id        INT NOT NULL REFERENCES symptoms(id) ON DELETE CASCADE,
    specialization_id INT NOT NULL REFERENCES specializations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_symptom_mappings_symptom ON symptom_mappings (symptom_id);

-- ---------------------------------------------------------------------
-- 7. doctor_schedules  (weekly availability)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctor_schedules (
    id                SERIAL PRIMARY KEY,
    doctor_id         INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    day_of_week       INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time        TIME NOT NULL,
    end_time          TIME NOT NULL,
    duration_minutes  INT NOT NULL DEFAULT 30 CHECK (duration_minutes IN (15, 20, 30, 60)),
    is_available      BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_doctor_day UNIQUE (doctor_id, day_of_week)
);

-- ---------------------------------------------------------------------
-- 8. doctor_unavailable_dates  (vacation / emergency / off)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctor_unavailable_dates (
    id        SERIAL PRIMARY KEY,
    doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    date      DATE NOT NULL,
    reason    VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_unavailable_doctor_date
    ON doctor_unavailable_dates (doctor_id, date);

-- ---------------------------------------------------------------------
-- 9. blocked_slots
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS blocked_slots (
    id         SERIAL PRIMARY KEY,
    doctor_id  INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    date       DATE NOT NULL,
    start_time TIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_blocked_doctor_date ON blocked_slots (doctor_id, date);

-- ---------------------------------------------------------------------
-- 10. patient_favorites
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patient_favorites (
    id         SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id  INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_patient_doctor UNIQUE (patient_id, doctor_id)
);

-- ---------------------------------------------------------------------
-- 11. notifications
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id               SERIAL PRIMARY KEY,
    recipient_role   VARCHAR(20) NOT NULL,   -- 'doctor' or 'patient'
    recipient_id     INT NOT NULL,
    message          VARCHAR(300) NOT NULL,
    notification_type VARCHAR(30) NOT NULL DEFAULT 'info',
    is_read          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_recipient
    ON notifications (recipient_role, recipient_id);

-- ---------------------------------------------------------------------
-- 12. reviews  (future-ready)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    id         SERIAL PRIMARY KEY,
    doctor_id  INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    rating     INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment    TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reviews_doctor ON reviews (doctor_id);
