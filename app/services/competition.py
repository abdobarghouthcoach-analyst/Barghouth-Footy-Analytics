from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competition import Competition
from app.repositories.competition import CompetitionRepository
from app.schemas.competition import CompetitionCreate, CompetitionResponse, CompetitionUpdate


class CompetitionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = CompetitionRepository(session)

    async def list_competitions(self) -> list[CompetitionResponse]:
        competitions = await self.repository.list()
        return [CompetitionResponse.from_orm(item) for item in competitions]

    async def get_competition(self, competition_id: UUID) -> CompetitionResponse | None:
        competition = await self.repository.get(competition_id)
        return CompetitionResponse.from_orm(competition) if competition else None

    async def create_competition(self, data: CompetitionCreate) -> CompetitionResponse:
        competition = Competition(
            name=data.name,
            country=data.country,
            level=data.level,
            competition_type=data.competition_type,
        )
        competition = await self.repository.create(competition)
        return CompetitionResponse.from_orm(competition)

    async def update_competition(
        self,
        competition_id: UUID,
        data: CompetitionUpdate,
    ) -> CompetitionResponse | None:
        competition = await self.repository.get(competition_id)
        if competition is None:
            return None

        if data.name is not None:
            competition.name = data.name
        if data.country is not None:
            competition.country = data.country
        if data.level is not None:
            competition.level = data.level
        if data.competition_type is not None:
            competition.competition_type = data.competition_type

        competition = await self.repository.update(competition)
        return CompetitionResponse.from_orm(competition)

    async def delete_competition(self, competition_id: UUID) -> bool:
        competition = await self.repository.get(competition_id)
        if competition is None:
            return False

        await self.repository.delete(competition)
        return True
