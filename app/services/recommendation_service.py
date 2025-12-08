"""
AI-Powered Recommendation Service
Provides intelligent recommendations for patient care, appointments, and prescriptions.

This service helps identify actionable insights to improve patient outcomes,
optimize resource utilization, and detect potential issues early.
"""

from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.user import User, UserRole


class RecommendationService:
    """Service for generating intelligent recommendations."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _parse_duration_days(duration_str: str) -> int:
        """
        Parse duration string to extract number of days.

        Args:
            duration_str: Duration string like "30 days" or "90 days"

        Returns:
            Number of days or 0 if parsing fails
        """
        if not duration_str:
            return 0
        try:
            duration_lower = duration_str.lower()
            if "day" in duration_lower:
                days = int("".join(filter(str.isdigit, duration_lower)))
                return days
        except (ValueError, TypeError):
            pass
        return 0

    def get_patient_care_recommendations(self, patient_id: int, tenant_id: int) -> List[Dict]:
        """
        Generate personalized care recommendations for a patient.

        Checks for:
        - Overdue follow-ups (>180 days since last appointment)
        - Expiring prescriptions (7 days or less)
        - Missing critical information (allergies, emergency contact)

        Args:
            patient_id: Patient ID
            tenant_id: Tenant ID for isolation

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Fetch patient with basic validation
        patient = (
            self.db.query(Patient)
            .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
            .first()
        )
        if not patient:
            return recommendations

        # Check for overdue appointments using date arithmetic
        today = datetime.now().date()
        last_appointment = (
            self.db.query(Appointment)
            .filter(
                Appointment.patient_id == patient_id,
                Appointment.tenant_id == tenant_id,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
            .order_by(Appointment.appointment_date.desc())
            .first()
        )

        if last_appointment:
            appointment_date = (
                last_appointment.appointment_date.date()
                if isinstance(last_appointment.appointment_date, datetime)
                else last_appointment.appointment_date
            )
            days_since = (today - appointment_date).days

            if days_since > 180:
                recommendations.append(
                    {
                        "type": "follow_up",
                        "priority": "high",
                        "title": "Schedule Follow-up Appointment",
                        "description": f"Last appointment was {days_since} days ago. Consider scheduling a follow-up.",
                        "action": "schedule_appointment",
                        "metadata": {"days_since_last": days_since},
                    }
                )

        # Check prescription refills - single query instead of loading all
        prescriptions = (
            self.db.query(Prescription)
            .filter(
                Prescription.patient_id == patient_id,
                Prescription.tenant_id == tenant_id,
            )
            .all()
        )

        for prescription in prescriptions:
            if prescription.prescribed_date and prescription.duration:
                days = self._parse_duration_days(prescription.duration)
                if days > 0:
                    prescribed_date = (
                        prescription.prescribed_date.date()
                        if isinstance(prescription.prescribed_date, datetime)
                        else prescription.prescribed_date
                    )
                    end_date = prescribed_date + timedelta(days=days)
                    days_until_end = (end_date - today).days

                    if 0 < days_until_end <= 7:
                        recommendations.append(
                            {
                                "type": "prescription_refill",
                                "priority": "medium",
                                "title": "Prescription Expiring Soon",
                                "description": f"Prescription for {prescription.medication_name} expires in {days_until_end} days.",
                                "action": "renew_prescription",
                                "metadata": {
                                    "prescription_id": prescription.id,
                                    "medication": prescription.medication_name,
                                    "days_until_end": days_until_end,
                                },
                            }
                        )

        # Check for missing patient information
        missing_fields = []
        if not patient.allergies or patient.allergies.strip() == "":
            missing_fields.append(("allergies", "Allergy Information", "low"))
        if not patient.emergency_contact or patient.emergency_contact.strip() == "":
            missing_fields.append(("emergency_contact", "Emergency Contact", "medium"))

        for field_name, field_label, priority in missing_fields:
            recommendations.append(
                {
                    "type": "data_quality",
                    "priority": priority,
                    "title": f"Update {field_label}",
                    "description": f"No {field_label.lower()} on file. Please update patient record.",
                    "action": "update_patient",
                    "metadata": {"field": field_name},
                }
            )

        return recommendations

    def get_appointment_slot_recommendations(
        self, doctor_id: int, date: datetime, tenant_id: int
    ) -> List[Dict]:
        """
        Recommend optimal appointment slots based on doctor availability.

        Uses a simple heuristic: avoid 12-1 PM (lunch) and recommend morning/afternoon peak hours.

        Args:
            doctor_id: Doctor user ID
            date: Target date for appointments
            tenant_id: Tenant ID for isolation

        Returns:
            List of recommended time slots
        """
        target_date = date.date()

        # Get all occupied hours for the doctor on that date
        existing_appointments = (
            self.db.query(func.extract("hour", Appointment.appointment_date))
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.tenant_id == tenant_id,
                func.date(Appointment.appointment_date) == target_date,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .all()
        )

        occupied_hours = {int(apt[0]) for apt in existing_appointments if apt[0] is not None}

        # Define working hours and preferred times
        working_hours = range(9, 17)  # 9 AM to 5 PM
        preferred_hours = {9, 10, 14, 15}  # Morning and afternoon peaks
        lunch_hour = 12

        recommendations = []
        for hour in working_hours:
            if hour not in occupied_hours and hour != lunch_hour:
                recommendations.append(
                    {
                        "time": f"{hour:02d}:00",
                        "available": True,
                        "recommended": hour in preferred_hours,
                        "reason": (
                            "Optimal time based on peak appointment hours"
                            if hour in preferred_hours
                            else "Available slot"
                        ),
                    }
                )

        return recommendations

    def get_medication_interaction_warnings(
        self, patient_id: int, new_medication: str, tenant_id: int
    ) -> List[Dict]:
        """
        Check for potential medication interactions.

        Uses a simple interaction database. In production, integrate with
        a comprehensive pharmacy database (e.g., DrugBank, FDA).

        Args:
            patient_id: Patient ID
            new_medication: New medication to check
            tenant_id: Tenant ID for isolation

        Returns:
            List of interaction warnings
        """
        warnings = []

        # Get active prescriptions for the patient
        today = datetime.now().date()
        active_prescriptions = (
            self.db.query(Prescription)
            .filter(
                Prescription.patient_id == patient_id,
                Prescription.tenant_id == tenant_id,
                or_(
                    Prescription.end_date.is_(None),
                    Prescription.end_date >= today,
                ),
            )
            .all()
        )

        # Known interactions (simplified for demo - use proper drug database in production)
        known_interactions = {
            "warfarin": ["aspirin", "ibuprofen"],
            "metformin": ["alcohol"],
            "lisinopril": ["potassium"],
        }

        new_med_lower = new_medication.lower()

        for prescription in active_prescriptions:
            existing_med = prescription.medication_name.lower()

            # Check bidirectional interactions
            is_interaction = (
                new_med_lower in known_interactions
                and existing_med in known_interactions[new_med_lower]
            ) or (
                existing_med in known_interactions
                and new_med_lower in known_interactions[existing_med]
            )

            if is_interaction:
                warnings.append(
                    {
                        "severity": "high",
                        "medication_1": new_medication,
                        "medication_2": prescription.medication_name,
                        "description": f"Potential interaction between {new_medication} and {prescription.medication_name}",
                        "recommendation": "Consult with pharmacist before prescribing",
                    }
                )

        return warnings

    def get_resource_optimization_recommendations(self, tenant_id: int) -> List[Dict]:
        """
        Provide recommendations for optimizing resource utilization.

        Analyzes doctor workload distribution and appointment cancellation patterns
        to identify optimization opportunities.

        Args:
            tenant_id: Tenant ID for isolation

        Returns:
            List of optimization recommendations
        """
        recommendations = []
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

        # Get doctor workload - single aggregated query
        doctor_loads = (
            self.db.query(
                User.id,
                User.full_name,
                func.count(Appointment.id).label("appointment_count"),
            )
            .join(Appointment, User.id == Appointment.doctor_id)
            .filter(
                User.tenant_id == tenant_id,
                User.role == UserRole.DOCTOR,
                Appointment.appointment_date >= week_start,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .group_by(User.id, User.full_name)
            .all()
        )

        if doctor_loads:
            loads = [load[2] for load in doctor_loads]
            avg_load = sum(loads) / len(loads)

            for doctor_id, doctor_name, load in doctor_loads:
                if load > avg_load * 1.5:
                    overload_percent = int((load / avg_load - 1) * 100)
                    recommendations.append(
                        {
                            "type": "workload_balance",
                            "priority": "medium",
                            "title": f"High Workload for Dr. {doctor_name}",
                            "description": f"Dr. {doctor_name} has {load} appointments this week, {overload_percent}% above average.",
                            "action": "redistribute_appointments",
                            "metadata": {
                                "doctor_id": doctor_id,
                                "current_load": load,
                                "average_load": int(avg_load),
                            },
                        }
                    )

        # Check for appointment cancellation pattern - single aggregated query
        total_recent = (
            self.db.query(func.count(Appointment.id))
            .filter(
                Appointment.tenant_id == tenant_id,
                Appointment.appointment_date >= today - timedelta(days=30),
            )
            .scalar()
            or 0
        )

        if total_recent > 0:
            cancelled_count = (
                self.db.query(func.count(Appointment.id))
                .filter(
                    Appointment.tenant_id == tenant_id,
                    Appointment.status == AppointmentStatus.CANCELLED,
                    Appointment.appointment_date >= today - timedelta(days=30),
                )
                .scalar()
                or 0
            )

            cancellation_rate = cancelled_count / total_recent

            if cancellation_rate > 0.15:  # > 15% cancellation
                recommendations.append(
                    {
                        "type": "no_show_reduction",
                        "priority": "high",
                        "title": "High Appointment Cancellation Rate",
                        "description": f"Cancellation rate is {int(cancellation_rate * 100)}%. Consider implementing reminder system.",
                        "action": "enable_reminders",
                        "metadata": {
                            "cancellation_rate": round(cancellation_rate * 100, 1),
                            "total_appointments": total_recent,
                        },
                    }
                )

        return recommendations
