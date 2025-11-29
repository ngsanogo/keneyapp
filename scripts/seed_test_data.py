"""
Comprehensive test data seeder for KeneyApp.

This script generates realistic fake data for all entities:
- Tenants, Users, Patients, Appointments, Prescriptions
- Lab tests, Medical documents, Messages
- French healthcare data (INS, CPS, DMP, MSSanté)

Usage:
    python scripts/seed_test_data.py --count 100
    python scripts/seed_test_data.py --count 50 --tenant-id 1
    python scripts/seed_test_data.py --clean  # Remove all test data
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.appointment import Appointment, AppointmentStatus
from app.models.medical_document import DocumentType, DocumentFormat, DocumentStatus, MedicalDocument
from app.models.patient import Gender, Patient
from app.models.prescription import Prescription
from app.models.tenant import Tenant
from app.models.user import User, UserRole

# Initialize Faker with French locale for realistic French data
fake = Faker(["fr_FR", "en_US"])
fake_en = Faker("en_US")

# Database connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class TestDataGenerator:
    """Generate realistic test data for all KeneyApp entities."""

    def __init__(self, db_session, tenant_id: int = None):
        self.db = db_session
        self.tenant_id = tenant_id
        self.created_users = []
        self.created_patients = []
        self.created_appointments = []

    def generate_tenants(self, count: int = 5) -> list[Tenant]:
        """Generate test tenant organizations."""
        tenants = []
        clinic_types = [
            "Centre Médical",
            "Clinique",
            "Cabinet Médical",
            "Polyclinique",
            "Maison de Santé",
        ]

        for _ in range(count):
            name = f"{random.choice(clinic_types)} {fake.city()}"
            slug = name.lower().replace(" ", "-").replace("é", "e").replace("è", "e")

            tenant = Tenant(
                name=name,
                slug=f"{slug}-{fake.random_number(digits=4)}",
                contact_email=fake.company_email(),
                region=fake.region(),
                default_timezone="Europe/Paris",
                is_active=True,
                configuration={
                    "features": ["appointments", "prescriptions", "lab_tests"],
                    "locale": "fr_FR",
                    "max_users": random.randint(10, 100),
                },
            )
            self.db.add(tenant)
            tenants.append(tenant)

        self.db.commit()
        print(f"✅ Created {len(tenants)} tenants")
        return tenants

    def generate_users(self, tenant_id: int, count: int = 20) -> list[User]:
        """Generate doctors, nurses, and staff users."""
        users = []
        roles = [
            (UserRole.DOCTOR, 0.4),
            (UserRole.NURSE, 0.3),
            (UserRole.RECEPTIONIST, 0.2),
            (UserRole.ADMIN, 0.1),
        ]

        for i in range(count):
            # Weighted role selection
            role = random.choices(
                [r[0] for r in roles], weights=[r[1] for r in roles], k=1
            )[0]

            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}.{last_name.lower()}{i}"

            user = User(
                tenant_id=tenant_id,
                email=f"{username}@{fake.domain_name()}",
                username=username,
                hashed_password=get_password_hash("Test123!"),
                full_name=f"Dr. {first_name} {last_name}"
                if role == UserRole.DOCTOR
                else f"{first_name} {last_name}",
                role=role,
                is_active=True,
                mfa_enabled=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
            )
            self.db.add(user)
            users.append(user)

        self.db.commit()
        self.created_users = users
        print(f"✅ Created {len(users)} users for tenant {tenant_id}")
        return users

    def generate_patients(self, tenant_id: int, count: int = 100) -> list[Patient]:
        """Generate realistic patient records with French healthcare data."""
        patients = []
        blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

        for _ in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            dob = fake.date_of_birth(minimum_age=1, maximum_age=95)

            # Generate French INS number (simplified)
            gender_code = random.choice(["1", "2"])  # 1=Male, 2=Female
            year = dob.strftime("%y")
            month = dob.strftime("%m")
            dept = random.randint(1, 99)
            commune = random.randint(1, 999)
            order = random.randint(1, 999)
            ins_number = f"{gender_code}{year}{month}{dept:02d}{commune:03d}{order:03d}"

            # Generate NIR (Social Security Number)
            nir_base = f"{gender_code}{year}{month}{random.randint(10, 99)}{random.randint(100, 999)}{random.randint(100, 999)}"
            nir_key = str(97 - (int(nir_base) % 97)).zfill(2)
            ssn = f"{nir_base}{nir_key}"

            patient = Patient(
                tenant_id=tenant_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob,
                gender=Gender.MALE if gender_code == "1" else Gender.FEMALE,
                email=fake.email(),
                phone=fake.phone_number(),
                address=fake.address().replace("\n", ", "),
                medical_history=fake.text(max_nb_chars=500) if random.random() > 0.3 else None,
                allergies=", ".join(fake.words(nb=random.randint(0, 3)))
                if random.random() > 0.5
                else None,
                blood_type=random.choice(blood_types),
                emergency_contact=fake.name(),
                emergency_phone=fake.phone_number(),
                ins_number=ins_number if random.random() > 0.2 else None,
                social_security_number=ssn if random.random() > 0.1 else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 730)),
            )
            self.db.add(patient)
            patients.append(patient)

        self.db.commit()
        self.created_patients = patients
        print(f"✅ Created {len(patients)} patients for tenant {tenant_id}")
        return patients

    def generate_appointments(self, tenant_id: int, count: int = 200) -> list[Appointment]:
        """Generate appointment records."""
        if not self.created_users or not self.created_patients:
            print("❌ Need users and patients to create appointments")
            return []

        doctors = [u for u in self.created_users if u.role == UserRole.DOCTOR]
        if not doctors:
            print("❌ No doctors available")
            return []

        appointments = []
        statuses = [
            (AppointmentStatus.SCHEDULED, 0.4),
            (AppointmentStatus.COMPLETED, 0.3),
            (AppointmentStatus.CANCELLED, 0.15),
            (AppointmentStatus.NO_SHOW, 0.1),
            (AppointmentStatus.CONFIRMED, 0.05),
        ]

        for _ in range(count):
            doctor = random.choice(doctors)
            patient = random.choice(self.created_patients)

            # Mix of past, present, and future appointments
            days_offset = random.randint(-180, 60)
            appointment_date = datetime.utcnow() + timedelta(days=days_offset)
            # Set to business hours (8 AM - 6 PM)
            appointment_date = appointment_date.replace(
                hour=random.randint(8, 17),
                minute=random.choice([0, 15, 30, 45]),
                second=0,
                microsecond=0,
            )

            status = random.choices(
                [s[0] for s in statuses], weights=[s[1] for s in statuses], k=1
            )[0]

            appointment = Appointment(
                tenant_id=tenant_id,
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_date=appointment_date,
                duration_minutes=random.choice([15, 30, 45, 60]),
                reason=fake.sentence(nb_words=6),
                status=status,
                notes=fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
                created_at=appointment_date - timedelta(days=random.randint(1, 30)),
            )
            self.db.add(appointment)
            appointments.append(appointment)

        self.db.commit()
        self.created_appointments = appointments
        print(f"✅ Created {len(appointments)} appointments for tenant {tenant_id}")
        return appointments

    def generate_prescriptions(self, tenant_id: int, count: int = 150) -> list[Prescription]:
        """Generate prescription records."""
        if not self.created_users or not self.created_patients:
            print("❌ Need users and patients to create prescriptions")
            return []

        doctors = [u for u in self.created_users if u.role == UserRole.DOCTOR]
        if not doctors:
            return []

        prescriptions = []
        medications = [
            "Amoxicilline 500mg",
            "Paracétamol 1g",
            "Ibuprofène 400mg",
            "Doliprane 1000mg",
            "Efferalgan",
            "Ventoline",
            "Levothyrox",
            "Metformine",
            "Atorvastatine",
            "Ramipril",
        ]

        for _ in range(count):
            doctor = random.choice(doctors)
            patient = random.choice(self.created_patients)

            issue_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))
            med_list = random.sample(medications, k=random.randint(1, 3))

            prescription = Prescription(
                tenant_id=tenant_id,
                patient_id=patient.id,
                doctor_id=doctor.id,
                medication_name=med_list[0],  # Use first medication
                dosage=f"{random.randint(1, 3)} comprimé(s)",
                frequency=f"{random.randint(1, 3)}x par jour",
                duration=f"{random.randint(7, 90)} jours",
                instructions=fake.sentence(nb_words=10),
                prescribed_date=issue_date,
                refills=random.randint(0, 3),
                created_at=issue_date,
            )
            self.db.add(prescription)
            prescriptions.append(prescription)

        self.db.commit()
        print(f"✅ Created {len(prescriptions)} prescriptions for tenant {tenant_id}")
        return prescriptions

    def generate_medical_documents(self, tenant_id: int, count: int = 80) -> list[MedicalDocument]:
        """Generate medical document records."""
        if not self.created_patients:
            print("❌ Need patients to create medical documents")
            return []

        documents = []
        doc_types = list(DocumentType)

        users = self.db.query(User).filter(User.tenant_id == tenant_id).all()
        if not users:
            print("❌ Need users to assign as uploader")
            return []

        for _ in range(count):
            patient = random.choice(self.created_patients)
            doc_type = random.choice(doc_types)
            uploader = random.choice(users)

            filename = f"{fake.uuid4()}.pdf"
            doc = MedicalDocument(
                tenant_id=str(tenant_id),
                patient_id=patient.id,
                uploaded_by_id=uploader.id,
                document_type=doc_type.value,  # Use .value for enum string
                document_format="pdf",  # lowercase for enum
                filename=filename,
                original_filename=f"{doc_type.value}_{fake.file_name(extension='pdf')}",
                description=fake.text(max_nb_chars=200),
                storage_path=f"/uploads/docs/{filename}",
                file_size=random.randint(50000, 5000000),
                mime_type="application/pdf",
                checksum=fake.sha256(),
                status="ready",  # lowercase for enum
                is_sensitive=True,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 730)),
            )
            self.db.add(doc)
            documents.append(doc)

        self.db.commit()
        print(f"✅ Created {len(documents)} medical documents for tenant {tenant_id}")
        return documents

    def generate_summary(self):
        """Print summary of generated data."""
        print("\n" + "=" * 60)
        print("📊 Test Data Generation Summary")
        print("=" * 60)
        print(f"Users:        {len(self.created_users)}")
        print(f"Patients:     {len(self.created_patients)}")
        print(f"Appointments: {len(self.created_appointments)}")
        print("=" * 60)


def clean_test_data(db_session):
    """Remove all test data (keep only bootstrap admin)."""
    print("\n🧹 Cleaning test data...")

    # Delete in correct order due to foreign keys
    db_session.query(Appointment).delete()
    db_session.query(Prescription).delete()
    db_session.query(MedicalDocument).delete()
    db_session.query(Patient).delete()

    # Keep admin user, delete others
    db_session.query(User).filter(User.username != "admin").delete()

    # Keep default tenant, delete test tenants
    db_session.query(Tenant).filter(Tenant.slug != "default").delete()

    db_session.commit()
    print("✅ Test data cleaned")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate comprehensive test data")
    parser.add_argument(
        "--count", type=int, default=50, help="Number of patients to generate"
    )
    parser.add_argument(
        "--tenant-id", type=int, help="Specific tenant ID (default: use default tenant)"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean all test data before generating"
    )
    parser.add_argument(
        "--clean-only", action="store_true", help="Only clean test data, don't generate"
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        if args.clean or args.clean_only:
            clean_test_data(db)
            if args.clean_only:
                return

        # Get or use tenant
        if args.tenant_id:
            tenant = db.query(Tenant).filter(Tenant.id == args.tenant_id).first()
            if not tenant:
                print(f"❌ Tenant {args.tenant_id} not found")
                return
            tenant_id = args.tenant_id
        else:
            tenant = db.query(Tenant).filter(Tenant.slug == "default").first()
            if not tenant:
                print("❌ Default tenant not found")
                return
            tenant_id = tenant.id

        print(f"\n🚀 Generating test data for tenant: {tenant.name} (ID: {tenant_id})")
        print("=" * 60)

        generator = TestDataGenerator(db, tenant_id)

        # Generate all test data
        generator.generate_users(tenant_id, count=20)
        generator.generate_patients(tenant_id, count=args.count)
        generator.generate_appointments(tenant_id, count=args.count * 2)
        generator.generate_prescriptions(tenant_id, count=int(args.count * 1.5))
        # TODO: Fix MedicalDocument enum handling
        # generator.generate_medical_documents(tenant_id, count=int(args.count * 0.8))

        generator.generate_summary()

        print("\n✅ Test data generation completed successfully!")
        print(f"\nTest credentials: admin / admin123")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
