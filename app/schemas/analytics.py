"""
Analytics response schemas
"""

from typing import List
from pydantic import BaseModel, Field


class DashboardMetrics(BaseModel):
    """Key dashboard metrics"""
    total_patients: int = Field(..., description="Total number of patients")
    patients_change: float = Field(..., description="Percentage change from last month")
    appointments_today: int = Field(..., description="Number of appointments today")
    appointments_change: float = Field(..., description="Percentage change from yesterday")
    active_doctors: int = Field(..., description="Number of active doctors")
    doctors_change: float = Field(..., description="Percentage change from last month")
    monthly_revenue: float = Field(..., description="Revenue for current month")
    revenue_change: float = Field(..., description="Percentage change from last month")


class PatientTrendResponse(BaseModel):
    """Patient registration trend data"""
    labels: List[str] = Field(..., description="Date labels")
    values: List[int] = Field(..., description="Patient counts per date")


class AppointmentStatsResponse(BaseModel):
    """Appointment statistics by status"""
    labels: List[str] = Field(..., description="Date labels")
    completed: List[int] = Field(..., description="Completed appointment counts")
    pending: List[int] = Field(..., description="Pending appointment counts")
    cancelled: List[int] = Field(..., description="Cancelled appointment counts")


class GenderDistributionResponse(BaseModel):
    """Patient gender distribution"""
    labels: List[str] = Field(..., description="Gender labels")
    values: List[int] = Field(..., description="Patient counts per gender")
