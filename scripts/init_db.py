#!/usr/bin/env python3
"""
Database initialization script for KeneyApp
Creates initial admin user and sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User, Patient, Appointment, Prescription
from app.models.user import UserRole
from app.models.appointment import AppointmentStatus
from app.models.prescription import PrescriptionStatus
from app.core.security import get_password_hash
from datetime import datetime, timedelta

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def create_admin_user():
    """Create initial admin user"""
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("✅ Admin user already exists")
            return

        # Create admin user
        admin_user = User(
            email="admin@keneyapp.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        print("✅ Admin user created successfully")
        print("   Username: admin")
        print("   Password: admin123")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_data():
    """Create sample data for testing"""
    db = SessionLocal()
    try:
        # Create sample doctor
        doctor = User(
            email="doctor@keneyapp.com",
            username="doctor",
            hashed_password=get_password_hash("doctor123"),
            full_name="Dr. John Smith",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True
        )
        db.add(doctor)
        db.flush()  # Get the ID

        # Create sample patients
        patients = [
            Patient(
                first_name="Alice",
                last_name="Johnson",
                date_of_birth=datetime(1985, 5, 15).date(),
                gender="Female",
                phone="+1-555-0101",
                email="alice.johnson@email.com",
                address="123 Main St, City, State 12345",
                emergency_contact_name="Bob Johnson",
                emergency_contact_phone="+1-555-0102",
                medical_history="No significant medical history",
                allergies="None known"
            ),
            Patient(
                first_name="Michael",
                last_name="Brown",
                date_of_birth=datetime(1978, 8, 22).date(),
                gender="Male",
                phone="+1-555-0201",
                email="michael.brown@email.com",
                address="456 Oak Ave, City, State 12345",
                emergency_contact_name="Sarah Brown",
                emergency_contact_phone="+1-555-0202",
                medical_history="Hypertension, Type 2 Diabetes",
                allergies="Penicillin"
            )
        ]
        
        for patient in patients:
            db.add(patient)
        db.flush()  # Get the IDs

        # Create sample appointments
        appointments = [
            Appointment(
                patient_id=patients[0].id,
                doctor_id=doctor.id,
                appointment_date=datetime.now() + timedelta(days=1),
                duration_minutes=30,
                status=AppointmentStatus.SCHEDULED,
                notes="Regular checkup"
            ),
            Appointment(
                patient_id=patients[1].id,
                doctor_id=doctor.id,
                appointment_date=datetime.now() + timedelta(days=3),
                duration_minutes=45,
                status=AppointmentStatus.SCHEDULED,
                notes="Follow-up for diabetes management"
            )
        ]
        
        for appointment in appointments:
            db.add(appointment)
        db.flush()  # Get the IDs

        # Create sample prescriptions
        prescriptions = [
            Prescription(
                patient_id=patients[1].id,
                doctor_id=doctor.id,
                appointment_id=appointments[1].id,
                medication_name="Metformin",
                dosage="500mg",
                frequency="Twice daily",
                duration="30 days",
                instructions="Take with food",
                status=PrescriptionStatus.ACTIVE,
                prescribed_date=datetime.now()
            )
        ]
        
        for prescription in prescriptions:
            db.add(prescription)

        db.commit()
        print("✅ Sample data created successfully")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("🚀 Initializing KeneyApp database...")
    
    try:
        create_tables()
        create_admin_user()
        create_sample_data()
        print("\n🎉 Database initialization completed successfully!")
        print("\nYou can now start the application with:")
        print("  python -m uvicorn app.main:app --reload")
        print("\nOr with Docker Compose:")
        print("  docker-compose up")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
