from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.import_job import ImportProvider, ImportStatus


class ImportJobBase(BaseModel):
    match_id: UUID
    provider: ImportProvider
    filename: str = Field(..., min_length=1, max_length=255)


class ImportJobCreate(ImportJobBase):
    pass


class ImportJobUpdate(BaseModel):
    status: ImportStatus | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    imported_events_count: int | None = None
    warnings_count: int | None = None
    error_message: str | None = Field(None, max_length=2000)


class ImportJobResponse(ImportJobBase):
    id: UUID
    status: ImportStatus
    started_at: datetime | None
    finished_at: datetime | None
    imported_events_count: int
    warnings_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
