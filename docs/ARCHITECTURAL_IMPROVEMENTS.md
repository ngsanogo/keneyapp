# Architectural Improvements from tmp Analysis

**Date**: November 5, 2025
**Purpose**: Document architectural patterns learned from GNU Health, Thalamus, and ERPNext/Frappe to enhance KeneyApp

---

## Executive Summary

After deep analysis of three major healthcare/business systems in tmp/, we've identified **10 key architectural patterns** that can significantly improve KeneyApp's design, maintainability, and extensibility.

**Systems Analyzed**:

1. **GNU Health (Tryton)** - Hospital management with 30+ modules
2. **Thalamus** - Federation server with ACL-based authorization
3. **ERPNext (Frappe)** - Modular ERP with hooks system

**Key Findings**:

- All three systems prioritize **modularity** over monolithic design
- **State machines** are critical for workflow management
- **Hook systems** enable extensibility without core modification
- **Dynamic field registration** supports custom extensions
- **Structured validation** with custom exceptions improves error handling

---

## Pattern 1: State Machine Workflows

### What We Learned (GNU Health Lab)

GNU Health uses explicit state machines for lab results:

```python
# From tmp/his/tryton/health_lab/health_lab.py
state = fields.Selection([
    ('draft', 'Draft'),
    ('done', 'Done'),
    ('validated', 'Validated'),
], 'State', readonly=True, sort=False)

@classmethod
@ModelView.button
def generate_document(cls, documents):
    """Transition draft → done"""
    hp = get_health_professional()
    cls.write(documents, {
        'done_by': hp,
        'done_date': datetime.now(),
        'state': 'done',
    })
```

**Benefits**:

- Clear audit trail of who did what when
- Enforces business rules (can't validate before completion)
- UI buttons automatically enable/disable based on state
- Database-level state tracking

### Apply to KeneyApp

**Current State**: Our models lack explicit workflow states

**Proposed Enhancement**:

```python
# app/models/lab.py - ENHANCED
from enum import Enum
from sqlalchemy import event

class LabResultState(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    VALIDATED = "validated"
    AMENDED = "amended"
    CANCELLED = "cancelled"

class LabResult(Base):
    __tablename__ = "lab_results"

    # ... existing fields ...

    state = Column(
        Enum(LabResultState),
        default=LabResultState.DRAFT,
        nullable=False,
        index=True
    )

    # Audit fields for each state transition
    reviewed_by_id = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    validated_by_id = Column(Integer, ForeignKey("users.id"))
    validated_at = Column(DateTime)
    validated_by = relationship("User", foreign_keys=[validated_by_id])

    @validates('state')
    def validate_state_transition(self, key, new_state):
        """Enforce valid state transitions"""
        valid_transitions = {
            LabResultState.DRAFT: [LabResultState.PENDING_REVIEW, LabResultState.CANCELLED],
            LabResultState.PENDING_REVIEW: [LabResultState.REVIEWED, LabResultState.DRAFT],
            LabResultState.REVIEWED: [LabResultState.VALIDATED, LabResultState.AMENDED],
            LabResultState.VALIDATED: [LabResultState.AMENDED],
            LabResultState.AMENDED: [LabResultState.PENDING_REVIEW],
            LabResultState.CANCELLED: [],  # Terminal state
        }

        if self.state and new_state not in valid_transitions.get(self.state, []):
            raise ValueError(
                f"Invalid state transition from {self.state} to {new_state}"
            )
        return new_state
```

**Implementation Steps**:

1. Add state enum and audit fields to LabResult model
2. Create migration: `alembic revision --autogenerate -m "add_lab_result_states"`
3. Add router endpoints: `POST /lab-results/{id}/submit`, `/review`, `/validate`
4. Add state transition service methods with RBAC checks
5. Update frontend to show state-specific actions

**Effort**: 1 sprint
**Priority**: High (improves compliance and audit trail)

---

## Pattern 2: Modular Package Structure

### What We Learned (GNU Health)

Tryton modules are self-contained packages with explicit dependencies:

```python
# tmp/his/tryton/health_lab/__init__.py
def register():
    """Register all models, wizards, and reports"""
    Pool.register(
        health_lab.TestType,
        health_lab.Lab,
        health_lab.GnuHealthTestCritearea,
        wizard.CreateLabTestOrderInit,
        sequences.LabTestSequence,
        module='health_lab', type_='model'
    )

    Pool.register(
        wizard.CreateLabTestOrder,
        module='health_lab', type_='wizard'
    )

# tryton.cfg declares dependencies
[tryton]
depends:
    health
xml:
    health_lab_view.xml
    data/lab_test_data.xml
    security/access_rights.xml
```

**Benefits**:

- Modules can be enabled/disabled independently
- Clear dependency graph prevents circular imports
- Each module has its own:
  - Models
  - Views/routers
  - Data fixtures
  - Security rules
  - Tests

### Apply to KeneyApp

**Current State**: Flat router/model structure without module boundaries

**Proposed Enhancement**:

```
app/
├── core/           # Existing - auth, config, db, cache
├── modules/        # NEW - Domain modules
│   ├── __init__.py
│   ├── patients/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routers.py
│   │   ├── services.py
│   │   ├── dependencies.py  # Module-specific deps
│   │   └── tests/
│   ├── lab/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routers.py
│   │   ├── services.py
│   │   ├── workflows.py     # State machine logic
│   │   └── tests/
│   ├── appointments/
│   └── billing/
└── main.py
```

**Module Registration Pattern**:

```python
# app/modules/__init__.py
from typing import List, Dict, Any
from fastapi import FastAPI

class Module:
    """Base class for KeneyApp modules"""

    name: str
    version: str
    depends: List[str] = []

    def register_models(self, app: FastAPI):
        """Register SQLAlchemy models"""
        pass

    def register_routers(self, app: FastAPI):
        """Register API routers"""
        pass

    def register_tasks(self, app: FastAPI):
        """Register Celery tasks"""
        pass

# app/modules/lab/__init__.py
from app.modules import Module
from . import routers, models

class LabModule(Module):
    name = "lab"
    version = "1.0.0"
    depends = ["patients"]  # Requires patients module

    def register_routers(self, app):
        from app.core.config import settings
        app.include_router(
            routers.router,
            prefix=f"{settings.API_V1_PREFIX}/lab",
            tags=["lab"]
        )

# app/main.py
from app.modules.lab import LabModule
from app.modules.patients import PatientModule

modules = [
    PatientModule(),
    LabModule(),
]

for module in modules:
    module.register_routers(app)
```

**Benefits**:

- Easier to add/remove features
- Teams can work on modules independently
- Clearer code organization
- Facilitates plugin system in future

**Implementation Steps**:

1. Create `app/modules/` directory structure
2. Migrate patients code to `app/modules/patients/`
3. Migrate lab code to `app/modules/lab/`
4. Create Module base class and registration system
5. Update imports and tests

**Effort**: 2-3 sprints (refactoring existing code)
**Priority**: Medium (improves long-term maintainability)

---

## Pattern 3: Dynamic Field Registration & Validation

### What We Learned (Tryton)

Tryton uses decorators and pyson for dynamic field behavior:

```python
# From GNU Health
@fields.depends('pathology')
def on_change_with_historize(self):
    """Auto-enable historize flag when pathology is set"""
    if (self.pathology):
        return True

STATES = {'readonly': Eval('state') == 'validated'}

specimen_type = fields.Char(
    'Specimen',
    help='Specimen type...',
    states={'invisible': Eval('source_type') != 'patient'}
)
```

**Benefits**:

- Fields can be conditionally required/hidden/readonly
- Business logic tied to field definitions
- Reduces boilerplate validation code

### Apply to KeneyApp

**Current State**: Pydantic validation is static; no dynamic field behavior

**Proposed Enhancement**:

```python
# app/schemas/base.py - NEW
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Callable, Dict, Any

class DynamicSchemaBase(BaseModel):
    """Base schema with dynamic field validation"""

    @classmethod
    def get_field_rules(cls, values: Dict[str, Any]) -> Dict[str, Dict]:
        """Override to define dynamic field rules based on other field values"""
        return {}

    @model_validator(mode='after')
    def apply_dynamic_rules(self):
        rules = self.get_field_rules(self.model_dump())

        for field_name, rule in rules.items():
            value = getattr(self, field_name)

            if rule.get('required') and not value:
                raise ValueError(f"{field_name} is required when {rule.get('condition')}")

            if rule.get('readonly') and value != getattr(self.__class__, field_name).default:
                raise ValueError(f"{field_name} is readonly when {rule.get('condition')}")

        return self

# app/schemas/lab.py - ENHANCED
class LabResultUpdate(DynamicSchemaBase):
    result_value: Optional[float] = None
    result_text: Optional[str] = None
    validated_by_id: Optional[int] = None
    state: Optional[LabResultState] = None

    @classmethod
    def get_field_rules(cls, values):
        rules = {}

        # If state is VALIDATED, validated_by_id is required
        if values.get('state') == LabResultState.VALIDATED:
            rules['validated_by_id'] = {
                'required': True,
                'condition': 'state is VALIDATED'
            }

        # If state is VALIDATED, can't change result
        if values.get('state') == LabResultState.VALIDATED:
            rules['result_value'] = {
                'readonly': True,
                'condition': 'state is VALIDATED'
            }

        return rules
```

**Effort**: 1 sprint
**Priority**: Medium

---

## Pattern 4: ACL-Based Fine-Grained Authorization

### What We Learned (Thalamus)

Thalamus uses JSON-based ACLs for method+endpoint+role permissions:

```python
# From tmp/thalamus/thalamus/thalamus.py
def access_control(username, roles, method, endpoint, view_args):
    """Check if user can access method on endpoint"""
    for user_role in roles:
        for acl_entry in ACL:
            if (acl_entry["role"] == user_role):
                actions = acl_entry["permissions"]
                if (endpoint in actions[method]):
                    # Check global vs personal access
                    if view_args:
                        if (username == view_args["person_id"] or
                                actions["global"] == "True"):
                            return True
                    else:
                        return True
    return False

# ACL example (JSON):
{
  "role": "health_professional",
  "permissions": {
    "GET": ["person", "page", "book"],
    "POST": ["page"],
    "PATCH": ["page"],
    "DELETE": [],
    "global": "False"  # Can only see own records
  }
}
```

**Benefits**:

- Centralized permission management
- Easier to audit who can do what
- Supports "own records only" vs "global access"
- No code changes needed to adjust permissions

### Apply to KeneyApp

**Current State**: Role-based decorators (`require_roles(['Admin', 'Doctor'])`)

**Proposed Enhancement**:

```python
# app/core/acl.py - NEW
from typing import List, Dict, Optional
import json
from pathlib import Path
from fastapi import Request, HTTPException

class ACLManager:
    """Fine-grained access control list manager"""

    def __init__(self, acl_file: Path):
        with open(acl_file) as f:
            self.acl: List[Dict] = json.load(f)

    def check_access(
        self,
        user_roles: List[str],
        method: str,
        resource: str,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        owner_id: Optional[int] = None
    ) -> bool:
        """Check if any of user's roles grant access"""

        for role in user_roles:
            for entry in self.acl:
                if entry["role"] != role:
                    continue

                permissions = entry["permissions"]

                # Check if method+resource is allowed
                if resource not in permissions.get(method, []):
                    continue

                # Check ownership if resource has owner
                if resource_id and owner_id:
                    if permissions.get("scope") == "own" and user_id != owner_id:
                        continue

                return True  # Access granted

        return False  # No role grants access

# config/acl.json - NEW
[
  {
    "role": "Doctor",
    "permissions": {
      "GET": ["patients", "appointments", "lab_results", "documents"],
      "POST": ["patients", "appointments", "lab_results"],
      "PUT": ["patients", "appointments", "lab_results"],
      "DELETE": [],
      "scope": "tenant"  # Can access all in tenant
    }
  },
  {
    "role": "Nurse",
    "permissions": {
      "GET": ["patients", "appointments", "lab_results"],
      "POST": ["appointments"],
      "PUT": ["appointments"],
      "DELETE": [],
      "scope": "tenant"
    }
  },
  {
    "role": "Receptionist",
    "permissions": {
      "GET": ["patients", "appointments"],
      "POST": ["patients", "appointments"],
      "PUT": ["patients", "appointments"],
      "DELETE": [],
      "scope": "tenant"
    }
  },
  {
    "role": "Patient",
    "permissions": {
      "GET": ["patients", "appointments", "documents"],
      "POST": ["appointments"],
      "PUT": [],
      "DELETE": [],
      "scope": "own"  # Can only see own records
    }
  }
]

# app/core/dependencies.py - ENHANCED
from app.core.acl import ACLManager
from app.core.config import settings

acl_manager = ACLManager(Path(settings.ACL_FILE))

def require_resource_access(resource: str, owner_field: str = None):
    """Dependency for checking ACL permissions"""
    async def dependency(
        request: Request,
        current_user: User = Depends(get_current_active_user)
    ):
        method = request.method

        # Extract resource owner if applicable
        owner_id = None
        if owner_field and hasattr(request.state, 'resource'):
            owner_id = getattr(request.state.resource, owner_field)

        if not acl_manager.check_access(
            user_roles=[current_user.role],
            method=method,
            resource=resource,
            user_id=current_user.id,
            owner_id=owner_id
        ):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for {method} {resource}"
            )

        return current_user

    return dependency

# Usage in routers
@router.get("/patients/{patient_id}")
async def get_patient(
    patient_id: int,
    current_user: User = Depends(require_resource_access("patients"))
):
    # ACL automatically checks if user can GET patients
    pass
```

**Benefits**:

- Permissions configurable without code changes
- Auditable permission matrix
- Easier compliance reporting
- Supports future multi-tenancy with "own" vs "tenant" vs "global" scopes

**Implementation Steps**:

1. Create `app/core/acl.py` and ACLManager class
2. Define initial `config/acl.json`
3. Add `require_resource_access()` dependency
4. Gradually migrate from `require_roles()` to ACL
5. Add tests for permission matrix

**Effort**: 2 sprints
**Priority**: Medium-High (enhances security model)

---

## Pattern 5: Hooks System for Extensibility

### What We Learned (ERPNext/Frappe)

Frappe uses a hooks.py system for app extensions:

```python
# From tmp/erpnext/erpnext/hooks.py
# DocType method overrides
doctype_js = {
    "Address": "public/js/address.js",
    "Communication": "public/js/communication.js",
}

# Extend core classes
extend_doctype_class = {
    "Address": "erpnext.accounts.custom.address.ERPNextAddress"
}

# Override methods
override_whitelisted_methods = {
    "frappe.www.contact.send_message": "erpnext.templates.utils.send_message"
}

# Lifecycle hooks
after_install = "erpnext.setup.install.after_install"
boot_session = "erpnext.startup.boot.boot_session"
on_session_creation = "erpnext.portal.utils.create_customer_or_supplier"
```

**Benefits**:

- Third-party apps can extend core without modifying it
- Clear extension points
- Lifecycle hooks for initialization
- Method override system

### Apply to KeneyApp

**Current State**: No formal plugin/extension system

**Proposed Enhancement**:

```python
# app/core/hooks.py - NEW
from typing import Callable, Dict, List, Any
from enum import Enum

class HookPoint(str, Enum):
    """Available hook points in KeneyApp"""
    BEFORE_PATIENT_CREATE = "before_patient_create"
    AFTER_PATIENT_CREATE = "after_patient_create"
    BEFORE_APPOINTMENT_CREATE = "before_appointment_create"
    AFTER_APPOINTMENT_CREATE = "after_appointment_create"
    BEFORE_LAB_RESULT_VALIDATE = "before_lab_result_validate"
    AFTER_LAB_RESULT_VALIDATE = "after_lab_result_validate"
    ON_USER_LOGIN = "on_user_login"
    ON_SESSION_START = "on_session_start"

class HookManager:
    """Manages extension hooks throughout the application"""

    def __init__(self):
        self._hooks: Dict[HookPoint, List[Callable]] = {
            hook: [] for hook in HookPoint
        }

    def register(self, hook_point: HookPoint, handler: Callable):
        """Register a handler for a hook point"""
        self._hooks[hook_point].append(handler)

    async def execute(self, hook_point: HookPoint, context: Dict[str, Any]):
        """Execute all handlers for a hook point"""
        for handler in self._hooks[hook_point]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(context)
                else:
                    handler(context)
            except Exception as e:
                # Log but don't fail the operation
                logger.error(f"Hook {hook_point} handler failed: {e}")

# Global hook manager instance
hook_manager = HookManager()

# app/plugins/__init__.py - NEW
"""Plugin system for KeneyApp extensions"""

class Plugin:
    """Base class for KeneyApp plugins"""

    name: str
    version: str
    author: str

    def register_hooks(self, hook_manager: HookManager):
        """Register plugin hooks"""
        pass

    def register_routers(self, app: FastAPI):
        """Register plugin routers"""
        pass

# app/plugins/example_audit_plugin.py - EXAMPLE
from app.core.hooks import hook_manager, HookPoint
from app.plugins import Plugin

class AuditPlugin(Plugin):
    name = "Enhanced Audit Logger"
    version = "1.0.0"
    author = "KeneyApp Team"

    def register_hooks(self, hook_manager):
        hook_manager.register(
            HookPoint.AFTER_PATIENT_CREATE,
            self.log_patient_creation
        )
        hook_manager.register(
            HookPoint.AFTER_LAB_RESULT_VALIDATE,
            self.notify_lab_validation
        )

    def log_patient_creation(self, context):
        patient = context['patient']
        user = context['user']
        print(f"[AUDIT] Patient {patient.id} created by {user.username}")

    async def notify_lab_validation(self, context):
        lab_result = context['lab_result']
        # Send notification to doctor
        await send_notification(
            user_id=lab_result.doctor_id,
            message=f"Lab result {lab_result.id} validated"
        )

# Usage in services
# app/services/patient_service.py
from app.core.hooks import hook_manager, HookPoint

async def create_patient(data: PatientCreate, db: Session, user: User):
    # ... create patient ...

    # Execute hooks
    await hook_manager.execute(HookPoint.AFTER_PATIENT_CREATE, {
        'patient': patient,
        'user': user,
        'db': db
    })

    return patient
```

**Benefits**:

- Plugins can extend core functionality
- Easier to add custom business logic per deployment
- No core code modification needed
- Testable in isolation

**Implementation Steps**:

1. Create `app/core/hooks.py` with HookManager
2. Create `app/plugins/` directory structure
3. Add hook execution points in key services
4. Document available hooks and their contexts
5. Create example plugin

**Effort**: 1-2 sprints
**Priority**: Medium (enables future extensibility)

---

## Pattern 6: Custom Exception Hierarchy

### What We Learned (ERPNext & GNU Health)

Both systems use custom exception types for domain-specific errors:

```python
# From ERPNext
class PartyFrozen(frappe.ValidationError):
    pass

class InvalidAccountCurrency(frappe.ValidationError):
    pass

# From GNU Health
class LabOrderExists(UserError):
    pass
```

**Benefits**:

- Clearer error semantics
- Easier to catch specific errors
- Better error messages
- Facilitates error handling middleware

### Apply to KeneyApp

**Current State**: Using generic HTTPException

**Proposed Enhancement**:

```python
# app/exceptions.py - ENHANCED
from fastapi import HTTPException, status

class KeneyAppException(HTTPException):
    """Base exception for KeneyApp"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "An error occurred"

    def __init__(self, detail: str = None):
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail
        )

# Validation errors (4xx)
class ValidationError(KeneyAppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

class PatientNotFoundError(KeneyAppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Patient not found"

class InvalidLabResultError(ValidationError):
    detail = "Lab result data is invalid"

class LabResultAlreadyValidatedError(ValidationError):
    detail = "Lab result has already been validated and cannot be modified"

class InvalidStateTransitionError(ValidationError):
    def __init__(self, from_state, to_state):
        super().__init__(
            detail=f"Cannot transition from {from_state} to {to_state}"
        )

class InsufficientPermissionsError(KeneyAppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Insufficient permissions for this operation"

# Business logic errors (409)
class AppointmentConflictError(KeneyAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Appointment time conflicts with existing appointment"

class TenantQuotaExceededError(KeneyAppException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    detail = "Tenant quota exceeded"

# Usage in services
def validate_lab_result(lab_result: LabResult, new_state: LabResultState):
    if lab_result.state == LabResultState.VALIDATED:
        raise LabResultAlreadyValidatedError()

    if lab_result.state == LabResultState.CANCELLED:
        raise InvalidStateTransitionError(lab_result.state, new_state)

# Exception handler in main.py
@app.exception_handler(KeneyAppException)
async def keneyapp_exception_handler(request: Request, exc: KeneyAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": exc.detail,
            "correlation_id": request.state.correlation_id
        }
    )
```

**Effort**: 1 sprint
**Priority**: Medium

---

## Pattern 7: Sequence Generators for IDs

### What We Learned (GNU Health)

Tryton uses configurable sequence generators:

```python
# From tmp/his/tryton/health_lab/sequences.py
lab_test_sequence = fields.Many2One(
    'ir.sequence', 'Lab test sequence', required=True,
    domain=[('sequence_type', '=', Id('health_lab', 'seq_type_gnuhealth_lab_test'))]
)

@classmethod
def generate_code(cls, **pattern):
    Config = Pool().get('gnuhealth.sequences')
    config = Config(1)
    sequence = config.get_multivalue('lab_test_sequence', **pattern)
    if sequence:
        return sequence.get()
```

**Benefits**:

- Human-readable IDs (LAB-2025-001234)
- Configurable per tenant
- Sequential but readable
- Better for paper forms and phone communication

### Apply to KeneyApp

**Current State**: Auto-increment integer IDs

**Proposed Enhancement**:

```python
# app/models/sequence.py - NEW
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Session
from datetime import datetime
import threading

_sequence_locks = {}

class Sequence(Base):
    __tablename__ = "sequences"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(50), nullable=False)  # e.g., "lab_result"
    prefix = Column(String(20))  # e.g., "LAB"
    suffix = Column(String(20))  # e.g., "/{year}"
    padding = Column(Integer, default=6)  # Zero-pad to 6 digits
    current_value = Column(Integer, default=0)
    reset_period = Column(String(20))  # daily, monthly, yearly, never
    last_reset = Column(DateTime)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_tenant_sequence'),
    )

class SequenceGenerator:
    """Thread-safe sequence number generator"""

    @classmethod
    def next_value(
        cls,
        db: Session,
        tenant_id: int,
        sequence_name: str
    ) -> str:
        """Generate next sequence value"""

        # Thread-safe lock per tenant+sequence
        lock_key = f"{tenant_id}:{sequence_name}"
        if lock_key not in _sequence_locks:
            _sequence_locks[lock_key] = threading.Lock()

        with _sequence_locks[lock_key]:
            sequence = db.query(Sequence).filter(
                Sequence.tenant_id == tenant_id,
                Sequence.name == sequence_name
            ).with_for_update().first()

            if not sequence:
                raise ValueError(f"Sequence {sequence_name} not configured")

            # Check if reset needed
            now = datetime.now()
            should_reset = False

            if sequence.reset_period == 'daily' and sequence.last_reset:
                should_reset = sequence.last_reset.date() < now.date()
            elif sequence.reset_period == 'monthly' and sequence.last_reset:
                should_reset = (
                    sequence.last_reset.year < now.year or
                    sequence.last_reset.month < now.month
                )
            elif sequence.reset_period == 'yearly' and sequence.last_reset:
                should_reset = sequence.last_reset.year < now.year

            if should_reset:
                sequence.current_value = 0
                sequence.last_reset = now

            # Increment
            sequence.current_value += 1
            db.commit()

            # Format
            parts = []
            if sequence.prefix:
                parts.append(sequence.prefix)

            # Add padded number
            parts.append(str(sequence.current_value).zfill(sequence.padding))

            # Process suffix (supports {year}, {month}, {day})
            if sequence.suffix:
                suffix = sequence.suffix.format(
                    year=now.year,
                    month=str(now.month).zfill(2),
                    day=str(now.day).zfill(2)
                )
                parts.append(suffix)

            return '-'.join(parts)

# Usage in models
class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, index=True)  # LAB-000123-2025
    # ... other fields ...

# In service
def create_lab_result(data: LabResultCreate, db: Session, user: User):
    lab_result = LabResult(**data.dict())

    # Generate code
    lab_result.code = SequenceGenerator.next_value(
        db=db,
        tenant_id=user.tenant_id,
        sequence_name="lab_result"
    )

    db.add(lab_result)
    db.commit()
    return lab_result

# Seed data for sequences
INSERT INTO sequences (tenant_id, name, prefix, suffix, padding, reset_period) VALUES
(1, 'lab_result', 'LAB', '/{year}', 6, 'yearly'),
(1, 'patient', 'PAT', '', 8, 'never'),
(1, 'appointment', 'APT', '/{year}-{month}', 5, 'monthly');
```

**Benefits**:

- Easier verbal communication ("Lab result LAB-123-2025")
- Tenant-specific sequences
- Configurable formats per deployment
- Better for printed forms

**Effort**: 1-2 sprints
**Priority**: Medium-Low (nice to have)

---

## Pattern 8: Report Template System

### What We Learned (GNU Health)

Lab module has configurable report styles:

```python
report_style = fields.Selection([
    ('tbl_h_r_u_nr', 'Table with result, unit and normal_range columns'),
    ('tbl_h_r_nr', 'Table with result and normal_range columns'),
    ('tbl_h_r', 'Table with result column'),
    ('no_tbl', 'Do not use table'),
    ('do_not_show', 'Do not show in report'),
], 'Report style', sort=False)

tags = fields.Char('Tags', help='Tags used in if directive of report template')

def has_tag(self, tag):
    tags = self.tags.split(':')
    return (tag in tags)
```

**Benefits**:

- Different report layouts per test type
- Template-driven report generation
- Conditional sections based on tags

### Apply to KeneyApp

**Implementation**: Create report template system

```python
# app/services/report_generator.py - NEW
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

class ReportGenerator:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader('app/templates/reports/')
        )

    def generate_lab_report(self, lab_result: LabResult) -> bytes:
        """Generate PDF lab report"""

        # Select template based on test type report_style
        template_name = f"lab_report_{lab_result.test_type.report_style}.html"
        template = self.env.get_template(template_name)

        html_content = template.render(
            lab_result=lab_result,
            patient=lab_result.patient,
            criteria=lab_result.criteria,
            generated_at=datetime.now()
        )

        return HTML(string=html_content).write_pdf()
```

**Effort**: 1 sprint
**Priority**: Medium

---

## Pattern 9: Search and Filter DSL

### What We Learned (Tryton)

Flexible search with domain expressions:

```python
@classmethod
def search_rec_name(cls, name, clause):
    """ Search for the full name and the code """
    field = None
    for field in ('name', 'code'):
        tests = cls.search([(field,) + tuple(clause[1:])], limit=1)
        if tests:
            break
    if tests:
        return [(field,) + tuple(clause[1:])]
    return [(cls._rec_name,) + tuple(clause[1:])]
```

**Benefits**:

- Search across multiple fields
- Consistent API for filtering

### Apply to KeneyApp

**Implementation**: Add search helpers to routers

```python
# app/core/search.py - NEW
from typing import List, Any
from sqlalchemy.orm import Query

class SearchFilter:
    """Helper for building SQLAlchemy queries from API filters"""

    @staticmethod
    def apply_filters(
        query: Query,
        model,
        filters: dict
    ) -> Query:
        """Apply filters to query"""

        for field, value in filters.items():
            if hasattr(model, field):
                if isinstance(value, str) and '*' in value:
                    # Wildcard search
                    pattern = value.replace('*', '%')
                    query = query.filter(getattr(model, field).like(pattern))
                elif isinstance(value, list):
                    # IN filter
                    query = query.filter(getattr(model, field).in_(value))
                else:
                    # Exact match
                    query = query.filter(getattr(model, field) == value)

        return query

# Usage
@router.get("/patients/")
def list_patients(
    name: str = None,
    status: List[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Patient)

    filters = {}
    if name:
        filters['name'] = f"*{name}*"  # Wildcard
    if status:
        filters['status'] = status  # IN filter

    query = SearchFilter.apply_filters(query, Patient, filters)
    return query.all()
```

**Effort**: 1 sprint
**Priority**: Low-Medium

---

## Pattern 10: Feature Flags System

### What We Learned (ERPNext)

ERPNext uses hooks for conditional features:

```python
# Enable/disable modules
modules = ['accounting', 'inventory', 'manufacturing']

# Feature flags in config
features = {
    'use_multi_currency': True,
    'enable_analytics': False
}
```

**Benefits**:

- Enable features per tenant
- A/B testing
- Gradual rollouts

### Apply to KeneyApp

```python
# app/core/features.py - NEW
from typing import Dict, Any
from functools import wraps

class FeatureFlags:
    """Manage feature flags per tenant"""

    def __init__(self):
        self._flags: Dict[int, Dict[str, bool]] = {}

    def is_enabled(self, tenant_id: int, feature: str) -> bool:
        """Check if feature is enabled for tenant"""
        return self._flags.get(tenant_id, {}).get(feature, False)

    def require_feature(feature: str):
        """Decorator to require feature flag"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract tenant_id from current_user
                current_user = kwargs.get('current_user')
                if not feature_flags.is_enabled(current_user.tenant_id, feature):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Feature '{feature}' not enabled"
                    )
                return await func(*args, **kwargs)
            return wrapper
        return decorator

feature_flags = FeatureFlags()

# Usage
@router.post("/lab-results/{id}/validate")
@require_feature("advanced_lab_workflow")
async def validate_lab_result(
    id: int,
    current_user: User = Depends(get_current_active_user)
):
    # Only accessible if feature enabled
    pass
```

**Effort**: 1 sprint
**Priority**: Low (future-proofing)

---

## Implementation Roadmap

### Phase 1: Foundation (Sprints 1-2)

**Goal**: Core improvements that benefit everything

1. ✅ **State Machine Workflows** - Lab results (HIGH PRIORITY)
   - Effort: 1 sprint
   - Impact: Compliance, audit trail

2. ✅ **Custom Exception Hierarchy** - Better error handling
   - Effort: 1 sprint
   - Impact: Debugging, API clarity

### Phase 2: Architecture (Sprints 3-5)

**Goal**: Structural improvements

3. **Modular Package Structure** - Reorganize code
   - Effort: 2-3 sprints
   - Impact: Long-term maintainability

4. **ACL-Based Authorization** - Fine-grained permissions
   - Effort: 2 sprints
   - Impact: Security, compliance

### Phase 3: Extensibility (Sprints 6-7)

**Goal**: Plugin system and dynamic behavior

5. **Hooks System** - Extension points
   - Effort: 1-2 sprints
   - Impact: Customization without core changes

6. **Dynamic Field Validation** - Context-aware validation
   - Effort: 1 sprint
   - Impact: Better UX, fewer errors

### Phase 4: Polish (Sprints 8-10)

**Goal**: Nice-to-have improvements

7. **Sequence Generators** - Human-readable IDs
   - Effort: 1-2 sprints
   - Impact: Usability

8. **Report Template System** - Flexible reports
   - Effort: 1 sprint
   - Impact: Professional output

9. **Search/Filter DSL** - Better queries
   - Effort: 1 sprint
   - Impact: API usability

10. **Feature Flags** - Tenant-specific features
    - Effort: 1 sprint
    - Impact: Gradual rollouts

---

## Measuring Success

**Metrics to Track**:

1. **Code Quality**
   - Lines of code per module (target: <500)
   - Cyclomatic complexity (target: <10)
   - Test coverage (maintain >70%)

2. **Developer Experience**
   - Time to add new feature (target: <2 days)
   - Number of merge conflicts (target: <5/month)
   - Documentation coverage (target: 100% of public APIs)

3. **System Health**
   - API error rate (target: <1%)
   - Permission denial logs (monitor for misconfiguration)
   - Plugin load failures (target: 0)

---

## Conclusion

By adopting these 10 architectural patterns from GNU Health, Thalamus, and ERPNext, KeneyApp will gain:

✅ **Better Modularity** - Easier to add/remove features
✅ **Stronger Security** - Fine-grained ACL system
✅ **Improved Compliance** - State machines and audit trails
✅ **Enhanced Extensibility** - Plugin system for customization
✅ **Professional UX** - Better IDs, reports, and error messages

**Next Steps**:

1. Review this document with team
2. Prioritize Phase 1 items for immediate implementation
3. Create detailed technical specs for approved patterns
4. Begin implementation in next sprint

---

**Document Version**: 1.0
**Last Updated**: November 5, 2025
**Status**: Ready for team review
