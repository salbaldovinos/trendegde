"""Add display_name, avatar_url, timezone columns to users table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "timezone",
            sa.Text(),
            server_default=sa.text("'America/New_York'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "timezone")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "display_name")
