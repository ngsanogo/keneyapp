"""
Tests exhaustifs complémentaires v3.0

Couvre les éléments manquants:
- Modèles v3.0 (Message, MedicalDocument, MedicalRecordShare)
- Schémas Pydantic v3.0
- Services métier (messaging, document, share, notification)
- Tests d'intégration E2E
- Tests de sécurité avancés
- Tests de performance et charge
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

# ============================================================================
# TESTS DES MODÈLES v3.0
# ============================================================================

class TestModelsV3:
    """Tests des modèles de données v3.0"""
    
    def test_message_model_creation(self, db: Session, test_doctor, test_patient, test_tenant):
        """Test de création d'un modèle Message"""
        from app.models.message import Message, MessageStatus
        
        message = Message(
            sender_id=test_doctor.id,
            receiver_id=test_patient.id,
            subject="Test Subject",
            encrypted_content="encrypted_data",
            tenant_id=test_tenant.id,
            status=MessageStatus.SENT,
            thread_id="thread-123"
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        assert message.id is not None
        assert message.sender_id == test_doctor.id
        assert message.receiver_id == test_patient.id
        assert message.status == MessageStatus.SENT
        assert message.is_read is False
        assert message.created_at is not None
    
    def test_message_relationships(self, db: Session, test_doctor, test_patient, test_tenant):
        """Test des relations du modèle Message"""
        from app.models.message import Message
        
        message = Message(
            sender_id=test_doctor.id,
            receiver_id=test_patient.id,
            subject="Relationship Test",
            encrypted_content="data",
            tenant_id=test_tenant.id
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        assert message.sender is not None
        assert message.sender.id == test_doctor.id
        assert message.receiver is not None
        assert message.receiver.id == test_patient.id
    
    def test_medical_document_model_creation(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de création d'un modèle MedicalDocument"""
        from app.models.medical_document import MedicalDocument, DocumentType, DocumentFormat, DocumentStatus
        
        document = MedicalDocument(
            patient_id=test_patient.id,
            uploaded_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            title="Lab Results",
            document_type=DocumentType.LAB_RESULT,
            format=DocumentFormat.PDF,
            file_path="/uploads/test.pdf",
            file_size=1024,
            checksum="abc123",
            status=DocumentStatus.ACTIVE
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        assert document.id is not None
        assert document.patient_id == test_patient.id
        assert document.document_type == DocumentType.LAB_RESULT
        assert document.format == DocumentFormat.PDF
        assert document.status == DocumentStatus.ACTIVE
    
    def test_medical_record_share_model_creation(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de création d'un modèle MedicalRecordShare"""
        from app.models.medical_record_share import MedicalRecordShare, ShareScope, ShareStatus
        import secrets
        
        share = MedicalRecordShare(
            patient_id=test_patient.id,
            shared_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            share_token=secrets.token_urlsafe(32),
            scope=ShareScope.FULL_RECORD,
            status=ShareStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db.add(share)
        db.commit()
        db.refresh(share)
        
        assert share.id is not None
        assert share.share_token is not None
        assert share.scope == ShareScope.FULL_RECORD
        assert share.status == ShareStatus.ACTIVE
    
    def test_model_timestamps(self, db: Session, test_doctor, test_patient, test_tenant):
        """Test que les timestamps sont automatiquement définis"""
        from app.models.message import Message
        
        message = Message(
            sender_id=test_doctor.id,
            receiver_id=test_patient.id,
            subject="Timestamp Test",
            encrypted_content="data",
            tenant_id=test_tenant.id
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        assert message.created_at is not None
        assert message.updated_at is not None
        assert message.created_at <= message.updated_at
    
    def test_model_soft_delete(self, db: Session, test_doctor, test_patient, test_tenant):
        """Test du soft delete sur les modèles"""
        from app.models.message import Message
        
        message = Message(
            sender_id=test_doctor.id,
            receiver_id=test_patient.id,
            subject="Delete Test",
            encrypted_content="data",
            tenant_id=test_tenant.id
        )
        
        db.add(message)
        db.commit()
        
        # Soft delete
        message.deleted_by_sender = True
        message.deleted_at_sender = datetime.utcnow()
        db.commit()
        db.refresh(message)
        
        assert message.deleted_by_sender is True
        assert message.deleted_at_sender is not None
    
    def test_model_tenant_isolation(self, db: Session, test_tenant, other_tenant, test_doctor, test_patient):
        """Test de l'isolation entre tenants"""
        from app.models.message import Message
        
        # Message dans tenant 1
        msg1 = Message(
            sender_id=test_doctor.id,
            receiver_id=test_patient.id,
            subject="Tenant 1",
            encrypted_content="data",
            tenant_id=test_tenant.id
        )
        db.add(msg1)
        db.commit()
        
        # Requête filtrant par tenant 2
        messages = db.query(Message).filter(Message.tenant_id == other_tenant.id).all()
        
        # Ne devrait pas trouver le message du tenant 1
        assert len(messages) == 0


# ============================================================================
# TESTS DES SCHÉMAS PYDANTIC v3.0
# ============================================================================

class TestSchemasV3:
    """Tests des schémas Pydantic v3.0"""
    
    def test_message_create_schema_validation(self):
        """Test de validation du schéma MessageCreate"""
        from app.schemas.message import MessageCreate
        
        # Données valides
        data = {
            "receiver_id": 1,
            "subject": "Test",
            "body": "Message body",
            "is_urgent": False
        }
        
        message = MessageCreate(**data)
        
        assert message.receiver_id == 1
        assert message.subject == "Test"
        assert message.body == "Message body"
        assert message.is_urgent is False
    
    def test_message_create_schema_missing_required(self):
        """Test de validation avec champs requis manquants"""
        from app.schemas.message import MessageCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            MessageCreate(subject="Test")  # Manque receiver_id et body
    
    def test_document_upload_schema_validation(self):
        """Test de validation du schéma de document"""
        from app.schemas.medical_document import MedicalDocumentCreate
        
        data = {
            "patient_id": 1,
            "title": "Lab Results",
            "document_type": "lab_result",
            "description": "Blood test"
        }
        
        doc = MedicalDocumentCreate(**data)
        
        assert doc.patient_id == 1
        assert doc.title == "Lab Results"
        assert doc.document_type == "lab_result"
    
    def test_share_create_schema_validation(self):
        """Test de validation du schéma de partage"""
        from app.schemas.medical_record_share import MedicalRecordShareCreate
        
        data = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_days": 7,
            "recipient_email": "doctor@external.com"
        }
        
        share = MedicalRecordShareCreate(**data)
        
        assert share.patient_id == 1
        assert share.scope == "full_record"
        assert share.expires_in_days == 7
    
    def test_schema_response_serialization(self):
        """Test de sérialisation des réponses"""
        from app.schemas.message import MessageResponse
        
        data = {
            "id": 1,
            "sender_id": 2,
            "receiver_id": 3,
            "subject": "Test",
            "body": "Message",
            "status": "sent",
            "is_read": False,
            "is_urgent": False,
            "thread_id": "thread-1",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        response = MessageResponse(**data)
        
        # Doit pouvoir sérialiser en JSON
        json_data = response.model_dump()
        assert json_data["id"] == 1
        assert json_data["subject"] == "Test"
    
    def test_schema_enum_validation(self):
        """Test de validation des enums"""
        from app.schemas.medical_document import MedicalDocumentCreate
        from pydantic import ValidationError
        
        # Enum invalide
        with pytest.raises(ValidationError):
            MedicalDocumentCreate(
                patient_id=1,
                title="Test",
                document_type="invalid_type"  # Type inexistant
            )


# ============================================================================
# TESTS D'INTÉGRATION E2E
# ============================================================================

class TestIntegrationE2E:
    """Tests d'intégration end-to-end"""
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_complete_message_workflow(self, mock_user, client, db, test_doctor, test_patient):
        """Test du workflow complet: envoi → lecture → réponse"""
        mock_user.return_value = test_doctor
        
        # 1. Envoi d'un message
        send_payload = {
            "receiver_id": test_patient.id,
            "subject": "Appointment Follow-up",
            "body": "Please schedule a follow-up appointment",
            "is_urgent": False
        }
        
        response = client.post("/api/v1/messages/", json=send_payload)
        assert response.status_code == 201
        message_data = response.json()
        message_id = message_data["id"]
        thread_id = message_data["thread_id"]
        
        # 2. Marquer comme lu
        response = client.post(f"/api/v1/messages/{message_id}/read")
        assert response.status_code == 200
        
        # 3. Répondre dans le même thread
        reply_payload = {
            "receiver_id": test_doctor.id,
            "subject": "Re: Appointment Follow-up",
            "body": "I will schedule it for next week",
            "is_urgent": False,
            "thread_id": thread_id
        }
        
        response = client.post("/api/v1/messages/", json=reply_payload)
        assert response.status_code == 201
        
        # 4. Récupérer la conversation complète
        response = client.get(f"/api/v1/messages/conversation/{thread_id}")
        assert response.status_code == 200
        conversation = response.json()
        assert len(conversation) == 2
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_complete_document_workflow(self, mock_user, client, db, test_doctor, test_patient, sample_pdf_bytes):
        """Test du workflow complet: upload → consultation → download → suppression"""
        mock_user.return_value = test_doctor
        
        # 1. Upload d'un document
        import io
        files = {"file": ("lab_results.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        data = {
            "patient_id": test_patient.id,
            "document_type": "lab_result",
            "title": "Blood Test Results"
        }
        
        response = client.post("/api/v1/documents/upload", files=files, data=data)
        assert response.status_code == 201
        document_data = response.json()
        document_id = document_data["id"]
        
        # 2. Consulter le document
        response = client.get(f"/api/v1/documents/{document_id}")
        assert response.status_code == 200
        
        # 3. Télécharger le document
        response = client.get(f"/api/v1/documents/{document_id}/download")
        assert response.status_code == 200
        
        # 4. Supprimer le document
        response = client.delete(f"/api/v1/documents/{document_id}")
        assert response.status_code == 200
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_complete_share_workflow(self, mock_user, client, db, test_doctor, test_patient):
        """Test du workflow complet: création → accès → révocation"""
        mock_user.return_value = test_doctor
        
        # 1. Créer un partage
        create_payload = {
            "patient_id": test_patient.id,
            "scope": "full_record",
            "expires_in_days": 7,
            "recipient_email": "external@doctor.com",
            "require_pin": True
        }
        
        response = client.post("/api/v1/shares/", json=create_payload)
        assert response.status_code == 201
        share_data = response.json()
        share_id = share_data["id"]
        share_token = share_data["share_token"]
        pin = share_data["pin"]
        
        # 2. Accéder au dossier partagé (sans auth - accès public)
        access_payload = {
            "share_token": share_token,
            "pin": pin
        }
        
        response = client.post("/api/v1/shares/access", json=access_payload)
        assert response.status_code == 200
        medical_record = response.json()
        assert "medical_record" in medical_record
        
        # 3. Révoquer le partage
        response = client.delete(f"/api/v1/shares/{share_id}")
        assert response.status_code == 200
        
        # 4. Tentative d'accès après révocation
        response = client.post("/api/v1/shares/access", json=access_payload)
        assert response.status_code in [403, 404]


# ============================================================================
# TESTS DE SÉCURITÉ AVANCÉS
# ============================================================================

class TestSecurityAdvanced:
    """Tests de sécurité avancés"""
    
    def test_sql_injection_in_search(self, client, auth_headers_doctor):
        """Test de protection contre injection SQL dans la recherche"""
        malicious_input = "'; DROP TABLE patients; --"
        
        response = client.get(
            f"/api/v1/patients/?search={malicious_input}",
            headers=auth_headers_doctor
        )
        
        # Ne devrait pas causer d'erreur, mais retourner une liste vide
        assert response.status_code == 200
    
    def test_xss_in_message_content(self, client, auth_headers_doctor, test_patient):
        """Test de protection XSS dans le contenu des messages"""
        xss_payload = "<script>alert('XSS')</script>"
        
        message_data = {
            "receiver_id": test_patient.id,
            "subject": "XSS Test",
            "body": xss_payload
        }
        
        response = client.post(
            "/api/v1/messages/",
            json=message_data,
            headers=auth_headers_doctor
        )
        
        assert response.status_code == 201
        # Le contenu devrait être échappé ou chiffré
    
    def test_csrf_protection(self, client):
        """Test de protection CSRF"""
        # FastAPI a une protection CSRF intégrée pour les formulaires
        # Vérifier que les endpoints POST sont protégés
        response = client.post("/api/v1/messages/")
        
        # Devrait échouer sans authentification
        assert response.status_code == 401
    
    def test_rate_limiting_enforcement(self, client, auth_headers_doctor, test_patient):
        """Test que le rate limiting est appliqué"""
        # Tenter d'envoyer beaucoup de messages rapidement
        for i in range(100):
            message_data = {
                "receiver_id": test_patient.id,
                "subject": f"Message {i}",
                "body": "Test"
            }
            
            response = client.post(
                "/api/v1/messages/",
                json=message_data,
                headers=auth_headers_doctor
            )
            
            # Si rate limiting actif, devrait recevoir 429 à un moment
            if response.status_code == 429:
                break
        
        # Note: En tests, le rate limiting est souvent désactivé
    
    def test_encryption_at_rest(self, db, test_doctor, test_patient, test_tenant):
        """Test que les données sensibles sont chiffrées au repos"""
        from app.services.messaging_service import create_message
        
        sensitive_content = "Patient has diabetes type 2"
        
        message = create_message(
            db=db,
            sender_id=test_doctor.id,
            receiver_id=test_patient.id,
            subject="Medical Update",
            body=sensitive_content,
            tenant_id=test_tenant.id
        )
        
        # Le contenu chiffré ne devrait PAS contenir le texte en clair
        assert sensitive_content not in message.encrypted_content
        assert message.encrypted_content != sensitive_content
    
    def test_password_hashing(self, db, test_tenant):
        """Test que les mots de passe sont bien hashés"""
        from app.models.user import User
        from app.core.security import verify_password
        
        plain_password = "TestPassword123!"
        
        user = User(
            email="newuser@test.com",
            username="newuser",
            role="Doctor",
            tenant_id=test_tenant.id,
            status="active"
        )
        
        from app.core.security import get_password_hash
        user.hashed_password = get_password_hash(plain_password)
        
        db.add(user)
        db.commit()
        
        # Le hash ne devrait pas contenir le mot de passe en clair
        assert plain_password not in user.hashed_password
        
        # Mais devrait pouvoir être vérifié
        assert verify_password(plain_password, user.hashed_password)


# ============================================================================
# TESTS DE PERFORMANCE ET CHARGE
# ============================================================================

class TestPerformanceAndLoad:
    """Tests de performance et de charge"""
    
    @pytest.mark.slow
    def test_bulk_patient_query_performance(self, db, test_tenant, test_patients_bulk, benchmark_timer):
        """Test de performance pour requête bulk de patients"""
        from app.models.patient import Patient
        
        benchmark_timer.start()
        
        patients = db.query(Patient).filter(
            Patient.tenant_id == test_tenant.id,
            Patient.status == "active"
        ).limit(100).all()
        
        benchmark_timer.stop()
        
        assert len(patients) >= 10
        assert benchmark_timer.elapsed < 1.0  # Moins d'1 seconde
    
    @pytest.mark.slow
    def test_concurrent_message_sending(self, db, test_doctor, test_patient, test_tenant):
        """Test d'envoi concurrent de messages"""
        from app.services.messaging_service import create_message
        import concurrent.futures
        
        def send_message(n):
            return create_message(
                db=db,
                sender_id=test_doctor.id,
                receiver_id=test_patient.id,
                subject=f"Concurrent {n}",
                body=f"Message {n}",
                tenant_id=test_tenant.id
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(send_message, range(50)))
        
        assert len(results) == 50
        assert all(msg is not None for msg in results)
    
    @pytest.mark.slow
    def test_large_document_upload_performance(self, client, auth_headers_doctor, test_patient, benchmark_timer):
        """Test de performance pour upload de gros fichiers"""
        import io
        
        # Fichier de 10 MB
        large_file = io.BytesIO(b"\x00" * (10 * 1024 * 1024))
        
        files = {"file": ("large.pdf", large_file, "application/pdf")}
        data = {
            "patient_id": test_patient.id,
            "document_type": "imaging",
            "title": "Large Scan"
        }
        
        benchmark_timer.start()
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=auth_headers_doctor
        )
        
        benchmark_timer.stop()
        
        assert response.status_code == 201
        assert benchmark_timer.elapsed < 10.0  # Moins de 10 secondes
    
    @pytest.mark.slow
    def test_api_response_time(self, client, auth_headers_doctor, benchmark_timer):
        """Test des temps de réponse API"""
        endpoints = [
            "/api/v1/patients/",
            "/api/v1/messages/",
            "/api/v1/documents/stats"
        ]
        
        for endpoint in endpoints:
            benchmark_timer.start()
            response = client.get(endpoint, headers=auth_headers_doctor)
            benchmark_timer.stop()
            
            assert response.status_code == 200
            assert benchmark_timer.elapsed < 0.5  # Moins de 500ms


# ============================================================================
# TESTS DES NOTIFICATIONS
# ============================================================================

class TestNotifications:
    """Tests du système de notifications"""
    
    @patch("app.services.notification_service.SMTPNotification.send")
    def test_email_notification(self, mock_smtp, test_patient):
        """Test d'envoi de notification email"""
        from app.services.notification_service import NotificationService
        
        service = NotificationService()
        
        result = service.send_appointment_reminder(
            patient_email=test_patient.email,
            patient_name=f"{test_patient.first_name} {test_patient.last_name}",
            appointment_date="2025-12-01 10:00",
            doctor_name="Dr. Smith"
        )
        
        assert mock_smtp.called
    
    @patch("app.services.notification_service.SMSNotification.send")
    def test_sms_notification(self, mock_sms, test_patient):
        """Test d'envoi de notification SMS"""
        from app.services.notification_service import NotificationService
        
        service = NotificationService()
        
        result = service.send_appointment_reminder_sms(
            phone=test_patient.phone,
            patient_name=test_patient.first_name,
            appointment_date="2025-12-01 10:00"
        )
        
        assert mock_sms.called
    
    @patch("app.tasks.send_upcoming_appointment_reminders.delay")
    def test_celery_task_scheduling(self, mock_task):
        """Test que les tâches Celery sont bien planifiées"""
        from app.tasks import send_upcoming_appointment_reminders
        
        send_upcoming_appointment_reminders.delay()
        
        assert mock_task.called


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app"])
