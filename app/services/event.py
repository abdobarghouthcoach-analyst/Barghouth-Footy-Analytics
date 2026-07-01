from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.repositories.event import EventRepository
from app.schemas.event import EventCreate, EventResponse, EventUpdate


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = EventRepository(session)

    async def list_events(self, match_id: UUID | None = None) -> list[EventResponse]:
        items = await self.repository.list(match_id=match_id)
        return [EventResponse.model_validate(i) for i in items]

    async def get_event(self, event_id: UUID) -> EventResponse | None:
        item = await self.repository.get(event_id)
        return EventResponse.model_validate(item) if item else None

    async def create_event(self, data: EventCreate | dict) -> EventResponse:
        data = EventCreate.model_validate(data)
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
            import_job_id=data.import_job_id,
            video_clip_id=data.video_clip_id,
            source=data.source,
            provider=data.provider,
            provider_event_id=data.provider_event_id,
            raw_payload=data.raw_payload,
        )
        event = await self.repository.create(event)
        return EventResponse.model_validate(event)

    async def update_event(self, event_id: UUID, data: EventUpdate | dict) -> EventResponse | None:
        data = EventUpdate.model_validate(data)
        item = await self.repository.get(event_id)
        if item is None:
            return None

        changed = False
        for field_name in ("team_id", "event_type", "minute", "second", "notes"):
            if field_name not in data.model_fields_set:
                continue
            value = getattr(data, field_name)
            if getattr(item, field_name) != value:
                setattr(item, field_name, value)
                changed = True

        if changed:
            item.edited_at = datetime.now(timezone.utc)

        item = await self.repository.update(item)
        return EventResponse.model_validate(item)

    async def delete_event(self, event_id: UUID) -> bool:
        item = await self.repository.get(event_id)
        if item is None:
            return False
        await self.repository.delete(item)
        return True
