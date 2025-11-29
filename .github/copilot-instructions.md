# Copilot Instructions for KeneyApp

These are concise, actionable rules for AI coding agents working in this repository. Focus on these patterns and workflows to be productive immediately.

## Architecture & Boundaries

- **Backend**: FastAPI (Python 3.11+) app in `app/` with routers in `app/routers`, business logic in `app/services`, ORM models in `app/models`, Pydantic schemas in `app/schemas`, and platform concerns in `app/core` (config, security, db, cache, rate limiting, metrics, audit).
- **Frontend**: React 18 + TypeScript in `frontend/` consuming REST (`/api/v1/...`) and GraphQL (`/graphql`).
- **Infrastructure**: PostgreSQL 15, Redis 7, Celery (workers + beat), Prometheus/Grafana. Local stack is orchestrated via `docker-compose.yml` and `./scripts/start_stack.sh`.
- **Multi-tenancy**: Most domain models are tenant-scoped. Seed scripts (`scripts/init_db.py`) create default tenant ("Default Tenant", slug: "default"); keep `tenant_id` set in all writes.
- **Healthcare Standards**: FHIR R4 interoperability in `app/fhir/`, medical terminologies (ICD-11, SNOMED CT, LOINC, ATC) in `app/services/terminology.py`, v3.0 features (messaging, documents, shares) in dedicated services.
- **Advanced Features**: E2E encrypted messaging (`app/services/messaging_service.py`), multi-level caching (`app/services/cache_service.py`), WebSocket notifications, DICOM support.

## Core Conventions (Backend)

### Routers & Endpoints

- Create `app/routers/<resource>.py` with `APIRouter(prefix="/<resource>", tags=["<resource>"])`.
- Include in `app/main.py` with `app.include_router(router, prefix=settings.API_V1_PREFIX)` alongside existing routers.
- Apply `@limiter.limit("X/minute")` from `app/core/rate_limit.py` (default: 10/minute for writes, 100/minute for reads).
- Example: `app/routers/patients.py` shows complete pattern.

### Authorization & RBAC

- Use dependency guards from `app/core/dependencies.py`:
  - `get_current_user` / `get_current_active_user` for authentication
  - `require_roles([UserRole.ADMIN, UserRole.DOCTOR, ...])` for RBAC
  - Roles: Admin, Doctor, Nurse, Receptionist. Super Admin bypasses all checks.
- JWT token includes `tenant_id` and `role`; both must be validated for multi-tenant security.

### Audit Logging (Required)

- Log CREATE/READ/UPDATE/DELETE and security events with `log_audit_event(...)` from `app/core/audit.py`.
- Pass `request` for correlation ID and client IP.
- Never log PHI in plain text; use sanitized details.
- Example: `app/routers/patients.py` shows comprehensive audit patterns.

### Caching Strategy

- **Simple caching**: Use `app/core/cache.py` helpers: `cache_get`, `cache_set`, `cache_clear_pattern`.
- **Advanced caching**: Use `CacheService` from `app/services/cache_service.py` for multi-level (memory + Redis) caching with statistics.
- **Naming**: `{resource}:list:{tenant}:{params}`, `{resource}:detail:{tenant}:{id}`.
- **TTL**: Lists 120s, details 300s (define constants like PATIENT_LIST_TTL_SECONDS, PATIENT_DETAIL_TTL_SECONDS).
- **Invalidation**: On mutation, clear related list/detail keys AND `dashboard:*` keys.
- **Key generation**: Use `cache_service.generate_key(prefix, *args, **kwargs)` for consistent hashing.
- See `docs/patterns/cache_keys.md` for complete patterns.

### PHI Encryption & Security

- Patient and sensitive payloads are encrypted/decrypted via `app/services/patient_security.py` and `app/core/encryption.py`.
- **Write flow**: `encrypt_patient_payload(data)` → store encrypted fields.
- **Read flow**: `serialize_patient_dict(patient)` → returns decrypted response.
- **Sensitive fields**: medical_history, allergies, emergency_contact, emergency_phone, address.
- **Never log PHI**: Sanitize all audit logs and error messages to exclude sensitive patient data.
- See `docs/ENCRYPTION_GUIDE.md` for complete encryption patterns.

### Metrics & Observability

- Correlation IDs via `CorrelationIdMiddleware` (X-Correlation-ID header).
- Prometheus metrics via `app/core/metrics.py`: increment counters like `patient_operations_total.labels(action="create", tenant_id=tenant).inc()`.
- Structured JSON logs with correlation IDs for tracing.
- `/metrics` endpoint exposes Prometheus-compatible metrics.

### Service Layer Pattern

- Business logic lives in `app/services/` (e.g., `patient_service.py`, `messaging_service.py`, `document_service.py`).
- Routers handle HTTP concerns (request/response, cache, audit, metrics); services handle domain logic and data access.
- Services accept `db: Session` in `__init__` and expose methods like `get_by_id(id, tenant_id)`, `create(data, tenant_id)`.
- Custom exceptions defined in `app/exceptions.py`: `PatientNotFoundError`, `DuplicateResourceError`, `raise_if_not_found`, `raise_if_tenant_mismatch`.
- Specialized services: `MessagingService` (E2E encryption), `CacheService` (multi-level caching), `DocumentService` (DICOM support), `ExportService` (bulk operations).

### Database Access

- Inject sessions with `db: Session = Depends(get_db)`. Never use global sessions.
- Models in `app/models/` extend `Base` from `app/core/database.py`.
- All tenant-scoped models have `tenant_id` column with index and foreign key.
- Timestamps: `created_at`, `updated_at` with `server_default=func.now()`.

## Workflows (Do This by Default)

### Local Development

- **Quick start**: `make dev` (uvicorn + React dev server).
- **Full stack**: `./scripts/start_stack.sh` (Docker Compose with DB, Redis, Celery, Prometheus).
  - On Windows: Run in Git Bash or WSL, or use `docker compose up -d` directly.
- **Backend only**: `uvicorn app.main:app --reload` (requires local PostgreSQL + Redis).
- **Frontend only**: `cd frontend && npm start`.
- **Windows users**: See `docs/WINDOWS_SETUP.md` for PowerShell-specific setup and ExecutionPolicy configuration.

### Testing

- **Backend**: `pytest tests/ -v` (skip slow tests: `-m "not slow and not smoke"`).
  - Markers: `smoke` (requires running server), `slow`, `integration`, `unit`, `api`, `security`, `performance`.
  - Target coverage: 70%+ (current: ~75%), tracked in `pytest.ini`.
- **Frontend**: `cd frontend && npm test -- --watchAll=false`.
- **Coverage**: `pytest --cov=app tests/` or `make test-cov`.
- **E2E integration**: `./scripts/run_e2e_tests.sh` (Docker-based, full scenarios in `tests/e2e/`).
- **CI parity**: `make ci` runs same checks as GitHub Actions.

### Code Quality

- **Format**: `make format` (Black + Prettier) or `black app tests`.
  - Windows: `.\scripts\format_all.ps1` or `.\scripts\format_all.ps1 -Check`.
- **Lint**: `make lint` (flake8 + mypy + ESLint).
  - Windows: `.\scripts\lint_all.ps1` or `.\scripts\lint_all.ps1 -Fix`.
- **Type checking**: `mypy app` (gradual typing, non-blocking).
- **Security**: `make security` (pip-audit + npm audit).

### Database Migrations

- **Create migration**: `alembic revision --autogenerate -m "description"`.
- **Apply migration**: `alembic upgrade head`.
- **Seed database**: `python scripts/init_db.py` (idempotent, creates default tenant + demo users).
  - Default tenant: name="Default Tenant", slug="default".
  - Demo users: admin/admin123, doctor/doctor123, nurse/nurse123, receptionist/receptionist123.
- **Reset database**: `make db-reset` (downgrade → upgrade → seed).

## Adding Features (Examples)

### New REST Endpoint

1. Define Pydantic schemas in `app/schemas/<resource>.py` (Create/Update/Response).
2. Create SQLAlchemy model in `app/models/<resource>.py` with `tenant_id` and timestamps.
3. Add Alembic migration: `alembic revision --autogenerate -m "add <resource>"`.
4. Create service in `app/services/<resource>_service.py` for business logic.
5. Create router in `app/routers/<resource>.py`:
   - Apply `require_roles([...])` for RBAC.
   - Add `@limiter.limit("X/minute")` for rate limiting.
   - Use `log_audit_event(...)` for CREATE/UPDATE/DELETE.
   - Implement caching with `cache_get`/`cache_set` and invalidation.
   - Increment metrics counters.
6. Include router in `app/main.py`: `app.include_router(resource.router, prefix=settings.API_V1_PREFIX)`.
7. See `docs/patterns/new_resource_scaffold.md` for complete template.

### Mutating Patient Data

- **Encrypt on write**: `encrypt_patient_payload(data)` before `db.add()`.
- **Decrypt on read**: `serialize_patient_dict(patient)` for responses.
- **Cache invalidation**: Clear `patients:list:*`, `patients:detail:*`, `dashboard:*`.
- **Metrics**: Increment `patient_operations_total.labels(action="...", tenant_id=...)`.
- **Audit**: Log action with sanitized details (no raw PHI).

### Background Tasks

- Add Celery tasks in `app/tasks.py` (see `generate_patient_report`, `send_appointment_reminder`).
- Trigger with `.delay(...)` from routers/services.
- Monitor with Flower at `http://localhost:5555`.

### GraphQL Extensions

- Schema/routers created via `app.graphql.schema.create_graphql_router()` and mounted at `/graphql`.
- Resolvers must enforce tenancy with `info.context.user.tenant_id` and RBAC with `ensure_roles(info, [UserRole.ADMIN, ...])` helper.
- Use `with get_session(info) as db:` context manager for scoped DB access.
- GraphQL context includes `GraphQLUserContext` with `id`, `username`, `tenant_id`, `role` from JWT.
- Mutations must log audit events with `log_audit_event(...)` and invalidate caches.
- Follow patterns in `app/graphql/schema.py` and see `docs/patterns/graphql_extension.md`.

### FHIR Interoperability

- Converters in `app/fhir/converters.py` map domain models ↔ FHIR resources.
- FHIR endpoints in `app/routers/fhir.py` follow HL7 FHIR R4 spec.
- Return OperationOutcome for errors (see `app/fhir/utils.py`).

## Project-Specific Gotchas

### Bootstrap Admin

- Local/test auth falls back to bootstrap admin when `ENABLE_BOOTSTRAP_ADMIN=True` (see `app/core/config.py` and `app/core/bootstrap.py`).
- **Never rely on this in production**; disable or override credentials.
- Creates default tenant "Default Tenant" (slug: "default") and admin user ("admin"/"admin123").

### Tenancy & Multi-Tenant Security

- **Always** filter queries by `tenant_id` from JWT payload/current user.
- Many tests expect this; missing tenant_id will cause 401/403 errors.
- Super Admin can access all tenants; others are restricted to their tenant.

### Rate Limiting & Security Headers

- Rate limits enforced by middleware (SlowAPI); bypass only for internal/health endpoints.
- Security headers (XSS, CSP, X-Frame-Options) set by `SecurityHeadersMiddleware` in `app/main.py`.
- CORS driven by `settings.ALLOWED_ORIGINS`; don't modify unless intentional.

### Error Handling

- Use FastAPI `HTTPException` with clear messages.
- FHIR endpoints return OperationOutcome for errors (see `app/main.py` exception handler).
- Custom exceptions in `app/exceptions.py` (raise, catch in routers, convert to HTTPException).

### OpenTelemetry Tracing

- Optional distributed tracing via `app/core/tracing.py`.
- Enable with `OTEL_ENABLED=True` and set `OTEL_EXPORTER_TYPE` (console/otlp/jaeger).
- Automatic span creation for HTTP requests and database queries.

## Where to Look

### Core Files

- **Entry point & wiring**: `app/main.py` (routers, middleware, exception handlers).
- **Settings**: `app/core/config.py` (Pydantic Settings; add new env vars here).
- **Auth/JWT**: `app/core/security.py`, dependencies: `app/core/dependencies.py`.
- **Caching & metrics**: `app/core/cache.py`, `app/core/metrics.py`.
- **Database**: `app/core/database.py` (session factory, Base class).

### Example Patterns

- **Complete CRUD pattern**: `app/routers/patients.py` (RBAC, caching, audit, encryption, metrics).
- **Service layer**: `app/services/patient_service.py` (business logic separation).
- **PHI handling**: `app/services/patient_security.py` (encryption/decryption workflows).
- **Background tasks**: `app/tasks.py` (Celery task patterns).
- **FHIR**: `app/routers/fhir.py`, `app/fhir/converters.py`.
- **GraphQL**: `app/graphql/schema.py`.

### Documentation

- **Comprehensive guides**: `README.md`, `docs/DEVELOPMENT.md`, `docs/guides/BUILD.md`, `ARCHITECTURE.md`.
- **Testing**: `docs/TESTING_GUIDE.md`, `docs/E2E_TESTING.md`, `docs/E2E_TESTING_QUICK_REF.md`.
- **Security & compliance**: `docs/ENCRYPTION_GUIDE.md`, `docs/SECURITY_BEST_PRACTICES.md`.
- **Healthcare standards**: `docs/MEDICAL_TERMINOLOGIES.md`, `docs/FHIR_GUIDE.md`.

## Run/Debug Quick Commands

```bash
# Start full stack (Docker)
./scripts/start_stack.sh          # Build and start all services
./scripts/start_stack.sh --logs   # Follow container logs
./scripts/start_stack.sh --down   # Stop and remove services

# Local development
make dev                          # Start backend + frontend
uvicorn app.main:app --reload     # Backend only
cd frontend && npm start          # Frontend only

# Testing
pytest tests/ -v                  # All backend tests
pytest -m "not smoke" -v          # Skip smoke tests
pytest --cov=app tests/           # With coverage
./scripts/run_e2e_tests.sh        # E2E integration tests (Docker)

# Database
alembic upgrade head              # Apply migrations
python scripts/init_db.py         # Seed database
make db-reset                     # Reset and reseed

# Code quality
make lint                         # All linters
make format                       # Format code
make security                     # Security scans
make ci                           # Full CI pipeline locally

# Build
./scripts/build.sh                # Full build with tests
./scripts/build.sh --quick        # Skip tests
make build                        # No Docker
make build-full                   # With Docker images
```

## Patterns & Checklists

### Pattern Documents

- **New resource scaffold (REST)**: `docs/patterns/new_resource_scaffold.md` (complete template with RBAC, caching, audit).
- **GraphQL extension guide**: `docs/patterns/graphql_extension.md` (resolver patterns, tenancy, mutations).
- **Cache keys and invalidation**: `docs/patterns/cache_keys.md` (naming conventions, TTLs, invalidation patterns).

### AI PR Checklist

Before committing, verify compliance with `.github/ai-commit-checklist.md`:

- ✅ Tenancy: DB reads/writes scoped by `tenant_id`.
- ✅ RBAC: Routes guarded with `require_roles`.
- ✅ Rate limits: Endpoints decorated appropriately.
- ✅ Audit: CREATE/READ/UPDATE/DELETE logged.
- ✅ PHI: Sensitive fields encrypted, never logged.
- ✅ Caching: Keys set/invalidated correctly.
- ✅ Metrics: Relevant counters incremented.
- ✅ Tests: `make lint` and `pytest -m "not smoke"` pass.

## Key Principles

1. **Tenancy first**: Filter by `tenant_id` everywhere.
2. **RBAC always**: Use `require_roles` on all protected endpoints.
3. **Audit everything**: Log all data access and mutations.
4. **Encrypt PHI**: Use `patient_security.py` helpers for sensitive data.
5. **Cache intelligently**: Set keys consistently, invalidate on mutation.
6. **Measure performance**: Increment metrics, use structured logs.
7. **Test thoroughly**: Add tests near affected features, run E2E for integration.
8. **Follow patterns**: Use existing routers/services as templates.

## Future Roadmap Context (from cahier_charges.md)

KeneyApp is designed for **French healthcare compliance** and international expansion:

### Planned French Healthcare Standards

- **INS (Identifiant National de Santé)**: Patient unique identifier - prepare patient models for INS integration
- **Pro Santé Connect**: CPS/e-CPS authentication for healthcare professionals
- **MSSanté**: Secure health messaging - current secure messaging is a foundation
- **DMP Integration**: French shared medical record system
- **Ségur FHIR Profiles**: ANS-specific FHIR profiles for French interoperability
- **HDS Certification**: Already architected for certified health data hosting compliance

### Current Implementation Status

- ✅ FHIR R4 base implementation (`app/fhir/`)
- ✅ Medical terminologies (ICD-11, SNOMED CT, LOINC, ATC) in place
- ✅ DICOM support for imaging documents
- ✅ Secure messaging foundation (v3.0 feature)
- ✅ Audit logging for compliance (RGPD/HIPAA/HDS-ready)
- 🚧 INS integration (planned)
- 🚧 Pro Santé Connect/CPS (planned)
- 🚧 MSSanté official connector (planned)
- 🚧 DMP/Ségur FHIR profiles (planned)

When implementing new healthcare features, consult `docs/cahier_charges.md` for complete requirements and compliance constraints.

Keep changes small, test incrementally, and consult pattern docs when uncertain.
