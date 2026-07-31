-- =====================================================================
--  Doctor Appointment Booking System - sample data (PostgreSQL)
--  =====================================================================
--  Optional: insert demo doctors and patients directly into PostgreSQL.
--  (The backend also seeds this automatically on first startup - see
--  app/seed.py - so you do NOT have to run this file.)
--
--  Run it with:
--      psql -U postgres -d appointment_db -f sample_data.sql
--
--  Demo login passwords:
--      Doctors  -> doctor123
--      Patients -> patient123
--
--  NOTE: The password_hash values below are REAL bcrypt hashes of the
--  passwords above, generated with Python's bcrypt library. bcrypt adds
--  a random salt, so you can even reuse these exact values.
-- =====================================================================

-- ---------- Doctors ----------
INSERT INTO doctors (name, email, phone, specialty, password_hash) VALUES
('Sarah Mitchell', 'smitchell@clinic.com', '555-0101', 'Cardiologist',     '$2b$12$WBj1DEOWGc93SNVmnV/g/eOUm0HXv416WMKRrpqluMD2Dnhwqzb9K'),
('John Carter',    'jcarter@clinic.com',   '555-0102', 'General Physician','$2b$12$WBj1DEOWGc93SNVmnV/g/eOUm0HXv416WMKRrpqluMD2Dnhwqzb9K'),
('Emily Rodriguez','erodriguez@clinic.com','555-0103', 'Dermatologist',    '$2b$12$WBj1DEOWGc93SNVmnV/g/eOUm0HXv416WMKRrpqluMD2Dnhwqzb9K'),
('Michael Chen',   'mchen@clinic.com',     '555-0104', 'Pediatrician',     '$2b$12$WBj1DEOWGc93SNVmnV/g/eOUm0HXv416WMKRrpqluMD2Dnhwqzb9K'),
('Linda Park',     'lpark@clinic.com',     '555-0105', 'Neurologist',      '$2b$12$WBj1DEOWGc93SNVmnV/g/eOUm0HXv416WMKRrpqluMD2Dnhwqzb9K');

-- ---------- Patients ----------
INSERT INTO patients (name, email, phone, password_hash) VALUES
('Alice Johnson', 'alice@example.com', '555-0201', '$2b$12$/GO6NPD07h2re.FpB6WODuZzC7aMSPKSdHY4Qma9xJupnji.x4S/O'),
('Bob Smith',     'bob@example.com',   '555-0202', '$2b$12$/GO6NPD07h2re.FpB6WODuZzC7aMSPKSdHY4Qma9xJupnji.x4S/O'),
('Carol Davis',   'carol@example.com', '555-0203', '$2b$12$/GO6NPD07h2re.FpB6WODuZzC7aMSPKSdHY4Qma9xJupnji.x4S/O');
