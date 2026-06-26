"""create events table

Revision ID: 20260626_005
Revises: 20260626_004
Create Date: 2026-06-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260626_005"
down_revision = "20260626_004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("minute", sa.Integer(), nullable=False),
        sa.Column("second", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(length=8), nullable=False),
        sa.Column("x_coordinate", sa.Float(), nullable=True),
        sa.Column("y_coordinate", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_provider", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("source_event_id", sa.String(length=128), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("events")
