from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.event import EventCreate, EventResponse, EventUpdate
from app.services.event import EventService

router = APIRouter(prefix="/events", tags=["Events"])


async def get_service(session: AsyncSession = Depends(get_db_session)) -> EventService:
    return EventService(session)


@router.get("/", response_model=list[EventResponse])
async def list_events(
    match_id: UUID | None = Query(None),
    service: EventService = Depends(get_service),
) -> list[EventResponse]:
    return await service.list_events(match_id=match_id)


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(data: EventCreate, service: EventService = Depends(get_service)) -> EventResponse:
    return await service.create_event(data)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: UUID, service: EventService = Depends(get_service)) -> EventResponse:
    event = await service.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(event_id: UUID, data: EventUpdate, service: EventService = Depends(get_service)) -> EventResponse:
    event = await service.update_event(event_id, data)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: UUID, service: EventService = Depends(get_service)) -> None:
    success = await service.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return None
