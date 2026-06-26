from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.season import SeasonCreate, SeasonResponse, SeasonUpdate
from app.services.season import SeasonService

router = APIRouter(prefix="/seasons", tags=["Seasons"])


async def get_service(session: AsyncSession = Depends(get_db_session)) -> SeasonService:
    return SeasonService(session)


@router.get("/", response_model=list[SeasonResponse])
async def list_seasons(service: SeasonService = Depends(get_service)) -> list[SeasonResponse]:
    return await service.list_seasons()


@router.post("/", response_model=SeasonResponse, status_code=status.HTTP_201_CREATED)
async def create_season(
    data: SeasonCreate,
    service: SeasonService = Depends(get_service),
) -> SeasonResponse:
    try:
        return await service.create_season(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{season_id}", response_model=SeasonResponse)
async def get_season(
    season_id: UUID,
    service: SeasonService = Depends(get_service),
) -> SeasonResponse:
    season = await service.get_season(season_id)
    if season is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Season not found")
    return season


@router.patch("/{season_id}", response_model=SeasonResponse)
async def update_season(
    season_id: UUID,
    data: SeasonUpdate,
    service: SeasonService = Depends(get_service),
) -> SeasonResponse:
    try:
        season = await service.update_season(season_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if season is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Season not found")
    return season


@router.delete("/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_season(
    season_id: UUID,
    service: SeasonService = Depends(get_service),
) -> None:
    success = await service.delete_season(season_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Season not found")
    return None
