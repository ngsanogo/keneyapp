"""
Tests for medical terminology services and coding.
"""

import pytest
from datetime import datetime

from app.models.medical_code import CodeSystem, MedicalCode
from app.services.terminology import TerminologyService, terminology_service


class TestTerminologyService:
    """Test terminology service functionality."""

    def test_get_coding_dict_icd11(self):
        """Test ICD-11 coding dictionary generation."""
        coding = TerminologyService.get_coding_dict(
            CodeSystem.ICD11, "2E65", "Essential hypertension"
        )

        assert coding is not None
        assert coding["system"] == "http://id.who.int/icd/release/11/mms"
        assert coding["code"] == "2E65"
        assert coding["display"] == "Essential hypertension"

    def test_get_coding_dict_snomed(self):
        """Test SNOMED CT coding dictionary generation."""
        coding = TerminologyService.get_coding_dict(
            CodeSystem.SNOMED_CT, "38341003", "Hypertensive disorder"
        )

        assert coding is not None
        assert coding["system"] == "http://snomed.info/sct"
        assert coding["code"] == "38341003"
        assert coding["display"] == "Hypertensive disorder"

    def test_get_coding_dict_loinc(self):
        """Test LOINC coding dictionary generation."""
        coding = TerminologyService.get_coding_dict(
            CodeSystem.LOINC, "8480-6", "Systolic blood pressure"
        )

        assert coding is not None
        assert coding["system"] == "http://loinc.org"
        assert coding["code"] == "8480-6"
        assert coding["display"] == "Systolic blood pressure"

    def test_get_coding_dict_atc(self):
        """Test ATC coding dictionary generation."""
        coding = TerminologyService.get_coding_dict(
            CodeSystem.ATC, "A10BA02", "Metformin"
        )

        assert coding is not None
        assert coding["system"] == "http://www.whocc.no/atc"
        assert coding["code"] == "A10BA02"
        assert coding["display"] == "Metformin"

    def test_get_coding_dict_cpt(self):
        """Test CPT coding dictionary generation."""
        coding = TerminologyService.get_coding_dict(
            CodeSystem.CPT, "99213", "Office visit, established patient"
        )

        assert coding is not None
        assert coding["system"] == "http://www.ama-assn.org/go/cpt"
        assert coding["code"] == "99213"

    def test_get_coding_dict_ccam(self):
        """Test CCAM coding dictionary generation."""
        coding = TerminologyService.get_coding_dict(
            CodeSystem.CCAM, "YYYY001", "Consultation de médecine générale"
        )

        assert coding is not None
        assert coding["system"] == "http://www.ccam.fr"
        assert coding["code"] == "YYYY001"

    def test_get_coding_dict_none_code(self):
        """Test that None code returns None."""
        coding = TerminologyService.get_coding_dict(CodeSystem.ICD11, None, "Display")

        assert coding is None

    def test_get_sample_codes(self):
        """Test sample codes retrieval."""
        samples = TerminologyService.get_sample_codes()

        assert "icd11" in samples
        assert "snomed_ct" in samples
        assert "loinc" in samples
        assert "atc" in samples
        assert "cpt" in samples
        assert "ccam" in samples

        # Verify ICD-11 samples
        assert len(samples["icd11"]) > 0
        assert any(code["code"] == "2E65" for code in samples["icd11"])

        # Verify LOINC samples
        assert len(samples["loinc"]) > 0
        assert any(code["code"] == "8480-6" for code in samples["loinc"])

        # Verify ATC samples
        assert len(samples["atc"]) > 0
        assert any(code["code"] == "A10BA02" for code in samples["atc"])


class TestMedicalCodeModel:
    """Test MedicalCode model."""

    def test_medical_code_repr(self):
        """Test MedicalCode string representation."""
        code = MedicalCode(
            code_system=CodeSystem.ICD11, code="2E65", display="Essential hypertension"
        )

        assert repr(code) == "<MedicalCode icd11:2E65>"

    def test_medical_code_fields(self):
        """Test MedicalCode field assignments."""
        code = MedicalCode(
            code_system=CodeSystem.SNOMED_CT,
            code="38341003",
            display="Hypertensive disorder",
            definition="A condition characterized by elevated blood pressure",
            parent_code="38341000",
            is_active=1,
        )

        assert code.code_system == CodeSystem.SNOMED_CT
        assert code.code == "38341003"
        assert code.display == "Hypertensive disorder"
        assert code.definition == "A condition characterized by elevated blood pressure"
        assert code.parent_code == "38341000"
        assert code.is_active == 1


class TestCodeSystemEnum:
    """Test CodeSystem enumeration."""

    def test_code_system_values(self):
        """Test all code system enum values."""
        assert CodeSystem.ICD11.value == "icd11"
        assert CodeSystem.SNOMED_CT.value == "snomed_ct"
        assert CodeSystem.LOINC.value == "loinc"
        assert CodeSystem.ATC.value == "atc"
        assert CodeSystem.CPT.value == "cpt"
        assert CodeSystem.CCAM.value == "ccam"
        assert CodeSystem.DICOM.value == "dicom"

    def test_code_system_enum_membership(self):
        """Test enum membership."""
        assert "icd11" in [cs.value for cs in CodeSystem]
        assert "snomed_ct" in [cs.value for cs in CodeSystem]
        assert "loinc" in [cs.value for cs in CodeSystem]
        assert "atc" in [cs.value for cs in CodeSystem]
