from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field

from app.domain.import_job import ImportProvider, ImportStatus


class ImportJobBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    match_id: UUID
    provider: ImportProvider
    original_filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("original_filename", "filename"),
    )


class ImportJobCreate(ImportJobBase):
    stored_file_path: str | None = None
    file_size_bytes: int | None = None
    checksum_sha256: str | None = Field(None, max_length=64)
    raw_metadata: dict[str, Any] | None = None
    summary: dict[str, Any] | None = None


class ImportJobUpdate(BaseModel):
    status: ImportStatus | None = None
    original_filename: str | None = Field(None, min_length=1, max_length=255)
    stored_file_path: str | None = None
    file_size_bytes: int | None = None
    checksum_sha256: str | None = Field(None, max_length=64)
    raw_metadata: dict[str, Any] | None = None
    summary: dict[str, Any] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    completed_at: datetime | None = None
    imported_events_count: int | None = None
    warnings_count: int | None = None
    error_message: str | None = Field(None, max_length=2000)


class ImportJobResponse(ImportJobBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    status: ImportStatus
    stored_file_path: str | None
    file_size_bytes: int | None
    checksum_sha256: str | None
    raw_metadata: dict[str, Any] | None
    summary: dict[str, Any] | None
    started_at: datetime | None
    finished_at: datetime | None
    completed_at: datetime | None
    imported_events_count: int
    warnings_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def filename(self) -> str:
        return self.original_filename
