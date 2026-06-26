from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.event import EventPeriod, SourceProvider
from app.models.base import TimestampedUUIDModel


class Event(TimestampedUUIDModel):
    __tablename__ = "events"

    match_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    player_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    minute: Mapped[int] = mapped_column(Integer, nullable=False)
    second: Mapped[int] = mapped_column(Integer, nullable=False)
    # Use a safe string length for enum-backed varchar columns (32 chars)
    period: Mapped[EventPeriod] = mapped_column(Enum(EventPeriod, native_enum=False, length=32), nullable=False)
    x_coordinate: Mapped[float | None] = mapped_column(Float, nullable=True)
    y_coordinate: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_provider: Mapped[SourceProvider] = mapped_column(Enum(SourceProvider, native_enum=False, length=32), nullable=False, default=SourceProvider.MANUAL)
    source_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
