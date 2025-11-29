"""
Configuration globale pytest pour KeneyApp v3.0

Fixtures réutilisables pour tous les tests:
- Base de données et sessions
- Utilisateurs (admin, doctor, nurse, patient)
- Tenants
- Authentification et tokens
- Clients API
- Données de test
"""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.user import User, UserRole

# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def db_engine():
    """Crée un moteur de base de données en mémoire pour les tests"""
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, None, None]:
    """Crée une session de base de données pour un test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Crée un client de test FastAPI avec override de la DB"""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# TENANT FIXTURES
# ============================================================================


@pytest.fixture
def test_tenant(db: Session) -> Tenant:
    """Crée un tenant de test par défaut"""
    tenant = Tenant(
        name="Test Medical Center",
        slug="test-medical-001",
        is_active=True,
        contact_email="admin@testmedical.com",
        configuration={},
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def other_tenant(db: Session) -> Tenant:
    """Crée un second tenant pour tester l'isolation"""
    tenant = Tenant(
        name="Other Clinic",
        slug="other-clinic-002",
        is_active=True,
        contact_email="admin@otherclinic.com",
        configuration={},
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


# ============================================================================
# USER FIXTURES
# ============================================================================


@pytest.fixture
def test_super_admin(db: Session, test_tenant) -> User:
    """Crée un super administrateur"""
    user = User(
        email="superadmin@test.com",
        username="superadmin",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        tenant_id=test_tenant.id,
        hashed_password=get_password_hash("superadmin123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db: Session, test_tenant) -> User:
    """Crée un administrateur"""
    user = User(
        email="admin@test.com",
        username="admin",
        full_name="Admin User",
        role=UserRole.ADMIN,
        tenant_id=test_tenant.id,
        hashed_password=get_password_hash("admin123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_doctor(db: Session, test_tenant) -> User:
    """Crée un médecin"""
    user = User(
        email="doctor@test.com",
        username="doctor_smith",
        full_name="John Smith",
        role=UserRole.DOCTOR,
        tenant_id=test_tenant.id,
        hashed_password=get_password_hash("doctor123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_doctor_2(db: Session, test_tenant) -> User:
    """Crée un second médecin"""
    user = User(
        email="doctor2@test.com",
        username="doctor_jones",
        full_name="Jane Jones",
        role=UserRole.DOCTOR,
        tenant_id=test_tenant.id,
        hashed_password=get_password_hash("doctor123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_nurse(db: Session, test_tenant) -> User:
    """Crée une infirmière"""
    user = User(
        email="nurse@test.com",
        username="nurse_williams",
        full_name="Mary Williams",
        role=UserRole.NURSE,
        tenant_id=test_tenant.id,
        hashed_password=get_password_hash("nurse123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_receptionist(db: Session, test_tenant) -> User:
    """Crée un réceptionniste"""
    user = User(
        email="receptionist@test.com",
        username="receptionist",
        full_name="Bob Johnson",
        role=UserRole.RECEPTIONIST,
        tenant_id=test_tenant.id,
        hashed_password=get_password_hash("receptionist123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================================
# PATIENT FIXTURES
# ============================================================================


@pytest.fixture
def test_patient(db: Session, test_tenant) -> Patient:
    """Crée un patient de test"""
    patient = Patient(
        first_name="Alice",
        last_name="Doe",
        birth_date="1990-05-15",
        gender="female",
        email="alice.doe@email.com",
        phone="+1234567892",
        address="456 Patient Street",
        tenant_id=test_tenant.id,
        status="active",
        blood_type="A+",
        allergies=["Penicillin"],
        emergency_contact_name="Bob Doe",
        emergency_contact_phone="+1234567893",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@pytest.fixture
def test_patient_2(db: Session, test_tenant) -> Patient:
    """Crée un second patient"""
    patient = Patient(
        first_name="Charlie",
        last_name="Brown",
        birth_date="1985-10-20",
        gender="male",
        email="charlie.brown@email.com",
        phone="+1234567894",
        tenant_id=test_tenant.id,
        status="active",
        blood_type="O+",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@pytest.fixture
def test_patients_bulk(db: Session, test_tenant) -> list[Patient]:
    """Crée 10 patients pour les tests en masse"""
    patients = []

    for i in range(10):
        patient = Patient(
            first_name=f"Patient{i}",
            last_name=f"Test{i}",
            birth_date=f"198{i % 10}-01-01",
            gender="male" if i % 2 == 0 else "female",
            email=f"patient{i}@test.com",
            tenant_id=test_tenant.id,
            status="active",
        )
        db.add(patient)
        patients.append(patient)

    db.commit()

    for patient in patients:
        db.refresh(patient)

    return patients


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================


@pytest.fixture
def auth_headers_super_admin(test_super_admin) -> dict:
    """Headers d'authentification pour super admin"""
    # En production, générer un vrai JWT token
    # Pour les tests, utiliser un mock
    return {
        "Authorization": f"Bearer mock_token_superadmin_{test_super_admin.id}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_admin(test_admin) -> dict:
    """Headers d'authentification pour admin"""
    return {
        "Authorization": f"Bearer mock_token_admin_{test_admin.id}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_doctor(test_doctor) -> dict:
    """Headers d'authentification pour médecin"""
    return {
        "Authorization": f"Bearer mock_token_doctor_{test_doctor.id}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_doctor_2(test_doctor_2) -> dict:
    """Headers d'authentification pour second médecin"""
    return {
        "Authorization": f"Bearer mock_token_doctor2_{test_doctor_2.id}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_nurse(test_nurse) -> dict:
    """Headers d'authentification pour infirmière"""
    return {
        "Authorization": f"Bearer mock_token_nurse_{test_nurse.id}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_receptionist(test_receptionist) -> dict:
    """Headers d'authentification pour réceptionniste"""
    return {
        "Authorization": f"Bearer mock_token_receptionist_{test_receptionist.id}",
        "Content-Type": "application/json",
    }


# ============================================================================
# FILE FIXTURES
# ============================================================================


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Retourne des bytes d'un PDF minimal valide"""
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
190
%%EOF"""


@pytest.fixture
def sample_image_png_bytes() -> bytes:
    """Retourne des bytes d'une image PNG 1x1 pixel"""
    # PNG 1x1 transparent
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"


@pytest.fixture
def sample_image_jpeg_bytes() -> bytes:
    """Retourne des bytes d'une image JPEG minimale"""
    # JPEG minimal
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xff\xd9"


# ============================================================================
# UTILITY FIXTURES
# ============================================================================


@pytest.fixture
def mock_email_service():
    """Mock du service d'envoi d'email"""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.send_email.return_value = True
    return mock


@pytest.fixture
def mock_sms_service():
    """Mock du service d'envoi de SMS"""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.send_sms.return_value = True
    return mock


@pytest.fixture
def mock_celery_task():
    """Mock pour les tâches Celery"""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.delay.return_value = MagicMock(id="mock-task-id")
    return mock


@pytest.fixture
def temp_upload_dir(tmp_path):
    """Crée un répertoire temporaire pour les uploads"""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return str(upload_dir)


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, temp_upload_dir):
    """Configure l'environnement de test"""
    # Override des variables d'environnement pour les tests
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("DOCUMENTS_UPLOAD_DIR", temp_upload_dir)
    monkeypatch.setenv("MAX_DOCUMENT_SIZE", str(50 * 1024 * 1024))  # 50 MB
    monkeypatch.setenv("ENABLE_RATE_LIMITING", "false")  # Désactiver pour les tests


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================


@pytest.fixture
def benchmark_timer():
    """Fixture pour mesurer les performances"""
    import time

    class BenchmarkTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return BenchmarkTimer()


# ============================================================================
# MARKERS CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """Configure les markers personnalisés"""
    config.addinivalue_line(
        "markers", "slow: marque les tests lents (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marque les tests d'intégration")
    config.addinivalue_line("markers", "unit: marque les tests unitaires")
    config.addinivalue_line("markers", "api: marque les tests d'API")
    config.addinivalue_line("markers", "security: marque les tests de sécurité")
    config.addinivalue_line("markers", "performance: marque les tests de performance")
    config.addinivalue_line(
        "markers", "smoke: smoke tests that require a running server"
    )


# ============================================================================
# HOOKS
# ============================================================================


def pytest_collection_modifyitems(config, items):
    """Modifie les items de collection pour ajouter automatiquement des markers"""
    for item in items:
        # Ajouter marker 'unit' par défaut si aucun autre marker
        if not any(
            marker in item.keywords
            for marker in ["integration", "api", "slow", "performance"]
        ):
            item.add_marker(pytest.mark.unit)

        # Marquer automatiquement les tests contenant 'api' dans le nom
        if "api" in item.nodeid.lower() or "endpoint" in item.nodeid.lower():
            item.add_marker(pytest.mark.api)

        # Marquer les tests de sécurité
        if "security" in item.nodeid.lower() or "auth" in item.nodeid.lower():
            item.add_marker(pytest.mark.security)


@pytest.fixture(scope="session")
def test_coverage_threshold():
    """Seuil de couverture de code requis"""
    return 90.0  # 90% de couverture minimum
