from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, match_id: UUID | None = None) -> List[Event]:
        statement = select(Event)
        if match_id is not None:
            statement = statement.where(Event.match_id == match_id)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get(self, event_id: UUID) -> Event | None:
        return await self.session.get(Event, event_id)

    async def create(self, event: Event) -> Event:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def update(self, event: Event) -> Event:
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def delete(self, event: Event) -> None:
        await self.session.delete(event)
        await self.session.commit()
