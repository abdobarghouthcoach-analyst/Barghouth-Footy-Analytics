from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    short_name: str | None = Field(None, min_length=1, max_length=32)
    city: str | None = Field(None, min_length=1, max_length=128)
    country: str | None = Field(None, min_length=1, max_length=128)
    stadium: str | None = Field(None, min_length=1, max_length=128)
    colours: str | None = Field(None, min_length=1, max_length=128)
    badge_url: HttpUrl | None = None
    club_id: UUID | None = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    short_name: str | None = Field(None, min_length=1, max_length=32)
    city: str | None = Field(None, min_length=1, max_length=128)
    country: str | None = Field(None, min_length=1, max_length=128)
    stadium: str | None = Field(None, min_length=1, max_length=128)
    colours: str | None = Field(None, min_length=1, max_length=128)
    badge_url: HttpUrl | None = None
    club_id: UUID | None = None


class TeamResponse(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
