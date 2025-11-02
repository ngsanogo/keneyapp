# GraphQL Extension Guide

Follow this pattern to extend the GraphQL API while preserving tenancy, RBAC, audit, and PHI guarantees.

## Where to work
- Schema and router live in `app/graphql/schema.py`.
- The FastAPI router is created via `create_graphql_router()` and mounted in `app/main.py` at `/graphql`.

## Core patterns to keep
- Context auth: Tokens are decoded in `_get_graphql_context`, which resolves `GraphQLUserContext` with `tenant_id` and `role`.
- Tenancy: Always filter by `info.context.user.tenant_id` in queries.
- RBAC: Use `ensure_roles(info, [...])` to guard resolvers.
- Sessions: Use `with get_session(info) as session:` to scope SQLAlchemy sessions.
- PHI: For patient-like data, serialize via `serialize_patient_model` to decrypt before returning.
- Audit: For mutations, call `log_audit_event(...)` with `request=info.context.request`.

## Example: add a query field
```python
@strawberry.type
class Query:
    # ...existing fields

    @strawberry.field
    def myResources(self, info: Info, limit: int = 25, offset: int = 0) -> list[MyResourceType]:
        ensure_roles(info, [UserRole.ADMIN, UserRole.DOCTOR])
        limit = max(1, min(limit, 100))
        with get_session(info) as session:
            rows = (session.query(MyResource)
                    .filter(MyResource.tenant_id == info.context.user.tenant_id)
                    .order_by(MyResource.created_at.desc())
                    .offset(max(0, offset)).limit(limit).all())
            return [to_my_resource_type(r) for r in rows]
```

## Example: add a mutation
```python
@strawberry.type
class Mutation:
    # ...existing mutations

    @strawberry.mutation
    def createMyResource(self, info: Info, name: str, description: str | None = None) -> MyResourceType:
        ensure_roles(info, [UserRole.ADMIN])
        with get_session(info) as session:
            entity = MyResource(tenant_id=info.context.user.tenant_id, name=name, description=description)
            session.add(entity); session.commit(); session.refresh(entity)

            log_audit_event(
                db=session,
                action="CREATE",
                resource_type="my_resource",
                resource_id=entity.id,
                status="success",
                user_id=info.context.user.id,
                username=info.context.user.username,
                details={"operation": "graphql_create"},
                request=info.context.request,
            )
            return to_my_resource_type(entity)
```

## Type mappers
- Mirror existing mappers like `to_patient_type`, `to_appointment_type`.
- If returning PHI, use decrypt/serialize helpers (see `serialize_patient_model`).

## Error handling
- Use `GraphQLError("message")` for client-facing errors.
- 401/403 cases are handled centrally in `_get_graphql_context`.

## Testing
- Use `POST /graphql` with a bearer token.
- Validate RBAC by trying with roles outside `ensure_roles`.
- Keep limits `<= 100` and offset `>= 0` as in existing resolvers.
