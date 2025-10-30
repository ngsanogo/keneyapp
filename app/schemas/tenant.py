"""
Tenant schemas for request and response validation.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TenantBase(BaseModel):
    """Shared tenant attributes."""

    name: str
    slug: str
    contact_email: Optional[EmailStr] = None
    region: Optional[str] = None
    default_timezone: Optional[str] = "UTC"
    is_active: bool = True
    configuration: Dict[str, Any] = Field(default_factory=dict)


class TenantCreate(TenantBase):
    """Payload for creating a tenant."""

    pass


class TenantUpdate(BaseModel):
    """Payload for updating tenant properties."""

    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    region: Optional[str] = None
    default_timezone: Optional[str] = None
    is_active: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None


class TenantResponse(TenantBase):
    """Tenant response payload."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantModuleBase(BaseModel):
    """Base attributes for tenant modules."""

    module_key: str
    is_enabled: bool = True
    configuration: Dict[str, Any] = Field(default_factory=dict)


class TenantModuleUpsert(BaseModel):
    """Request payload to create or update a tenant module."""

    is_enabled: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None


class TenantModuleResponse(TenantModuleBase):
    """Tenant module response."""

    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
