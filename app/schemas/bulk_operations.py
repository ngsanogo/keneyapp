"""
Bulk operations schemas for batch processing
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class BulkOperationType(str, Enum):
    """Types of bulk operations"""

    DELETE = "delete"
    UPDATE = "update"
    EXPORT = "export"
    ASSIGN_DOCTOR = "assign_doctor"
    TAG = "tag"


class BulkDeleteRequest(BaseModel):
    """Request to delete multiple patients"""

    patient_ids: List[int] = Field(
        ..., min_length=1, max_length=100, description="List of patient IDs to delete"
    )
    confirm: bool = Field(
        ..., description="Confirmation flag (must be true to proceed)"
    )


class BulkUpdateField(BaseModel):
    """Single field update for bulk operation"""

    field: str = Field(
        ..., description="Field name to update (e.g., 'phone', 'address')"
    )
    value: str = Field(..., description="New value for the field")


class BulkUpdateRequest(BaseModel):
    """Request to update multiple patients"""

    patient_ids: List[int] = Field(
        ..., min_length=1, max_length=100, description="List of patient IDs to update"
    )
    updates: List[BulkUpdateField] = Field(
        ..., min_length=1, description="Fields to update"
    )


class BulkOperationResult(BaseModel):
    """Result of a bulk operation"""

    success: bool
    total: int = Field(..., description="Total number of items processed")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: List[dict] = Field(default_factory=list, description="List of errors")
    message: str


class BulkExportRequest(BaseModel):
    """Request to export multiple patient records"""

    patient_ids: Optional[List[int]] = Field(
        None, description="Specific patient IDs to export (if None, exports all)"
    )
    format: str = Field(
        "csv", pattern="^(csv|excel|pdf|json)$", description="Export format"
    )
    include_sensitive: bool = Field(False, description="Include sensitive medical data")
