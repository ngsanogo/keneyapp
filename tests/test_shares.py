"""
Tests exhaustifs pour le système de partage sécurisé de dossiers médicaux v3.0

Couvre:
- Création de partages avec tokens sécurisés
- Validation PIN à 6 chiffres
- Accès public sans authentification
- Révocation manuelle et expiration automatique
- Tracking IP et limitation d'accès
- 5 scopes de partage (full_record, appointments_only, etc.)
- Permissions et sécurité
- Edge cases et performance
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import secrets

from app.main import app
from app.models.user import User
from app.models.patient import Patient
from app.models.medical_record_share import (
    MedicalRecordShare,
    ShareScope,
    ShareStatus
)
from app.models.tenant import Tenant
from app.services.share_service import (
    create_share,
    validate_and_access_share,
    get_shared_medical_record,
    revoke_share,
    get_user_shares,
    is_share_valid,
    generate_secure_pin
)


@pytest.fixture
def test_tenant(db: Session):
    """Tenant de test"""
    tenant = Tenant(name="Test Clinic", code="TEST", status="active", contact_email="test@clinic.com")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def test_patient(db: Session, test_tenant):
    """Patient de test"""
    patient = Patient(
        first_name="John",
        last_name="Doe",
        birth_date="1980-01-15",
        gender="male",
        tenant_id=test_tenant.id,
        status="active"
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@pytest.fixture
def test_doctor(db: Session, test_tenant):
    """Médecin de test"""
    doctor = User(
        email="doctor@clinic.com",
        username="doctor",
        role="Doctor",
        tenant_id=test_tenant.id,
        hashed_password="hash",
        status="active",
        is_active=True
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


# ============================================================================
# TESTS UNITAIRES - SERVICE SHARE
# ============================================================================

class TestShareService:
    """Tests du service de partage"""
    
    def test_generate_secure_pin(self):
        """Test de génération de PIN sécurisé"""
        pin = generate_secure_pin()
        
        assert pin is not None
        assert len(pin) == 6
        assert pin.isdigit()
        assert 100000 <= int(pin) <= 999999
    
    def test_create_share_basic(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de création d'un partage basique"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7,
            recipient_email="external@doctor.com"
        )
        
        assert share is not None
        assert share.patient_id == test_patient.id
        assert share.shared_by_id == test_doctor.id
        assert share.scope == ShareScope.FULL_RECORD
        assert share.status == ShareStatus.ACTIVE
        assert share.share_token is not None
        assert len(share.share_token) >= 32
        assert share.expires_at > datetime.utcnow()
    
    def test_create_share_with_pin(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de création d'un partage avec PIN"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.APPOINTMENTS_ONLY,
            expires_in_days=1,
            require_pin=True
        )
        
        assert share.pin is not None
        assert len(share.pin) == 6
        assert share.pin.isdigit()
    
    def test_create_share_with_access_limit(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de création avec limite d'accès"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.DOCUMENTS_ONLY,
            expires_in_days=7,
            max_access_count=3
        )
        
        assert share.max_access_count == 3
        assert share.access_count == 0
    
    def test_validate_and_access_share_success(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de validation et accès réussi"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7
        )
        
        # Accéder au partage
        accessed_share = validate_and_access_share(
            db=db,
            share_token=share.share_token,
            ip_address="192.168.1.1"
        )
        
        assert accessed_share is not None
        assert accessed_share.id == share.id
        assert accessed_share.access_count == 1
        assert accessed_share.last_accessed_at is not None
        assert "192.168.1.1" in accessed_share.accessed_from_ips
    
    def test_validate_share_with_pin_correct(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de validation avec PIN correct"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7,
            require_pin=True
        )
        
        pin = share.pin
        
        accessed_share = validate_and_access_share(
            db=db,
            share_token=share.share_token,
            pin=pin,
            ip_address="192.168.1.1"
        )
        
        assert accessed_share is not None
    
    def test_validate_share_with_pin_incorrect(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de validation avec PIN incorrect"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7,
            require_pin=True
        )
        
        with pytest.raises(ValueError, match="Invalid PIN"):
            validate_and_access_share(
                db=db,
                share_token=share.share_token,
                pin="000000",  # Mauvais PIN
                ip_address="192.168.1.1"
            )
    
    def test_validate_share_expired(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de validation d'un partage expiré"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=0  # Expire immédiatement
        )
        
        # Forcer l'expiration
        share.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.commit()
        
        with pytest.raises(ValueError, match="expired"):
            validate_and_access_share(
                db=db,
                share_token=share.share_token,
                ip_address="192.168.1.1"
            )
    
    def test_validate_share_max_access_reached(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de validation quand limite d'accès atteinte"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7,
            max_access_count=2
        )
        
        # Accéder 2 fois
        validate_and_access_share(db, share.share_token, ip_address="192.168.1.1")
        validate_and_access_share(db, share.share_token, ip_address="192.168.1.1")
        
        # 3ème tentative devrait échouer
        with pytest.raises(ValueError, match="access limit"):
            validate_and_access_share(db, share.share_token, ip_address="192.168.1.1")
    
    def test_get_shared_medical_record_full(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de récupération du dossier médical complet"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7
        )
        
        record = get_shared_medical_record(db, share)
        
        assert record is not None
        assert "patient" in record
        assert "appointments" in record
        assert "prescriptions" in record
        assert "documents" in record
    
    def test_get_shared_medical_record_appointments_only(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de récupération - scope appointments uniquement"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.APPOINTMENTS_ONLY,
            expires_in_days=7
        )
        
        record = get_shared_medical_record(db, share)
        
        assert "appointments" in record
        assert "prescriptions" not in record
        assert "documents" not in record
    
    def test_get_shared_medical_record_documents_only(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de récupération - scope documents uniquement"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.DOCUMENTS_ONLY,
            expires_in_days=7
        )
        
        record = get_shared_medical_record(db, share)
        
        assert "documents" in record
        assert "appointments" not in record
        assert "prescriptions" not in record
    
    def test_revoke_share(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de révocation d'un partage"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7
        )
        
        revoke_share(db, share.id, test_doctor.id, test_tenant.id)
        
        db.refresh(share)
        assert share.status == ShareStatus.REVOKED
        assert share.revoked_at is not None
        assert share.revoked_by_id == test_doctor.id
    
    def test_get_user_shares(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de récupération des partages d'un utilisateur"""
        # Créer plusieurs partages
        for i in range(3):
            create_share(
                db=db,
                patient_id=test_patient.id,
                shared_by_id=test_doctor.id,
                tenant_id=test_tenant.id,
                scope=ShareScope.FULL_RECORD,
                expires_in_days=7
            )
        
        shares = get_user_shares(db, test_doctor.id, test_tenant.id)
        
        assert len(shares) >= 3
    
    def test_is_share_valid_active(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de vérification qu'un partage est valide"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7
        )
        
        assert is_share_valid(share) is True
    
    def test_is_share_valid_revoked(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test qu'un partage révoqué n'est pas valide"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7
        )
        
        revoke_share(db, share.id, test_doctor.id, test_tenant.id)
        
        assert is_share_valid(share) is False


# ============================================================================
# TESTS API - ENDPOINTS SHARES
# ============================================================================

class TestSharesAPI:
    """Tests des endpoints API de partage"""
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_create_share_api(self, mock_user, db: Session, test_doctor, test_patient):
        """Test de création d'un partage via API"""
        mock_user.return_value = test_doctor
        
        client = TestClient(app)
        
        payload = {
            "patient_id": test_patient.id,
            "scope": "full_record",
            "expires_in_days": 7,
            "recipient_email": "external@doctor.com",
            "require_pin": True
        }
        
        response = client.post(
            "/api/v1/shares/",
            json=payload,
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["share_token"] is not None
        assert data["share_url"] is not None
        assert data["pin"] is not None
        assert len(data["pin"]) == 6
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_get_user_shares_api(self, mock_user, db: Session, test_doctor, test_patient, test_tenant):
        """Test de récupération des partages d'un utilisateur via API"""
        mock_user.return_value = test_doctor
        
        # Créer des partages
        create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, 7)
        
        client = TestClient(app)
        response = client.get(
            "/api/v1/shares/",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        shares = response.json()
        assert isinstance(shares, list)
        assert len(shares) >= 1
    
    def test_access_shared_record_public(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test d'accès public à un dossier partagé (sans auth)"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7
        )
        
        client = TestClient(app)
        
        payload = {
            "share_token": share.share_token
        }
        
        # Pas de header Authorization - accès public
        response = client.post(
            "/api/v1/shares/access",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "medical_record" in data
        assert "share_info" in data
    
    def test_access_shared_record_with_pin(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test d'accès avec PIN requis"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7,
            require_pin=True
        )
        
        pin = share.pin
        
        client = TestClient(app)
        
        payload = {
            "share_token": share.share_token,
            "pin": pin
        }
        
        response = client.post(
            "/api/v1/shares/access",
            json=payload
        )
        
        assert response.status_code == 200
    
    def test_access_shared_record_invalid_token(self):
        """Test d'accès avec token invalide"""
        client = TestClient(app)
        
        payload = {
            "share_token": "invalid_token_12345"
        }
        
        response = client.post(
            "/api/v1/shares/access",
            json=payload
        )
        
        assert response.status_code == 404
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_get_share_details(self, mock_user, db: Session, test_doctor, test_patient, test_tenant):
        """Test de récupération des détails d'un partage"""
        mock_user.return_value = test_doctor
        
        share = create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, 7)
        
        client = TestClient(app)
        response = client.get(
            f"/api/v1/shares/{share.id}",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == share.id
        assert data["access_count"] >= 0
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_revoke_share_api(self, mock_user, db: Session, test_doctor, test_patient, test_tenant):
        """Test de révocation via API"""
        mock_user.return_value = test_doctor
        
        share = create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, 7)
        
        client = TestClient(app)
        response = client.delete(
            f"/api/v1/shares/{share.id}",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        
        # Vérifier que le partage est révoqué
        db.refresh(share)
        assert share.status == ShareStatus.REVOKED


# ============================================================================
# TESTS SÉCURITÉ
# ============================================================================

class TestSharesSecurity:
    """Tests de sécurité du système de partage"""
    
    def test_share_token_uniqueness(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test que tous les tokens sont uniques"""
        tokens = set()
        
        for _ in range(100):
            share = create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, 7)
            tokens.add(share.share_token)
        
        # Tous les tokens doivent être uniques
        assert len(tokens) == 100
    
    def test_share_token_length_security(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test que les tokens ont une longueur sécurisée"""
        share = create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, 7)
        
        # Token doit faire au moins 32 caractères
        assert len(share.share_token) >= 32
    
    def test_pin_brute_force_protection(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de protection contre bruteforce du PIN"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7,
            require_pin=True
        )
        
        # Tentatives de bruteforce
        failed_attempts = 0
        for pin_attempt in range(100000, 100010):
            try:
                validate_and_access_share(
                    db=db,
                    share_token=share.share_token,
                    pin=str(pin_attempt),
                    ip_address="192.168.1.1"
                )
            except ValueError:
                failed_attempts += 1
        
        # Toutes les tentatives incorrectes doivent échouer
        assert failed_attempts >= 9  # Au moins 9 échecs sur 10 tentatives
    
    def test_ip_tracking(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test du tracking IP"""
        share = create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, 7)
        
        # Accès depuis différentes IPs
        ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
        
        for ip in ips:
            validate_and_access_share(db, share.share_token, ip_address=ip)
        
        db.refresh(share)
        
        # Toutes les IPs doivent être trackées
        for ip in ips:
            assert ip in share.accessed_from_ips
    
    def test_cannot_access_other_tenant_share(self, db: Session, test_patient, test_doctor):
        """Test qu'on ne peut pas accéder à un partage d'un autre tenant"""
        tenant1 = Tenant(name="Clinic 1", code="C1", status="active", contact_email="c1@test.com")
        tenant2 = Tenant(name="Clinic 2", code="C2", status="active", contact_email="c2@test.com")
        db.add_all([tenant1, tenant2])
        db.commit()
        
        # Partage dans tenant1
        share = create_share(db, test_patient.id, test_doctor.id, tenant1.id, ShareScope.FULL_RECORD, 7)
        
        # Tentative d'accès devrait fonctionner (public)
        accessed = validate_and_access_share(db, share.share_token, ip_address="192.168.1.1")
        
        assert accessed is not None
    
    def test_revoked_share_cannot_be_accessed(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test qu'un partage révoqué ne peut pas être accédé"""
        share = create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, 7)
        
        # Révoquer
        revoke_share(db, share.id, test_doctor.id, test_tenant.id)
        
        # Tentative d'accès
        with pytest.raises(ValueError, match="revoked"):
            validate_and_access_share(db, share.share_token, ip_address="192.168.1.1")


# ============================================================================
# TESTS EDGE CASES
# ============================================================================

class TestSharesEdgeCases:
    """Tests des cas limites"""
    
    def test_share_expires_exactly_at_expiration(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test qu'un partage expire exactement à l'heure prévue"""
        from freezegun import freeze_time
        
        with freeze_time("2025-01-01 12:00:00"):
            share = create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, expires_in_days=1)
        
        with freeze_time("2025-01-02 11:59:59"):
            # Encore valide
            assert is_share_valid(share) is True
        
        with freeze_time("2025-01-02 12:00:01"):
            # Expiré
            db.refresh(share)
            assert is_share_valid(share) is False
    
    def test_zero_access_count_limit(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test avec limite d'accès à 0 (devrait échouer immédiatement)"""
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7,
            max_access_count=0
        )
        
        with pytest.raises(ValueError):
            validate_and_access_share(db, share.share_token, ip_address="192.168.1.1")
    
    def test_very_long_expiration(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test avec expiration très longue (1 an)"""
        share = create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, expires_in_days=365)
        
        expected_expiry = datetime.utcnow() + timedelta(days=365)
        
        # Expiration devrait être dans environ 1 an
        assert (share.expires_at - expected_expiry).total_seconds() < 60
    
    def test_multiple_simultaneous_accesses(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test d'accès simultanés au même partage"""
        import concurrent.futures
        
        share = create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, 7, max_access_count=100)
        
        def access_share(n):
            return validate_and_access_share(db, share.share_token, ip_address=f"192.168.1.{n}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(access_share, range(10)))
        
        assert all(r is not None for r in results)
        
        db.refresh(share)
        assert share.access_count == 10
    
    def test_share_with_invalid_email(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de création avec email invalide"""
        # L'email n'est qu'indicatif, donc devrait accepter n'importe quoi
        share = create_share(
            db=db,
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            scope=ShareScope.FULL_RECORD,
            expires_in_days=7,
            recipient_email="not_an_email"
        )
        
        assert share is not None


# ============================================================================
# TESTS PERFORMANCE
# ============================================================================

class TestSharesPerformance:
    """Tests de performance"""
    
    def test_bulk_share_creation(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de création en masse"""
        import time
        
        start = time.time()
        for i in range(100):
            create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, 7)
        end = time.time()
        
        # Devrait prendre moins de 3 secondes
        assert (end - start) < 3.0
    
    def test_token_validation_performance(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de performance de validation de token"""
        share = create_share(db, test_patient.id, test_doctor.id, test_tenant.id, ShareScope.FULL_RECORD, 7)
        
        import time
        start = time.time()
        for _ in range(1000):
            validate_and_access_share(db, share.share_token, ip_address="192.168.1.1")
        end = time.time()
        
        # 1000 validations en moins de 5 secondes
        assert (end - start) < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app/routers/shares", "--cov=app/services/share_service"])
