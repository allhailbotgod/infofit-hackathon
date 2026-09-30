"""Create the initial service marketplace schema.

Revision ID: 20260930_01
Revises:
Create Date: 2026-09-30
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260930_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


user_role = postgresql.ENUM(
    "CUSTOMER", "PROVIDER", "ADMIN", name="user_role", create_type=False
)
verification_status = postgresql.ENUM(
    "PENDING", "VERIFIED", "REJECTED", name="verification_status", create_type=False
)
service_request_status = postgresql.ENUM(
    "PENDING",
    "ACCEPTED",
    "REJECTED",
    "COMPLETED",
    "CANCELLED",
    name="service_request_status",
    create_type=False,
)


def upgrade() -> None:
    """Create the application tables, constraints, indexes, and enum types."""
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    verification_status.create(bind, checkfirst=True)
    service_request_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "service_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "provider_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("bio", sa.String(length=1000), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=120), nullable=False),
        sa.Column("area", sa.String(length=120), nullable=False),
        sa.Column("verification_status", verification_status, nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "provider_availability",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.Column("day_of_week", sa.String(length=20), nullable=False),
        sa.Column("start_time", sa.String(length=20), nullable=False),
        sa.Column("end_time", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], ["provider_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "provider_services",
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.Column("service_category_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], ["provider_profiles.id"]),
        sa.ForeignKeyConstraint(["service_category_id"], ["service_categories.id"]),
        sa.PrimaryKeyConstraint("provider_id", "service_category_id"),
    )

    op.create_table(
        "service_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.Column("service_category_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("requested_date", sa.Date(), nullable=False),
        sa.Column("requested_time", sa.String(length=20), nullable=False),
        sa.Column("status", service_request_status, nullable=False),
        sa.Column("provider_response", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["provider_profiles.id"]),
        sa.ForeignKeyConstraint(["service_category_id"], ["service_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.Column("service_request_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["provider_profiles.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_request_id"),
    )


def downgrade() -> None:
    """Remove the initial schema in dependency order."""
    op.drop_table("reviews")
    op.drop_table("service_requests")
    op.drop_table("provider_services")
    op.drop_table("provider_availability")
    op.drop_table("provider_profiles")
    op.drop_table("service_categories")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    service_request_status.drop(bind, checkfirst=True)
    verification_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
