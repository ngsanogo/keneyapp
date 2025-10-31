"""Introduce tenants and tenant modules with entity scoping

Revision ID: 003
Revises: 002
Create Date: 2025-11-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text, select
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Create tenants table
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("contact_email", sa.String(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("default_timezone", sa.String(), nullable=True, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "configuration",
            postgresql.JSONB(astext_type=sa.Text()) if bind.dialect.name == "postgresql" else sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb") if bind.dialect.name == "postgresql" else sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("name", name="uq_tenants_name"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )
    op.create_index(op.f("ix_tenants_id"), "tenants", ["id"], unique=False)
    op.create_index(op.f("ix_tenants_slug"), "tenants", ["slug"], unique=False)

    # Create tenant_modules table
    op.create_table(
        "tenant_modules",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("module_key", sa.String(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "configuration",
            postgresql.JSONB(astext_type=sa.Text()) if bind.dialect.name == "postgresql" else sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb") if bind.dialect.name == "postgresql" else sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "module_key", name="uq_tenant_module"),
    )
    op.create_index(
        op.f("ix_tenant_modules_tenant_id"), "tenant_modules", ["tenant_id"], unique=False
    )

    # Extend user roles enum with super_admin when using PostgreSQL
    if bind.dialect.name == "postgresql":
        enum_exists = bind.execute(
            text("SELECT 1 FROM pg_type WHERE typname = 'userrole'")
        ).scalar() is not None
        if enum_exists:
            op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'super_admin'")

    # Add tenant_id columns to existing tables (only when they already exist)
    if "users" in existing_tables:
        op.add_column(
            "users",
            sa.Column("tenant_id", sa.Integer(), nullable=True),
        )
        op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"], unique=False)
    if "patients" in existing_tables:
        op.add_column(
            "patients",
            sa.Column("tenant_id", sa.Integer(), nullable=True),
        )
        op.create_index(op.f("ix_patients_tenant_id"), "patients", ["tenant_id"], unique=False)
    if "appointments" in existing_tables:
        op.add_column(
            "appointments",
            sa.Column("tenant_id", sa.Integer(), nullable=True),
        )
        op.create_index(
            op.f("ix_appointments_tenant_id"), "appointments", ["tenant_id"], unique=False
        )
    if "prescriptions" in existing_tables:
        op.add_column(
            "prescriptions",
            sa.Column("tenant_id", sa.Integer(), nullable=True),
        )
        op.create_index(
            op.f("ix_prescriptions_tenant_id"), "prescriptions", ["tenant_id"], unique=False
        )

    # Backfill tenant data with a default tenant
    tenants_table = sa.table(
        "tenants",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("contact_email", sa.String()),
        sa.column("region", sa.String()),
        sa.column("default_timezone", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("configuration", sa.JSON()),
    )
    insert_stmt = tenants_table.insert().values(
        name="Default Tenant",
        slug="default",
        contact_email=None,
        region=None,
        default_timezone="UTC",
        is_active=True,
        configuration={},
    )
    result = bind.execute(insert_stmt)

    if result.inserted_primary_key:
        default_tenant_id = result.inserted_primary_key[0]
    else:
        default_tenant_id = bind.execute(
            select(tenants_table.c.id).where(tenants_table.c.slug == "default")
        ).scalar_one()

    for table_name in ("users", "patients", "appointments", "prescriptions"):
        if table_name not in existing_tables:
            continue
        bind.execute(
            sa.text(f"UPDATE {table_name} SET tenant_id = :tenant_id WHERE tenant_id IS NULL"),
            {"tenant_id": default_tenant_id},
        )

    # Enforce non-null tenant_id and add foreign keys
    if "users" in existing_tables:
        op.alter_column("users", "tenant_id", nullable=False)
        op.create_foreign_key(
            "fk_users_tenant_id",
            source_table="users",
            referent_table="tenants",
            local_cols=["tenant_id"],
            remote_cols=["id"],
            ondelete="RESTRICT",
        )

    if "patients" in existing_tables:
        if bind.dialect.name == "postgresql":
            op.drop_constraint("patients_email_key", "patients", type_="unique")
        else:  # pragma: no cover - non-Postgres dialects handled best-effort
            try:
                op.drop_constraint("patients_email_key", "patients", type_="unique")
            except Exception:
                pass

        op.alter_column("patients", "tenant_id", nullable=False)
        op.create_foreign_key(
            "fk_patients_tenant_id",
            source_table="patients",
            referent_table="tenants",
            local_cols=["tenant_id"],
            remote_cols=["id"],
            ondelete="CASCADE",
        )

        op.create_unique_constraint(
            "uq_patients_tenant_email",
            "patients",
            ["tenant_id", "email"],
        )

    if "appointments" in existing_tables:
        op.alter_column("appointments", "tenant_id", nullable=False)
        op.create_foreign_key(
            "fk_appointments_tenant_id",
            source_table="appointments",
            referent_table="tenants",
            local_cols=["tenant_id"],
            remote_cols=["id"],
            ondelete="CASCADE",
        )

    if "prescriptions" in existing_tables:
        op.alter_column("prescriptions", "tenant_id", nullable=False)
        op.create_foreign_key(
            "fk_prescriptions_tenant_id",
            source_table="prescriptions",
            referent_table="tenants",
            local_cols=["tenant_id"],
            remote_cols=["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Drop foreign keys and tenant columns
    if "prescriptions" in existing_tables:
        op.drop_constraint("fk_prescriptions_tenant_id", "prescriptions", type_="foreignkey")
        op.drop_index(op.f("ix_prescriptions_tenant_id"), table_name="prescriptions")
        op.drop_column("prescriptions", "tenant_id")

    if "appointments" in existing_tables:
        op.drop_constraint("fk_appointments_tenant_id", "appointments", type_="foreignkey")
        op.drop_index(op.f("ix_appointments_tenant_id"), table_name="appointments")
        op.drop_column("appointments", "tenant_id")

    if "patients" in existing_tables:
        op.drop_constraint("fk_patients_tenant_id", "patients", type_="foreignkey")
        op.drop_index(op.f("ix_patients_tenant_id"), table_name="patients")
        op.drop_column("patients", "tenant_id")

    if "users" in existing_tables:
        op.drop_constraint("fk_users_tenant_id", "users", type_="foreignkey")
        op.drop_index(op.f("ix_users_tenant_id"), table_name="users")
        op.drop_column("users", "tenant_id")

    # Drop tenant modules and tenants tables
    op.drop_index(op.f("ix_tenant_modules_tenant_id"), table_name="tenant_modules")
    op.drop_table("tenant_modules")
    op.drop_index(op.f("ix_tenants_slug"), table_name="tenants")
    op.drop_index(op.f("ix_tenants_id"), table_name="tenants")
    op.drop_table("tenants")

    # PostgreSQL enum rollback - removing a value requires recreating the type, skipping automatic downgrade.
