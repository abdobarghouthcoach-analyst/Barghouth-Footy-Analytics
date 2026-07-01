"""create match video clips

Revision ID: 20260701_013
Revises: 20260701_012
Create Date: 2026-07-01 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260701_013"
down_revision: str | None = "20260701_012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "match_video_clips",
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_provider", sa.String(length=32), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["import_job_id"], ["import_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_match_video_clips_match_id", "match_video_clips", ["match_id"])
    op.create_index("ix_match_video_clips_import_job_id", "match_video_clips", ["import_job_id"])
    op.add_column("events", sa.Column("video_clip_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_events_video_clip_id_match_video_clips",
        "events",
        "match_video_clips",
        ["video_clip_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_events_video_clip_id_match_video_clips", "events", type_="foreignkey")
    op.drop_column("events", "video_clip_id")
    op.drop_index("ix_match_video_clips_import_job_id", table_name="match_video_clips")
    op.drop_index("ix_match_video_clips_match_id", table_name="match_video_clips")
    op.drop_table("match_video_clips")
