"""
Advanced filtering schemas for patient search and management
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class GenderFilter(str, Enum):
    """Gender filter options"""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    ALL = "all"


class AgeRange(BaseModel):
    """Age range filter"""

    min_age: Optional[int] = Field(None, ge=0, le=150, description="Minimum age")
    max_age: Optional[int] = Field(None, ge=0, le=150, description="Maximum age")


class PatientAdvancedFilters(BaseModel):
    """Advanced filtering options for patient search"""

    # Text search across multiple fields
    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Search in name, email, phone, address",
    )

    # Demographics
    gender: Optional[GenderFilter] = Field(None, description="Filter by gender")
    min_age: Optional[int] = Field(None, ge=0, le=150, description="Minimum age")
    max_age: Optional[int] = Field(None, ge=0, le=150, description="Maximum age")
    date_of_birth_from: Optional[date] = Field(
        None, description="Date of birth from (inclusive)"
    )
    date_of_birth_to: Optional[date] = Field(
        None, description="Date of birth to (inclusive)"
    )

    # Location
    city: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Filter by city"
    )
    country: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Filter by country"
    )

    # Medical history flags
    has_allergies: Optional[bool] = Field(
        None, description="Filter patients with allergies"
    )
    has_medical_history: Optional[bool] = Field(
        None, description="Filter patients with medical history"
    )

    # Date range filters
    created_from: Optional[datetime] = Field(
        None, description="Filter records created from date"
    )
    created_to: Optional[datetime] = Field(
        None, description="Filter records created to date"
    )
    updated_from: Optional[datetime] = Field(
        None, description="Filter records updated from date"
    )
    updated_to: Optional[datetime] = Field(
        None, description="Filter records updated to date"
    )

    # Sorting
    sort_by: str = Field(
        "created_at",
        pattern="^(first_name|last_name|date_of_birth|created_at|updated_at|email)$",
        description="Field to sort by",
    )
    sort_order: str = Field(
        "desc", pattern="^(asc|desc)$", description="Sort order"
    )

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=200, description="Items per page")

    @property
    def skip(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query"""
        return self.page_size


class PatientExportFormat(str, Enum):
    """Export format options"""

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    JSON = "json"


class PatientExportRequest(BaseModel):
    """Request schema for patient data export"""

    format: PatientExportFormat = Field(..., description="Export format")
    filters: Optional[PatientAdvancedFilters] = Field(
        None, description="Filters to apply before export"
    )
    include_fields: Optional[list[str]] = Field(
        None,
        description="Specific fields to include (if None, all fields included)",
    )
    include_sensitive: bool = Field(
        False, description="Include sensitive medical data (requires special permission)"
    )
