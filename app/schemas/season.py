from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeasonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    start_date: date
    end_date: date
    competition_id: UUID
    is_active: bool = Field(default=False)


class SeasonCreate(SeasonBase):
    pass


class SeasonUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    start_date: date | None = None
    end_date: date | None = None
    competition_id: UUID | None = None
    is_active: bool | None = None


class SeasonResponse(SeasonBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
