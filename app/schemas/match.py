from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.match import MatchStatus


class MatchBase(BaseModel):
    competition_id: UUID
    season_id: UUID
    home_team_id: UUID
    away_team_id: UUID
    kickoff_datetime: datetime
    venue: str = Field(..., min_length=1, max_length=128)
    status: MatchStatus = MatchStatus.SCHEDULED
    analyst_notes: str | None = Field(None, max_length=2000)


class MatchCreate(MatchBase):
    pass


class MatchUpdate(BaseModel):
    competition_id: UUID | None = None
    season_id: UUID | None = None
    home_team_id: UUID | None = None
    away_team_id: UUID | None = None
    kickoff_datetime: datetime | None = None
    venue: str | None = Field(None, min_length=1, max_length=128)
    status: MatchStatus | None = None
    analyst_notes: str | None = Field(None, max_length=2000)


class MatchResponse(MatchBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
