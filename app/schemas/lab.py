"""Pydantic schemas for laboratory test types and criteria."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LabTestTypeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    specimen_type: Optional[str] = Field(default=None, max_length=128)
    gender: Optional[str] = Field(default=None, pattern="^[mf]$")
    min_age_years: Optional[float] = None
    max_age_years: Optional[float] = None
    category: Optional[str] = Field(default=None, max_length=64)
    report_style: Optional[str] = Field(default=None, max_length=64)
    tags: Optional[str] = Field(default=None, max_length=255)
    active: Optional[bool] = True


class LabTestTypeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    specimen_type: Optional[str] = Field(default=None, max_length=128)
    gender: Optional[str] = Field(default=None, pattern="^[mf]$")
    min_age_years: Optional[float] = None
    max_age_years: Optional[float] = None
    category: Optional[str] = Field(default=None, max_length=64)
    report_style: Optional[str] = Field(default=None, max_length=64)
    tags: Optional[str] = Field(default=None, max_length=255)
    active: Optional[bool] = None


class LabTestTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    code: str
    name: str
    specimen_type: Optional[str]
    gender: Optional[str]
    min_age_years: Optional[float]
    max_age_years: Optional[float]
    category: Optional[str]
    report_style: Optional[str]
    tags: Optional[str]
    active: bool
    created_at: datetime
    updated_at: datetime
