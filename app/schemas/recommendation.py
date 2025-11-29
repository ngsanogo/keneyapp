"""
Pydantic schemas for recommendation system
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class PatientCareRecommendation(BaseModel):
    """Schema for patient care recommendations"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "type": "follow_up",
                "priority": "high",
                "title": "Schedule Follow-up Appointment",
                "description": "Last appointment was 200 days ago. Consider scheduling a follow-up.",
                "action": "schedule_appointment",
                "metadata": {"days_since_last": 200},
            }
        },
    )

    type: str = Field(
        ...,
        description="Type of recommendation (follow_up, prescription_refill, data_quality)",
    )
    priority: str = Field(..., description="Priority level (low, medium, high)")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    action: str = Field(..., description="Suggested action to take")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class AppointmentSlotRecommendation(BaseModel):
    """Schema for appointment slot recommendations"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "time": "10:00",
                "available": True,
                "recommended": True,
                "reason": "Optimal time based on patient flow patterns",
            }
        },
    )

    time: str = Field(..., description="Time slot in HH:MM format")
    available: bool = Field(..., description="Whether the slot is available")
    recommended: bool = Field(..., description="Whether this is a recommended time")
    reason: Optional[str] = Field(None, description="Reason for recommendation")


class MedicationInteractionWarning(BaseModel):
    """Schema for medication interaction warnings"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "severity": "high",
                "medication_1": "Warfarin",
                "medication_2": "Aspirin",
                "description": "Potential interaction between Warfarin and Aspirin",
                "recommendation": "Consult with pharmacist before prescribing",
            }
        },
    )

    severity: str = Field(
        ..., description="Severity level (low, medium, high, critical)"
    )
    medication_1: str = Field(..., description="First medication name")
    medication_2: str = Field(..., description="Second medication name")
    description: str = Field(..., description="Description of the interaction")
    recommendation: str = Field(..., description="Recommended action")


class ResourceOptimizationRecommendation(BaseModel):
    """Schema for resource optimization recommendations"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "type": "workload_balance",
                "priority": "medium",
                "title": "High Workload for Dr. Smith",
                "description": "Dr. Smith has 45 appointments this week, 50% above average.",
                "action": "redistribute_appointments",
                "metadata": {
                    "doctor_id": 5,
                    "current_load": 45,
                    "average_load": 30,
                },
            }
        },
    )

    type: str = Field(
        ...,
        description="Type of optimization (workload_balance, no_show_reduction, etc.)",
    )
    priority: str = Field(..., description="Priority level (low, medium, high)")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    action: str = Field(..., description="Suggested action to take")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
