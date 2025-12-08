# KeneyApp Codebase Analysis Report
**Generated**: December 8, 2025

## Critical Issues Identified

This comprehensive analysis identifies performance, security, and error handling issues across the KeneyApp codebase with severity ratings and actionable fixes.

---

## 1. CRITICAL ISSUES (High Priority)

### 1.1 N+1 Query Problem: Appointment Scheduler Service

**File**: `app/services/appointment_scheduler.py`  
**Severity**: HIGH  
**Impact**: Performance bottleneck in appointment availability checks

**Issue**:
- Lines 94, 145: Loading all appointments into memory and checking overlaps in Python loop
- Each check_doctor_availability() and check_patient_availability() call fetches entire result set
- When checking overlaps with 100+ appointments, causes full table scan + in-memory iteration
- Creates N+1 pattern: 1 query for appointments + N iterations = O(N) memory usage

**Problem Code**:
```python
appointments = query.all()  # Line 94, 145
for appt in appointments:
    appt_end = appt.appointment_date + timedelta(minutes=appt.duration_minutes)
    if start_time < appt_end and end_time > appt.appointment_date:
        return False
```

**Recommendation**:
Use SQL-based overlap detection instead of Python loop. Replace with database-native date/time overlap logic using PostgreSQL OVERLAPS or timestamp range queries.

**Fix Priority**: IMMEDIATE

---

### 1.2 N+1 Query: Messaging Service - Message Serialization

**File**: `app/routers/messages.py` (Lines 97-101)  
**Severity**: HIGH  
**Impact**: O(N) database queries for message retrieval

**Issue**:
```python
return [
    messaging_service.serialize_message(msg, str(current_user.tenant_id))
    for msg in messages  # Iteration over eager-loaded messages
]
```

While `messaging_service.get_user_messages()` uses `joinedload()` correctly, if `serialize_message()` accesses uneager-loaded relationships, it will trigger N queries per message.

**Verification Needed**: Check if `serialize_message()` accesses any lazy relationships.

**Fix Priority**: MEDIUM

---

### 1.3 Recommendation Service: Inefficient Prescription Refill Checks

**File**: `app/services/recommendation_service.py` (Lines 78-104)  
**Severity**: MEDIUM-HIGH  
**Impact**: Performance degradation with large prescription lists

**Issue**:
```python
prescriptions = (
    self.db.query(Prescription)
    .filter(
        Prescription.patient_id == patient_id,
        Prescription.tenant_id == tenant_id,
    )
    .all()  # Loads ALL prescriptions into memory
)

for prescription in prescriptions:  # Iterates in Python
    if prescription.prescribed_date and prescription.duration:
        days = self._parse_duration_days(prescription.duration)
        # ... checking expiry
```

This loads all prescriptions and processes in Python. For patients with 100+ prescriptions, this is inefficient.

**Better Approach**: Use database-side calculation with SQL functions.

**Fix Priority**: HIGH

---

### 1.4 Missing Rate Limiting on Public Shares Endpoint

**File**: `app/routers/shares.py` (Line 84)  
**Severity**: HIGH (Security)  
**Issue**: `/shares/access` endpoint has rate limiting (`@limiter.limit("20/hour")`) but is **public** (no auth required), making it vulnerable to brute force attacks on share tokens.

**Problem**:
- Rate limit of 20/hour is insufficient for token enumeration attacks
- No CAPTCHA or additional security for unauthenticated token access
- Attacker can try 20 invalid tokens per hour per IP address

**Recommendation**:
1. Implement per-IP rate limiting of 5 attempts per hour (stricter)
2. Add exponential backoff after 3 failed attempts
3. Implement CAPTCHA after 5 failed attempts
4. Add share token revocation on suspicious access patterns

**Fix Priority**: IMMEDIATE

---

### 1.5 Generic Exception Handling in Routers

**Files**: `app/routers/recommendations.py`, `app/routers/batch.py`, `app/routers/patients.py`  
**Severity**: HIGH (Security & Debugging)  
**Issue**: Catching broad `Exception` and returning raw error messages

**Problem Code** (recommendations.py, Line 65):
```python
except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to generate recommendations: {str(e)}",  # ❌ Exposes internals
    )
```

**Risks**:
- Exposes internal exception details to attackers
- Stack traces might leak database schema, function names, library versions
- Difficult to debug in production (generic error message)
- May leak PHI if exception message contains patient data

**Occurrences**:
- `app/routers/recommendations.py` lines 65, 123, 174, 216
- `app/routers/batch.py` lines 98, 204, 281
- `app/routers/appointments.py` line 70

**Recommendation**:
```python
except ValueError as e:
    logger.warning(f"Validation error in recommendations: {str(e)}")
    raise HTTPException(status_code=400, detail="Invalid input parameters")
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail="An internal error occurred")
```

**Fix Priority**: HIGH

---

## 2. SIGNIFICANT ISSUES (Medium Priority)

### 2.1 Missing Eager Loading: Dashboard Stats

**File**: `app/routers/dashboard.py` (Lines 37-127)  
**Severity**: MEDIUM  
**Issue**: Dashboard aggregations don't use eager loading, though they use aggregation functions (good). However, the query patterns could be optimized.

**Current Pattern**:
```python
patient_counts = (
    db.query(
        func.count().filter(Patient.tenant_id == tenant_id).label("total"),
        func.count().filter(...).label("recent"),
    )
    .select_from(Patient)
    .one()
)
```

**Observation**: This is actually correctly implemented - uses SQL aggregation instead of loading objects.

**No Issue Here** ✓

---

### 2.2 Missing Eager Loading: Batch Operations

**File**: `app/routers/batch.py` (Lines 30-100)  
**Severity**: MEDIUM  
**Issue**: Batch update/delete operations don't validate related records before transaction

**Problem** (Lines 110-135):
```python
for idx, update_data in enumerate(updates):
    patient_id = update_data.pop("id", None)
    if not patient_id:
        db.rollback()
        raise HTTPException(...)
    
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.tenant_id == current_user.tenant_id
    ).first()  # No eager loading of related data
```

If the batch operation needs to check appointments or prescriptions for validation, it will trigger N+1 queries.

**Fix Priority**: MEDIUM

---

### 2.3 Input Validation Gaps: Prescription Creation

**File**: `app/routers/prescriptions.py` (Lines 37-93)  
**Severity**: MEDIUM  
**Issue**: Minimal input validation before database insertion

**Problem**:
```python
db_prescription = Prescription(
    **prescription_data.model_dump(),  # Direct dict unpacking
    tenant_id=current_user.tenant_id,
)
```

**Missing Validation**:
- No check if patient exists
- No check if doctor exists
- No validation of dosage values
- No validation of duration format
- No check for duplicate active prescriptions (drug interactions not caught early)

**Recommendation**: 
Add service-layer validation before persistence:
```python
service = PrescriptionService(db)
try:
    db_prescription = service.create_prescription(prescription_data, current_user)
except PatientNotFoundError:
    raise HTTPException(status_code=404, detail="Patient not found")
except DoctorNotFoundError:
    raise HTTPException(status_code=404, detail="Doctor not found")
```

**Fix Priority**: MEDIUM

---

### 2.4 Missing Input Sanitization: FHIR Search Endpoint

**File**: `app/routers/fhir.py` (Lines 125-154)  
**Severity**: MEDIUM (Security)  
**Issue**: Search parameters not properly sanitized for ILIKE queries

**Problem Code**:
```python
if name:
    like = f"%{name}%"  # ❌ Potential SQL injection via ILIKE
    query = query.filter(
        (Patient.first_name.ilike(like)) | (Patient.last_name.ilike(like))
    )
```

**Risk**: While SQLAlchemy parameterizes the query, the ILIKE pattern construction could be exploited if the parameter handling changes.

**Recommendation**: Use SQLAlchemy's `literal_column()` carefully or add explicit validation.

**Fix Priority**: MEDIUM

---

### 2.5 Missing Error Handler for File Upload Failures

**File**: `app/routers/documents.py` (Lines 33-120)  
**Severity**: MEDIUM  
**Issue**: File upload endpoint lacks comprehensive error handling for disk I/O, permission, and size validation failures

**Missing Status Codes**:
- No `413 Payload Too Large` when file exceeds limit
- No `507 Insufficient Storage` for disk full scenarios
- No `500` with proper logging for I/O errors

**Current Code**:
```python
document = await document_service.upload_document(
    db=db,
    file=file,
    # ...
)
```

No try/catch around the upload operation.

**Recommendation**: Add proper error handling with specific status codes.

**Fix Priority**: MEDIUM

---

### 2.6 Cache Invalidation Race Condition: Share Service

**File**: `app/services/share_service.py` (Lines 152-170)  
**Severity**: MEDIUM  
**Issue**: No cache invalidation after share access count update

**Problem**:
```python
share.access_count += 1
share.last_accessed_at = datetime.now(timezone.utc)
db.commit()
```

If the share details are cached, the cache won't be invalidated after access count change. Subsequent requests may return stale access count.

**Recommendation**: 
```python
db.commit()
# Invalidate cache
cache_service.delete(f"share:detail:{share.id}")
```

**Fix Priority**: MEDIUM

---

## 3. MODERATE ISSUES (Lower Priority)

### 3.1 Missing Logging in Error Paths

**File**: Multiple routers  
**Severity**: LOW-MEDIUM  
**Issue**: Many error handlers don't log the underlying exception

**Examples**:
- `app/routers/appointments.py` line 70: `except Exception: raise HTTPException(...)`
- `app/routers/patients.py` line 947, 979: Silent exception swallowing

**Impact**: Difficult to debug production issues.

**Recommendation**: Always log exceptions before raising HTTP errors:
```python
except Exception as e:
    logger.error(f"Failed to fetch appointment: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to retrieve appointment")
```

**Fix Priority**: LOW

---

### 3.2 Missing Pagination Defaults Enforcement

**File**: `app/routers/prescriptions.py` (Line 107)  
**Severity**: LOW  
**Issue**: `limit` parameter can be set to 0 or negative values, bypassing pagination

**Current Code**:
```python
def get_prescriptions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    # ...
):
    prescriptions = (
        db.query(Prescription)
        # ...
        .offset(skip)
        .limit(limit)  # No validation!
        .all()
    )
```

**Risk**: Attacker can request `limit=999999` to load entire table.

**Recommendation**: Use Pydantic validators to enforce limits:
```python
from pydantic import Field, field_validator

class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
    
    @field_validator('limit')
    def limit_max(cls, v):
        return min(v, 1000)
```

**Fix Priority**: LOW

---

### 3.3 Missing Audit Log on Share Access Fails

**File**: `app/services/share_service.py` (Lines 133-139)  
**Severity**: LOW  
**Issue**: Failed share access attempts (invalid PIN, expired) not logged to audit trail

**Impact**: Can't detect brute force attacks or suspicious patterns.

**Recommendation**:
```python
def validate_and_access_share(...):
    share = get_share_by_token(db, token, pin)
    
    if not share:
        # Log failed access attempt
        log_audit_event(
            action="READ",
            resource_type="medical_record_share",
            status="failure",
            details={"reason": "invalid_token", "ip": ip_address},
        )
        raise HTTPException(...)
```

**Fix Priority**: LOW

---

## 4. SECURITY VULNERABILITIES

### 4.1 Missing CSRF Protection on State-Changing Operations

**File**: Multiple routers  
**Severity**: MEDIUM (if CSRF tokens not implemented elsewhere)  
**Issue**: POST/PUT/DELETE endpoints lack explicit CSRF token validation

**Note**: FastAPI doesn't automatically include CSRF protection. If frontend is separate SPA, verify CSRF tokens are in place in middleware.

**Check**: Review `app/core/middleware.py` for CSRF middleware.

**Fix Priority**: MEDIUM (depends on middleware implementation)

---

### 4.2 Missing Authorization Check on Document Download

**File**: `app/routers/documents.py` (not shown fully)  
**Severity**: HIGH (if present)  
**Issue**: Need to verify document download endpoint checks tenant/patient access

**Recommendation**: Verify file downloads are:
1. Scoped to current user's tenant
2. Scoped to authorized patients only
3. Logged with audit trail

**Fix Priority**: HIGH (pending full review)

---

### 4.3 Missing Validation on Sensitive Fields in Batch Operations

**File**: `app/routers/batch.py`  
**Severity**: MEDIUM  
**Issue**: Batch update accepts raw update dictionaries without field whitelisting

**Problem**:
```python
for idx, update_data in enumerate(updates):
    patient_id = update_data.pop("id", None)
    # ...
    # Any field in update_data could be updated!
    # Could allow privilege escalation if user_id field accepted
```

**Recommendation**: Use Pydantic schema to validate allowed fields:
```python
class PatientBatchUpdate(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    # Explicit whitelist - prevents injecting admin fields
```

**Fix Priority**: HIGH

---

## 5. PERFORMANCE ISSUES

### 5.1 Inefficient Appointment Slot Recommendation

**File**: `app/services/recommendation_service.py` (Lines 208-230)  
**Severity**: MEDIUM  
**Issue**: Extracts hours from all appointments, then checks availability in Python

**Current**:
```python
existing_appointments = (
    self.db.query(func.extract('hour', Appointment.appointment_date))
    .filter(...)
    .all()
)
occupied_hours = {int(apt[0]) for apt in existing_appointments if apt[0] is not None}
```

**Better**:
Use SQL aggregation to get occupied hours directly.

**Fix Priority**: MEDIUM

---

### 5.2 Cache Key Generation Inefficiency

**File**: `app/routers/patients.py` (Lines 140-152)  
**Severity**: LOW  
**Issue**: Cache key generation concatenates many parameters, creating verbose keys

```python
cache_key = cache_service.generate_key(
    "patients:list",
    current_user.tenant_id,
    pagination.page,
    pagination.page_size,
    sort.sort_by,
    sort.sort_order,
    filters.search,
    filters.date_from,
    filters.date_to,
)
```

**Impact**: Redis memory overhead with redundant keys.

**Recommendation**: Hash filter combinations or use structured cache keys.

**Fix Priority**: LOW

---

## 6. MISSING ERROR HANDLERS

### 6.1 Missing Handler for Duplicate Key Violations

**Severity**: MEDIUM  
**Issue**: When unique constraint violated, returns generic 500 error instead of 409 Conflict

**Recommendation**: Catch `IntegrityError`:
```python
from sqlalchemy.exc import IntegrityError

try:
    db.add(patient)
    db.commit()
except IntegrityError as e:
    db.rollback()
    if "uq_patients_tenant_email" in str(e):
        raise HTTPException(status_code=409, detail="Email already exists")
    raise
```

**Files Affected**:
- `app/routers/patients.py`
- `app/routers/prescriptions.py`
- `app/routers/users.py`

**Fix Priority**: MEDIUM

---

### 6.2 Missing Handler for Foreign Key Violations

**Severity**: MEDIUM  
**Issue**: Creating prescription with non-existent patient_id causes generic error

**Recommendation**: Add FK validation before INSERT:
```python
patient = db.query(Patient).filter(Patient.id == prescription_data.patient_id).first()
if not patient:
    raise HTTPException(status_code=404, detail="Patient not found")
```

**Fix Priority**: MEDIUM

---

## 7. LOGGING GAPS

### 7.1 Missing Request/Response Logging

**Severity**: LOW  
**Issue**: Important operations don't log full request context for debugging

**Affected**:
- Document uploads (no file size, MIME type logged)
- Batch operations (no operation count logged)
- Recommendation generation (no parameters logged)

**Recommendation**: Add structured logging with operation details.

**Fix Priority**: LOW

---

## Summary Table

| Category | Count | Severity | Action Required |
|----------|-------|----------|-----------------|
| N+1 Queries | 3 | HIGH | Refactor to use DB aggregation |
| Missing Rate Limits | 1 | HIGH | Add stricter limits to public endpoints |
| Generic Exception Handling | 7+ | HIGH | Add specific exception handling |
| Missing Validation | 5+ | MEDIUM | Add input validation to routers |
| Missing Eager Loading | 2+ | MEDIUM | Add joinedload/selectinload |
| Missing Error Handlers | 4+ | MEDIUM | Add specific HTTP status codes |
| Security Issues | 3+ | MEDIUM-HIGH | Add validation & sanitization |
| Logging Gaps | 5+ | LOW | Add detailed logging |

---

## Recommended Action Plan

### Phase 1: Critical (1-2 weeks)
1. ✅ Fix appointment overlap detection (SQL-based)
2. ✅ Strengthen rate limiting on public endpoints
3. ✅ Replace generic Exception handlers
4. ✅ Add input validation in batch operations

### Phase 2: Important (2-4 weeks)
1. ✅ Optimize prescription recommendation queries
2. ✅ Add missing error handlers for DB constraints
3. ✅ Implement file upload error handling
4. ✅ Add cache invalidation to share service

### Phase 3: Enhancement (4-8 weeks)
1. ✅ Add comprehensive logging
2. ✅ Optimize cache key generation
3. ✅ Improve query performance with aggregations
4. ✅ Add pagination validation

---

## Files Requiring Immediate Attention

### Tier 1 (Critical)
- `app/services/appointment_scheduler.py` - N+1 issue
- `app/routers/shares.py` - Security issue
- `app/routers/recommendations.py` - Exception handling
- `app/routers/batch.py` - Input validation & exceptions

### Tier 2 (Important)
- `app/services/recommendation_service.py` - Performance
- `app/routers/prescriptions.py` - Validation
- `app/routers/documents.py` - Error handling
- `app/routers/fhir.py` - Input sanitization

### Tier 3 (Enhancement)
- `app/routers/patients.py` - Logging
- `app/services/share_service.py` - Cache invalidation
- Multiple routers - Generic exception handling standardization

