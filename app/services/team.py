from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.repositories.team import TeamRepository
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate


class TeamService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = TeamRepository(session)

    async def list_teams(self) -> list[TeamResponse]:
        teams = await self.repository.list()
        return [TeamResponse.from_orm(item) for item in teams]

    async def get_team(self, team_id: UUID) -> TeamResponse | None:
        team = await self.repository.get(team_id)
        return TeamResponse.from_orm(team) if team else None

    async def create_team(self, data: TeamCreate) -> TeamResponse:
        team = Team(
            name=data.name,
            short_name=data.short_name,
            city=data.city,
            country=data.country,
            stadium=data.stadium,
            colours=data.colours,
            badge_url=data.badge_url,
            club_id=data.club_id,
        )
        team = await self.repository.create(team)
        return TeamResponse.from_orm(team)

    async def update_team(self, team_id: UUID, data: TeamUpdate) -> TeamResponse | None:
        team = await self.repository.get(team_id)
        if team is None:
            return None

        if data.name is not None:
            team.name = data.name
        if data.short_name is not None:
            team.short_name = data.short_name
        if data.city is not None:
            team.city = data.city
        if data.country is not None:
            team.country = data.country
        if data.stadium is not None:
            team.stadium = data.stadium
        if data.colours is not None:
            team.colours = data.colours
        if data.badge_url is not None:
            team.badge_url = data.badge_url
        if data.club_id is not None:
            team.club_id = data.club_id

        team = await self.repository.update(team)
        return TeamResponse.from_orm(team)

    async def delete_team(self, team_id: UUID) -> bool:
        team = await self.repository.get(team_id)
        if team is None:
            return False

        await self.repository.delete(team)
        return True
