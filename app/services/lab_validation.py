"""
Lab test validation service for age/gender constraints and workflow states.

Implements business rules from GNU Health patterns for lab test ordering
and result validation.
"""

from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from app.models.lab import LabTestType, LabResult, LabResultState
from app.models.patient import Patient
from app.models.user import User
from app.exceptions import (
    InvalidAgeForTestError,
    InvalidGenderForTestError,
    InvalidStateTransitionError,
    LabResultAlreadyValidatedError,
    CannotValidateOwnResultError,
    raise_if_not_found,
)


class LabValidationService:
    """Service for lab test validation and workflow management."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_age_years(self, birth_date: date) -> float:
        """
        Calculate age in years from birth date.

        Args:
            birth_date: Patient's date of birth

        Returns:
            Age in years (with decimal precision)
        """
        today = date.today()
        age = today.year - birth_date.year
        # Adjust for birthday not yet occurred this year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return float(age)

    def validate_test_for_patient(
        self, test_type: LabTestType, patient: Patient
    ) -> None:
        """
        Validate that a test type is appropriate for a patient.

        Checks age and gender constraints defined on the test type.

        Args:
            test_type: Lab test type to validate
            patient: Patient to validate against

        Raises:
            InvalidAgeForTestError: If patient age doesn't meet test requirements
            InvalidGenderForTestError: If patient gender doesn't match test requirements
        """
        # Check gender constraints
        if test_type.gender:
            # Map patient gender enum to test type gender code
            gender_map = {"male": "m", "female": "f"}
            patient_gender_code = gender_map.get(patient.gender.value)
            if patient_gender_code != test_type.gender:
                raise InvalidGenderForTestError(patient.gender.value, test_type.gender)

        # Check age constraints
        patient_age = self.calculate_age_years(patient.date_of_birth)

        if test_type.min_age_years is not None:
            if patient_age < test_type.min_age_years:
                raise InvalidAgeForTestError(
                    patient_age, test_type.min_age_years, test_type.max_age_years
                )

        if test_type.max_age_years is not None:
            if patient_age > test_type.max_age_years:
                raise InvalidAgeForTestError(
                    patient_age, test_type.min_age_years, test_type.max_age_years
                )

    def validate_state_transition(
        self, current_state: LabResultState, new_state: LabResultState
    ) -> None:
        """
        Validate that a state transition is allowed.

        Args:
            current_state: Current lab result state
            new_state: Desired new state

        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        valid_transitions = {
            LabResultState.DRAFT: [
                LabResultState.PENDING_REVIEW,
                LabResultState.CANCELLED,
            ],
            LabResultState.PENDING_REVIEW: [
                LabResultState.REVIEWED,
                LabResultState.DRAFT,
            ],
            LabResultState.REVIEWED: [
                LabResultState.VALIDATED,
                LabResultState.AMENDED,
            ],
            LabResultState.VALIDATED: [LabResultState.AMENDED],
            LabResultState.AMENDED: [LabResultState.PENDING_REVIEW],
            LabResultState.CANCELLED: [],  # Terminal state
        }

        allowed = valid_transitions.get(current_state, [])
        if new_state not in allowed:
            raise InvalidStateTransitionError(current_state.value, new_state.value)

    def can_modify_result(self, result: LabResult) -> bool:
        """
        Check if a lab result can be modified.

        Args:
            result: Lab result to check

        Returns:
            True if result can be modified, False otherwise
        """
        modifiable_states = [
            LabResultState.DRAFT,
            LabResultState.PENDING_REVIEW,
            LabResultState.AMENDED,
        ]
        return result.state in modifiable_states

    def can_validate_result(self, result: LabResult, user: User) -> None:
        """
        Validate that a user can validate a lab result.

        Args:
            result: Lab result to validate
            user: User attempting validation

        Raises:
            CannotValidateOwnResultError: If user is trying to validate their own result
            LabResultAlreadyValidatedError: If result is already validated
        """
        # Cannot validate own results
        if result.requested_by_id == user.id:
            raise CannotValidateOwnResultError()

        # Cannot re-validate
        if result.state == LabResultState.VALIDATED:
            raise LabResultAlreadyValidatedError()

    def transition_result_state(
        self,
        result: LabResult,
        new_state: LabResultState,
        user: Optional[User] = None,
    ) -> LabResult:
        """
        Transition a lab result to a new state with validation.

        Updates workflow tracking fields (reviewed_by, validated_by, etc.)
        based on the new state.

        Args:
            result: Lab result to transition
            new_state: Desired new state
            user: User performing the transition (for audit)

        Returns:
            Updated lab result

        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        from datetime import datetime, timezone

        # Validate transition
        self.validate_state_transition(result.state, new_state)

        # Update state
        result.state = new_state

        # Update workflow fields based on new state
        now = datetime.now(timezone.utc)
        if new_state == LabResultState.REVIEWED and user:
            result.reviewed_by_id = user.id
            result.reviewed_at = now
        elif new_state == LabResultState.VALIDATED and user:
            result.validated_by_id = user.id
            result.validated_at = now

        self.db.flush()
        return result

    def get_test_type_by_code(self, code: str, tenant_id: int) -> LabTestType:
        """
        Retrieve a test type by code within tenant scope.

        Args:
            code: Test type code
            tenant_id: Tenant ID

        Returns:
            LabTestType instance

        Raises:
            LabTestTypeNotFoundError: If test type doesn't exist
        """
        test_type = (
            self.db.query(LabTestType)
            .filter(
                LabTestType.code == code,
                LabTestType.tenant_id == tenant_id,
                LabTestType.active.is_(True),
            )
            .first()
        )
        raise_if_not_found(test_type, "Lab test type")
        return test_type

    def validate_criterion_value(
        self, value: float, normal_min: Optional[float], normal_max: Optional[float]
    ) -> bool:
        """
        Check if a test value falls within normal range.

        Args:
            value: Test result value
            normal_min: Minimum normal value
            normal_max: Maximum normal value

        Returns:
            True if within range, False if abnormal
        """
        if value is None:
            return True

        if normal_min is not None and value < normal_min:
            return False

        if normal_max is not None and value > normal_max:
            return False

        return True
