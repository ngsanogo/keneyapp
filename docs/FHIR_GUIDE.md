# FHIR Interoperability Guide

## Overview

KeneyApp implements HL7 FHIR (Fast Healthcare Interoperability Resources) version 4.0.1 for seamless integration with other healthcare systems. This enables standardized data exchange for patient records, appointments, and prescriptions.

## Supported Resources

### Patient Resource

- Full demographic information
- Contact details
- Medical identifiers
- FHIR R4 compliant
- **Operations**: read, create, search-type

### Appointment Resource

- Scheduling information
- Participant references
- Status tracking
- FHIR R4 compliant
- **Operations**: read, search-type

### MedicationRequest Resource

- Prescription details
- Dosage instructions
- Medication references (ATC coding)
- FHIR R4 compliant
- **Operations**: read

### Observation Resource

- Clinical measurements and vital signs
- Laboratory results
- LOINC coding for observation types
- Reference ranges and interpretation
- FHIR R4 compliant
- **Operations**: read, search-type

### Condition Resource

- Patient diagnoses and clinical conditions
- ICD-11 and SNOMED CT coding
- Clinical and verification status
- Onset and abatement tracking
- FHIR R4 compliant
- **Operations**: read, search-type

### Procedure Resource

- Medical procedures and interventions
- CPT, CCAM, and SNOMED CT coding
- Performer and timing information
- FHIR R4 compliant
- **Operations**: read, search-type

## API Endpoints

### Get FHIR Capability Statement

Returns server metadata describing supported resources and operations.

```http
GET /api/v1/fhir/metadata
```

**Response:**

```json
{
  "resourceType": "CapabilityStatement",
  "status": "active",
  "fhirVersion": "4.0.1",
  "rest": [{
    "mode": "server",
    "resource": [
      {
        "type": "Patient",
        "interaction": [
          {"code": "read"},
          {"code": "create"}
        ]
      }
    ]
  }]
}
```

### Patient Operations

#### Search Patients

```http
GET /api/v1/fhir/Patient?name={text}&family={text}&given={text}&birthdate=YYYY-MM-DD&_count=20&_page=1
Authorization: Bearer {token}
```

Returns a FHIR Bundle (type=searchset) with matching Patient resources.

#### Get Patient (FHIR Format)

```http
GET /api/v1/fhir/Patient/{patient_id}
Authorization: Bearer {token}
```

**Response:**

```json
{
  "resourceType": "Patient",
  "id": "123",
  "identifier": [{
    "system": "https://keneyapp.com/patient-id",
    "value": "123"
  }],
  "name": [{
    "family": "Doe",
    "given": ["John"],
    "use": "official"
  }],
  "gender": "male",
  "birthDate": "1980-01-15",
  "telecom": [
    {
      "system": "phone",
      "value": "+1-555-1234",
      "use": "mobile"
    },
    {
      "system": "email",
      "value": "john.doe@example.com",
      "use": "home"
    }
  ],
  "address": [{
    "use": "home",
    "text": "123 Main St, Boston, MA",
    "type": "physical"
  }],
  "active": true
}
```

#### Create Patient (FHIR Format)

```http
POST /api/v1/fhir/Patient
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**

```json
{
  "resourceType": "Patient",
  "name": [{
    "family": "Smith",
    "given": ["Jane"]
  }],
  "gender": "female",
  "birthDate": "1990-05-20",
  "telecom": [{
    "system": "email",
    "value": "jane.smith@example.com"
  }]
}
```

### Appointment Operations

#### Search Appointments

```http
GET /api/v1/fhir/Appointment?patient={patientId}&date=YYYY-MM-DD&status={status}&_count=20&_page=1
Authorization: Bearer {token}
```

Returns a FHIR Bundle (type=searchset) with matching Appointment resources.

#### Get Appointment (FHIR Format)

```http
GET /api/v1/fhir/Appointment/{appointment_id}
Authorization: Bearer {token}
```

**Response:**

```json
{
  "resourceType": "Appointment",
  "id": "456",
  "identifier": [{
    "system": "https://keneyapp.com/appointment-id",
    "value": "456"
  }],
  "status": "booked",
  "start": "2024-02-15T10:30:00",
  "description": "Annual checkup",
  "comment": "Fasting required",
  "participant": [
    {
      "actor": {
        "reference": "Patient/123"
      },
      "status": "accepted"
    },
    {
      "actor": {
        "reference": "Practitioner/789"
      },
      "status": "accepted"
    }
  ]
}
```

### MedicationRequest Operations

#### Get MedicationRequest (FHIR Format)

```http
GET /api/v1/fhir/MedicationRequest/{prescription_id}
Authorization: Bearer {token}
```

### Observation Operations

#### Search Observations

Search for clinical observations and lab results.

```http
GET /api/v1/fhir/Observation?patient={patientId}&code={loincCode}&date=YYYY-MM-DD&status={status}&_count=20&_page=1
Authorization: Bearer {token}
```

**Parameters:**

- `patient`: Patient ID reference
- `code`: LOINC code (e.g., `8480-6` for systolic blood pressure)
- `date`: Effective date (YYYY-MM-DD)
- `status`: Observation status (`registered`, `preliminary`, `final`, `amended`)

**Response (Bundle):**

```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "total": 2,
  "link": [
    {"relation": "self", "url": "https://api.example.com/api/v1/fhir/Observation?patient=123&_page=1&_count=20"},
    {"relation": "first", "url": "https://api.example.com/api/v1/fhir/Observation?patient=123&_page=1&_count=20"}
  ],
  "entry": [
    {
      "fullUrl": "https://api.example.com/api/v1/fhir/Observation/1",
      "resource": {
        "resourceType": "Observation",
        "id": "1",
        "status": "final",
        "code": {
          "coding": [{
            "system": "http://loinc.org",
            "code": "8480-6",
            "display": "Systolic blood pressure"
          }],
          "text": "Systolic blood pressure"
        },
        "subject": {"reference": "Patient/123"},
        "effectiveDateTime": "2024-01-15T10:30:00Z",
        "valueQuantity": {
          "value": 120.0,
          "unit": "mmHg"
        },
        "referenceRange": [{
          "low": {"value": 90.0},
          "high": {"value": 130.0}
        }],
        "interpretation": [{
          "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
            "code": "NORMAL",
            "display": "normal"
          }]
        }]
      },
      "search": {"mode": "match"}
    }
  ]
}
```

#### Get Observation (FHIR Format)

```http
GET /api/v1/fhir/Observation/{observation_id}
Authorization: Bearer {token}
```

**Response:**

```json
{
  "resourceType": "Observation",
  "id": "1",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "2339-0",
      "display": "Glucose [Mass/volume] in Blood"
    }],
    "text": "Glucose [Mass/volume] in Blood"
  },
  "subject": {"reference": "Patient/123"},
  "effectiveDateTime": "2024-01-15T10:30:00Z",
  "valueQuantity": {
    "value": 95.0,
    "unit": "mg/dL"
  },
  "referenceRange": [{
    "low": {"value": 70.0},
    "high": {"value": 100.0}
  }]
}
```

### Condition Operations

#### Search Conditions

Search for patient diagnoses and conditions.

```http
GET /api/v1/fhir/Condition?patient={patientId}&code={code}&clinical-status={status}&_count=20&_page=1
Authorization: Bearer {token}
```

**Parameters:**

- `patient`: Patient ID reference
- `code`: ICD-11 or SNOMED CT code (e.g., `5A11` for Type 2 diabetes)
- `clinical-status`: Clinical status (`active`, `resolved`, etc.)

**Response (Bundle):**

```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "total": 1,
  "entry": [{
    "fullUrl": "https://api.example.com/api/v1/fhir/Condition/1",
    "resource": {
      "resourceType": "Condition",
      "id": "1",
      "clinicalStatus": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
          "code": "active"
        }]
      },
      "verificationStatus": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
          "code": "confirmed"
        }]
      },
      "code": {
        "coding": [{
          "system": "http://id.who.int/icd/release/11/mms",
          "code": "5A11",
          "display": "Type 2 diabetes mellitus"
        }]
      },
      "subject": {"reference": "Patient/123"},
      "onsetDateTime": "2022-01-01T00:00:00Z",
      "recordedDate": "2022-01-01T00:00:00Z"
    },
    "search": {"mode": "match"}
  }]
}
```

#### Get Condition (FHIR Format)

```http
GET /api/v1/fhir/Condition/{condition_id}
Authorization: Bearer {token}
```

### Procedure Operations

#### Search Procedures

Search for medical procedures and interventions.

```http
GET /api/v1/fhir/Procedure?patient={patientId}&code={code}&date=YYYY-MM-DD&_count=20&_page=1
Authorization: Bearer {token}
```

**Parameters:**

- `patient`: Patient ID reference
- `code`: CPT, CCAM, or SNOMED CT code (e.g., `99213` for office visit)
- `date`: Performed date (YYYY-MM-DD)

**Response (Bundle):**

```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "total": 1,
  "entry": [{
    "fullUrl": "https://api.example.com/api/v1/fhir/Procedure/1",
    "resource": {
      "resourceType": "Procedure",
      "id": "1",
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
      "subject": {"reference": "Patient/123"},
      "performedDateTime": "2024-01-15T14:00:00Z",
      "performer": [{
        "actor": {"reference": "Practitioner/456"}
      }]
    },
    "search": {"mode": "match"}
  }]
}
```

#### Get Procedure (FHIR Format)

```http
GET /api/v1/fhir/Procedure/{procedure_id}
Authorization: Bearer {token}
```

**Response:**

```json
{
  "resourceType": "MedicationRequest",
  "id": "789",
  "identifier": [{
    "system": "https://keneyapp.com/prescription-id",
    "value": "789"
  }],
  "status": "active",
  "intent": "order",
  "medicationCodeableConcept": {
    "text": "Metformin"
  },
  "subject": {
    "reference": "Patient/123"
  },
  "requester": {
    "reference": "Practitioner/456"
  },
  "dosageInstruction": [{
    "text": "500mg twice daily for 30 days",
    "patientInstruction": "Take with meals",
    "timing": {
      "repeat": {
        "frequency": 1,
        "period": 1,
        "periodUnit": "d"
      }
    }
  }],
  "authoredOn": "2024-01-10T14:30:00"
}
```

## Data Mapping

### KeneyApp ↔ FHIR Patient

| KeneyApp Field | FHIR Field | Notes |
|---------------|-----------|-------|
| id | identifier.value | System: keneyapp.com |
| first_name | name.given[0] | - |
| last_name | name.family | - |
| gender | gender | male/female/other/unknown |
| date_of_birth | birthDate | ISO 8601 date |
| email | telecom (system=email) | - |
| phone | telecom (system=phone) | - |
| address | address.text | - |

### KeneyApp ↔ FHIR Appointment

| KeneyApp Field | FHIR Field | Notes |
|---------------|-----------|-------|
| id | identifier.value | - |
| status | status | Mapped: scheduled→booked |
| appointment_date | start | ISO 8601 datetime |
| reason | description | - |
| notes | comment | - |
| patient_id | participant[0].actor.reference | Patient/{id} |
| doctor_id | participant[1].actor.reference | Practitioner/{id} |

### KeneyApp ↔ FHIR MedicationRequest

| KeneyApp Field | FHIR Field | Notes |
|---------------|-----------|-------|
| id | identifier.value | - |
| medication_name | medicationCodeableConcept.text | - |
| dosage | dosageInstruction[0].text | Combined with frequency |
| frequency | dosageInstruction[0].text | - |
| duration | dosageInstruction[0].text | - |
| instructions | dosageInstruction[0].patientInstruction | - |
| patient_id | subject.reference | Patient/{id} |
| doctor_id | requester.reference | Practitioner/{id} |

## Error Handling

All FHIR endpoints return HL7 FHIR **OperationOutcome** resources for error responses.

### Error Response Format

```json
{
  "resourceType": "OperationOutcome",
  "issue": [{
    "severity": "error",
    "code": "not-found",
    "diagnostics": "Patient not found"
  }]
}
```

### Common Error Codes

| HTTP Status | FHIR Code | Meaning |
|------------|-----------|---------|
| 400 | `invalid` | Invalid request format or parameters |
| 401 | `unauthorized` | Missing or invalid authentication |
| 403 | `forbidden` | Insufficient permissions |
| 404 | `not-found` | Resource not found |
| 409 | `conflict` | Resource conflict (e.g., duplicate) |
| 422 | `processing` | Validation error |
| 429 | `throttled` | Rate limit exceeded |

### ETag and Versioning

Read operations return an `ETag` header for resource versioning:

```http
GET /api/v1/fhir/Patient/123
Authorization: Bearer {token}

HTTP/1.1 200 OK
ETag: W/"Patient/123-1642512000.0"
Content-Type: application/fhir+json
```

Use the `ETag` for conditional updates (future support for `PUT` with `If-Match`).

## Pagination and Search

### HATEOAS Links

Search results include HATEOAS paging links:

```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "total": 50,
  "link": [
    {"relation": "self", "url": "...?_page=2&_count=20"},
    {"relation": "first", "url": "...?_page=1&_count=20"},
    {"relation": "previous", "url": "...?_page=1&_count=20"},
    {"relation": "next", "url": "...?_page=3&_count=20"},
    {"relation": "last", "url": "...?_page=3&_count=20"}
  ],
  "entry": [...]
}
```

### Standard Search Parameters

All search endpoints support:

- `_count`: Items per page (default: 20, max: 100)
- `_page`: Page number (1-indexed)

Resource-specific search parameters are documented in each resource's search endpoint.

## Integration Examples

### Python Client

```python
import requests

BASE_URL = "https://api.keneyapp.com/api/v1/fhir"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/fhir+json"
}

# Get patient in FHIR format
response = requests.get(
    f"{BASE_URL}/Patient/123",
    headers=headers
)

fhir_patient = response.json()
print(f"Patient: {fhir_patient['name'][0]['given'][0]} {fhir_patient['name'][0]['family']}")

# Search observations for a patient
response = requests.get(
    f"{BASE_URL}/Observation",
    params={"patient": 123, "code": "8480-6", "_count": 10},
    headers=headers
)

bundle = response.json()
print(f"Found {bundle['total']} observations")

# Create patient from FHIR resource
new_patient = {
    "resourceType": "Patient",
    "name": [{"family": "Smith", "given": ["Jane"]}],
    "gender": "female",
    "birthDate": "1990-05-20"
}

response = requests.post(
    f"{BASE_URL}/Patient",
    headers=headers,
    json=new_patient
)

created_patient = response.json()
print(f"Created patient ID: {created_patient['id']}")
```

### JavaScript/TypeScript

```typescript
const BASE_URL = 'https://api.keneyapp.com/api/v1/fhir';
const TOKEN = 'your-jwt-token';

async function getFHIRPatient(patientId: number) {
  const response = await fetch(`${BASE_URL}/Patient/${patientId}`, {
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Accept': 'application/fhir+json'
    }
  });

  const patient = await response.json();
  return patient;
}

async function createFHIRPatient(patientData: any) {
  const response = await fetch(`${BASE_URL}/Patient`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/fhir+json'
    },
    body: JSON.stringify(patientData)
  });

  return await response.json();
}
```

### FHIR Client Libraries

#### HAPI FHIR (Java)

```java
import ca.uhn.fhir.context.FhirContext;
import ca.uhn.fhir.rest.client.api.IGenericClient;
import org.hl7.fhir.r4.model.Patient;

FhirContext ctx = FhirContext.forR4();
IGenericClient client = ctx.newRestfulGenericClient("https://api.keneyapp.com/api/v1/fhir");

// Add authentication
client.registerInterceptor(new BearerTokenAuthInterceptor(token));

// Read patient
Patient patient = client.read()
    .resource(Patient.class)
    .withId("123")
    .execute();

System.out.println("Patient: " + patient.getNameFirstRep().getNameAsSingleString());
```

#### fhir.resources (Python)

```python
from fhir.resources.patient import Patient
import requests

# Get FHIR patient
response = requests.get(
    "https://api.keneyapp.com/api/v1/fhir/Patient/123",
    headers={"Authorization": f"Bearer {token}"}
)

# Parse into FHIR resource object
patient = Patient.parse_obj(response.json())

print(f"Patient name: {patient.name[0].given[0]} {patient.name[0].family}")
print(f"Gender: {patient.gender}")
print(f"Birth date: {patient.birthDate}")
```

## Validation

### FHIR Validator

Responses can be validated using official FHIR validators:

```bash
# Using FHIR Validator CLI
java -jar validator_cli.jar response.json -version 4.0.1
```

### Schema Validation

```python
from fhir.resources.patient import Patient

try:
    patient = Patient.parse_obj(fhir_data)
    print("Valid FHIR resource")
except Exception as e:
    print(f"Invalid FHIR resource: {e}")
```

## Security

### Authentication

All FHIR endpoints require JWT authentication:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Authorization

Access controlled by role-based permissions:

- **Admin**: Full access
- **Doctor**: Read/write for their patients
- **Nurse**: Read access for their patients
- **Receptionist**: Limited read access

### Audit Logging

All FHIR operations are audit logged:

- Resource accessed
- User performing operation
- Timestamp
- Operation type (read/create)

## Rate Limiting

FHIR endpoints are rate limited:

- **Read operations**: 100 requests/minute
- **Write operations**: 30 requests/minute

## Error Handling

### FHIR OperationOutcome

Errors return FHIR OperationOutcome resources:

```json
{
  "resourceType": "OperationOutcome",
  "issue": [{
    "severity": "error",
    "code": "not-found",
    "diagnostics": "Patient not found"
  }]
}
```

### Common Error Codes

| HTTP Status | FHIR Code | Description |
|------------|-----------|-------------|
| 400 | invalid | Invalid FHIR resource |
| 401 | security | Authentication required |
| 403 | forbidden | Insufficient permissions |
| 404 | not-found | Resource not found |
| 429 | throttled | Rate limit exceeded |

## Testing

### Unit Tests

```python
def test_patient_to_fhir():
    patient = Patient(
        first_name="John",
        last_name="Doe",
        gender="male",
        date_of_birth=date(1980, 1, 15)
    )

    fhir_patient = fhir_converter.patient_to_fhir(patient)

    assert fhir_patient['resourceType'] == 'Patient'
    assert fhir_patient['name'][0]['family'] == 'Doe'
    assert fhir_patient['gender'] == 'male'
```

### Integration Tests

```python
def test_fhir_patient_endpoint():
    response = client.get(
        "/api/v1/fhir/Patient/123",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    fhir_patient = response.json()
    assert fhir_patient['resourceType'] == 'Patient'
```

## Compliance

### HIPAA

✅ **Data transmission**: Encrypted with TLS
✅ **Access control**: Role-based authorization
✅ **Audit logs**: All FHIR operations logged

### FHIR Conformance

✅ **FHIR R4**: Compliant with version 4.0.1
✅ **JSON format**: Primary format supported
✅ **RESTful API**: Standard FHIR REST interactions
✅ **Resource validation**: Pydantic validation

## Limitations

### Current Limitations

1. **Read-only for some resources**: Appointment and MedicationRequest are read-only via FHIR API
2. **Simplified medication coding**: Uses text instead of coded medications
3. **No search parameters**: Search not yet implemented
4. **No versioning**: Resource versioning not supported
5. **No transaction bundles**: Bundle operations not supported

### Planned Enhancements

- Search parameters support
- Additional resources (Observation, Condition, Procedure)
- Transaction bundles
- Subscription support
- Bulk data export

## Support

For FHIR integration support: <fhir-support@isdataconsulting.com>
