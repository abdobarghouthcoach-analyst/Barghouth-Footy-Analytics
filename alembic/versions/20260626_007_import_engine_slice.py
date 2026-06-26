"""add import engine metadata and event provenance

Revision ID: 20260626_007
Revises: 20260626_006
Create Date: 2026-06-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260626_007"
down_revision = "20260626_006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("import_jobs", sa.Column("original_filename", sa.String(length=255), nullable=True))
    op.add_column("import_jobs", sa.Column("stored_file_path", sa.Text(), nullable=True))
    op.add_column("import_jobs", sa.Column("file_size_bytes", sa.Integer(), nullable=True))
    op.add_column("import_jobs", sa.Column("checksum_sha256", sa.String(length=64), nullable=True))
    op.add_column("import_jobs", sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("import_jobs", sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("import_jobs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE import_jobs SET original_filename = filename WHERE original_filename IS NULL")
    op.alter_column("import_jobs", "original_filename", nullable=False)
    op.alter_column("import_jobs", "filename", nullable=True, existing_type=sa.String(length=255))
    op.alter_column("import_jobs", "status", server_default="created", existing_type=sa.String(length=32))
    op.execute("UPDATE import_jobs SET status = 'created' WHERE status = 'pending'")
    op.execute("UPDATE import_jobs SET status = 'parsing' WHERE status = 'running'")

    op.add_column(
        "events",
        sa.Column("import_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_jobs.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("events", sa.Column("source", sa.String(length=32), nullable=False, server_default="manual"))
    op.add_column("events", sa.Column("provider", sa.String(length=32), nullable=True))
    op.add_column("events", sa.Column("provider_event_id", sa.String(length=128), nullable=True))
    op.alter_column("events", "period", nullable=True, existing_type=sa.String(length=8))


def downgrade() -> None:
    op.execute("UPDATE events SET period = '1H' WHERE period IS NULL")
    op.alter_column("events", "period", nullable=False, existing_type=sa.String(length=8))
    op.drop_column("events", "provider_event_id")
    op.drop_column("events", "provider")
    op.drop_column("events", "source")
    op.drop_column("events", "import_job_id")

    op.execute("UPDATE import_jobs SET status = 'pending' WHERE status = 'created'")
    op.execute("UPDATE import_jobs SET status = 'running' WHERE status IN ('uploaded', 'extracting', 'parsing', 'normalizing', 'persisting')")
    op.alter_column("import_jobs", "status", server_default="pending", existing_type=sa.String(length=32))
    op.alter_column("import_jobs", "filename", nullable=False, existing_type=sa.String(length=255))
    op.drop_column("import_jobs", "completed_at")
    op.drop_column("import_jobs", "summary")
    op.drop_column("import_jobs", "raw_metadata")
    op.drop_column("import_jobs", "checksum_sha256")
    op.drop_column("import_jobs", "file_size_bytes")
    op.drop_column("import_jobs", "stored_file_path")
    op.drop_column("import_jobs", "original_filename")
