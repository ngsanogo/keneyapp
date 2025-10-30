"""
FHIR API Router for KeneyApp.
Provides HL7 FHIR-compliant endpoints for healthcare interoperability.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.rate_limit import limiter
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.fhir.converters import fhir_converter

router = APIRouter(prefix="/fhir", tags=["FHIR"])


@router.get("/Patient/{patient_id}")
@limiter.limit("100/minute")
def get_fhir_patient(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE)
    ),
):
    """
    Get patient in FHIR format.

    Args:
        patient_id: Patient ID
        request: Request context
        db: Database session
        current_user: Authenticated user

    Returns:
        FHIR Patient resource
    """
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )

    return fhir_converter.patient_to_fhir(patient)


@router.post("/Patient", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_fhir_patient(
    fhir_patient: Dict[str, Any],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)
    ),
):
    """
    Create patient from FHIR resource.

    Args:
        fhir_patient: FHIR Patient resource
        request: Request context
        db: Database session
        current_user: Authenticated user

    Returns:
        Created FHIR Patient resource
    """
    # Convert FHIR to KeneyApp format
    patient_data = fhir_converter.fhir_to_patient(fhir_patient)

    # Create patient
    patient = Patient(**patient_data, tenant_id=current_user.tenant_id)
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return fhir_converter.patient_to_fhir(patient)


@router.get("/Appointment/{appointment_id}")
@limiter.limit("100/minute")
def get_fhir_appointment(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST
        )
    ),
):
    """
    Get appointment in FHIR format.

    Args:
        appointment_id: Appointment ID
        request: Request context
        db: Database session
        current_user: Authenticated user

    Returns:
        FHIR Appointment resource
    """
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )

    return fhir_converter.appointment_to_fhir(appointment)


@router.get("/MedicationRequest/{prescription_id}")
@limiter.limit("100/minute")
def get_fhir_medication_request(
    prescription_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE)
    ),
):
    """
    Get prescription as FHIR MedicationRequest.

    Args:
        prescription_id: Prescription ID
        request: Request context
        db: Database session
        current_user: Authenticated user

    Returns:
        FHIR MedicationRequest resource
    """
    prescription = (
        db.query(Prescription)
        .filter(
            Prescription.id == prescription_id,
            Prescription.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found"
        )

    return fhir_converter.prescription_to_fhir(prescription)


@router.get("/metadata")
@limiter.limit("100/minute")
def get_fhir_capability_statement(request: Request):
    """
    Get FHIR CapabilityStatement (server metadata).

    Returns:
        FHIR CapabilityStatement resource
    """
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2024-01-01",
        "kind": "instance",
        "software": {"name": "KeneyApp", "version": "1.0.0"},
        "implementation": {
            "description": "KeneyApp FHIR Server",
            "url": "https://keneyapp.com/fhir",
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
                        "interaction": [{"code": "read"}, {"code": "create"}],
                    },
                    {"type": "Appointment", "interaction": [{"code": "read"}]},
                    {"type": "MedicationRequest", "interaction": [{"code": "read"}]},
                ],
            }
        ],
    }
