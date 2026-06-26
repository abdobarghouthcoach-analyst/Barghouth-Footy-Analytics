import asyncio
from uuid import UUID

import pytest

from app.models.event import Event


@pytest.mark.asyncio
async def test_event_crud(session):
    from app.services.event import EventService

    service = EventService(session)

    data = {
        "match_id": UUID(int=1),
        "team_id": UUID(int=2),
        "player_id": None,
        "event_type": "pass",
        "minute": 12,
        "second": 34,
        "period": "1H",
        "x_coordinate": 0.5,
        "y_coordinate": 0.5,
        "notes": "Test event",
        "tags": {"test": True},
        "source_provider": "manual",
        "source_event_id": "evt-1",
        "raw_payload": {"original": True},
    }

    # create
    created = await service.create_event(data)
    assert created.id is not None
    assert created.event_type == "pass"

    # get
    fetched = await service.get_event(created.id)
    assert fetched is not None
    assert fetched.id == created.id

    # update
    updated = await service.update_event(created.id, {"notes": "Updated"})
    assert updated is not None
    assert updated.notes == "Updated"

    # delete
    deleted = await service.delete_event(created.id)
    assert deleted is True
