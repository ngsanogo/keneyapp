"""
Tests for medical code schemas.
"""

import pytest
from datetime import datetime
from app.schemas.medical_code import (
    MedicalCodeBase,
    MedicalCodeCreate,
    MedicalCodeResponse,
    CodingSchema,
    ConditionBase,
    ConditionCreate,
    ConditionResponse,
    ObservationBase,
    ObservationCreate,
    ObservationResponse,
    ProcedureBase,
    ProcedureCreate,
    ProcedureResponse,
)


class TestMedicalCodeSchemas:
    """Test medical code schemas."""

    def test_medical_code_base_creation(self):
        """Test creating a medical code base schema."""
        code = MedicalCodeBase(
            code_system="ICD-11",
            code="1A00",
            display="Cholera",
            definition="An acute diarrhoeal infection caused by ingestion of food or water contaminated with the bacterium Vibrio cholerae.",
            parent_code=None,
        )
        assert code.code_system == "ICD-11"
        assert code.code == "1A00"
        assert code.display == "Cholera"

    def test_medical_code_create_schema(self):
        """Test MedicalCodeCreate schema."""
        code = MedicalCodeCreate(
            code_system="SNOMED CT",
            code="161891005",
            display="Backache",
        )
        assert code.code_system == "SNOMED CT"
        assert code.code == "161891005"

    def test_coding_schema_with_required_fields(self):
        """Test CodingSchema with required fields only."""
        coding = CodingSchema(
            system="http://loinc.org",
            code="8480-6",
        )
        assert coding.system == "http://loinc.org"
        assert coding.code == "8480-6"
        assert coding.display is None

    def test_coding_schema_with_display(self):
        """Test CodingSchema with display field."""
        coding = CodingSchema(
            system="http://loinc.org",
            code="8480-6",
            display="Systolic blood pressure",
        )
        assert coding.display == "Systolic blood pressure"


class TestConditionSchemas:
    """Test condition schemas."""

    def test_condition_base_defaults(self):
        """Test ConditionBase with default values."""
        condition = ConditionBase()
        assert condition.clinical_status == "active"
        assert condition.verification_status == "confirmed"
        assert condition.severity is None

    def test_condition_base_with_codes(self):
        """Test ConditionBase with medical codes."""
        condition = ConditionBase(
            icd11_code="2E85",
            icd11_display="Type 2 diabetes mellitus",
            snomed_code="44054006",
            snomed_display="Diabetes mellitus type 2",
            severity="moderate",
        )
        assert condition.icd11_code == "2E85"
        assert condition.snomed_code == "44054006"
        assert condition.severity == "moderate"

    def test_condition_create_requires_patient_id(self):
        """Test ConditionCreate requires patient_id."""
        condition = ConditionCreate(
            patient_id=123,
            icd11_code="2E85",
            icd11_display="Type 2 diabetes mellitus",
        )
        assert condition.patient_id == 123


class TestObservationSchemas:
    """Test observation schemas."""

    def test_observation_base_with_required_fields(self):
        """Test ObservationBase with required fields."""
        now = datetime.utcnow()
        observation = ObservationBase(
            loinc_code="8480-6",
            loinc_display="Systolic blood pressure",
            effective_datetime=now,
        )
        assert observation.status == "final"
        assert observation.loinc_code == "8480-6"
        assert observation.effective_datetime == now

    def test_observation_with_quantity_value(self):
        """Test observation with quantity value."""
        now = datetime.utcnow()
        observation = ObservationBase(
            loinc_code="8480-6",
            loinc_display="Systolic blood pressure",
            value_quantity="120",
            value_unit="mm[Hg]",
            reference_range_low="90",
            reference_range_high="140",
            effective_datetime=now,
        )
        assert observation.value_quantity == "120"
        assert observation.value_unit == "mm[Hg]"
        assert observation.reference_range_high == "140"

    def test_observation_create_requires_patient_id(self):
        """Test ObservationCreate requires patient_id."""
        now = datetime.utcnow()
        observation = ObservationCreate(
            patient_id=456,
            loinc_code="8480-6",
            loinc_display="Systolic blood pressure",
            value_quantity="120",
            value_unit="mm[Hg]",
            effective_datetime=now,
        )
        assert observation.patient_id == 456


class TestProcedureSchemas:
    """Test procedure schemas."""

    def test_procedure_base_defaults(self):
        """Test ProcedureBase with default status."""
        now = datetime.utcnow()
        procedure = ProcedureBase(performed_datetime=now)
        assert procedure.status == "completed"

    def test_procedure_with_cpt_code(self):
        """Test procedure with CPT code."""
        now = datetime.utcnow()
        procedure = ProcedureBase(
            cpt_code="99213",
            cpt_display="Office visit, established patient",
            performed_datetime=now,
        )
        assert procedure.cpt_code == "99213"
        assert procedure.cpt_display == "Office visit, established patient"

    def test_procedure_with_ccam_code(self):
        """Test procedure with CCAM code (French)."""
        now = datetime.utcnow()
        procedure = ProcedureBase(
            ccam_code="YYYY123",
            ccam_display="Consultation",
            performed_datetime=now,
        )
        assert procedure.ccam_code == "YYYY123"
        assert procedure.ccam_display == "Consultation"

    def test_procedure_with_snomed_code(self):
        """Test procedure with SNOMED CT code."""
        now = datetime.utcnow()
        procedure = ProcedureBase(
            snomed_code="80146002",
            snomed_display="Appendectomy",
            category="surgical",
            notes="Laparoscopic approach",
            outcome="successful",
            performed_datetime=now,
        )
        assert procedure.snomed_code == "80146002"
        assert procedure.category == "surgical"
        assert procedure.outcome == "successful"

    def test_procedure_create_requires_patient_id(self):
        """Test ProcedureCreate requires patient_id."""
        now = datetime.utcnow()
        procedure = ProcedureCreate(
            patient_id=789,
            cpt_code="99213",
            cpt_display="Office visit",
            performed_datetime=now,
        )
        assert procedure.patient_id == 789


class TestSchemaValidation:
    """Test schema validation."""

    def test_coding_schema_requires_system_and_code(self):
        """Test that system and code are required."""
        with pytest.raises(Exception):
            CodingSchema()

    def test_observation_requires_loinc_code(self):
        """Test that LOINC code is required for observations."""
        now = datetime.utcnow()
        with pytest.raises(Exception):
            ObservationBase(effective_datetime=now)

    def test_procedure_requires_performed_datetime(self):
        """Test that performed datetime is required."""
        with pytest.raises(Exception):
            ProcedureBase()
