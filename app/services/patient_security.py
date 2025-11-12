"""
Utilities for handling patient data encryption/decryption workflows.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from app.core.encryption import decrypt_patient_data, encrypt_patient_data
from app.models.patient import Patient
from app.schemas.patient import PatientResponse

SENSITIVE_PATIENT_FIELDS: List[str] = [
    "medical_history",
    "allergies",
    "emergency_contact",
    "emergency_phone",
    "address",
]


def encrypt_patient_payload(payload: Dict) -> Dict:
    """
    Encrypt sensitive fields in a complete payload before persistence.

    Args:
        payload: Patient payload dictionary (create/update)

    Returns:
        Payload with sensitive fields encrypted.
    """
    return encrypt_patient_data(payload)


def decrypt_patient_payload(payload: Dict) -> Dict:
    """
    Decrypt sensitive fields from a payload prior to serialization.

    Args:
        payload: Dictionary containing patient fields

    Returns:
        Payload with decrypted sensitive fields.
    """
    return decrypt_patient_data(payload)


def serialize_patient_model(patient: Patient) -> PatientResponse:
    """
    Build a PatientResponse model with decrypted sensitive fields.

    Args:
        patient: SQLAlchemy patient instance

    Returns:
        PatientResponse instance with decrypted data
    """
    raw = PatientResponse.model_validate(patient).model_dump()
    decrypted = decrypt_patient_payload(raw)
    return PatientResponse(**decrypted)


def serialize_patient_dict(patient: Patient) -> Dict:
    """
    Return a JSON-friendly dictionary of a patient with decrypted data.

    Args:
        patient: SQLAlchemy patient instance

    Returns:
        JSON serializable dictionary
    """
    return serialize_patient_model(patient).model_dump(mode="json")


def serialize_patient_collection(patients: Iterable[Patient]) -> List[Dict]:
    """
    Serialize a collection of patient models with decrypted data.

    Args:
        patients: Iterable of SQLAlchemy patient instances

    Returns:
        List of JSON serializable dictionaries
    """
    return [serialize_patient_dict(patient) for patient in patients]
