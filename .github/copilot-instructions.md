# Copilot Instructions for KeneyApp

These are concise, actionable rules for AI coding agents working in this repository. Focus on these patterns and workflows to be productive immediately.

## Architecture & Boundaries
- Backend: FastAPI app in `app/` with routers in `app/routers`, business logic in `app/services`, ORM models in `app/models`, Pydantic schemas in `app/schemas`, and platform concerns in `app/core` (config, security, db, cache, rate limiting, metrics, audit).
- Frontend: React + TypeScript in `frontend/` consuming REST (`/api/v1/...`) and GraphQL (`/graphql`).
- Infra: PostgreSQL, Redis, Celery (workers + beat), Prometheus/Grafana. Local stack is orchestrated via `docker-compose.yml` and `./scripts/start_stack.sh`.
- Multi-tenant: Most domain models are tenant-scoped. Seed and tests rely on a default tenant; keep `tenant_id` set in writes.

## Core Conventions (Backend)
- Routers: Create `app/routers/<resource>.py` with `APIRouter(prefix="/<resource>", tags=["<resource>"])`. Include it in `app/main.py` with `app.include_router(router, prefix=settings.API_V1_PREFIX)` and import alongside existing routers.
- AuthZ: Use dependency guards from `app/core/dependencies.py`:
  - `get_current_user` / `get_current_active_user` for auth
  - `require_roles([...])` for RBAC (Admin, Doctor, Nurse, Receptionist; Super Admin bypasses)
- Rate limits: Decorate endpoints with `@limiter.limit("X/minute")` from `app/core/rate_limit.py`.
- Audit logging: Log CREATE/READ/UPDATE/DELETE and security events with `log_audit_event(...)` from `app/core/audit.py` (pass `request` for correlation and IP). Don’t log PHI in plain text.
- Caching: Use Redis helpers in `app/core/cache.py`.
  - Keys: `patients:list:{tenant}:{skip}:{limit}`, `patients:detail:{tenant}:{id}`. Invalidate related list/detail keys and dashboard keys when mutating.
- Encryption & PHI: Patient payloads are encrypted/decrypted via `app/services/patient_security.py` and `app/core/encryption.py`. Always pass write payloads through encryptors and serialize responses.
- Metrics & Logs: Correlation IDs via `CorrelationIdMiddleware`; Prometheus metrics via `app/core/metrics.py` and `/metrics`. Prefer structured logs; rely on existing middlewares in `app/main.py`.
- DB access: Inject sessions with `db: Session = Depends(get_db)`. Never keep global sessions.

## Workflows (Do This by Default)
- Local dev: `make dev` (uvicorn + React dev server). Full stack: `./scripts/start_stack.sh` or `make docker-up`.
- Tests: `pytest tests/ -v` (backend), `cd frontend && npm test` (frontend). CI runs `pytest -m "not smoke"` and docker smoke tests.
- Lint/format/type-check: `make lint` or individually `black --check`, `flake8`, `mypy`. Frontend: `npm run lint`, `npm run format:check`.
- DB migrations: `alembic revision --autogenerate -m "..."`, then `alembic upgrade head`. Seed idempotently with `python scripts/init_db.py`.
- CI parity: `make ci` runs the same checks as GitHub Actions.

## Adding Features (Examples)
- New endpoint: define Pydantic schemas in `app/schemas/...`, add router handlers in `app/routers/...`, apply `require_roles`, validate inputs, add rate limits and audit logs, and update `app/main.py` to include the router.
- Mutating patient data: encrypt request payload with `encrypt_patient_payload`, serialize response with `serialize_patient_dict`, update Redis caches and bump metrics like `patient_operations_total`.
- Background work: Add Celery tasks in `app/tasks.py` (see `generate_patient_report`, `send_appointment_reminder`). Trigger with `.delay(...)` from routers/services.
- GraphQL: Schema/routers are created via `app.graphql.schema.create_graphql_router()` and mounted at `/graphql`; follow existing patterns when extending.

## Project-Specific Gotchas
- Bootstrap admin: Local/test auth can fall back to bootstrap admin when `ENABLE_BOOTSTRAP_ADMIN=True` (see `app/core/config.py` and `app/core/bootstrap.py`). Don’t rely on this in production code paths.
- Tenancy: Always filter queries by `tenant_id` from the JWT payload/current user. Many tests expect this.
- Rate limits & security headers are enforced by middleware; don’t remove or bypass. CORS is driven by `settings.ALLOWED_ORIGINS`.
- Errors: Use FastAPI HTTPException with clear messages; keep error formats consistent with examples in `docs/API_REFERENCE.md`.

## Where to Look
- Entry point and wiring: `app/main.py`
- Settings: `app/core/config.py` (Pydantic Settings; add new env vars here)
- Auth/JWT: `app/core/security.py`, deps: `app/core/dependencies.py`
- Caching & metrics: `app/core/cache.py`, `app/core/metrics.py`
- Patients pattern: `app/routers/patients.py`
- Tasks: `app/tasks.py`
- Docs for flows & commands: `README.md`, `docs/DEVELOPMENT.md`, `BUILD.md`, `docs/TESTING_GUIDE.md`

## Run/Debug Quick Commands
- Start stack: `./scripts/start_stack.sh` (add `--logs` to tail)
- Backend only: `uvicorn app.main:app --reload`
- Tests with coverage: `pytest --cov=app tests/`
- Docker smoke locally: `docker compose up -d && pytest tests/test_smoke.py -v`

Keep changes small, add tests near the affected feature, and follow existing patterns for RBAC, audit logging, caching, and encryption.

## Patterns & Checklists

- New resource scaffold (REST): `docs/patterns/new_resource_scaffold.md`
- GraphQL extension guide: `docs/patterns/graphql_extension.md`
- PHI logging checklist: `docs/patterns/phi_logging_checklist.md`
- Cache keys and invalidation: `docs/patterns/cache_keys.md`
- AI PR checklist: `.github/ai-commit-checklist.md`
