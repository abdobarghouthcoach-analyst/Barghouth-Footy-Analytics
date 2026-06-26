from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedUUIDModel
from app.models.competition import Competition


class Season(TimestampedUUIDModel):
    __tablename__ = "seasons"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    competition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    competition: Mapped[Competition] = relationship("Competition", backref="seasons")
