"""Terminology service: validate and translate medical codes with caching.

Uses the local MedicalCode reference table for validation/display and
provides a simple passthrough translate when systems are identical.
Future: connect to external terminology servers and extend mappings.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.cache import cache_get, cache_set
from app.models.medical_code import CodeSystem, MedicalCode


def _cache_key_validate(system: str, code: str) -> str:
    return f"terminology:validate:{system}:{code}"


def _cache_key_translate(system_from: str, code_from: str, system_to: str) -> str:
    return f"terminology:translate:{system_from}:{code_from}:{system_to}"


def validate_code(db: Session, *, system: str, code: str) -> Dict[str, Any]:
    """Validate a code in a given code system using local reference table.

    Args:
        db: SQLAlchemy session
        system: code system (icd11|snomed_ct|loinc|atc|cpt|ccam|dicom)
        code: code value

    Returns:
        Dict with keys: is_valid(bool), system(str), code(str), display(Optional[str])
    """
    ck = _cache_key_validate(system, code)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    q = (
        db.query(MedicalCode)
        .filter(MedicalCode.code_system == system, MedicalCode.code == code, MedicalCode.is_active == 1)
        .first()
    )

    result: Dict[str, Any] = {
        "is_valid": q is not None,
        "system": system,
        "code": code,
        "display": q.display if q else None,
    }
    # cache 24h
    cache_set(ck, result, expire=24 * 3600)
    return result


def translate_code(
    db: Session, *, system_from: str, code_from: str, system_to: str
) -> Dict[str, Any]:
    """Translate a code from one system to another.

    For now, supports identity mapping when systems are equal.
    Placeholder for future terminology server mapping.
    """
    ck = _cache_key_translate(system_from, code_from, system_to)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    if system_from == system_to:
        # Validate and return as-is
        v = validate_code(db, system=system_from, code=code_from)
        result = {
            "found": v["is_valid"],
            "source": {"system": system_from, "code": code_from, "display": v.get("display")},
            "target": {"system": system_to, "code": code_from, "display": v.get("display")},
        }
        cache_set(ck, result, expire=24 * 3600)
        return result

    # No cross-system mapping available yet
    result = {
        "found": False,
        "source": {"system": system_from, "code": code_from},
        "target": {"system": system_to, "code": None},
        "message": "No mapping available",
    }
    cache_set(ck, result, expire=3600)
    return result


class TerminologyService:
    """Static helper methods for medical coding.

    Provides utility methods for working with medical code systems
    without requiring a database session.
    """

    # System URI mappings
    SYSTEM_URIS = {
        CodeSystem.ICD11: "http://id.who.int/icd/release/11/mms",
        CodeSystem.SNOMED_CT: "http://snomed.info/sct",
        CodeSystem.LOINC: "http://loinc.org",
        CodeSystem.ATC: "http://www.whocc.no/atc",
        CodeSystem.CPT: "http://www.ama-assn.org/go/cpt",
        CodeSystem.CCAM: "http://www.ccam.fr",
        CodeSystem.DICOM: "http://dicom.nema.org/resources/ontology/DCM",
    }

    @staticmethod
    def get_coding_dict(
        code_system: CodeSystem, code: Optional[str], display: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """Generate a FHIR coding dictionary for a given code system and code.

        Args:
            code_system: The medical code system enum
            code: The code value (if None, returns None)
            display: Optional display text for the code

        Returns:
            Dictionary with system/code/display keys, or None if code is None
        """
        if code is None:
            return None

        result = {
            "system": TerminologyService.SYSTEM_URIS.get(code_system, ""),
            "code": code,
        }

        if display:
            result["display"] = display

        return result

    @staticmethod
    def get_sample_codes() -> Dict[str, List[Dict[str, str]]]:
        """Return sample codes for demonstration and testing.

        Returns:
            Dictionary mapping system names to lists of sample codes
        """
        return {
            "icd11": [
                {"code": "2E65", "display": "Essential hypertension"},
                {"code": "5A11", "display": "Type 2 diabetes mellitus"},
                {"code": "CA40.00", "display": "Acute myocardial infarction"},
            ],
            "snomed_ct": [
                {"code": "38341003", "display": "Hypertensive disorder"},
                {"code": "44054006", "display": "Diabetes mellitus type 2"},
                {"code": "22298006", "display": "Myocardial infarction"},
            ],
            "loinc": [
                {"code": "8480-6", "display": "Systolic blood pressure"},
                {"code": "8462-4", "display": "Diastolic blood pressure"},
                {"code": "2339-0", "display": "Glucose"},
            ],
            "atc": [
                {"code": "A10BA02", "display": "Metformin"},
                {"code": "C09AA01", "display": "Captopril"},
                {"code": "C10AA01", "display": "Simvastatin"},
            ],
            "cpt": [
                {"code": "99213", "display": "Office visit, established patient"},
                {"code": "99214", "display": "Office visit, complex"},
                {"code": "80053", "display": "Comprehensive metabolic panel"},
            ],
            "ccam": [
                {"code": "YYYY001", "display": "Consultation de médecine générale"},
                {"code": "YYYY002", "display": "Consultation de spécialité"},
                {"code": "GLQP002", "display": "Électrocardiogramme"},
            ],
        }


# Singleton instance for convenience
terminology_service = TerminologyService()
