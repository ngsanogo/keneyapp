"""
FHIR Resource Converters for KeneyApp.
Converts between KeneyApp models and FHIR resources for interoperability.
"""

from typing import Any, Dict

from fhir.resources.address import Address
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.humanname import HumanName
from fhir.resources.identifier import Identifier
from fhir.resources.patient import Patient as FHIRPatient

from app.models.appointment import Appointment
from app.models.patient import Patient
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
        # Build medication codeable concept with ATC code if available
        medication_concept = {"text": prescription.medication_name}

        # Add ATC coding if available
        if prescription.atc_code:
            medication_concept["coding"] = [
                {
                    "system": "http://www.whocc.no/atc",
                    "code": prescription.atc_code,
                    "display": prescription.atc_display or prescription.medication_name,
                }
            ]

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
            "medicationCodeableConcept": medication_concept,
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

    @staticmethod
    def condition_to_fhir(condition) -> Dict[str, Any]:
        """
        Convert KeneyApp Condition to FHIR Condition resource.

        Args:
            condition: KeneyApp Condition model instance

        Returns:
            FHIR Condition resource as dictionary
        """
        # Build code with ICD-11 and SNOMED CT
        code_concept = {}
        codings = []

        if condition.icd11_code:
            codings.append(
                {
                    "system": "http://id.who.int/icd/release/11/mms",
                    "code": condition.icd11_code,
                    "display": condition.icd11_display or condition.icd11_code,
                }
            )

        if condition.snomed_code:
            codings.append(
                {
                    "system": "http://snomed.info/sct",
                    "code": condition.snomed_code,
                    "display": condition.snomed_display or condition.snomed_code,
                }
            )

        if codings:
            code_concept["coding"] = codings

        fhir_condition = {
            "resourceType": "Condition",
            "id": str(condition.id),
            "identifier": [
                {
                    "system": "https://keneyapp.com/condition-id",
                    "value": str(condition.id),
                }
            ],
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": condition.clinical_status,
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": condition.verification_status,
                    }
                ]
            },
            "code": code_concept,
            "subject": {"reference": f"Patient/{condition.patient_id}"},
        }

        if condition.severity:
            fhir_condition["severity"] = {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": condition.severity,
                        "display": condition.severity,
                    }
                ]
            }

        if condition.onset_date:
            fhir_condition["onsetDateTime"] = condition.onset_date.isoformat()

        if condition.abatement_date:
            fhir_condition["abatementDateTime"] = condition.abatement_date.isoformat()

        if condition.notes:
            fhir_condition["note"] = [{"text": condition.notes}]

        if condition.recorded_date:
            fhir_condition["recordedDate"] = condition.recorded_date.isoformat()

        return fhir_condition

    @staticmethod
    def observation_to_fhir(observation) -> Dict[str, Any]:
        """
        Convert KeneyApp Observation to FHIR Observation resource.

        Args:
            observation: KeneyApp Observation model instance

        Returns:
            FHIR Observation resource as dictionary
        """
        fhir_observation = {
            "resourceType": "Observation",
            "id": str(observation.id),
            "identifier": [
                {
                    "system": "https://keneyapp.com/observation-id",
                    "value": str(observation.id),
                }
            ],
            "status": observation.status,
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": observation.loinc_code,
                        "display": observation.loinc_display,
                    }
                ],
                "text": observation.loinc_display,
            },
            "subject": {"reference": f"Patient/{observation.patient_id}"},
            "effectiveDateTime": observation.effective_datetime.isoformat(),
        }

        # Add value based on type
        if observation.value_quantity and observation.value_unit:
            fhir_observation["valueQuantity"] = {
                "value": (
                    float(observation.value_quantity)
                    if observation.value_quantity
                    else None
                ),
                "unit": observation.value_unit,
            }
        elif observation.value_string:
            fhir_observation["valueString"] = observation.value_string

        # Add reference range if available
        if observation.reference_range_low or observation.reference_range_high:
            fhir_observation["referenceRange"] = [
                {
                    "low": (
                        {"value": float(observation.reference_range_low)}
                        if observation.reference_range_low
                        else None
                    ),
                    "high": (
                        {"value": float(observation.reference_range_high)}
                        if observation.reference_range_high
                        else None
                    ),
                }
            ]

        # Add interpretation
        if observation.interpretation:
            fhir_observation["interpretation"] = [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code": observation.interpretation.upper(),
                            "display": observation.interpretation,
                        }
                    ]
                }
            ]

        if observation.issued_datetime:
            fhir_observation["issued"] = observation.issued_datetime.isoformat()

        if observation.notes:
            fhir_observation["note"] = [{"text": observation.notes}]

        return fhir_observation

    @staticmethod
    def procedure_to_fhir(procedure) -> Dict[str, Any]:
        """
        Convert KeneyApp Procedure to FHIR Procedure resource.

        Args:
            procedure: KeneyApp Procedure model instance

        Returns:
            FHIR Procedure resource as dictionary
        """
        # Build code with CPT, CCAM, and SNOMED CT
        code_concept = {}
        codings = []

        if procedure.cpt_code:
            codings.append(
                {
                    "system": "http://www.ama-assn.org/go/cpt",
                    "code": procedure.cpt_code,
                    "display": procedure.cpt_display or procedure.cpt_code,
                }
            )

        if procedure.ccam_code:
            codings.append(
                {
                    "system": "http://www.ccam.fr",
                    "code": procedure.ccam_code,
                    "display": procedure.ccam_display or procedure.ccam_code,
                }
            )

        if procedure.snomed_code:
            codings.append(
                {
                    "system": "http://snomed.info/sct",
                    "code": procedure.snomed_code,
                    "display": procedure.snomed_display or procedure.snomed_code,
                }
            )

        if codings:
            code_concept["coding"] = codings

        fhir_procedure = {
            "resourceType": "Procedure",
            "id": str(procedure.id),
            "identifier": [
                {
                    "system": "https://keneyapp.com/procedure-id",
                    "value": str(procedure.id),
                }
            ],
            "status": procedure.status,
            "code": code_concept,
            "subject": {"reference": f"Patient/{procedure.patient_id}"},
            "performedDateTime": procedure.performed_datetime.isoformat(),
        }

        if procedure.category:
            fhir_procedure["category"] = {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": procedure.category,
                        "display": procedure.category,
                    }
                ]
            }

        if procedure.outcome:
            fhir_procedure["outcome"] = {"text": procedure.outcome}

        if procedure.notes:
            fhir_procedure["note"] = [{"text": procedure.notes}]

        if procedure.performed_by_id:
            fhir_procedure["performer"] = [
                {"actor": {"reference": f"Practitioner/{procedure.performed_by_id}"}}
            ]

        return fhir_procedure


# Global converter instance
fhir_converter = FHIRConverter()


__all__ = [
    "FHIRConverter",
    "fhir_converter",
]
