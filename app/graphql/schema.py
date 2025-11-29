"""
GraphQL schema and router configuration for KeneyApp.

The schema exposes a curated subset of the domain model with
proper multi-tenant scoping, role-based access control, and
auditing hooks to mirror the REST API guarantees.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Iterable, Optional

import strawberry
from fastapi import HTTPException, Request, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from strawberry.exceptions import GraphQLError
from strawberry.fastapi import GraphQLRouter
from strawberry.fastapi.context import BaseContext
from strawberry.types import Info

from app.core.audit import log_audit_event
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Gender, Patient
from app.models.prescription import Prescription
from app.models.user import User, UserRole
from app.services.patient_security import (
    encrypt_patient_payload,
    serialize_patient_model,
)

# GraphQL enums that mirror core application enums
GenderEnum = strawberry.enum(Gender, name="Gender")
AppointmentStatusEnum = strawberry.enum(AppointmentStatus, name="AppointmentStatus")
UserRoleEnum = strawberry.enum(UserRole, name="UserRole")


class GraphQLUserContext:
    """Minimal representation of the authenticated user for GraphQL."""

    def __init__(self, id: int, username: str, tenant_id: int, role: UserRole) -> None:
        self.id = id
        self.username = username
        self.tenant_id = tenant_id
        self.role = role

    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN


class GraphQLContext(BaseContext):
    """Execution context passed to Strawberry resolvers."""

    def __init__(
        self,
        request: Request,
        user: GraphQLUserContext,
        session_factory: Callable[[], Session],
    ) -> None:
        super().__init__()
        self.request = request
        self.user = user
        self.session_factory = session_factory


@contextmanager
def get_session(info: Info) -> Iterable[Session]:
    """Provide a short-lived SQLAlchemy session scoped to a resolver."""

    session = info.context.session_factory()
    try:
        yield session
    finally:
        session.close()


def ensure_roles(info: Info, allowed_roles: Iterable[UserRole]) -> None:
    """Enforce role-based access control for GraphQL resolvers."""

    allowed = set(allowed_roles)
    if info.context.user.is_super_admin:
        return

    if info.context.user.role not in allowed:
        raise GraphQLError("Insufficient permissions for this operation.")


def to_user_type(user: User) -> "UserType":
    """Map ORM user model to GraphQL type."""

    return UserType(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tenant_id=user.tenant_id,
        is_active=user.is_active,
        is_locked=user.is_locked,
        mfa_enabled=user.mfa_enabled,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def to_patient_type(patient: Patient) -> "PatientType":
    """Map ORM patient model to GraphQL type."""

    patient_response = serialize_patient_model(patient)

    return PatientType(
        id=patient_response.id,
        tenant_id=patient_response.tenant_id,
        first_name=patient_response.first_name,
        last_name=patient_response.last_name,
        date_of_birth=patient_response.date_of_birth,
        gender=patient_response.gender,
        email=patient_response.email,
        phone=patient_response.phone,
        address=patient_response.address,
        medical_history=patient_response.medical_history,
        allergies=patient_response.allergies,
        blood_type=patient_response.blood_type,
        emergency_contact=patient_response.emergency_contact,
        emergency_phone=patient_response.emergency_phone,
        created_at=patient_response.created_at,
        updated_at=patient_response.updated_at,
    )


def to_appointment_type(appointment: Appointment) -> "AppointmentType":
    """Map ORM appointment model to GraphQL type."""

    return AppointmentType(
        id=appointment.id,
        tenant_id=appointment.tenant_id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        appointment_date=appointment.appointment_date,
        duration_minutes=appointment.duration_minutes,
        status=appointment.status,
        reason=appointment.reason,
        notes=appointment.notes,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
    )


def to_prescription_type(prescription: Prescription) -> "PrescriptionType":
    """Map ORM prescription model to GraphQL type."""

    return PrescriptionType(
        id=prescription.id,
        tenant_id=prescription.tenant_id,
        patient_id=prescription.patient_id,
        doctor_id=prescription.doctor_id,
        medication_name=prescription.medication_name,
        dosage=prescription.dosage,
        frequency=prescription.frequency,
        duration=prescription.duration,
        instructions=prescription.instructions,
        refills=prescription.refills,
        prescribed_date=prescription.prescribed_date,
        created_at=prescription.created_at,
        updated_at=prescription.updated_at,
    )


@strawberry.type
class UserType:
    """GraphQL representation of a system user."""

    id: int
    username: str
    email: str
    full_name: str
    role: UserRoleEnum
    tenant_id: int
    is_active: bool
    is_locked: bool
    mfa_enabled: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class PatientType:
    """GraphQL representation of a patient."""

    id: int
    tenant_id: int
    first_name: str
    last_name: str
    date_of_birth: date
    gender: GenderEnum
    email: Optional[str]
    phone: str
    address: Optional[str]
    medical_history: Optional[str]
    allergies: Optional[str]
    blood_type: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class AppointmentType:
    """GraphQL representation of an appointment."""

    id: int
    tenant_id: int
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    duration_minutes: int
    status: AppointmentStatusEnum
    reason: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class PrescriptionType:
    """GraphQL representation of a prescription."""

    id: int
    tenant_id: int
    patient_id: int
    doctor_id: int
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str]
    refills: int
    prescribed_date: datetime
    created_at: datetime
    updated_at: datetime


@strawberry.type
class AppointmentsByStatusType:
    """Aggregate appointment counts by status."""

    scheduled: int
    confirmed: int
    in_progress: int
    completed: int
    cancelled: int
    no_show: int


@strawberry.type
class RecentActivityType:
    """Aggregate entity counts for the trailing seven days."""

    patients: int
    appointments: int
    prescriptions: int


@strawberry.type
class DashboardStatsType:
    """GraphQL representation of dashboard metrics."""

    total_patients: int
    total_appointments: int
    total_prescriptions: int
    today_appointments: int
    appointments_by_status: AppointmentsByStatusType
    recent_activity: RecentActivityType


@strawberry.input
class PatientCreateInput:
    """Input payload for creating a patient via GraphQL."""

    first_name: str
    last_name: str
    date_of_birth: date
    gender: GenderEnum
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


@strawberry.type
class Query:
    """GraphQL query root."""

    @strawberry.field
    def hello(self) -> str:
        """Simple hello query for smoke testing."""

        return "Hello from KeneyApp GraphQL API!"

    @strawberry.field(name="apiVersion")
    def api_version(self) -> str:
        """Expose the running API version."""

        return settings.APP_VERSION

    @strawberry.field
    def me(self, info: Info) -> UserType:
        """Retrieve the authenticated user's profile."""

        with get_session(info) as session:
            user = session.query(User).filter(User.id == info.context.user.id).first()

            if not user:
                raise GraphQLError("Authenticated user record could not be found.")

            return to_user_type(user)

    @strawberry.field
    def patients(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        search: Optional[str] = None,
    ) -> list[PatientType]:
        """List patients for the current tenant."""

        ensure_roles(
            info,
            [
                UserRole.ADMIN,
                UserRole.DOCTOR,
                UserRole.NURSE,
                UserRole.RECEPTIONIST,
            ],
        )

        limit = max(1, min(limit, 100))

        with get_session(info) as session:
            query = session.query(Patient).filter(Patient.tenant_id == info.context.user.tenant_id)

            if search:
                term = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Patient.first_name.ilike(term),
                        Patient.last_name.ilike(term),
                        Patient.email.ilike(term),
                        Patient.phone.ilike(term),
                    )
                )

            patients = (
                query.order_by(Patient.last_name.asc(), Patient.first_name.asc())
                .offset(max(0, offset))
                .limit(limit)
                .all()
            )

            return [to_patient_type(patient) for patient in patients]

    @strawberry.field
    def patient(self, info: Info, patient_id: int) -> Optional[PatientType]:
        """Retrieve a single patient by identifier."""

        ensure_roles(
            info,
            [
                UserRole.ADMIN,
                UserRole.DOCTOR,
                UserRole.NURSE,
                UserRole.RECEPTIONIST,
            ],
        )

        with get_session(info) as session:
            patient = (
                session.query(Patient)
                .filter(
                    Patient.id == patient_id,
                    Patient.tenant_id == info.context.user.tenant_id,
                )
                .first()
            )

            return to_patient_type(patient) if patient else None

    @strawberry.field
    def appointments(
        self,
        info: Info,
        status: Optional[AppointmentStatusEnum] = None,
        upcoming_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AppointmentType]:
        """List appointments scoped to the current tenant."""

        ensure_roles(
            info,
            [
                UserRole.ADMIN,
                UserRole.DOCTOR,
                UserRole.NURSE,
                UserRole.RECEPTIONIST,
            ],
        )

        limit = max(1, min(limit, 100))

        with get_session(info) as session:
            query = session.query(Appointment).filter(
                Appointment.tenant_id == info.context.user.tenant_id
            )

            if status:
                query = query.filter(Appointment.status == status)

            if upcoming_only:
                now = datetime.now(timezone.utc)
                query = query.filter(Appointment.appointment_date >= now)

            appointments = (
                query.order_by(Appointment.appointment_date.asc())
                .offset(max(0, offset))
                .limit(limit)
                .all()
            )

            return [to_appointment_type(appointment) for appointment in appointments]

    @strawberry.field
    def appointment(
        self,
        info: Info,
        appointment_id: int,
    ) -> Optional[AppointmentType]:
        """Retrieve a single appointment by identifier."""

        ensure_roles(
            info,
            [
                UserRole.ADMIN,
                UserRole.DOCTOR,
                UserRole.NURSE,
                UserRole.RECEPTIONIST,
            ],
        )

        with get_session(info) as session:
            appointment = (
                session.query(Appointment)
                .filter(
                    Appointment.id == appointment_id,
                    Appointment.tenant_id == info.context.user.tenant_id,
                )
                .first()
            )

            return to_appointment_type(appointment) if appointment else None

    @strawberry.field
    def prescriptions(
        self,
        info: Info,
        limit: int = 50,
        offset: int = 0,
        patient_id: Optional[int] = None,
    ) -> list[PrescriptionType]:
        """List prescriptions scoped to the current tenant."""

        ensure_roles(
            info,
            [
                UserRole.ADMIN,
                UserRole.DOCTOR,
                UserRole.NURSE,
            ],
        )

        limit = max(1, min(limit, 100))

        with get_session(info) as session:
            query = session.query(Prescription).filter(
                Prescription.tenant_id == info.context.user.tenant_id
            )

            if patient_id is not None:
                query = query.filter(Prescription.patient_id == patient_id)

            prescriptions = (
                query.order_by(Prescription.prescribed_date.desc())
                .offset(max(0, offset))
                .limit(limit)
                .all()
            )

            return [to_prescription_type(prescription) for prescription in prescriptions]

    @strawberry.field
    def prescription(
        self,
        info: Info,
        prescription_id: int,
    ) -> Optional[PrescriptionType]:
        """Retrieve a single prescription by identifier."""

        ensure_roles(
            info,
            [
                UserRole.ADMIN,
                UserRole.DOCTOR,
                UserRole.NURSE,
            ],
        )

        with get_session(info) as session:
            prescription = (
                session.query(Prescription)
                .filter(
                    Prescription.id == prescription_id,
                    Prescription.tenant_id == info.context.user.tenant_id,
                )
                .first()
            )

            return to_prescription_type(prescription) if prescription else None

    @strawberry.field(name="dashboardStats")
    def dashboard_stats(self, info: Info) -> DashboardStatsType:
        """Return the metrics powering the operational dashboard."""

        ensure_roles(info, [UserRole.ADMIN, UserRole.DOCTOR])

        tenant_id = info.context.user.tenant_id

        with get_session(info) as session:
            total_patients = (
                session.query(func.count(Patient.id))
                .filter(Patient.tenant_id == tenant_id)
                .scalar()
            ) or 0

            total_appointments = (
                session.query(func.count(Appointment.id))
                .filter(Appointment.tenant_id == tenant_id)
                .scalar()
            ) or 0

            total_prescriptions = (
                session.query(func.count(Prescription.id))
                .filter(Prescription.tenant_id == tenant_id)
                .scalar()
            ) or 0

            today = datetime.now(timezone.utc).date()
            today_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
            today_end = datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)

            today_appointments = (
                session.query(func.count(Appointment.id))
                .filter(
                    Appointment.tenant_id == tenant_id,
                    Appointment.appointment_date >= today_start,
                    Appointment.appointment_date <= today_end,
                )
                .scalar()
            ) or 0

            def _count_by_status(status: AppointmentStatus) -> int:
                return (
                    session.query(func.count(Appointment.id))
                    .filter(
                        Appointment.tenant_id == tenant_id,
                        Appointment.status == status,
                    )
                    .scalar()
                ) or 0

            appointments_by_status = AppointmentsByStatusType(
                scheduled=_count_by_status(AppointmentStatus.SCHEDULED),
                confirmed=_count_by_status(AppointmentStatus.CONFIRMED),
                in_progress=_count_by_status(AppointmentStatus.IN_PROGRESS),
                completed=_count_by_status(AppointmentStatus.COMPLETED),
                cancelled=_count_by_status(AppointmentStatus.CANCELLED),
                no_show=_count_by_status(AppointmentStatus.NO_SHOW),
            )

            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

            recent_patients = (
                session.query(func.count(Patient.id))
                .filter(
                    Patient.tenant_id == tenant_id,
                    Patient.created_at >= seven_days_ago,
                )
                .scalar()
            ) or 0

            recent_appointments = (
                session.query(func.count(Appointment.id))
                .filter(
                    Appointment.tenant_id == tenant_id,
                    Appointment.created_at >= seven_days_ago,
                )
                .scalar()
            ) or 0

            recent_prescriptions = (
                session.query(func.count(Prescription.id))
                .filter(
                    Prescription.tenant_id == tenant_id,
                    Prescription.created_at >= seven_days_ago,
                )
                .scalar()
            ) or 0

            recent_activity = RecentActivityType(
                patients=recent_patients,
                appointments=recent_appointments,
                prescriptions=recent_prescriptions,
            )

            return DashboardStatsType(
                total_patients=total_patients,
                total_appointments=total_appointments,
                total_prescriptions=total_prescriptions,
                today_appointments=today_appointments,
                appointments_by_status=appointments_by_status,
                recent_activity=recent_activity,
            )


@strawberry.type
class Mutation:
    """GraphQL mutation root."""

    @strawberry.mutation
    def create_patient(
        self,
        info: Info,
        payload: PatientCreateInput,
    ) -> PatientType:
        """Create a patient record for the current tenant."""

        ensure_roles(
            info,
            [
                UserRole.ADMIN,
                UserRole.DOCTOR,
                UserRole.NURSE,
            ],
        )

        with get_session(info) as session:
            encrypted_payload = encrypt_patient_payload(
                {
                    "first_name": payload.first_name,
                    "last_name": payload.last_name,
                    "date_of_birth": payload.date_of_birth,
                    "gender": payload.gender,
                    "email": payload.email,
                    "phone": payload.phone,
                    "address": payload.address,
                    "medical_history": payload.medical_history,
                    "allergies": payload.allergies,
                    "blood_type": payload.blood_type,
                    "emergency_contact": payload.emergency_contact,
                    "emergency_phone": payload.emergency_phone,
                }
            )

            patient = Patient(
                tenant_id=info.context.user.tenant_id,
                **encrypted_payload,
            )

            session.add(patient)

            try:
                session.commit()
            except IntegrityError as exc:  # pragma: no cover - defensive
                session.rollback()
                raise GraphQLError(
                    "Unable to create patient. Ensure identifiers are unique."
                ) from exc

            session.refresh(patient)

            log_audit_event(
                db=session,
                action="CREATE",
                resource_type="patient",
                resource_id=patient.id,
                status="success",
                user_id=info.context.user.id,
                username=info.context.user.username,
                details={"operation": "graphql_create"},
                request=info.context.request,
            )

            return to_patient_type(patient)


schema = strawberry.Schema(query=Query, mutation=Mutation)


async def _get_graphql_context(request: Request) -> GraphQLContext:
    """Resolve the Strawberry execution context, validating credentials."""

    authorization = request.headers.get("Authorization")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )

    username = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim.",
        )

    with SessionLocal() as session:
        user = session.query(User).filter(User.username == username).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with token no longer exists.",
            )

        if tenant_id is not None and user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tenant mismatch.",
            )

        if not user.is_active or user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled or locked.",
            )

        if not user.tenant.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant is inactive.",
            )

        user_context = GraphQLUserContext(
            id=user.id,
            username=user.username,
            tenant_id=user.tenant_id,
            role=user.role,
        )

    return GraphQLContext(
        request=request,
        user=user_context,
        session_factory=SessionLocal,
    )


def create_graphql_router() -> GraphQLRouter:
    """Instantiate the Strawberry GraphQL router with our context factory."""

    return GraphQLRouter(schema, context_getter=_get_graphql_context)


__all__ = [
    "schema",
    "create_graphql_router",
    "UserType",
    "PatientType",
    "AppointmentType",
    "PrescriptionType",
]
