"""add event review workflow fields

Revision ID: 20260701_014
Revises: 20260701_013
Create Date: 2026-07-01 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260701_014"
down_revision: str | None = "20260701_013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("events", sa.Column("is_reviewed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("events", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("events", sa.Column("reviewed_by", sa.String(length=128), nullable=True))
    op.add_column("events", sa.Column("confidence", sa.String(length=32), nullable=True))
    op.create_check_constraint(
        "ck_events_confidence",
        "events",
        "confidence IS NULL OR confidence IN ('high', 'medium', 'low', 'unknown')",
    )
    op.alter_column("events", "is_reviewed", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_events_confidence", "events", type_="check")
    op.drop_column("events", "confidence")
    op.drop_column("events", "reviewed_by")
    op.drop_column("events", "reviewed_at")
    op.drop_column("events", "is_reviewed")
