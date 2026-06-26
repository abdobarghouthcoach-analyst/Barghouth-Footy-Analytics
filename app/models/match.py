from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.match import MatchStatus
from app.models.base import TimestampedUUIDModel


class Match(TimestampedUUIDModel):
    __tablename__ = "matches"

    competition_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False)
    season_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    home_team_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    away_team_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    kickoff_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    venue: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus, native_enum=False, length=32), nullable=False, default=MatchStatus.SCHEDULED)
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
