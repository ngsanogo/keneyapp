"""
Pydantic schemas for medical documents.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.medical_document import DocumentType, DocumentFormat, DocumentStatus


class DocumentUpload(BaseModel):
    """Schema for document upload metadata."""
    patient_id: int = Field(..., description="Patient ID this document belongs to")
    document_type: DocumentType = Field(..., description="Type of medical document")
    description: Optional[str] = Field(None, max_length=1000, description="Document description")
    tags: Optional[List[str]] = Field(None, description="Document tags for categorization")
    appointment_id: Optional[int] = Field(None, description="Related appointment ID")
    prescription_id: Optional[int] = Field(None, description="Related prescription ID")
    is_sensitive: bool = Field(True, description="Mark as sensitive/PHI")


class DocumentMetadata(BaseModel):
    """Schema for updating document metadata."""
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    document_type: Optional[DocumentType] = None


class DocumentResponse(BaseModel):
    """Schema for document response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_filename: str
    document_type: DocumentType
    document_format: DocumentFormat
    mime_type: str
    file_size: int
    storage_type: str
    status: DocumentStatus
    processing_error: Optional[str]
    ocr_text: Optional[str]
    extracted_metadata: Optional[str]
    patient_id: int
    uploaded_by_id: int
    appointment_id: Optional[int]
    prescription_id: Optional[int]
    description: Optional[str]
    tags: Optional[str]
    is_sensitive: bool
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class DocumentSummary(BaseModel):
    """Lightweight document summary."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    document_type: DocumentType
    document_format: DocumentFormat
    file_size: int
    status: DocumentStatus
    patient_id: int
    created_at: datetime
    is_sensitive: bool


class DocumentDownloadUrl(BaseModel):
    """Temporary download URL for document."""
    document_id: int
    download_url: str
    expires_at: datetime
    filename: str


class DocumentStats(BaseModel):
    """Document storage statistics."""
    total_documents: int
    total_size_bytes: int
    total_size_mb: float
    by_type: dict
    by_format: dict
    by_status: dict
