"""
FHIR Resource Converters for KeneyApp.
Converts between KeneyApp models and FHIR resources for interoperability.
"""

from typing import Dict, Any
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.address import Address
from fhir.resources.identifier import Identifier

from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.services.patient_security import serialize_patient_dict


class FHIRConverter:
    """Convert KeneyApp models to FHIR resources."""

    @staticmethod
    def patient_to_fhir(patient: Patient) -> Dict[str, Any]:
        """
        Convert KeneyApp Patient to FHIR Patient resource.

        Args:
            patient: KeneyApp Patient model instance

        Returns:
            FHIR Patient resource as dictionary
        """
        patient_dict = serialize_patient_dict(patient)

        fhir_patient = FHIRPatient()

        # Identifier
        fhir_patient.identifier = [
            Identifier(
                **{
                    "system": "https://keneyapp.com/patient-id",
                    "value": str(patient_dict["id"]),
                }
            )
        ]

        # Name
        fhir_patient.name = [
            HumanName(
                **{
                    "family": patient_dict["last_name"],
                    "given": [patient_dict["first_name"]],
                    "use": "official",
                }
            )
        ]

        # Gender
        gender_map = {
            "male": "male",
            "female": "female",
            "other": "other",
            "unknown": "unknown",
        }
        fhir_patient.gender = gender_map.get(patient_dict["gender"].lower(), "unknown")

        # Birth date
        fhir_patient.birthDate = patient_dict["date_of_birth"]

        # Contact information
        if patient_dict["phone"]:
            fhir_patient.telecom = [
                ContactPoint(
                    **{
                        "system": "phone",
                        "value": patient_dict["phone"],
                        "use": "mobile",
                    }
                )
            ]

        if patient_dict["email"]:
            if not getattr(fhir_patient, "telecom", None):
                fhir_patient.telecom = []
            fhir_patient.telecom.append(
                ContactPoint(
                    **{
                        "system": "email",
                        "value": patient_dict["email"],
                        "use": "home",
                    }
                )
            )

        # Address
        if patient_dict["address"]:
            fhir_patient.address = [
                Address(
                    **{
                        "use": "home",
                        "text": patient_dict["address"],
                        "type": "physical",
                    }
                )
            ]

        # Active status
        fhir_patient.active = True

        return fhir_patient.dict()

    @staticmethod
    def fhir_to_patient(fhir_patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert FHIR Patient resource to KeneyApp Patient data.

        Args:
            fhir_patient: FHIR Patient resource dictionary

        Returns:
            Dictionary suitable for creating KeneyApp Patient
        """
        patient_data = {}

        # Extract name
        if fhir_patient.get("name"):
            name = fhir_patient["name"][0]
            patient_data["first_name"] = name.get("given", [""])[0]
            patient_data["last_name"] = name.get("family", "")

        # Extract gender
        patient_data["gender"] = fhir_patient.get("gender", "unknown")

        # Extract birth date
        patient_data["date_of_birth"] = fhir_patient.get("birthDate")

        # Extract contact information
        if fhir_patient.get("telecom"):
            for contact in fhir_patient["telecom"]:
                if contact.get("system") == "phone":
                    patient_data["phone"] = contact.get("value")
                elif contact.get("system") == "email":
                    patient_data["email"] = contact.get("value")

        # Extract address
        if fhir_patient.get("address"):
            patient_data["address"] = fhir_patient["address"][0].get("text", "")

        return patient_data

    @staticmethod
    def appointment_to_fhir(appointment: Appointment) -> Dict[str, Any]:
        """
        Convert KeneyApp Appointment to FHIR Appointment resource.

        Args:
            appointment: KeneyApp Appointment model instance

        Returns:
            FHIR Appointment resource as dictionary
        """
        # Status mapping
        status_map = {
            "scheduled": "booked",
            "completed": "fulfilled",
            "cancelled": "cancelled",
            "confirmed": "booked",
        }

        fhir_appointment = {
            "resourceType": "Appointment",
            "id": str(appointment.id),
            "identifier": [
                {
                    "system": "https://keneyapp.com/appointment-id",
                    "value": str(appointment.id),
                }
            ],
            "status": status_map.get(appointment.status, "booked"),
            "participant": [
                {
                    "actor": {"reference": f"Patient/{appointment.patient_id}"},
                    "status": "accepted",
                },
                {
                    "actor": {"reference": f"Practitioner/{appointment.doctor_id}"},
                    "status": "accepted",
                },
            ],
        }

        # Start time
        if appointment.appointment_date:
            fhir_appointment["start"] = appointment.appointment_date.isoformat()

        # Description
        if appointment.reason:
            fhir_appointment["description"] = appointment.reason

        # Comment/Notes
        if appointment.notes:
            fhir_appointment["comment"] = appointment.notes

        return fhir_appointment

    @staticmethod
    def prescription_to_fhir(prescription: Prescription) -> Dict[str, Any]:
        """
        Convert KeneyApp Prescription to FHIR MedicationRequest resource.

        Args:
            prescription: KeneyApp Prescription model instance

        Returns:
            FHIR MedicationRequest resource as dictionary
        """
        fhir_med_request = {
            "resourceType": "MedicationRequest",
            "id": str(prescription.id),
            "identifier": [
                {
                    "system": "https://keneyapp.com/prescription-id",
                    "value": str(prescription.id),
                }
            ],
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": prescription.medication_name},
            "subject": {"reference": f"Patient/{prescription.patient_id}"},
            "requester": {"reference": f"Practitioner/{prescription.doctor_id}"},
            "dosageInstruction": [
                {
                    "text": f"{prescription.dosage} {prescription.frequency} for {prescription.duration}",
                    "timing": {
                        "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
                    },
                }
            ],
        }

        if prescription.instructions:
            fhir_med_request["dosageInstruction"][0][
                "patientInstruction"
            ] = prescription.instructions

        # Authored date
        if prescription.prescribed_date:
            fhir_med_request["authoredOn"] = prescription.prescribed_date.isoformat()

        return fhir_med_request


# Global converter instance
fhir_converter = FHIRConverter()


__all__ = [
    "FHIRConverter",
    "fhir_converter",
]
