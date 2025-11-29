"""
Laboratory models (test catalogs and results).
"""

from enum import Enum

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base


class LabResultState(str, Enum):
    """Lab result workflow states."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    VALIDATED = "validated"
    AMENDED = "amended"
    CANCELLED = "cancelled"


class LabTestCategory(str, Enum):
    """Standard lab test categories from GNU Health."""

    HEMATOLOGY = "hematology"
    FLUID_EXCRETA = "fluid_excreta"
    BIOCHEMICAL = "biochemical"
    IMMUNOLOGICAL = "immunological"
    MICROBIOLOGICAL = "microbiological"
    MOLECULAR_BIOLOGY = "molecular_biology"
    CHROMOSOME_GENETIC = "chromosome_genetic"
    OTHERS = "others"


class LabReportStyle(str, Enum):
    """Report rendering styles for test types."""

    TABLE_WITH_UNITS = "tbl_h_r_u_nr"  # Table with result, unit and normal_range
    TABLE_WITH_RANGE = "tbl_h_r_nr"  # Table with result and normal_range
    TABLE_RESULT_ONLY = "tbl_h_r"  # Table with result column
    TABLE_NO_HEADER = "tbl_nh_r"  # Table with result (no header)
    TABLE_NO_HEADER_IMG = "tbl_nh_r_img"  # Table with inline images (no header)
    NO_TABLE = "no_tbl"  # Do not use table
    DO_NOT_SHOW = "do_not_show"  # Do not show in report


class LabResult(Base):
    """Lab test result scoped by tenant and patient with workflow states."""

    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Link to test type catalog
    test_type_id = Column(
        Integer, ForeignKey("lab_test_types.id"), nullable=True, index=True
    )

    # Legacy field for backward compatibility
    test_name = Column(String(255), nullable=False, index=True)
    result_value = Column(String(255), nullable=False)
    units = Column(String(50), nullable=True)
    reference_range = Column(String(255), nullable=True)

    # New: Workflow state with audit trail
    state = Column(
        SQLEnum(LabResultState),
        default=LabResultState.DRAFT,
        nullable=False,
        index=True,
    )

    # Legacy status field (map to state)
    status = Column(String(50), nullable=False, default="final")
    notes = Column(Text, nullable=True)

    collected_at = Column(DateTime(timezone=True), nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)

    # Workflow audit fields
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    validated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    patient = relationship("Patient", backref="lab_results")
    test_type = relationship("LabTestType", backref="results")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    validated_by = relationship("User", foreign_keys=[validated_by_id])

    @validates("state")
    def validate_state_transition(self, key, new_state):
        """Enforce valid state transitions."""
        if not self.state:
            # Initial state assignment
            return new_state

        valid_transitions = {
            LabResultState.DRAFT: [
                LabResultState.PENDING_REVIEW,
                LabResultState.CANCELLED,
            ],
            LabResultState.PENDING_REVIEW: [
                LabResultState.REVIEWED,
                LabResultState.DRAFT,
            ],
            LabResultState.REVIEWED: [LabResultState.VALIDATED, LabResultState.AMENDED],
            LabResultState.VALIDATED: [LabResultState.AMENDED],
            LabResultState.AMENDED: [LabResultState.PENDING_REVIEW],
            LabResultState.CANCELLED: [],  # Terminal state
        }

        if new_state not in valid_transitions.get(self.state, []):
            raise ValueError(
                f"Invalid state transition from {self.state.value} to {new_state.value}"
            )

        return new_state

    @property
    def can_be_modified(self) -> bool:
        """Check if result can be modified."""
        return self.state in [
            LabResultState.DRAFT,
            LabResultState.PENDING_REVIEW,
            LabResultState.AMENDED,
        ]

    @property
    def is_final(self) -> bool:
        """Check if result is finalized."""
        return self.state == LabResultState.VALIDATED


class LabTestType(Base):
    """Catalog of laboratory test types with optional age/gender constraints."""

    __tablename__ = "lab_test_types"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_lab_test_type_tenant_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    code = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    specimen_type = Column(String(128), nullable=True)

    # Optional constraints
    gender = Column(String(1), nullable=True)  # 'm' | 'f' | None
    min_age_years = Column(Float, nullable=True)
    max_age_years = Column(Float, nullable=True)

    # Enhanced: Presentation and grouping with enums
    category = Column(SQLEnum(LabTestCategory), nullable=True, index=True)
    report_style = Column(
        SQLEnum(LabReportStyle), default=LabReportStyle.TABLE_WITH_RANGE, nullable=True
    )
    tags = Column(String(255), nullable=True)

    # Additional metadata
    description = Column(Text, nullable=True)

    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def has_tag(self, tag: str) -> bool:
        """Check if test type has a specific tag."""
        if not self.tags:
            return False
        return tag in self.tags.split(":")

    def all_tags(self) -> list:
        """Get all tags as a list."""
        if not self.tags:
            return []
        return sorted(self.tags.split(":"))

    @property
    def age_range_display(self) -> str:
        """Display age range in human-readable format."""
        if self.min_age_years is not None and self.max_age_years is not None:
            return f"{self.min_age_years}-{self.max_age_years} years"
        elif self.min_age_years is not None:
            return f"≥{self.min_age_years} years"
        elif self.max_age_years is not None:
            return f"≤{self.max_age_years} years"
        return "All ages"


class LabTestCriterion(Base):
    """Per-parameter criteria and reference ranges for a test type."""

    __tablename__ = "lab_test_criteria"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    test_type_id = Column(
        Integer, ForeignKey("lab_test_types.id"), nullable=False, index=True
    )

    # Stable identifier for interfacing/scripting (language-independent)
    code = Column(String(64), nullable=True, index=True)
    parameter = Column(String(128), nullable=False)

    # Test methodology
    test_method = Column(String(128), nullable=True)

    unit = Column(String(32), nullable=True)
    normal_min = Column(Float, nullable=True)
    normal_max = Column(Float, nullable=True)
    normal_range = Column(String(128), nullable=True)  # Text representation

    # Flags for result handling
    warning = Column(Boolean, default=False)  # Flag abnormal results
    limits_verified = Column(Boolean, default=False)  # Ranges confirmed for patient
    excluded = Column(Boolean, default=False)  # Analyte excluded from test instance
    to_integer = Column(Boolean, default=False)  # Round result in reports

    # Display order
    sequence = Column(Integer, default=0)

    gender = Column(String(1), nullable=True)  # optional override
    min_age_years = Column(Float, nullable=True)
    max_age_years = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    test_type = relationship("LabTestType", backref="criteria")

    def check_value_in_range(self, value: float) -> bool:
        """Check if a numeric value is within normal range."""
        if value is None:
            return True
        if self.normal_min is not None and value < self.normal_min:
            return False
        if self.normal_max is not None and value > self.normal_max:
            return False
        return True

    @property
    def normal_range_display(self) -> str:
        """Display normal range in human-readable format."""
        if self.normal_range:
            return self.normal_range
        if self.normal_min is not None and self.normal_max is not None:
            return f"{self.normal_min}-{self.normal_max}"
        elif self.normal_min is not None:
            return f"≥{self.normal_min}"
        elif self.normal_max is not None:
            return f"≤{self.normal_max}"
        return "N/A"
