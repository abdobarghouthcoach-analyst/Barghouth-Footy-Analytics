from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedUUIDModel


class MatchVideoClip(TimestampedUUIDModel):
    __tablename__ = "match_video_clips"

    match_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    import_job_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=True)
    source_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
