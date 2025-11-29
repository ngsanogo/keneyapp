"""
Patient service layer for business logic and validation.

Separates business rules from HTTP routing layer for better testability
and maintainability. Follows patterns from GNU Health and ERPNext.
"""

from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.exceptions import (
    DuplicateResourceError,
    PatientNotFoundError,
    raise_if_not_found,
    raise_if_tenant_mismatch,
)
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.patient_security import encrypt_patient_payload


class PatientService:
    """Service for patient CRUD operations and business logic."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, patient_id: int, tenant_id: int) -> Patient:
        """
        Retrieve a patient by ID within tenant scope.

        Args:
            patient_id: Patient ID
            tenant_id: Tenant ID for isolation

        Returns:
            Patient instance

        Raises:
            PatientNotFoundError: If patient doesn't exist or belongs to different tenant
        """
        patient = (
            self.db.query(Patient)
            .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
            .first()
        )
        if not patient:
            raise PatientNotFoundError()
        return patient

    def get_by_email(self, email: str, tenant_id: int) -> Optional[Patient]:
        """
        Find a patient by email within tenant scope.

        Args:
            email: Patient email address
            tenant_id: Tenant ID for isolation

        Returns:
            Patient instance or None if not found
        """
        return (
            self.db.query(Patient)
            .filter(Patient.email == email, Patient.tenant_id == tenant_id)
            .first()
        )

    def list_patients(
        self, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> List[Patient]:
        """
        List patients with pagination.

        Args:
            tenant_id: Tenant ID for isolation
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Patient instances
        """
        return (
            self.db.query(Patient)
            .filter(Patient.tenant_id == tenant_id)
            .offset(skip)
            .limit(min(100, max(1, limit)))
            .all()
        )

    def list_patients_paginated(
        self,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Tuple[List[Patient], int]:
        """
        List patients with pagination, filtering, and sorting.

        Args:
            tenant_id: Tenant ID for isolation
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search term (searches first_name, last_name, email, phone)
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            date_from: Filter patients created after this date
            date_to: Filter patients created before this date

        Returns:
            Tuple of (list of Patient instances, total count)
        """
        query = self.db.query(Patient).filter(Patient.tenant_id == tenant_id)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                    Patient.email.ilike(search_pattern),
                    Patient.phone.ilike(search_pattern),
                )
            )

        # Apply date filters
        if date_from:
            query = query.filter(Patient.created_at >= date_from)
        if date_to:
            # Include entire day
            end_of_day = datetime.combine(date_to, datetime.max.time())
            query = query.filter(Patient.created_at <= end_of_day)

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        if sort_by:
            sort_column = getattr(Patient, sort_by, None)
            if sort_column is not None:
                if sort_order == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
        else:
            # Default sort by created_at descending
            query = query.order_by(Patient.created_at.desc())

        # Apply pagination
        patients = query.offset(skip).limit(min(100, max(1, limit))).all()

        return patients, total

    def count_patients(self, tenant_id: int) -> int:
        """
        Count total patients in tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Total patient count
        """
        return (
            self.db.query(func.count(Patient.id))
            .filter(Patient.tenant_id == tenant_id)
            .scalar()
        )

    def create_patient(self, patient_data: PatientCreate, tenant_id: int) -> Patient:
        """
        Create a new patient with validation and encryption.

        Args:
            patient_data: Patient creation data
            tenant_id: Tenant ID for ownership

        Returns:
            Created Patient instance

        Raises:
            DuplicateResourceError: If email already exists in tenant
        """
        # Check for duplicate email
        if patient_data.email:
            existing = self.get_by_email(patient_data.email, tenant_id)
            if existing:
                raise DuplicateResourceError("Patient", patient_data.email)

        # Encrypt sensitive fields before persistence
        encrypted_payload = encrypt_patient_payload(patient_data.model_dump())

        # Create patient
        patient = Patient(**encrypted_payload, tenant_id=tenant_id)
        self.db.add(patient)
        self.db.flush()  # Get ID without committing
        return patient

    def update_patient(
        self, patient_id: int, patient_data: PatientUpdate, tenant_id: int
    ) -> Patient:
        """
        Update an existing patient with encryption.

        Args:
            patient_id: Patient ID
            patient_data: Updated patient data
            tenant_id: Tenant ID for isolation

        Returns:
            Updated Patient instance

        Raises:
            PatientNotFoundError: If patient doesn't exist
            TenantMismatchError: If patient belongs to different tenant
            DuplicateResourceError: If new email already exists
        """
        patient = self.get_by_id(patient_id, tenant_id)

        # Check email uniqueness if changing email
        update_dict = patient_data.model_dump(exclude_unset=True)
        if "email" in update_dict and update_dict["email"] != patient.email:
            existing = self.get_by_email(update_dict["email"], tenant_id)
            if existing and existing.id != patient_id:
                raise DuplicateResourceError("Patient", update_dict["email"])

        # Encrypt sensitive fields if present
        encrypted_update = encrypt_patient_payload(update_dict)

        # Update fields
        for field, value in encrypted_update.items():
            setattr(patient, field, value)

        self.db.flush()
        return patient

    def delete_patient(self, patient_id: int, tenant_id: int) -> None:
        """
        Delete a patient.

        Args:
            patient_id: Patient ID
            tenant_id: Tenant ID for isolation

        Raises:
            PatientNotFoundError: If patient doesn't exist
            TenantMismatchError: If patient belongs to different tenant
        """
        patient = self.get_by_id(patient_id, tenant_id)
        self.db.delete(patient)
        self.db.flush()

    def validate_patient_access(self, patient_id: int, user_tenant_id: int) -> Patient:
        """
        Validate that a user can access a patient.

        Args:
            patient_id: Patient ID
            user_tenant_id: User's tenant ID

        Returns:
            Patient instance if access is valid

        Raises:
            PatientNotFoundError: If patient doesn't exist
            TenantMismatchError: If patient belongs to different tenant
        """
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        raise_if_not_found(patient, "Patient")
        raise_if_tenant_mismatch(patient.tenant_id, user_tenant_id)
        return patient

    def search_patients(
        self, tenant_id: int, query: str, skip: int = 0, limit: int = 100
    ) -> List[Patient]:
        """
        Search patients by name or email.

        Args:
            tenant_id: Tenant ID for isolation
            query: Search query string
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching Patient instances
        """
        search_pattern = f"%{query}%"
        return (
            self.db.query(Patient)
            .filter(
                Patient.tenant_id == tenant_id,
                (
                    Patient.first_name.ilike(search_pattern)
                    | Patient.last_name.ilike(search_pattern)
                    | Patient.email.ilike(search_pattern)
                ),
            )
            .offset(skip)
            .limit(min(100, max(1, limit)))
            .all()
        )
