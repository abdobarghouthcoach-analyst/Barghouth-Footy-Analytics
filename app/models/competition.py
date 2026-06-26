from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.competition import CompetitionLevel, CompetitionType
from app.models.base import TimestampedUUIDModel


class Competition(TimestampedUUIDModel):
    __tablename__ = "competitions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[CompetitionLevel] = mapped_column(
        Enum(CompetitionLevel, native_enum=False, length=64), nullable=False
    )
    competition_type: Mapped[CompetitionType] = mapped_column(
        Enum(CompetitionType, native_enum=False, length=64), nullable=False
    )
