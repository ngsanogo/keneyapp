# Plan d'Actions Correctives - KeneyApp
## Suite à l'Audit Complet de Novembre 2025

**Date** : 10 novembre 2025  
**Priorité** : Implémentation séquentielle par priorité  
**Responsable** : Équipe Développement KeneyApp

---

## 📋 Vue d'Ensemble

Ce document détaille les actions correctives concrètes à implémenter suite à l'audit complet du dépôt. Les actions sont priorisées par criticité et impact.

### Résumé des Actions

| Priorité | Actions | Effort Total | Deadline |
|----------|---------|--------------|----------|
| 🔴 P1 - CRITIQUE | 2 actions | 24-32h | < 1 semaine |
| 🟠 P2 - HAUTE | 3 actions | 18h | < 2 semaines |
| 🟡 P3 - MOYENNE | 3 actions | 36h | < 1 mois |
| 🟢 P4 - BASSE | 2 actions | 44h | Amélioration continue |

**Total Effort Estimé** : 122-130 heures (~16-17 jours-personne)

---

## 🔴 PRIORITÉ 1 - CRITIQUE (< 1 semaine)

### Action 1.1 : Migration Librairie Cryptographique

**Problème** : Utilisation de PyCrypto/pycryptodome (deprecated, vulnérabilités non patchées)

**Impact** : 
- 🔴 Sécurité : Vulnérabilités connues
- 🔴 Conformité : Non-conforme standards HDS/FIPS
- 🔴 Maintenance : Pas de support sécurité

**Solution** : Migration vers `cryptography` (library officielle Python)

#### Étapes Détaillées

**1. Mise à jour requirements.txt**
```bash
# Remplacer
pycryptodome==3.21.0

# Par
cryptography==41.0.7
```

**2. Migration app/core/encryption.py**

```python
# AVANT (À REMPLACER)
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2

# APRÈS (NOUVEAU)
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64

class DataEncryption:
    """PHI data encryption using AES-256-GCM with cryptography library."""
    
    def __init__(self, key: bytes):
        """Initialize with 256-bit key."""
        if len(key) != 32:  # 256 bits
            raise ValueError("Key must be 32 bytes for AES-256")
        self.key = key
    
    def encrypt(self, plaintext: bytes) -> dict:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            plaintext: Data to encrypt
            
        Returns:
            dict: {
                'iv': base64-encoded IV (12 bytes for GCM),
                'ciphertext': base64-encoded encrypted data,
                'tag': base64-encoded authentication tag (16 bytes)
            }
        """
        # Generate random IV (96 bits recommended for GCM)
        iv = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        # Return IV, ciphertext, and authentication tag
        return {
            'iv': base64.b64encode(iv).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'tag': base64.b64encode(encryptor.tag).decode('utf-8')
        }
    
    def decrypt(self, encrypted_data: dict) -> bytes:
        """
        Decrypt AES-256-GCM encrypted data.
        
        Args:
            encrypted_data: Dict with 'iv', 'ciphertext', 'tag'
            
        Returns:
            bytes: Decrypted plaintext
            
        Raises:
            ValueError: If authentication fails
        """
        # Decode from base64
        iv = base64.b64decode(encrypted_data['iv'])
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        tag = base64.b64decode(encrypted_data['tag'])
        
        # Create cipher with tag for authentication
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt and verify
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext

def derive_key_from_password(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """
    Derive encryption key from password using PBKDF2.
    
    Args:
        password: User password
        salt: Salt (generated if None)
        
    Returns:
        tuple: (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits
        salt=salt,
        iterations=100000,  # OWASP recommendation
        backend=default_backend()
    )
    
    key = kdf.derive(password.encode('utf-8'))
    
    return key, salt
```

**3. Mise à jour app/services/patient_security.py**

```python
# Adapter les appels à la nouvelle API
from app.core.encryption import DataEncryption, derive_key_from_password
from app.core.config import settings

def get_encryption_instance() -> DataEncryption:
    """Get encryption instance with app key."""
    # Use environment variable or secure key storage
    key = settings.ENCRYPTION_KEY.encode('utf-8')[:32]  # Ensure 32 bytes
    return DataEncryption(key)

def encrypt_patient_payload(data: dict) -> dict:
    """Encrypt sensitive patient data fields."""
    encryptor = get_encryption_instance()
    encrypted_data = data.copy()
    
    sensitive_fields = [
        'medical_history', 
        'allergies', 
        'emergency_contact',
        'emergency_phone',
        'address'
    ]
    
    for field in sensitive_fields:
        if field in encrypted_data and encrypted_data[field]:
            plaintext = str(encrypted_data[field]).encode('utf-8')
            encrypted = encryptor.encrypt(plaintext)
            encrypted_data[field] = encrypted  # Store as dict
    
    return encrypted_data

def decrypt_patient_field(encrypted_field: dict) -> str:
    """Decrypt a single patient field."""
    if not encrypted_field:
        return None
        
    encryptor = get_encryption_instance()
    try:
        decrypted_bytes = encryptor.decrypt(encrypted_field)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        # Log error, return encrypted or None
        return None
```

**4. Tests exhaustifs**

```python
# tests/test_encryption_migration.py

import pytest
from app.core.encryption import DataEncryption, derive_key_from_password

class TestCryptographyMigration:
    """Test new cryptography library implementation."""
    
    def test_encryption_decryption_cycle(self):
        """Test basic encrypt/decrypt cycle."""
        key = b'0' * 32  # 256-bit key
        encryptor = DataEncryption(key)
        
        plaintext = b"Sensitive patient data"
        encrypted = encryptor.encrypt(plaintext)
        
        # Verify structure
        assert 'iv' in encrypted
        assert 'ciphertext' in encrypted
        assert 'tag' in encrypted
        
        # Decrypt
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_authentication_tag_verification(self):
        """Test GCM authentication tag prevents tampering."""
        key = b'0' * 32
        encryptor = DataEncryption(key)
        
        plaintext = b"Original data"
        encrypted = encryptor.encrypt(plaintext)
        
        # Tamper with ciphertext
        tampered = encrypted.copy()
        tampered['ciphertext'] = tampered['ciphertext'][:-4] + 'XXXX'
        
        # Should raise authentication error
        with pytest.raises(Exception):
            encryptor.decrypt(tampered)
    
    def test_key_derivation(self):
        """Test PBKDF2 key derivation."""
        password = "strong_password_123"
        key1, salt = derive_key_from_password(password)
        
        # Same password, same salt = same key
        key2, _ = derive_key_from_password(password, salt)
        assert key1 == key2
        
        # Different salt = different key
        key3, _ = derive_key_from_password(password)
        assert key1 != key3
    
    def test_patient_payload_encryption(self):
        """Test patient data encryption workflow."""
        from app.services.patient_security import (
            encrypt_patient_payload,
            decrypt_patient_field
        )
        
        patient_data = {
            'name': 'John Doe',  # Not encrypted
            'medical_history': 'Diabetes Type 2',  # Encrypted
            'allergies': 'Penicillin'  # Encrypted
        }
        
        encrypted = encrypt_patient_payload(patient_data)
        
        # Name unchanged
        assert encrypted['name'] == 'John Doe'
        
        # Sensitive fields encrypted
        assert isinstance(encrypted['medical_history'], dict)
        assert 'iv' in encrypted['medical_history']
        
        # Decrypt and verify
        decrypted_history = decrypt_patient_field(encrypted['medical_history'])
        assert decrypted_history == 'Diabetes Type 2'
```

**5. Migration données existantes**

```python
# scripts/migrate_encryption.py
"""
Script de migration des données chiffrées existantes.
À exécuter en maintenance pour re-chiffrer avec nouvelle lib.
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.patient import Patient
from app.services.patient_security import encrypt_patient_payload

def migrate_patient_encryption():
    """Re-encrypt all patient data with new library."""
    db: Session = SessionLocal()
    
    try:
        patients = db.query(Patient).all()
        
        for patient in patients:
            # Decrypt with old library (if needed)
            # Then re-encrypt with new library
            # This depends on your current data format
            
            print(f"Migrating patient {patient.id}")
            # Update patient with new encryption
            # db.commit()
        
        print(f"Migration complete: {len(patients)} patients")
        
    finally:
        db.close()

if __name__ == "__main__":
    # Run with caution in production
    # Backup database first!
    migrate_patient_encryption()
```

**6. Documentation**

```bash
# Mettre à jour docs/ENCRYPTION_GUIDE.md
# Ajouter section "Migration Notes"
# Documenter nouvelle API encryption
```

#### Checklist Validation

- [ ] `requirements.txt` mis à jour
- [ ] `app/core/encryption.py` migré
- [ ] `app/services/patient_security.py` adapté
- [ ] Tests unitaires écrits et passent
- [ ] Tests intégration PHI encryption passent
- [ ] Script migration données préparé
- [ ] Documentation mise à jour
- [ ] Review de sécurité effectuée
- [ ] Déployé en staging et validé
- [ ] Backup database avant prod
- [ ] Migration prod effectuée
- [ ] Monitoring post-migration (24h)

**Effort Estimé** : 8 heures  
**Deadline** : J+3 maximum  
**Criticité** : 🔴 BLOQUANT

---

### Action 1.2 : Tests Modules Critiques - Appointments

**Problème** : Coverage 35% pour `app/routers/appointments.py` (74 lignes non testées)

**Objectif** : Passer à 70%+ coverage

#### Tests à Implémenter

```python
# tests/test_routers_appointments_complete.py

import pytest
from fastapi import status
from app.models.user import UserRole

class TestAppointmentsCompleteCoverage:
    """Complete test coverage for appointments router."""
    
    def test_create_appointment_doctor_role(self, client, doctor_token, patient_fixture):
        """Doctor can create appointments."""
        headers = {"Authorization": f"Bearer {doctor_token}"}
        
        appointment_data = {
            "patient_id": patient_fixture.id,
            "doctor_id": 1,
            "scheduled_at": "2025-12-01T10:00:00",
            "reason": "Annual checkup",
            "status": "scheduled"
        }
        
        response = client.post(
            "/api/v1/appointments/",
            json=appointment_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["reason"] == "Annual checkup"
        assert data["status"] == "scheduled"
    
    def test_create_appointment_receptionist_role(self, client, receptionist_token):
        """Receptionist can create appointments."""
        # Similar to doctor test
        pass
    
    def test_create_appointment_unauthorized_role(self, client, nurse_token):
        """Nurse cannot create appointments (RBAC test)."""
        headers = {"Authorization": f"Bearer {nurse_token}"}
        
        appointment_data = {
            "patient_id": 1,
            "doctor_id": 1,
            "scheduled_at": "2025-12-01T10:00:00",
            "reason": "Test"
        }
        
        response = client.post(
            "/api/v1/appointments/",
            json=appointment_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_appointments_pagination(self, client, admin_token):
        """Test appointment list pagination."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create 25 appointments
        for i in range(25):
            # Create appointment...
            pass
        
        # Test page 1
        response = client.get(
            "/api/v1/appointments/?page=1&per_page=10",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        
        # Test page 2
        response = client.get(
            "/api/v1/appointments/?page=2&per_page=10",
            headers=headers
        )
        assert len(response.json()["items"]) == 10
    
    def test_update_appointment_status(self, client, doctor_token, appointment_fixture):
        """Test appointment status update."""
        headers = {"Authorization": f"Bearer {doctor_token}"}
        
        update_data = {"status": "completed"}
        
        response = client.patch(
            f"/api/v1/appointments/{appointment_fixture.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
    
    def test_cancel_appointment(self, client, doctor_token, appointment_fixture):
        """Test appointment cancellation."""
        # Test status change to cancelled
        pass
    
    def test_appointment_not_found(self, client, admin_token):
        """Test 404 for non-existent appointment."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get(
            "/api/v1/appointments/99999",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_appointment_date_validation(self, client, doctor_token):
        """Test validation for past dates."""
        headers = {"Authorization": f"Bearer {doctor_token}"}
        
        invalid_data = {
            "patient_id": 1,
            "doctor_id": 1,
            "scheduled_at": "2020-01-01T10:00:00",  # Past date
            "reason": "Test"
        }
        
        response = client.post(
            "/api/v1/appointments/",
            json=invalid_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_appointment_cache_invalidation(self, client, doctor_token, redis_client):
        """Test cache invalidation on appointment creation."""
        # Create appointment
        # Verify cache keys cleared
        pass
    
    def test_appointment_audit_logging(self, client, doctor_token, db):
        """Test audit logs created for appointment operations."""
        # Create appointment
        # Query audit_logs table
        # Verify CREATE event logged
        pass
```

**Effort Estimé** : 8 heures  
**Deadline** : J+5

---

## 🟠 PRIORITÉ 2 - HAUTE (< 2 semaines)

### Action 2.1 : Tests Prescriptions (39% → 70%)

#### Tests Complets Prescriptions

```python
# tests/test_routers_prescriptions_complete.py

class TestPrescriptionsComplete:
    """Complete prescription workflow tests."""
    
    def test_create_prescription_with_atc_code(self):
        """Test prescription creation with ATC medication code."""
        pass
    
    def test_prescription_drug_interactions_check(self):
        """Test drug interaction validation."""
        pass
    
    def test_prescription_refill_workflow(self):
        """Test prescription refill process."""
        pass
    
    def test_prescription_rbac_doctor_only(self):
        """Only doctors can create prescriptions."""
        pass
    
    def test_prescription_patient_history(self):
        """Test listing patient prescription history."""
        pass
```

**Effort Estimé** : 8 heures

### Action 2.2 : Tests Lab Results (37% → 70%)

```python
# tests/test_routers_lab_complete.py

class TestLabResultsComplete:
    """Complete lab results tests."""
    
    def test_create_lab_result_with_loinc(self):
        """Test lab result with LOINC code."""
        pass
    
    def test_lab_result_validation_service(self):
        """Test biomedical validation rules."""
        pass
    
    def test_lab_result_critical_values_alert(self):
        """Test alerts for critical lab values."""
        pass
```

**Effort Estimé** : 6 heures

### Action 2.3 : Documentation Docstrings

**Action** : Ajouter docstrings Google-style à toutes les fonctions publiques

```python
def example_function(param1: str, param2: int) -> dict:
    """
    Brief description of what the function does.
    
    More detailed explanation if needed. Explain the algorithm,
    business logic, or any important considerations.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        dict: Description of return value with structure:
            - key1 (str): Description
            - key2 (int): Description
            
    Raises:
        ValueError: When param1 is empty
        DatabaseError: When database connection fails
        
    Example:
        >>> result = example_function("test", 42)
        >>> print(result["key1"])
        'test'
    """
    pass
```

**Cibles** :
- `app/services/*.py` : Toutes fonctions publiques
- `app/routers/*.py` : Endpoints principaux
- `app/core/*.py` : Utilities et helpers

**Effort Estimé** : 4 heures

---

## 🟡 PRIORITÉ 3 - MOYENNE (< 1 mois)

### Action 3.1 : Tests OAuth (33% → 70%)

Tests flows Google/Microsoft/Okta, error handling, token exchange.

**Effort Estimé** : 6 heures

### Action 3.2 : Tests Messaging Service (28% → 70%)

Tests encryption/decryption, threading, notifications.

**Effort Estimé** : 8 heures

### Action 3.3 : Tests Celery Tasks (34% → 70%)

Tests appointment reminders, report generation, cleanup.

**Effort Estimé** : 8 heures

---

## 🟢 PRIORITÉ 4 - BASSE (Amélioration Continue)

### Action 4.1 : Performance Testing

Implémenter tests de charge avec locust.

**Effort Estimé** : 16 heures

### Action 4.2 : Frontend E2E Tests

Tests end-to-end avec Cypress ou Playwright.

**Effort Estimé** : 24 heures

---

## 📊 Tableau de Suivi

| Action | Priorité | Statut | Assigné | Début | Fin | Notes |
|--------|----------|--------|---------|-------|-----|-------|
| Migration crypto | P1 | 🔴 À faire | - | - | - | BLOQUANT |
| Tests appointments | P1 | 🔴 À faire | - | - | - | Critique |
| Tests prescriptions | P2 | ⚪ Planifié | - | - | - | - |
| Tests lab | P2 | ⚪ Planifié | - | - | - | - |
| Docstrings | P2 | ⚪ Planifié | - | - | - | - |
| Tests OAuth | P3 | ⚪ Planifié | - | - | - | - |
| Tests messaging | P3 | ⚪ Planifié | - | - | - | - |
| Tests tasks | P3 | ⚪ Planifié | - | - | - | - |
| Performance tests | P4 | ⚪ Backlog | - | - | - | - |
| Frontend E2E | P4 | ⚪ Backlog | - | - | - | - |

---

## 🎯 Objectifs Mesurables

### Coverage Targets

**Situation actuelle** : 75.31%

**Objectifs par Sprint** :
- Sprint 1 (semaine 1) : 75% → 78% (tests appointments)
- Sprint 2 (semaine 2) : 78% → 82% (tests prescriptions + lab)
- Sprint 3 (semaine 3-4) : 82% → 85% (tests OAuth + messaging + tasks)

**Target Final** : **85%+ coverage**

### Security Metrics

- ✅ Zero vulnérabilités CRITICAL/HIGH en production
- ✅ Migration cryptography complétée
- ✅ Audit logging 100% des opérations sensibles
- ✅ RBAC enforcement 100% endpoints

---

## 📞 Support et Questions

Pour toute question sur ce plan d'actions :
- 📧 Email : contact@isdataconsulting.com
- 📖 Documentation : `docs/`
- 🐛 Issues : GitHub Issues

---

**Date de création** : 10 novembre 2025  
**Dernière mise à jour** : 10 novembre 2025  
**Responsable** : Équipe KeneyApp
