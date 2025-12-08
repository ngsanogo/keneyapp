"""
Patient service layer for business logic and validation.

Separates business rules from HTTP routing layer for better testability
and maintainability. Follows patterns from GNU Health and ERPNext.
"""

from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

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
            .options(
                selectinload(Patient.appointments),
                selectinload(Patient.documents)
            )
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

        # Add eager loading to prevent N+1 queries
        query = query.options(
            selectinload(Patient.appointments),
            selectinload(Patient.documents)
        )

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

    def list_patients_advanced(
        self,
        tenant_id: int,
        search: Optional[str] = None,
        gender: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        date_of_birth_from: Optional[date] = None,
        date_of_birth_to: Optional[date] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        has_allergies: Optional[bool] = None,
        has_medical_history: Optional[bool] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        updated_from: Optional[datetime] = None,
        updated_to: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Patient], int]:
        """
        Advanced patient search with multiple filter criteria.

        Args:
            tenant_id: Tenant ID for isolation
            search: Text search across name, email, phone, address
            gender: Filter by gender
            min_age: Minimum age filter
            max_age: Maximum age filter
            date_of_birth_from: DOB range start
            date_of_birth_to: DOB range end
            city: Filter by city
            country: Filter by country
            has_allergies: Filter patients with/without allergies
            has_medical_history: Filter patients with/without medical history
            created_from: Record creation date start
            created_to: Record creation date end
            updated_from: Record update date start
            updated_to: Record update date end
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            skip: Pagination offset
            limit: Max results

        Returns:
            Tuple of (list of Patient instances, total count)
        """
        query = self.db.query(Patient).filter(Patient.tenant_id == tenant_id)

        # Text search across multiple fields
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                    Patient.email.ilike(search_pattern),
                    Patient.phone.ilike(search_pattern),
                    Patient.address.ilike(search_pattern),
                )
            )

        # Gender filter
        if gender and gender != "all":
            query = query.filter(Patient.gender == gender)

        # Age filters (calculated from date of birth)
        if min_age is not None or max_age is not None:
            today = date.today()
            if max_age is not None:
                min_dob = date(today.year - max_age - 1, today.month, today.day)
                query = query.filter(Patient.date_of_birth >= min_dob)
            if min_age is not None:
                max_dob = date(today.year - min_age, today.month, today.day)
                query = query.filter(Patient.date_of_birth <= max_dob)

        # Date of birth range
        if date_of_birth_from:
            query = query.filter(Patient.date_of_birth >= date_of_birth_from)
        if date_of_birth_to:
            query = query.filter(Patient.date_of_birth <= date_of_birth_to)

        # Location filters (note: address field stores full address, may need parsing)
        if city:
            city_pattern = f"%{city}%"
            query = query.filter(Patient.address.ilike(city_pattern))
        if country:
            country_pattern = f"%{country}%"
            query = query.filter(Patient.address.ilike(country_pattern))

        # Medical history flags
        if has_allergies is not None:
            if has_allergies:
                query = query.filter(Patient.allergies.isnot(None))
                query = query.filter(Patient.allergies != "")
            else:
                query = query.filter(
                    or_(Patient.allergies.is_(None), Patient.allergies == "")
                )

        if has_medical_history is not None:
            if has_medical_history:
                query = query.filter(Patient.medical_history.isnot(None))
                query = query.filter(Patient.medical_history != "")
            else:
                query = query.filter(
                    or_(
                        Patient.medical_history.is_(None),
                        Patient.medical_history == "",
                    )
                )

        # Date range filters for created_at
        if created_from:
            query = query.filter(Patient.created_at >= created_from)
        if created_to:
            end_of_day = datetime.combine(
                created_to.date() if isinstance(created_to, datetime) else created_to,
                datetime.max.time(),
            )
            query = query.filter(Patient.created_at <= end_of_day)

        # Date range filters for updated_at
        if updated_from:
            query = query.filter(Patient.updated_at >= updated_from)
        if updated_to:
            end_of_day = datetime.combine(
                updated_to.date() if isinstance(updated_to, datetime) else updated_to,
                datetime.max.time(),
            )
            query = query.filter(Patient.updated_at <= end_of_day)

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(Patient, sort_by, None)
        if sort_column is not None:
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(Patient.created_at.desc())

        # Apply pagination
        patients = query.offset(skip).limit(min(200, max(1, limit))).all()

        return patients, total
