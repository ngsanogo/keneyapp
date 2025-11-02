# Cache Keys & Invalidation Patterns

KeneyApp uses Redis for read-side performance. Follow these key families and invalidation rules.

## Patients (existing example)
- Lists: `patients:list:{tenant}:{skip}:{limit}` (TTL ~120s)
- Detail: `patients:detail:{tenant}:{id}` (TTL ~300s)
- Invalidate on create/update/delete:
  - `patients:list:{tenant}:*`
  - `patients:detail:{tenant}:{id}`
  - `dashboard:*`

## Appointments (recommended)
- Lists (optionally partition by status):
  - `appointments:list:{tenant}:{status|all}:{skip}:{limit}` (TTL ~60s)
- Detail:
  - `appointments:detail:{tenant}:{id}` (TTL ~180s)
- Invalidate on create/update/delete/status-change:
  - `appointments:list:{tenant}:*`
  - `appointments:detail:{tenant}:{id}`
  - `dashboard:*`

## Prescriptions (recommended)
- Lists (optionally partition by patient):
  - `prescriptions:list:{tenant}:{patientId|all}:{skip}:{limit}` (TTL ~120s)
- Detail:
  - `prescriptions:detail:{tenant}:{id}` (TTL ~300s)
- Invalidate on create/update/delete:
  - `prescriptions:list:{tenant}:*`
  - `prescriptions:detail:{tenant}:{id}`
  - `dashboard:*`

## Dashboard
- Keys often depend on aggregates; use a simple wildcard pattern like `dashboard:*` and clear it after relevant mutations.

## Utilities
- Use `cache_get`, `cache_set`, and `cache_clear_pattern` from `app/core/cache.py`.
- Prefer short TTLs for highly volatile data (appointments) and longer TTLs for stable data.
- Keep keys deterministic and tenant-prefixed to avoid cross-tenant leaks.

## Gotchas
- Avoid storing PHI directly; cache only serialized, decrypted responses that are safe for the client.
- Keep limit caps (<=100) in list endpoints to bound key cardinality.
