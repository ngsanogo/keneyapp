# FHIR Interoperability Guide

## Overview

KeneyApp implements HL7 FHIR (Fast Healthcare Interoperability Resources) version 4.0.1 for seamless integration with other healthcare systems. This enables standardized data exchange for patient records, appointments, and prescriptions.

## Supported Resources

### Patient Resource
- Full demographic information
- Contact details
- Medical identifiers
- FHIR R4 compliant

### Appointment Resource
- Scheduling information
- Participant references
- Status tracking
- FHIR R4 compliant

### MedicationRequest Resource
- Prescription details
- Dosage instructions
- Medication references
- FHIR R4 compliant

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

For FHIR integration support: fhir-support@isdataconsulting.com
