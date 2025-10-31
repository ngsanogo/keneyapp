"""
Medical Terminology Service.

Provides utilities for working with medical codes and terminologies:
- ICD-11: International Classification of Diseases
- SNOMED CT: Systematized Nomenclature of Medicine
- LOINC: Logical Observation Identifiers Names and Codes
- ATC: Anatomical Therapeutic Chemical Classification
- CPT: Current Procedural Terminology
- CCAM: Classification Commune des Actes Médicaux
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.medical_code import MedicalCode, CodeSystem


class TerminologyService:
    """Service for managing and validating medical terminologies."""

    @staticmethod
    def get_code(
        db: Session, code_system: CodeSystem, code: str
    ) -> Optional[MedicalCode]:
        """
        Retrieve a medical code from the terminology database.

        Args:
            db: Database session
            code_system: The code system (ICD-11, SNOMED CT, etc.)
            code: The code value

        Returns:
            MedicalCode instance or None if not found
        """
        return (
            db.query(MedicalCode)
            .filter(
                MedicalCode.code_system == code_system,
                MedicalCode.code == code,
                MedicalCode.is_active == 1,
            )
            .first()
        )

    @staticmethod
    def search_codes(
        db: Session, code_system: CodeSystem, search_term: str, limit: int = 20
    ) -> List[MedicalCode]:
        """
        Search for medical codes by display text.

        Args:
            db: Database session
            code_system: The code system to search
            search_term: Text to search for
            limit: Maximum number of results

        Returns:
            List of matching MedicalCode instances
        """
        return (
            db.query(MedicalCode)
            .filter(
                MedicalCode.code_system == code_system,
                MedicalCode.display.ilike(f"%{search_term}%"),
                MedicalCode.is_active == 1,
            )
            .limit(limit)
            .all()
        )

    @staticmethod
    def validate_code(db: Session, code_system: CodeSystem, code: str) -> bool:
        """
        Validate that a medical code exists in the system.

        Args:
            db: Database session
            code_system: The code system
            code: The code to validate

        Returns:
            True if the code is valid, False otherwise
        """
        return TerminologyService.get_code(db, code_system, code) is not None

    @staticmethod
    def create_code(
        db: Session,
        code_system: CodeSystem,
        code: str,
        display: str,
        definition: Optional[str] = None,
        parent_code: Optional[str] = None,
    ) -> MedicalCode:
        """
        Create a new medical code entry.

        Args:
            db: Database session
            code_system: The code system
            code: The code value
            display: Human-readable display name
            definition: Optional detailed definition
            parent_code: Optional parent code for hierarchical systems

        Returns:
            Created MedicalCode instance
        """
        medical_code = MedicalCode(
            code_system=code_system,
            code=code,
            display=display,
            definition=definition,
            parent_code=parent_code,
            is_active=1,
        )
        db.add(medical_code)
        db.commit()
        db.refresh(medical_code)
        return medical_code

    @staticmethod
    def get_coding_dict(
        code_system: CodeSystem, code: Optional[str], display: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a FHIR-compatible coding dictionary.

        Args:
            code_system: The code system
            code: The code value
            display: The display text

        Returns:
            Dictionary with system, code, and display, or None if code is None
        """
        if not code:
            return None

        # Map our code systems to official FHIR URIs
        system_uris = {
            CodeSystem.ICD11: "http://id.who.int/icd/release/11/mms",
            CodeSystem.SNOMED_CT: "http://snomed.info/sct",
            CodeSystem.LOINC: "http://loinc.org",
            CodeSystem.ATC: "http://www.whocc.no/atc",
            CodeSystem.CPT: "http://www.ama-assn.org/go/cpt",
            CodeSystem.CCAM: "http://www.ccam.fr",
            CodeSystem.DICOM: "http://dicom.nema.org/resources/ontology/DCM",
        }

        if code_system not in system_uris:
            raise ValueError(
                f"Unsupported code system: {code_system}. "
                f"Supported systems: {', '.join(cs.value for cs in CodeSystem)}"
            )

        return {
            "system": system_uris[code_system],
            "code": code,
            "display": display or code,
        }

    @staticmethod
    def get_sample_codes() -> Dict[str, List[Dict[str, str]]]:
        """
        Get sample medical codes for testing and demonstration.

        Returns:
            Dictionary of code system to list of sample codes
        """
        return {
            "icd11": [
                {"code": "2E65", "display": "Essential hypertension"},
                {"code": "5A11", "display": "Type 2 diabetes mellitus"},
                {"code": "CA40.0", "display": "Acute myocardial infarction"},
                {"code": "DB91.0", "display": "Acute upper respiratory infection"},
            ],
            "snomed_ct": [
                {"code": "38341003", "display": "Hypertensive disorder"},
                {"code": "44054006", "display": "Diabetes mellitus type 2"},
                {"code": "22298006", "display": "Myocardial infarction"},
                {"code": "54150009", "display": "Upper respiratory infection"},
            ],
            "loinc": [
                {"code": "8480-6", "display": "Systolic blood pressure"},
                {"code": "8462-4", "display": "Diastolic blood pressure"},
                {"code": "2339-0", "display": "Glucose [Mass/volume] in Blood"},
                {"code": "2085-9", "display": "HDL Cholesterol"},
                {"code": "2093-3", "display": "Total Cholesterol"},
            ],
            "atc": [
                {"code": "C09AA01", "display": "Captopril"},
                {"code": "A10BA02", "display": "Metformin"},
                {"code": "C10AA01", "display": "Simvastatin"},
                {"code": "J01CA04", "display": "Amoxicillin"},
            ],
            "cpt": [
                {"code": "99213", "display": "Office visit, established patient"},
                {
                    "code": "99214",
                    "display": "Office visit, established patient, moderate complexity",
                },
                {
                    "code": "93000",
                    "display": "Electrocardiogram, routine ECG with at least 12 leads",
                },
                {"code": "80053", "display": "Comprehensive metabolic panel"},
            ],
            "ccam": [
                {"code": "YYYY001", "display": "Consultation de médecine générale"},
                {"code": "DEQP003", "display": "Électrocardiogramme"},
                {"code": "YYYY600", "display": "Consultation de cardiologie"},
            ],
        }


# Global instance
terminology_service = TerminologyService()


__all__ = [
    "TerminologyService",
    "terminology_service",
]
