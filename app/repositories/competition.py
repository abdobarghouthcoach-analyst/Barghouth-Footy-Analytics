from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competition import Competition


class CompetitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> List[Competition]:
        result = await self.session.execute(select(Competition))
        return result.scalars().all()

    async def get(self, competition_id: UUID) -> Competition | None:
        result = await self.session.get(Competition, competition_id)
        return result

    async def create(self, competition: Competition) -> Competition:
        self.session.add(competition)
        await self.session.commit()
        await self.session.refresh(competition)
        return competition

    async def update(self, competition: Competition) -> Competition:
        await self.session.commit()
        await self.session.refresh(competition)
        return competition

    async def delete(self, competition: Competition) -> None:
        await self.session.delete(competition)
        await self.session.commit()
