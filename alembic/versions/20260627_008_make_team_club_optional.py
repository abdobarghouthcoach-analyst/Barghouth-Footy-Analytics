"""make team club optional

Revision ID: 20260627_008
Revises: 20260626_007
Create Date: 2026-06-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260627_008"
down_revision: str | None = "20260626_007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "teams",
        "club_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(sa.text("UPDATE teams SET club_id = '00000000-0000-0000-0000-000000000000' WHERE club_id IS NULL"))
    op.alter_column(
        "teams",
        "club_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
