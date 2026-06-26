from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.season import Season
from app.repositories.season import SeasonRepository
from app.schemas.season import SeasonCreate, SeasonResponse, SeasonUpdate


class SeasonService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = SeasonRepository(session)

    async def list_seasons(self) -> list[SeasonResponse]:
        seasons = await self.repository.list()
        return [SeasonResponse.model_validate(item) for item in seasons]

    async def get_season(self, season_id: UUID) -> SeasonResponse | None:
        season = await self.repository.get(season_id)
        return SeasonResponse.model_validate(season) if season else None

    async def create_season(self, data: SeasonCreate) -> SeasonResponse:
        if data.start_date >= data.end_date:
            raise ValueError("start_date must be before end_date")

        season = Season(
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            competition_id=data.competition_id,
            is_active=data.is_active,
        )
        season = await self.repository.create(season)
        return SeasonResponse.model_validate(season)

    async def update_season(self, season_id: UUID, data: SeasonUpdate) -> SeasonResponse | None:
        season = await self.repository.get(season_id)
        if season is None:
            return None

        if data.name is not None:
            season.name = data.name
        if data.start_date is not None:
            season.start_date = data.start_date
        if data.end_date is not None:
            season.end_date = data.end_date
        if data.competition_id is not None:
            season.competition_id = data.competition_id
        if data.is_active is not None:
            season.is_active = data.is_active

        if season.start_date >= season.end_date:
            raise ValueError("start_date must be before end_date")

        season = await self.repository.update(season)
        return SeasonResponse.model_validate(season)

    async def delete_season(self, season_id: UUID) -> bool:
        season = await self.repository.get(season_id)
        if season is None:
            return False

        await self.repository.delete(season)
        return True
