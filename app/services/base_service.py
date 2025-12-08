"""
Base service class with common CRUD operations.

This base class provides reusable patterns for service layer operations,
reducing code duplication and ensuring consistency across services.
"""

from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session

from app.core.database import Base
from app.exceptions import ResourceNotFoundError, TenantMismatchError

# Type variable for model classes
ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """
    Base service class with common CRUD operations.

    Provides standard create, read, update, delete operations with
    built-in tenant isolation and error handling.

    Usage:
        class PatientService(BaseService[Patient]):
            def __init__(self, db: Session):
                super().__init__(db, Patient)
    """

    def __init__(self, db: Session, model: Type[ModelType]):
        """
        Initialize service with database session and model class.

        Args:
            db: SQLAlchemy database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    def get_by_id(
        self, id: int, tenant_id: Optional[int] = None, raise_if_not_found: bool = True
    ) -> Optional[ModelType]:
        """
        Get a single record by ID with optional tenant filtering.

        Args:
            id: Record ID
            tenant_id: Optional tenant ID for multi-tenant filtering
            raise_if_not_found: Whether to raise exception if not found

        Returns:
            Model instance or None

        Raises:
            ResourceNotFoundError: If record not found and raise_if_not_found is True
            TenantMismatchError: If record exists but belongs to different tenant
        """
        # First query by ID without tenant filter to detect tenant mismatch
        query = self.db.query(self.model).filter(self.model.id == id)
        record = query.first()

        # Check tenant mismatch before reporting not found
        if record and tenant_id is not None and hasattr(record, "tenant_id"):
            if record.tenant_id != tenant_id:
                raise TenantMismatchError(
                    f"{self.model.__name__} {id} does not belong to tenant {tenant_id}"
                )

        # If no record or tenant mismatch was already handled
        if record is None and raise_if_not_found:
            raise ResourceNotFoundError(detail=f"{self.model.__name__} with id={id} not found")

        return record

    def list(
        self,
        tenant_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None,
        include_deleted: bool = False,
    ) -> List[ModelType]:
        """
        List records with pagination and optional filtering.

        Args:
            tenant_id: Optional tenant ID for multi-tenant filtering
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            filters: Optional dict of filters to apply
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of model instances
        """
        query = self.db.query(self.model)

        # Apply tenant filter
        if tenant_id is not None and hasattr(self.model, "tenant_id"):
            query = query.filter(self.model.tenant_id == tenant_id)

        # Filter out soft-deleted records
        if not include_deleted and hasattr(self.model, "is_deleted"):
            query = query.filter(~self.model.is_deleted)

        # Apply custom filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        return query.all()

    def count(
        self,
        tenant_id: Optional[int] = None,
        filters: Optional[dict] = None,
        include_deleted: bool = False,
    ) -> int:
        """
        Count records with optional filtering.

        Args:
            tenant_id: Optional tenant ID for multi-tenant filtering
            filters: Optional dict of filters to apply
            include_deleted: Whether to include soft-deleted records

        Returns:
            Count of matching records
        """
        query = self.db.query(self.model)

        # Apply tenant filter
        if tenant_id is not None and hasattr(self.model, "tenant_id"):
            query = query.filter(self.model.tenant_id == tenant_id)

        # Filter out soft-deleted records
        if not include_deleted and hasattr(self.model, "is_deleted"):
            query = query.filter(~self.model.is_deleted)

        # Apply custom filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)

        return query.count()

    def create(self, data: dict, tenant_id: Optional[int] = None, commit: bool = True) -> ModelType:
        """
        Create a new record.

        Args:
            data: Dictionary of field values
            tenant_id: Optional tenant ID to assign
            commit: Whether to commit immediately

        Returns:
            Created model instance
        """
        # Add tenant_id if model supports it
        if tenant_id is not None and hasattr(self.model, "tenant_id"):
            data["tenant_id"] = tenant_id

        record = self.model(**data)
        self.db.add(record)

        if commit:
            self.db.commit()
            self.db.refresh(record)

        return record

    def update(
        self, id: int, data: dict, tenant_id: Optional[int] = None, commit: bool = True
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            id: Record ID
            data: Dictionary of field values to update
            tenant_id: Optional tenant ID for verification
            commit: Whether to commit immediately

        Returns:
            Updated model instance

        Raises:
            ResourceNotFoundError: If record not found
            TenantMismatchError: If record belongs to different tenant
        """
        record = self.get_by_id(id, tenant_id=tenant_id)

        # Update fields
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        if commit:
            self.db.commit()
            self.db.refresh(record)

        return record

    def delete(
        self,
        id: int,
        tenant_id: Optional[int] = None,
        soft_delete: bool = True,
        commit: bool = True,
    ) -> bool:
        """
        Delete a record (soft or hard delete).

        Args:
            id: Record ID
            tenant_id: Optional tenant ID for verification
            soft_delete: Whether to soft delete (set is_deleted=True)
            commit: Whether to commit immediately

        Returns:
            True if deleted successfully

        Raises:
            ResourceNotFoundError: If record not found
            TenantMismatchError: If record belongs to different tenant
        """
        record = self.get_by_id(id, tenant_id=tenant_id)

        if soft_delete and hasattr(record, "is_deleted"):
            # Soft delete
            record.is_deleted = True
        else:
            # Hard delete
            self.db.delete(record)

        if commit:
            self.db.commit()

        return True

    def bulk_create(
        self, data_list: List[dict], tenant_id: Optional[int] = None, commit: bool = True
    ) -> List[ModelType]:
        """
        Create multiple records in bulk.

        Args:
            data_list: List of dictionaries with field values
            tenant_id: Optional tenant ID to assign to all records
            commit: Whether to commit immediately

        Returns:
            List of created model instances
        """
        records = []

        for data in data_list:
            # Add tenant_id if model supports it
            if tenant_id is not None and hasattr(self.model, "tenant_id"):
                data["tenant_id"] = tenant_id

            record = self.model(**data)
            self.db.add(record)
            records.append(record)

        if commit:
            self.db.commit()
            for record in records:
                self.db.refresh(record)

        return records

    def exists(self, id: int, tenant_id: Optional[int] = None) -> bool:
        """
        Check if a record exists.

        Args:
            id: Record ID
            tenant_id: Optional tenant ID for filtering

        Returns:
            True if record exists, False otherwise
        """
        query = self.db.query(self.model.id).filter(self.model.id == id)

        if tenant_id is not None and hasattr(self.model, "tenant_id"):
            query = query.filter(self.model.tenant_id == tenant_id)

        return query.first() is not None
