"""
API routes for medical document upload and management.
"""

import json
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, require_roles
from app.core.rate_limit import limiter
from app.models.medical_document import DocumentType
from app.models.user import User, UserRole
from app.schemas.medical_document import (
    DocumentMetadata,
    DocumentResponse,
    DocumentStats,
    DocumentUpload,
)
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("20/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="Medical document file"),
    patient_id: int = Form(..., description="Patient ID"),
    document_type: DocumentType = Form(..., description="Document type"),
    description: Optional[str] = Form(None, description="Document description"),
    tags: Optional[str] = Form(None, description="JSON array of tags"),
    appointment_id: Optional[int] = Form(None, description="Related appointment ID"),
    prescription_id: Optional[int] = Form(None, description="Related prescription ID"),
    is_sensitive: bool = Form(True, description="Mark as sensitive"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload a medical document (PDF, image, DICOM, etc.).

    **Access:** All authenticated users

    **Rate limit:** 20 uploads per minute

    **Supported formats:**
    - PDF documents
    - Images (JPEG, PNG)
    - DICOM medical imaging
    - Word documents (DOCX)
    - Text files

    **File size limit:** 50 MB

    **Security:**
    - Files are stored securely with unique filenames
    - SHA-256 checksum for integrity verification
    - Duplicate detection
    - PHI marked as sensitive by default
    """
    # Parse tags if provided
    tags_list = None
    if tags:
        try:
            tags_list = json.loads(tags)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tags format. Must be JSON array.",
            )

    # Create metadata object
    metadata = DocumentUpload(
        patient_id=patient_id,
        document_type=document_type,
        description=description,
        tags=tags_list,
        appointment_id=appointment_id,
        prescription_id=prescription_id,
        is_sensitive=is_sensitive,
    )

    # Upload document
    document = await document_service.upload_document(
        db=db,
        file=file,
        metadata=metadata,
        user_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
        request=request,
    )

    return document


@router.get("/patient/{patient_id}", response_model=List[DocumentResponse])
@limiter.limit("60/minute")
async def get_patient_documents(
    request: Request,
    patient_id: int,
    document_type: Optional[DocumentType] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get all documents for a specific patient.

    **Access:** All authenticated users (same tenant)

    **Rate limit:** 60 requests per minute

    **Query Parameters:**
    - `document_type`: Filter by document type
    - `skip`: Pagination offset
    - `limit`: Maximum results (max 100)
    """
    if limit > 100:
        limit = 100

    documents = document_service.get_patient_documents(
        db=db,
        patient_id=patient_id,
        tenant_id=str(current_user.tenant_id),
        document_type=document_type,
        skip=skip,
        limit=limit,
    )

    return documents


@router.get("/stats", response_model=DocumentStats)
@limiter.limit("60/minute")
async def get_document_statistics(
    request: Request,
    patient_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get document storage statistics.

    **Access:** All authenticated users

    **Rate limit:** 60 requests per minute

    **Query Parameters:**
    - `patient_id`: Filter stats for specific patient
    """
    return document_service.get_document_stats(
        db=db, tenant_id=str(current_user.tenant_id), patient_id=patient_id
    )


@router.get("/{document_id}", response_model=DocumentResponse)
@limiter.limit("60/minute")
async def get_document(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get document metadata by ID.

    **Access:** All authenticated users (same tenant)

    **Rate limit:** 60 requests per minute
    """
    document = document_service.get_document(
        db=db, document_id=document_id, tenant_id=str(current_user.tenant_id)
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied",
        )

    return document


@router.get("/{document_id}/download")
@limiter.limit("30/minute")
async def download_document(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Download a medical document.

    **Access:** All authenticated users (same tenant)

    **Rate limit:** 30 downloads per minute

    **Security:** Access is logged for audit compliance
    """
    document = document_service.get_document(
        db=db, document_id=document_id, tenant_id=str(current_user.tenant_id)
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied",
        )

    # Get file path
    file_path = document_service.get_document_file_path(document)

    # Verify file exists
    import os

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on storage",
        )

    # Log access for audit
    from app.core.audit import log_audit_event

    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="READ",
        resource_type="medical_document",
        resource_id=str(document.id),
        details={"patient_id": document.patient_id, "download": True},
        request=request,
    )

    # Return file
    return FileResponse(
        path=file_path,
        filename=document.original_filename,
        media_type=document.mime_type,
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
@limiter.limit("30/minute")
async def update_document_metadata(
    request: Request,
    document_id: int,
    metadata: DocumentMetadata,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR])),
    db: Session = Depends(get_db),
):
    """
    Update document metadata (description, tags, type).

    **Access:** Admin, Doctor

    **Rate limit:** 30 requests per minute
    """
    document = document_service.get_document(
        db=db, document_id=document_id, tenant_id=str(current_user.tenant_id)
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied",
        )

    # Update metadata
    if metadata.description is not None:
        document.description = metadata.description

    if metadata.tags is not None:
        document.tags = json.dumps(metadata.tags)

    if metadata.document_type is not None:
        document.document_type = metadata.document_type

    db.commit()
    db.refresh(document)

    # Audit log
    from app.core.audit import log_audit_event

    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        resource_type="medical_document",
        resource_id=str(document.id),
        details={"patient_id": document.patient_id, "metadata_update": True},
        request=request,
    )

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_document(
    request: Request,
    document_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR])),
    db: Session = Depends(get_db),
):
    """
    Delete a medical document (soft delete).

    **Access:** Admin, Doctor

    **Rate limit:** 30 requests per minute

    **Note:** This is a soft delete. The document is archived but not physically removed.
    """
    success = document_service.delete_document(
        db=db,
        document_id=document_id,
        tenant_id=str(current_user.tenant_id),
        user_id=current_user.id,
        request=request,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied",
        )

    return None
