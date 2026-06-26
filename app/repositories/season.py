from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.season import Season


class SeasonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> List[Season]:
        result = await self.session.execute(select(Season))
        return result.scalars().all()

    async def get(self, season_id: UUID) -> Season | None:
        return await self.session.get(Season, season_id)

    async def create(self, season: Season) -> Season:
        self.session.add(season)
        await self.session.commit()
        await self.session.refresh(season)
        return season

    async def update(self, season: Season) -> Season:
        await self.session.commit()
        await self.session.refresh(season)
        return season

    async def delete(self, season: Season) -> None:
        await self.session.delete(season)
        await self.session.commit()
