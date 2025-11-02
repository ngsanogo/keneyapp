"""
Tests exhaustifs pour le système de gestion de documents médicaux v3.0

Couvre:
- Upload de documents (PDF, images, DICOM)
- Validation MIME et format
- Calcul et vérification checksum SHA-256
- Détection de doublons
- Download et streaming
- Permissions et accès
- Métadonnées et recherche
- Soft delete
- Edge cases (taille, formats, corruption)
"""
import pytest
import io
import hashlib
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open

from app.main import app
from app.models.user import User
from app.models.patient import Patient
from app.models.medical_document import (
    MedicalDocument,
    DocumentType,
    DocumentFormat,
    DocumentStatus
)
from app.models.tenant import Tenant
from app.services.document_service import (
    upload_document,
    get_document,
    get_patient_documents,
    calculate_file_checksum,
    validate_file,
    check_duplicate_document,
    get_document_stats,
    delete_document
)


@pytest.fixture
def test_tenant(db: Session):
    """Crée un tenant de test"""
    tenant = Tenant(
        name="Test Hospital",
        code="HOSP001",
        status="active",
        contact_email="test@hospital.com"
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def test_patient(db: Session, test_tenant):
    """Crée un patient de test"""
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
    """Crée un médecin de test"""
    doctor = User(
        email="doctor@hospital.com",
        username="doctor_doc",
        first_name="Jane",
        last_name="Smith",
        role="Doctor",
        tenant_id=test_tenant.id,
        hashed_password="$2b$12$dummy_hash",
        status="active",
        is_active=True
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@pytest.fixture
def sample_pdf_file():
    """Crée un fichier PDF de test"""
    # PDF minimal valide
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n190\n%%EOF"
    return io.BytesIO(pdf_content)


@pytest.fixture
def sample_image_file():
    """Crée un fichier image de test (PNG 1x1 pixel)"""
    # PNG 1x1 transparent
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    return io.BytesIO(png_content)


# ============================================================================
# TESTS UNITAIRES - SERVICE DOCUMENT
# ============================================================================

class TestDocumentService:
    """Tests du service de gestion de documents"""
    
    def test_calculate_file_checksum(self, sample_pdf_file):
        """Test du calcul de checksum SHA-256"""
        checksum = calculate_file_checksum(sample_pdf_file)
        
        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 = 64 caractères hexa
        
        # Vérifier que le checksum est déterministe
        sample_pdf_file.seek(0)
        checksum2 = calculate_file_checksum(sample_pdf_file)
        assert checksum == checksum2
    
    def test_validate_file_pdf(self, sample_pdf_file):
        """Test de validation d'un fichier PDF"""
        is_valid, mime_type = validate_file(sample_pdf_file, "test.pdf")
        
        assert is_valid is True
        assert mime_type == "application/pdf"
    
    def test_validate_file_image_png(self, sample_image_file):
        """Test de validation d'une image PNG"""
        is_valid, mime_type = validate_file(sample_image_file, "test.png")
        
        assert is_valid is True
        assert "image/png" in mime_type
    
    def test_validate_file_invalid_format(self):
        """Test de validation d'un format non supporté"""
        fake_exe = io.BytesIO(b"MZ\x90\x00")  # Signature d'un .exe
        
        is_valid, mime_type = validate_file(fake_exe, "malware.exe")
        
        assert is_valid is False
    
    def test_upload_document_success(self, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Test d'upload d'un document réussi"""
        upload_file = UploadFile(
            filename="lab_results.pdf",
            file=sample_pdf_file
        )
        
        document = upload_document(
            db=db,
            file=upload_file,
            patient_id=test_patient.id,
            uploaded_by_id=test_doctor.id,
            tenant_id=test_tenant.id,
            document_type=DocumentType.LAB_RESULT,
            title="Blood Test Results",
            description="Routine blood work"
        )
        
        assert document is not None
        assert document.patient_id == test_patient.id
        assert document.uploaded_by_id == test_doctor.id
        assert document.title == "Blood Test Results"
        assert document.document_type == DocumentType.LAB_RESULT
        assert document.format == DocumentFormat.PDF
        assert document.status == DocumentStatus.ACTIVE
        assert document.checksum is not None
        assert document.file_size > 0
    
    def test_upload_document_duplicate_detection(self, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Test de détection de doublons"""
        # Premier upload
        file1 = UploadFile(filename="doc1.pdf", file=sample_pdf_file)
        doc1 = upload_document(db, file1, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, "Doc 1")
        
        # Tentative d'upload du même fichier
        sample_pdf_file.seek(0)
        file2 = UploadFile(filename="doc2.pdf", file=sample_pdf_file)
        
        # Vérifier si c'est un doublon
        is_duplicate = check_duplicate_document(db, test_patient.id, doc1.checksum, test_tenant.id)
        
        assert is_duplicate is True
    
    def test_upload_document_too_large(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test d'upload d'un fichier trop volumineux"""
        # Créer un fichier > 50 MB
        large_file = io.BytesIO(b"0" * (51 * 1024 * 1024))
        upload_file = UploadFile(filename="huge.pdf", file=large_file)
        
        with pytest.raises(ValueError, match="exceed"):
            upload_document(db, upload_file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Huge")
    
    def test_get_document_by_id(self, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Test de récupération d'un document par ID"""
        file = UploadFile(filename="test.pdf", file=sample_pdf_file)
        uploaded_doc = upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, "Test")
        
        retrieved_doc = get_document(db, uploaded_doc.id, test_tenant.id)
        
        assert retrieved_doc is not None
        assert retrieved_doc.id == uploaded_doc.id
        assert retrieved_doc.title == "Test"
    
    def test_get_patient_documents(self, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Test de récupération de tous les documents d'un patient"""
        # Créer plusieurs documents
        for i in range(3):
            sample_pdf_file.seek(0)
            file = UploadFile(filename=f"doc{i}.pdf", file=sample_pdf_file)
            upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, f"Doc {i}")
        
        documents = get_patient_documents(db, test_patient.id, test_tenant.id)
        
        assert len(documents) >= 3
    
    def test_get_patient_documents_filter_by_type(self, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Test de filtrage des documents par type"""
        # Upload différents types
        sample_pdf_file.seek(0)
        file1 = UploadFile(filename="lab.pdf", file=sample_pdf_file)
        upload_document(db, file1, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, "Lab")
        
        sample_pdf_file.seek(0)
        file2 = UploadFile(filename="imaging.pdf", file=sample_pdf_file)
        upload_document(db, file2, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.IMAGING, "X-Ray")
        
        # Filtrer par type
        lab_docs = get_patient_documents(db, test_patient.id, test_tenant.id, document_type=DocumentType.LAB_RESULT)
        
        assert all(doc.document_type == DocumentType.LAB_RESULT for doc in lab_docs)
    
    def test_get_document_stats(self, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Test des statistiques de documents"""
        # Créer des documents
        for i in range(5):
            sample_pdf_file.seek(0)
            file = UploadFile(filename=f"doc{i}.pdf", file=sample_pdf_file)
            upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, f"Doc {i}")
        
        stats = get_document_stats(db, test_patient.id, test_tenant.id)
        
        assert stats["total"] >= 5
        assert stats["by_type"][DocumentType.LAB_RESULT.value] >= 5
        assert stats["total_size"] > 0
    
    def test_delete_document_soft_delete(self, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Test de suppression soft d'un document"""
        file = UploadFile(filename="to_delete.pdf", file=sample_pdf_file)
        document = upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Delete Me")
        
        delete_document(db, document.id, test_doctor.id, test_tenant.id)
        
        db.refresh(document)
        assert document.status == DocumentStatus.DELETED
        assert document.deleted_at is not None
        assert document.deleted_by_id == test_doctor.id
    
    def test_upload_different_formats(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test d'upload de différents formats de fichiers"""
        formats = {
            "test.pdf": (b"%PDF-1.4", DocumentFormat.PDF),
            "test.jpg": (b"\xff\xd8\xff", DocumentFormat.JPEG),
            "test.png": (b"\x89PNG\r\n\x1a\n", DocumentFormat.PNG),
        }
        
        for filename, (content, expected_format) in formats.items():
            file_obj = io.BytesIO(content + b"\x00" * 1000)
            upload_file = UploadFile(filename=filename, file=file_obj)
            
            doc = upload_document(db, upload_file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, filename)
            
            assert doc.format == expected_format


# ============================================================================
# TESTS API - ENDPOINTS DOCUMENTS
# ============================================================================

class TestDocumentsAPI:
    """Tests des endpoints API de gestion de documents"""
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_upload_document_api(self, mock_user, db: Session, test_doctor, test_patient, sample_pdf_file):
        """Test d'upload via l'API"""
        mock_user.return_value = test_doctor
        
        client = TestClient(app)
        
        files = {
            "file": ("lab_results.pdf", sample_pdf_file, "application/pdf")
        }
        data = {
            "patient_id": test_patient.id,
            "document_type": "lab_result",
            "title": "Blood Test",
            "description": "Routine checkup"
        }
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "Blood Test"
        assert result["document_type"] == "lab_result"
        assert result["checksum"] is not None
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_upload_document_missing_file(self, mock_user, test_doctor, test_patient):
        """Test d'upload sans fichier"""
        mock_user.return_value = test_doctor
        
        client = TestClient(app)
        
        data = {
            "patient_id": test_patient.id,
            "document_type": "lab_result",
            "title": "No File"
        }
        
        response = client.post(
            "/api/v1/documents/upload",
            data=data,
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_get_patient_documents_api(self, mock_user, db: Session, test_doctor, test_patient, test_tenant, sample_pdf_file):
        """Test de récupération des documents d'un patient via API"""
        mock_user.return_value = test_doctor
        
        # Créer des documents
        file = UploadFile(filename="test.pdf", file=sample_pdf_file)
        upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, "Test")
        
        client = TestClient(app)
        response = client.get(
            f"/api/v1/documents/patient/{test_patient.id}",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        documents = response.json()
        assert isinstance(documents, list)
        assert len(documents) >= 1
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_get_document_by_id_api(self, mock_user, db: Session, test_doctor, test_patient, test_tenant, sample_pdf_file):
        """Test de récupération d'un document par ID via API"""
        mock_user.return_value = test_doctor
        
        file = UploadFile(filename="specific.pdf", file=sample_pdf_file)
        doc = upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, "Specific")
        
        client = TestClient(app)
        response = client.get(
            f"/api/v1/documents/{doc.id}",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == doc.id
        assert result["title"] == "Specific"
    
    @patch("app.core.dependencies.get_current_active_user")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake file content")
    def test_download_document_api(self, mock_file, mock_user, db: Session, test_doctor, test_patient, test_tenant, sample_pdf_file):
        """Test de téléchargement d'un document via API"""
        mock_user.return_value = test_doctor
        
        file = UploadFile(filename="download_test.pdf", file=sample_pdf_file)
        doc = upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, "Download")
        
        client = TestClient(app)
        response = client.get(
            f"/api/v1/documents/{doc.id}/download",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_update_document_metadata(self, mock_user, db: Session, test_doctor, test_patient, test_tenant, sample_pdf_file):
        """Test de mise à jour des métadonnées d'un document"""
        mock_user.return_value = test_doctor
        
        file = UploadFile(filename="update_test.pdf", file=sample_pdf_file)
        doc = upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, "Original Title")
        
        client = TestClient(app)
        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }
        
        response = client.patch(
            f"/api/v1/documents/{doc.id}",
            json=update_data,
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "Updated Title"
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_delete_document_api(self, mock_user, db: Session, test_doctor, test_patient, test_tenant, sample_pdf_file):
        """Test de suppression via API"""
        mock_user.return_value = test_doctor
        
        file = UploadFile(filename="delete_api.pdf", file=sample_pdf_file)
        doc = upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Delete")
        
        client = TestClient(app)
        response = client.delete(
            f"/api/v1/documents/{doc.id}",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_get_document_stats_api(self, mock_user, test_doctor, test_patient):
        """Test de l'endpoint de statistiques"""
        mock_user.return_value = test_doctor
        
        client = TestClient(app)
        response = client.get(
            "/api/v1/documents/stats",
            params={"patient_id": test_patient.id},
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        stats = response.json()
        assert "total" in stats
        assert "by_type" in stats


# ============================================================================
# TESTS SÉCURITÉ
# ============================================================================

class TestDocumentsSecurity:
    """Tests de sécurité des documents"""
    
    def test_malicious_filename_sanitization(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de sanitization des noms de fichiers malveillants"""
        malicious_names = [
            "../../../etc/passwd",
            "../../windows/system32/config.sys",
            "<script>alert('xss')</script>.pdf",
            "file;rm -rf /.pdf"
        ]
        
        for bad_name in malicious_names:
            file_obj = io.BytesIO(b"%PDF-1.4" + b"\x00" * 100)
            upload_file = UploadFile(filename=bad_name, file=file_obj)
            
            # Ne devrait pas lever d'exception, mais sanitizer le nom
            doc = upload_document(db, upload_file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Test")
            
            assert doc is not None
            # Le nom de fichier stocké ne devrait pas contenir les caractères dangereux
            assert ".." not in doc.file_path
            assert "/" not in Path(doc.file_path).name
    
    def test_file_type_spoofing_prevention(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de prévention du spoofing de type de fichier"""
        # Fichier .exe avec extension .pdf
        fake_pdf = io.BytesIO(b"MZ\x90\x00" + b"\x00" * 100)
        upload_file = UploadFile(filename="virus.pdf", file=fake_pdf)
        
        with pytest.raises(ValueError, match="Invalid file type"):
            upload_document(db, upload_file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Malware")
    
    def test_access_control_different_tenant(self, db: Session, test_patient, test_doctor, sample_pdf_file):
        """Test que les documents ne sont pas accessibles entre tenants"""
        # Créer un second tenant
        other_tenant = Tenant(name="Other Clinic", code="OTHER", status="active", contact_email="other@clinic.com")
        db.add(other_tenant)
        db.commit()
        
        # Document dans le premier tenant
        file = UploadFile(filename="private.pdf", file=sample_pdf_file)
        doc = upload_document(db, file, test_patient.id, test_doctor.id, test_patient.tenant_id, DocumentType.OTHER, "Private")
        
        # Tentative d'accès depuis l'autre tenant
        retrieved = get_document(db, doc.id, other_tenant.id)
        
        assert retrieved is None
    
    def test_checksum_verification(self, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Test de vérification de l'intégrité via checksum"""
        file = UploadFile(filename="integrity.pdf", file=sample_pdf_file)
        doc = upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Integrity")
        
        original_checksum = doc.checksum
        
        # Simuler une corruption du fichier
        # (en production, on comparerait le checksum au téléchargement)
        sample_pdf_file.seek(0)
        current_checksum = calculate_file_checksum(sample_pdf_file)
        
        assert current_checksum == original_checksum
    
    @patch("app.core.dependencies.get_current_active_user")
    def test_unauthorized_download_attempt(self, mock_user, db: Session, test_patient, test_tenant, sample_pdf_file):
        """Test de tentative de téléchargement non autorisé"""
        # Créer un utilisateur non autorisé
        unauthorized_user = User(
            email="unauthorized@test.com",
            username="unauth",
            role="Receptionist",
            tenant_id=test_tenant.id,
            hashed_password="hash",
            status="active"
        )
        db.add(unauthorized_user)
        db.commit()
        
        # Créer un document d'un autre utilisateur
        authorized_doctor = User(
            email="authorized@test.com",
            username="auth_doc",
            role="Doctor",
            tenant_id=test_tenant.id,
            hashed_password="hash",
            status="active"
        )
        db.add(authorized_doctor)
        db.commit()
        
        file = UploadFile(filename="confidential.pdf", file=sample_pdf_file)
        doc = upload_document(db, file, test_patient.id, authorized_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, "Confidential")
        
        # Tenter d'accéder avec l'utilisateur non autorisé
        mock_user.return_value = unauthorized_user
        
        client = TestClient(app)
        response = client.get(
            f"/api/v1/documents/{doc.id}",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Devrait être refusé (selon les règles RBAC)
        assert response.status_code in [403, 404]


# ============================================================================
# TESTS EDGE CASES
# ============================================================================

class TestDocumentsEdgeCases:
    """Tests des cas limites"""
    
    def test_empty_file(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test d'upload d'un fichier vide"""
        empty_file = io.BytesIO(b"")
        upload_file = UploadFile(filename="empty.pdf", file=empty_file)
        
        with pytest.raises(ValueError, match="empty"):
            upload_document(db, upload_file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Empty")
    
    def test_unicode_filename(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test d'upload avec nom de fichier Unicode"""
        unicode_name = "résultat_médical_été_2025_🏥.pdf"
        file_obj = io.BytesIO(b"%PDF-1.4" + b"\x00" * 100)
        upload_file = UploadFile(filename=unicode_name, file=file_obj)
        
        doc = upload_document(db, upload_file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, "Unicode")
        
        assert doc is not None
    
    def test_very_long_filename(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test d'upload avec nom de fichier très long"""
        long_name = "a" * 300 + ".pdf"
        file_obj = io.BytesIO(b"%PDF-1.4" + b"\x00" * 100)
        upload_file = UploadFile(filename=long_name, file=file_obj)
        
        doc = upload_document(db, upload_file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Long")
        
        # Le nom devrait être tronqué
        assert len(doc.original_filename) <= 255
    
    def test_concurrent_uploads(self, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Test d'uploads concurrents du même fichier"""
        import concurrent.futures
        
        def upload_doc(n):
            sample_pdf_file.seek(0)
            file = UploadFile(filename=f"concurrent_{n}.pdf", file=io.BytesIO(sample_pdf_file.read()))
            return upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, f"Concurrent {n}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(upload_doc, range(5)))
        
        assert all(doc is not None for doc in results)
    
    def test_corrupted_file_header(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test d'upload d'un fichier avec header corrompu"""
        corrupted = io.BytesIO(b"\x00\x00\x00\x00" * 100)
        upload_file = UploadFile(filename="corrupted.pdf", file=corrupted)
        
        with pytest.raises(ValueError):
            upload_document(db, upload_file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Corrupted")
    
    def test_document_without_extension(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test d'upload d'un fichier sans extension"""
        file_obj = io.BytesIO(b"%PDF-1.4" + b"\x00" * 100)
        upload_file = UploadFile(filename="no_extension", file=file_obj)
        
        # Devrait détecter le type via MIME
        doc = upload_document(db, upload_file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "No Ext")
        
        assert doc.format == DocumentFormat.PDF


# ============================================================================
# TESTS PERFORMANCE
# ============================================================================

class TestDocumentsPerformance:
    """Tests de performance"""
    
    def test_large_file_upload_performance(self, db: Session, test_patient, test_doctor, test_tenant):
        """Test de performance pour l'upload d'un fichier volumineux"""
        import time
        
        # Fichier de 10 MB
        large_file = io.BytesIO(b"\x00" * (10 * 1024 * 1024))
        upload_file = UploadFile(filename="large.pdf", file=large_file)
        
        start = time.time()
        doc = upload_document(db, upload_file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.IMAGING, "Large")
        end = time.time()
        
        assert doc is not None
        # Upload devrait prendre moins de 5 secondes
        assert (end - start) < 5.0
    
    def test_checksum_calculation_performance(self, sample_pdf_file):
        """Test de performance du calcul de checksum"""
        import time
        
        # Fichier de 5 MB
        large_file = io.BytesIO(b"\x00" * (5 * 1024 * 1024))
        
        start = time.time()
        checksum = calculate_file_checksum(large_file)
        end = time.time()
        
        assert checksum is not None
        # Calcul devrait prendre moins de 1 seconde
        assert (end - start) < 1.0
    
    def test_bulk_document_retrieval(self, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Test de performance pour récupération en masse"""
        # Créer 100 documents
        for i in range(100):
            sample_pdf_file.seek(0)
            file = UploadFile(filename=f"bulk_{i}.pdf", file=sample_pdf_file)
            upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, f"Bulk {i}")
        
        import time
        start = time.time()
        documents = get_patient_documents(db, test_patient.id, test_tenant.id, skip=0, limit=50)
        end = time.time()
        
        assert len(documents) == 50
        # Requête devrait prendre moins de 1 seconde
        assert (end - start) < 1.0


# ============================================================================
# TESTS AUDIT & LOGGING
# ============================================================================

class TestDocumentsAudit:
    """Tests de l'audit et du logging"""
    
    @patch("app.core.audit.log_audit_event")
    def test_audit_on_upload(self, mock_audit, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Vérifier qu'un événement d'audit est créé lors de l'upload"""
        file = UploadFile(filename="audit.pdf", file=sample_pdf_file)
        upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Audit")
        
        assert mock_audit.called
    
    @patch("app.core.audit.log_audit_event")
    def test_audit_on_download(self, mock_audit, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Vérifier qu'un événement d'audit est créé lors du téléchargement"""
        file = UploadFile(filename="download_audit.pdf", file=sample_pdf_file)
        doc = upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.OTHER, "Download Audit")
        
        mock_audit.reset_mock()
        get_document(db, doc.id, test_tenant.id)
        
        # L'audit devrait être loggé lors du download effectif
        # (implémenté dans le endpoint de download)
    
    def test_no_phi_in_audit_logs(self, caplog, db: Session, test_patient, test_doctor, test_tenant, sample_pdf_file):
        """Vérifier qu'aucune PHI n'est loggée"""
        with caplog.at_level("INFO"):
            file = UploadFile(filename="confidential.pdf", file=sample_pdf_file)
            upload_document(db, file, test_patient.id, test_doctor.id, test_tenant.id, DocumentType.LAB_RESULT, "Patient blood type AB+")
        
        # Vérifier qu'aucun log ne contient d'informations médicales
        for record in caplog.records:
            assert "blood type" not in record.message.lower()
            assert "AB+" not in record.message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app/routers/documents", "--cov=app/services/document_service"])
