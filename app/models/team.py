from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedUUIDModel


class Team(TimestampedUUIDModel):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str] = mapped_column(String(32), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    country: Mapped[str] = mapped_column(String(128), nullable=False)
    stadium: Mapped[str] = mapped_column(String(128), nullable=False)
    colours: Mapped[str] = mapped_column(String(128), nullable=False)
    badge_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    club_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Future relationships:
    # matches: Mapped[list[Match]] = relationship("Match", secondary="match_teams", back_populates="teams")
