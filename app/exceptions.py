"""
Custom exception hierarchy for KeneyApp.

Following patterns from ERPNext and GNU Health for domain-specific errors.
"""

from fastapi import HTTPException, status


class KeneyAppException(HTTPException):
    """Base exception for KeneyApp domain errors."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "An error occurred"

    def __init__(self, detail: str = None, headers: dict = None):
        super().__init__(
            status_code=self.status_code, detail=detail or self.detail, headers=headers
        )


# ============================================================================
# Validation Errors (422 Unprocessable Entity)
# ============================================================================


class ValidationError(KeneyAppException):
    """Base class for validation errors."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation error"


class InvalidStateTransitionError(ValidationError):
    """Raised when attempting an invalid state transition."""

    def __init__(self, from_state: str, to_state: str):
        super().__init__(detail=f"Cannot transition from {from_state} to {to_state}")


class InvalidLabResultError(ValidationError):
    """Raised when lab result data is invalid."""

    detail = "Lab result data is invalid"


class LabResultAlreadyValidatedError(ValidationError):
    """Raised when trying to modify a validated lab result."""

    detail = "Lab result has already been validated and cannot be modified"


class LabResultNotModifiableError(ValidationError):
    """Raised when lab result state doesn't allow modification."""

    def __init__(self, state: str):
        super().__init__(detail=f"Lab result in state '{state}' cannot be modified")


class InvalidAgeForTestError(ValidationError):
    """Raised when patient age doesn't meet test requirements."""

    def __init__(
        self, patient_age: float, min_age: float = None, max_age: float = None
    ):
        if min_age is not None and max_age is not None:
            msg = f"Test requires age between {min_age} and {max_age} years (patient: {patient_age})"
        elif min_age is not None:
            msg = f"Test requires age ≥{min_age} years (patient: {patient_age})"
        else:
            msg = f"Test requires age ≤{max_age} years (patient: {patient_age})"
        super().__init__(detail=msg)


class InvalidGenderForTestError(ValidationError):
    """Raised when patient gender doesn't match test requirements."""

    def __init__(self, patient_gender: str, required_gender: str):
        super().__init__(
            detail=f"Test requires gender '{required_gender}' (patient: '{patient_gender}')"
        )


class TenantMismatchError(ValidationError):
    """Raised when tenant_id doesn't match across related resources."""

    detail = "Tenant mismatch between related resources"


# ============================================================================
# Not Found Errors (404)
# ============================================================================


class ResourceNotFoundError(KeneyAppException):
    """Base class for not found errors."""

    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class PatientNotFoundError(ResourceNotFoundError):
    """Raised when patient is not found."""

    detail = "Patient not found"


class LabResultNotFoundError(ResourceNotFoundError):
    """Raised when lab result is not found."""

    detail = "Lab result not found"


class LabTestTypeNotFoundError(ResourceNotFoundError):
    """Raised when lab test type is not found."""

    detail = "Lab test type not found"


class AppointmentNotFoundError(ResourceNotFoundError):
    """Raised when appointment is not found."""

    detail = "Appointment not found"


class UserNotFoundError(ResourceNotFoundError):
    """Raised when user is not found."""

    detail = "User not found"


# ============================================================================
# Authorization/Permission Errors (403)
# ============================================================================


class AuthenticationError(KeneyAppException):
    """Raised when authentication fails."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication failed"


class InsufficientPermissionsError(KeneyAppException):
    """Raised when user lacks permissions for operation."""

    status_code = status.HTTP_403_FORBIDDEN
    detail = "Insufficient permissions for this operation"


class CannotValidateOwnResultError(InsufficientPermissionsError):
    """Raised when user tries to validate their own lab result."""

    detail = "Cannot validate your own lab result"


class RequiresDifferentRoleError(InsufficientPermissionsError):
    """Raised when operation requires a different role."""

    def __init__(self, required_role: str):
        super().__init__(detail=f"Operation requires '{required_role}' role")


# ============================================================================
# Conflict Errors (409)
# ============================================================================


class ConflictError(KeneyAppException):
    """Base class for conflict errors."""

    status_code = status.HTTP_409_CONFLICT
    detail = "Resource conflict"


class AppointmentConflictError(ConflictError):
    """Raised when appointment time conflicts with existing appointment."""

    detail = "Appointment time conflicts with existing appointment"


class DuplicateResourceError(ConflictError):
    """Raised when attempting to create duplicate resource."""

    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            detail=f"{resource_type} with identifier '{identifier}' already exists"
        )


class LabOrderExistsError(ConflictError):
    """Raised when lab order already exists (from GNU Health pattern)."""

    detail = "Lab order already exists for this patient and test"


# ============================================================================
# Business Logic Errors (422)
# ============================================================================


class BusinessLogicError(ValidationError):
    """Base class for business rule violations."""

    detail = "Business rule violation"


class PatientInactiveError(BusinessLogicError):
    """Raised when trying to operate on inactive patient."""

    detail = "Cannot perform operation on inactive patient"


class TenantInactiveError(BusinessLogicError):
    """Raised when trying to operate on inactive tenant."""

    detail = "Tenant is inactive"


class TenantQuotaExceededError(KeneyAppException):
    """Raised when tenant exceeds quota."""

    status_code = status.HTTP_402_PAYMENT_REQUIRED
    detail = "Tenant quota exceeded"


class FeatureNotEnabledError(BusinessLogicError):
    """Raised when feature is not enabled for tenant."""

    def __init__(self, feature_name: str):
        super().__init__(
            detail=f"Feature '{feature_name}' is not enabled for this tenant"
        )


# ============================================================================
# Integration/External Errors (502, 503)
# ============================================================================


class ExternalServiceError(KeneyAppException):
    """Raised when external service call fails."""

    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "External service error"


class FHIRServerError(ExternalServiceError):
    """Raised when FHIR server interaction fails."""

    detail = "FHIR server error"


class CacheUnavailableError(KeneyAppException):
    """Raised when Redis cache is unavailable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Cache service unavailable"


class DatabaseUnavailableError(KeneyAppException):
    """Raised when database is unavailable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Database service unavailable"


# ============================================================================
# Helper Functions
# ============================================================================


def raise_if_not_found(resource, resource_type: str = "Resource"):
    """Helper to raise ResourceNotFoundError if resource is None."""
    if resource is None:
        raise ResourceNotFoundError(detail=f"{resource_type} not found")
    return resource


def raise_if_tenant_mismatch(resource_tenant_id: int, user_tenant_id: int):
    """Helper to raise TenantMismatchError if tenants don't match."""
    if resource_tenant_id != user_tenant_id:
        raise TenantMismatchError(
            detail=f"Resource belongs to tenant {resource_tenant_id}, user belongs to {user_tenant_id}"
        )
