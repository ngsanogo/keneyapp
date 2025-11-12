"""
Medical document storage and management service.
Supports local filesystem and S3-compatible storage.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.models.medical_document import (
    DocumentFormat,
    DocumentStatus,
    DocumentType,
    MedicalDocument,
)
from app.models.patient import Patient
from app.schemas.medical_document import DocumentStats, DocumentUpload

# Document storage configuration
UPLOAD_DIR = os.getenv("DOCUMENTS_UPLOAD_DIR", "./uploads/medical_documents")
MAX_FILE_SIZE = int(os.getenv("MAX_DOCUMENT_SIZE", 50 * 1024 * 1024))  # 50 MB default
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/jpg",
    "application/dicom",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


def init_storage_directory():
    """Initialize local storage directory."""
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def detect_document_format(mime_type: str) -> DocumentFormat:
    """Detect document format from MIME type."""
    mime_format_map = {
        "application/pdf": DocumentFormat.PDF,
        "image/jpeg": DocumentFormat.JPEG,
        "image/jpg": DocumentFormat.JPEG,
        "image/png": DocumentFormat.PNG,
        "application/dicom": DocumentFormat.DICOM,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentFormat.DOCX,
        "text/plain": DocumentFormat.TXT,
    }
    return mime_format_map.get(mime_type, DocumentFormat.PDF)


def calculate_file_checksum(file_data: bytes) -> str:
    """Calculate SHA-256 checksum of file."""
    return hashlib.sha256(file_data).hexdigest()


def generate_secure_filename(
    original_filename: str, tenant_id: str, patient_id: int
) -> Tuple[str, str]:
    """Generate secure unique filename and storage path."""
    # Extract extension
    ext = Path(original_filename).suffix.lower()

    # Generate unique filename
    unique_id = uuid.uuid4().hex
    secure_filename = f"{tenant_id}_{patient_id}_{unique_id}{ext}"

    # Organize by tenant and patient
    storage_path = os.path.join(UPLOAD_DIR, str(tenant_id), str(patient_id), secure_filename)

    return secure_filename, storage_path


async def save_file_to_local_storage(file: UploadFile, storage_path: str) -> int:
    """Save uploaded file to local storage."""
    # Create directory if needed
    Path(storage_path).parent.mkdir(parents=True, exist_ok=True)

    # Write file
    file_size = 0
    with open(storage_path, "wb") as buffer:
        content = await file.read()
        file_size = len(content)
        buffer.write(content)

    return file_size


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported types: {', '.join(ALLOWED_MIME_TYPES)}",
        )


async def upload_document(
    db: Session,
    file: UploadFile,
    metadata: DocumentUpload,
    user_id: int,
    tenant_id: str,
    request: Optional[Request] = None,
) -> MedicalDocument:
    """
    Upload and store a medical document.
    """
    # Initialize storage
    init_storage_directory()

    # Validate file
    validate_file(file)

    # Verify patient exists and belongs to tenant
    patient = (
        db.query(Patient)
        .filter(Patient.id == metadata.patient_id, Patient.tenant_id == tenant_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or access denied",
        )

    # Generate secure filename and path
    filename = file.filename or "unnamed_file"
    secure_filename, storage_path = generate_secure_filename(
        filename, tenant_id, metadata.patient_id
    )

    # Read file content for checksum
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f} MB",
        )

    # Calculate checksum
    checksum = calculate_file_checksum(content)

    # Check for duplicate (same checksum for same patient)
    existing = (
        db.query(MedicalDocument)
        .filter(
            MedicalDocument.patient_id == metadata.patient_id,
            MedicalDocument.checksum == checksum,
            MedicalDocument.deleted_at.is_(None),
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document already exists (duplicate detected)",
        )

    # Save file to storage
    Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
    with open(storage_path, "wb") as buffer:
        buffer.write(content)

    # Detect format
    content_type = file.content_type or "application/octet-stream"
    document_format = detect_document_format(content_type)

    # Convert tags to JSON
    tags_json = json.dumps(metadata.tags) if metadata.tags else None

    # Create database record
    document = MedicalDocument(
        filename=secure_filename,
        original_filename=file.filename,
        document_type=metadata.document_type,
        document_format=document_format,
        mime_type=file.content_type,
        file_size=file_size,
        storage_path=storage_path,
        storage_type="local",
        checksum=checksum,
        status=DocumentStatus.READY,
        patient_id=metadata.patient_id,
        uploaded_by_id=user_id,
        appointment_id=metadata.appointment_id,
        prescription_id=metadata.prescription_id,
        description=metadata.description,
        tags=tags_json,
        is_sensitive=metadata.is_sensitive,
        tenant_id=tenant_id,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Audit log
    if request:
        log_audit_event(
            db=db,
            user_id=user_id,
            action="CREATE",
            resource_type="medical_document",
            resource_id=int(document.id) if document.id else None,
            details={
                "patient_id": metadata.patient_id,
                "document_type": metadata.document_type.value,
                "file_size": file_size,
                "filename": file.filename,
            },
            request=request,
        )

    return document


def get_document(
    db: Session, document_id: int, tenant_id: str, user_id: Optional[int] = None
) -> Optional[MedicalDocument]:
    """Get document by ID with tenant validation."""
    query = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.tenant_id == tenant_id,
        MedicalDocument.deleted_at.is_(None),
    )

    return query.first()


def get_patient_documents(
    db: Session,
    patient_id: int,
    tenant_id: str,
    document_type: Optional[DocumentType] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[MedicalDocument]:
    """Get all documents for a patient."""
    query = db.query(MedicalDocument).filter(
        MedicalDocument.patient_id == patient_id,
        MedicalDocument.tenant_id == tenant_id,
        MedicalDocument.deleted_at.is_(None),
    )

    if document_type:
        query = query.filter(MedicalDocument.document_type == document_type)

    return query.order_by(MedicalDocument.created_at.desc()).offset(skip).limit(limit).all()


def delete_document(
    db: Session,
    document_id: int,
    tenant_id: str,
    user_id: int,
    request: Optional[Request] = None,
) -> bool:
    """Soft delete a document."""
    document = get_document(db, document_id, tenant_id)

    if not document:
        return False

    # Soft delete
    setattr(document, "deleted_at", datetime.now(timezone.utc))
    setattr(document, "status", DocumentStatus.ARCHIVED)
    db.commit()

    # Audit log
    if request:
        log_audit_event(
            db=db,
            user_id=user_id,
            action="DELETE",
            resource_type="medical_document",
            resource_id=int(document.id) if document.id else None,
            details={"patient_id": document.patient_id, "soft_delete": True},
            request=request,
        )

    return True


def get_document_file_path(document: MedicalDocument) -> str:
    """Get the file system path for a document."""
    return str(document.storage_path)


def get_document_stats(
    db: Session, tenant_id: str, patient_id: Optional[int] = None
) -> DocumentStats:
    """Get document storage statistics."""
    query = db.query(MedicalDocument).filter(
        MedicalDocument.tenant_id == tenant_id, MedicalDocument.deleted_at.is_(None)
    )

    if patient_id:
        query = query.filter(MedicalDocument.patient_id == patient_id)

    documents = query.all()

    total_size = sum(doc.file_size for doc in documents)

    # Count by type
    by_type: dict[str, int] = {}
    for doc in documents:
        doc_type = doc.document_type.value
        by_type[doc_type] = by_type.get(doc_type, 0) + 1

    # Count by format
    by_format: dict[str, int] = {}
    for doc in documents:
        doc_format = doc.document_format.value
        by_format[doc_format] = by_format.get(doc_format, 0) + 1

    # Count by status
    by_status: dict[str, int] = {}
    for doc in documents:
        doc_status = doc.status.value
        by_status[doc_status] = by_status.get(doc_status, 0) + 1

    return DocumentStats(
        total_documents=len(documents),
        total_size_bytes=total_size,
        total_size_mb=round(total_size / (1024 * 1024), 2),
        by_type=by_type,
        by_format=by_format,
        by_status=by_status,
    )
