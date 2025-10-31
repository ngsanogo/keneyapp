"""
Database initialization script with sample data.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.patient import Patient, Gender
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription
from app.models.tenant import Tenant


def init_db():
    """Initialize database with sample data."""
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_user = db.query(User).first()
        if existing_user:
            print("Database already initialized!")
            return
        
        # Ensure at least one tenant exists (align with migration defaults)
        default_tenant = db.query(Tenant).filter(Tenant.slug == "default").first()
        if not default_tenant:
            default_tenant = Tenant(
                name="Default Tenant",
                slug="default",
                is_active=True,
                configuration={},
            )
            db.add(default_tenant)
            db.flush()

        tenant_id = default_tenant.id

        # Create sample users
        admin_user = User(
            tenant_id=tenant_id,
            email="admin@keneyapp.com",
            username="admin",
            full_name="Admin User",
            role=UserRole.ADMIN,
            hashed_password=get_password_hash("admin123"),
            is_active=True
        )

        doctor_user = User(
            tenant_id=tenant_id,
            email="doctor@keneyapp.com",
            username="doctor",
            full_name="Dr. Jean Dupont",
            role=UserRole.DOCTOR,
            hashed_password=get_password_hash("doctor123"),
            is_active=True
        )

        nurse_user = User(
            tenant_id=tenant_id,
            email="nurse@keneyapp.com",
            username="nurse",
            full_name="Marie Martin",
            role=UserRole.NURSE,
            hashed_password=get_password_hash("nurse123"),
            is_active=True
        )

        receptionist_user = User(
            tenant_id=tenant_id,
            email="receptionist@keneyapp.com",
            username="receptionist",
            full_name="Sophie Bernard",
            role=UserRole.RECEPTIONIST,
            hashed_password=get_password_hash("receptionist123"),
            is_active=True
        )
        
        db.add_all([admin_user, doctor_user, nurse_user, receptionist_user])
        db.commit()
        
        # Create sample patients
        patient1 = Patient(
            tenant_id=tenant_id,
            first_name="Pierre",
            last_name="Dubois",
            date_of_birth=datetime(1985, 5, 15).date(),
            gender=Gender.MALE,
            email="pierre.dubois@example.com",
            phone="+33 6 12 34 56 78",
            address="123 Rue de la Paix, 75001 Paris",
            blood_type="O+",
            allergies="Penicillin",
            emergency_contact="Marie Dubois",
            emergency_phone="+33 6 98 76 54 32"
        )
        
        patient2 = Patient(
            tenant_id=tenant_id,
            first_name="Claire",
            last_name="Laurent",
            date_of_birth=datetime(1990, 8, 20).date(),
            gender=Gender.FEMALE,
            email="claire.laurent@example.com",
            phone="+33 6 23 45 67 89",
            address="456 Avenue des Champs-Élysées, 75008 Paris",
            blood_type="A+",
            emergency_contact="Paul Laurent",
            emergency_phone="+33 6 87 65 43 21"
        )
        
        db.add_all([patient1, patient2])
        db.commit()
        
        # Create sample appointments
        tomorrow = datetime.utcnow() + timedelta(days=1)
        appointment1 = Appointment(
            tenant_id=tenant_id,
            patient_id=patient1.id,
            doctor_id=doctor_user.id,
            appointment_date=tomorrow.replace(hour=10, minute=0),
            duration_minutes=30,
            status=AppointmentStatus.SCHEDULED,
            reason="Consultation de routine",
            notes="Patient signale des douleurs au dos"
        )
        
        next_week = datetime.utcnow() + timedelta(days=7)
        appointment2 = Appointment(
            tenant_id=tenant_id,
            patient_id=patient2.id,
            doctor_id=doctor_user.id,
            appointment_date=next_week.replace(hour=14, minute=30),
            duration_minutes=45,
            status=AppointmentStatus.SCHEDULED,
            reason="Suivi annuel",
            notes="Contrôle de santé régulier"
        )
        
        db.add_all([appointment1, appointment2])
        db.commit()
        
        # Create sample prescriptions
        prescription1 = Prescription(
            tenant_id=tenant_id,
            patient_id=patient1.id,
            doctor_id=doctor_user.id,
            medication_name="Paracétamol",
            dosage="500mg",
            frequency="3 fois par jour",
            duration="7 jours",
            instructions="À prendre après les repas",
            refills=2
        )
        
        prescription2 = Prescription(
            tenant_id=tenant_id,
            patient_id=patient2.id,
            doctor_id=doctor_user.id,
            medication_name="Vitamine D",
            dosage="1000 UI",
            frequency="1 fois par jour",
            duration="30 jours",
            instructions="À prendre le matin",
            refills=1
        )
        
        db.add_all([prescription1, prescription2])
        db.commit()
        
        print("✓ Database initialized successfully!")
        print("\nSample users created:")
        print("  Admin: admin / admin123")
        print("  Doctor: doctor / doctor123")
        print("  Nurse: nurse / nurse123")
        print("  Receptionist: receptionist / receptionist123")
        
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
