"""
Common schemas for API responses and requests
Provides consistent response formats across all endpoints
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters"""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        """Calculate skip offset for database queries"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Alias for page_size"""
        return self.page_size


class SortParams(BaseModel):
    """Standard sorting parameters"""

    sort_by: Optional[str] = Field(
        None, pattern="^[a-zA-Z_][a-zA-Z0-9_]*$", description="Field to sort by"
    )
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class FilterParams(BaseModel):
    """Base filter parameters"""

    search: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Search query"
    )
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, v, info):
        """Ensure date_to is after date_from"""
        if v and info.data.get("date_from") and v < info.data["date_from"]:
            raise ValueError("date_to must be after date_from")
        return v


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper
    Provides consistent structure for all paginated endpoints
    """

    items: List[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    @classmethod
    def create(
        cls, items: List[T], total: int, page: int, page_size: int
    ) -> "PaginatedResponse[T]":
        """Factory method to create paginated response"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class SuccessResponse(BaseModel):
    """Standard success response"""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorDetail(BaseModel):
    """Detailed error information"""

    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response"""

    success: bool = False
    error: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response"""

    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(default_factory=dict)


class BulkOperationRequest(BaseModel):
    """Request for bulk operations"""

    ids: List[int] = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)
    params: Optional[Dict[str, Any]] = None


class BulkOperationResponse(BaseModel):
    """Response for bulk operations"""

    success_count: int = Field(..., ge=0)
    failure_count: int = Field(..., ge=0)
    total: int = Field(..., ge=0)
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def create(
        cls, success_count: int, errors: Optional[List[Dict[str, Any]]] = None
    ) -> "BulkOperationResponse":
        """Factory method"""
        failure_count = len(errors) if errors else 0
        return cls(
            success_count=success_count,
            failure_count=failure_count,
            total=success_count + failure_count,
            errors=errors or [],
        )


class ExportRequest(BaseModel):
    """Request for data export"""

    format: str = Field(..., pattern="^(csv|xlsx|pdf|json)$")
    filters: Optional[Dict[str, Any]] = None
    columns: Optional[List[str]] = None


class ImportRequest(BaseModel):
    """Request for data import"""

    format: str = Field(..., pattern="^(csv|xlsx|json)$")
    validate_only: bool = False
    skip_errors: bool = False


class ImportResponse(BaseModel):
    """Response for data import"""

    success: bool
    imported_count: int = 0
    failed_count: int = 0
    validation_errors: List[ErrorDetail] = Field(default_factory=list)


class AuditInfo(BaseModel):
    """Audit information for entities"""

    created_at: datetime
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    version: int = 1


class BaseEntityResponse(BaseModel):
    """Base response schema for entities with audit info"""

    id: int
    audit: AuditInfo

    model_config = {"from_attributes": True}
