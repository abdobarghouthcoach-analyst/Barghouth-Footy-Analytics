"""add import and event status constraints

Revision ID: 20260701_012
Revises: 20260629_011
Create Date: 2026-07-01 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260701_012"
down_revision: str | None = "20260629_011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE import_jobs SET status = lower(status)")
    op.execute("UPDATE import_jobs SET status = 'created' WHERE status = 'pending'")
    op.execute("UPDATE import_jobs SET status = 'parsing' WHERE status = 'running'")
    op.execute("UPDATE events SET source = lower(source)")
    op.execute("UPDATE events SET provider = lower(provider) WHERE provider IS NOT NULL")

    op.create_check_constraint(
        "ck_import_jobs_status",
        "import_jobs",
        "status IN ('created', 'uploaded', 'extracting', 'parsing', 'normalizing', 'persisting', 'completed', 'failed', 'deleted')",
    )
    op.create_check_constraint("ck_events_source", "events", "source IN ('manual', 'import')")
    op.create_check_constraint("ck_events_provider", "events", "provider IS NULL OR provider IN ('veo', 'other')")


def downgrade() -> None:
    op.drop_constraint("ck_events_provider", "events", type_="check")
    op.drop_constraint("ck_events_source", "events", type_="check")
    op.drop_constraint("ck_import_jobs_status", "import_jobs", type_="check")
