from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.competition import CompetitionLevel, CompetitionType


class CompetitionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    country: str = Field(..., min_length=1, max_length=128)
    level: CompetitionLevel
    competition_type: CompetitionType


class CompetitionCreate(CompetitionBase):
    pass


class CompetitionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    country: str | None = Field(None, min_length=1, max_length=128)
    level: CompetitionLevel | None = None
    competition_type: CompetitionType | None = None


class CompetitionResponse(CompetitionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
