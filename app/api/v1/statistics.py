from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.domain.football.statistics import StatisticName, StatisticScope
from app.schemas.statistics import (
    MatchStatisticsResponse,
    PlayerStatisticsResponse,
    StatisticExplanationResponse,
    TeamStatisticsResponse,
)
from app.services.statistics import (
    MatchNotFoundError,
    StatisticExplanationNotFoundError,
    StatisticsService,
)

router = APIRouter(prefix="/matches/{match_id}/statistics", tags=["Statistics"])


async def get_service(session: AsyncSession = Depends(get_db_session)) -> StatisticsService:
    return StatisticsService(session)


@router.get("", response_model=MatchStatisticsResponse)
async def get_match_statistics(
    match_id: UUID,
    service: StatisticsService = Depends(get_service),
) -> MatchStatisticsResponse:
    try:
        return await service.get_match_statistics(match_id)
    except MatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/teams", response_model=TeamStatisticsResponse)
async def get_team_statistics(
    match_id: UUID,
    service: StatisticsService = Depends(get_service),
) -> TeamStatisticsResponse:
    try:
        return await service.get_team_statistics(match_id)
    except MatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/players", response_model=PlayerStatisticsResponse)
async def get_player_statistics(
    match_id: UUID,
    service: StatisticsService = Depends(get_service),
) -> PlayerStatisticsResponse:
    try:
        return await service.get_player_statistics(match_id)
    except MatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/explain", response_model=StatisticExplanationResponse)
async def explain_statistic(
    match_id: UUID,
    scope: StatisticScope = Query(...),
    name: StatisticName = Query(...),
    team_id: str | None = Query(None),
    player_id: str | None = Query(None),
    service: StatisticsService = Depends(get_service),
) -> StatisticExplanationResponse:
    try:
        return await service.explain_statistic(
            match_id=match_id,
            scope=scope,
            name=name,
            team_id=team_id,
            player_id=player_id,
        )
    except (MatchNotFoundError, StatisticExplanationNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
