"""
Analytics response schemas
"""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DashboardMetrics(BaseModel):
    """Key dashboard metrics"""

    total_patients: int = Field(..., description="Total number of patients")
    patients_change: float = Field(..., description="Percentage change from last month")
    appointments_today: int = Field(..., description="Number of appointments today")
    appointments_change: float = Field(
        ..., description="Percentage change from yesterday"
    )
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


class DateRangeParams(BaseModel):
    """Date range filter parameters"""

    date_from: Optional[date] = Field(None, description="Start date (inclusive)")
    date_to: Optional[date] = Field(None, description="End date (inclusive)")

    def get_date_range(self) -> tuple[datetime, datetime]:
        """
        Get datetime range for queries.

        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        if self.date_from and self.date_to:
            start = datetime.combine(self.date_from, datetime.min.time())
            end = datetime.combine(self.date_to, datetime.max.time())
        elif self.date_from:
            start = datetime.combine(self.date_from, datetime.min.time())
            end = datetime.now()
        elif self.date_to:
            # Default to 30 days before date_to
            end = datetime.combine(self.date_to, datetime.max.time())
            from datetime import timedelta

            start = end - timedelta(days=30)
        else:
            # Default to last 30 days
            from datetime import timedelta

            end = datetime.now()
            start = end - timedelta(days=30)

        return start, end


class CustomPeriodMetrics(BaseModel):
    """Metrics for a custom date range"""

    period_start: date
    period_end: date
    total_patients: int
    new_patients: int
    total_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    pending_appointments: int
    total_prescriptions: int
    unique_doctors_seen: int


class AgeDistributionResponse(BaseModel):
    """Patient age distribution"""

    labels: List[str] = Field(..., description="Age range labels")
    values: List[int] = Field(..., description="Patient counts per age range")


class TopConditionsResponse(BaseModel):
    """Top medical conditions"""

    conditions: List[str] = Field(..., description="Condition names")
    counts: List[int] = Field(..., description="Number of patients per condition")


class DoctorPerformanceResponse(BaseModel):
    """Doctor performance metrics"""

    doctor_names: List[str]
    appointments_count: List[int]
    completion_rate: List[float]
    average_rating: List[float]
