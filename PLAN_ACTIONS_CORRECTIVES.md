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
| ✅ P0 - DÉJÀ FAIT | 1 action (crypto) | 0h | Complété |
| 🔴 P1 - CRITIQUE | 1 action | 8h | < 1 semaine |
| 🟠 P2 - HAUTE | 3 actions | 18h | < 2 semaines |
| 🟡 P3 - MOYENNE | 3 actions | 22h | < 1 mois |
| 🟢 P4 - BASSE | 2 actions | 40h | Amélioration continue |

**Total Effort Restant** : 88 heures (~11 jours-personne)

---

## ✅ PRIORITÉ 0 - DÉJÀ COMPLÉTÉ

### Action 0.1 : ✅ Migration Librairie Cryptographique

**État** : ✅ **COMPLÉTÉ AVANT L'AUDIT**

**Implémentation actuelle vérifiée** :
- ✅ `cryptography>=46.0.3` dans requirements.txt
- ✅ `app/core/encryption.py` utilise AESGCM moderne
- ✅ PBKDF2-HMAC-SHA256 avec 100,000 itérations (OWASP)
- ✅ AES-256-GCM avec authentification intégrée
- ✅ 11 tests passent dans `tests/test_encryption.py`
- ✅ Support Unicode et validation d'intégrité

**Code actuel** :
```python
# app/core/encryption.py - IMPLÉMENTATION MODERNE
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class DataEncryption:
    def __init__(self, key: Optional[str] = None):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"keneyapp-salt",
            iterations=100000,
            backend=default_backend(),
        )
        self.derived_key = kdf.derive(self.key.encode("utf-8"))
        self.aesgcm = AESGCM(self.derived_key)
```

**Aucune action requise** - Migration déjà complétée et testée.

---

## 🔴 PRIORITÉ 1 - CRITIQUE (< 1 semaine)

### Action 1.1 : Tests Modules Critiques - Appointments

**Problème** : Coverage 35% pour `app/routers/appointments.py` (74 lignes non testées)

**Objectif** : Passer à 70%+ coverage

**Impact** : Haute - module médical critique pour scheduling rendez-vous

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
        # Test RBAC - receptionists have permission
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
        headers = {"Authorization": f"Bearer {doctor_token}"}
        
        response = client.patch(
            f"/api/v1/appointments/{appointment_fixture.id}",
            json={"status": "cancelled"},
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    
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
    
    def test_appointment_cache_invalidation(self, client, doctor_token, redis_mock):
        """Test cache invalidation on appointment creation."""
        # Verify cache keys cleared after mutation
        pass
    
    def test_appointment_audit_logging(self, client, doctor_token, db):
        """Test audit logs created for appointment operations."""
        # Verify CREATE event logged in audit_logs table
        pass
    
    def test_list_appointments_by_date_range(self, client, admin_token):
        """Test filtering appointments by date range."""
        pass
    
    def test_list_appointments_by_patient(self, client, admin_token):
        """Test filtering appointments by patient ID."""
        pass
```

#### Checklist Validation

- [ ] 12+ tests unitaires écrits
- [ ] Tests RBAC pour tous rôles (doctor, nurse, receptionist, admin)
- [ ] Tests pagination (page 1, page 2, limites)
- [ ] Tests validation (dates passées, données invalides)
- [ ] Tests cache invalidation
- [ ] Tests audit logging
- [ ] Tests 404/403 errors
- [ ] Coverage 35% → 70%+
- [ ] Tous tests passent
- [ ] CI pipeline vert

**Effort Estimé** : 8 heures  
**Deadline** : J+5  
**Criticité** : 🔴 HAUTE

---

## 🟠 PRIORITÉ 2 - HAUTE (< 2 semaines)

### Action 2.1 : Tests Prescriptions (39% → 70%)

**Objectif** : Augmenter coverage du module prescriptions

```python
# tests/test_routers_prescriptions_complete.py

class TestPrescriptionsComplete:
    """Complete prescription workflow tests."""
    
    def test_create_prescription_with_atc_code(self, client, doctor_token):
        """Test prescription creation with ATC medication code."""
        headers = {"Authorization": f"Bearer {doctor_token}"}
        
        prescription_data = {
            "patient_id": 1,
            "medication": "Metformin",
            "atc_code": "A10BA02",  # ATC code
            "dosage": "500mg",
            "frequency": "2x/day",
            "duration": "30 days"
        }
        
        response = client.post(
            "/api/v1/prescriptions/",
            json=prescription_data,
            headers=headers
        )
        
        assert response.status_code == 201
        assert response.json()["atc_code"] == "A10BA02"
    
    def test_prescription_drug_interactions_check(self, client, doctor_token):
        """Test drug interaction validation."""
        # Test Celery task triggered for interaction check
        pass
    
    def test_prescription_refill_workflow(self, client, doctor_token):
        """Test prescription refill process."""
        pass
    
    def test_prescription_rbac_doctor_only(self, client, nurse_token):
        """Only doctors can create prescriptions."""
        headers = {"Authorization": f"Bearer {nurse_token}"}
        
        response = client.post(
            "/api/v1/prescriptions/",
            json={"patient_id": 1, "medication": "Test"},
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_prescription_patient_history(self, client, doctor_token):
        """Test listing patient prescription history."""
        pass
    
    def test_prescription_dosage_validation(self, client, doctor_token):
        """Test validation of dosage formats."""
        pass
    
    def test_prescription_expires_in_validation(self, client, doctor_token):
        """Test validation of expiration dates."""
        pass
```

**Effort Estimé** : 8 heures

### Action 2.2 : Tests Lab Results (37% → 70%)

```python
# tests/test_routers_lab_complete.py

class TestLabResultsComplete:
    """Complete lab results tests."""
    
    def test_create_lab_result_with_loinc(self, client, doctor_token):
        """Test lab result with LOINC code."""
        headers = {"Authorization": f"Bearer {doctor_token}"}
        
        lab_data = {
            "patient_id": 1,
            "test_name": "Blood Glucose",
            "loinc_code": "2339-0",  # Glucose [Mass/volume] in Blood
            "result_value": "95",
            "unit": "mg/dL",
            "reference_range": "70-100",
            "status": "final"
        }
        
        response = client.post(
            "/api/v1/lab-results/",
            json=lab_data,
            headers=headers
        )
        
        assert response.status_code == 201
        assert response.json()["loinc_code"] == "2339-0"
    
    def test_lab_result_validation_service(self, client, doctor_token):
        """Test biomedical validation rules."""
        # Test normal/abnormal flagging
        pass
    
    def test_lab_result_critical_values_alert(self, client, doctor_token):
        """Test alerts for critical lab values."""
        # Test notification triggered for critical values
        pass
    
    def test_lab_result_history_trend(self, client, doctor_token):
        """Test retrieving lab result history for trend analysis."""
        pass
```

**Effort Estimé** : 6 heures

### Action 2.3 : Documentation Docstrings

**Objectif** : Ajouter docstrings Google-style à toutes fonctions publiques

**Format standard** :
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

**Cibles prioritaires** :
- `app/services/*.py` : Toutes fonctions publiques
- `app/routers/*.py` : Endpoints principaux
- `app/core/*.py` : Utilities et helpers
- `app/fhir/*.py` : Converteurs FHIR

**Effort Estimé** : 4 heures

---

## 🟡 PRIORITÉ 3 - MOYENNE (< 1 mois)

### Action 3.1 : Tests OAuth (33% → 70%)

Tests flows Google/Microsoft/Okta, error handling, token exchange.

**Effort Estimé** : 6 heures

### Action 3.2 : Tests Messaging Service (28% → 70%)

Tests encryption/decryption messages, threading, notifications.

**Effort Estimé** : 8 heures

### Action 3.3 : Tests Celery Tasks (34% → 70%)

Tests appointment reminders, report generation, cleanup tasks.

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
| Migration crypto | P0 | ✅ Complété | - | - | - | Avant audit |
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
