from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate
from app.services.team import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])


async def get_service(session: AsyncSession = Depends(get_db_session)) -> TeamService:
    return TeamService(session)


@router.get("/", response_model=list[TeamResponse])
async def list_teams(service: TeamService = Depends(get_service)) -> list[TeamResponse]:
    return await service.list_teams()


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    service: TeamService = Depends(get_service),
) -> TeamResponse:
    return await service.create_team(data)


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    service: TeamService = Depends(get_service),
) -> TeamResponse:
    team = await service.get_team(team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    data: TeamUpdate,
    service: TeamService = Depends(get_service),
) -> TeamResponse:
    team = await service.update_team(team_id, data)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    service: TeamService = Depends(get_service),
) -> None:
    success = await service.delete_team(team_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return None
