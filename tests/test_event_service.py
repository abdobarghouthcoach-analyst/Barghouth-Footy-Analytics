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
    assert created.is_reviewed is False
    assert created.reviewed_at is None
    assert created.reviewed_by is None
    assert created.confidence is None

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


@pytest.mark.asyncio
async def test_event_review_state_updates_without_marking_corrected(session):
    from app.services.event import EventService

    service = EventService(session)
    created = await service.create_event(
        {
            "match_id": UUID(int=1),
            "team_id": UUID(int=2),
            "event_type": "goal",
            "minute": 10,
            "second": 5,
            "period": "1H",
        }
    )

    reviewed = await service.update_event(created.id, {"is_reviewed": True, "reviewed_by": "analyst"})

    assert reviewed is not None
    assert reviewed.is_reviewed is True
    assert reviewed.reviewed_at is not None
    assert reviewed.reviewed_by == "analyst"
    assert reviewed.edited_at is None

    unreviewed = await service.update_event(created.id, {"is_reviewed": False})

    assert unreviewed is not None
    assert unreviewed.is_reviewed is False
    assert unreviewed.reviewed_at is None
    assert unreviewed.reviewed_by is None
    assert unreviewed.edited_at is None


@pytest.mark.asyncio
async def test_event_confidence_updates_without_marking_corrected(session):
    from app.services.event import EventService

    service = EventService(session)
    created = await service.create_event(
        {
            "match_id": UUID(int=1),
            "team_id": UUID(int=2),
            "event_type": "shot_on_goal",
            "minute": 12,
            "second": 4,
            "period": "1H",
        }
    )

    updated = await service.update_event(created.id, {"confidence": "high"})

    assert updated is not None
    assert updated.confidence == "high"
    assert updated.edited_at is None


def test_event_update_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        EventUpdate.model_validate({"confidence": "certain"})


@pytest.mark.asyncio
async def test_event_unreviewed_state_cannot_keep_reviewer(session):
    from app.services.event import EventService

    service = EventService(session)
    created = await service.create_event(
        {
            "match_id": UUID(int=1),
            "team_id": UUID(int=2),
            "event_type": "goal",
            "minute": 10,
            "second": 5,
            "period": "1H",
        }
    )

    updated = await service.update_event(created.id, {"is_reviewed": False, "reviewed_by": "analyst"})

    assert updated is not None
    assert updated.is_reviewed is False
    assert updated.reviewed_at is None
    assert updated.reviewed_by is None
