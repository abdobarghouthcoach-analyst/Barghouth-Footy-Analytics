from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team


class TeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> List[Team]:
        result = await self.session.execute(select(Team))
        return result.scalars().all()

    async def get(self, team_id: UUID) -> Team | None:
        return await self.session.get(Team, team_id)

    async def create(self, team: Team) -> Team:
        self.session.add(team)
        await self.session.commit()
        await self.session.refresh(team)
        return team

    async def update(self, team: Team) -> Team:
        await self.session.commit()
        await self.session.refresh(team)
        return team

    async def delete(self, team: Team) -> None:
        await self.session.delete(team)
        await self.session.commit()
