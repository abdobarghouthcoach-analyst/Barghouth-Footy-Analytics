from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.import_job import ImportProvider, ImportStatus
from app.models.base import TimestampedUUIDModel


class ImportJob(TimestampedUUIDModel):
    __tablename__ = "import_jobs"

    match_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[ImportProvider] = mapped_column(Enum(ImportProvider, native_enum=False, length=32), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(Enum(ImportStatus, native_enum=False, length=32), nullable=False, default=ImportStatus.PENDING)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_events_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warnings_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
