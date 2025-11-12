# AI Commit Checklist (KeneyApp)

Use this checklist before opening a PR or committing automated changes.

## Functional

- [ ] Tenancy: All DB reads/writes are scoped by `tenant_id` (from token/current user).
- [ ] RBAC: Routes/mutations guarded with `require_roles([...])` or `ensure_roles(...)`.
- [ ] Rate limits: Endpoints decorated with `@limiter.limit("X/minute")` appropriately.
- [ ] Audit: Create/Read/Update/Delete + security events use `log_audit_event(...)` with `request`.
- [ ] PHI: Sensitive fields encrypted on write and never logged; responses serialized via patient security where applicable.
- [ ] Caching: List/detail keys set consistently; invalidation patterns applied on mutate; dashboard keys cleared when needed.
- [ ] Metrics: Increment relevant counters/gauges (e.g., `patient_operations_total`).
- [ ] GraphQL: Resolvers enforce tenancy, RBAC, and use `get_session(info)`; mutations log audit events.

## Quality Gates

- [ ] Backend: `make lint` passes (flake8, black --check, mypy non-blocking).
- [ ] Backend tests: `pytest -m "not smoke"` pass locally.
- [ ] Frontend: `npm run lint` and `npm test -- --watchAll=false` pass if touched.
- [ ] Migrations: Alembic migration added and applied if models changed.
- [ ] Docs: Updated `.github/copilot-instructions.md` or `docs/patterns/*` if patterns changed.

## Safety

- [ ] No secrets or tokens in code or logs.
- [ ] CORS and security headers unchanged unless intentional.
- [ ] Rate limits remain reasonable for the endpoint risk.

Refer to:

- Backend patterns: `app/routers/patients.py`, `app/core/*`
- GraphQL patterns: `app/graphql/schema.py`
- Caching: `app/core/cache.py`, `docs/patterns/cache_keys.md`
- PHI: `app/services/patient_security.py`, `docs/patterns/phi_logging_checklist.md`
