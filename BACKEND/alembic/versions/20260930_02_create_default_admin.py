"""Create the initial administrator account.

Revision ID: 20260930_02
Revises: 20260930_01
Create Date: 2026-09-30
"""

from collections.abc import Sequence
import uuid

from alembic import op
from pwdlib import PasswordHash
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260930_02"
down_revision: str | None = "20260930_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ADMIN_ID = uuid.UUID("58fadb72-7a51-4ae6-919f-23ea6a7c8f40")
ADMIN_EMAIL = "jayrad200@gmail.com"

users = sa.table(
    "users",
    sa.column("id", sa.Uuid()),
    sa.column("name", sa.String()),
    sa.column("email", sa.String()),
    sa.column("phone", sa.String()),
    sa.column("password_hash", sa.String()),
    sa.column(
        "role",
        postgresql.ENUM(
            "CUSTOMER", "PROVIDER", "ADMIN", name="user_role", create_type=False
        ),
    ),
)


def upgrade() -> None:
    """Insert the default administrator once, without storing a plain password."""
    bind = op.get_bind()
    existing_admin = bind.execute(
        sa.select(users.c.id).where(users.c.email == ADMIN_EMAIL)
    ).scalar_one_or_none()
    if existing_admin is None:
        bind.execute(
            sa.insert(users).values(
                id=ADMIN_ID,
                name="Developer Gerald",
                email=ADMIN_EMAIL,
                phone="+2348000000000",
                password_hash=PasswordHash.recommended().hash("allhailbotgod"),
                role="ADMIN",
            )
        )


def downgrade() -> None:
    """Remove only the administrator inserted by this migration."""
    op.execute(sa.delete(users).where(users.c.id == ADMIN_ID))
