from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.match import MatchCreate, MatchResponse, MatchUpdate
from app.services.match import MatchService

router = APIRouter(prefix="/matches", tags=["Matches"])


async def get_service(session: AsyncSession = Depends(get_db_session)) -> MatchService:
    return MatchService(session)


@router.get("/", response_model=list[MatchResponse])
async def list_matches(service: MatchService = Depends(get_service)) -> list[MatchResponse]:
    return await service.list_matches()


@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    data: MatchCreate,
    service: MatchService = Depends(get_service),
) -> MatchResponse:
    try:
        return await service.create_match(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: UUID,
    service: MatchService = Depends(get_service),
) -> MatchResponse:
    match = await service.get_match(match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


@router.patch("/{match_id}", response_model=MatchResponse)
async def update_match(
    match_id: UUID,
    data: MatchUpdate,
    service: MatchService = Depends(get_service),
) -> MatchResponse:
    try:
        match = await service.update_match(match_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_match(
    match_id: UUID,
    service: MatchService = Depends(get_service),
) -> None:
    success = await service.delete_match(match_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return None
