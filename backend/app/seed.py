"""
seed.py - Sample data for the project (Pakistan healthcare version).

This script fills the database with:
    - canonical specializations and symptom-to-specialization mappings
    - demo doctors with full profiles, fees and weekly schedules
    - demo patients, sample appointments and reviews
    - sample notifications

It runs automatically on backend startup but only seeds tables that are
empty (so it is safe to run many times).

Demo login credentials:

    DOCTORS (password: doctor123)
      smitchell@clinic.com  -> Dr. Sarah Mitchell   (Cardiologist, Lahore)
      jcarter@clinic.com    -> Dr. John Carter      (General Physician, Karachi)
      erodriguez@clinic.com -> Dr. Emily Rodriguez  (Dermatologist, Islamabad)
      mchen@clinic.com      -> Dr. Michael Chen     (Pediatrician, Lahore)
      lpark@clinic.com      -> Dr. Linda Park       (Neurologist, Karachi)

    PATIENTS (password: patient123)
      alice@example.com     -> Alice Johnson
      bob@example.com       -> Bob Smith
      carol@example.com     -> Carol Davis
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal, engine
from .security import hash_password

DOCTOR_PASSWORD = "doctor123"
PATIENT_PASSWORD = "patient123"


# ---------------------------------------------------------------------------
# Specializations + symptom mapping
# ---------------------------------------------------------------------------

SPECIALIZATIONS = [
    ("Cardiologist", "heart, chest pain, blood pressure, cardiology"),
    ("Dentist", "teeth, tooth, gums, dental, toothache"),
    ("General Physician", "fever, flu, general, physician, cold"),
    ("Dermatologist", "skin, rash, acne, allergy, hair, pimples"),
    ("Pediatrician", "child, children, baby, kids, pediatric"),
    ("Neurologist", "brain, headache, migraine, nerve, epilepsy"),
    ("Gastroenterologist", "stomach, digestion, liver, acidity, gastric"),
    ("ENT Specialist", "ear, nose, throat, ent, sinus, tonsils"),
    ("Ophthalmologist", "eye, eyesight, vision, retina, cataract"),
    ("Orthopedic Surgeon", "bone, joint, fracture, spine, knee, back"),
    ("Gynecologist", "pregnancy, women, maternity, uterus, pcos"),
    ("Psychiatrist", "depression, anxiety, mental, stress, sleep"),
    ("Urologist", "kidney, urine, bladder, prostate"),
    ("Endocrinologist", "diabetes, thyroid, hormone"),
    ("Pulmonologist", "asthma, cough, breathing, lungs, chest infection"),
]

# symptom name -> specialization name
SYMPTOM_MAPPINGS = {
    "Tooth Pain": "Dentist",
    "Toothache": "Dentist",
    "Gum Bleeding": "Dentist",
    "Stomach Pain": "Gastroenterologist",
    "Acidity": "Gastroenterologist",
    "Liver Problem": "Gastroenterologist",
    "Chest Pain": "Cardiologist",
    "Heart Problem": "Cardiologist",
    "High Blood Pressure": "Cardiologist",
    "Skin Rash": "Dermatologist",
    "Skin Allergy": "Dermatologist",
    "Hair Fall": "Dermatologist",
    "Ear Pain": "ENT Specialist",
    "Sore Throat": "ENT Specialist",
    "Eye Infection": "Ophthalmologist",
    "Blurred Vision": "Ophthalmologist",
    "Joint Pain": "Orthopedic Surgeon",
    "Back Pain": "Orthopedic Surgeon",
    "Bone Fracture": "Orthopedic Surgeon",
    "Pregnancy": "Gynecologist",
    "Child Specialist": "Pediatrician",
    "Baby Fever": "Pediatrician",
    "Depression": "Psychiatrist",
    "Anxiety": "Psychiatrist",
    "Migraine": "Neurologist",
    "Epilepsy": "Neurologist",
    "Diabetes": "Endocrinologist",
    "Thyroid": "Endocrinologist",
    "Asthma": "Pulmonologist",
    "Cough": "Pulmonologist",
    "Kidney Stone": "Urologist",
}


def _seed_catalog(db: Session):
    """Create specializations, symptoms and their mappings."""
    if db.query(models.Specialization).count() > 0:
        return

    spec_objects = {}
    for name, keywords in SPECIALIZATIONS:
        spec = models.Specialization(name=name, keywords=keywords)
        db.add(spec)
        spec_objects[name] = spec
    db.flush()  # give the specializations their ids

    for symptom_name, spec_name in SYMPTOM_MAPPINGS.items():
        symptom = models.Symptom(name=symptom_name)
        db.add(symptom)
        db.flush()
        db.add(
            models.SymptomMapping(
                symptom_id=symptom.id,
                specialization_id=spec_objects[spec_name].id,
            )
        )


# ---------------------------------------------------------------------------
# Doctors
# ---------------------------------------------------------------------------

def _create_doctors():
    """Create the demo doctors with full profiles, fees and schedules."""
    doctors = [
        models.Doctor(
            name="Sarah Mitchell", email="smitchell@clinic.com", phone="03001234567",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-001234", gender="Female", date_of_birth=date(1980, 5, 12),
            years_of_experience=18, qualifications="MBBS, FCPS (Cardiology)",
            specialization="Cardiologist", languages="English, Urdu",
            biography="Board-certified cardiologist with 18 years of experience in interventional "
                      "cardiology. Head of the cardiac unit at Gulberg Medical Complex, Lahore.",
            hospital_name="Gulberg Medical Complex", clinic_address="24-B Main Boulevard, Gulberg III",
            city="Lahore", province="Punjab",
            first_visit_fee=2500, followup_fee=2000, online_fee=1500,
            is_verified=True, booking_enabled=True, patients_treated=1200,
        ),
        models.Doctor(
            name="John Carter", email="jcarter@clinic.com", phone="03011234568",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-002345", gender="Male", date_of_birth=date(1985, 2, 20),
            years_of_experience=12, qualifications="MBBS, MCPS (Family Medicine)",
            specialization="General Physician", languages="English, Urdu, Sindhi",
            biography="Trusted family physician in Karachi. Known for friendly, thorough check-ups "
                      "and affordable care for the whole family.",
            hospital_name="Clifton Health Center", clinic_address="Suite 12, Block 4, Clifton",
            city="Karachi", province="Sindh",
            first_visit_fee=1500, followup_fee=1200, online_fee=1000,
            is_verified=True, booking_enabled=True, patients_treated=2100,
        ),
        models.Doctor(
            name="Emily Rodriguez", email="erodriguez@clinic.com", phone="03002345679",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-003456", gender="Female", date_of_birth=date(1988, 11, 3),
            years_of_experience=10, qualifications="MBBS, FCPS (Dermatology)",
            specialization="Dermatologist", languages="English, Urdu, Punjabi",
            biography="Cosmetic and clinical dermatologist helping patients with acne, pigmentation "
                      "and hair loss using modern, evidence-based treatments.",
            hospital_name="Skyline Aesthetic Clinic", clinic_address="F-7 Markaz, Main Jinnah Avenue",
            city="Islamabad", province="ICT",
            first_visit_fee=2000, followup_fee=1500, online_fee=1500,
            is_verified=True, booking_enabled=True, patients_treated=860,
        ),
        models.Doctor(
            name="Michael Chen", email="mchen@clinic.com", phone="03003456780",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-004567", gender="Male", date_of_birth=date(1990, 7, 15),
            years_of_experience=8, qualifications="MBBS, MCPS (Paediatrics)",
            specialization="Pediatrician", languages="English, Urdu",
            biography="Caring paediatrician who believes every child deserves gentle, patient care. "
                      "Focused on vaccination, nutrition and child development.",
            hospital_name="Children Care Hospital", clinic_address="Model Town, Link Road",
            city="Lahore", province="Punjab",
            first_visit_fee=1800, followup_fee=1500, online_fee=1200,
            is_verified=True, booking_enabled=True, patients_treated=1500,
        ),
        models.Doctor(
            name="Linda Park", email="lpark@clinic.com", phone="03004567891",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-005678", gender="Female", date_of_birth=date(1979, 9, 28),
            years_of_experience=20, qualifications="MBBS, FRCP (Neurology)",
            specialization="Neurologist", languages="English, Urdu, Sindhi",
            biography="Senior neurologist specialising in migraine, epilepsy and stroke care. "
                      "25+ years of teaching and clinical practice.",
            hospital_name="Neuro Wellness Institute", clinic_address="Main Shahrah-e-Faisal",
            city="Karachi", province="Sindh",
            first_visit_fee=3000, followup_fee=2500, online_fee=2000,
            is_verified=True, booking_enabled=True, patients_treated=980,
        ),
        # --- Additional specialists so every example search works ------
        models.Doctor(
            name="Ahmed Raza", email="araza@clinic.com", phone="03005678902",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-006789", gender="Male", date_of_birth=date(1991, 4, 17),
            years_of_experience=7, qualifications="BDS, FCPS (Oral Surgery)",
            specialization="Dentist", languages="English, Urdu, Punjabi",
            biography="Gentle dentist specialising in painless root canals, teeth whitening "
                      "and cosmetic dentistry.",
            hospital_name="Smile Dental Care", clinic_address="DHA Phase 6, Commercial Area",
            city="Lahore", province="Punjab",
            first_visit_fee=1500, followup_fee=1200, online_fee=800,
            is_verified=True, booking_enabled=True, patients_treated=640,
        ),
        models.Doctor(
            name="Fatima Khan", email="fkhan@clinic.com", phone="03006789013",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-007890", gender="Female", date_of_birth=date(1987, 12, 1),
            years_of_experience=11, qualifications="MBBS, FCPS (Gastroenterology)",
            specialization="Gastroenterologist", languages="English, Urdu",
            biography="Gastroenterologist focused on acidity, liver disease and endoscopy. "
                      "Runs a dedicated GI clinic in Karachi.",
            hospital_name="Karachi GI Center", clinic_address="Plot 44, Shahrah-e-Faisal",
            city="Karachi", province="Sindh",
            first_visit_fee=2200, followup_fee=1800, online_fee=1500,
            is_verified=True, booking_enabled=True, patients_treated=720,
        ),
        models.Doctor(
            name="Ali Hassan", email="ahassan@clinic.com", phone="03007890124",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-008901", gender="Male", date_of_birth=date(1984, 6, 25),
            years_of_experience=13, qualifications="MBBS, FCPS (ENT)",
            specialization="ENT Specialist", languages="English, Urdu",
            biography="ENT specialist treating ear, nose and throat conditions including "
                      "sinusitis and tonsillitis.",
            hospital_name="Islamabad ENT Clinic", clinic_address="G-9 Markaz, Blue Area Road",
            city="Islamabad", province="ICT",
            first_visit_fee=1800, followup_fee=1500, online_fee=1000,
            is_verified=True, booking_enabled=True, patients_treated=1100,
        ),
        models.Doctor(
            name="Ayesha Malik", email="amalik@clinic.com", phone="03008901235",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-009012", gender="Female", date_of_birth=date(1983, 3, 9),
            years_of_experience=15, qualifications="MBBS, FCPS (Gynaecology)",
            specialization="Gynecologist", languages="English, Urdu",
            biography="Trusted gynaecologist for pregnancy care, fertility and women's health. "
                      "15 years of gentle, respectful care.",
            hospital_name="Mother Care Hospital", clinic_address="Ferozepur Road",
            city="Lahore", province="Punjab",
            first_visit_fee=2500, followup_fee=2000, online_fee=1500,
            is_verified=True, booking_enabled=True, patients_treated=1500,
        ),
        models.Doctor(
            name="Imran Sheikh", email="isheikh@clinic.com", phone="03009012346",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-010123", gender="Male", date_of_birth=date(1978, 8, 14),
            years_of_experience=19, qualifications="MBBS, FRCS (Orthopaedics)",
            specialization="Orthopedic Surgeon", languages="English, Urdu",
            biography="Orthopedic surgeon for joint replacement, sports injuries and "
                      "spine problems.",
            hospital_name="Rawalpindi Ortho Center", clinic_address="Saddar Road",
            city="Rawalpindi", province="Punjab",
            first_visit_fee=2800, followup_fee=2200, online_fee=1800,
            is_verified=True, booking_enabled=True, patients_treated=900,
        ),
        models.Doctor(
            name="Mariam Tariq", email="mtariq@clinic.com", phone="03000123457",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-011234", gender="Female", date_of_birth=date(1992, 1, 30),
            years_of_experience=6, qualifications="MBBS, MRCP (Endocrinology)",
            specialization="Endocrinologist", languages="English, Urdu, Sindhi",
            biography="Endocrinologist helping patients manage diabetes and thyroid "
                      "disorders with practical, personalised plans.",
            hospital_name="Endo Care Clinic", clinic_address="Bahadurabad, Main Street",
            city="Karachi", province="Sindh",
            first_visit_fee=2000, followup_fee=1600, online_fee=1200,
            is_verified=True, booking_enabled=True, patients_treated=380,
        ),
        models.Doctor(
            name="Usman Chaudhry", email="uchaudhry@clinic.com", phone="03001234568",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-012345", gender="Male", date_of_birth=date(1986, 10, 22),
            years_of_experience=10, qualifications="MBBS, FCPS (Psychiatry)",
            specialization="Psychiatrist", languages="English, Urdu",
            biography="Psychiatrist for depression, anxiety and stress management. "
                      "Counselling and medication management in a safe space.",
            hospital_name="Mind Matters Clinic", clinic_address="Model Town, Block B",
            city="Lahore", province="Punjab",
            first_visit_fee=2500, followup_fee=2000, online_fee=2000,
            is_verified=True, booking_enabled=True, patients_treated=520,
        ),
        models.Doctor(
            name="Nadia Akhtar", email="nakhtar@clinic.com", phone="03002345679",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-013456", gender="Female", date_of_birth=date(1990, 5, 5),
            years_of_experience=9, qualifications="MBBS, FCPS (Ophthalmology)",
            specialization="Ophthalmologist", languages="English, Urdu",
            biography="Eye specialist for cataract, vision and retinal conditions.",
            hospital_name="Vision Eye Institute", clinic_address="F-8 Markaz",
            city="Islamabad", province="ICT",
            first_visit_fee=1800, followup_fee=1400, online_fee=1000,
            is_verified=True, booking_enabled=True, patients_treated=760,
        ),
        models.Doctor(
            name="Kamran Ali", email="kali@clinic.com", phone="03003456790",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-014567", gender="Male", date_of_birth=date(1981, 7, 18),
            years_of_experience=14, qualifications="MBBS, FCPS (Pulmonology)",
            specialization="Pulmonologist", languages="English, Urdu, Pashto",
            biography="Pulmonologist treating asthma, chronic cough and breathing "
                      "problems, with a focus on air-quality related illness.",
            hospital_name="Peshawar Lung Center", clinic_address="University Road",
            city="Peshawar", province="KPK",
            first_visit_fee=2000, followup_fee=1600, online_fee=1200,
            is_verified=True, booking_enabled=True, patients_treated=610,
        ),
        models.Doctor(
            name="Sana Batool", email="sbatool@clinic.com", phone="03004567801",
            password_hash=hash_password(DOCTOR_PASSWORD),
            pmdc_number="PMDC-015678", gender="Female", date_of_birth=date(1989, 11, 11),
            years_of_experience=8, qualifications="MBBS, FCPS (Urology)",
            specialization="Urologist", languages="English, Urdu, Balochi",
            biography="Urologist for kidney stones, urinary tract and prostate care.",
            hospital_name="Quetta Kidney Care", clinic_address="Jinnah Road",
            city="Quetta", province="Balochistan",
            first_visit_fee=2600, followup_fee=2000, online_fee=1500,
            is_verified=True, booking_enabled=True, patients_treated=410,
        ),
    ]
    return doctors


def _seed_schedules(db: Session, doctor: models.Doctor, days: list, start_h, end_h, duration):
    """Add a simple weekly schedule to a doctor."""
    for day in days:
        db.add(
            models.DoctorSchedule(
                doctor_id=doctor.id,
                day_of_week=day,
                start_time=time(start_h, 0),
                end_time=time(end_h, 0),
                duration_minutes=duration,
                is_available=True,
            )
        )


def _create_patients():
    """Create the demo patients."""
    return [
        models.Patient(name="Alice Johnson", email="alice@example.com", phone="03011223344",
                       password_hash=hash_password(PATIENT_PASSWORD)),
        models.Patient(name="Bob Smith", email="bob@example.com", phone="03022334455",
                       password_hash=hash_password(PATIENT_PASSWORD)),
        models.Patient(name="Carol Davis", email="carol@example.com", phone="03033445566",
                       password_hash=hash_password(PATIENT_PASSWORD)),
    ]


def _create_appointments(db: Session, doctors, patients):
    """Create sample appointments so the dashboards are not empty."""
    today = date.today()

    # A few already-booked slots for today and tomorrow.
    bookings = [
        (doctors[0], patients[0], today, time(10, 0), models.AppointmentStatus.BOOKED, 2500, "First"),
        (doctors[1], patients[1], today, time(11, 0), models.AppointmentStatus.BOOKED, 1500, "First"),
        (doctors[2], patients[2], today + timedelta(days=1), time(9, 30), models.AppointmentStatus.BOOKED, 2000, "First"),
        (doctors[3], patients[0], today - timedelta(days=1), time(10, 0), models.AppointmentStatus.COMPLETED, 1800, "First"),
        (doctors[4], patients[1], today - timedelta(days=2), time(14, 0), models.AppointmentStatus.COMPLETED, 3000, "First"),
    ]
    appointments = []
    for doctor, patient, appt_date, appt_time, status, fee, visit_type in bookings:
        appointments.append(
            models.Appointment(
                doctor_id=doctor.id, patient_id=patient.id,
                appointment_date=appt_date, appointment_time=appt_time,
                status=status, consultation_fee=fee, visit_type=visit_type,
            )
        )
    return appointments


def _seed_reviews(db: Session, doctors, patients):
    """Add a few reviews so doctor profiles show ratings."""
    if db.query(models.Review).count() > 0:
        return
    sample = [
        (0, 0, 5, "Very professional and explains everything clearly."),
        (0, 1, 4, "Good doctor, the checkup was thorough."),
        (1, 0, 4, "Friendly and affordable. Highly recommended."),
        (2, 2, 5, "My skin allergy is much better after treatment."),
        (3, 1, 5, "Excellent with kids, my son loves visiting."),
        (4, 2, 4, "Great neurologist, very experienced."),
        (5, 0, 5, "Painless extraction, very gentle dentist."),
        (6, 1, 4, "My acidity and digestion are much better now."),
        (8, 2, 5, "Wonderful care throughout my pregnancy."),
        (11, 0, 5, "Very understanding psychiatrist. Highly recommend."),
    ]
    for doctor_idx, patient_idx, rating, comment in sample:
        db.add(
            models.Review(
                doctor_id=doctors[doctor_idx].id,
                patient_id=patients[patient_idx].id,
                rating=rating,
                comment=comment,
            )
        )


def _seed_notifications(db: Session, doctors, patients):
    """Create a couple of sample notifications."""
    if db.query(models.Notification).count() > 0:
        return
    db.add_all(
        [
            models.Notification(
                recipient_role="doctor", recipient_id=doctors[0].id,
                message="You have 2 appointments today.",
                notification_type="info",
            ),
            models.Notification(
                recipient_role="patient", recipient_id=patients[0].id,
                message="Your appointment with Dr. Sarah Mitchell is tomorrow at 10:00 AM.",
                notification_type="info",
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

def seed_data():
    """Create tables (if missing) and insert demo data (if empty)."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        _seed_catalog(db)
        db.commit()

        # If doctors already exist, skip seeding user accounts.
        if db.query(models.Doctor).count() == 0:
            doctors = _create_doctors()
            patients = _create_patients()
            db.add_all(doctors)
            db.add_all(patients)
            db.commit()

            for doctor in doctors:
                db.refresh(doctor)
            for patient in patients:
                db.refresh(patient)

            # Give each doctor a weekly schedule.
            # Original five doctors
            _seed_schedules(db, doctors[0], [0, 1, 2, 3, 4], 9, 17, 30)   # Mon-Fri
            _seed_schedules(db, doctors[1], [0, 1, 2, 3, 4, 5], 10, 14, 20)  # Mon-Sat
            _seed_schedules(db, doctors[2], [0, 1, 2, 3, 5], 11, 15, 30)  # Mon-Thu + Sat
            _seed_schedules(db, doctors[3], [0, 1, 2, 3, 4], 9, 13, 15)   # Mon-Fri, 15 min
            _seed_schedules(db, doctors[4], [1, 2, 3, 4, 5], 12, 16, 60)  # Tue-Sat, 60 min
            # Additional specialists
            _seed_schedules(db, doctors[5], [0, 1, 2, 3, 4, 5], 9, 13, 30)   # Dentist
            _seed_schedules(db, doctors[6], [0, 1, 2, 3, 4], 10, 16, 30)     # Gastro
            _seed_schedules(db, doctors[7], [0, 1, 2, 3, 4, 5], 11, 15, 20)  # ENT
            _seed_schedules(db, doctors[8], [0, 1, 2, 3, 4], 10, 14, 30)     # Gynae (Mon-Fri)
            _seed_schedules(db, doctors[9], [1, 2, 3, 4, 5], 12, 16, 30)     # Ortho
            _seed_schedules(db, doctors[10], [0, 1, 2, 3, 4], 9, 15, 20)     # Endocrine
            _seed_schedules(db, doctors[11], [0, 1, 2, 3, 4, 5], 14, 18, 30) # Psych
            _seed_schedules(db, doctors[12], [0, 1, 2, 3, 4], 9, 13, 20)     # Eye
            _seed_schedules(db, doctors[13], [0, 1, 2, 3, 4, 5], 10, 14, 30) # Pulmo
            _seed_schedules(db, doctors[14], [0, 1, 2, 3, 4], 11, 15, 30)    # Urologist

            db.add_all(_create_appointments(db, doctors, patients))
            db.commit()

            _seed_reviews(db, doctors, patients)
            _seed_notifications(db, doctors, patients)
            db.commit()

            print("[seed] Sample data created: catalog, 5 doctors, 3 patients, appointments, reviews.")
            print("[seed] Doctor login password: doctor123 | Patient login password: patient123")
        else:
            print("[seed] Doctors already exist, skipping sample accounts.")
    finally:
        db.close()


# Allow running the seed manually:  python -m app.seed
if __name__ == "__main__":
    seed_data()
