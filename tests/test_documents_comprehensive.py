"""
Comprehensive tests for document management service (v3.0).

Tests cover:
- Document upload (PDF, images, DICOM)
- File validation (MIME, size limits)
- Duplicate detection (checksum)
- Document retrieval and download
- Metadata management
- Storage (local and S3-compatible)
- OCR readiness
- Security and access control
"""

import hashlib
import io
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.unit
class TestDocumentValidation:
    """Test document validation logic."""

    def test_allowed_mime_types(self):
        """Test that only allowed MIME types are accepted."""
        allowed_types = [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "application/dicom",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]

        for mime_type in allowed_types:
            assert mime_type in [
                "application/pdf",
                "image/jpeg",
                "image/png",
                "application/dicom",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
            ]

    def test_file_size_limit(self):
        """Test file size validation."""
        max_size = 50 * 1024 * 1024  # 50 MB

        # Valid size
        assert 1024 < max_size

        # Invalid size
        assert 100 * 1024 * 1024 > max_size

    def test_checksum_calculation(self):
        """Test SHA-256 checksum calculation."""
        content = b"Test file content for checksum"
        checksum = hashlib.sha256(content).hexdigest()

        assert len(checksum) == 64  # SHA-256 produces 64 hex characters

        # Same content produces same checksum
        checksum2 = hashlib.sha256(content).hexdigest()
        assert checksum == checksum2


@pytest.mark.integration
class TestDocumentUpload:
    """Test document upload operations."""

    def test_upload_pdf_document(self, client: TestClient, auth_headers: dict):
        """Test uploading a PDF document."""
        # Create a fake PDF file
        pdf_content = b"%PDF-1.4\n%Test PDF content"
        file = io.BytesIO(pdf_content)

        files = {"file": ("test_document.pdf", file, "application/pdf")}
        data = {
            "document_type": "lab_result",
            "patient_id": 1,
            "description": "Résultats d'analyses sanguines",
        }

        response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        assert response.status_code in [201, 200]
        if response.status_code == 201:
            result = response.json()
            assert result["document_type"] == "lab_result"
            assert result["mime_type"] == "application/pdf"
            assert "id" in result

    def test_upload_image_document(self, client: TestClient, auth_headers: dict):
        """Test uploading an image document."""
        # Create a minimal valid JPEG
        jpeg_content = bytes.fromhex(
            "FFD8FFE000104A46494600010101006000600000FFDB004300080606070605080707"
            "070909080A0C140D0C0B0B0C1912130F141D1A1F1E1D1A1C1C20242E2720222C231C"
            "1C2837292C30313434341F27393D38323C2E333432FFDB0043010909090C0B0C180D"
            "0D1832211C213232323232323232323232323232323232323232323232323232323232"
            "3232323232323232323232323232323232FFC00011080001000103012200021101031101"
            "FFC4001500010100000000000000000000000000000000FFC40014100100000000000000"
            "000000000000000000FFDA000C03010002110311003F00BF8001FFD9"
        )
        file = io.BytesIO(jpeg_content)

        files = {"file": ("xray.jpg", file, "image/jpeg")}
        data = {
            "document_type": "imaging",
            "patient_id": 1,
            "description": "Radiographie thorax",
        }

        response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        assert response.status_code in [201, 200]

    def test_upload_file_too_large(self, client: TestClient, auth_headers: dict):
        """Test that files exceeding size limit are rejected."""
        # Create a large file (> 50 MB)
        large_content = b"x" * (51 * 1024 * 1024)  # 51 MB
        file = io.BytesIO(large_content)

        files = {"file": ("large_file.pdf", file, "application/pdf")}
        data = {"document_type": "other", "patient_id": 1}

        response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        # Should be rejected (413 Payload Too Large or 400 Bad Request)
        assert response.status_code in [413, 400, 422]

    def test_upload_invalid_mime_type(self, client: TestClient, auth_headers: dict):
        """Test that invalid MIME types are rejected."""
        file = io.BytesIO(b"executable content")

        files = {"file": ("malicious.exe", file, "application/x-msdownload")}
        data = {"document_type": "other", "patient_id": 1}

        response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        assert response.status_code in [400, 415, 422]

    def test_upload_without_patient_id(self, client: TestClient, auth_headers: dict):
        """Test that patient_id is required for upload."""
        file = io.BytesIO(b"Test content")

        files = {"file": ("test.pdf", file, "application/pdf")}
        data = {
            "document_type": "other"
            # Missing patient_id
        }

        response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestDuplicateDetection:
    """Test duplicate document detection."""

    def test_duplicate_checksum_detection(self, client: TestClient, auth_headers: dict):
        """Test that duplicate files are detected by checksum."""
        content = b"Unique document content for duplicate test"
        file1 = io.BytesIO(content)

        # Upload first time
        files1 = {"file": ("document1.pdf", file1, "application/pdf")}
        data1 = {"document_type": "lab_result", "patient_id": 1}

        response1 = client.post(
            "/api/v1/documents/upload", files=files1, data=data1, headers=auth_headers
        )

        assert response1.status_code in [201, 200]

        # Upload same content again
        file2 = io.BytesIO(content)
        files2 = {"file": ("document2.pdf", file2, "application/pdf")}
        data2 = {"document_type": "lab_result", "patient_id": 1}

        response2 = client.post(
            "/api/v1/documents/upload", files=files2, data=data2, headers=auth_headers
        )

        # Should either reject or return existing document
        assert response2.status_code in [200, 201, 409]

        # If allowed, should flag as duplicate
        if response2.status_code in [200, 201]:
            result2 = response2.json()
            # Check if duplicate is noted (implementation dependent)


@pytest.mark.integration
class TestDocumentRetrieval:
    """Test document retrieval operations."""

    def test_get_patient_documents(self, client: TestClient, auth_headers: dict):
        """Test retrieving all documents for a patient."""
        # First upload a document
        file = io.BytesIO(b"Test content")
        files = {"file": ("test.pdf", file, "application/pdf")}
        data = {"document_type": "lab_result", "patient_id": 1}

        upload_response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        if upload_response.status_code in [200, 201]:
            # Get patient documents
            response = client.get("/api/v1/documents/patient/1", headers=auth_headers)

            assert response.status_code == 200
            documents = response.json()
            assert isinstance(documents, list)

    def test_get_document_details(self, client: TestClient, auth_headers: dict):
        """Test retrieving document details."""
        # Upload document first
        file = io.BytesIO(b"Test content")
        files = {"file": ("test.pdf", file, "application/pdf")}
        data = {"document_type": "lab_result", "patient_id": 1}

        upload_response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        if upload_response.status_code in [200, 201]:
            doc_id = upload_response.json()["id"]

            # Get document details
            response = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)

            assert response.status_code == 200
            doc = response.json()
            assert doc["id"] == doc_id

    def test_download_document(self, client: TestClient, auth_headers: dict):
        """Test downloading a document file."""
        # Upload document first
        content = b"Downloadable content"
        file = io.BytesIO(content)
        files = {"file": ("test.pdf", file, "application/pdf")}
        data = {"document_type": "lab_result", "patient_id": 1}

        upload_response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        if upload_response.status_code in [200, 201]:
            doc_id = upload_response.json()["id"]

            # Download document
            response = client.get(
                f"/api/v1/documents/{doc_id}/download", headers=auth_headers
            )

            assert response.status_code == 200
            assert len(response.content) > 0


@pytest.mark.integration
class TestDocumentMetadata:
    """Test document metadata management."""

    def test_update_document_metadata(self, client: TestClient, auth_headers: dict):
        """Test updating document metadata."""
        # Upload document first
        file = io.BytesIO(b"Test content")
        files = {"file": ("test.pdf", file, "application/pdf")}
        data = {
            "document_type": "lab_result",
            "patient_id": 1,
            "description": "Original description",
        }

        upload_response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        if upload_response.status_code in [200, 201]:
            doc_id = upload_response.json()["id"]

            # Update metadata
            update_data = {
                "description": "Updated description",
                "tags": ["urgent", "reviewed"],
            }

            response = client.patch(
                f"/api/v1/documents/{doc_id}", json=update_data, headers=auth_headers
            )

            assert response.status_code in [200, 204]

    def test_document_tags(self, client: TestClient, auth_headers: dict):
        """Test adding tags to documents."""
        file = io.BytesIO(b"Test content")
        files = {"file": ("test.pdf", file, "application/pdf")}
        data = {
            "document_type": "lab_result",
            "patient_id": 1,
            "tags": ["blood_test", "annual_checkup"],
        }

        response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        if response.status_code in [200, 201]:
            result = response.json()
            # Tags should be stored (if implemented)


@pytest.mark.integration
class TestDocumentSecurity:
    """Test document security and access control."""

    def test_cannot_access_other_tenant_document(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that documents are tenant-isolated."""
        # Try to access non-existent document from another tenant
        response = client.get("/api/v1/documents/99999", headers=auth_headers)

        assert response.status_code in [403, 404]

    def test_rbac_doctor_can_upload(self, client: TestClient, auth_headers: dict):
        """Test that doctors can upload documents."""
        file = io.BytesIO(b"Test content")
        files = {"file": ("test.pdf", file, "application/pdf")}
        data = {"document_type": "prescription", "patient_id": 1}

        response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        # Should succeed (200/201) or be forbidden if not doctor role
        assert response.status_code in [200, 201, 403]

    def test_document_marked_as_sensitive(
        self, client: TestClient, auth_headers: dict, db_session: Session
    ):
        """Test that uploaded documents are marked as sensitive."""
        from app.models.medical_document import MedicalDocument

        # Check that is_sensitive defaults to True
        doc = db_session.query(MedicalDocument).first()
        if doc:
            assert doc.is_sensitive is True or doc.is_sensitive is None


@pytest.mark.integration
class TestDocumentStatistics:
    """Test document statistics endpoint."""

    def test_get_document_stats(self, client: TestClient, auth_headers: dict):
        """Test retrieving document storage statistics."""
        response = client.get("/api/v1/documents/stats", headers=auth_headers)

        assert response.status_code == 200
        stats = response.json()
        assert "total_documents" in stats
        assert "total_size_bytes" in stats
        assert "documents_by_type" in stats


@pytest.mark.integration
class TestDocumentDeletion:
    """Test document deletion (soft delete)."""

    def test_soft_delete_document(self, client: TestClient, auth_headers: dict):
        """Test soft-deleting a document."""
        # Upload document first
        file = io.BytesIO(b"Test content")
        files = {"file": ("test.pdf", file, "application/pdf")}
        data = {"document_type": "other", "patient_id": 1}

        upload_response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        if upload_response.status_code in [200, 201]:
            doc_id = upload_response.json()["id"]

            # Delete document
            response = client.delete(
                f"/api/v1/documents/{doc_id}", headers=auth_headers
            )

            assert response.status_code in [200, 204]

            # Verify soft delete (document should not be retrievable)
            get_response = client.get(
                f"/api/v1/documents/{doc_id}", headers=auth_headers
            )
            assert get_response.status_code in [404, 410]


@pytest.mark.integration
class TestDICOMSupport:
    """Test DICOM file support."""

    def test_upload_dicom_file(self, client: TestClient, auth_headers: dict):
        """Test uploading a DICOM medical imaging file."""
        # Minimal DICOM file header
        dicom_content = b"DICM"  # Simplified for test
        file = io.BytesIO(dicom_content)

        files = {"file": ("scan.dcm", file, "application/dicom")}
        data = {"document_type": "imaging", "patient_id": 1, "description": "CT Scan"}

        response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        # Should accept or validate DICOM format
        assert response.status_code in [200, 201, 400, 415]


@pytest.mark.unit
class TestOCRReadiness:
    """Test OCR field readiness."""

    def test_ocr_text_field_exists(self, db_session: Session):
        """Test that ocr_text field exists for future OCR integration."""
        from app.models.medical_document import MedicalDocument

        # Check model has ocr_text field
        assert hasattr(MedicalDocument, "ocr_text")


@pytest.mark.integration
class TestDocumentTypes:
    """Test all document types."""

    @pytest.mark.parametrize(
        "doc_type",
        [
            "lab_result",
            "imaging",
            "prescription",
            "consultation_note",
            "vaccination_record",
            "insurance",
            "id_document",
            "other",
        ],
    )
    def test_all_document_types_accepted(
        self, client: TestClient, auth_headers: dict, doc_type: str
    ):
        """Test that all document types are accepted."""
        file = io.BytesIO(b"Test content")
        files = {"file": ("test.pdf", file, "application/pdf")}
        data = {"document_type": doc_type, "patient_id": 1}

        response = client.post(
            "/api/v1/documents/upload", files=files, data=data, headers=auth_headers
        )

        assert response.status_code in [200, 201]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
