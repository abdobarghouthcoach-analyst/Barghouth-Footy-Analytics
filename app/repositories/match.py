from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import Match
from app.models.team import Team


class MatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> List[Match]:
        result = await self.session.execute(select(Match))
        return result.scalars().all()

    async def list_with_team_names(self) -> List[tuple[Match, str | None, str | None]]:
        home_team = aliased(Team)
        away_team = aliased(Team)
        result = await self.session.execute(
            select(Match, home_team.name, away_team.name)
            .outerjoin(home_team, Match.home_team_id == home_team.id)
            .outerjoin(away_team, Match.away_team_id == away_team.id)
        )
        return list(result.all())

    async def get(self, match_id: UUID) -> Match | None:
        return await self.session.get(Match, match_id)

    async def get_with_team_names(self, match_id: UUID) -> tuple[Match, str | None, str | None] | None:
        home_team = aliased(Team)
        away_team = aliased(Team)
        result = await self.session.execute(
            select(Match, home_team.name, away_team.name)
            .outerjoin(home_team, Match.home_team_id == home_team.id)
            .outerjoin(away_team, Match.away_team_id == away_team.id)
            .where(Match.id == match_id)
        )
        row = result.one_or_none()
        return row if row is None else (row[0], row[1], row[2])

    async def create(self, match: Match) -> Match:
        self.session.add(match)
        await self.session.commit()
        await self.session.refresh(match)
        return match

    async def update(self, match: Match) -> Match:
        await self.session.commit()
        await self.session.refresh(match)
        return match

    async def delete(self, match: Match) -> None:
        await self.session.delete(match)
        await self.session.commit()
