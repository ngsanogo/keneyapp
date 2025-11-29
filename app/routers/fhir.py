"""
FHIR API Router for KeneyApp.
Provides HL7 FHIR-compliant endpoints for healthcare interoperability.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.rate_limit import limiter
from app.fhir.converters import fhir_converter
from app.fhir.utils import make_search_bundle, operation_outcome
from app.models.appointment import Appointment
from app.models.medical_code import Condition as ConditionModel
from app.models.medical_code import Observation as ObservationModel
from app.models.medical_code import Procedure as ProcedureModel
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.user import User, UserRole
from app.services.patient_security import encrypt_patient_payload

router = APIRouter(prefix="/fhir", tags=["FHIR"])


@router.get("/Patient/{patient_id}")
@limiter.limit("100/minute")
def get_fhir_patient(
    patient_id: int,
    request: Request,
    response: Response,
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
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=operation_outcome("not-found", "Patient not found"),
        )

    # Weak ETag based on last update
    if getattr(patient, "updated_at", None):
        response.headers["ETag"] = (
            f'W/"Patient/{patient.id}-{patient.updated_at.timestamp()}"'
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
    patient_data = encrypt_patient_payload(fhir_converter.fhir_to_patient(fhir_patient))

    # Create patient
    patient = Patient(**patient_data, tenant_id=current_user.tenant_id)
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return fhir_converter.patient_to_fhir(patient)


@router.get("/Patient")
@limiter.limit("100/minute")
def search_fhir_patient(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST
        )
    ),
    name: Optional[str] = Query(None, description="Search in family or given"),
    family: Optional[str] = Query(None, description="Family name"),
    given: Optional[str] = Query(None, description="Given name"),
    birthdate: Optional[str] = Query(None, description="YYYY-MM-DD"),
    _count: int = Query(20, ge=1, le=100),
    _page: int = Query(1, ge=1),
):
    """FHIR Patient search (subset of R4 parameters)."""
    query = db.query(Patient).filter(Patient.tenant_id == current_user.tenant_id)

    # Basic parameters mapping
    if name:
        like = f"%{name}%"
        query = query.filter(
            (Patient.first_name.ilike(like)) | (Patient.last_name.ilike(like))
        )
    if family:
        query = query.filter(Patient.last_name.ilike(f"%{family}%"))
    if given:
        query = query.filter(Patient.first_name.ilike(f"%{given}%"))
    if birthdate:
        # R4 allows prefixes; we implement exact match for simplicity
        query = query.filter(Patient.date_of_birth == birthdate)

    total = query.count()

    # Pagination
    offset = (_page - 1) * _count
    patients: List[Patient] = (
        query.order_by(Patient.id.asc()).offset(offset).limit(_count).all()
    )

    # Convert to FHIR and bundle
    fhir_list = [fhir_converter.patient_to_fhir(p) for p in patients]
    base_url = (
        str(request.base_url).rstrip("/") + request.url.path
    )  # /api/v1/fhir/Patient
    base_url = base_url.rsplit("/", 1)[0]  # /api/v1/fhir
    query_params = {
        "name": name,
        "family": family,
        "given": given,
        "birthdate": birthdate,
    }
    bundle = make_search_bundle(
        base_url=base_url,
        resource_type="Patient",
        resources=fhir_list,
        total=total,
        page=_page,
        count=_count,
        query_params=query_params,
    )
    return bundle


@router.get("/Appointment/{appointment_id}")
@limiter.limit("100/minute")
def get_fhir_appointment(
    appointment_id: int,
    request: Request,
    response: Response,
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
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=operation_outcome("not-found", "Appointment not found"),
        )

    # Weak ETag based on last update
    if getattr(appointment, "updated_at", None):
        response.headers["ETag"] = (
            f'W/"Appointment/{appointment.id}-{appointment.updated_at.timestamp()}"'
        )

    return fhir_converter.appointment_to_fhir(appointment)


@router.get("/MedicationRequest/{prescription_id}")
@limiter.limit("100/minute")
def get_fhir_medication_request(
    prescription_id: int,
    request: Request,
    response: Response,
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
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=operation_outcome("not-found", "Prescription not found"),
        )

    # Weak ETag based on last update
    if getattr(prescription, "updated_at", None):
        response.headers["ETag"] = (
            f'W/"MedicationRequest/{prescription.id}-{prescription.updated_at.timestamp()}"'
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
        "date": "2025-01-01",
        "kind": "instance",
        "software": {"name": "KeneyApp", "version": settings.APP_VERSION},
        "implementation": {
            "description": "KeneyApp FHIR Server",
            "url": str(request.base_url).rstrip("/") + str(router.prefix),
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "search-type"},
                        ],
                        "searchParam": [
                            {"name": "name", "type": "string"},
                            {"name": "family", "type": "string"},
                            {"name": "given", "type": "string"},
                            {"name": "birthdate", "type": "date"},
                        ],
                    },
                    {
                        "type": "Appointment",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                        "searchParam": [
                            {"name": "patient", "type": "reference"},
                            {"name": "date", "type": "date"},
                            {"name": "status", "type": "token"},
                        ],
                    },
                    {
                        "type": "Observation",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                        "searchParam": [
                            {"name": "patient", "type": "reference"},
                            {"name": "code", "type": "token"},
                            {"name": "date", "type": "date"},
                            {"name": "status", "type": "token"},
                        ],
                    },
                    {
                        "type": "Condition",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                        "searchParam": [
                            {"name": "patient", "type": "reference"},
                            {"name": "code", "type": "token"},
                            {"name": "clinical-status", "type": "token"},
                        ],
                    },
                    {
                        "type": "Procedure",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                        "searchParam": [
                            {"name": "patient", "type": "reference"},
                            {"name": "code", "type": "token"},
                            {"name": "date", "type": "date"},
                        ],
                    },
                    {"type": "MedicationRequest", "interaction": [{"code": "read"}]},
                ],
            }
        ],
    }


@router.get("/Appointment")
@limiter.limit("100/minute")
def search_fhir_appointment(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST
        )
    ),
    patient: Optional[int] = Query(None, description="Patient ID reference"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD (filters by day)"),
    status: Optional[str] = Query(None, description="Appointment status token"),
    _count: int = Query(20, ge=1, le=100),
    _page: int = Query(1, ge=1),
):
    """FHIR Appointment search (subset)."""
    query = db.query(Appointment).filter(
        Appointment.tenant_id == current_user.tenant_id
    )

    if patient is not None:
        query = query.filter(Appointment.patient_id == patient)
    if date:
        # Filter by same calendar day (simplified); relies on database casting
        # This is a minimal approach; for production use proper range filtering
        query = query.filter(
            cast(Appointment.appointment_date, String).like(f"{date}%")
        )
    if status:
        query = query.filter(Appointment.status == status)

    total = query.count()
    offset = (_page - 1) * _count
    appts: List[Appointment] = (
        query.order_by(Appointment.id.asc()).offset(offset).limit(_count).all()
    )

    fhir_list = [fhir_converter.appointment_to_fhir(a) for a in appts]
    base_url = str(request.base_url).rstrip("/") + request.url.path
    base_url = base_url.rsplit("/", 1)[0]
    query_params = {"patient": patient, "date": date, "status": status}
    bundle = make_search_bundle(
        base_url=base_url,
        resource_type="Appointment",
        resources=fhir_list,
        total=total,
        page=_page,
        count=_count,
        query_params=query_params,
    )
    return bundle


@router.get("/Observation/{observation_id}")
@limiter.limit("100/minute")
def get_fhir_observation(
    observation_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE)
    ),
):
    """Get Observation in FHIR format."""
    obs = (
        db.query(ObservationModel)
        .filter(
            ObservationModel.id == observation_id,
            ObservationModel.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not obs:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=operation_outcome("not-found", "Observation not found"),
        )

    if getattr(obs, "updated_at", None):
        response.headers["ETag"] = (
            f'W/"Observation/{obs.id}-{obs.updated_at.timestamp()}"'
        )

    return fhir_converter.observation_to_fhir(obs)


@router.get("/Observation")
@limiter.limit("100/minute")
def search_fhir_observation(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE)
    ),
    patient: Optional[int] = Query(None, description="Patient ID reference"),
    code: Optional[str] = Query(None, description="LOINC code token"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD (filters by day)"),
    status: Optional[str] = Query(None, description="Observation status token"),
    _count: int = Query(20, ge=1, le=100),
    _page: int = Query(1, ge=1),
):
    """FHIR Observation search (subset)."""
    query = db.query(ObservationModel).filter(
        ObservationModel.tenant_id == current_user.tenant_id
    )

    if patient is not None:
        query = query.filter(ObservationModel.patient_id == patient)
    if code:
        query = query.filter(ObservationModel.loinc_code == code)
    if date:
        query = query.filter(
            cast(ObservationModel.effective_datetime, String).like(f"{date}%")
        )
    if status:
        query = query.filter(ObservationModel.status == status)

    total = query.count()
    offset = (_page - 1) * _count
    obs_list: List[ObservationModel] = (
        query.order_by(ObservationModel.id.asc()).offset(offset).limit(_count).all()
    )

    fhir_list = [fhir_converter.observation_to_fhir(o) for o in obs_list]
    base_url = str(request.base_url).rstrip("/") + request.url.path
    base_url = base_url.rsplit("/", 1)[0]
    query_params = {"patient": patient, "code": code, "date": date, "status": status}
    bundle = make_search_bundle(
        base_url=base_url,
        resource_type="Observation",
        resources=fhir_list,
        total=total,
        page=_page,
        count=_count,
        query_params=query_params,
    )
    return bundle


@router.get("/Condition/{condition_id}")
@limiter.limit("100/minute")
def get_fhir_condition(
    condition_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE)
    ),
):
    """Get Condition in FHIR format."""
    condition = (
        db.query(ConditionModel)
        .filter(
            ConditionModel.id == condition_id,
            ConditionModel.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not condition:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=operation_outcome("not-found", "Condition not found"),
        )

    if getattr(condition, "updated_at", None):
        response.headers["ETag"] = (
            f'W/"Condition/{condition.id}-{condition.updated_at.timestamp()}"'
        )

    return fhir_converter.condition_to_fhir(condition)


@router.get("/Condition")
@limiter.limit("100/minute")
def search_fhir_condition(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE)
    ),
    patient: Optional[int] = Query(None, description="Patient ID reference"),
    code: Optional[str] = Query(None, description="ICD-11 or SNOMED CT code token"),
    clinical_status: Optional[str] = Query(
        None,
        alias="clinical-status",
        description="Clinical status token (active, resolved, etc.)",
    ),
    _count: int = Query(20, ge=1, le=100),
    _page: int = Query(1, ge=1),
):
    """FHIR Condition search (subset)."""
    query = db.query(ConditionModel).filter(
        ConditionModel.tenant_id == current_user.tenant_id
    )

    if patient is not None:
        query = query.filter(ConditionModel.patient_id == patient)
    if code:
        # Search in both icd11_code and snomed_code
        query = query.filter(
            (ConditionModel.icd11_code == code) | (ConditionModel.snomed_code == code)
        )
    if clinical_status:
        query = query.filter(ConditionModel.clinical_status == clinical_status)

    total = query.count()
    offset = (_page - 1) * _count
    conditions: List[ConditionModel] = (
        query.order_by(ConditionModel.id.asc()).offset(offset).limit(_count).all()
    )

    fhir_list = [fhir_converter.condition_to_fhir(c) for c in conditions]
    base_url = str(request.base_url).rstrip("/") + request.url.path
    base_url = base_url.rsplit("/", 1)[0]
    query_params = {
        "patient": patient,
        "code": code,
        "clinical-status": clinical_status,
    }
    bundle = make_search_bundle(
        base_url=base_url,
        resource_type="Condition",
        resources=fhir_list,
        total=total,
        page=_page,
        count=_count,
        query_params=query_params,
    )
    return bundle


@router.get("/Procedure/{procedure_id}")
@limiter.limit("100/minute")
def get_fhir_procedure(
    procedure_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE)
    ),
):
    """Get Procedure in FHIR format."""
    procedure = (
        db.query(ProcedureModel)
        .filter(
            ProcedureModel.id == procedure_id,
            ProcedureModel.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not procedure:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=operation_outcome("not-found", "Procedure not found"),
        )

    if getattr(procedure, "updated_at", None):
        response.headers["ETag"] = (
            f'W/"Procedure/{procedure.id}-{procedure.updated_at.timestamp()}"'
        )

    return fhir_converter.procedure_to_fhir(procedure)


@router.get("/Procedure")
@limiter.limit("100/minute")
def search_fhir_procedure(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE)
    ),
    patient: Optional[int] = Query(None, description="Patient ID reference"),
    code: Optional[str] = Query(None, description="CPT, CCAM, or SNOMED CT code token"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD (filters by day)"),
    _count: int = Query(20, ge=1, le=100),
    _page: int = Query(1, ge=1),
):
    """FHIR Procedure search (subset)."""
    query = db.query(ProcedureModel).filter(
        ProcedureModel.tenant_id == current_user.tenant_id
    )

    if patient is not None:
        query = query.filter(ProcedureModel.patient_id == patient)
    if code:
        # Search in cpt_code, ccam_code, or snomed_code
        query = query.filter(
            (ProcedureModel.cpt_code == code)
            | (ProcedureModel.ccam_code == code)
            | (ProcedureModel.snomed_code == code)
        )
    if date:
        query = query.filter(
            cast(ProcedureModel.performed_datetime, String).like(f"{date}%")
        )

    total = query.count()
    offset = (_page - 1) * _count
    procedures: List[ProcedureModel] = (
        query.order_by(ProcedureModel.id.asc()).offset(offset).limit(_count).all()
    )

    fhir_list = [fhir_converter.procedure_to_fhir(p) for p in procedures]
    base_url = str(request.base_url).rstrip("/") + request.url.path
    base_url = base_url.rsplit("/", 1)[0]
    query_params = {"patient": patient, "code": code, "date": date}
    bundle = make_search_bundle(
        base_url=base_url,
        resource_type="Procedure",
        resources=fhir_list,
        total=total,
        page=_page,
        count=_count,
        query_params=query_params,
    )
    return bundle


@router.post("/", status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
def fhir_bundle_transaction(  # noqa: C901
    bundle: Dict[str, Any],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    """
    Minimal FHIR Bundle transaction endpoint (batch GET only).
    Accepts a FHIR Bundle of type 'batch' and executes contained GET requests atomically.
    If any entry fails, returns OperationOutcome and no changes are made.
    """
    if bundle.get("resourceType") != "Bundle" or bundle.get("type") != "batch":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=operation_outcome("invalid", "Only batch Bundle supported"),
        )
    entries = bundle.get("entry", [])
    responses = []
    for entry in entries:
        req = entry.get("request", {})
        method = req.get("method", "GET").upper()
        url = req.get("url", "")
        if method != "GET":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=operation_outcome("not-supported", "Only GET batch supported"),
            )
        # Only support Patient, Appointment, Observation, Condition, Procedure, MedicationRequest
        if url.startswith("Patient/"):
            patient_id = url.split("/")[1]
            patient = (
                db.query(Patient)
                .filter(
                    Patient.id == patient_id,
                    Patient.tenant_id == current_user.tenant_id,
                )
                .first()
            )
            if not patient:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=operation_outcome(
                        "not-found", f"Patient {patient_id} not found"
                    ),
                )
            resource = fhir_converter.patient_to_fhir(patient)
        elif url.startswith("Appointment/"):
            appointment_id = url.split("/")[1]
            appointment = (
                db.query(Appointment)
                .filter(
                    Appointment.id == appointment_id,
                    Appointment.tenant_id == current_user.tenant_id,
                )
                .first()
            )
            if not appointment:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=operation_outcome(
                        "not-found", f"Appointment {appointment_id} not found"
                    ),
                )
            resource = fhir_converter.appointment_to_fhir(appointment)
        elif url.startswith("Observation/"):
            obs_id = url.split("/")[1]
            obs = (
                db.query(ObservationModel)
                .filter(
                    ObservationModel.id == obs_id,
                    ObservationModel.tenant_id == current_user.tenant_id,
                )
                .first()
            )
            if not obs:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=operation_outcome(
                        "not-found", f"Observation {obs_id} not found"
                    ),
                )
            resource = fhir_converter.observation_to_fhir(obs)
        elif url.startswith("Condition/"):
            cond_id = url.split("/")[1]
            cond = (
                db.query(ConditionModel)
                .filter(
                    ConditionModel.id == cond_id,
                    ConditionModel.tenant_id == current_user.tenant_id,
                )
                .first()
            )
            if not cond:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=operation_outcome(
                        "not-found", f"Condition {cond_id} not found"
                    ),
                )
            resource = fhir_converter.condition_to_fhir(cond)
        elif url.startswith("Procedure/"):
            proc_id = url.split("/")[1]
            proc = (
                db.query(ProcedureModel)
                .filter(
                    ProcedureModel.id == proc_id,
                    ProcedureModel.tenant_id == current_user.tenant_id,
                )
                .first()
            )
            if not proc:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=operation_outcome(
                        "not-found", f"Procedure {proc_id} not found"
                    ),
                )
            resource = fhir_converter.procedure_to_fhir(proc)
        elif url.startswith("MedicationRequest/"):
            rx_id = url.split("/")[1]
            rx = (
                db.query(Prescription)
                .filter(
                    Prescription.id == rx_id,
                    Prescription.tenant_id == current_user.tenant_id,
                )
                .first()
            )
            if not rx:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=operation_outcome(
                        "not-found", f"MedicationRequest {rx_id} not found"
                    ),
                )
            resource = fhir_converter.prescription_to_fhir(rx)
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=operation_outcome(
                    "not-supported", f"Resource {url} not supported in batch"
                ),
            )
        responses.append(
            {
                "response": {"status": "200 OK"},
                "resource": resource,
            }
        )
    return {"resourceType": "Bundle", "type": "batch-response", "entry": responses}
