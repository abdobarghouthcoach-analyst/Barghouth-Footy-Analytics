from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.event import EventPeriod, EventProvider, EventSource, SourceProvider


class EventBase(BaseModel):
    match_id: UUID
    team_id: UUID | None = None
    player_id: UUID | None = None
    event_type: str = Field(..., min_length=1, max_length=64)
    minute: int = Field(..., ge=0)
    second: int = Field(..., ge=0, le=59)
    period: EventPeriod | None = None
    x_coordinate: float | None = Field(None, ge=0.0, le=1.0)
    y_coordinate: float | None = Field(None, ge=0.0, le=1.0)
    notes: str | None = Field(None, max_length=2000)
    tags: dict | None = None
    source_provider: SourceProvider = SourceProvider.MANUAL
    source_event_id: str | None = Field(None, max_length=128)
    import_job_id: UUID | None = None
    video_clip_id: UUID | None = None
    source: EventSource = EventSource.MANUAL
    provider: EventProvider | None = None
    provider_event_id: str | None = Field(None, max_length=128)
    raw_payload: dict | None = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    team_id: UUID | None = None
    event_type: str | None = Field(None, min_length=1, max_length=64)
    minute: int | None = Field(None, ge=0)
    second: int | None = Field(None, ge=0, le=59)
    notes: str | None = Field(None, max_length=2000)


class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    edited_at: datetime | None = None
