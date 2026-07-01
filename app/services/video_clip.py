from pathlib import Path
from uuid import UUID

from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.match import Match
from app.models.video_clip import MatchVideoClip
from app.schemas.video_clip import MatchVideoClipResponse
from app.video.storage import VideoClipStorage


class VideoClipNotFoundError(ValueError):
    pass


class MatchNotFoundError(ValueError):
    pass


class VideoClipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.storage = VideoClipStorage(Path(settings.video_storage_root))

    async def list_match_clips(self, match_id: UUID) -> list[MatchVideoClipResponse]:
        match = await self.session.get(Match, match_id)
        if match is None:
            raise MatchNotFoundError("Match not found")
        result = await self.session.execute(
            select(MatchVideoClip).where(MatchVideoClip.match_id == match_id).order_by(MatchVideoClip.created_at.asc())
        )
        return [MatchVideoClipResponse.model_validate(clip) for clip in result.scalars().all()]

    async def stream_clip(self, clip_id: UUID) -> FileResponse:
        clip = await self.session.get(MatchVideoClip, clip_id)
        if clip is None:
            raise VideoClipNotFoundError("Video clip not found")
        path = self.storage.resolve_clip_path(clip.storage_path)
        if not path.exists() or not path.is_file():
            raise VideoClipNotFoundError("Video clip file not found")
        return FileResponse(path, media_type=clip.mime_type, filename=clip.original_filename)
