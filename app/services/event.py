from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.repositories.event import EventRepository
from app.schemas.event import EventCreate, EventResponse, EventUpdate


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = EventRepository(session)

    async def list_events(self) -> list[EventResponse]:
        items = await self.repository.list()
        return [EventResponse.from_orm(i) for i in items]

    async def get_event(self, event_id: UUID) -> EventResponse | None:
        item = await self.repository.get(event_id)
        return EventResponse.from_orm(item) if item else None

    async def create_event(self, data: EventCreate) -> EventResponse:
        event = Event(
            match_id=data.match_id,
            team_id=data.team_id,
            player_id=data.player_id,
            event_type=data.event_type,
            minute=data.minute,
            second=data.second,
            period=data.period,
            x_coordinate=data.x_coordinate,
            y_coordinate=data.y_coordinate,
            notes=data.notes,
            tags=data.tags,
            source_provider=data.source_provider,
            source_event_id=data.source_event_id,
            raw_payload=data.raw_payload,
        )
        event = await self.repository.create(event)
        return EventResponse.from_orm(event)

    async def update_event(self, event_id: UUID, data: EventUpdate) -> EventResponse | None:
        item = await self.repository.get(event_id)
        if item is None:
            return None

        if data.match_id is not None:
            item.match_id = data.match_id
        if data.team_id is not None:
            item.team_id = data.team_id
        if data.player_id is not None:
            item.player_id = data.player_id
        if data.event_type is not None:
            item.event_type = data.event_type
        if data.minute is not None:
            item.minute = data.minute
        if data.second is not None:
            item.second = data.second
        if data.period is not None:
            item.period = data.period
        if data.x_coordinate is not None:
            item.x_coordinate = data.x_coordinate
        if data.y_coordinate is not None:
            item.y_coordinate = data.y_coordinate
        if data.notes is not None:
            item.notes = data.notes
        if data.tags is not None:
            item.tags = data.tags
        if data.source_provider is not None:
            item.source_provider = data.source_provider
        if data.source_event_id is not None:
            item.source_event_id = data.source_event_id
        if data.raw_payload is not None:
            item.raw_payload = data.raw_payload

        item = await self.repository.update(item)
        return EventResponse.from_orm(item)

    async def delete_event(self, event_id: UUID) -> bool:
        item = await self.repository.get(event_id)
        if item is None:
            return False
        await self.repository.delete(item)
        return True
