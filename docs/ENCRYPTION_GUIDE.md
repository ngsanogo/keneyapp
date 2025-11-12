# Data Encryption Guide

## Overview

KeneyApp implements encryption at rest for sensitive patient data using AES-256-GCM, ensuring HIPAA and GDPR compliance. This guide explains how encryption works and how to use it effectively.

## Encryption Algorithm

**Algorithm**: AES-256-GCM (Advanced Encryption Standard with Galois/Counter Mode)

**Key Features**:

- **256-bit key**: Maximum security for healthcare data
- **Authenticated encryption**: Prevents tampering and ensures integrity
- **Random nonces**: Each encryption produces unique ciphertext
- **PBKDF2 key derivation**: Strong key derivation from application secret

## Architecture

### Key Derivation

```
SECRET_KEY (from config)
    ↓
PBKDF2 (100,000 iterations)
    ↓
Derived 256-bit key
    ↓
Used for AES-256-GCM encryption
```

### Encryption Process

```
Plaintext
    ↓
Generate random 12-byte nonce
    ↓
AES-256-GCM encryption
    ↓
[nonce | authentication_tag | ciphertext]
    ↓
Base64 encoding
    ↓
Encrypted string (stored in database)
```

## Usage

### Basic Encryption/Decryption

```python
from app.core.encryption import encrypt_sensitive_data, decrypt_sensitive_data

# Encrypt data
plaintext = "Patient medical history: Diabetes Type 2"
encrypted = encrypt_sensitive_data(plaintext)
# Result: "CjK9xL2e... (base64 string)"

# Decrypt data
decrypted = decrypt_sensitive_data(encrypted)
# Result: "Patient medical history: Diabetes Type 2"
```

### Patient Data Encryption

```python
from app.core.encryption import encrypt_patient_data, decrypt_patient_data

# Encrypt sensitive patient fields
patient_data = {
    "first_name": "John",
    "last_name": "Doe",
    "medical_history": "Hypertension, Diabetes",
    "allergies": "Penicillin, Sulfa drugs",
    "emergency_contact": "Jane Doe",
    "emergency_phone": "+1-555-1234",
    "address": "123 Main St, Boston, MA"
}

# Only sensitive fields are encrypted
encrypted_data = encrypt_patient_data(patient_data)

# Decrypt when needed
decrypted_data = decrypt_patient_data(encrypted_data)
```

### Sensitive Fields

The following patient fields are automatically encrypted:

- `medical_history`
- `allergies`
- `emergency_contact`
- `emergency_phone`
- `address`

Non-sensitive fields (first_name, last_name, email) remain unencrypted for searching and indexing.

## Integration with Models

### Manual Encryption in Routes

```python
from app.core.encryption import encrypt_patient_data, decrypt_patient_data
from app.models.patient import Patient

# Creating a patient with encrypted data
@router.post("/patients/")
def create_patient(patient_data: PatientCreate, db: Session = Depends(get_db)):
    # Encrypt sensitive fields
    encrypted_data = encrypt_patient_data(patient_data.dict())

    # Create patient
    patient = Patient(**encrypted_data)
    db.add(patient)
    db.commit()

    return patient

# Retrieving and decrypting patient data
@router.get("/patients/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    # Decrypt sensitive fields
    patient_dict = patient.__dict__
    decrypted_data = decrypt_patient_data(patient_dict)

    return decrypted_data
```

### Custom Encryption for New Fields

```python
from app.core.encryption import encryption

# Encrypt a custom field
diagnosis = "Stage 2 Chronic Kidney Disease"
encrypted_diagnosis = encryption.encrypt_field(diagnosis)

# Decrypt later
decrypted_diagnosis = encryption.decrypt_field(encrypted_diagnosis)
```

## Security Considerations

### Key Management

**Current**: Key derived from `SECRET_KEY` in environment variables

**Production Recommendations**:

1. Use AWS KMS, Azure Key Vault, or GCP Secret Manager
2. Rotate keys periodically (e.g., annually)
3. Store keys separately from application code
4. Use different keys for different environments

### Key Rotation

When rotating encryption keys:

```python
from app.core.encryption import DataEncryption

# Create encryptors with old and new keys
old_encryptor = DataEncryption(key=OLD_SECRET_KEY)
new_encryptor = DataEncryption(key=NEW_SECRET_KEY)

# Re-encrypt data
for patient in db.query(Patient).all():
    # Decrypt with old key
    decrypted = old_encryptor.decrypt_field(patient.medical_history)

    # Encrypt with new key
    patient.medical_history = new_encryptor.encrypt_field(decrypted)

db.commit()
```

### Best Practices

1. **Never log encrypted data**: Avoid logging sensitive fields
2. **Never log decrypted data**: Especially in production
3. **Validate inputs**: Always validate before encryption
4. **Handle None values**: Use `encrypt_field()`/`decrypt_field()` for nullable fields
5. **Audit access**: Log all access to encrypted data
6. **Use HTTPS**: Always transmit data over TLS
7. **Secure backups**: Ensure database backups are also encrypted

## Performance Considerations

### Encryption Overhead

- **Encryption time**: ~0.1-0.5ms per field
- **Decryption time**: ~0.1-0.5ms per field
- **Storage overhead**: ~33% increase (base64 encoding + nonce + tag)

### Optimization Tips

1. **Selective encryption**: Only encrypt truly sensitive fields
2. **Cache decrypted data**: Cache in memory for frequently accessed records
3. **Batch operations**: Encrypt multiple fields in one operation
4. **Async encryption**: Use background tasks for bulk encryption

### Example: Batch Encryption

```python
from app.core.encryption import encrypt_patient_data

# Encrypt multiple patients
patients_data = [patient1_dict, patient2_dict, patient3_dict]
encrypted_patients = [encrypt_patient_data(p) for p in patients_data]

# Bulk insert
db.bulk_insert_mappings(Patient, encrypted_patients)
db.commit()
```

## Database Considerations

### Storage

Encrypted fields require more storage:

- Original: VARCHAR(200)
- Encrypted: VARCHAR(300+) or TEXT

Update your database schema:

```sql
ALTER TABLE patients
  ALTER COLUMN medical_history TYPE TEXT,
  ALTER COLUMN allergies TYPE TEXT,
  ALTER COLUMN address TYPE TEXT;
```

### Searching Encrypted Data

**Problem**: Cannot search directly on encrypted fields

**Solutions**:

1. **Partial decryption**: Decrypt and search in application layer

```python
patients = db.query(Patient).all()
results = [p for p in patients if 'diabetes' in decrypt_patient_data(p.__dict__)['medical_history'].lower()]
```

2. **Searchable encryption**: Use deterministic encryption for searchable fields (advanced)

3. **Metadata fields**: Store searchable metadata separately

```python
# Add searchable flag
patient.has_diabetes = True  # Unencrypted boolean
patient.medical_history = encrypted_value  # Encrypted details
```

## Compliance

### HIPAA Requirements

✅ **Encryption at rest**: AES-256-GCM provides HIPAA-compliant encryption
✅ **Key management**: Separate key storage required
✅ **Access controls**: Encryption combined with RBAC
✅ **Audit trails**: All decryption events should be logged

### GDPR Requirements

✅ **Data protection**: Encryption provides technical safeguard
✅ **Right to erasure**: Delete encrypted data to make unrecoverable
✅ **Data minimization**: Only encrypt necessary fields
✅ **Pseudonymization**: Encryption provides pseudonymization

## Troubleshooting

### Error: "Decryption failed"

**Causes**:

1. Wrong encryption key
2. Corrupted ciphertext
3. Data not actually encrypted

**Solution**:

```python
try:
    decrypted = decrypt_sensitive_data(encrypted_data)
except ValueError as e:
    # Handle decryption error
    logger.error(f"Decryption failed: {e}")
    # Maybe data is not encrypted, try using as-is
```

### Error: "Invalid ciphertext"

**Cause**: Attempting to decrypt invalid base64 or tampered data

**Solution**: Validate data before decryption

```python
import base64

def is_encrypted(data: str) -> bool:
    try:
        base64.b64decode(data)
        return len(data) > 50  # Encrypted data is usually longer
    except:
        return False
```

## Testing

### Unit Tests

```python
def test_encryption_decryption():
    plaintext = "Test data"
    encrypted = encrypt_sensitive_data(plaintext)
    decrypted = decrypt_sensitive_data(encrypted)
    assert decrypted == plaintext

def test_patient_data_encryption():
    original = {"medical_history": "Diabetes"}
    encrypted = encrypt_patient_data(original)
    decrypted = decrypt_patient_data(encrypted)
    assert decrypted["medical_history"] == "Diabetes"
```

### Integration Tests

Test encryption with actual database operations:

```python
def test_patient_encryption_in_db(db):
    # Create patient with encrypted data
    patient_data = {"first_name": "John", "medical_history": "Diabetes"}
    encrypted = encrypt_patient_data(patient_data)

    patient = Patient(**encrypted)
    db.add(patient)
    db.commit()

    # Retrieve and verify
    retrieved = db.query(Patient).filter(Patient.id == patient.id).first()
    assert retrieved.medical_history != "Diabetes"  # Should be encrypted

    # Decrypt and verify
    decrypted = decrypt_patient_data(retrieved.__dict__)
    assert decrypted["medical_history"] == "Diabetes"
```

## Future Enhancements

Planned improvements:

1. **Field-level key rotation**: Support key rotation per field
2. **Hardware security modules**: Integration with HSMs
3. **Envelope encryption**: Multiple layers of encryption
4. **Searchable encryption**: Encrypt while maintaining searchability
5. **Homomorphic encryption**: Compute on encrypted data

## Support

For encryption-related questions: <security@isdataconsulting.com>
