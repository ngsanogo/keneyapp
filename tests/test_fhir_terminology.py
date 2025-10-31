"""
Tests for FHIR converters with medical terminology coding.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from app.fhir.converters import FHIRConverter
from app.models.prescription import Prescription


class TestFHIRPrescriptionWithATC:
    """Test FHIR MedicationRequest conversion with ATC codes."""

    def test_prescription_to_fhir_with_atc_code(self):
        """Test prescription conversion to FHIR with ATC code."""
        prescription = Mock(spec=Prescription)
        prescription.id = 1
        prescription.patient_id = 123
        prescription.doctor_id = 456
        prescription.medication_name = "Metformin"
        prescription.atc_code = "A10BA02"
        prescription.atc_display = "Metformin"
        prescription.dosage = "500mg"
        prescription.frequency = "twice daily"
        prescription.duration = "30 days"
        prescription.instructions = "Take with meals"
        prescription.prescribed_date = datetime(
            2024, 1, 15, 14, 30, tzinfo=timezone.utc
        )

        fhir_result = FHIRConverter.prescription_to_fhir(prescription)

        assert fhir_result["resourceType"] == "MedicationRequest"
        assert fhir_result["id"] == "1"
        assert fhir_result["status"] == "active"

        # Check ATC coding
        assert "medicationCodeableConcept" in fhir_result
        assert "coding" in fhir_result["medicationCodeableConcept"]

        atc_coding = fhir_result["medicationCodeableConcept"]["coding"][0]
        assert atc_coding["system"] == "http://www.whocc.no/atc"
        assert atc_coding["code"] == "A10BA02"
        assert atc_coding["display"] == "Metformin"

    def test_prescription_to_fhir_without_atc_code(self):
        """Test prescription conversion to FHIR without ATC code."""
        prescription = Mock(spec=Prescription)
        prescription.id = 2
        prescription.patient_id = 123
        prescription.doctor_id = 456
        prescription.medication_name = "Aspirin"
        prescription.atc_code = None
        prescription.dosage = "100mg"
        prescription.frequency = "once daily"
        prescription.duration = "90 days"
        prescription.instructions = None
        prescription.prescribed_date = datetime(
            2024, 1, 15, 14, 30, tzinfo=timezone.utc
        )

        fhir_result = FHIRConverter.prescription_to_fhir(prescription)

        assert fhir_result["resourceType"] == "MedicationRequest"

        # Check medication concept (should only have text, no coding)
        assert "medicationCodeableConcept" in fhir_result
        assert fhir_result["medicationCodeableConcept"]["text"] == "Aspirin"
        assert "coding" not in fhir_result["medicationCodeableConcept"]


class TestFHIRConditionConverter:
    """Test FHIR Condition resource conversion."""

    def test_condition_to_fhir_with_icd11_and_snomed(self):
        """Test condition conversion with both ICD-11 and SNOMED CT codes."""
        condition = Mock()
        condition.id = 1
        condition.patient_id = 123
        condition.clinical_status = "active"
        condition.verification_status = "confirmed"
        condition.severity = "moderate"
        condition.icd11_code = "2E65"
        condition.icd11_display = "Essential hypertension"
        condition.snomed_code = "38341003"
        condition.snomed_display = "Hypertensive disorder"
        condition.notes = "Patient diagnosed with high blood pressure"
        condition.onset_date = datetime(2023, 6, 15, tzinfo=timezone.utc)
        condition.abatement_date = None
        condition.recorded_date = datetime(2023, 6, 15, tzinfo=timezone.utc)

        fhir_result = FHIRConverter.condition_to_fhir(condition)

        assert fhir_result["resourceType"] == "Condition"
        assert fhir_result["id"] == "1"

        # Check clinical status
        assert "clinicalStatus" in fhir_result
        assert fhir_result["clinicalStatus"]["coding"][0]["code"] == "active"

        # Check verification status
        assert "verificationStatus" in fhir_result
        assert fhir_result["verificationStatus"]["coding"][0]["code"] == "confirmed"

        # Check coding with both ICD-11 and SNOMED CT
        assert "code" in fhir_result
        assert "coding" in fhir_result["code"]
        codings = fhir_result["code"]["coding"]
        assert len(codings) == 2

        # Check ICD-11 coding
        icd11_coding = next(c for c in codings if "icd" in c["system"])
        assert icd11_coding["system"] == "http://id.who.int/icd/release/11/mms"
        assert icd11_coding["code"] == "2E65"
        assert icd11_coding["display"] == "Essential hypertension"

        # Check SNOMED CT coding
        snomed_coding = next(c for c in codings if "snomed" in c["system"])
        assert snomed_coding["system"] == "http://snomed.info/sct"
        assert snomed_coding["code"] == "38341003"
        assert snomed_coding["display"] == "Hypertensive disorder"

    def test_condition_to_fhir_with_icd11_only(self):
        """Test condition conversion with only ICD-11 code."""
        condition = Mock()
        condition.id = 2
        condition.patient_id = 123
        condition.clinical_status = "active"
        condition.verification_status = "confirmed"
        condition.severity = None
        condition.icd11_code = "5A11"
        condition.icd11_display = "Type 2 diabetes mellitus"
        condition.snomed_code = None
        condition.snomed_display = None
        condition.notes = None
        condition.onset_date = datetime(2022, 1, 1, tzinfo=timezone.utc)
        condition.abatement_date = None
        condition.recorded_date = datetime(2022, 1, 1, tzinfo=timezone.utc)

        fhir_result = FHIRConverter.condition_to_fhir(condition)

        assert fhir_result["resourceType"] == "Condition"

        # Check coding (should have only ICD-11)
        codings = fhir_result["code"]["coding"]
        assert len(codings) == 1
        assert codings[0]["system"] == "http://id.who.int/icd/release/11/mms"
        assert codings[0]["code"] == "5A11"


class TestFHIRObservationConverter:
    """Test FHIR Observation resource conversion."""

    def test_observation_to_fhir_with_loinc(self):
        """Test observation conversion with LOINC code."""
        observation = Mock()
        observation.id = 1
        observation.patient_id = 123
        observation.status = "final"
        observation.loinc_code = "8480-6"
        observation.loinc_display = "Systolic blood pressure"
        observation.value_quantity = "120"
        observation.value_unit = "mmHg"
        observation.value_string = None
        observation.reference_range_low = "90"
        observation.reference_range_high = "130"
        observation.interpretation = "normal"
        observation.effective_datetime = datetime(
            2024, 1, 15, 10, 30, tzinfo=timezone.utc
        )
        observation.issued_datetime = datetime(2024, 1, 15, 10, 35, tzinfo=timezone.utc)
        observation.notes = "Measured while seated"

        fhir_result = FHIRConverter.observation_to_fhir(observation)

        assert fhir_result["resourceType"] == "Observation"
        assert fhir_result["id"] == "1"
        assert fhir_result["status"] == "final"

        # Check LOINC coding
        assert "code" in fhir_result
        assert "coding" in fhir_result["code"]
        loinc_coding = fhir_result["code"]["coding"][0]
        assert loinc_coding["system"] == "http://loinc.org"
        assert loinc_coding["code"] == "8480-6"
        assert loinc_coding["display"] == "Systolic blood pressure"

        # Check value
        assert "valueQuantity" in fhir_result
        assert fhir_result["valueQuantity"]["value"] == 120.0
        assert fhir_result["valueQuantity"]["unit"] == "mmHg"

        # Check reference range
        assert "referenceRange" in fhir_result
        ref_range = fhir_result["referenceRange"][0]
        assert ref_range["low"]["value"] == 90.0
        assert ref_range["high"]["value"] == 130.0

        # Check interpretation
        assert "interpretation" in fhir_result
        assert fhir_result["interpretation"][0]["coding"][0]["code"] == "NORMAL"


class TestFHIRProcedureConverter:
    """Test FHIR Procedure resource conversion."""

    def test_procedure_to_fhir_with_cpt_and_ccam(self):
        """Test procedure conversion with CPT and CCAM codes."""
        procedure = Mock()
        procedure.id = 1
        procedure.patient_id = 123
        procedure.status = "completed"
        procedure.cpt_code = "99213"
        procedure.cpt_display = "Office visit, established patient"
        procedure.ccam_code = "YYYY001"
        procedure.ccam_display = "Consultation de médecine générale"
        procedure.snomed_code = None
        procedure.snomed_display = None
        procedure.category = "diagnostic"
        procedure.notes = "Annual checkup"
        procedure.outcome = "Patient in good health"
        procedure.performed_datetime = datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc)
        procedure.performed_by_id = 456

        fhir_result = FHIRConverter.procedure_to_fhir(procedure)

        assert fhir_result["resourceType"] == "Procedure"
        assert fhir_result["id"] == "1"
        assert fhir_result["status"] == "completed"

        # Check coding with both CPT and CCAM
        assert "code" in fhir_result
        assert "coding" in fhir_result["code"]
        codings = fhir_result["code"]["coding"]
        assert len(codings) == 2

        # Check CPT coding
        cpt_coding = next(c for c in codings if "cpt" in c["system"])
        assert cpt_coding["system"] == "http://www.ama-assn.org/go/cpt"
        assert cpt_coding["code"] == "99213"
        assert cpt_coding["display"] == "Office visit, established patient"

        # Check CCAM coding
        ccam_coding = next(c for c in codings if "ccam" in c["system"])
        assert ccam_coding["system"] == "http://www.ccam.fr"
        assert ccam_coding["code"] == "YYYY001"
        assert ccam_coding["display"] == "Consultation de médecine générale"
