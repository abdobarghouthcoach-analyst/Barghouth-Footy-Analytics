from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MatchVideoClipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_id: UUID
    import_job_id: UUID | None = None
    source_provider: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    duration_seconds: int | None = None
    created_at: datetime
    updated_at: datetime
