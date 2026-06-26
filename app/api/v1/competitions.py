from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.competition import CompetitionCreate, CompetitionResponse, CompetitionUpdate
from app.services.competition import CompetitionService

router = APIRouter(prefix="/competitions", tags=["Competitions"])


async def get_service(session: AsyncSession = Depends(get_db_session)) -> CompetitionService:
    return CompetitionService(session)


@router.get("/", response_model=list[CompetitionResponse])
async def list_competitions(service: CompetitionService = Depends(get_service)) -> list[CompetitionResponse]:
    return await service.list_competitions()


@router.post("/", response_model=CompetitionResponse, status_code=status.HTTP_201_CREATED)
async def create_competition(
    data: CompetitionCreate,
    service: CompetitionService = Depends(get_service),
) -> CompetitionResponse:
    return await service.create_competition(data)


@router.get("/{competition_id}", response_model=CompetitionResponse)
async def get_competition(
    competition_id: UUID,
    service: CompetitionService = Depends(get_service),
) -> CompetitionResponse:
    competition = await service.get_competition(competition_id)
    if competition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found")
    return competition


@router.patch("/{competition_id}", response_model=CompetitionResponse)
async def update_competition(
    competition_id: UUID,
    data: CompetitionUpdate,
    service: CompetitionService = Depends(get_service),
) -> CompetitionResponse:
    competition = await service.update_competition(competition_id, data)
    if competition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found")
    return competition


@router.delete("/{competition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competition(
    competition_id: UUID,
    service: CompetitionService = Depends(get_service),
) -> None:
    success = await service.delete_competition(competition_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found")
    return None
