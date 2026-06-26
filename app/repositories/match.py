from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import Match


class MatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> List[Match]:
        result = await self.session.execute(select(Match))
        return result.scalars().all()

    async def get(self, match_id: UUID) -> Match | None:
        return await self.session.get(Match, match_id)

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
