# Medical Terminologies and Standards Guide

## Overview

KeneyApp implements comprehensive international healthcare standards, nomenclatures, and terminologies to ensure interoperability, compliance, and best practices in healthcare data management.

## Supported Standards and Nomenclatures

### 1. Diagnostic Coding

#### ICD-11 (International Classification of Diseases, 11th Revision)
- **Organization**: World Health Organization (WHO)
- **Usage**: Classification and coding of diseases, symptoms, and health conditions
- **URI**: `http://id.who.int/icd/release/11/mms`
- **Implementation**: Used in `Condition` resources for diagnosis coding

**Example**:
```json
{
  "icd11_code": "2E65",
  "icd11_display": "Essential hypertension"
}
```

#### SNOMED CT (Systematized Nomenclature of Medicine - Clinical Terms)
- **Organization**: SNOMED International
- **Usage**: Comprehensive clinical terminology for diseases, clinical findings, procedures, and more
- **URI**: `http://snomed.info/sct`
- **Implementation**: Used in `Condition` and `Procedure` resources for detailed clinical coding

**Example**:
```json
{
  "snomed_code": "38341003",
  "snomed_display": "Hypertensive disorder"
}
```

### 2. Laboratory and Observations

#### LOINC (Logical Observation Identifiers Names and Codes)
- **Organization**: Regenstrief Institute
- **Usage**: Universal standard for laboratory and clinical observations
- **URI**: `http://loinc.org`
- **Implementation**: Used in `Observation` resources for lab results and vital signs

**Example**:
```json
{
  "loinc_code": "8480-6",
  "loinc_display": "Systolic blood pressure",
  "value_quantity": "120",
  "value_unit": "mmHg"
}
```

### 3. Medication Coding

#### ATC (Anatomical Therapeutic Chemical Classification)
- **Organization**: World Health Organization (WHO)
- **Usage**: Classification of medications by therapeutic, pharmacological, and chemical properties
- **URI**: `http://www.whocc.no/atc`
- **Implementation**: Used in `Prescription` resources for medication coding

**Example**:
```json
{
  "medication_name": "Metformin",
  "atc_code": "A10BA02",
  "atc_display": "Metformin"
}
```

### 4. Procedure Coding

#### CPT (Current Procedural Terminology)
- **Organization**: American Medical Association (AMA)
- **Usage**: Medical procedure coding for billing and documentation (primarily US)
- **URI**: `http://www.ama-assn.org/go/cpt`
- **Implementation**: Used in `Procedure` resources

**Example**:
```json
{
  "cpt_code": "99213",
  "cpt_display": "Office visit, established patient"
}
```

#### CCAM (Classification Commune des Actes Médicaux)
- **Organization**: Agence Nationale de Santé (ANS), France
- **Usage**: Medical procedure classification for billing and reimbursement (France)
- **URI**: `http://www.ccam.fr`
- **Implementation**: Used in `Procedure` resources

**Example**:
```json
{
  "ccam_code": "YYYY001",
  "ccam_display": "Consultation de médecine générale"
}
```

### 5. Medical Imaging

#### DICOM (Digital Imaging and Communications in Medicine)
- **Organization**: NEMA (National Electrical Manufacturers Association)
- **Usage**: Standard for medical imaging and related information
- **URI**: `http://dicom.nema.org/resources/ontology/DCM`
- **Implementation**: Reference support for future imaging integration

## Database Schema

### Medical Codes Table

```sql
CREATE TABLE medical_codes (
    id INTEGER PRIMARY KEY,
    code_system VARCHAR(50) NOT NULL,  -- icd11, snomed_ct, loinc, atc, cpt, ccam, dicom
    code VARCHAR(50) NOT NULL,
    display VARCHAR(500) NOT NULL,
    definition TEXT,
    parent_code VARCHAR(50),           -- For hierarchical code systems
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Clinical Resources

#### Conditions (Diagnoses)
```sql
CREATE TABLE conditions (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    clinical_status VARCHAR(20),       -- active, resolved, inactive
    verification_status VARCHAR(20),   -- confirmed, provisional, differential
    severity VARCHAR(20),              -- mild, moderate, severe
    icd11_code VARCHAR(50),            -- ICD-11 diagnosis code
    icd11_display VARCHAR(500),
    snomed_code VARCHAR(50),           -- SNOMED CT code
    snomed_display VARCHAR(500),
    notes TEXT,
    onset_date TIMESTAMP,
    abatement_date TIMESTAMP,
    recorded_by_id INTEGER,
    recorded_date TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### Observations (Laboratory Results, Vital Signs)
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    status VARCHAR(20),                -- registered, preliminary, final, amended
    loinc_code VARCHAR(50) NOT NULL,   -- LOINC observation code
    loinc_display VARCHAR(500) NOT NULL,
    value_quantity VARCHAR(50),        -- Numeric value
    value_unit VARCHAR(50),            -- Unit of measure
    value_string TEXT,                 -- Text value for non-numeric
    reference_range_low VARCHAR(50),
    reference_range_high VARCHAR(50),
    interpretation VARCHAR(50),        -- normal, high, low, critical
    effective_datetime TIMESTAMP NOT NULL,
    issued_datetime TIMESTAMP,
    performer_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### Procedures
```sql
CREATE TABLE procedures (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    status VARCHAR(20),                -- preparation, in-progress, completed
    cpt_code VARCHAR(50),              -- CPT procedure code (US)
    cpt_display VARCHAR(500),
    ccam_code VARCHAR(50),             -- CCAM procedure code (France)
    ccam_display VARCHAR(500),
    snomed_code VARCHAR(50),           -- SNOMED CT procedure code
    snomed_display VARCHAR(500),
    category VARCHAR(100),             -- surgical, diagnostic, therapeutic
    notes TEXT,
    outcome VARCHAR(500),
    performed_datetime TIMESTAMP NOT NULL,
    performed_by_id INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## FHIR Interoperability

### FHIR R4 Resource Mapping

#### Condition Resource
```json
{
  "resourceType": "Condition",
  "id": "123",
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    }]
  },
  "code": {
    "coding": [
      {
        "system": "http://id.who.int/icd/release/11/mms",
        "code": "2E65",
        "display": "Essential hypertension"
      },
      {
        "system": "http://snomed.info/sct",
        "code": "38341003",
        "display": "Hypertensive disorder"
      }
    ]
  },
  "subject": {"reference": "Patient/456"}
}
```

#### Observation Resource
```json
{
  "resourceType": "Observation",
  "id": "789",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "8480-6",
      "display": "Systolic blood pressure"
    }]
  },
  "subject": {"reference": "Patient/456"},
  "effectiveDateTime": "2024-01-15T10:30:00Z",
  "valueQuantity": {
    "value": 120,
    "unit": "mmHg"
  }
}
```

#### Procedure Resource
```json
{
  "resourceType": "Procedure",
  "id": "321",
  "status": "completed",
  "code": {
    "coding": [
      {
        "system": "http://www.ama-assn.org/go/cpt",
        "code": "99213",
        "display": "Office visit, established patient"
      },
      {
        "system": "http://www.ccam.fr",
        "code": "YYYY001",
        "display": "Consultation de médecine générale"
      }
    ]
  },
  "subject": {"reference": "Patient/456"},
  "performedDateTime": "2024-01-15T14:00:00Z"
}
```

#### MedicationRequest with ATC
```json
{
  "resourceType": "MedicationRequest",
  "id": "654",
  "status": "active",
  "intent": "order",
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.whocc.no/atc",
      "code": "A10BA02",
      "display": "Metformin"
    }],
    "text": "Metformin"
  },
  "subject": {"reference": "Patient/456"}
}
```

## API Usage Examples

### Creating a Condition with ICD-11 and SNOMED CT Codes

```python
import requests

response = requests.post(
    "https://api.keneyapp.com/api/v1/conditions",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "patient_id": 456,
        "clinical_status": "active",
        "verification_status": "confirmed",
        "icd11_code": "2E65",
        "icd11_display": "Essential hypertension",
        "snomed_code": "38341003",
        "snomed_display": "Hypertensive disorder",
        "onset_date": "2024-01-01T00:00:00Z"
    }
)
```

### Creating an Observation with LOINC Code

```python
response = requests.post(
    "https://api.keneyapp.com/api/v1/observations",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "patient_id": 456,
        "status": "final",
        "loinc_code": "8480-6",
        "loinc_display": "Systolic blood pressure",
        "value_quantity": "120",
        "value_unit": "mmHg",
        "reference_range_low": "90",
        "reference_range_high": "130",
        "interpretation": "normal",
        "effective_datetime": "2024-01-15T10:30:00Z"
    }
)
```

### Creating a Procedure with CPT and CCAM Codes

```python
response = requests.post(
    "https://api.keneyapp.com/api/v1/procedures",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "patient_id": 456,
        "status": "completed",
        "cpt_code": "99213",
        "cpt_display": "Office visit, established patient",
        "ccam_code": "YYYY001",
        "ccam_display": "Consultation de médecine générale",
        "category": "diagnostic",
        "performed_datetime": "2024-01-15T14:00:00Z"
    }
)
```

### Creating a Prescription with ATC Code

```python
response = requests.post(
    "https://api.keneyapp.com/api/v1/prescriptions",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "patient_id": 456,
        "medication_name": "Metformin",
        "atc_code": "A10BA02",
        "atc_display": "Metformin",
        "dosage": "500mg",
        "frequency": "twice daily",
        "duration": "30 days"
    }
)
```

## Compliance and Regulations

### RGPD (General Data Protection Regulation - Europe)
✅ **Implemented**:
- Data encryption at rest (AES-256-GCM)
- Access control and audit logging
- Patient consent management
- Right to data portability (via FHIR exports)
- Right to be forgotten

### HIPAA (Health Insurance Portability and Accountability Act - US)
✅ **Implemented**:
- Secure data transmission (TLS)
- Access controls and authentication
- Audit trails for all data access
- Data encryption
- Business Associate Agreement (BAA) ready

### HDS (Hébergeur de Données de Santé - France)
✅ **Compliant Architecture**:
- ISO 27001 security controls
- Data encryption (at rest and in transit)
- Comprehensive audit logging
- Access control and authentication
- Regular security assessments
- Incident response procedures

## Integration with AI Systems

### Structured Data for AI/ML

The standardized coding enables:

1. **Clinical Decision Support**: ICD-11 and SNOMED CT codes enable AI-powered diagnosis suggestions
2. **Predictive Analytics**: LOINC-coded lab results support trend analysis and early warning systems
3. **Drug Interaction Checking**: ATC codes enable automated medication safety checks
4. **Research and Analytics**: OMOP CDM compatibility for observational research

### OMOP CDM (Observational Medical Outcomes Partnership Common Data Model)

KeneyApp's standardized coding makes it compatible with OMOP CDM for research purposes:
- ICD-11/SNOMED CT → Condition tables
- LOINC → Measurement tables
- ATC → Drug exposure tables
- CPT/CCAM → Procedure occurrence tables

## Standards Compliance Matrix

| **Category**         | **Standard**      | **Status** | **Implementation**                    |
|----------------------|-------------------|------------|---------------------------------------|
| **Diagnostics**      | ICD-11            | ✅ Active  | Condition resources                   |
|                      | SNOMED CT         | ✅ Active  | Condition, Procedure resources        |
| **Laboratory**       | LOINC             | ✅ Active  | Observation resources                 |
| **Medications**      | ATC               | ✅ Active  | Prescription/MedicationRequest        |
| **Procedures (US)**  | CPT               | ✅ Active  | Procedure resources                   |
| **Procedures (FR)**  | CCAM              | ✅ Active  | Procedure resources                   |
| **Imaging**          | DICOM             | 📋 Planned | Future imaging module                 |
| **Interoperability** | HL7 FHIR R4       | ✅ Active  | All clinical resources                |
| **Compliance (EU)**  | RGPD              | ✅ Active  | Complete application                  |
| **Compliance (US)**  | HIPAA             | ✅ Active  | Complete application                  |
| **Compliance (FR)**  | HDS Certification | ✅ Ready   | Infrastructure and security controls  |

## Resources and References

### Official Standards Organizations

- **WHO ICD-11**: https://icd.who.int/
- **SNOMED International**: https://www.snomed.org/
- **LOINC**: https://loinc.org/
- **WHO ATC**: https://www.whocc.no/atc/
- **AMA CPT**: https://www.ama-assn.org/practice-management/cpt
- **ANS France**: https://esante.gouv.fr/
- **HL7 FHIR**: https://www.hl7.org/fhir/

### Implementation Libraries

- **Python FHIR**: `fhir.resources` (https://pypi.org/project/fhir.resources/)
- **HAPI FHIR (Java)**: https://hapifhir.io/
- **FHIR.js**: https://github.com/FHIR/fhir.js

### Validation Tools

- **FHIR Validator**: https://confluence.hl7.org/display/FHIR/Using+the+FHIR+Validator
- **Terminology Services**: https://tx.fhir.org/

## Best Practices

1. **Always Use Standardized Codes**: When available, use ICD-11, SNOMED CT, LOINC, or ATC codes
2. **Dual Coding**: Use both ICD-11 and SNOMED CT for diagnoses when possible for maximum interoperability
3. **FHIR Compliance**: All clinical data should be exportable in FHIR format
4. **Version Control**: Track which version of code systems you're using
5. **Regular Updates**: Medical terminologies are updated regularly; plan for updates
6. **Validation**: Validate codes against official terminology services
7. **Fallback**: Always include display text even when codes are present

## Future Enhancements

- [ ] Integration with official terminology servers (WHO, NLM, etc.)
- [ ] Automatic code validation against terminology services
- [ ] Support for additional resources (AllergyIntolerance, Immunization)
- [ ] DICOM integration for medical imaging
- [ ] IHE (Integrating the Healthcare Enterprise) profiles
- [ ] OpenEHR archetype support
- [ ] Real-time code lookup and suggestion APIs
- [ ] Bulk terminology import utilities

## Support

For questions about medical terminologies implementation:
- **Technical Support**: fhir-support@isdataconsulting.com
- **Documentation**: https://docs.keneyapp.com
- **Community**: https://community.keneyapp.com

---

*Last Updated: 2024-10-31*
*Version: 1.0.0*
