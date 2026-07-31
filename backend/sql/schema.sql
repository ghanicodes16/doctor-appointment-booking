-- =====================================================================
--  Doctor Appointment Booking System - PostgreSQL schema
--  =====================================================================
--  This file creates all three database tables from scratch.
--
--  Run it against PostgreSQL with:
--      psql -U postgres -d appointment_db -f schema.sql
--
--  Tables created:
--      1. doctors       - doctor accounts (created by the admin/seed)
--      2. patients      - patient accounts (self-registration)
--      3. appointments  - bookings linking a doctor, patient, date, time
--
--  The most important part is the UNIQUE constraint on appointments
--  (doctor_id, appointment_date, appointment_time) which prevents a
--  doctor from being double-booked at the same time.
-- =====================================================================

-- Optionally create the database first (run separately if needed):
--   CREATE DATABASE appointment_db;

-- ---------------------------------------------------------------------
-- Status values that an appointment can have.
-- PostgreSQL ENUM types keep the allowed values enforced at DB level.
-- ---------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE appointment_status AS ENUM ('Booked', 'Completed', 'Cancelled');
EXCEPTION
    WHEN duplicate_object THEN NULL; -- type already exists, do nothing
END $$;

-- ---------------------------------------------------------------------
-- 1. doctors table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    id            SERIAL PRIMARY KEY,        -- unique id, auto-increment
    name          VARCHAR(100) NOT NULL,     -- full name of the doctor
    email         VARCHAR(100) UNIQUE NOT NULL,  -- login email, must be unique
    phone         VARCHAR(20)  NOT NULL,     -- contact phone number
    specialty     VARCHAR(100) NOT NULL,     -- e.g. 'Cardiologist'
    password_hash VARCHAR(255) NOT NULL,     -- bcrypt hash, never plain text
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()  -- account creation time
);

-- ---------------------------------------------------------------------
-- 2. patients table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id            SERIAL PRIMARY KEY,        -- unique id, auto-increment
    name          VARCHAR(100) NOT NULL,     -- full name of the patient
    email         VARCHAR(100) UNIQUE NOT NULL,  -- login email, must be unique
    phone         VARCHAR(20)  NOT NULL,     -- contact phone number
    password_hash VARCHAR(255) NOT NULL,     -- bcrypt hash, never plain text
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()  -- account creation time
);

-- ---------------------------------------------------------------------
-- 3. appointments table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    id               SERIAL PRIMARY KEY,     -- unique appointment id
    doctor_id        INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    patient_id       INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    appointment_date DATE NOT NULL,          -- which day (e.g. 2026-08-10)
    appointment_time TIME NOT NULL,          -- which time (e.g. 09:30)
    status           appointment_status NOT NULL DEFAULT 'Booked',
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),  -- when the booking was made

    -- THE DOUBLE-BOOKING GUARANTEE -------------------------------------
    -- No two appointments may exist for the same doctor on the same
    -- date at the same time. The database itself enforces this, even if
    -- two patients click "Book" at the exact same moment.
    CONSTRAINT uq_doctor_slot UNIQUE (doctor_id, appointment_date, appointment_time)
);

-- ---------------------------------------------------------------------
-- Indexes to make common queries fast.
-- ---------------------------------------------------------------------
-- Doctors' appointments on a specific date (used by the dashboard).
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date
    ON appointments (doctor_id, appointment_date);

-- A patient's list of appointments.
CREATE INDEX IF NOT EXISTS idx_appointments_patient
    ON appointments (patient_id);
