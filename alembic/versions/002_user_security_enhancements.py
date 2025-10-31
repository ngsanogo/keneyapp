"""User security enhancements

Revision ID: 002
Revises: 001
Create Date: 2025-10-29

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "users" not in inspector.get_table_names():
        # Fresh databases will pick up the latest model definition via create_all().
        return

    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.add_column("users", sa.Column("last_login", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users",
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "mfa_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column("users", sa.Column("mfa_secret", sa.String(), nullable=True))

    op.execute("UPDATE users SET password_changed_at = NOW()")

    op.create_index(op.f("ix_users_mfa_enabled"), "users", ["mfa_enabled"], unique=False)
    op.create_index(op.f("ix_users_is_locked"), "users", ["is_locked"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "users" not in inspector.get_table_names():
        return

    op.drop_index(op.f("ix_users_is_locked"), table_name="users")
    op.drop_index(op.f("ix_users_mfa_enabled"), table_name="users")
    op.drop_column("users", "mfa_secret")
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "is_locked")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("users", "password_changed_at")
    op.drop_column("users", "last_login")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "created_at")
