"""
Pydantic schemas for medical codes and clinical data.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# Medical Code Schemas
class MedicalCodeBase(BaseModel):
    """Base schema for medical codes."""
    
    code_system: str
    code: str
    display: str
    definition: Optional[str] = None
    parent_code: Optional[str] = None


class MedicalCodeCreate(MedicalCodeBase):
    """Schema for creating medical codes."""
    pass


class MedicalCodeResponse(MedicalCodeBase):
    """Schema for medical code responses."""
    
    id: int
    is_active: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Coding Schema (FHIR-compatible)
class CodingSchema(BaseModel):
    """FHIR-compatible coding schema."""
    
    system: str = Field(..., description="URI for the code system")
    code: str = Field(..., description="The code value")
    display: Optional[str] = Field(None, description="Human-readable display text")


# Condition Schemas
class ConditionBase(BaseModel):
    """Base schema for conditions."""
    
    clinical_status: str = "active"
    verification_status: str = "confirmed"
    severity: Optional[str] = None
    icd11_code: Optional[str] = None
    icd11_display: Optional[str] = None
    snomed_code: Optional[str] = None
    snomed_display: Optional[str] = None
    notes: Optional[str] = None
    onset_date: Optional[datetime] = None
    abatement_date: Optional[datetime] = None


class ConditionCreate(ConditionBase):
    """Schema for creating conditions."""
    
    patient_id: int


class ConditionResponse(ConditionBase):
    """Schema for condition responses."""
    
    id: int
    tenant_id: int
    patient_id: int
    recorded_by_id: Optional[int] = None
    recorded_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Observation Schemas
class ObservationBase(BaseModel):
    """Base schema for observations."""
    
    status: str = "final"
    loinc_code: str
    loinc_display: str
    value_quantity: Optional[str] = None
    value_unit: Optional[str] = None
    value_string: Optional[str] = None
    reference_range_low: Optional[str] = None
    reference_range_high: Optional[str] = None
    interpretation: Optional[str] = None
    effective_datetime: datetime
    notes: Optional[str] = None


class ObservationCreate(ObservationBase):
    """Schema for creating observations."""
    
    patient_id: int


class ObservationResponse(ObservationBase):
    """Schema for observation responses."""
    
    id: int
    tenant_id: int
    patient_id: int
    performer_id: Optional[int] = None
    issued_datetime: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Procedure Schemas
class ProcedureBase(BaseModel):
    """Base schema for procedures."""
    
    status: str = "completed"
    cpt_code: Optional[str] = None
    cpt_display: Optional[str] = None
    ccam_code: Optional[str] = None
    ccam_display: Optional[str] = None
    snomed_code: Optional[str] = None
    snomed_display: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None
    performed_datetime: datetime


class ProcedureCreate(ProcedureBase):
    """Schema for creating procedures."""
    
    patient_id: int


class ProcedureResponse(ProcedureBase):
    """Schema for procedure responses."""
    
    id: int
    tenant_id: int
    patient_id: int
    performed_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
