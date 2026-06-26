from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedUUIDModel


class Competition(TimestampedUUIDModel):
    __tablename__ = "competitions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[str] = mapped_column(String(64), nullable=False)
    competition_type: Mapped[str] = mapped_column(String(64), nullable=False)
