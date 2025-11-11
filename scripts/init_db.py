"""
Database initialization script with sample data.
"""

from datetime import datetime, timedelta

from app.core.database import SessionLocal, engine, Base

# Import all models to ensure mappers are registered before create_all / queries
import app.models  # noqa: F401
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.patient import Patient, Gender
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription
from app.models.tenant import Tenant


def init_db():
    """Initialize database with sample data."""

    # Tables are created by Alembic migrations, not here
    # Base.metadata.create_all(bind=engine)

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
            is_active=True,
        )

        doctor_user = User(
            tenant_id=tenant_id,
            email="doctor@keneyapp.com",
            username="doctor",
            full_name="Dr. Jean Dupont",
            role=UserRole.DOCTOR,
            hashed_password=get_password_hash("doctor123"),
            is_active=True,
        )

        nurse_user = User(
            tenant_id=tenant_id,
            email="nurse@keneyapp.com",
            username="nurse",
            full_name="Marie Martin",
            role=UserRole.NURSE,
            hashed_password=get_password_hash("nurse123"),
            is_active=True,
        )

        receptionist_user = User(
            tenant_id=tenant_id,
            email="receptionist@keneyapp.com",
            username="receptionist",
            full_name="Sophie Bernard",
            role=UserRole.RECEPTIONIST,
            hashed_password=get_password_hash("receptionist123"),
            is_active=True,
        )

        db.add_all([admin_user, doctor_user, nurse_user, receptionist_user])
        db.commit()

        # TEMPORARY: Skip demo data creation due to model/migration mismatch
        # TODO: Create proper migrations for all model fields before re-enabling
        # # Create sample patients
        # patient1 = Patient(...)
        # patient2 = Patient(...)
        # db.add_all([patient1, patient2])
        # db.commit()
        
        # # Create sample appointments...
        # # Create sample prescriptions...

        print("✓ Database initialized successfully!")
        print("\nSample users created:")
        print("  Admin: admin / admin123")
        print("  Doctor: doctor / doctor123")
        print("  Nurse: nurse / nurse123")
        print("  Receptionist: receptionist / receptionist123")
        print("\n⚠ Demo data (patients, appointments, prescriptions) skipped - use API to create")

    finally:
        db.close()


if __name__ == "__main__":
    init_db()
