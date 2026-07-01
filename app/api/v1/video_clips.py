from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.video_clip import MatchVideoClipResponse
from app.services.video_clip import MatchNotFoundError, VideoClipNotFoundError, VideoClipService

router = APIRouter(tags=["Video Clips"])


async def get_service(session: AsyncSession = Depends(get_db_session)) -> VideoClipService:
    return VideoClipService(session)


@router.get("/matches/{match_id}/video-clips", response_model=list[MatchVideoClipResponse])
async def list_match_video_clips(
    match_id: UUID,
    service: VideoClipService = Depends(get_service),
) -> list[MatchVideoClipResponse]:
    try:
        return await service.list_match_clips(match_id)
    except MatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/video-clips/{clip_id}/stream", response_class=FileResponse)
async def stream_video_clip(
    clip_id: UUID,
    service: VideoClipService = Depends(get_service),
) -> FileResponse:
    try:
        return await service.stream_clip(clip_id)
    except (VideoClipNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
