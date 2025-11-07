# tmp Folder Integration Analysis & Recommendations

**Date**: November 5, 2025  
**Purpose**: Systematic analysis of tmp/ resources to identify high-value components for KeneyApp integration

---

## Executive Summary

The tmp/ folder contains 5 major open-source healthcare and business management systems:
- **GNU Health HIS** (his/): Comprehensive hospital management with ~30 modules
- **Thalamus**: Federation server for multi-institution data sharing
- **LimeSurvey**: Survey platform for questionnaires and assessments
- **ERPNext**: Full ERP with healthcare extensions
- **Frappe Docker**: Container orchestration for Frappe apps

**Key Finding**: GNU Health provides the richest immediately applicable healthcare domain models and datasets that can directly enhance KeneyApp's clinical capabilities.

---

## 1. GNU Health HIS Analysis

### 1.1 ICD-11 Disease Codes ✅ **INTEGRATED**
**Location**: `tmp/his/tryton/health_icd11/data/diseases.xml`

**Value Proposition**:
- Complete ICD-11 taxonomy with 24,824+ disease codes
- Hierarchical structure with parent-child relationships
- Multilingual descriptions (English, Spanish, French)
- Chapter-based organization (e.g., 01-Infectious diseases, 02-Neoplasms)

**Integration Status**: ✅ **COMPLETED**
- Script created: `scripts/import_icd11_from_tmp.py`
- Imports to: `medical_codes` table
- Features: Streaming XML parser, batch commits, active filtering
- Usage: `python scripts/import_icd11_from_tmp.py --batch-size 500 --limit 1000`

**Immediate Benefits**:
- Rich disease lookup for diagnoses
- Standards-compliant coding for insurance/reporting
- Foundation for FHIR Condition resources

---

### 1.2 Laboratory Module ✅ **SCAFFOLDED**
**Location**: `tmp/his/tryton/health_lab/health_lab.py`

**Key Models Identified**:

#### TestType (Lab Test Catalog)
```python
# Fields we should enhance our LabTestType with:
- specimen_type: Char  # whole blood, plasma, urine, feces
- gender: Selection ['m', 'f', None]  # Gender-specific tests
- min_age / max_age: Float  # Age constraints (in years)
- category: Selection [  # Test classification
    'hematology', 'fluid_excreta', 'biochemical',
    'immunological', 'microbiological', 'molecular_biology',
    'chromosome_genetic', 'others'
  ]
- report_style: Selection  # How results display in reports
- tags: Char  # Colon-separated tags for report templating
- active: Boolean  # Soft delete flag
```

#### GnuHealthTestCritearea (Test Criteria/Analytes)
```python
# Enhanced fields for our LabTestCriterion:
- test_method: Char  # e.g., "Real-time PCR"
- excluded: Boolean  # Analyte excluded from this test instance
- result: Float  # Numeric result value
- result_text: Text  # Qualitative results (colors, morphology)
- to_integer: Boolean  # Round result in reports
- remarks: Text  # Context-specific notes
- warning: Boolean  # Flag abnormal results
- lower_limit / upper_limit: Float  # Reference ranges
- limits_verified: Boolean  # Ranges confirmed for patient context
- sequence: Integer  # Display order
- code: Char  # Interface script identifier (stable, language-independent)
```

**Integration Status**: ✅ **PARTIALLY IMPLEMENTED**
- Models: `app/models/lab.py` has LabTestType and LabTestCriterion
- Enhancements needed:
  - Add `category` enum field to LabTestType
  - Add `report_style` field for report generation
  - Add `test_method`, `excluded`, `result_text`, `to_integer`, `warning` to LabTestCriterion
  - Implement `limits_verified` workflow flag

**Recommended Actions**:
1. **Immediate** (v1.1):
   - Add category enum to LabTestType (use GNU Health's categories)
   - Add test_method and warning fields to LabTestCriterion
   - Update migration: `alembic revision --autogenerate -m "enhance_lab_models"`

2. **Short-term** (v1.2):
   - Implement lab result workflow states (draft → done → validated)
   - Add professional assignment (requestor, pathologist fields)
   - Build report generation with configurable styles

3. **Medium-term** (v1.3):
   - Lab interfaces for automated analyzer integration
   - Image attachment for microscopy results
   - Pathology cross-referencing

---

### 1.3 Socioeconomic Status (SES) Module 🎯 **HIGH VALUE**
**Location**: `tmp/his/tryton/health_socioeconomics/health_socioeconomics.py`

**Model**: PatientSESAssessment

**Core Fields**:
```python
# Patient demographics & SES
education: Selection [
    'None', 'Incomplete Primary School', 'Primary School',
    'Incomplete Secondary School', 'Secondary School', 'University'
]
occupation: Many2One('gnuhealth.occupation')
ses: Selection ['Lower', 'Lower-middle', 'Middle', 'Middle-upper', 'Higher']
income: Selection ['Low', 'Medium', 'High']
housing: Selection [
    'Shanty, deficient sanitary',
    'Small, crowded but good sanitary',
    'Comfortable and good sanitary',
    'Roomy and excellent sanitary',
    'Luxury and excellent sanitary'
]
homeless: Boolean

# Family APGAR Assessment (Family Functionality)
fam_apgar_help: Selection [0='None', 1='Moderately', 2='Very much']
fam_apgar_discussion: Selection  # Problem discussion
fam_apgar_decisions: Selection  # Decision making
fam_apgar_timesharing: Selection  # Time together
fam_apgar_affection: Selection  # Family affection
fam_apgar_score: Integer  # Total: 7-10=Functional, 4-6=Some dysfunction, 0-3=Severe

# Metadata
assessment_date: DateTime
health_professional: Many2One
state: Selection ['in_progress', 'done']
signed_by: Many2One  # Validates assessment
```

**Value Proposition**:
- **Social Determinants of Health (SDOH)**: Essential for comprehensive care
- **Risk Stratification**: Identify vulnerable populations
- **Family Dynamics**: APGAR score predicts health outcomes
- **Grant Compliance**: Required for many public health programs
- **Cultural Sensitivity**: Housing/SES context informs treatment plans

**Integration Plan**:

#### Phase 1: Data Model (Sprint 1)
```python
# New models to create:
app/models/socioeconomic.py
- SocioeconomicAssessment
- Occupation (lookup table)

app/schemas/socioeconomic.py
- SESAssessmentCreate
- SESAssessmentUpdate
- SESAssessmentResponse

app/routers/socioeconomic.py
- POST /api/v1/ses-assessments/
- GET /api/v1/ses-assessments/?patient_id={id}
- PUT /api/v1/ses-assessments/{id}
```

#### Phase 2: FHIR Integration (Sprint 2)
- Map SES to FHIR Observation resources
- Use LOINC codes for standardized SDOH reporting
- Expose via `/fhir/Observation?category=social-history`

#### Phase 3: Analytics (Sprint 3)
- Dashboard widget: SES distribution
- Risk scoring algorithms
- Population health segmentation

**Immediate Action**: Create models and basic CRUD endpoints

---

### 1.4 Other Notable GNU Health Modules

#### Pediatrics (`health_pediatrics`)
- Growth charts (WHO standards)
- Immunization schedules
- Developmental milestones
- **Consideration**: Integrate if targeting maternal/child health

#### Gynecology & Obstetrics (`health_gyneco`, `health_obstetrics`)
- Pregnancy tracking
- Prenatal assessments
- Delivery records
- **Consideration**: High-value for women's health clinics

#### Surgery (`health_surgery`)
- Surgical procedures
- Operating room scheduling
- Anesthesia records
- **Consideration**: Complex; defer until OR management needed

#### Nursing (`health_nursing`)
- Nursing assessments
- Care plans
- Ambulatory care
- **Consideration**: Enhance with nurse role-specific workflows

---

## 2. Thalamus Federation Server

**Location**: `tmp/thalamus/`

**Purpose**: RESTful API hub for GNU Health Federation - multi-institution data sharing

**Key Concepts**:

### 2.1 Architecture
- **Message Relay**: Concentrator for distributed health nodes
- **Authentication**: bcrypt-hashed passwords, role-based access
- **Authorization**: ACL with endpoint/method/role mappings
- **Resources**: People, Pages of Life (health records), Domiciliary Units

### 2.2 ACL Model (Access Control List)
```json
{
  "role": "health_professional",
  "permissions": {
    "GET": ["person", "page", "book"],
    "POST": ["page"],
    "PATCH": ["page"],
    "DELETE": [],
    "global": "False"  // Can only see own records
  }
}
```

### 2.3 Federation Patterns
- **Federated Identity**: `person_id` as unique identifier across institutions
- **Personal Health Record (PHR)**: "Pages of Life" model for lifelong health data
- **Consent Management**: Patient controls who accesses their records
- **Audit Trail**: All federation actions logged

**Value for KeneyApp**:

#### Short-term (Not Immediate):
- Study ACL structure for our RBAC enhancements
- Consider "super admin" vs "tenant admin" vs "health professional" hierarchy

#### Long-term (Roadmap):
- **Multi-Institution Sharing**: Allow patients to grant access to records across KeneyApp tenants
- **Referral Networks**: Seamless data exchange when referring to specialists
- **Research Consortiums**: Aggregate de-identified data across sites
- **Public Health Reporting**: Push notifiable diseases to health authorities

**Recommendation**: Document for future federation phase (v2.0+); not immediate priority

---

## 3. LimeSurvey

**Location**: `tmp/LimeSurvey/`

**Purpose**: Open-source survey platform for questionnaires and assessments

**Features**:
- 30+ question types (multiple choice, scale, matrix, text, etc.)
- Conditional logic and branching
- Multilingual support (80+ languages)
- GDPR compliance
- RemoteControl API (XML-RPC/JSON-RPC)
- 900+ templates

**Healthcare Use Cases**:
- Patient satisfaction surveys (HCAHPS)
- Health risk assessments (HRA)
- Mental health screening (PHQ-9, GAD-7)
- Quality of life measures (SF-36, EQ-5D)
- Pre-operative assessments
- Outcome tracking (PROMs - Patient-Reported Outcome Measures)

**Integration Approach**:

### Option A: Embedded (Recommended for MVP)
**Pros**: Full control, seamless UX, patient data stays in KeneyApp
**Cons**: Must build survey engine from scratch

**Implementation**:
```python
# New models
app/models/survey.py
- Survey (questionnaire definition)
- SurveyQuestion (individual questions)
- SurveyResponse (patient answers)
- SurveyTemplate (reusable questionnaires)

# Features to build
- Question types: multiple choice, scale (1-10), text, yes/no
- Conditional display logic
- Score calculation (e.g., PHQ-9 depression score)
- Result interpretation and flagging
```

**Effort**: Medium (2-3 sprints for basic engine)

### Option B: API Integration
**Pros**: Leverage LimeSurvey's mature feature set
**Cons**: External dependency, data sync complexity, additional infrastructure

**Implementation**:
- Deploy LimeSurvey instance (Docker)
- Use RemoteControl API to create/manage surveys
- Iframe survey links in KeneyApp patient portal
- Sync responses back via webhooks/API polling

**Effort**: Low (1 sprint for basic integration)

**Recommendation**: 
- **Phase 1**: Build minimal embedded survey engine for common assessments (PHQ-9, GAD-7)
- **Phase 2**: Offer LimeSurvey integration as enterprise feature for advanced users

---

## 4. ERPNext / Frappe

**Location**: `tmp/erpnext/`, `tmp/frappe_docker/`

**Purpose**: Full-featured open-source ERP system (accounting, inventory, HR, projects)

**Relevant Modules**:
- **Accounting**: Invoicing, payments, financial reports
- **Asset Management**: Medical equipment tracking
- **Projects**: Care delivery programs, research studies
- **Stock/Inventory**: Medications, supplies, consumables

**Healthcare Considerations**:
ERPNext is primarily designed for general business operations, but has healthcare extensions for:
- Patient billing
- Insurance claims
- Pharmacy inventory
- Laboratory billing

**Recommendation**: 
- **Not a direct fit** for core clinical workflows (our FastAPI/FHIR architecture is better suited)
- **Potential integration** for back-office operations:
  - Billing module → KeneyApp generates invoices → push to ERPNext for accounting
  - Inventory → Track medical supplies consumed during appointments
  - HR → Staff scheduling and payroll

**Priority**: Low for current roadmap; revisit if enterprise clients request ERP integration

---

## Priority Matrix & Implementation Roadmap

### Immediate (v1.1 - Current Sprint)
✅ **ICD-11 Import** - DONE
- Run import script in dev/staging
- Validate code counts and hierarchy
- Add to seed data process

✅ **Lab Model Enhancements** - IN PROGRESS
- Add category enum to LabTestType
- Add test_method, warning to LabTestCriterion
- Create migration and test endpoints

### Short-term (v1.2 - Next 2 Sprints)

🎯 **Priority 1: Socioeconomic Module**
- Sprint 1: Models, schemas, CRUD endpoints
- Sprint 2: Dashboard integration, FHIR mapping
- **Impact**: High (SDOH required for grants, patient stratification)

🎯 **Priority 2: Enhanced Lab Workflows**
- Lab result states (draft → validated)
- Professional assignment (requestor, pathologist)
- Report generation with configurable styles
- **Impact**: High (improves lab usability, workflow compliance)

🎯 **Priority 3: Basic Survey Engine**
- Models for surveys, questions, responses
- PHQ-9 and GAD-7 templates
- Score calculation and flagging
- **Impact**: Medium-High (mental health screening is common need)

### Medium-term (v1.3-1.4 - Next Quarter)

📋 **Nursing & Care Plan Module**
- Nursing assessments and care plans
- Task management for care team
- Patient education tracking
- **Impact**: Medium (enhances nursing workflows)

📋 **Growth Charts & Pediatrics**
- WHO growth standards
- Immunization scheduler
- Developmental milestones
- **Impact**: Medium (valuable for family clinics)

📋 **Survey Advanced Features**
- Conditional logic/branching
- Additional question types (matrix, ranking)
- Survey templates library
- **Impact**: Medium (expands assessment capabilities)

### Long-term (v2.0+ - Future Roadmap)

🔮 **Federation & Multi-Institution Sharing**
- Adapt Thalamus federation concepts
- Patient-controlled data sharing
- Referral network with data exchange
- **Impact**: Transformative (enables collaborative care networks)

🔮 **ERP Integration (Enterprise Feature)**
- Billing/accounting sync
- Inventory management for supplies
- HR/staff scheduling integration
- **Impact**: High for large enterprises

🔮 **Specialized Clinical Modules**
- Surgery/OR management
- Gynecology/Obstetrics
- Radiology (DICOM integration)
- **Impact**: Varies by target market segment

---

## Technical Integration Guidelines

### For Any New Module:

1. **Follow KeneyApp Conventions** (from `.github/copilot-instructions.md`):
   - Router in `app/routers/` with RBAC decorators
   - Pydantic schemas in `app/schemas/`
   - SQLAlchemy models in `app/models/` with tenant scoping
   - Rate limits (`@limiter.limit()`)
   - Audit logging (`log_audit_event()`)
   - Cache invalidation patterns
   - FHIR endpoint mapping where applicable

2. **Multi-tenancy**:
   - All models MUST include `tenant_id` foreign key
   - All queries MUST filter by current user's tenant
   - Unique constraints MUST include tenant_id

3. **Testing**:
   - Unit tests in `tests/test_<module>.py`
   - Maintain coverage >70%
   - Test tenant isolation

4. **Documentation**:
   - API endpoints in `docs/API_REFERENCE.md`
   - FHIR mappings in `docs/FHIR_GUIDE.md`
   - Update `docs/NEW_FEATURES.md`

5. **Database Migrations**:
   - Use Alembic: `alembic revision --autogenerate -m "add_<module>"`
   - Review generated migration before committing
   - Add seed data if needed

---

## Data Extraction Scripts

### Already Created:
✅ `scripts/import_icd11_from_tmp.py` - ICD-11 disease codes

### To Be Created:

#### Lab Reference Data
```python
# scripts/import_lab_categories.py
"""
Extract lab test categories and units from GNU Health
Populate lab_test_categories and lab_test_units tables
"""
```

#### Socioeconomic Lookups
```python
# scripts/import_occupations.py
"""
Extract occupation taxonomy from GNU Health
Populate occupations table with standard codes
"""
```

#### Survey Templates
```python
# scripts/import_survey_templates.py
"""
Create PHQ-9, GAD-7, and other validated assessment templates
Populate surveys and survey_questions tables
"""
```

---

## Conclusion & Next Steps

### Key Takeaways:
1. **GNU Health is a goldmine** of healthcare domain models and data
2. **ICD-11 integration is complete** - ready for use
3. **Lab enhancements are high ROI** - improve immediately
4. **SES module is strategic** - unlocks SDOH capabilities for grants
5. **Federation concepts inform future** - but not urgent now

### Immediate Action Items (This Week):
- [ ] Run ICD-11 import in staging environment
- [ ] Create lab model enhancement migration
- [ ] Add category enum to LabTestType
- [ ] Update lab router tests

### Next Sprint Planning:
- [ ] Socioeconomic module design review
- [ ] Create SES models and migration
- [ ] Build SES CRUD endpoints
- [ ] Design dashboard SES widgets

### Delete tmp/ When:
- ✅ ICD-11 import validated and documented
- ✅ GNU Health patterns documented in this analysis
- ✅ No pending code extraction planned

**Status**: Can delete tmp/ after completing lab enhancements and validating ICD-11 import in staging.

---

## Appendix: File Inventory

### tmp/ Structure:
```
tmp/
├── his/                      # GNU Health HIS (30+ modules)
│   └── tryton/
│       ├── health_icd11/     # ✅ ICD-11 disease codes (EXTRACTED)
│       ├── health_lab/       # ✅ Lab models (ANALYZED)
│       ├── health_socioeconomics/  # ✅ SES module (ANALYZED)
│       ├── health_pediatrics/      # 📋 Growth charts
│       ├── health_gyneco/          # 📋 Gynecology
│       ├── health_surgery/         # 📋 Surgery management
│       └── [25+ other modules]
├── thalamus/                 # ✅ Federation server (ANALYZED)
├── LimeSurvey/              # ✅ Survey platform (ANALYZED)
├── erpnext/                 # ✅ ERP system (REVIEWED)
└── frappe_docker/           # ✅ Container orchestration (NOTED)
```

### Models Created/Enhanced:
- ✅ `app/models/lab.py` - LabTestType, LabTestCriterion
- ⏳ `app/models/socioeconomic.py` - PLANNED
- ⏳ `app/models/survey.py` - PLANNED

### Scripts Created:
- ✅ `scripts/import_icd11_from_tmp.py`

### Docs Created:
- ✅ `docs/TMP_INTEGRATION_ANALYSIS.md` (this document)

---

**Document Version**: 2.0  
**Last Updated**: November 5, 2025  
**Author**: AI Analysis (via GitHub Copilot)  
**Status**: Ready for team review

---

## License Notice

- `tmp/` is a staging area only; no runtime dependency will be kept.
- GNU Health modules are GPL-3.0-or-later. We are not importing their code, only data mappings (ICD-11) and design patterns.
- LimeSurvey is GPL-2.0-or-later. We document patterns only; no code imported.
- ERPNext is GPL-3.0. We reference concepts only; no code imported.
