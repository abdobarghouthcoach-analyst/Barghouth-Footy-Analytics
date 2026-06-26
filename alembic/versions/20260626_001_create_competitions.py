"""create competitions table

Revision ID: 20260626_001
Revises: None
Create Date: 2026-06-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260626_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "competitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=128), nullable=False),
        sa.Column(
            "level",
            sa.Enum(
                "first",
                "second",
                "youth",
                name="competitionlevel",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.Column(
            "competition_type",
            sa.Enum(
                "league",
                "cup",
                "international",
                name="competitiontype",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("competitions")
