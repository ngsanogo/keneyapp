"""
AI-Powered Recommendation Service
Provides intelligent recommendations for patient care, appointments, and prescriptions.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.user import User, UserRole


class RecommendationService:
    """Service for generating intelligent recommendations."""

    def __init__(self, db: Session):
        self.db = db

    def get_patient_care_recommendations(
        self, patient_id: int, tenant_id: int
    ) -> List[Dict]:
        """
        Generate personalized care recommendations for a patient.

        Args:
            patient_id: Patient ID
            tenant_id: Tenant ID for isolation

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        patient = (
            self.db.query(Patient)
            .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
            .first()
        )

        if not patient:
            return recommendations

        # Check for overdue appointments
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
            days_since = (
                datetime.now().date() - last_appointment.appointment_date
            ).days
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

        # Check prescription refills
        active_prescriptions = (
            self.db.query(Prescription)
            .filter(
                Prescription.patient_id == patient_id,
                Prescription.tenant_id == tenant_id,
            )
            .all()
        )

        for prescription in active_prescriptions:
            if prescription.end_date:
                days_until_end = (prescription.end_date - datetime.now().date()).days
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
        if not patient.allergies or patient.allergies.strip() == "":
            recommendations.append(
                {
                    "type": "data_quality",
                    "priority": "low",
                    "title": "Update Allergy Information",
                    "description": "No allergy information on file. Please update patient record.",
                    "action": "update_patient",
                    "metadata": {"field": "allergies"},
                }
            )

        if not patient.emergency_contact or patient.emergency_contact.strip() == "":
            recommendations.append(
                {
                    "type": "data_quality",
                    "priority": "medium",
                    "title": "Add Emergency Contact",
                    "description": "No emergency contact on file. Critical for patient safety.",
                    "action": "update_patient",
                    "metadata": {"field": "emergency_contact"},
                }
            )

        return recommendations

    def get_appointment_slot_recommendations(
        self, doctor_id: int, date: datetime, tenant_id: int
    ) -> List[Dict]:
        """
        Recommend optimal appointment slots based on doctor availability and patterns.

        Args:
            doctor_id: Doctor user ID
            date: Target date for appointments
            tenant_id: Tenant ID for isolation

        Returns:
            List of recommended time slots
        """
        # Get existing appointments for the doctor on that date
        existing_appointments = (
            self.db.query(Appointment)
            .filter(
                and_(
                    Appointment.doctor_id == doctor_id,
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.appointment_date) == date.date(),
                    Appointment.status != AppointmentStatus.CANCELLED,
                )
            )
            .all()
        )

        # Define working hours (9 AM to 5 PM)
        working_start = 9
        working_end = 17
        slot_duration = 30  # 30-minute slots

        occupied_slots = []
        for apt in existing_appointments:
            start_hour = apt.appointment_date.hour
            occupied_slots.append(start_hour)

        # Generate recommended slots
        recommendations = []
        for hour in range(working_start, working_end):
            if hour not in occupied_slots:
                slot_time = datetime.combine(date.date(), datetime.min.time()).replace(
                    hour=hour
                )
                recommendations.append(
                    {
                        "time": slot_time.strftime("%H:%M"),
                        "available": True,
                        "recommended": hour in [9, 10, 14, 15],  # Morning and afternoon
                        "reason": "Optimal time based on patient flow patterns",
                    }
                )

        return recommendations

    def get_medication_interaction_warnings(
        self, patient_id: int, new_medication: str, tenant_id: int
    ) -> List[Dict]:
        """
        Check for potential medication interactions.

        Args:
            patient_id: Patient ID
            new_medication: New medication to check
            tenant_id: Tenant ID for isolation

        Returns:
            List of interaction warnings
        """
        warnings = []

        # Get active prescriptions for the patient
        active_prescriptions = (
            self.db.query(Prescription)
            .filter(
                Prescription.patient_id == patient_id,
                Prescription.tenant_id == tenant_id,
                or_(
                    Prescription.end_date.is_(None),
                    Prescription.end_date >= datetime.now().date(),
                ),
            )
            .all()
        )

        # Simple interaction checking (in production, use a comprehensive drug database)
        known_interactions = {
            "warfarin": ["aspirin", "ibuprofen"],
            "metformin": ["alcohol"],
            "lisinopril": ["potassium"],
        }

        new_med_lower = new_medication.lower()
        for prescription in active_prescriptions:
            existing_med = prescription.medication_name.lower()

            # Check if new medication interacts with existing
            if (
                new_med_lower in known_interactions
                and existing_med in known_interactions[new_med_lower]
            ):
                warnings.append(
                    {
                        "severity": "high",
                        "medication_1": new_medication,
                        "medication_2": prescription.medication_name,
                        "description": f"Potential interaction between {new_medication} and {prescription.medication_name}",
                        "recommendation": "Consult with pharmacist before prescribing",
                    }
                )

            # Check if existing medication interacts with new
            if (
                existing_med in known_interactions
                and new_med_lower in known_interactions[existing_med]
            ):
                warnings.append(
                    {
                        "severity": "high",
                        "medication_1": prescription.medication_name,
                        "medication_2": new_medication,
                        "description": f"Potential interaction between {prescription.medication_name} and {new_medication}",
                        "recommendation": "Consult with pharmacist before prescribing",
                    }
                )

        return warnings

    def get_resource_optimization_recommendations(self, tenant_id: int) -> List[Dict]:
        """
        Provide recommendations for optimizing resource utilization.

        Args:
            tenant_id: Tenant ID for isolation

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        # Check doctor workload distribution
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

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
            avg_load = sum(load[2] for load in doctor_loads) / len(doctor_loads)
            for doctor_id, doctor_name, load in doctor_loads:
                if load > avg_load * 1.5:
                    recommendations.append(
                        {
                            "type": "workload_balance",
                            "priority": "medium",
                            "title": f"High Workload for Dr. {doctor_name}",
                            "description": f"Dr. {doctor_name} has {load} appointments this week, {int((load/avg_load - 1) * 100)}% above average.",
                            "action": "redistribute_appointments",
                            "metadata": {
                                "doctor_id": doctor_id,
                                "current_load": load,
                                "average_load": int(avg_load),
                            },
                        }
                    )

        # Check for appointment no-shows pattern
        no_show_rate = (
            self.db.query(func.count(Appointment.id))
            .filter(
                Appointment.tenant_id == tenant_id,
                Appointment.status == AppointmentStatus.CANCELLED,
                Appointment.appointment_date >= today - timedelta(days=30),
            )
            .scalar()
            or 0
        )

        total_recent = (
            self.db.query(func.count(Appointment.id))
            .filter(
                Appointment.tenant_id == tenant_id,
                Appointment.appointment_date >= today - timedelta(days=30),
            )
            .scalar()
            or 0
        )

        if total_recent > 0 and (no_show_rate / total_recent) > 0.15:
            recommendations.append(
                {
                    "type": "no_show_reduction",
                    "priority": "high",
                    "title": "High Appointment Cancellation Rate",
                    "description": f"Cancellation rate is {int((no_show_rate / total_recent) * 100)}%. Consider implementing reminder system.",
                    "action": "enable_reminders",
                    "metadata": {
                        "cancellation_rate": round(
                            (no_show_rate / total_recent) * 100, 1
                        ),
                        "total_appointments": total_recent,
                    },
                }
            )

        return recommendations
