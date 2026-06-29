import asyncio
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.models.event import Event
from app.schemas.event import EventUpdate


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
    assert updated.edited_at is not None

    # delete
    deleted = await service.delete_event(created.id)
    assert deleted is True


@pytest.mark.asyncio
async def test_event_correction_updates_only_editable_fields(session):
    from app.services.event import EventService

    service = EventService(session)
    created = await service.create_event(
        {
            "match_id": UUID(int=1),
            "team_id": UUID(int=2),
            "event_type": "shot_on_goal",
            "minute": 1,
            "second": 2,
            "period": "1H",
            "source": "import",
            "provider": "veo",
            "import_job_id": UUID(int=7),
            "provider_event_id": "clip-1",
            "raw_payload": {"filename": "01 000102_-_Shot_on_goal.mp4"},
        }
    )

    updated = await service.update_event(
        created.id,
        {
            "event_type": "goal",
            "team_id": None,
            "minute": 6,
            "second": 59,
            "notes": "Corrected after review",
        },
    )

    assert updated is not None
    assert updated.event_type == "goal"
    assert updated.team_id is None
    assert updated.minute == 6
    assert updated.second == 59
    assert updated.notes == "Corrected after review"
    assert updated.source == "import"
    assert updated.provider == "veo"
    assert updated.import_job_id == UUID(int=7)
    assert updated.provider_event_id == "clip-1"
    assert updated.raw_payload == {"filename": "01 000102_-_Shot_on_goal.mp4"}
    assert updated.edited_at is not None


def test_event_update_rejects_immutable_fields():
    with pytest.raises(ValidationError):
        EventUpdate.model_validate(
            {
                "source": "manual",
                "provider": None,
                "import_job_id": None,
                "raw_payload": {},
                "provider_event_id": "changed",
            }
        )
