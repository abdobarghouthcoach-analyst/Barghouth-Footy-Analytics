import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.season import Season
from app.schemas.season import SeasonCreate, SeasonUpdate
from app.services.season import SeasonService


@pytest.fixture
def season_service() -> SeasonService:
    mock_session = Mock()
    service = SeasonService(session=mock_session)
    service.repository = Mock()
    return service


def make_season(
    id_value,
    name="2023/24",
    start_date=date(2023, 8, 1),
    end_date=date(2024, 5, 31),
    competition_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    is_active=False,
):
    season = Season(
        name=name,
        start_date=start_date,
        end_date=end_date,
        competition_id=competition_id,
        is_active=is_active,
    )
    season.id = uuid.UUID(id_value)
    season.created_at = datetime.now(timezone.utc)
    season.updated_at = season.created_at
    return season


@pytest.mark.asyncio
async def test_list_seasons(season_service: SeasonService):
    season = make_season("22222222-2222-2222-2222-222222222222")
    season_service.repository.list = AsyncMock(return_value=[season])

    result = await season_service.list_seasons()

    assert len(result) == 1
    assert result[0].id == season.id
    assert result[0].competition_id == season.competition_id


@pytest.mark.asyncio
async def test_get_season_found(season_service: SeasonService):
    season = make_season("33333333-3333-3333-3333-333333333333")
    season_service.repository.get = AsyncMock(return_value=season)

    result = await season_service.get_season(season.id)

    assert result is not None
    assert result.id == season.id
    assert result.name == season.name


@pytest.mark.asyncio
async def test_get_season_not_found(season_service: SeasonService):
    season_service.repository.get = AsyncMock(return_value=None)

    result = await season_service.get_season(uuid.UUID("44444444-4444-4444-4444-444444444444"))

    assert result is None


@pytest.mark.asyncio
async def test_create_season(season_service: SeasonService):
    season = make_season("55555555-5555-5555-5555-555555555555", name="2024/25", start_date=date(2024, 8, 1), end_date=date(2025, 5, 31), is_active=True)
    season_service.repository.create = AsyncMock(return_value=season)

    data = SeasonCreate(
        name="2024/25",
        start_date=date(2024, 8, 1),
        end_date=date(2025, 5, 31),
        competition_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        is_active=True,
    )
    result = await season_service.create_season(data)

    assert result.id == season.id
    assert result.name == "2024/25"
    assert result.is_active is True


@pytest.mark.asyncio
async def test_create_season_invalid_dates(season_service: SeasonService):
    data = SeasonCreate(
        name="Invalid Season",
        start_date=date(2025, 8, 1),
        end_date=date(2025, 5, 31),
        competition_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        is_active=False,
    )

    with pytest.raises(ValueError, match="start_date must be before end_date"):
        await season_service.create_season(data)


@pytest.mark.asyncio
async def test_update_season(season_service: SeasonService):
    season = make_season("66666666-6666-6666-6666-666666666666")
    season_service.repository.get = AsyncMock(return_value=season)
    season_service.repository.update = AsyncMock(return_value=season)

    update_payload = SeasonUpdate(name="2024/25", is_active=True)
    result = await season_service.update_season(season.id, update_payload)

    assert result is not None
    assert result.name == "2024/25"
    assert result.is_active is True


@pytest.mark.asyncio
async def test_update_season_not_found(season_service: SeasonService):
    season_service.repository.get = AsyncMock(return_value=None)

    result = await season_service.update_season(
        uuid.UUID("77777777-7777-7777-7777-777777777777"),
        SeasonUpdate(name="2024/25"),
    )

    assert result is None


@pytest.mark.asyncio
async def test_delete_season_not_found(season_service: SeasonService):
    season_service.repository.get = AsyncMock(return_value=None)

    result = await season_service.delete_season(uuid.UUID("88888888-8888-8888-8888-888888888888"))

    assert result is False


@pytest.mark.asyncio
async def test_delete_season_success(season_service: SeasonService):
    season = make_season("99999999-9999-9999-9999-999999999999")
    season_service.repository.get = AsyncMock(return_value=season)
    season_service.repository.delete = AsyncMock(return_value=None)

    result = await season_service.delete_season(season.id)

    assert result is True
