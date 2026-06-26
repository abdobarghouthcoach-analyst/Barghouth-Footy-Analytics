"""create matches table

Revision ID: 20260626_004
Revises: 20260626_003
Create Date: 2026-06-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260626_004"
down_revision = "20260626_003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("competition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("season_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("home_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("away_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kickoff_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("venue", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "scheduled",
                "live",
                "finished",
                "cancelled",
                "postponed",
                name="matchstatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("analyst_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("matches")
